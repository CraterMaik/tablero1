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
from database import SessionLocal, UnidadEjecutora
from db_operations import inicializar_datos_ejemplo, obtener_programacion_df, procesar_archivo_programacion, obtener_alertas, crear_alerta, eliminar_alerta

st.set_page_config(page_title="Dashboard de Programación Presupuestal", layout="wide", initial_sidebar_state="expanded")

@st.cache_data(ttl=60)
def cargar_datos():
    """Carga datos desde la base de datos"""
    db = SessionLocal()
    try:
        df_programacion = obtener_programacion_df(db)
        return df_programacion
    finally:
        db.close()

df_programacion = cargar_datos()

st.title("📊 Dashboard de Programación Presupuestal")

tabs = st.tabs(["📈 Dashboard Principal", "📤 Importar/Exportar", "⚠️ Alertas", "📊 Análisis Comparativo"])

with tabs[0]:
    st.markdown("---")
    
    st.sidebar.header("🔍 Filtros")
    
    if len(df_programacion) == 0:
        st.warning("⚠️ No hay datos cargados. Por favor, importe un archivo de programación en la pestaña 'Importar/Exportar'")
        st.stop()
    
    años_disponibles = sorted(df_programacion['Año'].unique())
    año_seleccionado = st.sidebar.selectbox(
        "Seleccionar Año",
        options=["Todos"] + años_disponibles,
        index=0
    )
    
    ues_disponibles = sorted(df_programacion['UE'].unique())
    ue_seleccionada = st.sidebar.multiselect(
        "Seleccionar UE",
        options=ues_disponibles,
        default=ues_disponibles
    )
    
    metas_disponibles = sorted(df_programacion['Meta'].unique())
    meta_seleccionada = st.sidebar.multiselect(
        "Seleccionar Meta",
        options=metas_disponibles,
        default=metas_disponibles[:5] if len(metas_disponibles) > 5 else metas_disponibles
    )
    
    st.sidebar.markdown("---")
    
    df_filtrado = df_programacion.copy()
    
    if año_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Año'] == año_seleccionado]
    
    if ue_seleccionada:
        df_filtrado = df_filtrado[df_filtrado['UE'].isin(ue_seleccionada)]
    
    if meta_seleccionada:
        df_filtrado = df_filtrado[df_filtrado['Meta'].isin(meta_seleccionada)]
    
    st.header("📊 Resumen Ejecutivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_registros = len(df_filtrado)
        st.metric(
            label="Total Registros",
            value=f"{total_registros:,}"
        )
    
    with col2:
        total_pim = df_filtrado['PIM'].sum()
        st.metric(
            label="PIM Total",
            value=f"S/ {total_pim:,.0f}",
            delta=f"Presupuesto"
        )
    
    with col3:
        total_certificado = df_filtrado['Certificado'].sum()
        st.metric(
            label="Certificado Total",
            value=f"S/ {total_certificado:,.0f}",
            delta=f"{(total_certificado/total_pim*100) if total_pim > 0 else 0:.1f}%"
        )
    
    with col4:
        pct_ejecucion = (total_certificado / total_pim * 100) if total_pim > 0 else 0
        st.metric(
            label="% Ejecución",
            value=f"{pct_ejecucion:.1f}%",
            delta="Certificado vs PIM"
        )
    
    st.markdown("---")
    
    st.header("🏢 Análisis por Unidad Ejecutora")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gasto_por_ue = df_filtrado.groupby('UE').agg({
            'PIM': 'sum',
            'Certificado': 'sum'
        }).reset_index()
        gasto_por_ue = gasto_por_ue.sort_values('Certificado', ascending=False)
        
        fig_ue = px.bar(
            gasto_por_ue,
            x='Certificado',
            y='UE',
            orientation='h',
            title="Certificado por Unidad Ejecutora",
            labels={'Certificado': 'Monto (S/)', 'UE': 'Unidad Ejecutora'},
            color='Certificado',
            color_continuous_scale='Blues'
        )
        fig_ue.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_ue, use_container_width=True)
    
    with col2:
        gasto_por_ue['Ejecución_%'] = (gasto_por_ue['Certificado'] / gasto_por_ue['PIM'] * 100).round(2)
        
        fig_ejecucion = px.bar(
            gasto_por_ue,
            x='UE',
            y='Ejecución_%',
            title="% Ejecución por UE (Certificado/PIM)",
            labels={'Ejecución_%': '% Ejecución', 'UE': 'Unidad Ejecutora'},
            color='Ejecución_%',
            color_continuous_scale='Greens'
        )
        fig_ejecucion.update_layout(height=400, showlegend=False)
        fig_ejecucion.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Meta 100%")
        st.plotly_chart(fig_ejecucion, use_container_width=True)
    
    st.markdown("---")
    
    st.header("💰 Presupuesto vs Certificado")
    
    pim_cert_comp = df_filtrado.groupby('UE').agg({
        'PIM': 'sum',
        'Certificado': 'sum',
        'PIM_Por_Certificar': 'sum'
    }).reset_index()
    
    fig_presup_cert = go.Figure()
    
    fig_presup_cert.add_trace(go.Bar(
        name='PIM',
        x=pim_cert_comp['UE'],
        y=pim_cert_comp['PIM'],
        marker_color='lightblue'
    ))
    
    fig_presup_cert.add_trace(go.Bar(
        name='Certificado',
        x=pim_cert_comp['UE'],
        y=pim_cert_comp['Certificado'],
        marker_color='darkblue'
    ))
    
    fig_presup_cert.update_layout(
        title='PIM vs Certificado por UE',
        xaxis_title='Unidad Ejecutora',
        yaxis_title='Monto (S/)',
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig_presup_cert, use_container_width=True)
    
    st.markdown("---")
    
    st.header("📋 Detalle de Programación")
    
    busqueda = st.text_input("🔎 Buscar en descripción:", "")
    
    df_tabla_detalle = df_filtrado.copy()
    
    if busqueda:
        df_tabla_detalle = df_tabla_detalle[
            df_tabla_detalle['Descripción'].str.contains(busqueda, case=False, na=False) |
            df_tabla_detalle['Meta'].str.contains(busqueda, case=False, na=False)
        ]
    
    df_tabla_display = df_tabla_detalle[['Año', 'UE', 'Meta', 'Clasificador', 'Descripción', 'PIM', 'Certificado', 'PIM_Por_Certificar', 'Ejecución_%']].copy()
    df_tabla_display['PIM'] = df_tabla_display['PIM'].apply(lambda x: f"S/ {x:,.0f}")
    df_tabla_display['Certificado'] = df_tabla_display['Certificado'].apply(lambda x: f"S/ {x:,.0f}")
    df_tabla_display['PIM_Por_Certificar'] = df_tabla_display['PIM_Por_Certificar'].apply(lambda x: f"S/ {x:,.0f}")
    
    st.dataframe(
        df_tabla_display,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    st.caption(f"Mostrando {len(df_tabla_detalle)} de {len(df_programacion)} registros totales")

with tabs[1]:
    st.header("📤 Importar y Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Importar Programación Anual")
        
        año_importacion = st.number_input(
            "Año de la programación",
            min_value=2020,
            max_value=2030,
            value=2024,
            step=1
        )
        
        st.info("""
        **Formato requerido:**
        
        - Archivo Excel (.xlsx) con estructura de Programación Anual
        - Columnas: PIM, CERTIFICADO, PIM POR CERTIFICAR, TOTAL ANUAL, etc.
        - El archivo debe incluir las Unidades Ejecutoras y Metas
        """)
        
        archivo_carga = st.file_uploader(
            "Cargar archivo Excel de Programación Anual",
            type=['xlsx'],
            key="file_uploader"
        )
        
        if archivo_carga and st.button("Importar Datos"):
            with st.spinner("Procesando archivo..."):
                db = SessionLocal()
                exito, mensaje = procesar_archivo_programacion(db, archivo_carga, año_importacion)
                db.close()
                
                if exito:
                    st.success(f"✅ {mensaje}")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {mensaje}")
    
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
                    
                    df_programacion.to_excel(writer, sheet_name='Programación', index=False)
                    
                    resumen_ue = df_programacion.groupby('UE').agg({
                        'PIM': 'sum',
                        'Certificado': 'sum',
                        'PIM_Por_Certificar': 'sum',
                        'Devengado': 'sum'
                    }).reset_index()
                    resumen_ue.to_excel(writer, sheet_name='Resumen_UE', index=False)
                    
                    gasto_por_ue = df_programacion.groupby('UE')['Certificado'].sum().reset_index()
                    gasto_por_ue = gasto_por_ue.sort_values('Certificado', ascending=False)
                    
                    gasto_por_ue.to_excel(writer, sheet_name='Datos_Gráficos', index=False, startrow=0, startcol=0)
                    
                    graficos_sheet = workbook.add_worksheet('Gráficos')
                    
                    chart1 = workbook.add_chart({'type': 'column'})
                    chart1.add_series({
                        'name': 'Certificado por UE',
                        'categories': ['Datos_Gráficos', 1, 0, len(gasto_por_ue), 0],
                        'values': ['Datos_Gráficos', 1, 1, len(gasto_por_ue), 1],
                    })
                    chart1.set_title({'name': 'Certificado por Unidad Ejecutora'})
                    chart1.set_x_axis({'name': 'UE'})
                    chart1.set_y_axis({'name': 'Monto (S/)'})
                    chart1.set_size({'width': 600, 'height': 400})
                    
                    graficos_sheet.insert_chart('B2', chart1)
                
                output.seek(0)
                st.download_button(
                    label="⬇️ Descargar Reporte Excel",
                    data=output,
                    file_name=f"programacion_presupuestal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            elif formato_exportacion == "PDF":
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                story = []
                styles = getSampleStyleSheet()
                
                story.append(Paragraph("Reporte de Programación Presupuestal", styles['Title']))
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
                
                story.append(Paragraph("Resumen Ejecutivo", styles['Heading1']))
                data_resumen = [
                    ['Métrica', 'Valor'],
                    ['Total Registros', f"{len(df_programacion):,}"],
                    ['PIM Total', f"S/ {df_programacion['PIM'].sum():,.0f}"],
                    ['Certificado Total', f"S/ {df_programacion['Certificado'].sum():,.0f}"],
                    ['% Ejecución', f"{(df_programacion['Certificado'].sum()/df_programacion['PIM'].sum()*100):.2f}%"]
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
                story.append(Paragraph("Certificado por Unidad Ejecutora", styles['Heading1']))
                
                gasto_por_ue = df_programacion.groupby('UE')['Certificado'].sum().reset_index()
                gasto_por_ue = gasto_por_ue.sort_values('Certificado', ascending=False)
                
                fig_ue = px.bar(
                    gasto_por_ue,
                    x='Certificado',
                    y='UE',
                    orientation='h',
                    title="Certificado por Unidad Ejecutora",
                    labels={'Certificado': 'Monto (S/)', 'UE': 'Unidad Ejecutora'}
                )
                
                img_bytes = fig_ue.to_image(format="png", width=600, height=400)
                img_buffer = io.BytesIO(img_bytes)
                img = Image(img_buffer, width=5*inch, height=3.3*inch)
                story.append(img)
                
                doc.build(story)
                buffer.seek(0)
                
                st.download_button(
                    label="⬇️ Descargar Reporte PDF",
                    data=buffer,
                    file_name=f"programacion_presupuestal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )

with tabs[2]:
    st.header("⚠️ Alertas de Presupuesto")
    
    db = SessionLocal()
    try:
        alertas = obtener_alertas(db)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Alertas Activas")
            if alertas:
                for alerta in alertas:
                    ue_nombre = "Todas"
                    if alerta.unidad_ejecutora_id:
                        ue = db.query(UnidadEjecutora).filter(UnidadEjecutora.id == alerta.unidad_ejecutora_id).first()
                        if ue:
                            ue_nombre = ue.codigo
                    
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.info(f"🔔 **{alerta.nombre}** - UE: {ue_nombre} - Umbral: {alerta.umbral_porcentaje}%")
                    with col_b:
                        if st.button("Eliminar", key=f"del_{alerta.id}"):
                            eliminar_alerta(db, alerta.id)
                            st.rerun()
            else:
                st.info("No hay alertas configuradas")
        
        with col2:
            st.subheader("Nueva Alerta")
            
            nombre_alerta = st.text_input("Nombre de la alerta")
            
            ues = db.query(UnidadEjecutora).all()
            ue_options = ["Todas"] + [ue.codigo for ue in ues]
            ue_alerta = st.selectbox("Unidad Ejecutora", ue_options)
            
            umbral_alerta = st.slider("Umbral de ejecución (%)", 0, 100, 80)
            
            if st.button("Crear Alerta"):
                if nombre_alerta:
                    ue_id = None
                    if ue_alerta != "Todas":
                        ue_obj = db.query(UnidadEjecutora).filter(UnidadEjecutora.codigo == ue_alerta).first()
                        if ue_obj:
                            ue_id = ue_obj.id
                    
                    crear_alerta(db, nombre_alerta, ue_id, umbral_alerta)
                    st.success("✅ Alerta creada exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Ingrese un nombre para la alerta")
        
        st.markdown("---")
        st.subheader("📊 Estado de Alertas")
        
        alertas_activas = df_programacion.groupby('UE').agg({
            'PIM': 'sum',
            'Certificado': 'sum'
        }).reset_index()
        alertas_activas['Ejecución_%'] = (alertas_activas['Certificado'] / alertas_activas['PIM'] * 100).round(2)
        
        for alerta in alertas:
            if alerta.unidad_ejecutora_id:
                ue = db.query(UnidadEjecutora).filter(UnidadEjecutora.id == alerta.unidad_ejecutora_id).first()
                if ue:
                    ue_data = alertas_activas[alertas_activas['UE'] == ue.codigo]
                    if not ue_data.empty:
                        ejecucion = ue_data.iloc[0]['Ejecución_%']
                        if ejecucion >= alerta.umbral_porcentaje:
                            st.warning(f"⚠️ **{alerta.nombre}**: {ue.codigo} ha alcanzado {ejecucion:.2f}% (Umbral: {alerta.umbral_porcentaje}%)")
    finally:
        db.close()

with tabs[3]:
    st.header("📊 Análisis Comparativo")
    
    if len(años_disponibles) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            año1 = st.selectbox("Año 1", años_disponibles, index=0)
        
        with col2:
            año2 = st.selectbox("Año 2", años_disponibles, index=min(1, len(años_disponibles)-1))
        
        df_año1 = df_programacion[df_programacion['Año'] == año1].groupby('UE')['Certificado'].sum().reset_index()
        df_año1.columns = ['UE', f'Certificado_{año1}']
        
        df_año2 = df_programacion[df_programacion['Año'] == año2].groupby('UE')['Certificado'].sum().reset_index()
        df_año2.columns = ['UE', f'Certificado_{año2}']
        
        df_comp = df_año1.merge(df_año2, on='UE', how='outer').fillna(0)
        df_comp['Variación'] = df_comp[f'Certificado_{año2}'] - df_comp[f'Certificado_{año1}']
        df_comp['Variación_%'] = ((df_comp[f'Certificado_{año2}'] - df_comp[f'Certificado_{año1}']) / df_comp[f'Certificado_{año1}'] * 100).round(2)
        df_comp['Variación_%'] = df_comp['Variación_%'].replace([float('inf'), float('-inf')], 0)
        
        fig_comp = go.Figure()
        
        fig_comp.add_trace(go.Bar(
            name=str(año1),
            x=df_comp['UE'],
            y=df_comp[f'Certificado_{año1}'],
            marker_color='lightblue'
        ))
        
        fig_comp.add_trace(go.Bar(
            name=str(año2),
            x=df_comp['UE'],
            y=df_comp[f'Certificado_{año2}'],
            marker_color='darkblue'
        ))
        
        fig_comp.update_layout(
            title=f'Comparación de Certificado: {año1} vs {año2}',
            xaxis_title='Unidad Ejecutora',
            yaxis_title='Certificado (S/)',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig_comp, use_container_width=True)
        
        st.subheader("📈 Tabla Comparativa")
        
        df_comp_display = df_comp.copy()
        df_comp_display[f'Certificado_{año1}'] = df_comp_display[f'Certificado_{año1}'].apply(lambda x: f"S/ {x:,.0f}")
        df_comp_display[f'Certificado_{año2}'] = df_comp_display[f'Certificado_{año2}'].apply(lambda x: f"S/ {x:,.0f}")
        df_comp_display['Variación'] = df_comp_display['Variación'].apply(lambda x: f"S/ {x:,.0f}")
        
        st.dataframe(df_comp_display, use_container_width=True, hide_index=True)
    else:
        st.info("Se necesitan datos de al menos 2 años para realizar comparaciones")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>Dashboard de Programación Presupuestal - Generado con Streamlit</p>
    <p>Última actualización: {}</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
