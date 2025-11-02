import psycopg2

try:
    conn = psycopg2.connect(
        host="ep-falling-grass-a40q9cy3-pooler.us-east-1.aws.neon.tech",
        port=5432,
        user="neondb_owner",
        password="npg_VSt5nCNLq1Ak",
        dbname="todoflow",
        sslmode="require"
    )
    print("✅ Connected successfully to Neon!")
    conn.close()
except Exception as e:
    print("❌ Error:", e)
