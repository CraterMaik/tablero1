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
from db_operations import (
    inicializar_datos_ejemplo, 
    obtener_programacion_df, 
    obtener_adquisiciones_df,
    obtener_detalle_adquisicion,
    procesar_archivo_programacion, 
    obtener_alertas, 
    crear_alerta, 
    eliminar_alerta
)
from database import SessionLocal as DirectSessionLocal

st.set_page_config(page_title="Dashboard de Programación Presupuestal", layout="wide", initial_sidebar_state="expanded")

# Estilos CSS personalizados - Fondo azul INEI para métricas
st.markdown("""
<style>
    /* Estilo azul INEI para las métricas del resumen ejecutivo */
    .metric-inei {
        background: #1f4e78;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 10px;
    }
    .metric-inei .metric-label {
        font-size: 14px;
        font-weight: 500;
        opacity: 0.9;
        margin-bottom: 8px;
    }
    .metric-inei .metric-value {
        font-size: 28px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
# def cargar_datos_programacion():
#     """Carga datos de programación desde la base de datos"""
#     # Las funciones crean su propia sesión internamente
#     return obtener_programacion_df()

@st.cache_data(ttl=60)
def cargar_datos_adquisiciones():
    """Carga datos de adquisiciones desde la base de datos"""
    # Las funciones crean su propia sesión internamente
    return obtener_adquisiciones_df()

@st.dialog("Detalle de Adquisición", width="large")
def mostrar_detalle_adquisicion(codigo_adquisicion):
    """Modal para mostrar el detalle completo de una adquisición con timeline"""
    db = DirectSessionLocal()
    try:
        detalle_completo = obtener_detalle_adquisicion(db, codigo_adquisicion)
        
        if not detalle_completo:
            st.error("No se encontró la adquisición")
            return
        
        adq = detalle_completo['adquisicion']
        detalle = detalle_completo['detalle']
        procesos = detalle_completo['procesos']
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"{codigo_adquisicion}")
            st.write(f"**{adq.descripcion}**")
        
        with col2:
            if detalle:
                st.metric("PIM Asignado", f"S/ {detalle.pim_asignado:,.0f}")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            if detalle:
                st.metric("Requerimientos", f"{detalle.requerimientos_adquiridos}/{detalle.requerimientos_total}")
        
        with col_b:
            st.metric("Estado", adq.estado)
        
        with col_c:
            st.metric("Monto Referencial", f"S/ {adq.monto_referencial:,.0f}")
        
        with col_d:
            st.metric("Monto Adjudicado", f"S/ {adq.monto_adjudicado:,.0f}")
        
        if detalle:
            st.info(f"**Unidad Responsable:** {detalle.unidad_responsable} | **Tipo:** {detalle.tipo_servicio}")
        
        st.divider()
        
        if procesos:
            st.subheader("Timeline del Proceso")
            
            df_procesos = pd.DataFrame([{
                'Orden': p.orden,
                'Hito': p.hito,
                'Area': p.tipo_flujo,
                'Fecha_Inicio': p.fecha_inicio,
                'Fecha_Fin': p.fecha_fin if p.fecha_fin else p.fecha_inicio,
                'Dias': p.dias_transcurridos,
                'Responsable': p.responsable_correo
            } for p in procesos])
            
            fig_timeline = px.timeline(
                df_procesos,
                x_start='Fecha_Inicio',
                x_end='Fecha_Fin',
                y='Hito',
                color='Area',
                hover_data=['Dias', 'Responsable'],
                title="Flujo de Proceso de Adquisición",
                color_discrete_map={'OTIN': '#FFB84D', 'OTA': '#90EE90'}
            )
            
            fig_timeline.update_layout(
                height=400,
                yaxis={'categoryorder': 'array', 'categoryarray': df_procesos['Hito'].tolist()[::-1]},
                xaxis_title="Fecha",
                yaxis_title="",
                showlegend=True
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            total_dias = sum(p.dias_transcurridos for p in procesos)
            st.metric("**Total de Días del Proceso**", f"{total_dias} días")
            
            st.divider()
            st.subheader("Detalle de Pasos del Proceso")
            
            df_procesos_tabla = pd.DataFrame([{
                'Orden': p.orden,
                'Hito': p.hito,
                'Área': p.tipo_flujo,
                'Días': p.dias_transcurridos,
                'Fecha Inicio': p.fecha_inicio.strftime('%d/%m/%Y') if p.fecha_inicio else '',
                'Responsable': p.responsable_correo if p.responsable_correo else '',
                'Comentarios': p.comentarios if p.comentarios else ''
            } for p in procesos])
            
            st.dataframe(df_procesos_tabla, use_container_width=True, hide_index=True)
        
        else:
            st.info("No hay información de proceso disponible para esta adquisición")
    
    finally:
        db.close()

#df_programacion = cargar_datos_programacion()
df_adquisiciones = cargar_datos_adquisiciones()

st.title("📊 Dashboard de Adquisiciones")

st.sidebar.header("🔍 Filtros")

if len(df_adquisiciones) == 0:
     st.warning("⚠️ No hay datos cargados. Por favor, importe un archivo de programación en la pestaña 'Importar/Exportar'")
else:
    años_disponibles = sorted(df_adquisiciones['Año'].unique())
    opciones_año = ["Todos"] + list(años_disponibles)
    indice_default = opciones_año.index(2025) if 2025 in años_disponibles else 0
    año_seleccionado = st.sidebar.selectbox(
         "Seleccionar Año",
         options=opciones_año,
         index=indice_default
    )
    
    metas_disponibles = sorted(df_adquisiciones['Meta'].unique())
    meta_seleccionada = st.sidebar.multiselect(
        "Seleccionar Meta",
        options=metas_disponibles,
        default=metas_disponibles[:5] if len(metas_disponibles) > 5 else metas_disponibles
    )
    
    ues_disponibles = sorted(df_adquisiciones['UE'].unique())
    ue_seleccionada = st.sidebar.multiselect(
        "Seleccionar DDNNTT",
        options=ues_disponibles,
        default=ues_disponibles
    )

    if len(df_adquisiciones) > 0:
        tipos_permitidos = ['BIEN', 'SERVICIO']
        tipos_en_datos = [t for t in tipos_permitidos if t in df_adquisiciones['Tipo_Servicio'].values]
        tipo_servicio_seleccionado = st.sidebar.multiselect(
            "Tipo (Bien/Servicio)",
            options=tipos_permitidos,
            default=tipos_en_datos
        )

        estados_permitidos = ['EN PROCESO', 'CULMINADO', 'CANCELADO', 'HISTORICO', 'NO INICIADO']
        estados_en_datos = [e for e in estados_permitidos if e in df_adquisiciones['Estado'].values]
        estado_seleccionado = st.sidebar.multiselect(
            "Estado",
            options=estados_permitidos,
            default=estados_en_datos
        )
    else:
        tipo_servicio_seleccionado = []
        estado_seleccionado = []

    st.sidebar.markdown("---")
   

tabs = st.tabs([
    # "💰 Presupuestal General", 
    "🛒 Adquisiciones", 
    "📤 Importar/Exportar", 
    # "⚠️ Alertas", 
    # "📊 Análisis Comparativo"
])

# with tabs[0]:
#     st.header("💰 Presupuestal General")
    
#     if len(df_programacion) == 0:
#         st.warning("⚠️ No hay datos de programación disponibles")
#         st.stop()
    
#     df_filtrado = df_programacion.copy()
    
#     if año_seleccionado != "Todos":
#         df_filtrado = df_filtrado[df_filtrado['Año'] == año_seleccionado]
    
#     if ue_seleccionada:
#         df_filtrado = df_filtrado[df_filtrado['UE'].isin(ue_seleccionada)]
    
#     if meta_seleccionada:
#         df_filtrado = df_filtrado[df_filtrado['Meta'].isin(meta_seleccionada)]
    
#     st.subheader("Resumen Ejecutivo")

#     col1, col2, col3, col4 = st.columns(4)

#     total_registros = len(df_filtrado)
#     total_pim = df_filtrado['PIM'].sum()
#     total_certificado = df_filtrado['Certificado'].sum()
#     pct_ejecucion = (total_certificado / total_pim * 100) if total_pim > 0 else 0

#     with col1:
#         st.markdown(f"""
#         <div class="metric-inei">
#             <div class="metric-label">Total Registros</div>
#             <div class="metric-value">{total_registros:,}</div>
#         </div>
#         """, unsafe_allow_html=True)

#     with col2:
#         st.markdown(f"""
#         <div class="metric-inei">
#             <div class="metric-label">PIM Total</div>
#             <div class="metric-value">S/ {total_pim:,.2f}</div>
#         </div>
#         """, unsafe_allow_html=True)

#     with col3:
#         st.markdown(f"""
#         <div class="metric-inei">
#             <div class="metric-label">Certificado Total</div>
#             <div class="metric-value">S/ {total_certificado:,.2f}</div>
#         </div>
#         """, unsafe_allow_html=True)

#     with col4:
#         st.markdown(f"""
#         <div class="metric-inei">
#             <div class="metric-label">% Ejecución</div>
#             <div class="metric-value">{pct_ejecucion:.1f}%</div>
#         </div>
#         """, unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.subheader("PIM y Certificado por UE")
        
#         gasto_por_ue = df_filtrado.groupby('UE').agg({
#             'PIM': 'sum',
#             'Certificado': 'sum'
#         }).reset_index()
#         gasto_por_ue = gasto_por_ue.sort_values('Certificado', ascending=False)
        
#         fig_presup_cert = go.Figure()
        
#         fig_presup_cert.add_trace(go.Bar(
#             name='PIM',
#             x=gasto_por_ue['UE'],
#             y=gasto_por_ue['PIM'],
#             marker_color='lightblue'
#         ))
        
#         fig_presup_cert.add_trace(go.Bar(
#             name='Certificado',
#             x=gasto_por_ue['UE'],
#             y=gasto_por_ue['Certificado'],
#             marker_color='darkblue'
#         ))
        
#         fig_presup_cert.update_layout(
#             xaxis_title='Unidad Ejecutora',
#             yaxis_title='Monto (S/)',
#             barmode='group',
#             height=400,
#             showlegend=True
#         )
        
#         st.plotly_chart(fig_presup_cert, use_container_width=True)
    
#     with col2:
#         st.subheader("% Ejecución por UE")
        
#         gasto_por_ue['Ejecución_%'] = (gasto_por_ue['Certificado'] / gasto_por_ue['PIM'] * 100).round(2)
        
#         fig_ejecucion = px.bar(
#             gasto_por_ue,
#             x='UE',
#             y='Ejecución_%',
#             labels={'Ejecución_%': '% Ejecución', 'UE': 'Unidad Ejecutora'},
#             color='Ejecución_%',
#             color_continuous_scale='Greens'
#         )
#         fig_ejecucion.update_layout(height=400, showlegend=False)
#         fig_ejecucion.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Meta 100%")
#         st.plotly_chart(fig_ejecucion, use_container_width=True)
    
#     st.markdown("---")
    
#     st.subheader("Análisis por Clasificador Presupuestal")
    
#     clasificadores_agregado = df_filtrado.groupby('Clasificador').agg({
#         'PIM': 'sum',
#         'Certificado': 'sum'
#     }).reset_index()
#     clasificadores_agregado = clasificadores_agregado.sort_values('PIM', ascending=False).head(10)
    
#     col_c1, col_c2 = st.columns(2)
    
#     with col_c1:
#         st.write("**Top 10 Clasificadores por Presupuesto**")
        
#         fig_clasificadores = go.Figure()
        
#         fig_clasificadores.add_trace(go.Bar(
#             name='PIM',
#             y=clasificadores_agregado['Clasificador'],
#             x=clasificadores_agregado['PIM'],
#             marker_color='lightcoral',
#             orientation='h'
#         ))
        
#         fig_clasificadores.add_trace(go.Bar(
#             name='Certificado',
#             y=clasificadores_agregado['Clasificador'],
#             x=clasificadores_agregado['Certificado'],
#             marker_color='darkred',
#             orientation='h'
#         ))
        
#         fig_clasificadores.update_layout(
#             xaxis_title='Monto (S/)',
#             yaxis_title='',
#             barmode='group',
#             height=400,
#             showlegend=True
#         )
        
#         st.plotly_chart(fig_clasificadores, use_container_width=True)
    
#     with col_c2:
#         st.write("**Distribución de Presupuesto por Clasificador**")
        
#         fig_treemap = px.treemap(
#             clasificadores_agregado,
#             path=['Clasificador'],
#             values='PIM',
#             color='Certificado',
#             color_continuous_scale='Reds',
#             hover_data={'PIM': ':,.0f', 'Certificado': ':,.0f'}
#         )
        
#         fig_treemap.update_layout(height=400)
        
#         st.plotly_chart(fig_treemap, use_container_width=True)
    
#     st.markdown("---")
    
#     st.subheader("Tabla Detallada")
    
#     busqueda = st.text_input("🔎 Buscar en descripción:", "")
    
#     df_tabla_detalle = df_filtrado.copy()
    
#     if busqueda:
#         df_tabla_detalle = df_tabla_detalle[
#             df_tabla_detalle['Descripción'].str.contains(busqueda, case=False, na=False) |
#             df_tabla_detalle['Meta'].str.contains(busqueda, case=False, na=False)
#         ]
    
#     df_tabla_display = df_tabla_detalle[['Año', 'UE', 'Meta', 'Clasificador', 'Descripción', 'PIM', 'Certificado', 'PIM_Por_Certificar', 'Ejecución_%']].copy()
#     df_tabla_display['PIM'] = df_tabla_display['PIM'].apply(lambda x: f"S/ {x:,.0f}")
#     df_tabla_display['Certificado'] = df_tabla_display['Certificado'].apply(lambda x: f"S/ {x:,.0f}")
#     df_tabla_display['PIM_Por_Certificar'] = df_tabla_display['PIM_Por_Certificar'].apply(lambda x: f"S/ {x:,.0f}")
    
#     st.dataframe(
#         df_tabla_display,
#         use_container_width=True,
#         hide_index=True,
#         height=400
#     )
    
#     st.caption(f"Mostrando {len(df_tabla_detalle)} de {len(df_programacion)} registros totales")

with tabs[0]:
    # st.header("")
    
    if len(df_adquisiciones) == 0:
        st.info("⚠️ No hay datos de adquisiciones disponibles")
    else:
        df_adq_filtrado = df_adquisiciones.copy()

        if año_seleccionado != "Todos":
            df_adq_filtrado = df_adq_filtrado[df_adq_filtrado['Año'] == año_seleccionado]

        if ue_seleccionada:
            df_adq_filtrado = df_adq_filtrado[df_adq_filtrado['UE'].isin(ue_seleccionada)]

        if meta_seleccionada:
            df_adq_filtrado = df_adq_filtrado[df_adq_filtrado['Meta'].isin(meta_seleccionada)]

        if tipo_servicio_seleccionado:
            df_adq_filtrado = df_adq_filtrado[df_adq_filtrado['Tipo_Servicio'].isin(tipo_servicio_seleccionado)]

        if estado_seleccionado:
            df_adq_filtrado = df_adq_filtrado[df_adq_filtrado['Estado'].isin(estado_seleccionado)]

        st.subheader("Resumen Ejecutivo")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            total_adquisiciones = len(df_adq_filtrado)
            st.markdown(f"""
            <div class="metric-inei">
                <div class="metric-label">Total<br>Requerimientos</div>
                <div class="metric-value">{total_adquisiciones:,}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            total_culminados = len(df_adq_filtrado[df_adq_filtrado['Estado'] == 'CULMINADO'])
            st.markdown(f"""
            <div class="metric-inei">
                <div class="metric-label">Total Adquiridos<br>(Culminados)</div>
                <div class="metric-value">{total_culminados:,}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            total_referencial = df_adq_filtrado['Monto_Referencial'].sum()
            st.markdown(f"""
            <div class="metric-inei">
                <div class="metric-label">Monto Total<br>(PIM)</div>
                <div class="metric-value">S/ {total_referencial:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            monto_culminados = df_adq_filtrado[df_adq_filtrado['Estado'] == 'CULMINADO']['Monto_Adjudicado'].sum()
            st.markdown(f"""
            <div class="metric-inei">
                <div class="metric-label">Monto Adquiridos<br>(Culminados)</div>
                <div class="metric-value">S/ {monto_culminados:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        

        # with col4:
        #     total_adjudicado = df_adq_filtrado['Monto_Adjudicado'].sum()
        #     st.markdown(f"""
        #     <div class="metric-inei">
        #         <div class="metric-label">Monto Adquiridos Total<br>(CERTIFICADO)</div>
        #         <div class="metric-value">S/ {total_adjudicado:,.2f}</div>
        #     </div>
        #     """, unsafe_allow_html=True)

        with col5:
            pct_avance = (monto_culminados / total_referencial * 100) if total_referencial > 0 else 0
            st.markdown(f"""
            <div class="metric-inei">
                <div class="metric-label">% Avance<br>(Adqui. / PIM)</div>
                <div class="metric-value">{pct_avance:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Adquisiciones por Estado")
            
            adq_por_estado = df_adq_filtrado.groupby('Estado').size().reset_index(name='Cantidad')
            
            fig_estado = px.pie(
                adq_por_estado,
                values='Cantidad',
                names='Estado',
                title='Distribución por Estado'
            )
            fig_estado.update_layout(height=400)
            st.plotly_chart(fig_estado, use_container_width=True)
        
        with col2:
            st.subheader("Montos por DDNNTT")
            
            montos_por_ue = df_adq_filtrado.groupby('UE').agg({
                'Monto_Referencial': 'sum',
                'Monto_Adjudicado': 'sum'
            }).reset_index()
            
            fig_montos = go.Figure()
            
            fig_montos.add_trace(go.Bar(
                name='PIM',
                x=montos_por_ue['UE'],
                y=montos_por_ue['Monto_Referencial'],
                marker_color='lightcoral'
            ))
            
            fig_montos.add_trace(go.Bar(
                name='Monto Adquiridos',
                x=montos_por_ue['UE'],
                y=montos_por_ue['Monto_Adjudicado'],
                marker_color='darkred'
            ))
            
            fig_montos.update_layout(
                xaxis_title='DDNNTT',
                yaxis_title='Monto (S/)',
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig_montos, use_container_width=True)
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Certificado por Mes")

            # Diccionario de meses en español
            meses_español = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }

            # Preparar datos: extraer mes de fecha de adjudicación
            df_con_fecha = df_adq_filtrado[df_adq_filtrado['Fecha_Adjudicacion'].notna()].copy()

            if len(df_con_fecha) > 0:
                df_con_fecha['Mes'] = pd.to_datetime(df_con_fecha['Fecha_Adjudicacion']).dt.month
                df_con_fecha['Mes_Nombre'] = df_con_fecha['Mes'].map(meses_español)

                gastos_por_mes = df_con_fecha.groupby(['Mes', 'Mes_Nombre'])['Monto_Adjudicado'].sum().reset_index()
                gastos_por_mes = gastos_por_mes.sort_values('Mes')

                fig_meses = px.bar(
                    gastos_por_mes,
                    x='Mes_Nombre',
                    y='Monto_Adjudicado',
                    title='Adquisiciones Certificados por Mes',
                    labels={'Monto_Adjudicado': 'Monto Adquirido (S/)', 'Mes_Nombre': 'Mes'}
                )
                fig_meses.update_traces(marker_color='steelblue')
                fig_meses.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_meses, use_container_width=True)
            else:
                st.info("No hay adquisiciones con fecha de adjudicación para mostrar")
        
        with col4:
            st.subheader("% Avance por DDNNTT")

            avance_por_ue = df_adq_filtrado.groupby('UE').agg({
                'Monto_Referencial': 'sum',
                'Monto_Adjudicado': 'sum'
            }).reset_index()
            avance_por_ue['Avance_%'] = (avance_por_ue['Monto_Adjudicado'] / avance_por_ue['Monto_Referencial'] * 100).round(1)
            avance_por_ue = avance_por_ue.sort_values('Avance_%', ascending=True)

            if len(avance_por_ue) > 0:
                fig_avance = px.bar(
                    avance_por_ue,
                    x='Avance_%',
                    y='UE',
                    orientation='h',
                    title='Porcentaje de Avance por Unidad Ejecutora',
                    labels={'Avance_%': '% Avance', 'UE': 'Unidad Ejecutora'},
                    text='Avance_%'
                )
                fig_avance.update_traces(
                    marker_color='#2c5aa0',
                    texttemplate='%{text:.1f}%',
                    textposition='outside'
                )
                fig_avance.update_layout(
                    height=400,
                    showlegend=False,
                    xaxis=dict(range=[0, max(avance_por_ue['Avance_%'].max() * 1.15, 100)])
                )
                st.plotly_chart(fig_avance, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar avance por UE")
        
        st.markdown("---")
        
        st.subheader("Tabla Detallada de Adquisiciones")

        col_busq, col_sel = st.columns([2, 3])

        with col_busq:
            busqueda_adq = st.text_input("🔎 Buscar en descripción:", "")

        with col_sel:
            adquisiciones_disponibles = df_adq_filtrado['Descripción'].unique().tolist()
            adquisiciones_seleccionadas = st.multiselect(
                "Filtrar por Adquisición:",
                options=adquisiciones_disponibles,
                default=[],
                placeholder="Seleccionar adquisiciones..."
            )

        df_adq_tabla = df_adq_filtrado.copy()

        if adquisiciones_seleccionadas:
            df_adq_tabla = df_adq_tabla[df_adq_tabla['Descripción'].isin(adquisiciones_seleccionadas)]

        if busqueda_adq:
            df_adq_tabla = df_adq_tabla[
                df_adq_tabla['Descripción'].str.contains(busqueda_adq, case=False, na=False) |
                df_adq_tabla['Proveedor'].str.contains(busqueda_adq, case=False, na=False)
            ]
        
        df_adq_display = df_adq_tabla[['Año', 'UE', 'Meta', 'Código', 'Descripción', 'Tipo_Servicio', 'Tipo_Proceso', 'Estado', 'Monto_Referencial', 'Monto_Adjudicado', 'Proveedor', 'Avance_%']].copy()
        df_adq_display['Monto_Referencial'] = df_adq_display['Monto_Referencial'].apply(lambda x: f"S/ {x:,.0f}")
        df_adq_display['Monto_Adjudicado'] = df_adq_display['Monto_Adjudicado'].apply(lambda x: f"S/ {x:,.0f}")

        seleccion = st.dataframe(
            df_adq_display,
            use_container_width=True,
            hide_index=True,
            height=400,
            on_select="rerun",
            selection_mode="single-row",
            key="tabla_adquisiciones"
        )

        if seleccion and seleccion.selection and seleccion.selection.rows:
            fila_seleccionada = seleccion.selection.rows[0]
            codigo_seleccionado_tabla = df_adq_display.iloc[fila_seleccionada]['Código']
            mostrar_detalle_adquisicion(codigo_seleccionado_tabla)

        st.caption(f"Mostrando {len(df_adq_tabla)} de {len(df_adquisiciones)} adquisiciones totales")

with tabs[1]:
    st.header("Importar y Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Importar Programación Anual")
        
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
                try:
                    exito, mensaje = procesar_archivo_programacion(db, archivo_carga, año_importacion)
                    
                    if exito:
                        st.success(f"✅ {mensaje}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {mensaje}")
                finally:
                    db.close()
    
    with col2:
        st.subheader("Exportar Reportes")
        
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
                    
                    if len(df_adquisiciones) > 0:
                        df_adquisiciones.to_excel(writer, sheet_name='Adquisiciones', index=False)
                    
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

st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>Dashboard de Programación Presupuestal</p>
    <p>Última actualización: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
</div>
""", unsafe_allow_html=True)
