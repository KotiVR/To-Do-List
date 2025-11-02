import psycopg2

try:
    conn = psycopg2.connect(
        host="db.ihbhargjqkyohyroakgj.supabase.co",      # e.g. db.xxxxxx.supabase.co
        port=5432,
        user="postgres",
        password="QznnLCZZX7mstMOo",
        dbname="postgres"
    )
    print("✅ Connected successfully to Supabase PostgreSQL!")
    conn.close()
except Exception as e:
    print("❌ Database connection failed:")
    print(e)
