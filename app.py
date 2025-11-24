import streamlit as st

st.set_page_config(
    page_title="Sistema de Gestión Presupuestal - INEI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .hero-section {
        background: linear-gradient(135deg, #1a3a6c 0%, #2c5aa0 100%);
        padding: 60px 40px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .hero-title {
        font-size: 48px;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .hero-subtitle {
        font-size: 20px;
        opacity: 0.9;
        margin-bottom: 30px;
    }
    .feature-card {
        background: white;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        height: 100%;
        border: 1px solid #e0e0e0;
    }
    .feature-icon {
        font-size: 48px;
        margin-bottom: 15px;
    }
    .feature-title {
        font-size: 20px;
        font-weight: 600;
        color: #1a3a6c;
        margin-bottom: 10px;
    }
    .feature-desc {
        color: #666;
        font-size: 14px;
    }
    .stats-container {
        background: #f8f9fa;
        padding: 30px;
        border-radius: 10px;
        margin: 30px 0;
    }
    .stat-item {
        text-align: center;
        padding: 20px;
    }
    .stat-value {
        font-size: 36px;
        font-weight: 700;
        color: #1a3a6c;
    }
    .stat-label {
        color: #666;
        font-size: 14px;
    }
    .cta-button {
        background: #2c5aa0;
        color: white;
        padding: 15px 40px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 18px;
        font-weight: 600;
        display: inline-block;
        margin-top: 20px;
    }
    .footer {
        text-align: center;
        color: #666;
        padding: 40px 20px;
        border-top: 1px solid #e0e0e0;
        margin-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-section">
    <div class="hero-title">Sistema de Gestión Presupuestal</div>
    <div class="hero-subtitle">Plataforma integral para el seguimiento y control de adquisiciones y programación presupuestal</div>
</div>
""", unsafe_allow_html=True)

# Botón para ir al Dashboard
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🚀 Ir al Dashboard", use_container_width=True, type="primary"):
        st.switch_page("pages/dashboard.py")

st.markdown("<br>", unsafe_allow_html=True)

# Features Section
st.markdown("### Funcionalidades Principales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Dashboard Interactivo</div>
        <div class="feature-desc">Visualización en tiempo real de indicadores clave de gestión presupuestal</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🛒</div>
        <div class="feature-title">Gestión de Adquisiciones</div>
        <div class="feature-desc">Seguimiento completo del ciclo de adquisiciones por unidad ejecutora</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📈</div>
        <div class="feature-title">Análisis de Avance</div>
        <div class="feature-desc">Monitoreo del porcentaje de ejecución y cumplimiento de metas</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📤</div>
        <div class="feature-title">Reportes y Exportación</div>
        <div class="feature-desc">Generación de reportes en Excel y PDF para análisis detallado</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Información adicional
st.markdown("### Acerca del Sistema")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### Objetivos
    - Centralizar la información de programación presupuestal
    - Facilitar el seguimiento de adquisiciones
    - Proporcionar indicadores de gestión en tiempo real
    - Optimizar la toma de decisiones basada en datos
    """)

with col2:
    st.markdown("""
    #### Módulos Disponibles
    - **Adquisiciones**: Gestión completa del proceso de compras
    - **Importar/Exportar**: Carga masiva y generación de reportes
    - **Filtros Avanzados**: Por año, DDNNTT, meta, estado y tipo
    - **Timeline de Procesos**: Seguimiento detallado por adquisición
    """)

# Footer
st.markdown("""
<div class="footer">
    <p><strong>Sistema de Gestión Presupuestal</strong></p>
    <p>Instituto Nacional de Estadística e Informática - INEI</p>
    <p style="font-size: 12px; margin-top: 10px;">© 2025 - Todos los derechos reservados</p>
</div>
""", unsafe_allow_html=True)
