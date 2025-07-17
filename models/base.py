# models/base.py

from sqlalchemy import (create_engine,
    Column,
    Integer,
    String,
    Float,       
    DateTime,
    ForeignKey,
    Text,)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
engine = create_engine("sqlite:///data/experiments.db", echo=False)

# ─────────────────── Cell ────────────────────
class Cell(Base):
    __tablename__ = "cells"
    id             = Column(Integer, primary_key=True)
    cell_id        = Column(String, unique=True)
    chemistry      = Column(String)
    rated_capacity = Column(Float)
    configuration  = Column(String)
    assembly_date  = Column(DateTime)
    notes          = Column(Text)
    znbr_molarity  = Column(Float)   # eg 1M
    teacl_molarity = Column(Float)

    channel        = Column(Integer)     # 1‑8
    status         = Column(String)      # 'running' / 'stopped'

    cycles = relationship("Cycle", back_populates="cell", cascade="all,delete")

 # ─────────────────── Cycle ───────────────────
class Cycle(Base):
    __tablename__ = "cycles"
    id              = Column(Integer, primary_key=True)
    cell_id         = Column(Integer, ForeignKey("cells.id"))   # ← key line
    cycle_no        = Column(Integer)
    current_density = Column(Float)
    charge_V        = Column(Float)
    discharge_V     = Column(Float)
    capacity_mAh    = Column(Float)
    pH              = Column(Float)
    csv_path        = Column(String)
    ce_pct          = Column(Float)
    delta_V         = Column(Float)
    observation     = Column(Text)
    photo_path      = Column(String)

    cell = relationship("Cell", back_populates="cycles")


# DB connection
if __name__ == "__main__":
    Base.metadata.create_all(engine)