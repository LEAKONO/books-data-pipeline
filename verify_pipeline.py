#!/usr/bin/env python3
"""Complete pipeline verification"""

import subprocess
import snowflake.connector
import json
import os

print("=" * 50)
print("🔍 PIPELINE VERIFICATION")
print("=" * 50)

# 1. Check scraper output
print("\n📁 1. Checking scraper output...")
json_files = [f for f in os.listdir("data/raw") if f.endswith(".json")]
if json_files:
    latest = max(json_files, key=lambda x: os.path.getctime(f"data/raw/{x}"))
    with open(f"data/raw/{latest}", "r") as f:
        books = json.load(f)
    print(f"   ✅ Latest file: {latest}")
    print(f"   ✅ Books in file: {len(books)}")
else:
    print("   ❌ No JSON files found")

# 2. Check Snowflake connection
print("\n❄️ 2. Checking Snowflake...")
try:
    conn = snowflake.connector.connect(
        account='UHEZXRL-FQ09331',
        user='BOOKS_USER',
        password='BooksPass123!',
        database='BOOKS_DB',
        warehouse='BOOKS_WH'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM RAW.RAW_BOOKS")
    count = cursor.fetchone()[0]
    print(f"   ✅ Connected successfully")
    print(f"   ✅ Books in Snowflake: {count}")
    
    cursor.execute("SELECT COUNT(DISTINCT CATEGORY) FROM RAW.RAW_BOOKS")
    categories = cursor.fetchone()[0]
    print(f"   ✅ Unique categories: {categories}")
    
    conn.close()
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Check Airflow
print("\n✈️ 3. Checking Airflow...")
result = subprocess.run(["curl", "-s", "http://localhost:8080/health"], 
                        capture_output=True, text=True)
if "healthy" in result.stdout:
    print("   ✅ Airflow is running")
else:
    print("   ⚠️ Airflow may not be running")

print("\n" + "=" * 50)
print("✅ VERIFICATION COMPLETE")
print("=" * 50)
