#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = "/Users/koheimacmini/Documents/40_Program/20250506_Claude_Code_SecondeChallenge/lifeplan-simulator/instance/lifeplan.db"

def inspect_education_costs():
    """Inspect the education_costs table and display its contents."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='education_costs'")
    if not cursor.fetchone():
        print("The education_costs table doesn't exist.")
        conn.close()
        return False
    
    # Get column names
    cursor.execute("PRAGMA table_info(education_costs)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Table columns: {columns}")
    
    # Get all records
    cursor.execute("SELECT * FROM education_costs")
    records = cursor.fetchall()
    
    if not records:
        print("No records found in the education_costs table.")
        conn.close()
        return False
    
    # Print records in a formatted way
    print(f"\nFound {len(records)} records in education_costs table:")
    print("-" * 80)
    for record in records:
        print(f"ID: {record[0]}")
        print(f"Education Type: {record[1]}")
        print(f"Institution Type: {record[2]}")
        print(f"Academic Field: {record[3]}")
        print(f"Annual Cost: {record[4]}万円")
        print("-" * 80)
    
    conn.close()
    return True

def populate_education_costs():
    """Populate the education_costs table with appropriate education cost data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Education cost data (all costs in 万円/year)
    education_costs = [
        # 幼稚園
        ('幼稚園', '公立', None, 10),  # 公立幼稚園 約10万円/年
        ('幼稚園', '私立', None, 30),  # 私立幼稚園 約30万円/年
        
        # 小学校
        ('小学校', '公立', None, 15),  # 公立小学校 約15万円/年
        ('小学校', '私立', None, 100),  # 私立小学校 約100万円/年
        
        # 中学校
        ('中学校', '公立', None, 25),  # 公立中学校 約25万円/年
        ('中学校', '私立', None, 120),  # 私立中学校 約120万円/年
        
        # 高校
        ('高校', '公立', None, 30),  # 公立高校 約30万円/年
        ('高校', '私立', None, 100),  # 私立高校 約100万円/年
        
        # 大学
        ('大学', '国公立', '文系', 60),  # 国公立大学(文系) 約60万円/年
        ('大学', '国公立', '理系', 65),  # 国公立大学(理系) 約65万円/年
        ('大学', '私立', '文系', 100),  # 私立大学(文系) 約100万円/年
        ('大学', '私立', '理系', 140),  # 私立大学(理系) 約140万円/年
    ]
    
    # Clear existing data if any
    cursor.execute("DELETE FROM education_costs")
    
    # Insert new data
    cursor.executemany(
        "INSERT INTO education_costs (education_type, institution_type, academic_field, annual_cost) VALUES (?, ?, ?, ?)", 
        education_costs
    )
    
    conn.commit()
    print(f"Successfully populated education_costs table with {len(education_costs)} records")
    conn.close()

if __name__ == "__main__":
    print(f"Connecting to database: {DB_PATH}")
    
    # First inspect the table
    if not inspect_education_costs():
        # If no records found, populate the table
        print("\nPopulating education_costs table with default values...")
        populate_education_costs()
        
        # Verify the populated data
        print("\nVerifying populated data:")
        inspect_education_costs()