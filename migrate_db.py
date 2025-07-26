from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, MetaData, Table
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///instance/quiz_app.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def add_source_url_column():
    # Create a MetaData instance
    metadata = MetaData()
    
    # Reflect the database to get the current state
    metadata.reflect(bind=engine)
    
    # Get the newsletters table
    newsletters_table = metadata.tables['newsletters']
    
    # Check if the column already exists
    if 'source_url' not in newsletters_table.columns:
        print("Adding source_url column to newsletters table...")
        
        # Create a new column
        from sqlalchemy.schema import AddColumn
        from sqlalchemy import text
        
        # Use raw SQL to add the column
        with engine.connect() as connection:
            connection.execute(text('ALTER TABLE newsletters ADD COLUMN source_url VARCHAR(500)'))
            connection.commit()
        
        print("Successfully added source_url column to newsletters table.")
    else:
        print("source_url column already exists in newsletters table.")

if __name__ == "__main__":
    print("Starting database migration...")
    add_source_url_column()
    print("Database migration completed.")
    
    # Close the session
    session.close()
