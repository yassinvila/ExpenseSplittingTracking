#!/usr/bin/env python3
"""
Database migration script for Centsible
Adds new columns to existing expenses table
"""

import sqlite3
import os

def migrate_database():
    """Migrate existing database to add new columns to expenses table"""
    
    if not os.path.exists('test.db'):
        print("❌ Database file 'test.db' not found. Please run init_db.py first.")
        return
    
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    try:
        # Check if new columns already exist
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = ['note', 'date', 'category', 'currency', 'split_method']
        missing_columns = [col for col in new_columns if col not in columns]
        
        if not missing_columns:
            print("✅ Database is already up to date!")
            return
        
        print(f"🔄 Adding missing columns: {', '.join(missing_columns)}")
        
        # Add missing columns one by one
        for column in missing_columns:
            if column == 'note':
                cursor.execute("ALTER TABLE expenses ADD COLUMN note TEXT")
            elif column == 'date':
                cursor.execute("ALTER TABLE expenses ADD COLUMN date TEXT")
            elif column == 'category':
                cursor.execute("ALTER TABLE expenses ADD COLUMN category TEXT")
            elif column == 'currency':
                cursor.execute("ALTER TABLE expenses ADD COLUMN currency TEXT")
            elif column == 'split_method':
                cursor.execute("ALTER TABLE expenses ADD COLUMN split_method TEXT")
            
            print(f"✅ Added column: {column}")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Migrating Centsible Database...")
    migrate_database()

