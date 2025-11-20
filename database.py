import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Direccion(Base):
    __tablename__ = 'direcciones'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    presupuestos = relationship("Presupuesto", back_populates="direccion")
    adquisiciones = relationship("Adquisicion", back_populates="direccion")

class Meta(Base):
    __tablename__ = 'metas'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    adquisiciones = relationship("Adquisicion", back_populates="meta")

class Presupuesto(Base):
    __tablename__ = 'presupuestos'
    
    id = Column(Integer, primary_key=True, index=True)
    direccion_id = Column(Integer, ForeignKey('direcciones.id'), nullable=False)
    año = Column(Integer, nullable=False)
    monto = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    direccion = relationship("Direccion", back_populates="presupuestos")

class Adquisicion(Base):
    __tablename__ = 'adquisiciones'
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False)
    direccion_id = Column(Integer, ForeignKey('direcciones.id'), nullable=False)
    meta_id = Column(Integer, ForeignKey('metas.id'), nullable=False)
    año = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    descripcion = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    estado = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    direccion = relationship("Direccion", back_populates="adquisiciones")
    meta = relationship("Meta", back_populates="adquisiciones")

class Alerta(Base):
    __tablename__ = 'alertas'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    direccion_id = Column(Integer, ForeignKey('direcciones.id'), nullable=True)
    umbral_porcentaje = Column(Float, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
