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