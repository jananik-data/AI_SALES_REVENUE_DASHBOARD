import sqlite3
import pandas as pd
import sys

# Set UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def view_database():
    conn = sqlite3.connect("sales_dashboard.db")
    
    print("=" * 75)
    print(" >>> REVPULSE AI - SQLITE DATABASE EXPLORER <<<")
    print("=" * 75)
    
    # 1. Users Table
    print("\n[1] REGISTERED USERS TABLE:")
    print("-" * 75)
    users_df = pd.read_sql_query("SELECT id, username, email, created_at FROM users", conn)
    if not users_df.empty:
        print(users_df.to_string(index=False))
    else:
        print("No users found.")
    
    # 2. Database Counts Summary
    print("\n" + "=" * 75)
    print(" [2] DATABASE TOTALS SUMMARY:")
    print("-" * 75)
    user_count = pd.read_sql_query("SELECT COUNT(*) as total_users FROM users", conn).iloc[0]['total_users']
    sales_count = pd.read_sql_query("SELECT COUNT(*) as total_sales FROM sales", conn).iloc[0]['total_sales']
    chat_count = pd.read_sql_query("SELECT COUNT(*) as total_chats FROM chat_history", conn).iloc[0]['total_chats']
    pred_count = pd.read_sql_query("SELECT COUNT(*) as total_predictions FROM predictions", conn).iloc[0]['total_predictions']
    
    print(f" * Total Registered Users       : {user_count}")
    print(f" * Total Sales Transactions      : {sales_count:,} records")
    print(f" * Total AI Analyst Chat Logs    : {chat_count}")
    print(f" * Total AI Prediction Runs      : {pred_count}")
    
    # 3. Recent Sales Transactions
    print("\n" + "=" * 75)
    print(" [3] RECENT 10 SALES TRANSACTIONS:")
    print("-" * 75)
    sales_df = pd.read_sql_query(
        "SELECT id, date, product, category, region, quantity, revenue, user_id FROM sales ORDER BY id DESC LIMIT 10", 
        conn
    )
    if not sales_df.empty:
        print(sales_df.to_string(index=False))
    else:
        print("No sales records found.")
    
    print("\n" + "=" * 75)
    conn.close()

if __name__ == "__main__":
    view_database()
