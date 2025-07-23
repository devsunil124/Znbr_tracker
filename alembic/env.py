import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import create_engine

from alembic import context

# --- Get the project root directory ---
project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from models.base import Base

# This is the Alembic Config object
config = context.config

# --- Load secrets from .streamlit/secrets.toml ---
secrets_path = os.path.join(project_root, '.streamlit', 'secrets.toml')
if os.path.exists(secrets_path):
    load_dotenv(dotenv_path=secrets_path)
else:
    print(f"Warning: Secrets file not found at {secrets_path}")

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    db_url = os.getenv("DATABASE_URL") # <-- USES POSTGRESQL
    if not db_url:
        raise ValueError("DATABASE_URL not found in .streamlit/secrets.toml")

    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Get the single database URL from environment variables
    db_url = os.getenv("DATABASE_URL") # <-- USES POSTGRESQL
    if not db_url:
        raise ValueError("DATABASE_URL must be set in .streamlit/secrets.toml")

    # Manually create the SQLAlchemy engine
    connectable = create_engine(db_url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()