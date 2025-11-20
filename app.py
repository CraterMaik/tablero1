import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Dashboard de Adquisiciones", layout="wide", initial_sidebar_state="expanded")

@st.cache_data
def generar_datos_ejemplo():
    """Genera datos de ejemplo para el dashboard"""
    np.random.seed(42)
    
    direcciones = ["Dirección Administrativa", "Dirección de Operaciones", "Dirección de TI", 
                   "Dirección Financiera", "Dirección de RRHH"]
    
    metas = ["Equipamiento", "Infraestructura", "Tecnología", "Capacitación", "Servicios"]
    
    años = [2023, 2024, 2025]
    
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    # Generar presupuestos por año y dirección
    presupuestos = []
    for año in años:
        for direccion in direcciones:
            presupuesto_anual = np.random.randint(500000, 2000000)
            presupuestos.append({
                'Año': año,
                'Dirección': direccion,
                'Presupuesto': presupuesto_anual
            })
    
    df_presupuestos = pd.DataFrame(presupuestos)
    
    # Generar adquisiciones
    adquisiciones = []
    id_counter = 1
    
    for año in años:
        num_adquisiciones = 80 if año == 2023 else (90 if año == 2024 else 60)
        
        for _ in range(num_adquisiciones):
            direccion = np.random.choice(direcciones)
            meta = np.random.choice(metas)
            mes = np.random.choice(meses)
            mes_num = meses.index(mes) + 1
            
            # Obtener presupuesto de la dirección
            presupuesto_dir = df_presupuestos[
                (df_presupuestos['Año'] == año) & 
                (df_presupuestos['Dirección'] == direccion)
            ]['Presupuesto'].values[0]
            
            # Generar monto proporcional al presupuesto
            monto = np.random.randint(5000, int(presupuesto_dir * 0.15))
            
            adquisiciones.append({
                'ID': f"ADQ-{id_counter:04d}",
                'Dirección': direccion,
                'Meta': meta,
                'Año': año,
                'Mes': mes,
                'Mes_Num': mes_num,
                'Fecha': f"{mes_num:02d}/{año}",
                'Descripción': f"{meta} - {direccion[:20]}",
                'Monto': monto,
                'Estado': np.random.choice(['Completado', 'En Proceso', 'Pendiente'], p=[0.7, 0.2, 0.1])
            })
            id_counter += 1
    
    df_adquisiciones = pd.DataFrame(adquisiciones)
    
    return df_adquisiciones, df_presupuestos

# Cargar datos
df_adquisiciones, df_presupuestos = generar_datos_ejemplo()

# Título principal
st.title("📊 Dashboard de Control de Adquisiciones")
st.markdown("---")

# Sidebar - Filtros
st.sidebar.header("🔍 Filtros")

# Filtro de año
años_disponibles = sorted(df_adquisiciones['Año'].unique())
año_seleccionado = st.sidebar.selectbox(
    "Seleccionar Año",
    options=["Todos"] + años_disponibles,
    index=0
)

# Filtro de dirección
direcciones_disponibles = sorted(df_adquisiciones['Dirección'].unique())
direccion_seleccionada = st.sidebar.multiselect(
    "Seleccionar Dirección/Área",
    options=direcciones_disponibles,
    default=direcciones_disponibles
)

# Filtro de meta
metas_disponibles = sorted(df_adquisiciones['Meta'].unique())
meta_seleccionada = st.sidebar.multiselect(
    "Seleccionar Meta",
    options=metas_disponibles,
    default=metas_disponibles
)

# Filtro de estado
estados_disponibles = df_adquisiciones['Estado'].unique()
estado_seleccionado = st.sidebar.multiselect(
    "Seleccionar Estado",
    options=estados_disponibles,
    default=estados_disponibles
)

st.sidebar.markdown("---")
st.sidebar.info("💡 Usa los filtros para explorar los datos de adquisiciones por año, dirección y meta.")

# Aplicar filtros
df_filtrado = df_adquisiciones.copy()

if año_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Año'] == año_seleccionado]

if direccion_seleccionada:
    df_filtrado = df_filtrado[df_filtrado['Dirección'].isin(direccion_seleccionada)]

if meta_seleccionada:
    df_filtrado = df_filtrado[df_filtrado['Meta'].isin(meta_seleccionada)]

if estado_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['Estado'].isin(estado_seleccionado)]

# SECCIÓN 1: RESUMEN EJECUTIVO
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
        value=f"${monto_total:,.0f}",
        delta=f"{(monto_total/1000000):.1f}M"
    )

with col3:
    # Calcular presupuesto total según filtros
    if año_seleccionado != "Todos":
        df_pres_filtrado = df_presupuestos[df_presupuestos['Año'] == año_seleccionado]
    else:
        df_pres_filtrado = df_presupuestos
    
    if direccion_seleccionada:
        df_pres_filtrado = df_pres_filtrado[df_pres_filtrado['Dirección'].isin(direccion_seleccionada)]
    
    presupuesto_total = df_pres_filtrado['Presupuesto'].sum()
    st.metric(
        label="Presupuesto Total",
        value=f"${presupuesto_total:,.0f}",
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

# SECCIÓN 2: ANÁLISIS POR DIRECCIÓN
st.header("🏢 Análisis por Dirección/Área")

col1, col2 = st.columns(2)

with col1:
    # Gasto por dirección
    gasto_por_dir = df_filtrado.groupby('Dirección')['Monto'].sum().reset_index()
    gasto_por_dir = gasto_por_dir.sort_values('Monto', ascending=False)
    
    fig_dir = px.bar(
        gasto_por_dir,
        x='Monto',
        y='Dirección',
        orientation='h',
        title="Gasto Total por Dirección",
        labels={'Monto': 'Monto ($)', 'Dirección': 'Dirección'},
        color='Monto',
        color_continuous_scale='Blues'
    )
    fig_dir.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_dir, use_container_width=True)

with col2:
    # Número de adquisiciones por dirección
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
    st.plotly_chart(fig_adq_dir, use_container_width=True)

st.markdown("---")

# SECCIÓN 3: ANÁLISIS DE PRESUPUESTO VS GASTO
st.header("💰 Presupuesto vs Gasto por Dirección")

# Calcular gasto y presupuesto por dirección y año
if año_seleccionado != "Todos":
    años_analisis = [año_seleccionado]
else:
    años_analisis = años_disponibles

datos_comparacion = []
for año in años_analisis:
    for direccion in direccion_seleccionada if direccion_seleccionada else direcciones_disponibles:
        gasto = df_adquisiciones[
            (df_adquisiciones['Año'] == año) & 
            (df_adquisiciones['Dirección'] == direccion)
        ]['Monto'].sum()
        
        presupuesto = df_presupuestos[
            (df_presupuestos['Año'] == año) & 
            (df_presupuestos['Dirección'] == direccion)
        ]['Presupuesto'].values[0]
        
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

# Gráfico de comparación
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
    yaxis_title='Monto ($)',
    barmode='group',
    height=500,
    xaxis_tickangle=-45
)

st.plotly_chart(fig_comp, use_container_width=True)

# Tabla de indicadores de estatus
st.subheader("📊 Indicadores de Estatus por Dirección")

def obtener_estatus(porcentaje):
    if porcentaje < 75:
        return "✅ Dentro de Presupuesto"
    elif porcentaje < 95:
        return "⚠️ En Riesgo"
    else:
        return "🚨 Excedido/Crítico"

df_comparacion['Estatus'] = df_comparacion['Porcentaje'].apply(obtener_estatus)

# Formatear la tabla
df_tabla = df_comparacion.copy()
df_tabla['Presupuesto'] = df_tabla['Presupuesto'].apply(lambda x: f"${x:,.0f}")
df_tabla['Gasto'] = df_tabla['Gasto'].apply(lambda x: f"${x:,.0f}")
df_tabla['Disponible'] = df_tabla['Disponible'].apply(lambda x: f"${x:,.0f}")
df_tabla['Porcentaje'] = df_tabla['Porcentaje'].apply(lambda x: f"{x:.1f}%")

st.dataframe(
    df_tabla[['Año', 'Dirección', 'Presupuesto', 'Gasto', 'Disponible', 'Porcentaje', 'Estatus']],
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# SECCIÓN 4: ANÁLISIS POR META
st.header("🎯 Análisis por Meta")

col1, col2 = st.columns(2)

with col1:
    # Distribución de gasto por meta
    gasto_por_meta = df_filtrado.groupby('Meta')['Monto'].sum().reset_index()
    
    fig_meta_pie = px.pie(
        gasto_por_meta,
        values='Monto',
        names='Meta',
        title='Distribución de Gasto por Meta',
        hole=0.4
    )
    fig_meta_pie.update_layout(height=400)
    st.plotly_chart(fig_meta_pie, use_container_width=True)

with col2:
    # Gasto por meta (barras)
    gasto_por_meta_sorted = gasto_por_meta.sort_values('Monto', ascending=False)
    
    fig_meta_bar = px.bar(
        gasto_por_meta_sorted,
        x='Meta',
        y='Monto',
        title='Gasto Total por Meta',
        labels={'Monto': 'Monto ($)', 'Meta': 'Meta'},
        color='Monto',
        color_continuous_scale='Oranges'
    )
    fig_meta_bar.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_meta_bar, use_container_width=True)

st.markdown("---")

# SECCIÓN 5: TENDENCIAS TEMPORALES
st.header("📅 Tendencias Temporales")

if año_seleccionado == "Todos":
    # Gasto por año
    gasto_por_año = df_filtrado.groupby('Año')['Monto'].sum().reset_index()
    
    fig_año = px.line(
        gasto_por_año,
        x='Año',
        y='Monto',
        title='Evolución del Gasto por Año',
        markers=True,
        labels={'Monto': 'Monto ($)', 'Año': 'Año'}
    )
    fig_año.update_traces(line_color='#1f77b4', marker_size=10)
    fig_año.update_layout(height=400)
    st.plotly_chart(fig_año, use_container_width=True)
    
    # Gasto mensual por año
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
        labels={'Monto': 'Monto ($)', 'Periodo': 'Periodo'}
    )
    fig_mensual.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_mensual, use_container_width=True)
else:
    # Para un año específico, mostrar tendencia mensual
    df_año = df_filtrado[df_filtrado['Año'] == año_seleccionado].copy()
    gasto_mensual_año = df_año.groupby(['Mes', 'Mes_Num'])['Monto'].sum().reset_index()
    gasto_mensual_año = gasto_mensual_año.sort_values('Mes_Num')
    
    fig_mensual_año = px.bar(
        gasto_mensual_año,
        x='Mes',
        y='Monto',
        title=f'Gasto Mensual - Año {año_seleccionado}',
        labels={'Monto': 'Monto ($)', 'Mes': 'Mes'},
        color='Monto',
        color_continuous_scale='Viridis'
    )
    fig_mensual_año.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_mensual_año, use_container_width=True)

st.markdown("---")

# SECCIÓN 6: TABLA DETALLADA
st.header("📋 Detalle de Adquisiciones")

# Búsqueda
busqueda = st.text_input("🔎 Buscar en descripción o ID:", "")

df_tabla_detalle = df_filtrado.copy()

if busqueda:
    df_tabla_detalle = df_tabla_detalle[
        df_tabla_detalle['ID'].str.contains(busqueda, case=False, na=False) |
        df_tabla_detalle['Descripción'].str.contains(busqueda, case=False, na=False)
    ]

# Ordenar por monto descendente
df_tabla_detalle = df_tabla_detalle.sort_values('Monto', ascending=False)

# Formatear monto para display
df_tabla_display = df_tabla_detalle[['ID', 'Dirección', 'Meta', 'Año', 'Mes', 'Descripción', 'Monto', 'Estado']].copy()
df_tabla_display['Monto'] = df_tabla_display['Monto'].apply(lambda x: f"${x:,.0f}")

st.dataframe(
    df_tabla_display,
    use_container_width=True,
    hide_index=True,
    height=400
)

# Resumen de la tabla
st.caption(f"Mostrando {len(df_tabla_detalle)} de {len(df_adquisiciones)} adquisiciones totales")

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    <p>Dashboard de Control de Adquisiciones - Generado con Streamlit</p>
    <p>Última actualización: {}</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
