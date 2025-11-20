import random
from datetime import datetime, timedelta
from database import SessionLocal, Base, engine, UnidadEjecutora, MetaPresupuestal, ProgramacionPresupuestal, Adquisicion
from sqlalchemy import text

def crear_tablas():
    """Crea todas las tablas"""
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas")

def limpiar_base_datos():
    """Elimina todos los datos existentes"""
    with engine.connect() as conn:
        try:
            conn.execute(text("DELETE FROM adquisiciones"))
        except:
            pass
        try:
            conn.execute(text("DELETE FROM programacion_presupuestal"))
        except:
            pass
        try:
            conn.execute(text("DELETE FROM alertas"))
        except:
            pass
        try:
            conn.execute(text("DELETE FROM metas_presupuestales"))
        except:
            pass
        try:
            conn.execute(text("DELETE FROM unidades_ejecutoras"))
        except:
            pass
        conn.commit()
    print("✅ Base de datos limpiada")

def generar_unidades_ejecutoras(db):
    """Genera las Unidades Ejecutoras"""
    unidades = [
        {"codigo": "CIDE", "nombre": "Centro de Innovación y Desarrollo Empresarial"},
        {"codigo": "DNCE", "nombre": "Dirección Nacional de Cooperación Empresarial"},
        {"codigo": "DNCN", "nombre": "Dirección Nacional de Competitividad y Normalización"},
        {"codigo": "DTDIS", "nombre": "Dirección Técnica de Desarrollo e Innovación Social"},
        {"codigo": "DTIE", "nombre": "Dirección Técnica de Infraestructura Económica"},
        {"codigo": "ENEI", "nombre": "Escuela Nacional de Emprendimiento e Innovación"},
        {"codigo": "OTA", "nombre": "Oficina Técnica de Administración"},
        {"codigo": "OTAJ", "nombre": "Oficina Técnica de Asesoría Jurídica"},
        {"codigo": "OTD", "nombre": "Oficina Técnica de Desarrollo"},
        {"codigo": "OTED", "nombre": "Oficina Técnica de Educación"},
        {"codigo": "OTIN", "nombre": "Oficina Técnica de Informática"},
        {"codigo": "OTPP", "nombre": "Oficina Técnica de Planeamiento y Presupuesto"}
    ]
    
    ues_dict = {}
    for u in unidades:
        ue = UnidadEjecutora(codigo=u["codigo"], nombre=u["nombre"])
        db.add(ue)
        ues_dict[u["codigo"]] = ue
    
    db.commit()
    print(f"✅ {len(unidades)} Unidades Ejecutoras creadas")
    return ues_dict

def generar_metas_presupuestales(db):
    """Genera las Metas Presupuestales"""
    metas = [
        {"codigo": "0001", "descripcion": "Gestión Administrativa"},
        {"codigo": "0013", "descripcion": "Desarrollo de la Competitividad Empresarial"},
        {"codigo": "0046", "descripcion": "Fortalecimiento de la Innovación Tecnológica"},
        {"codigo": "0078", "descripcion": "Promoción de las Exportaciones"},
        {"codigo": "0092", "descripcion": "Desarrollo de las MIPYMES"},
        {"codigo": "0104", "descripcion": "Capacitación y Asistencia Técnica"},
        {"codigo": "0115", "descripcion": "Infraestructura Productiva"},
        {"codigo": "0128", "descripcion": "Investigación y Desarrollo"},
        {"codigo": "0139", "descripcion": "Normalización y Calidad"},
        {"codigo": "0145", "descripcion": "Propiedad Intelectual"},
    ]
    
    metas_dict = {}
    for m in metas:
        meta = MetaPresupuestal(codigo=m["codigo"], descripcion=m["descripcion"])
        db.add(meta)
        metas_dict[m["codigo"]] = meta
    
    db.commit()
    print(f"✅ {len(metas)} Metas Presupuestales creadas")
    return metas_dict

def generar_programacion_presupuestal(db, ues_dict, metas_dict, año):
    """Genera datos de Programación Presupuestal para un año"""
    clasificadores = [
        "2.1. Personal y Obligaciones Sociales",
        "2.3. Bienes y Servicios",
        "2.5. Otros Gastos",
        "2.6. Adquisición de Activos",
        "3.1. Transferencias Corrientes",
        "3.2. Transferencias de Capital"
    ]
    
    registros = []
    for ue_codigo, ue in ues_dict.items():
        for meta_codigo, meta in metas_dict.items():
            num_clasificadores = random.randint(3, 6)
            for _ in range(num_clasificadores):
                clasificador = random.choice(clasificadores)
                pim = random.uniform(50000, 5000000)
                ejecucion_pct = random.uniform(0.65, 0.99)
                certificado = pim * ejecucion_pct
                
                prog = ProgramacionPresupuestal(
                    año=año,
                    unidad_ejecutora_id=ue.id,
                    meta_id=meta.id,
                    clasificador=clasificador.split('.')[0],
                    descripcion_clasificador=clasificador,
                    pim=pim,
                    certificado=certificado,
                    pim_por_certificar=pim - certificado,
                    compromiso_anual=certificado * random.uniform(0.95, 1.0),
                    devengado_acumulado=certificado * random.uniform(0.85, 0.95),
                    compromiso_por_devengar=certificado * random.uniform(0.05, 0.15),
                    pim_por_devengar=pim - certificado,
                    total_anual=pim,
                    saldo=pim - certificado
                )
                registros.append(prog)
    
    db.add_all(registros)
    db.commit()
    print(f"✅ {len(registros)} registros de Programación Presupuestal para {año}")
    return len(registros)

def generar_adquisiciones(db, ues_dict, metas_dict, año):
    """Genera datos de Adquisiciones para un año"""
    tipos_proceso = [
        "Licitación Pública",
        "Concurso Público",
        "Adjudicación Simplificada",
        "Selección de Consultores",
        "Comparación de Precios",
        "Subasta Inversa Electrónica"
    ]
    
    estados = [
        "Convocado",
        "En Evaluación",
        "Adjudicado",
        "Contratado",
        "En Ejecución",
        "Finalizado",
        "Cancelado",
        "Desierto"
    ]
    
    descripciones = [
        "Adquisición de equipos de cómputo",
        "Servicio de mantenimiento de infraestructura",
        "Consultoría para desarrollo de sistemas",
        "Adquisición de mobiliario de oficina",
        "Servicio de capacitación y formación",
        "Adquisición de vehículos",
        "Servicio de consultoría especializada",
        "Adquisición de suministros de oficina",
        "Servicio de limpieza y mantenimiento",
        "Adquisición de software empresarial",
        "Servicio de seguridad y vigilancia",
        "Obra de remodelación de oficinas"
    ]
    
    proveedores = [
        "Tech Solutions SAC",
        "Servicios Integrales del Perú SRL",
        "Consultores Asociados EIRL",
        "Grupo Empresarial del Sur SA",
        "Innovación y Desarrollo SAC",
        "Soluciones Corporativas SAC"
    ]
    
    registros = []
    for ue_codigo, ue in ues_dict.items():
        num_adquisiciones = random.randint(15, 35)
        for i in range(num_adquisiciones):
            meta = random.choice(list(metas_dict.values()))
            estado = random.choice(estados)
            monto_ref = random.uniform(10000, 500000)
            
            if estado in ["Adjudicado", "Contratado", "En Ejecución", "Finalizado"]:
                monto_adj = monto_ref * random.uniform(0.85, 0.98)
            else:
                monto_adj = 0
            
            fecha_conv = datetime(año, random.randint(1, 12), random.randint(1, 28))
            fecha_adj = None
            if estado in ["Adjudicado", "Contratado", "En Ejecución", "Finalizado"]:
                fecha_adj = fecha_conv + timedelta(days=random.randint(15, 60))
            
            adq = Adquisicion(
                año=año,
                unidad_ejecutora_id=ue.id,
                meta_id=meta.id,
                codigo_adquisicion=f"ADQ-{año}-{ue_codigo}-{i+1:04d}",
                descripcion=random.choice(descripciones),
                tipo_proceso=random.choice(tipos_proceso),
                estado=estado,
                monto_referencial=monto_ref,
                monto_adjudicado=monto_adj,
                fecha_convocatoria=fecha_conv,
                fecha_adjudicacion=fecha_adj,
                proveedor=random.choice(proveedores) if monto_adj > 0 else None
            )
            registros.append(adq)
    
    db.add_all(registros)
    db.commit()
    print(f"✅ {len(registros)} registros de Adquisiciones para {año}")
    return len(registros)

def main():
    """Función principal para generar datos seed"""
    print("\n🌱 Generando datos seed...\n")
    
    crear_tablas()
    limpiar_base_datos()
    
    db = SessionLocal()
    try:
        ues_dict = generar_unidades_ejecutoras(db)
        metas_dict = generar_metas_presupuestales(db)
        
        total_prog_2024 = generar_programacion_presupuestal(db, ues_dict, metas_dict, 2024)
        total_prog_2025 = generar_programacion_presupuestal(db, ues_dict, metas_dict, 2025)
        
        total_adq_2024 = generar_adquisiciones(db, ues_dict, metas_dict, 2024)
        total_adq_2025 = generar_adquisiciones(db, ues_dict, metas_dict, 2025)
        
        print(f"\n📊 Resumen:")
        print(f"   - {len(ues_dict)} Unidades Ejecutoras")
        print(f"   - {len(metas_dict)} Metas Presupuestales")
        print(f"   - {total_prog_2024 + total_prog_2025} Programaciones Presupuestales")
        print(f"   - {total_adq_2024 + total_adq_2025} Adquisiciones")
        print(f"\n✅ Datos seed generados exitosamente!\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
