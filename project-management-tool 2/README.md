# Calyx Containers - Q1 2026 Supply Chain Project Management Tool

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

A comprehensive web-based project management application built with Streamlit for tracking Calyx Containers' Q1 2026 supply chain objectives focused on Flexpack pricing reduction and material purchasing optimization.

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [Project Structure](#-project-structure)
- [Data Model](#-data-model)
- [Q1 2026 Objectives](#-q1-2026-objectives)
- [Customization](#-customization)
- [Contributing](#-contributing)

## ✨ Features

### 📊 Dashboard
- **Key Metrics**: Total projects, completion rates, overdue items, and budget tracking
- **Visual Charts**: Status distribution, workload by owner, budget vs. actual spend
- **Upcoming Deadlines**: Real-time view of approaching milestones

### 📅 Interactive Timeline
- **Gantt Chart**: Visual timeline of all projects and subtasks
- **Hover Tooltips**: Detailed information including duration, owner, completion %, and budget
- **Filtering**: Filter by owner, status, or priority
- **Subtask Toggle**: Show/hide subtasks for different views

### 📋 Project Management
- **Editable Fields**: 
  - Project name, description, priority, status
  - Start/due dates, estimated/actual hours
  - Budget allocation and spending
  - Team member assignment
  - Tags and categories
- **Subtask Tracking**: Individual milestones with completion criteria and success metrics
- **Notes System**: Timestamped comments and notes per project

### ✅ Completion Tracker
- **Visual Progress Bars**: Color-coded completion for each objective
- **Checkbox Interface**: Quick-toggle subtask completion
- **Status Indicators**: Not Started, In Progress, Completed, Overdue

### ⚙️ Settings & Data Management
- **Export**: Download all data as JSON
- **Import**: Upload JSON files to restore or migrate data
- **Reset**: Return to original Q1 2026 objectives

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd project-management-tool

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd project-management-tool
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

### Dependencies
- `streamlit>=1.28.0` - Web application framework
- `pandas>=2.0.0` - Data manipulation
- `plotly>=5.18.0` - Interactive visualizations
- `numpy>=1.24.0` - Numerical operations

## 📖 Usage Guide

### Dashboard
The dashboard provides an at-a-glance view of all Q1 2026 supply chain objectives:
- **Metrics Row**: Quick stats on projects, completion, and overdue items
- **Charts**: Visual representation of status, workload, budget, and milestones
- **Upcoming Deadlines**: Table of the next 10 due subtasks

### Timeline View
The timeline presents an interactive Gantt chart:
1. Use sidebar filters to narrow down projects
2. Toggle "Show Subtasks" to see detailed breakdown
3. Hover over bars for detailed tooltips
4. The red dashed line indicates today's date

### Projects Page
Manage individual projects through tabbed interface:
1. **Details Tab**: Edit all project fields
2. **Subtasks Tab**: 
   - Check/uncheck completion
   - Click 📝 to edit subtask details
   - Add new subtasks
3. **Notes Tab**: Add timestamped comments

### Completion Tracker
Quick-update interface for tracking progress:
- Expandable cards for each objective
- Direct checkbox toggle for subtasks
- Automatic percentage calculation

### Settings
- **Export**: Download current state as JSON backup
- **Import**: Load previously exported data
- **Reset**: Restore original Q1 2026 data

## 📁 Project Structure

```
project-management-tool/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── app.py                       # Main Streamlit application
├── data/
│   └── projects.json           # Project data storage
├── components/
│   ├── __init__.py             # Package exports
│   ├── visualizations.py       # Chart creation functions
│   └── ui_components.py        # Reusable UI elements
├── utils/
│   ├── __init__.py             # Package exports
│   └── data_manager.py         # Data persistence layer
└── assets/                      # Static assets (if any)
```

## 📊 Data Model

### Project Schema
```json
{
  "id": "proj_001",
  "name": "Project Name",
  "description": "Project description",
  "priority": "High|Medium|Low",
  "status": "Not Started|In Progress|Completed|On Hold",
  "owner": "Owner Name",
  "team_members": ["Member 1", "Member 2"],
  "start_date": "2026-01-06",
  "due_date": "2026-03-31",
  "estimated_hours": 200,
  "actual_hours": 50,
  "budget": 15000,
  "budget_spent": 3000,
  "completion_percentage": 25,
  "category": "Category Name",
  "tags": ["tag1", "tag2"],
  "objective_number": 1,
  "subtasks": [...],
  "notes": [...]
}
```

### Subtask Schema
```json
{
  "id": "task_001_1",
  "name": "Subtask Name",
  "description": "Subtask description",
  "completion_criteria": "What defines done",
  "start_date": "2026-01-06",
  "due_date": "2026-01-31",
  "owner": "Owner Name",
  "dependencies": "Prerequisites",
  "success_metric": "How success is measured",
  "completed": false,
  "notes": []
}
```

## 🎯 Q1 2026 Objectives

The application comes pre-loaded with 8 strategic supply chain objectives:

| # | Objective | Owner | Priority |
|---|-----------|-------|----------|
| 1 | CMY Color Strategy Implementation | Greg Furner | High |
| 2 | Premium White to Standard White Transition | Greg Furner | High |
| 3 | 30" Thermal Laminator Acquisition | Cory Timmons | High |
| 4 | Growve Partnership as 30" Print Partner | Cory Timmons | High |
| 5 | Dazpak Material Cost Optimization | Cory Timmons | High |
| 6 | 26" Flexo Setup with Dazpak | Cory Timmons | Medium |
| 7 | Brand My Bags Vendor Evaluation | Cory Timmons | Medium |
| 8 | Alternative CR Zipper Implementation | Cory Timmons | High |

Each objective includes detailed subtasks with:
- Specific completion criteria
- Timeline with start/end dates
- Dependencies and prerequisites
- Success metrics and KPIs

## 🔧 Customization

### Adding New Team Members
Edit `components/ui_components.py` and update the `all_team_members` list in `render_project_editor()`:

```python
all_team_members = ['Greg Furner', 'Cory Timmons', 'New Member', ...]
```

### Modifying Color Scheme
Edit `components/visualizations.py` and update the `COLORS` dictionary:

```python
COLORS = {
    'Not Started': '#6c757d',
    'In Progress': '#0d6efd',
    'Completed': '#198754',
    'Overdue': '#dc3545',
    'On Hold': '#ffc107',
    # Add custom colors...
}
```

### Adding New Project Fields
1. Update the data model in `data/projects.json`
2. Add UI components in `components/ui_components.py`
3. Update the main app rendering in `app.py`

### Changing Timeline Range
Edit `components/visualizations.py` in the `create_gantt_chart()` function:

```python
xaxis=dict(
    range=[
        datetime(2026, 1, 1),  # Start date
        datetime(2026, 4, 7)   # End date
    ]
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary to Calyx Containers. All rights reserved.

---

**Calyx Containers** | Q1 2026 Supply Chain Management  
Primary Owners: Greg Furner (Production) & Cory Timmons (Supply Chain)
