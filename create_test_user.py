#!/usr/bin/env python3
"""
Create a test user in the ePetCare database.
"""

import os
import sqlite3
import hashlib
import time
from datetime import datetime

def create_test_user(db_path, username, password, is_staff=True, is_superuser=False):
    """Create a test user in the database."""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the user already exists
        cursor.execute("SELECT id FROM auth_user WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"User '{username}' already exists with ID {existing_user[0]}")
            
            # Update the password for the existing user
            # Generate a simple password hash (not Django's format but will work for our app)
            password_hash = f"md5${hashlib.md5(password.encode()).hexdigest()}"
            
            cursor.execute(
                "UPDATE auth_user SET password = ? WHERE username = ?",
                (password_hash, username)
            )
            conn.commit()
            print(f"Updated password for user '{username}'")
            return True
        
        # Generate a simple password hash (not Django's format but will work for our app)
        password_hash = f"md5${hashlib.md5(password.encode()).hexdigest()}"
        
        # Get the current time in Django's format
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insert the new user
        cursor.execute("""
            INSERT INTO auth_user (
                username, password, first_name, last_name, email,
                is_staff, is_active, is_superuser, date_joined, last_login
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, password_hash, "Test", "User", f"{username}@example.com",
            1 if is_staff else 0, 1, 1 if is_superuser else 0, now, now
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        print(f"Created user '{username}' with ID {user_id}")
        
        # Check if we need to create a veterinarian record
        if is_staff:
            # Check if the vet_veterinarian table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vet_veterinarian'")
            if cursor.fetchone():
                # Check if a record already exists for this user
                cursor.execute("SELECT id FROM vet_veterinarian WHERE user_id = ?", (user_id,))
                if not cursor.fetchone():
                    # Create a veterinarian record
                    cursor.execute("""
                        INSERT INTO vet_veterinarian (
                            user_id, full_name, specialization, license_number, phone, bio, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user_id, "Test Veterinarian", "General", "VET12345", "555-1234",
                        "Test veterinarian account", now
                    ))
                    conn.commit()
                    print(f"Created veterinarian record for user '{username}'")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating test user: {e}")
        return False

if __name__ == "__main__":
    db_path = "db.sqlite3"
    username = "testvet"
    password = "password123"
    
    success = create_test_user(db_path, username, password)
    
    if success:
        print(f"\nTest user created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")
    else:
        print("\nFailed to create test user.")
