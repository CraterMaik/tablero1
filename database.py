import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
# Configurar engine con pool_pre_ping para detectar conexiones cerradas
# y pool_recycle para evitar conexiones SSL obsoletas
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexión antes de usar
    pool_recycle=3600,   # Recicla conexiones cada hora
    pool_size=5,         # Tamaño del pool
    max_overflow=10      # Conexiones extras permitidas
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UnidadEjecutora(Base):
    __tablename__ = 'unidades_ejecutoras'
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    programaciones = relationship("ProgramacionPresupuestal", back_populates="unidad_ejecutora")

class MetaPresupuestal(Base):
    __tablename__ = 'metas_presupuestales'
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    programaciones = relationship("ProgramacionPresupuestal", back_populates="meta")

class ProgramacionPresupuestal(Base):
    __tablename__ = 'programacion_presupuestal'
    
    id = Column(Integer, primary_key=True, index=True)
    año = Column(Integer, nullable=False)
    unidad_ejecutora_id = Column(Integer, ForeignKey('unidades_ejecutoras.id'), nullable=False)
    meta_id = Column(Integer, ForeignKey('metas_presupuestales.id'), nullable=True)
    clasificador = Column(String, nullable=True)
    descripcion_clasificador = Column(Text, nullable=True)
    
    pim = Column(Float, default=0)
    certificado = Column(Float, default=0)
    pim_por_certificar = Column(Float, default=0)
    compromiso_anual = Column(Float, default=0)
    devengado_acumulado = Column(Float, default=0)
    compromiso_por_devengar = Column(Float, default=0)
    pim_por_devengar = Column(Float, default=0)
    total_anual = Column(Float, default=0)
    saldo = Column(Float, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    unidad_ejecutora = relationship("UnidadEjecutora", back_populates="programaciones")
    meta = relationship("MetaPresupuestal", back_populates="programaciones")

class Adquisicion(Base):
    __tablename__ = 'adquisiciones'
    
    id = Column(Integer, primary_key=True, index=True)
    año = Column(Integer, nullable=False)
    unidad_ejecutora_id = Column(Integer, ForeignKey('unidades_ejecutoras.id'), nullable=False)
    meta_id = Column(Integer, ForeignKey('metas_presupuestales.id'), nullable=True)
    codigo_adquisicion = Column(String, nullable=True)
    descripcion = Column(Text, nullable=False)
    tipo_proceso = Column(String, nullable=True)
    estado = Column(String, nullable=False)
    monto_referencial = Column(Float, default=0)
    cantidad = Column(Integer, default=0)
    monto_adjudicado = Column(Float, default=0)
    fecha_convocatoria = Column(DateTime, nullable=True)
    fecha_adjudicacion = Column(DateTime, nullable=True)
    proveedor = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    unidad_ejecutora = relationship("UnidadEjecutora")
    meta = relationship("MetaPresupuestal")
    detalle = relationship("AdquisicionDetalle", back_populates="adquisicion", uselist=False)
    procesos = relationship("AdquisicionProceso", back_populates="adquisicion", order_by="AdquisicionProceso.orden")

class AdquisicionDetalle(Base):
    __tablename__ = 'adquisiciones_detalle'
    
    id = Column(Integer, primary_key=True, index=True)
    adquisicion_id = Column(Integer, ForeignKey('adquisiciones.id'), nullable=False, unique=True)
    requerimientos_total = Column(Integer, default=1)
    requerimientos_adquiridos = Column(Integer, default=0)
    tipo_servicio = Column(String, nullable=True)
    pim_asignado = Column(Float, default=0)
    unidad_responsable = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    adquisicion = relationship("Adquisicion", back_populates="detalle")

class AdquisicionProceso(Base):
    __tablename__ = 'adquisiciones_proceso'
    
    id = Column(Integer, primary_key=True, index=True)
    adquisicion_id = Column(Integer, ForeignKey('adquisiciones.id'), nullable=False)
    orden = Column(Integer, nullable=False)
    hito = Column(String, nullable=False)
    tipo_flujo = Column(String, nullable=False)
    responsable_area = Column(String, nullable=False)
    responsable_correo = Column(String, nullable=True)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=True)
    dias_transcurridos = Column(Integer, default=0)
    comentarios = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    adquisicion = relationship("Adquisicion", back_populates="procesos")

class Alerta(Base):
    __tablename__ = 'alertas'
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    unidad_ejecutora_id = Column(Integer, ForeignKey('unidades_ejecutoras.id'), nullable=True)
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
