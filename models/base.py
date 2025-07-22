# models/base.py
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ─────────────────── Cell ────────────────────
class Cell(Base):
    __tablename__ = "cells"
    id = Column(Integer, primary_key=True)
    cell_id = Column(String, unique=True)
    chemistry = Column(String)
    rated_capacity = Column(Float)
    configuration = Column(String)
    assembly_date = Column(DateTime)
    notes = Column(Text)
    znbr_molarity = Column(Float)
    teacl_molarity = Column(Float)
    channel = Column(Integer)
    status = Column(String)
    cycles = relationship("Cycle", back_populates="cell", cascade="all,delete")

# ─────────────────── Cycle ───────────────────
class Cycle(Base):
    __tablename__ = "cycles"
    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey("cells.id"))
    cycle_no = Column(Integer)
    current_density = Column(Float)
    charge_V = Column(Float)
    discharge_V = Column(Float)
    capacity_mAh = Column(Float)
    pH = Column(Float)
    csv_path = Column(String)
    ce_pct = Column(Float)
    delta_V = Column(Float)
    observation = Column(Text)
    photo_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    cell = relationship("Cell", back_populates="cycles")