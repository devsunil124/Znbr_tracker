# database.py
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Get secrets from st.secrets to connect to Turso
db_url = st.secrets["DATABASE_URL"]

# Create the SQLAlchemy engine for the Streamlit app
engine = create_engine(db_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
@contextmanager 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()