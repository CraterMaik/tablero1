# Replit Agent Instructions

## Overview

This is a **Dashboard de Adquisiciones** (Acquisitions Dashboard) - a comprehensive data visualization and management application built with Streamlit and PostgreSQL. The application provides interactive dashboards for tracking and analyzing acquisition data across multiple organizational departments, including budget monitoring, spending patterns, procurement metrics, data import/export capabilities, configurable alerts, year-over-year comparisons, and future spending projections.

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
- **Charts**: Line charts, bar charts, pie charts, grouped comparisons, and trend visualizations

### Data Processing
- **Technology**: Pandas with NumPy
- **Rationale**: Industry-standard data manipulation libraries that integrate seamlessly with Streamlit and Plotly
- **Features**:
  - DataFrame operations for data aggregation and transformation
  - Statistical calculations for projections
  - Data import from Excel files

### Database
- **Technology**: PostgreSQL with SQLAlchemy ORM
- **Rationale**: Provides persistent storage for real acquisition data, budgets, and alert configurations
- **Schema**:
  - **Direcciones** (Departments): Administrative units
  - **Metas** (Goals/Categories): Acquisition categories (Equipment, Infrastructure, Technology, Training, Services)
  - **Presupuestos** (Budgets): Annual budget allocations by department
  - **Adquisiciones** (Acquisitions): Individual acquisition records with code, amount, status
  - **Alertas** (Alerts): Configurable budget threshold alerts

### Report Generation
- **Technology**: ReportLab (PDF), XlsxWriter (Excel), Kaleido (Image Export)
- **Rationale**: Enables professional report generation with embedded charts and formatted data
- **Features**: 
  - Excel: Multi-sheet workbooks with native Excel charts (column and pie)
  - PDF: Styled documents with embedded Plotly chart images (PNG format)
  - Chart Export: Kaleido library with Chromium for PNG generation from Plotly graphs

## Feature Modules

### 1. Dashboard Principal (Main Dashboard)
- Executive summary with key metrics (total acquisitions, spending, budget, execution percentage)
- Analysis by department with bar charts
- Budget vs actual spending comparison with status indicators
- Analysis by goal/category with pie and bar charts
- Temporal trends (yearly and monthly evolution)
- Detailed acquisition table with search functionality
- Interactive filters: year, department, goal, status

### 2. Importar/Exportar (Import/Export)
- **Import**: Load data from Excel (.xlsx) or CSV (.csv) files for mass updates
  - Supported types: acquisitions, budgets
  - Automatic validation: column presence, value ranges, valid states
  - Real-time error reporting with descriptive messages
- **Export**: Generate comprehensive reports in PDF or Excel format with embedded charts
  - Excel: Multiple sheets (acquisitions, budgets, comparisons) + native Excel charts (column and pie)
  - PDF: Formatted summary tables + Plotly graphs exported as PNG images

### 3. Alertas (Alerts)
- Configurable budget threshold alerts per department
- Visual display of active alerts
- Real-time alert triggering when spending exceeds thresholds
- Alert management (create, delete)

### 4. Comparativas (Year-over-Year Comparisons)
- Side-by-side year comparison
- Variation analysis by department
- Percentage and absolute difference calculations
- Grouped bar charts for visual comparison

### 5. Proyecciones (Future Projections)
- Statistical projections based on historical trends
- Average growth rate calculation
- Visual representation of historical data + projection
- Methodology transparency

## Data Structure

### Direcciones (Departments)
- Nombre (Name)
- Activo (Active status)

### Metas (Goals/Categories)
- Nombre (Name)
- Activo (Active status)

### Presupuestos (Budgets)
- Dirección (Department reference)
- Año (Year)
- Monto (Amount)

### Adquisiciones (Acquisitions)
- Código (Unique code)
- Dirección (Department reference)
- Meta (Goal reference)
- Año (Year)
- Mes (Month 1-12)
- Descripción (Description)
- Monto (Amount)
- Estado (Status: Completado, En Proceso, Pendiente)

### Alertas (Alerts)
- Nombre (Name)
- Dirección (Optional department filter)
- Umbral_porcentaje (Threshold percentage)
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

- **app.py**: Main Streamlit application with all dashboard features
- **database.py**: SQLAlchemy models and database connection setup
- **db_operations.py**: Database utility functions (data loading, queries, import/export)
- **.streamlit/config.toml**: Streamlit server configuration

## Performance Optimization

- **Caching Strategy**: 
  - `@st.cache_data` for data loading (60-second TTL)
  - `@st.cache_resource` for database session
- **Database Connection**: Single session factory with proper cleanup
- **Data Loading**: Efficient queries with joins to minimize database calls

## Notes

- Application initializes with example data if database is empty
- **Currency Format**: All monetary values displayed in Peruvian Soles (S/) with thousand separators
- **Import Validation**: CSV and Excel files validated for required columns, value ranges, and valid states
- Filters are preserved across interactions within the same session
- Export functionality generates timestamped files with embedded charts
- Alert system checks all active alerts against current data in real-time
- Projections use simple linear growth model based on historical average
- Year-over-year comparisons calculate both percentage and absolute variations
- Chart exports require Chromium (system dependency) for Kaleido PNG generation

## Recent Changes (November 2025)

- ✅ **Currency Format**: Changed from USD ($) to Peruvian Soles (S/) throughout entire application
- ✅ **CSV Import**: Added support for CSV file imports with same validation as Excel
- ✅ **Excel Export with Charts**: Implemented native Excel charts (column and pie) in dedicated "Gráficos" sheet
- ✅ **PDF Export with Charts**: Implemented Plotly chart export as PNG images embedded in PDF reports
- ✅ **Import Validation**: Added comprehensive validation for column presence, data types, value ranges, and valid states
- ✅ **System Dependencies**: Added Chromium as system dependency for Kaleido chart rendering
- ✅ **Error Handling**: Enhanced import functionality with descriptive error messages for validation failures
