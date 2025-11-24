import pandas as pd
import re
from sqlalchemy.orm import Session
from database import UnidadEjecutora, MetaPresupuestal, ProgramacionPresupuestal, Adquisicion, AdquisicionDetalle, AdquisicionProceso, Alerta, SessionLocal
import numpy as np

def inicializar_datos_ejemplo(db: Session):
    """Inicializa la base de datos con datos de ejemplo si está vacía"""
    
    if db.query(UnidadEjecutora).count() > 0:
        return
    
    unidades_ejemplo = ['CIDE', 'DNCE', 'DNCN']
    
    for codigo in unidades_ejemplo:
        ue = UnidadEjecutora(codigo=codigo, nombre=f"Unidad {codigo}")
        db.add(ue)
    db.commit()

def procesar_archivo_programacion(db: Session, archivo, año: int):
    """
    Procesa un archivo Excel de programación anual y carga los datos en la BD
    
    Args:
        db: Sesión de base de datos
        archivo: Archivo Excel cargado
        año: Año de la programación
    
    Returns:
        Tuple (éxito: bool, mensaje: str)
    """
    try:
        df = pd.read_excel(archivo, skiprows=4)
        
        df.columns = ['Descripcion', 'PIM', 'CERTIFICADO', 'PIM_POR_CERTIFICAR', 'COMPROMISO_ANUAL', 
                      'DEVENGADO_ACUMULADO', 'COMPROMISO_ANUAL_POR_DEVENGAR', 'PIM_POR_DEVENGAR',
                      'NOV_Programacion', 'NOV_Ejecucion', 'NOV_Pendiente', 'DIC_Prog', 
                      'TOTAL_ANUAL', 'SALDO']
        
        df = df[df['Descripcion'] != 'ddnntt / meta / clasificador'].copy()
        df = df.dropna(subset=['Descripcion'])
        
        ue_actual = None
        meta_actual = None
        
        registros_creados = 0
        
        for idx, row in df.iterrows():
            desc = str(row['Descripcion']).strip()
            
            # Check for UE row first (UE rows have empty PIM)
            if re.match(r'^[A-Z]{3,5}$', desc):
                ue = db.query(UnidadEjecutora).filter(UnidadEjecutora.codigo == desc).first()
                if not ue:
                    ue = UnidadEjecutora(codigo=desc, nombre=f"Unidad {desc}")
                    db.add(ue)
                    db.commit()
                ue_actual = ue
                meta_actual = None
                continue
            
            # Check for Meta row (Meta rows also have empty PIM)
            if desc.startswith('0') and ' - ' in desc:
                partes = desc.split(' - ', 1)
                codigo_meta = partes[0].strip()
                descripcion_meta = partes[1].strip() if len(partes) > 1 else codigo_meta
                
                meta = db.query(MetaPresupuestal).filter(
                    MetaPresupuestal.codigo == codigo_meta
                ).first()
                
                if not meta:
                    meta = MetaPresupuestal(codigo=codigo_meta, descripcion=descripcion_meta)
                    db.add(meta)
                    db.commit()
                
                meta_actual = meta
                continue
            
            # Skip rows without PIM value (after checking for UE/Meta)
            if pd.isna(row['PIM']):
                continue
            
            # Skip if we don't have a UE context yet
            if ue_actual is None:
                continue
            
            clasificador = None
            descripcion_clasificador = desc
            if re.match(r'^\d+\.\s*\d+\.', desc):
                partes_clas = desc.split(' ', 1)
                clasificador = partes_clas[0].strip()
                descripcion_clasificador = partes_clas[1].strip() if len(partes_clas) > 1 else desc
            
            prog = ProgramacionPresupuestal(
                año=año,
                unidad_ejecutora_id=ue_actual.id,
                meta_id=meta_actual.id if meta_actual else None,
                clasificador=clasificador,
                descripcion_clasificador=descripcion_clasificador,
                pim=float(row['PIM']) if not pd.isna(row['PIM']) else 0,
                certificado=float(row['CERTIFICADO']) if not pd.isna(row['CERTIFICADO']) else 0,
                pim_por_certificar=float(row['PIM_POR_CERTIFICAR']) if not pd.isna(row['PIM_POR_CERTIFICAR']) else 0,
                compromiso_anual=float(row['COMPROMISO_ANUAL']) if not pd.isna(row['COMPROMISO_ANUAL']) else 0,
                devengado_acumulado=float(row['DEVENGADO_ACUMULADO']) if not pd.isna(row['DEVENGADO_ACUMULADO']) else 0,
                compromiso_por_devengar=float(row['COMPROMISO_ANUAL_POR_DEVENGAR']) if not pd.isna(row['COMPROMISO_ANUAL_POR_DEVENGAR']) else 0,
                pim_por_devengar=float(row['PIM_POR_DEVENGAR']) if not pd.isna(row['PIM_POR_DEVENGAR']) else 0,
                total_anual=float(row['TOTAL_ANUAL']) if not pd.isna(row['TOTAL_ANUAL']) else 0,
                saldo=float(row['SALDO']) if not pd.isna(row['SALDO']) else 0
            )
            
            db.add(prog)
            registros_creados += 1
        
        db.commit()
        return True, f"Se cargaron {registros_creados} registros exitosamente para el año {año}"
        
    except Exception as e:
        db.rollback()
        return False, f"Error al procesar archivo: {str(e)}"

def obtener_programacion_df(db: Session = None):
    """Obtiene todas las programaciones como DataFrame"""
    # Crear sesión propia si no se proporciona una
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        programaciones = db.query(
            ProgramacionPresupuestal.año.label('Año'),
            UnidadEjecutora.codigo.label('UE'),
            MetaPresupuestal.codigo.label('Meta_Codigo'),
            MetaPresupuestal.descripcion.label('Meta'),
            ProgramacionPresupuestal.clasificador.label('Clasificador'),
            ProgramacionPresupuestal.descripcion_clasificador.label('Descripción'),
            ProgramacionPresupuestal.pim.label('PIM'),
            ProgramacionPresupuestal.certificado.label('Certificado'),
            ProgramacionPresupuestal.pim_por_certificar.label('PIM_Por_Certificar'),
            ProgramacionPresupuestal.devengado_acumulado.label('Devengado'),
            ProgramacionPresupuestal.total_anual.label('Total_Anual'),
            ProgramacionPresupuestal.saldo.label('Saldo')
        ).join(UnidadEjecutora).outerjoin(MetaPresupuestal).all()
        
        df = pd.DataFrame([{
            'Año': p.Año,
            'UE': p.UE,
            'Meta_Codigo': p.Meta_Codigo if p.Meta_Codigo else '',
            'Meta': p.Meta if p.Meta else 'Sin Meta',
            'Clasificador': p.Clasificador if p.Clasificador else '',
            'Descripción': p.Descripción,
            'PIM': p.PIM,
            'Certificado': p.Certificado,
            'PIM_Por_Certificar': p.PIM_Por_Certificar,
            'Devengado': p.Devengado,
            'Total_Anual': p.Total_Anual,
            'Saldo': p.Saldo,
            'Ejecución_%': round((p.Certificado / p.PIM * 100) if p.PIM > 0 else 0, 2)
        } for p in programaciones])
        
        return df
    finally:
        if should_close:
            db.close()

def obtener_alertas(db: Session):
    """Obtiene todas las alertas activas"""
    return db.query(Alerta).filter(Alerta.activo == True).all()

def crear_alerta(db: Session, nombre: str, unidad_ejecutora_id: int = None, umbral: float = 80.0):
    """Crea una nueva alerta"""
    alerta = Alerta(
        nombre=nombre,
        unidad_ejecutora_id=unidad_ejecutora_id,
        umbral_porcentaje=umbral
    )
    db.add(alerta)
    db.commit()
    return alerta

def eliminar_alerta(db: Session, alerta_id: int):
    """Elimina una alerta"""
    alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
    if alerta:
        db.delete(alerta)
        db.commit()
        return True
    return False

def obtener_adquisiciones_df(db: Session = None):
    """Obtiene todas las adquisiciones como DataFrame"""
    # Crear sesión propia si no se proporciona una
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        adquisiciones = db.query(
            Adquisicion.año.label('Año'),
            UnidadEjecutora.codigo.label('UE'),
            UnidadEjecutora.nombre.label('UE_Nombre'),
            MetaPresupuestal.codigo.label('Meta_Codigo'),
            MetaPresupuestal.descripcion.label('Meta'),
            Adquisicion.codigo_adquisicion.label('Código'),
            Adquisicion.cantidad.label('Cantidad'),
            Adquisicion.descripcion.label('Descripción'),
            Adquisicion.tipo_proceso.label('Tipo_Proceso'),
            Adquisicion.estado.label('Estado'),
            Adquisicion.monto_referencial.label('Monto_Referencial'),
            Adquisicion.monto_adjudicado.label('Monto_Adjudicado'),
            Adquisicion.proveedor.label('Proveedor'),
            Adquisicion.fecha_convocatoria.label('Fecha_Convocatoria'),
            Adquisicion.fecha_adjudicacion.label('Fecha_Adjudicacion'),
            AdquisicionDetalle.tipo_servicio.label('Tipo_Servicio')
        ).join(UnidadEjecutora).outerjoin(MetaPresupuestal).outerjoin(
            AdquisicionDetalle, Adquisicion.id == AdquisicionDetalle.adquisicion_id
        ).all()

        df = pd.DataFrame([{
            'Año': a.Año,
            'UE': a.UE,
            'UE_Nombre': a.UE_Nombre,
            'Meta_Codigo': a.Meta_Codigo if a.Meta_Codigo else '',
            'Meta': a.Meta if a.Meta else 'Sin Meta',
            'Código': a.Código if a.Código else '',
            'Cantidad': a.Cantidad if a.Cantidad else 0,
            'Descripción': a.Descripción,
            'Tipo_Proceso': a.Tipo_Proceso if a.Tipo_Proceso else 'No especificado',
            'Estado': a.Estado,
            'Monto_Referencial': a.Monto_Referencial,
            'Monto_Adjudicado': a.Monto_Adjudicado,
            'Proveedor': a.Proveedor if a.Proveedor else 'Sin proveedor',
            'Fecha_Convocatoria': a.Fecha_Convocatoria,
            'Fecha_Adjudicacion': a.Fecha_Adjudicacion,
            'Avance_%': round((a.Monto_Adjudicado / a.Monto_Referencial * 100) if a.Monto_Referencial > 0 else 0, 2),
            'Tipo_Servicio': a.Tipo_Servicio if a.Tipo_Servicio else 'No especificado'
        } for a in adquisiciones])

        return df
    finally:
        if should_close:
            db.close()

def obtener_detalle_adquisicion(db: Session, codigo_adquisicion: str):
    """Obtiene el detalle completo de una adquisición por su código"""
    adq = db.query(Adquisicion).filter(Adquisicion.codigo_adquisicion == codigo_adquisicion).first()
    if not adq:
        return None
    
    detalle = db.query(AdquisicionDetalle).filter(AdquisicionDetalle.adquisicion_id == adq.id).first()
    procesos = db.query(AdquisicionProceso).filter(
        AdquisicionProceso.adquisicion_id == adq.id
    ).order_by(AdquisicionProceso.orden).all()
    
    return {
        'adquisicion': adq,
        'detalle': detalle,
        'procesos': procesos
    }

def obtener_procesos_df(db: Session, adquisicion_id: int):
    """Obtiene los procesos de una adquisición como DataFrame para visualización"""
    procesos = db.query(AdquisicionProceso).filter(
        AdquisicionProceso.adquisicion_id == adquisicion_id
    ).order_by(AdquisicionProceso.orden).all()
    
    df = pd.DataFrame([{
        'Orden': p.orden,
        'Hito': p.hito,
        'Tipo_Flujo': p.tipo_flujo,
        'Responsable': p.responsable_area,
        'Correo': p.responsable_correo if p.responsable_correo else '',
        'Fecha_Inicio': p.fecha_inicio,
        'Fecha_Fin': p.fecha_fin,
        'Dias': p.dias_transcurridos,
        'Comentarios': p.comentarios if p.comentarios else ''
    } for p in procesos])
    
    return df
