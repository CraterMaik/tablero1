# Replit Agent Instructions

## Overview

This project is a **Dashboard de Programación Presupuestal** (Budget Programming Dashboard), a Streamlit and PostgreSQL application for visualizing and managing government budget execution data. It offers interactive dashboards for tracking budget allocation, certified spending, execution percentages, and procurement processes across various organizational units. Key capabilities include data import/export, configurable alerts, and year-over-year comparisons to provide comprehensive financial oversight.

## User Preferences

Preferred communication style: Simple, everyday language in Spanish.

## System Architecture

### UI/UX
- **Frontend Framework**: Streamlit for rapid interactive data application development.
- **Data Visualization**: Plotly (Express and Graph Objects) for interactive, high-quality charts like bar charts and execution percentage visualizations.
- **Layout**: Wide layout, expandable sidebar for filters, and a tabbed interface for organizing features.
- **Reporting**: ReportLab for PDF, XlsxWriter for Excel with native charts, and Kaleido for image export of Plotly graphs.

### Technical Implementations
- **Data Processing**: Pandas with NumPy for robust data manipulation, aggregation, and transformation, including hierarchical data extraction from Excel.
- **Database**: PostgreSQL with SQLAlchemy ORM for persistent storage of budget, acquisition, and alert data.
  - **Schema**: Includes `UnidadEjecutora`, `MetaPresupuestal`, `ProgramacionPresupuestal`, `Adquisicion` (with `AdquisicionDetalle` and `AdquisicionProceso`), and `Alerta` tables.
- **Performance**: Utilizes `st.cache_data` for efficient data loading with a 60-second TTL and fresh database sessions to optimize performance and stability.

### Feature Specifications
- **Presupuestal General Dashboard**: Displays executive summaries, grouped bar charts of PIM and Certificado by `Unidad Ejecutora`, execution percentage, and a detailed budget table. Includes filters for `Año`, `Meta`, and `Unidad Ejecutora`.
- **Adquisiciones Dashboard**: Presents an executive summary of acquisitions, visualizations by `Estado`, and grouped bar charts of `Monto Referencial` vs `Monto Adjudicado` by `Unidad Ejecutora`. Features a detailed acquisitions table and an interactive modal for viewing `AdquisicionDetalle` and `AdquisicionProceso` timelines.
- **Import/Export**: Facilitates importing `programación anual específica` from Excel (parsing hierarchical data) and exporting comprehensive reports in PDF or Excel formats with embedded charts.
- **Alerts**: Allows configuration of budget execution threshold alerts per `Unidad Ejecutora` or globally, with real-time status checking and management.
- **Análisis Comparativo**: Enables side-by-side year-over-year comparisons with variation analysis and visual representations.

## External Dependencies

- **Python Libraries**:
    - `streamlit`: Core application framework.
    - `pandas`, `numpy`: Data manipulation and analysis.
    - `plotly`: Interactive data visualizations.
    - `kaleido`: Plotly chart export to static images.
    - `sqlalchemy`, `psycopg2-binary`: ORM and PostgreSQL adapter.
    - `openpyxl`, `xlsxwriter`: Excel file reading and writing.
    - `reportlab`, `pillow`: PDF generation and image processing.
- **System Dependencies**:
    - `chromium`: Required by Kaleido for rendering Plotly charts to PNG images.
- **Database**:
    - PostgreSQL: Used as the primary database, integrated via Replit with environment variables (`DATABASE_URL`, `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`).

## Recent Changes (November 2025)

### Phase 1: Database Schema & Modal Implementation (November 20)
- ✅ **Enhanced Database Schema**: Added detailed tracking for acquisition processes
  - **AdquisicionDetalle**: Stores requerimientos, tipo_servicio, PIM asignado, unidad responsable
  - **AdquisicionProceso**: Tracks process steps with orden, hito, tipo_flujo, fechas, días, responsables
  - One-to-one relationship: Adquisicion → AdquisicionDetalle
  - One-to-many relationship: Adquisicion → AdquisicionProceso (ordered)
- ✅ **Expanded Seed Data**: Generated comprehensive process tracking data
  - 548 acquisition details (1 per acquisition)
  - 3,533 process steps (~5-8 steps per acquisition)
  - Deterministic generation with alternating OTIN/OTA workflow pattern
- ✅ **Modal Interface for Acquisition Details**: Implemented interactive modal using @st.dialog
  - Opens on selection from Adquisiciones table via selectbox + button
  - Displays comprehensive acquisition information:
    - Header with código, descripción, PIM asignado
    - KPI cards: requerimientos, estado, montos
    - Timeline visualization with Plotly showing process flow (OTIN → OTA)
    - Total días calculation across all process steps
    - Detailed process table with fechas, responsables, comentarios
- ✅ **Timeline Visualization**: Created horizontal Plotly timeline chart
  - Color-coded by tipo_flujo (OTIN: orange, OTA: green)
  - Shows fecha_inicio → fecha_fin for each step
  - Hover data includes días and responsable
  - Chronological ordering of process steps
- ✅ **Removed Sidebar Classifier Detail**: Eliminated "Detalle por Clasificador" from sidebar
  - Simplified sidebar to only show filters (Año, Meta, UE)
  - Moved functionality to main dashboard
- ✅ **Integrated Classifier Charts in Main Dashboard**: Added visualizations directly in Presupuestal General tab
  - Top 10 clasificadores bar chart (horizontal) showing PIM vs Certificado
  - Treemap visualization of budget distribution by clasificador
  - Both charts respect all active filters (año, meta, UE)
  - Positioned before detailed table for better visibility
- ✅ **Selector for Acquisitions**: Enhanced table interaction
  - Selectbox to choose acquisition from filtered results
  - "Ver Detalle" button to open modal
  - Table with selection_mode enabled for visual feedback

### Phase 2: SSL Connection Error Resolution (November 20)
- ✅ **Fixed Critical SSL Connection Error**: Resolved "SSL connection has been closed unexpectedly" errors
  - **Root Cause**: PostgreSQL connections were being reused after being closed by the server
  - **Solution**: Configured SQLAlchemy engine with connection pool management:
    - `pool_pre_ping=True`: Verifies connection is alive before using it
    - `pool_recycle=3600`: Recycles connections every hour to prevent stale connections
    - `pool_size=5`: Maintains 5 connections in the pool
    - `max_overflow=10`: Allows up to 10 additional temporary connections
- ✅ **Improved Database Session Management**:
  - Modified `obtener_programacion_df()` and `obtener_adquisiciones_df()` to create their own sessions
  - Functions can work standalone or receive an existing session
  - Proper try/finally blocks ensure sessions are always closed
  - Simplified cached functions in app.py to avoid session management issues
- ✅ **Verified Fix**: Comprehensive testing confirmed:
  - No SSL errors when changing filters multiple times
  - Smooth operation across both tabs (Presupuestal General, Adquisiciones)
  - Stable performance with year, meta, and UE filter combinations

### Phase 3: Additional Acquisition Analytics (November 20)
- ✅ **New Monthly Spending Chart**: Added "Gasto por Mes" visualization
  - Bar chart showing acquisitions spending grouped by month
  - Extracts month from Fecha_Adjudicacion field
  - Shows total Monto_Adjudicado per month
  - Respects all active filters (year, meta, UE)
  - Displays only months with adjudicated acquisitions
- ✅ **Top 10 Spending Chart**: Added "Top 10 Más Gastadas" visualization
  - Horizontal bar chart showing top 10 acquisitions by spending
  - Ordered by Monto_Adjudicado (highest to lowest)
  - Truncated descriptions for better readability
  - Hover shows full details (code, description, amount)
  - Respects all active filters