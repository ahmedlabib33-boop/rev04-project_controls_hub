# 🏗️ Project Controls Intelligence Hub

A scalable, multi-project construction/project-controls intelligence system with modern interactive design.

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
# Windows
RUN_APP.bat

# Or directly
streamlit run dashboard.py --server.port 8755
```

### Create a New Project

Simply create a new folder under `projects/`:

```bash
mkdir projects/My_New_Project
```

The system will auto-discover it and create the standard folder structure.

## 📁 Project Structure

```
projects/
  _PROJECT_TEMPLATE/          # Template for new projects
  Project_Alpha/            # Your project folders
  Project_Beta/

src/construction_system/     # Core modules
  project_catalog.py        # Auto-discovery engine
  project_context.py        # Path resolver
  database.py               # SQLite layer
  importers.py              # CSV/XLSX pipeline
  analytics.py              # KPI calculations
  steel_delay_tia.py        # Delay analysis
  contract_matcher.py       # Claims intelligence
  letters_auto_ingest.py    # Letters processing

dashboard.py                # Main Streamlit app
app.py                      # Entry point
```

## 🔧 Core Features

### Multi-Project Support
- **Stable project_id** via UUID in `project_manifest.json`
- **Folder rename safe** - project_id never changes
- **Auto-discovery** - new folders detected without code changes
- **Project isolation** - no cross-project data leakage

### Data Import Pipeline
- CSV and XLSX loaders with validation
- Automatic type normalization (dates, numerics, IDs)
- Missing file handling with empty/setup states
- Validation warnings logged per-project

### Analytics Engine
- Progress metrics (SPI, variance)
- Cost metrics (CPI, payment ratios)
- Risk scoring and distribution
- Delay event analysis
- S-Curve visualization

### Delay TIA Engine
- Steel supply vs demand analysis
- First negative availability detection
- Affected activity identification
- Delay window calculation
- Concurrency matrix analysis

### Claims Intelligence
- Contract clause matching
- Evidence linking
- Structured decision matrix:
  - YES valid
  - YES supporting
  - NO
  - NOT ENOUGH DATA
  - COMMERCIAL ONLY

### Letters Intelligence
- Auto-scan inbox folders
- PDF/DOCX/TXT/XLSX support
- Classification by type:
  - Delay notice, EOT notice, Claim notice
  - Instruction, Warning, Payment issue
  - RFI/Design, Steel/Material, Site handover
- Auto-link to claims and delays

### Output Studio
- Word reports
- Excel exports
- HTML summaries
- PowerPoint slides
- All outputs scoped to selected project

### No-Git GitHub Sync
```bash
# Watch mode (continuous sync every 30 seconds)
RUN_FULL_PROJECT_NO_GIT_SYNC.bat Watch 30

# Single sync
RUN_FULL_PROJECT_NO_GIT_SYNC.bat Once 30

# Dry run (simulate only)
RUN_FULL_PROJECT_NO_GIT_SYNC.bat DryRun 30
```

## 🧪 Validation

```bash
# Compile check
python -m compileall -q dashboard.py contract_claims_center.py src tools scripts tests

# Run tests
python -m pytest -q tests

# Generate data lineage
python tools/generate_data_lineage.py

# Validate project isolation
python tools/validate_project_isolation.py --sync-probe

# Evaluate modules
python scripts/evaluate_delay_tia.py --label project_isolation
python scripts/evaluate_output_studio.py --label project_isolation
```

## 🔒 Security

- GitHub token from environment only (`GITHUB_TOKEN` or `GH_TOKEN`)
- No secrets in source code, config, or logs
- AI integration optional (OpenAI key from env)
- `.gitignore` excludes secrets, cache, logs

## 🎨 Design

Modern dark theme with:
- Interactive Plotly charts
- Real-time metric cards
- Gauge visualizations
- Gantt charts
- Treemaps
- Responsive sidebar navigation

## 📊 Data Files

Place your project data in:
```
projects/<YourProject>/data/import_templates/
  activities.csv
  wbs.csv
  contracts.csv
  payments.csv
  risks.csv
  s_curve.csv
  steel_status.csv
  delay_events.csv
  ...
```

## 🏛️ Architecture Rules

1. **Never use folder name as identity** - always use `project_id`
2. **No cross-project fallback** - missing data shows empty state
3. **ProjectContext resolves all paths** - no hardcoded paths
4. **All tables include project_id** - database isolation
5. **Cache keys include project_id** - no cache contamination
6. **Outputs to selected project only** - file system isolation

## 📄 License

MIT License - Production-structured, modular, testable, ready for future UI enhancement.
