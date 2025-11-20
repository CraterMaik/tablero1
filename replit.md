# Replit Agent Instructions

## Overview

This is a **Dashboard de Programación Presupuestal** (Budget Programming Dashboard) - a comprehensive data visualization and management application built with Streamlit and PostgreSQL. The application provides interactive dashboards for tracking and analyzing government budget execution data ("programación anual específica") across multiple organizational units (Unidades Ejecutoras), including budget allocation monitoring, certified spending tracking, execution percentages, data import/export capabilities, configurable alerts, and year-over-year comparisons.

## User Preferences

Preferred communication style: Simple, everyday language in Spanish.

## System Architecture

### Frontend Framework
- **Technology**: Streamlit
- **Rationale**: Streamlit provides rapid development of interactive data applications with minimal boilerplate code, making it ideal for analytical dashboards
- **Key Features**: 
  - Wide layout configuration for better data visualization
  - Expandable sidebar for filters and controls
  - Cached data loading for performance optimization
  - Tabbed interface for organizing multiple features
  - File upload/download capabilities

### Data Visualization
- **Technology**: Plotly (Express and Graph Objects)
- **Rationale**: Plotly offers interactive, publication-quality graphs that enhance user engagement and data exploration
- **Charts**: Bar charts (horizontal and vertical), grouped comparisons, and execution percentage visualizations

### Data Processing
- **Technology**: Pandas with NumPy
- **Rationale**: Industry-standard data manipulation libraries that integrate seamlessly with Streamlit and Plotly
- **Features**:
  - DataFrame operations for data aggregation and transformation
  - Hierarchical data extraction from Excel files
  - Data import from Excel (.xlsx) format

### Database
- **Technology**: PostgreSQL with SQLAlchemy ORM
- **Rationale**: Provides persistent storage for government budget data and alert configurations
- **Schema**:
  - **UnidadEjecutora** (Executive Units): Government organizational units (UEs) identified by code
  - **MetaPresupuestal** (Budget Goals): Budget allocation categories with codes and descriptions
  - **ProgramacionPresupuestal** (Budget Programming): Detailed budget records with PIM, certified spending, and execution data
  - **Adquisicion** (Acquisitions): Procurement process records with codes, states, amounts, dates, and providers
  - **Alerta** (Alerts): Configurable budget threshold alerts per UE

### Report Generation
- **Technology**: ReportLab (PDF), XlsxWriter (Excel), Kaleido (Image Export)
- **Rationale**: Enables professional report generation with embedded charts and formatted data
- **Features**: 
  - Excel: Multi-sheet workbooks with native Excel charts (column format)
  - PDF: Styled documents with embedded Plotly chart images (PNG format)
  - Chart Export: Kaleido library with Chromium for PNG generation from Plotly graphs

## Feature Modules

### 1. Presupuestal General (Main Budget Dashboard)
- Executive summary with key metrics:
  - Total Registros: Total number of budget records (filtered)
  - PIM Total: Total budget allocation (Presupuesto Institucional Modificado)
  - Certificado Total: Total certified spending
  - % Ejecución: Overall execution percentage (Certificado/PIM * 100)
- Analysis by Unidad Ejecutora (UE):
  - Grouped bar chart showing PIM and Certificado by UE
  - Bar chart showing % Ejecución by UE
- Detailed budget table with filterable data
- Interactive filters (in sidebar): Año (Year - first), Meta (Budget Goal), UE (Executive Unit)
- **Navbar lateral**: Detalle por Clasificador section showing breakdown by specific clasificador with filters applied

### 2. Adquisiciones (Acquisitions Dashboard)
- Executive summary with key metrics:
  - Total Adquisiciones: Total number of acquisitions (filtered)
  - Monto Referencial Total: Total referential amount
  - Monto Adjudicado Total: Total awarded amount
  - % Avance: Progress percentage (Adjudicado/Referencial * 100)
- Analysis visualizations:
  - Pie chart showing acquisitions by Estado (Status)
  - Grouped bar chart showing Monto Referencial and Monto Adjudicado by UE
- Detailed acquisitions table with filterable data
- Same interactive filters as Presupuestal General tab

### 3. Importar/Exportar (Import/Export)
- **Import**: Load programación anual específica from Excel (.xlsx) files
  - Hierarchical structure parsing (UE → Meta → Clasificador)
  - Automatic extraction of UE codes, Meta codes, and Clasificador from description column
  - Column mapping: PIM, CERTIFICADO, PIM POR CERTIFICAR, TOTAL ANUAL, SALDO, etc.
  - Real-time error reporting with descriptive messages
  - Year specification for multi-year data management
- **Export**: Generate comprehensive reports in PDF or Excel format
  - Excel: Multiple sheets (Programación, Resumen_UE, Datos_Gráficos) + native Excel charts
  - PDF: Formatted summary tables + Plotly graphs exported as PNG images

### 3. Alertas (Alerts)
- Configurable budget execution threshold alerts
- Alert creation with:
  - Alert name
  - Optional UE filter (or "Todas" for all UEs)
  - Execution percentage threshold (0-100%)
- Visual display of active alerts
- Real-time alert status checking against current execution data
- Alert management (create, delete)

### 4. Análisis Comparativo (Year-over-Year Comparisons)
- Side-by-side year comparison
- Variation analysis by UE
- Percentage and absolute difference calculations
- Grouped bar charts for visual comparison
- Requires at least 2 years of data

## Data Structure

### UnidadEjecutora (Executive Units)
- Código (Code): Unique UE identifier (e.g., CIDE, DNCE, DNCN, DTDIS)
- Nombre (Name): Full name of the unit
- Activo (Active status)

### MetaPresupuestal (Budget Goals)
- Código (Code): Meta identifier (e.g., 0046, 0013)
- Descripción (Description): Full description of the budget goal
- Activo (Active status)

### ProgramacionPresupuestal (Budget Programming)
- Año (Year): Fiscal year
- Unidad Ejecutora (UE reference)
- Meta (Budget goal reference, optional)
- Clasificador (Budget classifier code)
- Descripción Clasificador (Classifier description)
- **Budget Metrics**:
  - **PIM**: Presupuesto Institucional Modificado (Modified Institutional Budget)
  - **CERTIFICADO**: Certified spending amount
  - **PIM POR CERTIFICAR**: Remaining budget to certify
  - **COMPROMISO_ANUAL**: Annual commitment
  - **DEVENGADO_ACUMULADO**: Accumulated accrued expenses
  - **COMPROMISO_POR_DEVENGAR**: Commitment pending accrual
  - **PIM_POR_DEVENGAR**: Budget pending accrual
  - **TOTAL_ANUAL**: Total annual amount
  - **SALDO**: Balance

### Alertas (Alerts)
- Nombre (Name)
- Unidad Ejecutora (Optional UE filter)
- Umbral_porcentaje (Threshold percentage for execution alert)
- Activo (Active status)

## External Dependencies

### Python Libraries
- **streamlit**: Core application framework
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive data visualization
- **kaleido**: Plotly chart export to static images (PNG)
- **numpy**: Numerical computing
- **sqlalchemy**: ORM for database operations
- **psycopg2-binary**: PostgreSQL adapter
- **openpyxl**: Excel file reading (supports .xlsx)
- **xlsxwriter**: Excel file writing with native chart support
- **reportlab**: PDF generation with tables and images
- **pillow**: Image processing for PDF reports

### System Dependencies
- **chromium**: Web browser required by Kaleido for rendering Plotly charts to PNG images

### Database
- PostgreSQL (Neon-backed via Replit integration)
- Environment variables: DATABASE_URL, PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE

## Application Files

- **app.py**: Main Streamlit application with all dashboard features (522 lines)
- **database.py**: SQLAlchemy models and database connection setup (79 lines)
- **db_operations.py**: Database utility functions for data loading, Excel import, queries, and alert management (176 lines)
- **.streamlit/config.toml**: Streamlit server configuration

## Performance Optimization

- **Caching Strategy**: 
  - `@st.cache_data` for data loading (60-second TTL)
  - Fresh database sessions for each tab to avoid SSL connection issues
- **Database Connection**: Session factory with proper try/finally cleanup
- **Data Loading**: Efficient queries with joins to minimize database calls

## Data Import Process

### Excel File Structure (Programación Anual Específica)
The import function expects Excel files with the following structure:
1. **Header rows**: First 4 rows are skipped (contain metadata)
2. **Column structure**: 14 columns (Descripcion, PIM, CERTIFICADO, PIM_POR_CERTIFICAR, etc.)
3. **Hierarchical data**:
   - **UE rows**: Single code (e.g., "DNCE", "CIDE") triggers creation of new UE context
   - **Meta rows**: Code starting with "0" and containing " - " (e.g., "0046 - META DESCRIPTION")
   - **Clasificador rows**: All other rows with numeric PIM values, may start with classifier code (e.g., "2.3. DESCRIPTION")

### Import Logic
1. Parse Excel file starting from row 5
2. Iterate through rows:
   - If row matches UE pattern (3-5 uppercase letters), create/select UE
   - If row matches Meta pattern (starts with "0" + " - "), create/select Meta
   - Otherwise, create ProgramacionPresupuestal record with current UE and Meta context
3. Extract Clasificador code from description if present
4. Store all numeric budget metrics

## Notes

- **Currency Format**: All monetary values displayed in Peruvian Soles (S/) with thousand separators
- **Import Validation**: Excel files validated for required columns and hierarchical structure
- **One File Per Year**: Users upload separate Excel files for each fiscal year
- Filters are preserved across interactions within the same session
- Export functionality generates timestamped files with embedded charts
- Alert system checks all active alerts against current execution data in real-time
- Year-over-year comparisons calculate both percentage and absolute variations
- Chart exports require Chromium (system dependency) for Kaleido PNG generation
- Database sessions use try/finally blocks to ensure proper cleanup and avoid SSL errors

## Recent Changes (November 2025)

### Phase 1: Initial Migration (Early November)
- ✅ **Complete Schema Restructure**: Migrated from acquisitions model to government budget programming model
  - Old schema: Direcciones, Metas, Presupuestos, Adquisiciones
  - New schema: UnidadEjecutora, MetaPresupuestal, ProgramacionPresupuestal, Alertas
- ✅ **Excel Parser**: Implemented hierarchical data extraction for programación anual específica files
  - Parses UE codes, Meta codes, and Clasificador from description column
  - Handles 14 budget metric columns including PIM, CERTIFICADO, DEVENGADO, etc.
  - **Critical Fix (Nov 20)**: Corrected parser logic to detect UE/Meta rows BEFORE filtering on PIM values
    - UE and Meta rows have empty PIM cells, so must be detected first
    - Parser now checks pattern matching before numeric validation
- ✅ **Data Import**: Successfully imported 725 budget records for 2024 from provided Excel file
  - 12 government units (UEs): CIDE, DNCE, DNCN, DTDIS, DTIE, ENEI, OTA, OTAJ, OTD, OTED, OTIN, OTPP
  - 26 budget goals (Metas) extracted from data

### Phase 2: Dashboard Reorganization (Late November)
- ✅ **Expanded Database Schema**: Added Adquisicion table for procurement tracking
  - Fields: año, UE, meta, código_adquisición, descripción, tipo_proceso, estado, montos, fechas, proveedor
- ✅ **Generated Seed Data**: Created comprehensive test data for 2024 and 2025
  - 1,094 Programación Presupuestal records
  - 548 Adquisicion records
  - 12 Unidades Ejecutoras
  - 10 Metas Presupuestales
- ✅ **Complete Dashboard Reorganization**: Restructured entire application with dual-tab architecture
  - **New Tab 1 - Presupuestal General**: Budget programming dashboard with PIM/Certificado metrics and visualizations
  - **New Tab 2 - Adquisiciones**: Procurement dashboard with referential/adjudicated amounts and status tracking
  - Maintained secondary tabs: Importar/Exportar, Alertas, Análisis Comparativo
- ✅ **Filter Reorganization**: Changed filter order in sidebar for better UX
  - New order: Año (first), Meta, UE
  - All filters apply to both main tabs
- ✅ **Navbar Lateral Implementation**: Added "Detalle por Clasificador" sidebar section
  - Allows drilling down into specific budget classifiers
  - Shows breakdown by UE with filtered metrics
  - Respects all active filters (año, meta, UE)
- ✅ **Database Session Management**: Enhanced caching and session handling
  - Applied @st.cache_data(ttl=60) to both data loading functions
  - Proper try/finally blocks for session cleanup
  - Minimized SSL connection issues
- ✅ **Data Query Functions**: Added obtener_adquisiciones_df() for procurement data retrieval
- ✅ **Currency Format**: Maintained Peruvian Soles (S/) format throughout both dashboards
