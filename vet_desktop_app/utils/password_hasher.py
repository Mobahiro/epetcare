"""
Password hashing utility for desktop app (Django-compatible)
Uses PBKDF2 algorithm like Django without requiring Django settings
"""

import hashlib
import base64
import secrets


def make_password(password: str, salt: str = None, iterations: int = 600000) -> str:
    """
    Create a Django-compatible password hash using PBKDF2-SHA256
    
    Args:
        password: Plain text password to hash
        salt: Optional salt (will be generated if not provided)
        iterations: Number of PBKDF2 iterations (Django default: 600000)
    
    Returns:
        Hashed password in Django format: pbkdf2_sha256$iterations$salt$hash
    """
    if salt is None:
        # Generate a random salt (Django uses 12 characters)
        salt = secrets.token_urlsafe(9)  # Generates ~12 characters
    
    # Hash the password using PBKDF2-SHA256
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    
    # Base64 encode the hash
    hash_b64 = base64.b64encode(hash_obj).decode('ascii').strip()
    
    # Return in Django format
    return f"pbkdf2_sha256${iterations}${salt}${hash_b64}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a Django-style hash
    
    Args:
        password: Plain text password to verify
        hashed: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        algorithm, iterations, salt, hash_b64 = hashed.split('$')
        
        if algorithm != 'pbkdf2_sha256':
            return False
        
        # Hash the provided password with the same salt and iterations
        computed_hash = make_password(password, salt, int(iterations))
        
        # Compare the hashes
        return computed_hash == hashed
    except Exception:
        return False
