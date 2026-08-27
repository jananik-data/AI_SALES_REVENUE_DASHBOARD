"""
SQLite to PostgreSQL (Neon) Migration Script
---------------------------------------------
Reads all data from local SQLite and migrates it to the production Neon PostgreSQL.

Usage:
    cd <project root>
    python migrate_sqlite_to_postgres.py
"""

import os
import sys

# Load env vars from backend/.env
from dotenv import load_dotenv
load_dotenv("backend/.env")

import sqlite3
from pathlib import Path
from datetime import datetime

# ─── 1. Source: SQLite ────────────────────────────────────────────────────────
SQLITE_PATH = Path(__file__).parent / "sales_dashboard.db"

if not SQLITE_PATH.exists():
    print(f"[ERROR] SQLite database not found at: {SQLITE_PATH}")
    print("       Make sure you run this from the project root directory.")
    sys.exit(1)

# ─── 2. Target: Neon PostgreSQL ───────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    print("[ERROR] DATABASE_URL is not set in backend/.env")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"[INFO] Source: {SQLITE_PATH}")
print(f"[INFO] Target: {DATABASE_URL[:60]}...")

# ─── 3. Read from SQLite ──────────────────────────────────────────────────────
sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row
cursor = sqlite_conn.cursor()

# Fetch all users
cursor.execute("SELECT * FROM users")
users = [dict(row) for row in cursor.fetchall()]
print(f"[INFO] Found {len(users)} user(s) in SQLite.")

# Fetch all sales
cursor.execute("SELECT * FROM sales")
sales = [dict(row) for row in cursor.fetchall()]
print(f"[INFO] Found {len(sales)} sale record(s) in SQLite.")

# Fetch chat history if exists
try:
    cursor.execute("SELECT * FROM chat_history")
    chats = [dict(row) for row in cursor.fetchall()]
    print(f"[INFO] Found {len(chats)} chat history record(s) in SQLite.")
except Exception:
    chats = []
    print("[INFO] No chat_history table found (skipping).")

sqlite_conn.close()

if not users and not sales:
    print("[WARN] No data found in SQLite database. Nothing to migrate.")
    sys.exit(0)

# ─── 4. Write to PostgreSQL ───────────────────────────────────────────────────
import psycopg2
from psycopg2.extras import execute_values

try:
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_conn.autocommit = False
    pg_cur = pg_conn.cursor()
    print("[INFO] Connected to Neon PostgreSQL successfully.")
except Exception as e:
    print(f"[ERROR] Could not connect to PostgreSQL: {e}")
    sys.exit(1)

try:
    # ── Users ──────────────────────────────────────────────────────────────────
    migrated_users = 0
    user_id_map = {}  # old_sqlite_id -> new_postgres_id (for sales FK mapping)

    for u in users:
        try:
            pg_cur.execute("""
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET username = EXCLUDED.username
                RETURNING id
            """, (
                u.get("username"),
                u.get("email"),
                u.get("password_hash"),
                u.get("created_at") or datetime.utcnow().isoformat()
            ))
            new_id = pg_cur.fetchone()[0]
            user_id_map[u["id"]] = new_id
            migrated_users += 1
        except Exception as e:
            print(f"  [WARN] Skipping user {u.get('email')}: {e}")
            pg_conn.rollback()
            # Try fetching existing user
            try:
                pg_cur.execute("SELECT id FROM users WHERE email = %s", (u.get("email"),))
                row = pg_cur.fetchone()
                if row:
                    user_id_map[u["id"]] = row[0]
            except Exception:
                pass

    print(f"[OK] Migrated {migrated_users} user(s).")

    # ── Sales Records (Bulk Insert) ─────────────────────────────────────────────
    migrated_sales = 0
    skipped_sales = 0

    sales_values = []
    for s in sales:
        old_user_id = s.get("user_id")
        new_user_id = user_id_map.get(old_user_id)
        if not new_user_id:
            skipped_sales += 1
            continue
        
        sales_values.append((
            new_user_id,
            s.get("date"),
            s.get("product"),
            s.get("category"),
            s.get("quantity"),
            s.get("price"),
            s.get("region"),
            s.get("revenue"),
            s.get("created_at") or datetime.utcnow().isoformat()
        ))

    if sales_values:
        try:
            execute_values(pg_cur, """
                INSERT INTO sales (user_id, date, product, category, quantity, price, region, revenue, created_at)
                VALUES %s
            """, sales_values)
            migrated_sales += len(sales_values)
        except Exception as e:
            print(f"  [ERROR] Bulk inserting sales failed: {e}")

    print(f"[OK] Migrated {migrated_sales} sale record(s). Skipped: {skipped_sales}.")

    # ── Chat History ──────────────────────────────────────────────────────────
    migrated_chats = 0
    for c in chats:
        old_user_id = c.get("user_id")
        new_user_id = user_id_map.get(old_user_id)
        if not new_user_id:
            continue
        try:
            pg_cur.execute("""
                INSERT INTO chat_history (user_id, role, message, tool_calls_json, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                new_user_id,
                c.get("role"),
                c.get("message"),
                c.get("tool_calls_json"),
                c.get("created_at") or datetime.utcnow().isoformat()
            ))
            migrated_chats += 1
        except Exception as e:
            print(f"  [WARN] Skipping chat record id={c.get('id')}: {e}")

    if chats:
        print(f"[OK] Migrated {migrated_chats} chat history record(s).")

    pg_conn.commit()
    print("\n✅ Migration completed successfully!")
    print(f"   Users:   {migrated_users}")
    print(f"   Sales:   {migrated_sales}")
    print(f"   Chats:   {migrated_chats}")

except Exception as e:
    pg_conn.rollback()
    print(f"[ERROR] Migration failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    pg_cur.close()
    pg_conn.close()
