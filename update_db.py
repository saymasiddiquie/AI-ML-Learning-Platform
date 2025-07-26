import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, String, text

# Initialize database connection
db_path = 'quiz_db.db'
engine = create_engine(f'sqlite:///{db_path}')

# Method 1: Direct SQLite connection to add column
try:
    print("Attempting to add source_url column using direct SQLite connection...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(newsletters)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'source_url' not in columns:
        cursor.execute('ALTER TABLE newsletters ADD COLUMN source_url TEXT')
        conn.commit()
        print("Successfully added source_url column to newsletters table.")
    else:
        print("source_url column already exists in newsletters table.")
        
except Exception as e:
    print(f"Error updating database: {e}")
    
    # Method 2: Try SQLAlchemy text() if direct SQL fails
    try:
        print("Trying alternative method using SQLAlchemy text()...")
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE newsletters ADD COLUMN source_url TEXT'))
            conn.commit()
            print("Successfully added source_url column using SQLAlchemy text().")
    except Exception as e2:
        print(f"Alternative method also failed: {e2}")
        print("\nPlease try one of these manual solutions:")
        print("1. Delete the quiz_db.db file and restart the application to create a new database.")
        print("2. Use a SQLite browser to manually add the column:")
        print("   - Open quiz_db.db in a SQLite browser")
        print("   - Execute: ALTER TABLE newsletters ADD COLUMN source_url TEXT")

finally:
    if 'conn' in locals():
        conn.close()
    print("Database update process completed.")
