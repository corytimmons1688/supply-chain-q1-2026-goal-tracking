"""
Calyx Containers - Q1 2026 Supply Chain Project Management Tool
================================================================

A comprehensive Streamlit application for managing supply chain projects,
tracking milestones, and visualizing progress for Q1 2026 objectives.

Features:
- Dashboard with key metrics and charts
- Interactive Gantt chart timeline
- Project and subtask editing
- Completion tracking with visual progress
- Notes and comments system
- Data persistence with JSON storage

Author: Calyx Containers Team
Date: January 2026
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import sys

# Add the project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_manager import DataManager, generate_project_id, generate_subtask_id
from components.visualizations import (
    create_gantt_chart,
    create_completion_chart,
    create_status_pie_chart,
    create_owner_workload_chart,
    create_budget_chart,
    create_priority_chart,
    create_monthly_milestone_chart,
    get_status_with_overdue,
    COLORS
)
from components.ui_components import (
    render_status_badge,
    render_priority_badge,
    render_progress_bar,
    render_project_card,
    render_project_editor,
    render_subtask_editor,
    render_subtask_list,
    render_notes_section,
    render_metrics_row
)


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Calyx Containers - Q1 2026 Supply Chain",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1E3A5F 0%, #2B547E 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 4px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1E3A5F;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATA INITIALIZATION
# =============================================================================

@st.cache_resource
def get_data_manager():
    """Initialize and cache the data manager."""
    return DataManager(data_dir="data")


def load_projects():
    """Load projects from storage into session state."""
    if 'projects' not in st.session_state:
        dm = get_data_manager()
        st.session_state.projects = dm.load_projects()
    return st.session_state.projects


def save_projects():
    """Save projects from session state to storage."""
    dm = get_data_manager()
    dm.save_projects(st.session_state.projects)


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

def render_sidebar():
    """Render the sidebar navigation and filters."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #1E3A5F; margin: 0;">📦 Calyx Containers</h2>
            <p style="color: #666; font-size: 0.9rem;">Supply Chain Management</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "📅 Timeline", "📋 Projects", "✅ Completion Tracker", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Quick Stats
        projects = load_projects()
        total = len(projects)
        completed = sum(1 for p in projects if p.get('status') == 'Completed')
        
        st.markdown("### Quick Stats")
        st.progress(completed / total if total > 0 else 0)
        st.caption(f"{completed}/{total} objectives complete")
        
        # Time remaining in Q1
        q1_end = date(2026, 3, 31)
        today = date.today()
        if today < q1_end:
            days_left = (q1_end - today).days
            st.info(f"📅 {days_left} days left in Q1")
        
        st.divider()
        
        # Filters (for applicable pages)
        if page in ["📅 Timeline", "📋 Projects"]:
            st.markdown("### Filters")
            
            # Owner filter
            owners = list(set(p.get('owner', 'Unassigned') for p in projects))
            owner_filter = st.selectbox(
                "Owner",
                ["All"] + sorted(owners),
                key="sidebar_owner_filter"
            )
            
            # Status filter
            status_filter = st.selectbox(
                "Status",
                ["All", "Not Started", "In Progress", "Completed", "Overdue"],
                key="sidebar_status_filter"
            )
            
            # Priority filter
            priority_filter = st.selectbox(
                "Priority",
                ["All", "High", "Medium", "Low"],
                key="sidebar_priority_filter"
            )
            
            st.session_state.filters = {
                'owner': owner_filter,
                'status': status_filter,
                'priority': priority_filter
            }
        
        return page


# =============================================================================
# DASHBOARD PAGE
# =============================================================================

def render_dashboard():
    """Render the main dashboard page."""
    projects = load_projects()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Q1 2026 Supply Chain Dashboard</h1>
        <p>Flexpack Pricing Reduction & Material Purchasing Objectives</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Metrics Row
    render_metrics_row(projects)
    
    st.divider()
    
    # Charts Row 1
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(
            create_completion_chart(projects),
            use_container_width=True,
            key="dashboard_completion"
        )
    
    with col2:
        st.plotly_chart(
            create_status_pie_chart(projects),
            use_container_width=True,
            key="dashboard_status_pie"
        )
    
    # Charts Row 2
    col3, col4 = st.columns(2)
    
    with col3:
        st.plotly_chart(
            create_owner_workload_chart(projects),
            use_container_width=True,
            key="dashboard_workload"
        )
    
    with col4:
        st.plotly_chart(
            create_budget_chart(projects),
            use_container_width=True,
            key="dashboard_budget"
        )
    
    # Charts Row 3
    col5, col6 = st.columns(2)
    
    with col5:
        st.plotly_chart(
            create_priority_chart(projects),
            use_container_width=True,
            key="dashboard_priority"
        )
    
    with col6:
        st.plotly_chart(
            create_monthly_milestone_chart(projects),
            use_container_width=True,
            key="dashboard_milestones"
        )
    
    # Recent Activity / Upcoming Deadlines
    st.divider()
    st.markdown("### 📅 Upcoming Deadlines")
    
    # Collect all subtasks with their due dates
    upcoming = []
    for project in projects:
        for subtask in project.get('subtasks', []):
            if not subtask.get('completed'):
                due_date = subtask.get('due_date')
                if isinstance(due_date, str):
                    due_date = datetime.fromisoformat(due_date).date()
                if due_date:
                    upcoming.append({
                        'Project': f"Obj {project.get('objective_number')}: {project.get('name', '')[:30]}",
                        'Subtask': subtask.get('name', ''),
                        'Due Date': due_date,
                        'Owner': subtask.get('owner', project.get('owner', 'Unassigned')),
                        'Days Away': (due_date - date.today()).days
                    })
    
    # Sort by due date and show next 10
    upcoming.sort(key=lambda x: x['Due Date'])
    upcoming_df = pd.DataFrame(upcoming[:10])
    
    if not upcoming_df.empty:
        upcoming_df['Status'] = upcoming_df['Days Away'].apply(
            lambda x: '🔴 Overdue' if x < 0 else '🟡 Due Soon' if x <= 7 else '🟢 On Track'
        )
        upcoming_df['Due Date'] = upcoming_df['Due Date'].apply(lambda x: x.strftime('%b %d, %Y'))
        st.dataframe(
            upcoming_df[['Project', 'Subtask', 'Due Date', 'Owner', 'Status']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("🎉 All subtasks completed!")


# =============================================================================
# TIMELINE PAGE
# =============================================================================

def render_timeline():
    """Render the timeline/Gantt chart page."""
    projects = load_projects()
    filters = st.session_state.get('filters', {})
    
    st.markdown("## 📅 Project Timeline")
    st.markdown("Interactive Gantt chart showing all Q1 2026 supply chain objectives and subtasks.")
    
    # Timeline options
    col1, col2 = st.columns([3, 1])
    
    with col2:
        show_subtasks = st.checkbox("Show Subtasks", value=True, key="timeline_show_subtasks")
    
    # Create and display Gantt chart
    fig = create_gantt_chart(
        projects,
        filter_owner=filters.get('owner'),
        filter_status=filters.get('status'),
        filter_priority=filters.get('priority'),
        show_subtasks=show_subtasks
    )
    
    st.plotly_chart(fig, use_container_width=True, key="timeline_gantt")
    
    # Legend
    with st.expander("📖 Timeline Legend"):
        cols = st.columns(5)
        statuses = ['Not Started', 'In Progress', 'Completed', 'Overdue', 'On Hold']
        for col, status in zip(cols, statuses):
            with col:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 20px; height: 20px; background: {COLORS.get(status, '#999')}; border-radius: 4px;"></div>
                    <span>{status}</span>
                </div>
                """, unsafe_allow_html=True)


# =============================================================================
# PROJECTS PAGE
# =============================================================================

def render_projects():
    """Render the projects list and editor page."""
    projects = load_projects()
    filters = st.session_state.get('filters', {})
    
    st.markdown("## 📋 Project Management")
    
    # Filter projects based on sidebar filters
    filtered_projects = projects.copy()
    
    if filters.get('owner') and filters.get('owner') != "All":
        filtered_projects = [p for p in filtered_projects if p.get('owner') == filters.get('owner')]
    
    if filters.get('priority') and filters.get('priority') != "All":
        filtered_projects = [p for p in filtered_projects if p.get('priority') == filters.get('priority')]
    
    if filters.get('status') and filters.get('status') != "All":
        target_status = filters.get('status')
        filtered_projects = [p for p in filtered_projects if get_status_with_overdue(p) == target_status]
    
    # Sort by objective number
    filtered_projects.sort(key=lambda x: x.get('objective_number', 999))
    
    # Project selection
    st.markdown(f"### Showing {len(filtered_projects)} of {len(projects)} projects")
    
    # Create tabs for each project
    if filtered_projects:
        project_tabs = st.tabs([f"Obj {p.get('objective_number', '?')}" for p in filtered_projects])
        
        for tab, project in zip(project_tabs, filtered_projects):
            with tab:
                render_single_project(project)
    else:
        st.info("No projects match the current filters. Adjust filters in the sidebar.")


def render_single_project(project: dict):
    """Render a single project with all its details and editing capabilities."""
    project_id = project.get('id')
    
    # Project header card
    render_project_card(project)
    
    # Tabs for different sections
    proj_tabs = st.tabs(["📝 Details", "✅ Subtasks", "💬 Notes"])
    
    # Details Tab
    with proj_tabs[0]:
        with st.expander("Edit Project Details", expanded=False):
            updates = render_project_editor(project, key_prefix=f"proj_{project_id}")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 Save Changes", key=f"save_{project_id}", type="primary"):
                    # Find and update the project
                    for i, p in enumerate(st.session_state.projects):
                        if p.get('id') == project_id:
                            st.session_state.projects[i].update(updates)
                            break
                    save_projects()
                    st.success("Project updated!")
                    st.rerun()
    
    # Subtasks Tab
    with proj_tabs[1]:
        st.markdown("#### Subtask Milestones")
        
        subtasks = project.get('subtasks', [])
        
        if subtasks:
            # Completion summary
            completed_count = sum(1 for s in subtasks if s.get('completed'))
            st.progress(completed_count / len(subtasks))
            st.caption(f"{completed_count}/{len(subtasks)} subtasks completed")
            
            # Subtask list with checkboxes
            updated_subtasks = render_subtask_list(subtasks, project_id)
            
            # Check if any subtask was toggled
            if updated_subtasks != subtasks:
                for i, p in enumerate(st.session_state.projects):
                    if p.get('id') == project_id:
                        st.session_state.projects[i]['subtasks'] = updated_subtasks
                        # Update completion percentage based on subtasks
                        completion = int((sum(1 for s in updated_subtasks if s.get('completed')) / len(updated_subtasks)) * 100)
                        st.session_state.projects[i]['completion_percentage'] = completion
                        break
                save_projects()
                st.rerun()
            
            # Edit subtask modal
            editing_subtask_key = f'editing_subtask_{project_id}'
            if editing_subtask_key in st.session_state:
                subtask_idx = st.session_state[editing_subtask_key]
                subtask = subtasks[subtask_idx]
                
                st.divider()
                st.markdown(f"#### ✏️ Editing: {subtask.get('name', 'Subtask')}")
                
                subtask_updates = render_subtask_editor(
                    subtask,
                    key_prefix=f"subtask_{project_id}_{subtask_idx}"
                )
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 Save Subtask", key=f"save_subtask_{project_id}_{subtask_idx}"):
                        for i, p in enumerate(st.session_state.projects):
                            if p.get('id') == project_id:
                                st.session_state.projects[i]['subtasks'][subtask_idx].update(subtask_updates)
                                break
                        save_projects()
                        del st.session_state[editing_subtask_key]
                        st.success("Subtask updated!")
                        st.rerun()
                with col2:
                    if st.button("Cancel", key=f"cancel_subtask_{project_id}_{subtask_idx}"):
                        del st.session_state[editing_subtask_key]
                        st.rerun()
        else:
            st.info("No subtasks defined for this project.")
        
        # Add new subtask
        with st.expander("➕ Add New Subtask"):
            new_subtask = {
                'id': generate_subtask_id(),
                'name': '',
                'description': '',
                'completion_criteria': '',
                'start_date': date(2026, 1, 6),
                'due_date': date(2026, 1, 31),
                'owner': project.get('owner', ''),
                'dependencies': '',
                'success_metric': '',
                'completed': False,
                'notes': []
            }
            
            new_subtask_data = render_subtask_editor(new_subtask, key_prefix=f"new_subtask_{project_id}")
            
            if st.button("Add Subtask", key=f"add_subtask_{project_id}"):
                if new_subtask_data.get('name'):
                    new_subtask.update(new_subtask_data)
                    for i, p in enumerate(st.session_state.projects):
                        if p.get('id') == project_id:
                            if 'subtasks' not in st.session_state.projects[i]:
                                st.session_state.projects[i]['subtasks'] = []
                            st.session_state.projects[i]['subtasks'].append(new_subtask)
                            break
                    save_projects()
                    st.success("Subtask added!")
                    st.rerun()
                else:
                    st.warning("Please enter a subtask name.")
    
    # Notes Tab
    with proj_tabs[2]:
        notes = project.get('notes', [])
        updated_notes = render_notes_section(notes, key_prefix=f"notes_{project_id}")
        
        if updated_notes != notes:
            for i, p in enumerate(st.session_state.projects):
                if p.get('id') == project_id:
                    st.session_state.projects[i]['notes'] = updated_notes
                    break
            save_projects()
            st.rerun()


# =============================================================================
# COMPLETION TRACKER PAGE
# =============================================================================

def render_completion_tracker():
    """Render the completion tracking page with progress overview."""
    projects = load_projects()
    
    st.markdown("## ✅ Completion Tracker")
    st.markdown("Track progress across all Q1 2026 supply chain objectives.")
    
    # Overall Progress
    total_subtasks = sum(len(p.get('subtasks', [])) for p in projects)
    completed_subtasks = sum(
        sum(1 for s in p.get('subtasks', []) if s.get('completed'))
        for p in projects
    )
    overall_percentage = int((completed_subtasks / total_subtasks * 100)) if total_subtasks > 0 else 0
    
    st.markdown("### Overall Q1 Progress")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(render_progress_bar(overall_percentage, height=30), unsafe_allow_html=True)
    with col2:
        st.metric("Subtasks Complete", f"{completed_subtasks}/{total_subtasks}")
    with col3:
        projects_complete = sum(1 for p in projects if p.get('status') == 'Completed')
        st.metric("Projects Complete", f"{projects_complete}/{len(projects)}")
    
    st.divider()
    
    # Project-by-project breakdown
    st.markdown("### Project Breakdown")
    
    for project in sorted(projects, key=lambda x: x.get('objective_number', 999)):
        subtasks = project.get('subtasks', [])
        completed = sum(1 for s in subtasks if s.get('completed'))
        percentage = int((completed / len(subtasks) * 100)) if subtasks else 0
        
        with st.expander(
            f"**Objective {project.get('objective_number', '?')}: {project.get('name', 'Unnamed')}** — {percentage}% complete",
            expanded=percentage < 100
        ):
            # Progress bar
            st.markdown(render_progress_bar(percentage), unsafe_allow_html=True)
            
            # Owner and dates
            st.caption(f"Owner: {project.get('owner', 'Unassigned')} | Due: {project.get('due_date', 'Not set')}")
            
            # Subtask checklist
            if subtasks:
                for i, subtask in enumerate(subtasks):
                    due_date = subtask.get('due_date')
                    if isinstance(due_date, str):
                        due_date = datetime.fromisoformat(due_date).date()
                    
                    is_completed = subtask.get('completed', False)
                    is_overdue = due_date and due_date < date.today() and not is_completed
                    
                    col1, col2 = st.columns([0.1, 0.9])
                    
                    with col1:
                        new_completed = st.checkbox(
                            "",
                            value=is_completed,
                            key=f"tracker_{project.get('id')}_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with col2:
                        status_icon = "✅" if new_completed else "🔴" if is_overdue else "⬜"
                        style = "text-decoration: line-through; color: #888;" if new_completed else ""
                        st.markdown(f"""
                        <span style="{style}">
                            {status_icon} {subtask.get('name', 'Unnamed')}
                            <span style="color: #888; font-size: 0.8rem;">
                                (Due: {due_date.strftime('%b %d') if due_date else 'Not set'})
                            </span>
                        </span>
                        """, unsafe_allow_html=True)
                    
                    # Update if changed
                    if new_completed != is_completed:
                        for pi, p in enumerate(st.session_state.projects):
                            if p.get('id') == project.get('id'):
                                st.session_state.projects[pi]['subtasks'][i]['completed'] = new_completed
                                # Update project completion percentage
                                completed_count = sum(1 for s in st.session_state.projects[pi]['subtasks'] if s.get('completed'))
                                total_count = len(st.session_state.projects[pi]['subtasks'])
                                st.session_state.projects[pi]['completion_percentage'] = int((completed_count / total_count) * 100) if total_count > 0 else 0
                                break
                        save_projects()
                        st.rerun()
            else:
                st.info("No subtasks defined.")


# =============================================================================
# SETTINGS PAGE
# =============================================================================

def render_settings():
    """Render the settings page."""
    st.markdown("## ⚙️ Settings")
    
    # Data Management
    st.markdown("### Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export Data")
        projects = load_projects()
        
        if st.button("📥 Export to JSON"):
            import json
            json_str = json.dumps(projects, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"calyx_projects_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    with col2:
        st.markdown("#### Import Data")
        uploaded_file = st.file_uploader("Upload JSON file", type=['json'])
        
        if uploaded_file is not None:
            try:
                import json
                imported_data = json.load(uploaded_file)
                if st.button("📤 Import Data"):
                    st.session_state.projects = imported_data
                    save_projects()
                    st.success(f"Imported {len(imported_data)} projects!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    st.divider()
    
    # Reset Data
    st.markdown("### Reset to Default Data")
    st.warning("⚠️ This will reset all projects to the original Q1 2026 supply chain objectives.")
    
    if st.button("🔄 Reset to Default", type="secondary"):
        # Reload original data from file
        dm = get_data_manager()
        original_data = dm.load_projects()
        st.session_state.projects = original_data
        st.success("Data reset to defaults!")
        st.rerun()
    
    st.divider()
    
    # About
    st.markdown("### About")
    st.markdown("""
    **Calyx Containers Supply Chain Project Management Tool**
    
    Version 1.0.0 | Q1 2026
    
    This application tracks the 8 strategic supply chain objectives for Q1 2026,
    focused on reducing flexpack pricing through optimized material purchasing,
    strategic vendor partnerships, and operational efficiencies.
    
    **Primary Owners:**
    - Greg Furner (Production Manager)
    - Cory Timmons (Supply Chain Manager)
    
    **Features:**
    - Interactive Gantt chart timeline
    - Project and subtask tracking
    - Completion percentage monitoring
    - Budget tracking
    - Notes and comments
    - Data export/import
    """)


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application entry point."""
    # Initialize data
    load_projects()
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Render selected page
    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "📅 Timeline":
        render_timeline()
    elif page == "📋 Projects":
        render_projects()
    elif page == "✅ Completion Tracker":
        render_completion_tracker()
    elif page == "⚙️ Settings":
        render_settings()


if __name__ == "__main__":
    main()
