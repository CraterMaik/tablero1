import pandas as pd
from sqlalchemy.orm import Session
from database import Direccion, Meta, Presupuesto, Adquisicion, Alerta, SessionLocal
import numpy as np

def inicializar_datos_ejemplo(db: Session):
    """Inicializa la base de datos con datos de ejemplo si está vacía"""
    
    if db.query(Direccion).count() > 0:
        return
    
    np.random.seed(42)
    
    direcciones_nombres = [
        "Dirección Administrativa",
        "Dirección de Operaciones",
        "Dirección de TI",
        "Dirección Financiera",
        "Dirección de RRHH"
    ]
    
    metas_nombres = [
        "Equipamiento",
        "Infraestructura",
        "Tecnología",
        "Capacitación",
        "Servicios"
    ]
    
    meses_nombres = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    
    direcciones = []
    for nombre in direcciones_nombres:
        dir = Direccion(nombre=nombre)
        db.add(dir)
        direcciones.append(dir)
    db.commit()
    
    metas = []
    for nombre in metas_nombres:
        meta = Meta(nombre=nombre)
        db.add(meta)
        metas.append(meta)
    db.commit()
    
    años = [2023, 2024, 2025]
    for año in años:
        for dir in direcciones:
            presupuesto_anual = np.random.randint(500000, 2000000)
            pres = Presupuesto(
                direccion_id=dir.id,
                año=año,
                monto=presupuesto_anual
            )
            db.add(pres)
    db.commit()
    
    id_counter = 1
    for año in años:
        num_adquisiciones = 80 if año == 2023 else (90 if año == 2024 else 60)
        
        for _ in range(num_adquisiciones):
            dir = np.random.choice(direcciones)
            meta = np.random.choice(metas)
            mes_num = np.random.randint(1, 13)
            mes_nombre = meses_nombres[mes_num - 1]
            
            presupuesto_dir = db.query(Presupuesto).filter(
                Presupuesto.direccion_id == dir.id,
                Presupuesto.año == año
            ).first()
            
            monto = np.random.randint(5000, int(presupuesto_dir.monto * 0.15))
            
            adq = Adquisicion(
                codigo=f"ADQ-{id_counter:04d}",
                direccion_id=dir.id,
                meta_id=meta.id,
                año=año,
                mes=mes_num,
                descripcion=f"{meta.nombre} - {dir.nombre[:20]}",
                monto=monto,
                estado=np.random.choice(['Completado', 'En Proceso', 'Pendiente'], p=[0.7, 0.2, 0.1])
            )
            db.add(adq)
            id_counter += 1
    
    db.commit()

def obtener_adquisiciones_df(db: Session):
    """Obtiene todas las adquisiciones como DataFrame"""
    adquisiciones = db.query(
        Adquisicion.codigo.label('ID'),
        Direccion.nombre.label('Dirección'),
        Meta.nombre.label('Meta'),
        Adquisicion.año.label('Año'),
        Adquisicion.mes.label('Mes_Num'),
        Adquisicion.descripcion.label('Descripción'),
        Adquisicion.monto.label('Monto'),
        Adquisicion.estado.label('Estado')
    ).join(Direccion).join(Meta).all()
    
    df = pd.DataFrame([{
        'ID': a.ID,
        'Dirección': a.Dirección,
        'Meta': a.Meta,
        'Año': a.Año,
        'Mes_Num': a.Mes_Num,
        'Mes': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][a.Mes_Num - 1],
        'Fecha': f"{a.Mes_Num:02d}/{a.Año}",
        'Descripción': a.Descripción,
        'Monto': a.Monto,
        'Estado': a.Estado
    } for a in adquisiciones])
    
    return df

def obtener_presupuestos_df(db: Session):
    """Obtiene todos los presupuestos como DataFrame"""
    presupuestos = db.query(
        Presupuesto.año.label('Año'),
        Direccion.nombre.label('Dirección'),
        Presupuesto.monto.label('Presupuesto')
    ).join(Direccion).all()
    
    df = pd.DataFrame([{
        'Año': p.Año,
        'Dirección': p.Dirección,
        'Presupuesto': p.Presupuesto
    } for p in presupuestos])
    
    return df

def cargar_datos_desde_archivo(db: Session, archivo, tipo_datos, formato='xlsx'):
    """Carga datos desde archivo Excel o CSV con validación"""
    try:
        if formato == 'csv' or archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)
    except Exception as e:
        raise ValueError(f"Error al leer el archivo: {str(e)}")
    
    if tipo_datos == "adquisiciones":
        columnas_requeridas = ['Código', 'Dirección', 'Meta', 'Año', 'Mes', 'Descripción', 'Monto', 'Estado']
        columnas_faltantes = set(columnas_requeridas) - set(df.columns)
        if columnas_faltantes:
            raise ValueError(f"Faltan columnas requeridas: {', '.join(columnas_faltantes)}")
        
        if df.empty:
            raise ValueError("El archivo no contiene datos")
        
        if not df['Mes'].between(1, 12).all():
            raise ValueError("El mes debe estar entre 1 y 12")
        
        estados_validos = ['Completado', 'En Proceso', 'Pendiente']
        if not df['Estado'].isin(estados_validos).all():
            raise ValueError(f"El estado debe ser uno de: {', '.join(estados_validos)}")
        
        for _, row in df.iterrows():
            direccion = db.query(Direccion).filter(Direccion.nombre == row['Dirección']).first()
            if not direccion:
                direccion = Direccion(nombre=row['Dirección'])
                db.add(direccion)
                db.commit()
            
            meta = db.query(Meta).filter(Meta.nombre == row['Meta']).first()
            if not meta:
                meta = Meta(nombre=row['Meta'])
                db.add(meta)
                db.commit()
            
            adq_existente = db.query(Adquisicion).filter(Adquisicion.codigo == row['Código']).first()
            if adq_existente:
                adq_existente.monto = float(row['Monto'])
                adq_existente.descripcion = row['Descripción']
                adq_existente.estado = row['Estado']
            else:
                adq = Adquisicion(
                    codigo=row['Código'],
                    direccion_id=direccion.id,
                    meta_id=meta.id,
                    año=int(row['Año']),
                    mes=int(row['Mes']),
                    descripcion=row['Descripción'],
                    monto=float(row['Monto']),
                    estado=row['Estado']
                )
                db.add(adq)
        db.commit()
        return True
    
    elif tipo_datos == "presupuestos":
        columnas_requeridas = ['Dirección', 'Año', 'Presupuesto']
        columnas_faltantes = set(columnas_requeridas) - set(df.columns)
        if columnas_faltantes:
            raise ValueError(f"Faltan columnas requeridas: {', '.join(columnas_faltantes)}")
        
        if df.empty:
            raise ValueError("El archivo no contiene datos")
        
        if (df['Presupuesto'] <= 0).any():
            raise ValueError("El presupuesto debe ser mayor a 0")
        
        for _, row in df.iterrows():
            direccion = db.query(Direccion).filter(Direccion.nombre == row['Dirección']).first()
            if not direccion:
                direccion = Direccion(nombre=row['Dirección'])
                db.add(direccion)
                db.commit()
            
            pres_existente = db.query(Presupuesto).filter(
                Presupuesto.direccion_id == direccion.id,
                Presupuesto.año == int(row['Año'])
            ).first()
            
            if pres_existente:
                pres_existente.monto = float(row['Presupuesto'])
            else:
                pres = Presupuesto(
                    direccion_id=direccion.id,
                    año=int(row['Año']),
                    monto=float(row['Presupuesto'])
                )
                db.add(pres)
        db.commit()
        return True
    
    return False

def cargar_datos_desde_excel(db: Session, archivo, tipo_datos):
    """Función legacy - usa cargar_datos_desde_archivo"""
    return cargar_datos_desde_archivo(db, archivo, tipo_datos, 'xlsx')

def obtener_alertas(db: Session):
    """Obtiene todas las alertas activas"""
    return db.query(Alerta).filter(Alerta.activo == True).all()

def crear_alerta(db: Session, nombre, direccion_id, umbral):
    """Crea una nueva alerta"""
    alerta = Alerta(
        nombre=nombre,
        direccion_id=direccion_id,
        umbral_porcentaje=umbral
    )
    db.add(alerta)
    db.commit()
    return alerta

def eliminar_alerta(db: Session, alerta_id):
    """Elimina una alerta"""
    alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
    if alerta:
        db.delete(alerta)
        db.commit()
        return True
    return False
