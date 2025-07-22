# database.py
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This is the explicit import fix from before
import sqlalchemy_libsql

# Get secrets from st.secrets to connect to Turso
db_url = st.secrets["TURSO_DATABASE_URL"]
db_token = st.secrets["TURSO_AUTH_TOKEN"]

# Create the SQLAlchemy engine for the Streamlit app
engine = create_engine(
    db_url,
    connect_args={"auth_token": db_token}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()