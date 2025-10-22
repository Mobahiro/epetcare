"""PostgreSQL database wrapper for the Vet Desktop app.

This replaces direct SQLite usage so the desktop app can talk to the same
Render Postgres database as the Django web application.

We mimic the minimal interface currently expected from utils.database:
 - setup_postgres_connection(config)
 - get_connection()
 - class PostgresDatabaseManager with methods used by data_access:
     fetch_by_id, fetch_all, execute_query, execute_non_query,
     insert, update, delete

We translate the existing SQLite style '?' placeholders into '%s' for psycopg2.
"""
from __future__ import annotations

import psycopg2
import psycopg2.extras
import logging
import socket
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger('epetcare')

_pg_conn = None
_connect_kwargs: Optional[dict] = None


class PostgresConfigError(Exception):
    pass


def setup_postgres_connection(cfg: Dict[str, Any]) -> bool:
    """Establish a global PostgreSQL connection.

    Supports either discrete keys (host, port, database, user, password) or a
    single DATABASE_URL (in cfg['database_url']). If DATABASE_URL is provided
    and discrete keys are blank, it will be parsed.
    """
    global _pg_conn
    close_connection()

    # If the host field itself accidentally contains a URL, shift it into database_url
    if cfg.get('host', '').startswith(('postgres://', 'postgresql://')):
        if not cfg.get('database_url'):
            cfg['database_url'] = cfg['host']
        # Blank out host so parsing logic below runs
        cfg['host'] = ''

    # Parse database_url if provided
    if cfg.get('database_url'):
        url = cfg['database_url']
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('postgres', 'postgresql'):
                logger.warning("Unexpected scheme '%s' in database_url", parsed.scheme)
            # Overwrite blank/falsy existing keys with parsed values.
            # Note: dict.setdefault only sets when the key is missing; here we
            # intentionally assign when value is empty (e.g., '').
            if parsed.username and not cfg.get('user'):
                cfg['user'] = parsed.username
            if parsed.password and not cfg.get('password'):
                cfg['password'] = parsed.password
            if parsed.hostname and not cfg.get('host'):
                cfg['host'] = parsed.hostname
            if parsed.port and not cfg.get('port'):
                cfg['port'] = parsed.port
            # Path usually like '/dbname'
            if parsed.path and len(parsed.path) > 1 and not cfg.get('database'):
                cfg['database'] = parsed.path.lstrip('/')
            # sslmode might appear in query
            if not cfg.get('sslmode'):
                qs = parse_qs(parsed.query)
                if 'sslmode' in qs and qs['sslmode']:
                    cfg['sslmode'] = qs['sslmode'][0]
        except Exception as e:
            logger.error("Failed parsing database_url '%s': %s", url, e)

    required = ['host', 'port', 'database', 'user', 'password']
    missing = [k for k in required if not cfg.get(k)]
    if missing:
        logger.error(f"Postgres config missing keys after parsing: {missing}")
        return False

    # Heuristic: Render internal hostnames often are short like 'dpg-xxxxxx', while external include region and domain.
    # If there's no dot in the host, user probably copied only the internal hostname which won't resolve externally.
    if '.' not in cfg['host']:
        logger.error(
            "Host '%s' lacks a domain component. Use the External Database URL host (e.g. dpg-xxxxx-region.a.region-postgres.render.com).",
            cfg['host']
        )
        return False

    connect_kwargs = {
        'host': cfg['host'],
        'port': cfg['port'],
        'dbname': cfg['database'],
        'user': cfg['user'],
        'password': cfg['password'],
        'cursor_factory': psycopg2.extras.RealDictCursor
    }
    # Connection hygiene and resilience
    # - connect_timeout: fail fast on network issues
    # - keepalives*: keep idle connections alive to avoid server closing them
    connect_kwargs.setdefault('connect_timeout', 10)
    connect_kwargs.setdefault('keepalives', 1)
    connect_kwargs.setdefault('keepalives_idle', 60)
    connect_kwargs.setdefault('keepalives_interval', 30)
    connect_kwargs.setdefault('keepalives_count', 5)
    if cfg.get('sslmode'):
        connect_kwargs['sslmode'] = cfg['sslmode']

    # Pre-flight DNS resolution diagnostics
    try:
        resolved = socket.getaddrinfo(connect_kwargs['host'], connect_kwargs['port'])
        logger.debug(f"Host '{connect_kwargs['host']}' resolved to: {[r[4][0] for r in resolved]}")
    except socket.gaierror as de:
        logger.error(
            "DNS resolution failed for host '%s': %s. If this is a Render host, use the exact host value from the Render dashboard (Connections tab).",
            connect_kwargs['host'], de
        )
        return False

    try:
        logger.info(
            "Connecting to PostgreSQL host=%s port=%s db=%s user=%s sslmode=%s",
            connect_kwargs['host'], connect_kwargs['port'], connect_kwargs['dbname'], connect_kwargs['user'], connect_kwargs.get('sslmode')
        )
        _pg_conn = psycopg2.connect(**connect_kwargs)
        _pg_conn.autocommit = False
        # Save kwargs to allow auto-reconnect later
        global _connect_kwargs
        _connect_kwargs = dict(connect_kwargs)
        logger.info("PostgreSQL connection established")
        return True
    except Exception as e:
        logger.error(
            "Failed to connect to PostgreSQL host=%s port=%s db=%s user=%s: %s",
            connect_kwargs['host'], connect_kwargs['port'], connect_kwargs['dbname'], connect_kwargs['user'], e
        )
        return False


def close_connection():
    global _pg_conn
    if _pg_conn is not None:
        try:
            _pg_conn.close()
        except Exception:
            pass
    _pg_conn = None


def _reconnect_if_needed() -> bool:
    """Reconnect using stored connection kwargs if connection is closed."""
    global _pg_conn
    if _pg_conn is not None and getattr(_pg_conn, 'closed', 0) == 0:
        return True
    if not _connect_kwargs:
        logger.error("No stored connection parameters; cannot reconnect.")
        return False
    try:
        logger.info("Reconnecting to PostgreSQL ...")
        _pg_conn = psycopg2.connect(**_connect_kwargs)
        _pg_conn.autocommit = False
        logger.info("Reconnected to PostgreSQL")
        return True
    except Exception as e:
        logger.error(f"Auto-reconnect failed: {e}")
        return False


def get_connection():
    if _pg_conn is None or getattr(_pg_conn, 'closed', 0) != 0:
        if not _reconnect_if_needed():
            raise PostgresConfigError("PostgreSQL connection not initialized and auto-reconnect failed")
    return _pg_conn


def _convert_placeholders(query: str) -> str:
    """Convert SQLite-style '?' placeholders to psycopg2 '%s'.

    Naive approach: replace '?' that are not inside quotes. For current use
    (simple queries with positional params) a direct replace is acceptable.
    """
    # Simple direct replace; existing code never mixes literal '?' characters.
    return query.replace('?', '%s')


class PostgresDatabaseManager:
    def __init__(self, connection=None):
        self.conn = connection or get_connection()

    def fetch_by_id(self, table: str, id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        try:
            q = f"SELECT * FROM {table} WHERE id = %s"
            with self.conn.cursor() as cur:
                cur.execute(q, (id,))
                row = cur.fetchone()
                return (True, row) if row else (False, None)
        except Exception as e:
            logger.error(f"fetch_by_id error ({table}): {e}")
            return False, None

    def fetch_all(self, table: str, conditions: Dict[str, Any] = None,
                  order_by: str = None, limit: int = None) -> Tuple[bool, List[Dict[str, Any]]]:
        try:
            params: List[Any] = []
            q = f"SELECT * FROM {table}"
            if conditions:
                clauses = []
                for k, v in conditions.items():
                    clauses.append(f"{k} = %s")
                    params.append(v)
                q += " WHERE " + " AND ".join(clauses)
            if order_by:
                q += f" ORDER BY {order_by}"
            if limit:
                q += f" LIMIT {limit}"
            with self.conn.cursor() as cur:
                cur.execute(q, params)
                return True, cur.fetchall()
        except Exception as e:
            logger.error(f"fetch_all error ({table}): {e}")
            return False, []

    def execute_query(self, query: str, params: tuple = (), **_) -> Tuple[bool, List[Dict[str, Any]]]:
        q = _convert_placeholders(query)
        for attempt in (1, 2):
            try:
                # Ensure connection is alive
                if getattr(self.conn, 'closed', 0) != 0:
                    if not _reconnect_if_needed():
                        raise PostgresConfigError("Connection closed and reconnect failed")
                    self.conn = get_connection()
                with self.conn.cursor() as cur:
                    cur.execute(q, params)
                    rows = cur.fetchall()
                    return True, rows
            except Exception as e:
                logger.error(f"execute_query error: {e}; query={query}")
                try:
                    self.conn.rollback()
                except Exception:
                    pass
                # On first failure, try to reconnect and retry once
                if attempt == 1:
                    if _reconnect_if_needed():
                        self.conn = get_connection()
                        continue
                return False, []

    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        q = _convert_placeholders(query)
        for attempt in (1, 2):
            try:
                if getattr(self.conn, 'closed', 0) != 0:
                    if not _reconnect_if_needed():
                        raise PostgresConfigError("Connection closed and reconnect failed")
                    self.conn = get_connection()
                with self.conn.cursor() as cur:
                    cur.execute(q, params)
                    self.conn.commit()
                    return cur.rowcount
            except Exception as e:
                logger.error(f"execute_non_query error: {e}; query={query}")
                try:
                    self.conn.rollback()
                except Exception:
                    pass
                if attempt == 1:
                    if _reconnect_if_needed():
                        self.conn = get_connection()
                        continue
                return 0

    def insert(self, table: str, data: Dict[str, Any]) -> Tuple[bool, Union[int, str]]:
        try:
            cols = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            values = tuple(data.values())
            q = f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) RETURNING id"
            with self.conn.cursor() as cur:
                cur.execute(q, values)
                new_id = cur.fetchone()['id']
                self.conn.commit()
                return True, new_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"insert error ({table}): {e}")
            return False, str(e)

    def update(self, table: str, data: Dict[str, Any], id: int) -> Tuple[bool, Union[int, str]]:
        try:
            set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
            values = list(data.values()) + [id]
            q = f"UPDATE {table} SET {set_clause} WHERE id = %s"
            with self.conn.cursor() as cur:
                cur.execute(q, values)
                affected = cur.rowcount
                self.conn.commit()
                return True, affected
        except Exception as e:
            self.conn.rollback()
            logger.error(f"update error ({table}): {e}")
            return False, str(e)

    def delete(self, table: str, id: int) -> Tuple[bool, Union[int, str]]:
        try:
            q = f"DELETE FROM {table} WHERE id = %s"
            with self.conn.cursor() as cur:
                cur.execute(q, (id,))
                affected = cur.rowcount
                self.conn.commit()
                return True, affected
        except Exception as e:
            self.conn.rollback()
            logger.error(f"delete error ({table}): {e}")
            return False, str(e)


__all__ = [
    'setup_postgres_connection', 'get_connection', 'PostgresDatabaseManager'
]
