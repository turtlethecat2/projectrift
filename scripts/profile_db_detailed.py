#!/usr/bin/env python3
"""
Detailed database profiling to distinguish connection vs query time.
"""

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv()

import psycopg2
from psycopg2.extras import RealDictCursor

connection_string = os.getenv("DATABASE_URL")
print(f"DATABASE_URL: {connection_string[:30]}..." if connection_string else "NOT SET")
print()

# Test 1: Connection time
print("Test 1: Connection time")
start = time.perf_counter()
conn = psycopg2.connect(connection_string)
conn_time = (time.perf_counter() - start) * 1000
print(f"  Connection time: {conn_time:.2f}ms")

# Test 2: Query time (with existing connection)
print("\nTest 2: Query time (reusing connection)")
cur = conn.cursor(cursor_factory=RealDictCursor)

start = time.perf_counter()
query = """
    SELECT
        COALESCE(SUM(gold_value), 0) AS total_gold,
        COALESCE(SUM(xp_value), 0) AS total_xp,
        COUNT(*) AS total_events,
        COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) AS events_today,
        SUM(CASE WHEN event_type = 'call_dial' THEN 1 ELSE 0 END) AS calls_made,
        SUM(CASE WHEN event_type = 'call_connect' THEN 1 ELSE 0 END) AS calls_connected,
        SUM(CASE WHEN event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS meetings_booked,
        SUM(CASE WHEN created_at >= DATE_TRUNC('week', CURRENT_DATE) AND event_type = 'meeting_booked' THEN 1 ELSE 0 END) AS weekly_meetings_booked
    FROM raw_events
"""
cur.execute(query)
result = cur.fetchone()
query_time = (time.perf_counter() - start) * 1000
print(f"  Query time: {query_time:.2f}ms")
print(f"  Result: {dict(result)}")

# Test 3: Row count in raw_events
print("\nTest 3: Table size")
cur.execute("SELECT COUNT(*) FROM raw_events")
count = cur.fetchone()["count"]
print(f"  raw_events rows: {count}")

# Test 4: Second query (connection warm)
print("\nTest 4: Second query (cache warm)")
start = time.perf_counter()
cur.execute(query)
result = cur.fetchone()
query2_time = (time.perf_counter() - start) * 1000
print(f"  Query time: {query2_time:.2f}ms")

cur.close()
conn.close()

# Test 5: Fresh connection + query (simulating current behavior)
print("\nTest 5: Fresh connection + query (current HUD behavior)")
start = time.perf_counter()
conn2 = psycopg2.connect(connection_string)
cur2 = conn2.cursor(cursor_factory=RealDictCursor)
cur2.execute(query)
result = cur2.fetchone()
cur2.close()
conn2.close()
total_time = (time.perf_counter() - start) * 1000
print(f"  Total time: {total_time:.2f}ms")

print("\n" + "=" * 50)
print("ANALYSIS")
print("=" * 50)
print(f"Connection overhead: {conn_time:.0f}ms")
print(f"Query execution: {query_time:.0f}ms")
print(f"Combined (fresh): {total_time:.0f}ms")
print()
print("RECOMMENDATION:")
if conn_time > 100:
    print(
        "- Connection is slow - use connection pooling or @st.cache_resource for connection"
    )
if query_time > 50:
    print("- Query is slow - add index or optimize query")
    print("- Consider @st.cache_data with short TTL for stats")
