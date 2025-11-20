import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.units import inch
import xlsxwriter
from database import SessionLocal, init_db, Direccion, Meta
from db_operations import inicializar_datos_ejemplo, obtener_adquisiciones_df, obtener_presupuestos_df, cargar_datos_desde_archivo, obtener_alertas, crear_alerta, eliminar_alerta

st.set_page_config(page_title="Dashboard de Adquisiciones", layout="wide", initial_sidebar_state="expanded")

init_db()

@st.cache_resource
def get_db_session():
    return SessionLocal()

@st.cache_data(ttl=60)
def cargar_datos():
    """Carga datos desde la base de datos"""
    db = SessionLocal()
    try:
        inicializar_datos_ejemplo(db)
        df_adquisiciones = obtener_adquisiciones_df(db)
        df_presupuestos = obtener_presupuestos_df(db)
        return df_adquisiciones, df_presupuestos
    finally:
        db.close()

df_adquisiciones, df_presupuestos = cargar_datos()
df_comparacion = pd.DataFrame()

st.title("📊 Dashboard de Control de Adquisiciones")

tabs = st.tabs(["📈 Dashboard Principal", "📤 Importar/Exportar", "⚠️ Alertas", "📊 Comparativas", "🔮 Proyecciones"])

with tabs[0]:
    st.markdown("---")
    
    st.sidebar.header("🔍 Filtros")
    
    años_disponibles = sorted(df_adquisiciones['Año'].unique())
    año_seleccionado = st.sidebar.selectbox(
        "Seleccionar Año",
        options=["Todos"] + años_disponibles,
        index=0
    )
    
    direcciones_disponibles = sorted(df_adquisiciones['Dirección'].unique())
    direccion_seleccionada = st.sidebar.multiselect(
        "Seleccionar Dirección/Área",
        options=direcciones_disponibles,
        default=direcciones_disponibles
    )
    
    metas_disponibles = sorted(df_adquisiciones['Meta'].unique())
    meta_seleccionada = st.sidebar.multiselect(
        "Seleccionar Meta",
        options=metas_disponibles,
        default=metas_disponibles
    )
    
    estados_disponibles = df_adquisiciones['Estado'].unique()
    estado_seleccionado = st.sidebar.multiselect(
        "Seleccionar Estado",
        options=estados_disponibles,
        default=estados_disponibles
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Usa los filtros para explorar los datos de adquisiciones por año, dirección y meta.")
    
    df_filtrado = df_adquisiciones.copy()
    
    if año_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Año'] == año_seleccionado]
    
    if direccion_seleccionada:
        df_filtrado = df_filtrado[df_filtrado['Dirección'].isin(direccion_seleccionada)]
    
    if meta_seleccionada:
        df_filtrado = df_filtrado[df_filtrado['Meta'].isin(meta_seleccionada)]
    
    if estado_seleccionado:
        df_filtrado = df_filtrado[df_filtrado['Estado'].isin(estado_seleccionado)]
    
    st.header("📈 Resumen Ejecutivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_adquisiciones = len(df_filtrado)
        st.metric(
            label="Total Adquisiciones",
            value=f"{total_adquisiciones:,}",
            delta=f"{len(df_filtrado[df_filtrado['Estado'] == 'Completado'])} completadas"
        )
    
    with col2:
        monto_total = df_filtrado['Monto'].sum()
        st.metric(
            label="Gasto Total",
            value=f"S/ {monto_total:,.0f}",
            delta=f"{(monto_total/1000000):.1f}M"
        )
    
    with col3:
        if año_seleccionado != "Todos":
            df_pres_filtrado = df_presupuestos[df_presupuestos['Año'] == año_seleccionado]
        else:
            df_pres_filtrado = df_presupuestos
        
        if direccion_seleccionada:
            df_pres_filtrado = df_pres_filtrado[df_pres_filtrado['Dirección'].isin(direccion_seleccionada)]
        
        presupuesto_total = df_pres_filtrado['Presupuesto'].sum()
        st.metric(
            label="Presupuesto Total",
            value=f"S/ {presupuesto_total:,.0f}",
            delta=f"{(presupuesto_total/1000000):.1f}M"
        )
    
    with col4:
        porcentaje_ejecutado = (monto_total / presupuesto_total * 100) if presupuesto_total > 0 else 0
        delta_color = "normal" if porcentaje_ejecutado <= 100 else "inverse"
        st.metric(
            label="% Ejecutado",
            value=f"{porcentaje_ejecutado:.1f}%",
            delta=f"{porcentaje_ejecutado - 100:.1f}% vs presupuesto",
            delta_color=delta_color
        )
    
    st.markdown("---")
    
    st.header("🏢 Análisis por Dirección/Área")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gasto_por_dir = df_filtrado.groupby('Dirección')['Monto'].sum().reset_index()
        gasto_por_dir = gasto_por_dir.sort_values('Monto', ascending=False)
        
        fig_dir = px.bar(
            gasto_por_dir,
            x='Monto',
            y='Dirección',
            orientation='h',
            title="Gasto Total por Dirección",
            labels={'Monto': 'Monto (S/)', 'Dirección': 'Dirección'},
            color='Monto',
            color_continuous_scale='Blues'
        )
        fig_dir.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_dir, width='stretch')
    
    with col2:
        adq_por_dir = df_filtrado.groupby('Dirección').size().reset_index(name='Cantidad')
        adq_por_dir = adq_por_dir.sort_values('Cantidad', ascending=False)
        
        fig_adq_dir = px.bar(
            adq_por_dir,
            x='Cantidad',
            y='Dirección',
            orientation='h',
            title="Número de Adquisiciones por Dirección",
            labels={'Cantidad': 'Cantidad', 'Dirección': 'Dirección'},
            color='Cantidad',
            color_continuous_scale='Greens'
        )
        fig_adq_dir.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_adq_dir, width='stretch')
    
    st.markdown("---")
    
    st.header("💰 Presupuesto vs Gasto por Dirección")
    
    if año_seleccionado != "Todos":
        años_analisis = [año_seleccionado]
    else:
        años_analisis = años_disponibles
    
    datos_comparacion = []
    for año in años_analisis:
        for direccion in direccion_seleccionada if direccion_seleccionada else direcciones_disponibles:
            gasto = df_filtrado[
                (df_filtrado['Año'] == año) & 
                (df_filtrado['Dirección'] == direccion)
            ]['Monto'].sum()
            
            presupuesto_data = df_presupuestos[
                (df_presupuestos['Año'] == año) & 
                (df_presupuestos['Dirección'] == direccion)
            ]['Presupuesto'].values
            
            if len(presupuesto_data) > 0:
                presupuesto = presupuesto_data[0]
                porcentaje = (gasto / presupuesto * 100) if presupuesto > 0 else 0
                
                datos_comparacion.append({
                    'Año': año,
                    'Dirección': direccion,
                    'Presupuesto': presupuesto,
                    'Gasto': gasto,
                    'Disponible': presupuesto - gasto,
                    'Porcentaje': porcentaje
                })
    
    df_comparacion = pd.DataFrame(datos_comparacion)
    
    if len(df_comparacion) > 0:
        fig_comp = go.Figure()
    
        fig_comp.add_trace(go.Bar(
            name='Presupuesto',
            x=df_comparacion['Dirección'] + ' - ' + df_comparacion['Año'].astype(str),
            y=df_comparacion['Presupuesto'],
            marker_color='lightblue'
        ))
    
        fig_comp.add_trace(go.Bar(
            name='Gasto',
            x=df_comparacion['Dirección'] + ' - ' + df_comparacion['Año'].astype(str),
            y=df_comparacion['Gasto'],
            marker_color='darkblue'
        ))
    
        fig_comp.update_layout(
            title='Comparación Presupuesto vs Gasto Real',
            xaxis_title='Dirección - Año',
            yaxis_title='Monto (S/)',
            barmode='group',
            height=500,
            xaxis_tickangle=-45
        )
    
        st.plotly_chart(fig_comp, width='stretch')
    
        st.subheader("📊 Indicadores de Estatus por Dirección")
    
        def obtener_estatus(porcentaje):
            if porcentaje < 75:
                return "✅ Dentro de Presupuesto"
            elif porcentaje < 95:
                return "⚠️ En Riesgo"
            else:
                return "🚨 Excedido/Crítico"
    
        df_comparacion['Estatus'] = df_comparacion['Porcentaje'].apply(obtener_estatus)
    
        df_tabla = df_comparacion.copy()
        df_tabla['Presupuesto'] = df_tabla['Presupuesto'].apply(lambda x: f"S/ {x:,.0f}")
        df_tabla['Gasto'] = df_tabla['Gasto'].apply(lambda x: f"S/ {x:,.0f}")
        df_tabla['Disponible'] = df_tabla['Disponible'].apply(lambda x: f"S/ {x:,.0f}")
        df_tabla['Porcentaje'] = df_tabla['Porcentaje'].apply(lambda x: f"{x:.1f}%")
    
        st.dataframe(
            df_tabla[['Año', 'Dirección', 'Presupuesto', 'Gasto', 'Disponible', 'Porcentaje', 'Estatus']],
            width='stretch',
            hide_index=True
        )
    else:
        st.info("ℹ️ No hay datos disponibles para las direcciones y años seleccionados con los filtros actuales.")
    
    st.markdown("---")
    
    st.header("🎯 Análisis por Meta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gasto_por_meta = df_filtrado.groupby('Meta')['Monto'].sum().reset_index()
        
        fig_meta_pie = px.pie(
            gasto_por_meta,
            values='Monto',
            names='Meta',
            title='Distribución de Gasto por Meta',
            hole=0.4
        )
        fig_meta_pie.update_layout(height=400)
        st.plotly_chart(fig_meta_pie, width='stretch')
    
    with col2:
        gasto_por_meta_sorted = gasto_por_meta.sort_values('Monto', ascending=False)
        
        fig_meta_bar = px.bar(
            gasto_por_meta_sorted,
            x='Meta',
            y='Monto',
            title='Gasto Total por Meta',
            labels={'Monto': 'Monto (S/)', 'Meta': 'Meta'},
            color='Monto',
            color_continuous_scale='Oranges'
        )
        fig_meta_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_meta_bar, width='stretch')
    
    st.markdown("---")
    
    st.header("📅 Tendencias Temporales")
    
    if año_seleccionado == "Todos":
        gasto_por_año = df_filtrado.groupby('Año')['Monto'].sum().reset_index()
        
        fig_año = px.line(
            gasto_por_año,
            x='Año',
            y='Monto',
            title='Evolución del Gasto por Año',
            markers=True,
            labels={'Monto': 'Monto (S/)', 'Año': 'Año'}
        )
        fig_año.update_traces(line_color='#1f77b4', marker_size=10)
        fig_año.update_layout(height=400)
        st.plotly_chart(fig_año, width='stretch')
        
        df_filtrado_mensual = df_filtrado.copy()
        df_filtrado_mensual['Año-Mes'] = df_filtrado_mensual['Año'].astype(str) + '-' + df_filtrado_mensual['Mes_Num'].astype(str).str.zfill(2)
        gasto_mensual = df_filtrado_mensual.groupby(['Año', 'Mes', 'Mes_Num'])['Monto'].sum().reset_index()
        gasto_mensual = gasto_mensual.sort_values(['Año', 'Mes_Num'])
        gasto_mensual['Periodo'] = gasto_mensual['Mes'] + ' ' + gasto_mensual['Año'].astype(str)
        
        fig_mensual = px.line(
            gasto_mensual,
            x='Periodo',
            y='Monto',
            color='Año',
            title='Evolución Mensual del Gasto',
            markers=True,
            labels={'Monto': 'Monto (S/)', 'Periodo': 'Periodo'}
        )
        fig_mensual.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_mensual, width='stretch')
    else:
        df_año = df_filtrado[df_filtrado['Año'] == año_seleccionado].copy()
        gasto_mensual_año = df_año.groupby(['Mes', 'Mes_Num'])['Monto'].sum().reset_index()
        gasto_mensual_año = gasto_mensual_año.sort_values('Mes_Num')
        
        fig_mensual_año = px.bar(
            gasto_mensual_año,
            x='Mes',
            y='Monto',
            title=f'Gasto Mensual - Año {año_seleccionado}',
            labels={'Monto': 'Monto (S/)', 'Mes': 'Mes'},
            color='Monto',
            color_continuous_scale='Viridis'
        )
        fig_mensual_año.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_mensual_año, width='stretch')
    
    st.markdown("---")
    
    st.header("📋 Detalle de Adquisiciones")
    
    busqueda = st.text_input("🔎 Buscar en descripción o ID:", "")
    
    df_tabla_detalle = df_filtrado.copy()
    
    if busqueda:
        df_tabla_detalle = df_tabla_detalle[
            df_tabla_detalle['ID'].str.contains(busqueda, case=False, na=False) |
            df_tabla_detalle['Descripción'].str.contains(busqueda, case=False, na=False)
        ]
    
    df_tabla_detalle = df_tabla_detalle.sort_values('Monto', ascending=False)
    
    df_tabla_display = df_tabla_detalle[['ID', 'Dirección', 'Meta', 'Año', 'Mes', 'Descripción', 'Monto', 'Estado']].copy()
    df_tabla_display['Monto'] = df_tabla_display['Monto'].apply(lambda x: f"S/ {x:,.0f}")
    
    st.dataframe(
        df_tabla_display,
        width='stretch',
        hide_index=True,
        height=400
    )
    
    st.caption(f"Mostrando {len(df_tabla_detalle)} de {len(df_adquisiciones)} adquisiciones totales")

with tabs[1]:
    st.header("📤 Importar y Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Importar Datos")
        
        tipo_importacion = st.selectbox(
            "Tipo de datos a importar",
            ["adquisiciones", "presupuestos"]
        )
        
        st.info(f"""
        **Formato requerido para {tipo_importacion}:**
        
        {"- Código, Dirección, Meta, Año, Mes, Descripción, Monto, Estado" if tipo_importacion == "adquisiciones" else "- Dirección, Año, Presupuesto"}
        """)
        
        archivo_carga = st.file_uploader(
            "Cargar archivo Excel (.xlsx) o CSV (.csv)",
            type=['xlsx', 'csv'],
            key="file_uploader"
        )
        
        if archivo_carga and st.button("Importar Datos"):
            try:
                db = SessionLocal()
                formato = 'csv' if archivo_carga.name.endswith('.csv') else 'xlsx'
                if cargar_datos_desde_archivo(db, archivo_carga, tipo_importacion, formato):
                    st.success(f"✅ Datos de {tipo_importacion} importados exitosamente")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ Error al importar datos")
                db.close()
            except ValueError as e:
                st.error(f"❌ Error de validación: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("📤 Exportar Reportes")
        
        formato_exportacion = st.selectbox(
            "Formato de exportación",
            ["Excel", "PDF"]
        )
        
        if st.button("Generar Reporte"):
            if formato_exportacion == "Excel":
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    
                    df_adquisiciones.to_excel(writer, sheet_name='Adquisiciones', index=False)
                    df_presupuestos.to_excel(writer, sheet_name='Presupuestos', index=False)
                    
                    if len(df_comparacion) > 0:
                        df_comparacion.to_excel(writer, sheet_name='Comparativa', index=False)
                    
                    gasto_por_dir = df_adquisiciones.groupby('Dirección')['Monto'].sum().reset_index()
                    gasto_por_dir = gasto_por_dir.sort_values('Monto', ascending=False)
                    gasto_por_meta = df_adquisiciones.groupby('Meta')['Monto'].sum().reset_index()
                    
                    gasto_por_dir.to_excel(writer, sheet_name='Datos_Gráficos', index=False, startrow=0, startcol=0)
                    gasto_por_meta.to_excel(writer, sheet_name='Datos_Gráficos', index=False, startrow=len(gasto_por_dir)+2, startcol=0)
                    
                    graficos_sheet = workbook.add_worksheet('Gráficos')
                    
                    chart1 = workbook.add_chart({'type': 'column'})
                    chart1.add_series({
                        'name': 'Gasto por Dirección',
                        'categories': ['Datos_Gráficos', 1, 0, len(gasto_por_dir), 0],
                        'values': ['Datos_Gráficos', 1, 1, len(gasto_por_dir), 1],
                    })
                    chart1.set_title({'name': 'Gasto Total por Dirección'})
                    chart1.set_x_axis({'name': 'Dirección'})
                    chart1.set_y_axis({'name': 'Monto (S/)'})
                    chart1.set_legend({'position': 'none'})
                    chart1.set_size({'width': 600, 'height': 400})
                    
                    graficos_sheet.insert_chart('B2', chart1)
                    
                    chart2 = workbook.add_chart({'type': 'pie'})
                    chart2.add_series({
                        'name': 'Gasto por Meta',
                        'categories': ['Datos_Gráficos', len(gasto_por_dir)+3, 0, len(gasto_por_dir)+len(gasto_por_meta)+2, 0],
                        'values': ['Datos_Gráficos', len(gasto_por_dir)+3, 1, len(gasto_por_dir)+len(gasto_por_meta)+2, 1],
                    })
                    chart2.set_title({'name': 'Distribución de Gasto por Meta'})
                    chart2.set_size({'width': 600, 'height': 400})
                    
                    graficos_sheet.insert_chart('K2', chart2)
                
                output.seek(0)
                st.download_button(
                    label="⬇️ Descargar Reporte Excel con Gráficos",
                    data=output,
                    file_name=f"reporte_adquisiciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            elif formato_exportacion == "PDF":
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                story = []
                styles = getSampleStyleSheet()
                
                story.append(Paragraph("Reporte de Adquisiciones", styles['Title']))
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
                
                story.append(Paragraph("Resumen Ejecutivo", styles['Heading1']))
                data_resumen = [
                    ['Métrica', 'Valor'],
                    ['Total Adquisiciones', f"{len(df_adquisiciones):,}"],
                    ['Gasto Total', f"S/ {df_adquisiciones['Monto'].sum():,.0f}"],
                    ['Presupuesto Total', f"S/ {df_presupuestos['Presupuesto'].sum():,.0f}"]
                ]
                
                tabla_resumen = Table(data_resumen)
                tabla_resumen.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(tabla_resumen)
                story.append(Spacer(1, 0.2*inch))
                
                story.append(PageBreak())
                story.append(Paragraph("Análisis de Gasto por Dirección", styles['Heading1']))
                story.append(Spacer(1, 0.2*inch))
                
                gasto_por_dir = df_adquisiciones.groupby('Dirección')['Monto'].sum().reset_index()
                gasto_por_dir = gasto_por_dir.sort_values('Monto', ascending=False)
                
                fig_dir = px.bar(
                    gasto_por_dir,
                    x='Monto',
                    y='Dirección',
                    orientation='h',
                    title="Gasto Total por Dirección",
                    labels={'Monto': 'Monto (S/)', 'Dirección': 'Dirección'}
                )
                
                img_bytes = fig_dir.to_image(format="png", width=600, height=400)
                img_buffer = io.BytesIO(img_bytes)
                img = Image(img_buffer, width=5*inch, height=3.3*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
                
                story.append(PageBreak())
                story.append(Paragraph("Distribución de Gasto por Meta", styles['Heading1']))
                story.append(Spacer(1, 0.2*inch))
                
                gasto_por_meta = df_adquisiciones.groupby('Meta')['Monto'].sum().reset_index()
                fig_meta = px.pie(
                    gasto_por_meta,
                    values='Monto',
                    names='Meta',
                    title='Distribución de Gasto por Meta'
                )
                
                img_bytes_meta = fig_meta.to_image(format="png", width=600, height=400)
                img_buffer_meta = io.BytesIO(img_bytes_meta)
                img_meta = Image(img_buffer_meta, width=5*inch, height=3.3*inch)
                story.append(img_meta)
                
                doc.build(story)
                buffer.seek(0)
                
                st.download_button(
                    label="⬇️ Descargar Reporte PDF con Gráficos",
                    data=buffer,
                    file_name=f"reporte_adquisiciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )

with tabs[2]:
    st.header("⚠️ Alertas de Presupuesto")
    
    db = get_db_session()
    alertas = obtener_alertas(db)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Alertas Activas")
        if alertas:
            for alerta in alertas:
                direccion_nombre = "Todas" if not alerta.direccion_id else db.query(Direccion).filter(Direccion.id == alerta.direccion_id).first().nombre
                
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.info(f"🔔 **{alerta.nombre}** - Dirección: {direccion_nombre} - Umbral: {alerta.umbral_porcentaje}%")
                with col_b:
                    if st.button("Eliminar", key=f"del_{alerta.id}"):
                        eliminar_alerta(db, alerta.id)
                        st.rerun()
        else:
            st.info("No hay alertas configuradas")
    
    with col2:
        st.subheader("Nueva Alerta")
        nombre_alerta = st.text_input("Nombre de la alerta")
        direccion_alerta = st.selectbox(
            "Dirección",
            ["Todas"] + direcciones_disponibles
        )
        umbral_alerta = st.slider("Umbral de presupuesto (%)", 50, 100, 80)
        
        if st.button("Crear Alerta"):
            if nombre_alerta:
                dir_id = None
                if direccion_alerta != "Todas":
                    dir_obj = db.query(Direccion).filter(Direccion.nombre == direccion_alerta).first()
                    dir_id = dir_obj.id if dir_obj else None
                
                crear_alerta(db, nombre_alerta, dir_id, umbral_alerta)
                st.success("✅ Alerta creada")
                st.rerun()
    
    st.markdown("---")
    st.subheader("🚨 Alertas Activadas")
    
    alertas_activadas = []
    for alerta in alertas:
        if alerta.direccion_id:
            direccion_obj = db.query(Direccion).filter(Direccion.id == alerta.direccion_id).first()
            if direccion_obj:
                for año in años_disponibles:
                    gasto = df_adquisiciones[
                        (df_adquisiciones['Año'] == año) & 
                        (df_adquisiciones['Dirección'] == direccion_obj.nombre)
                    ]['Monto'].sum()
                    
                    presupuesto_data = df_presupuestos[
                        (df_presupuestos['Año'] == año) & 
                        (df_presupuestos['Dirección'] == direccion_obj.nombre)
                    ]['Presupuesto'].values
                    
                    if len(presupuesto_data) > 0:
                        presupuesto = presupuesto_data[0]
                        porcentaje = (gasto / presupuesto * 100) if presupuesto > 0 else 0
                        
                        if porcentaje >= alerta.umbral_porcentaje:
                            alertas_activadas.append({
                                'Alerta': alerta.nombre,
                                'Dirección': direccion_obj.nombre,
                                'Año': año,
                                'Porcentaje': f"{porcentaje:.1f}%",
                                'Umbral': f"{alerta.umbral_porcentaje}%"
                            })
    
    if alertas_activadas:
        df_alertas = pd.DataFrame(alertas_activadas)
        st.warning(f"⚠️ Se encontraron {len(alertas_activadas)} alertas activadas")
        st.dataframe(df_alertas, width='stretch', hide_index=True)
    else:
        st.success("✅ No hay alertas activadas en este momento")

with tabs[3]:
    st.header("📊 Comparativas Año contra Año")
    
    if len(años_disponibles) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            año_base = st.selectbox("Año Base", años_disponibles[:-1])
        with col2:
            año_comparacion = st.selectbox("Año Comparación", [a for a in años_disponibles if a > año_base])
        
        df_año_base = df_adquisiciones[df_adquisiciones['Año'] == año_base]
        df_año_comp = df_adquisiciones[df_adquisiciones['Año'] == año_comparacion]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            gasto_base = df_año_base['Monto'].sum()
            gasto_comp = df_año_comp['Monto'].sum()
            variacion = ((gasto_comp - gasto_base) / gasto_base * 100) if gasto_base > 0 else 0
            
            st.metric(
                label=f"Gasto Total {año_base}",
                value=f"S/ {gasto_base:,.0f}"
            )
        
        with col2:
            st.metric(
                label=f"Gasto Total {año_comparacion}",
                value=f"S/ {gasto_comp:,.0f}"
            )
        
        with col3:
            st.metric(
                label="Variación",
                value=f"{variacion:+.1f}%",
                delta=f"S/ {(gasto_comp - gasto_base):,.0f}"
            )
        
        st.markdown("---")
        
        st.subheader("Variación por Dirección")
        
        datos_variacion = []
        for direccion in direcciones_disponibles:
            gasto_dir_base = df_año_base[df_año_base['Dirección'] == direccion]['Monto'].sum()
            gasto_dir_comp = df_año_comp[df_año_comp['Dirección'] == direccion]['Monto'].sum()
            var_dir = ((gasto_dir_comp - gasto_dir_base) / gasto_dir_base * 100) if gasto_dir_base > 0 else 0
            
            datos_variacion.append({
                'Dirección': direccion,
                f'{año_base}': gasto_dir_base,
                f'{año_comparacion}': gasto_dir_comp,
                'Variación %': var_dir,
                'Diferencia': gasto_dir_comp - gasto_dir_base
            })
        
        df_variacion = pd.DataFrame(datos_variacion)
        
        fig_variacion = go.Figure()
        fig_variacion.add_trace(go.Bar(
            name=str(año_base),
            x=df_variacion['Dirección'],
            y=df_variacion[f'{año_base}'],
            marker_color='lightblue'
        ))
        fig_variacion.add_trace(go.Bar(
            name=str(año_comparacion),
            x=df_variacion['Dirección'],
            y=df_variacion[f'{año_comparacion}'],
            marker_color='darkblue'
        ))
        
        fig_variacion.update_layout(
            title=f'Comparación de Gasto {año_base} vs {año_comparacion}',
            barmode='group',
            height=400
        )
        st.plotly_chart(fig_variacion, width='stretch')
        
        df_tabla_var = df_variacion.copy()
        df_tabla_var[f'{año_base}'] = df_tabla_var[f'{año_base}'].apply(lambda x: f"S/ {x:,.0f}")
        df_tabla_var[f'{año_comparacion}'] = df_tabla_var[f'{año_comparacion}'].apply(lambda x: f"S/ {x:,.0f}")
        df_tabla_var['Diferencia'] = df_tabla_var['Diferencia'].apply(lambda x: f"S/ {x:,.0f}")
        df_tabla_var['Variación %'] = df_tabla_var['Variación %'].apply(lambda x: f"{x:+.1f}%")
        
        st.dataframe(df_tabla_var, width='stretch', hide_index=True)
    else:
        st.info("Se necesitan al menos 2 años de datos para realizar comparativas")

with tabs[4]:
    st.header("🔮 Proyecciones de Gasto Futuro")
    
    if len(años_disponibles) >= 2:
        direccion_proyeccion = st.selectbox(
            "Seleccionar Dirección para Proyección",
            ["Todas"] + direcciones_disponibles
        )
        
        if direccion_proyeccion == "Todas":
            df_historico = df_adquisiciones.groupby('Año')['Monto'].sum().reset_index()
        else:
            df_historico = df_adquisiciones[df_adquisiciones['Dirección'] == direccion_proyeccion].groupby('Año')['Monto'].sum().reset_index()
        
        if len(df_historico) >= 2:
            años_hist = df_historico['Año'].values
            gastos_hist = df_historico['Monto'].values
            
            coeficientes = pd.Series(gastos_hist).pct_change().dropna()
            tasa_promedio = coeficientes.mean()
            
            año_siguiente = años_hist[-1] + 1
            proyeccion_simple = gastos_hist[-1] * (1 + tasa_promedio)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    label=f"Proyección para {año_siguiente}",
                    value=f"S/ {proyeccion_simple:,.0f}",
                    delta=f"{tasa_promedio*100:+.1f}% vs año anterior"
                )
            
            with col2:
                st.metric(
                    label="Tasa de Crecimiento Promedio",
                    value=f"{tasa_promedio*100:.2f}%"
                )
            
            df_proyeccion = pd.DataFrame({
                'Año': list(años_hist) + [año_siguiente],
                'Gasto': list(gastos_hist) + [proyeccion_simple],
                'Tipo': ['Real'] * len(años_hist) + ['Proyección']
            })
            
            fig_proyeccion = px.line(
                df_proyeccion,
                x='Año',
                y='Gasto',
                color='Tipo',
                markers=True,
                title=f'Proyección de Gasto - {direccion_proyeccion}',
                labels={'Gasto': 'Monto (S/)', 'Año': 'Año'}
            )
            fig_proyeccion.update_layout(height=400)
            st.plotly_chart(fig_proyeccion, width='stretch')
            
            st.info(f"""
            **Metodología de Proyección:**
            - Basada en tasa de crecimiento promedio histórica
            - Tasa calculada: {tasa_promedio*100:.2f}% anual
            - Datos históricos: {len(años_hist)} años
            """)
        else:
            st.warning("Se necesitan al menos 2 años de datos para proyecciones")
    else:
        st.info("Se necesitan al menos 2 años de datos para realizar proyecciones")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>Dashboard de Control de Adquisiciones - Generado con Streamlit</p>
    <p>Última actualización: {}</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
