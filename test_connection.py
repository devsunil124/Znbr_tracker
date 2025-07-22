# test_connection.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# This is the explicit import that should fix discovery issues
import sqlalchemy_libsql

print("--- Starting Connection Test ---")

# --- Load Secrets ---
project_root = os.path.dirname(os.path.abspath(__file__))
secrets_path = os.path.join(project_root, '.streamlit', 'secrets.toml')

if not os.path.exists(secrets_path):
    raise FileNotFoundError(f"SECRETS FILE NOT FOUND at: {secrets_path}")

load_dotenv(dotenv_path=secrets_path)
print("Successfully loaded secrets file.")

db_url = os.getenv("TURSO_DATABASE_URL")
db_token = os.getenv("TURSO_AUTH_TOKEN")

if not db_url or not db_token:
    raise ValueError("TURSO_DATABASE_URL or TURSO_AUTH_TOKEN not found in secrets file.")

print("Successfully read URL and Token from secrets.")

# --- Create Engine and Connect ---
try:
    print("Attempting to create SQLAlchemy engine...")
    engine = create_engine(
        db_url,
        connect_args={"auth_token": db_token}
    )
    print("Engine created successfully.")

    with engine.connect() as connection:
        print("Connection successful!")
        result = connection.execute(text("SELECT 1"))
        print("Test query successful. Result:", result.scalar())

    print("\n✅✅✅ DATABASE CONNECTION IS WORKING! ✅✅✅")

except Exception as e:
    print("\n❌❌❌ CONNECTION FAILED! ❌❌❌")
    print("Error Type:", type(e))
    print("Error Details:", e)