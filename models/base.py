# models/base.py

from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Cell(Base):
    __tablename__ = "cells"
    id             = Column(Integer, primary_key=True)
    cell_id        = Column(String, unique=True)        # e.g. S‑01
    chemistry      = Column(String)                    # Zn‑Br variant
    rated_capacity = Column(Float)                     # mAh
    configuration  = Column(String)                    # e.g. 2×2 cm
    assembly_date  = Column(DateTime)
    notes          = Column(Text)

    channel        = Column(Integer)                   # 1‑8
    status         = Column(String)                    # 'running'/'stopped'

    cycles = relationship("Cycle", back_populates="cell", cascade="all,delete")

class Cycle(Base):
    __tablename__ = "cycles"

    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer)  # foreign key in full version
    cycle_no = Column(Integer)
    current_density = Column(String)
    charge_V = Column(String)
    discharge_V = Column(String)
    capacity_mAh = Column(String)
    pH = Column(String)
    csv_path = Column(String)  # if uploaded
    ce_pct = Column(String)  # auto-calculated
    delta_V = Column(String)  # auto-calculated
    observation = Column(Text)
    photo_path = Column(String)  # optional image


# DB connection
engine = create_engine("sqlite:///data/experiments.db", echo=True)
Base.metadata.create_all(engine)
Base.metadata.create_all(engine)
