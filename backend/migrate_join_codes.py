#!/usr/bin/env python3
"""
Migration script to add join codes to existing groups
Run this once to update the database schema
"""

import sqlite3
import random
import string

DB_NAME = "test.db"

def generate_join_code():
    """Generate a unique 4-digit alphanumeric join code"""
    while True:
        # Generate 4-character code with uppercase letters and numbers
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        # Check if code already exists
        conn = sqlite3.connect(DB_NAME)
        existing = conn.execute(
            'SELECT 1 FROM groups WHERE join_code = ?', (code,)
        ).fetchone()
        conn.close()
        
        if not existing:
            return code

def migrate_database():
    """Add join_code column to groups table and populate existing groups"""
    conn = sqlite3.connect(DB_NAME)
    
    try:
        # Check if join_code column already exists
        cursor = conn.execute("PRAGMA table_info(groups)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'join_code' not in columns:
            print("Adding join_code column to groups table...")
            conn.execute("ALTER TABLE groups ADD COLUMN join_code TEXT")
            print("✅ Column added successfully")
        else:
            print("✅ join_code column already exists")
        
        # Get all groups without join codes
        groups_without_codes = conn.execute(
            "SELECT group_id, group_name FROM groups WHERE join_code IS NULL OR join_code = ''"
        ).fetchall()
        
        if groups_without_codes:
            print(f"Found {len(groups_without_codes)} groups without join codes. Adding codes...")
            
            for group_id, group_name in groups_without_codes:
                join_code = generate_join_code()
                conn.execute(
                    "UPDATE groups SET join_code = ? WHERE group_id = ?",
                    (join_code, group_id)
                )
                print(f"  - {group_name}: {join_code}")
            
            print("✅ All groups now have join codes")
        else:
            print("✅ All groups already have join codes")
        
        conn.commit()
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Running database migration for join codes...")
    migrate_database()
