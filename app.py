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
from datetime import datetime, date, timedelta
import os
import sys
import json
import copy
from typing import Dict, List, Optional, Any, Callable

# Add the project root to path for imports
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Try relative imports first, fall back to direct imports if that fails
try:
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
except ImportError:
    # If imports fail, define everything inline
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np
    
    # =========================================================================
    # INLINE DATA MANAGER
    # =========================================================================
    
    class DataManager:
        """Manages project data storage and retrieval."""
        
        def __init__(self, data_dir: str = "data"):
            self.data_dir = data_dir
            self.projects_file = os.path.join(data_dir, "projects.json")
            self.ensure_data_dir()
        
        def ensure_data_dir(self):
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
        
        def _serialize_dates(self, obj: Any) -> Any:
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: self._serialize_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [self._serialize_dates(item) for item in obj]
            return obj
        
        def _deserialize_dates(self, obj: Any, date_fields: List[str]) -> Any:
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    if k in date_fields and isinstance(v, str):
                        try:
                            result[k] = datetime.fromisoformat(v).date()
                        except (ValueError, TypeError):
                            result[k] = v
                    else:
                        result[k] = self._deserialize_dates(v, date_fields)
                return result
            elif isinstance(obj, list):
                return [self._deserialize_dates(item, date_fields) for item in obj]
            return obj
        
        def save_projects(self, projects: List[Dict]) -> bool:
            try:
                self.ensure_data_dir()
                serialized = self._serialize_dates(projects)
                with open(self.projects_file, 'w') as f:
                    json.dump(serialized, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                return True
            except Exception as e:
                print(f"Error saving projects: {e}")
                return False
        
        def load_projects(self) -> List[Dict]:
            date_fields = ['start_date', 'due_date', 'timestamp', 'created_at', 'updated_at']
            if not os.path.exists(self.projects_file):
                return []
            try:
                with open(self.projects_file, 'r') as f:
                    data = json.load(f)
                return self._deserialize_dates(data, date_fields)
            except Exception as e:
                print(f"Error loading projects: {e}")
                return []
    
    def generate_project_id() -> str:
        return f"proj_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    def generate_subtask_id() -> str:
        return f"task_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    # =========================================================================
    # INLINE VISUALIZATIONS
    # =========================================================================
    
    COLORS = {
        'Not Started': '#6c757d',
        'In Progress': '#0d6efd',
        'Completed': '#198754',
        'Overdue': '#dc3545',
        'On Hold': '#ffc107',
        'High': '#dc3545',
        'Medium': '#ffc107',
        'Low': '#198754',
        'primary': '#1E3A5F',
        'secondary': '#2B547E',
        'accent': '#4A90D9',
        'background': '#f8f9fa',
    }
    
    def get_status_with_overdue(project: Dict) -> str:
        status = project.get('status', 'Not Started')
        if status == 'Completed':
            return status
        due_date = project.get('due_date')
        if due_date:
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date).date()
            if due_date < date.today():
                return 'Overdue'
        return status
    
    def create_gantt_chart(projects: List[Dict], 
                           filter_owner: Optional[str] = None,
                           filter_status: Optional[str] = None,
                           filter_priority: Optional[str] = None,
                           show_subtasks: bool = True) -> go.Figure:
        tasks = []
        for project in projects:
            if filter_owner and filter_owner != "All" and project.get('owner') != filter_owner:
                continue
            if filter_status and filter_status != "All":
                actual_status = get_status_with_overdue(project)
                if actual_status != filter_status:
                    continue
            if filter_priority and filter_priority != "All" and project.get('priority') != filter_priority:
                continue
            
            start_date = project.get('start_date')
            due_date = project.get('due_date')
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date).date()
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date).date()
            if not start_date or not due_date:
                continue
            
            status = get_status_with_overdue(project)
            completion = project.get('completion_percentage', 0)
            
            tasks.append({
                'Task': f"Obj {project.get('objective_number', '?')}: {project.get('name', 'Unnamed')[:40]}",
                'Start': start_date,
                'Finish': due_date,
                'Resource': status,
                'Completion': completion,
                'Owner': project.get('owner', 'Unassigned'),
                'Priority': project.get('priority', 'Medium'),
                'Budget': f"${project.get('budget', 0):,.0f}",
                'Type': 'Project',
                'Description': project.get('description', '')[:100]
            })
            
            if show_subtasks:
                for subtask in project.get('subtasks', []):
                    sub_start = subtask.get('start_date')
                    sub_due = subtask.get('due_date')
                    if isinstance(sub_start, str):
                        sub_start = datetime.fromisoformat(sub_start).date()
                    if isinstance(sub_due, str):
                        sub_due = datetime.fromisoformat(sub_due).date()
                    if not sub_start or not sub_due:
                        continue
                    
                    sub_status = 'Completed' if subtask.get('completed') else 'In Progress' if sub_start <= date.today() else 'Not Started'
                    if sub_due < date.today() and not subtask.get('completed'):
                        sub_status = 'Overdue'
                    
                    tasks.append({
                        'Task': f"  └ {subtask.get('name', 'Unnamed')[:35]}",
                        'Start': sub_start,
                        'Finish': sub_due,
                        'Resource': sub_status,
                        'Completion': 100 if subtask.get('completed') else 0,
                        'Owner': subtask.get('owner', project.get('owner', 'Unassigned')),
                        'Priority': project.get('priority', 'Medium'),
                        'Budget': '-',
                        'Type': 'Subtask',
                        'Description': subtask.get('description', '')[:80]
                    })
        
        if not tasks:
            fig = go.Figure()
            fig.add_annotation(text="No projects match the selected filters", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), height=200)
            return fig
        
        df = pd.DataFrame(tasks)
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Resource",
                          color_discrete_map=COLORS, custom_data=['Owner', 'Completion', 'Priority', 'Budget', 'Type', 'Description'])
        
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Start: %{x}<br>End: %{base}<br>Owner: %{customdata[0]}<br>Completion: %{customdata[1]}%<br>Priority: %{customdata[2]}<br>Budget: %{customdata[3]}<extra></extra>")
        fig.update_layout(title=dict(text="Q1 2026 Supply Chain Timeline", font=dict(size=20, color=COLORS['primary'])),
                          xaxis_title="Date", yaxis_title="", showlegend=True, legend_title_text="Status",
                          height=max(400, len(tasks) * 35), yaxis=dict(autorange="reversed"),
                          xaxis=dict(tickformat="%b %d", dtick="D7", tickangle=-45, range=[datetime(2026, 1, 1), datetime(2026, 4, 7)]),
                          margin=dict(l=10, r=10, t=60, b=80))
        return fig
    
    def create_completion_chart(projects: List[Dict]) -> go.Figure:
        if not projects:
            fig = go.Figure()
            fig.add_annotation(text="No projects to display", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), height=300)
            return fig
        data = [{'Project': f"Obj {p.get('objective_number', '?')}: {p.get('name', 'Unnamed')[:30]}",
                 'Completion': p.get('completion_percentage', 0), 'Status': get_status_with_overdue(p),
                 'Owner': p.get('owner', 'Unassigned')} for p in projects]
        df = pd.DataFrame(data)
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No projects to display", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), height=300)
            return fig
        df = df.sort_values('Completion', ascending=True)
        fig = px.bar(df, x='Completion', y='Project', orientation='h', color='Status',
                     color_discrete_map=COLORS, custom_data=['Owner', 'Status'])
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Completion: %{x}%<br>Owner: %{customdata[0]}<extra></extra>")
        fig.update_layout(title=dict(text="Project Completion Progress", font=dict(size=18, color=COLORS['primary'])),
                          xaxis_title="Completion %", yaxis_title="", xaxis=dict(range=[0, 100]),
                          height=max(300, len(data) * 40), showlegend=True, margin=dict(l=10, r=10, t=50, b=30))
        return fig
    
    def create_status_pie_chart(projects: List[Dict]) -> go.Figure:
        if not projects:
            fig = go.Figure()
            fig.add_annotation(text="No data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(height=300)
            return fig
        status_counts = {}
        for p in projects:
            status = get_status_with_overdue(p)
            status_counts[status] = status_counts.get(status, 0) + 1
        if not status_counts:
            fig = go.Figure()
            fig.add_annotation(text="No data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(height=300)
            return fig
        fig = go.Figure(data=[go.Pie(labels=list(status_counts.keys()), values=list(status_counts.values()), hole=0.4,
                                      marker_colors=[COLORS.get(s, '#999') for s in status_counts.keys()])])
        fig.update_layout(title=dict(text="Status Distribution", font=dict(size=16, color=COLORS['primary'])),
                          height=300, margin=dict(l=20, r=20, t=50, b=20))
        return fig
    
    def create_owner_workload_chart(projects: List[Dict]) -> go.Figure:
        if not projects:
            fig = go.Figure()
            fig.add_annotation(text="No data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(height=350)
            return fig
        owner_data = {}
        for p in projects:
            owner = p.get('owner', 'Unassigned')
            if owner not in owner_data:
                owner_data[owner] = {'projects': 0, 'hours': 0}
            owner_data[owner]['projects'] += 1
            owner_data[owner]['hours'] += p.get('estimated_hours', 0)
        if not owner_data:
            fig = go.Figure()
            fig.add_annotation(text="No data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(height=350)
            return fig
        df = pd.DataFrame([{'Owner': o, 'Projects': d['projects'], 'Hours': d['hours']} for o, d in owner_data.items()])
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Projects by Owner", "Estimated Hours by Owner"))
        fig.add_trace(go.Bar(name='Projects', x=df['Owner'], y=df['Projects'], marker_color=COLORS['primary']), row=1, col=1)
        fig.add_trace(go.Bar(name='Hours', x=df['Owner'], y=df['Hours'], marker_color=COLORS['accent']), row=1, col=2)
        fig.update_layout(title=dict(text="Workload Distribution", font=dict(size=18, color=COLORS['primary'])),
                          height=350, showlegend=False, margin=dict(l=10, r=10, t=80, b=30))
        return fig
    
    def create_budget_chart(projects: List[Dict]) -> go.Figure:
        data = [{'Project': f"Obj {p.get('objective_number', '?')}", 'Budget': p.get('budget', 0),
                 'Spent': p.get('budget_spent', 0), 'Name': p.get('name', '')} for p in projects]
        df = pd.DataFrame(data)
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Budget', x=df['Project'], y=df['Budget'], marker_color=COLORS['secondary'],
                             customdata=df['Name'], hovertemplate="<b>%{customdata}</b><br>Budget: $%{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Bar(name='Spent', x=df['Project'], y=df['Spent'], marker_color=COLORS['accent'],
                             customdata=df['Name'], hovertemplate="<b>%{customdata}</b><br>Spent: $%{y:,.0f}<extra></extra>"))
        fig.update_layout(title=dict(text="Budget vs. Actual Spend", font=dict(size=18, color=COLORS['primary'])),
                          xaxis_title="Objective", yaxis_title="Amount ($)", barmode='group', height=350, margin=dict(l=10, r=10, t=50, b=30))
        return fig
    
    def create_priority_chart(projects: List[Dict]) -> go.Figure:
        priority_counts = {}
        for p in projects:
            priority = p.get('priority', 'Medium')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        labels = [p for p in ['High', 'Medium', 'Low'] if p in priority_counts]
        values = [priority_counts[p] for p in labels]
        colors = [COLORS.get(p, '#999') for p in labels]
        fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color=colors)])
        fig.update_layout(title=dict(text="Projects by Priority", font=dict(size=16, color=COLORS['primary'])),
                          xaxis_title="Priority", yaxis_title="Count", height=300, margin=dict(l=10, r=10, t=50, b=30))
        return fig
    
    def create_monthly_milestone_chart(projects: List[Dict]) -> go.Figure:
        monthly_data = {'January': 0, 'February': 0, 'March': 0}
        for p in projects:
            for subtask in p.get('subtasks', []):
                due_date = subtask.get('due_date')
                if isinstance(due_date, str):
                    due_date = datetime.fromisoformat(due_date).date()
                if due_date:
                    month = due_date.strftime('%B')
                    if month in monthly_data:
                        monthly_data[month] += 1
        fig = go.Figure(data=[go.Bar(x=list(monthly_data.keys()), y=list(monthly_data.values()),
                                      marker_color=[COLORS['primary'], COLORS['secondary'], COLORS['accent']])])
        fig.update_layout(title=dict(text="Subtask Deadlines by Month", font=dict(size=16, color=COLORS['primary'])),
                          xaxis_title="Month", yaxis_title="Subtasks Due", height=300, margin=dict(l=10, r=10, t=50, b=30))
        return fig
    
    # =========================================================================
    # INLINE UI COMPONENTS
    # =========================================================================
    
    def render_status_badge(status: str) -> str:
        colors = {'Not Started': '#6c757d', 'In Progress': '#0d6efd', 'Completed': '#198754', 'Overdue': '#dc3545', 'On Hold': '#ffc107'}
        color = colors.get(status, '#6c757d')
        return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{status}</span>'
    
    def render_priority_badge(priority: str) -> str:
        colors = {'High': '#dc3545', 'Medium': '#ffc107', 'Low': '#198754'}
        color = colors.get(priority, '#6c757d')
        text_color = 'white' if priority != 'Medium' else 'black'
        return f'<span style="background-color: {color}; color: {text_color}; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{priority}</span>'
    
    def render_progress_bar(percentage: int, height: int = 20) -> str:
        color = '#198754' if percentage >= 75 else '#ffc107' if percentage >= 50 else '#dc3545' if percentage > 0 else '#6c757d'
        return f'''<div style="background-color: #e9ecef; border-radius: 4px; height: {height}px; width: 100%;">
            <div style="background-color: {color}; width: {percentage}%; height: 100%; border-radius: 4px; 
                        display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">{percentage}%</div></div>'''
    
    def render_project_card(project: Dict, on_edit: Optional[Callable] = None) -> None:
        status = project.get('status', 'Not Started')
        due_date = project.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date).date()
        if due_date and due_date < date.today() and status != 'Completed':
            status = 'Overdue'
        completion = project.get('completion_percentage', 0)
        st.markdown(f"""<div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; background: white;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                <div><h4 style="margin: 0; color: #1E3A5F;">Objective {project.get('objective_number', '?')}: {project.get('name', 'Unnamed')}</h4>
                    <p style="color: #666; font-size: 13px; margin: 5px 0;">{project.get('description', '')[:150]}{'...' if len(project.get('description', '')) > 150 else ''}</p></div>
                <div style="text-align: right;">{render_status_badge(status)}<br><br>{render_priority_badge(project.get('priority', 'Medium'))}</div></div>
            <div style="display: flex; gap: 20px; font-size: 13px; color: #666; margin-bottom: 10px;">
                <span>👤 {project.get('owner', 'Unassigned')}</span>
                <span>📅 Due: {due_date.strftime('%b %d, %Y') if due_date else 'Not set'}</span>
                <span>💰 ${project.get('budget', 0):,.0f}</span>
                <span>⏱️ {project.get('estimated_hours', 0)}h estimated</span></div>
            {render_progress_bar(completion)}</div>""", unsafe_allow_html=True)
    
    def render_project_editor(project: Dict, key_prefix: str = "") -> Dict:
        updates = {}
        col1, col2 = st.columns(2)
        with col1:
            updates['name'] = st.text_input("Project Name", value=project.get('name', ''), key=f"{key_prefix}_name")
            updates['description'] = st.text_area("Description", value=project.get('description', ''), height=100, key=f"{key_prefix}_desc")
            updates['owner'] = st.selectbox("Owner", options=['Greg Furner', 'Cory Timmons', 'Other'],
                index=['Greg Furner', 'Cory Timmons', 'Other'].index(project.get('owner', 'Other')) if project.get('owner') in ['Greg Furner', 'Cory Timmons', 'Other'] else 2, key=f"{key_prefix}_owner")
            all_team_members = ['Greg Furner', 'Cory Timmons', 'Legal', 'Finance', 'QA Team', 'Sales Team', 'Production Team', 'IT', 'Facilities', 'HP Technician', 'Dazpak Technical', 'Dazpak', 'Ross', 'Growve']
            current_team = project.get('team_members', [])
            valid_defaults = [m for m in current_team if m in all_team_members]
            updates['team_members'] = st.multiselect("Team Members", options=all_team_members, default=valid_defaults, key=f"{key_prefix}_team")
        with col2:
            updates['priority'] = st.selectbox("Priority", options=['High', 'Medium', 'Low'],
                index=['High', 'Medium', 'Low'].index(project.get('priority', 'Medium')), key=f"{key_prefix}_priority")
            updates['status'] = st.selectbox("Status", options=['Not Started', 'In Progress', 'Completed', 'On Hold'],
                index=['Not Started', 'In Progress', 'Completed', 'On Hold'].index(project.get('status', 'Not Started')) if project.get('status') in ['Not Started', 'In Progress', 'Completed', 'On Hold'] else 0, key=f"{key_prefix}_status")
            start_date = project.get('start_date')
            due_date = project.get('due_date')
            if isinstance(start_date, str): start_date = datetime.fromisoformat(start_date).date()
            if isinstance(due_date, str): due_date = datetime.fromisoformat(due_date).date()
            updates['start_date'] = st.date_input("Start Date", value=start_date or date(2026, 1, 6), key=f"{key_prefix}_start", format="MM/DD/YYYY")
            updates['due_date'] = st.date_input("Due Date", value=due_date or date(2026, 3, 31), key=f"{key_prefix}_due", format="MM/DD/YYYY")
        with st.expander("Additional Details", expanded=False):
            col3, col4 = st.columns(2)
            with col3:
                updates['estimated_hours'] = st.number_input("Estimated Hours", min_value=0, value=project.get('estimated_hours', 0), key=f"{key_prefix}_est_hours")
                updates['actual_hours'] = st.number_input("Actual Hours Spent", min_value=0, value=project.get('actual_hours', 0), key=f"{key_prefix}_act_hours")
                updates['completion_percentage'] = st.slider("Completion %", min_value=0, max_value=100, value=project.get('completion_percentage', 0), key=f"{key_prefix}_completion")
            with col4:
                updates['budget'] = st.number_input("Budget ($)", min_value=0, value=project.get('budget', 0), key=f"{key_prefix}_budget")
                updates['budget_spent'] = st.number_input("Budget Spent ($)", min_value=0, value=project.get('budget_spent', 0), key=f"{key_prefix}_spent")
                updates['category'] = st.text_input("Category", value=project.get('category', ''), key=f"{key_prefix}_category")
            current_tags = project.get('tags', [])
            tags_str = st.text_input("Tags (comma-separated)", value=', '.join(current_tags) if current_tags else '', key=f"{key_prefix}_tags")
            updates['tags'] = [t.strip() for t in tags_str.split(',') if t.strip()]
        return updates
    
    def render_subtask_editor(subtask: Dict, key_prefix: str = "") -> Dict:
        updates = {}
        col1, col2 = st.columns([3, 1])
        with col1:
            updates['name'] = st.text_input("Subtask Name", value=subtask.get('name', ''), key=f"{key_prefix}_name")
        with col2:
            updates['completed'] = st.checkbox("Completed", value=subtask.get('completed', False), key=f"{key_prefix}_completed")
        updates['description'] = st.text_area("Description", value=subtask.get('description', ''), height=80, key=f"{key_prefix}_desc")
        col3, col4 = st.columns(2)
        with col3:
            updates['completion_criteria'] = st.text_area("Completion Criteria", value=subtask.get('completion_criteria', ''), height=80, key=f"{key_prefix}_criteria")
            start_date = subtask.get('start_date')
            if isinstance(start_date, str): start_date = datetime.fromisoformat(start_date).date()
            updates['start_date'] = st.date_input("Start Date", value=start_date or date(2026, 1, 6), key=f"{key_prefix}_start", format="MM/DD/YYYY")
        with col4:
            updates['success_metric'] = st.text_area("Success Metric", value=subtask.get('success_metric', ''), height=80, key=f"{key_prefix}_metric")
            due_date = subtask.get('due_date')
            if isinstance(due_date, str): due_date = datetime.fromisoformat(due_date).date()
            updates['due_date'] = st.date_input("Due Date", value=due_date or date(2026, 1, 31), key=f"{key_prefix}_due", format="MM/DD/YYYY")
        updates['owner'] = st.text_input("Owner", value=subtask.get('owner', ''), key=f"{key_prefix}_owner")
        updates['dependencies'] = st.text_area("Dependencies", value=subtask.get('dependencies', ''), height=60, key=f"{key_prefix}_deps")
        return updates
    
    def render_subtask_list(subtasks: List[Dict], project_id: str) -> List[Dict]:
        updated_subtasks = []
        for i, subtask in enumerate(subtasks):
            due_date = subtask.get('due_date')
            if isinstance(due_date, str): due_date = datetime.fromisoformat(due_date).date()
            is_completed = subtask.get('completed', False)
            is_overdue = due_date and due_date < date.today() and not is_completed
            status_icon = "✅" if is_completed else "🔴" if is_overdue else "⏳"
            col1, col2, col3 = st.columns([0.5, 4, 1])
            with col1:
                completed = st.checkbox("", value=is_completed, key=f"subtask_{project_id}_{i}_check", label_visibility="collapsed")
            with col2:
                st.markdown(f"""<div style="{'text-decoration: line-through; color: #888;' if completed else ''}">
                    <strong>{status_icon} {subtask.get('name', 'Unnamed Subtask')}</strong>
                    <br><span style="font-size: 12px; color: #666;">Due: {due_date.strftime('%b %d') if due_date else 'Not set'} | Owner: {subtask.get('owner', 'Unassigned')}</span></div>""", unsafe_allow_html=True)
            with col3:
                if st.button("📝", key=f"edit_subtask_{project_id}_{i}", help="Edit subtask"):
                    st.session_state[f'editing_subtask_{project_id}'] = i
            updated_subtask = subtask.copy()
            updated_subtask['completed'] = completed
            updated_subtasks.append(updated_subtask)
        return updated_subtasks
    
    def render_notes_section(notes: List[Dict], key_prefix: str) -> List[Dict]:
        st.markdown("#### Notes & Comments")
        if notes:
            for note in notes:
                timestamp = note.get('timestamp', '')
                if isinstance(timestamp, str) and timestamp:
                    try: timestamp = datetime.fromisoformat(timestamp).strftime('%b %d, %Y %H:%M')
                    except: pass
                st.markdown(f"""<div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 8px; border-left: 3px solid #1E3A5F;">
                    <div style="font-size: 11px; color: #666; margin-bottom: 4px;">{timestamp}</div><div>{note.get('text', '')}</div></div>""", unsafe_allow_html=True)
        else:
            st.info("No notes yet")
        new_note = st.text_area("Add a note", key=f"{key_prefix}_new_note", height=80, placeholder="Type your note here...")
        if st.button("Add Note", key=f"{key_prefix}_add_note"):
            if new_note.strip():
                notes = notes.copy() if notes else []
                notes.append({'text': new_note.strip(), 'timestamp': datetime.now().isoformat()})
                return notes
        return notes
    
    def render_metrics_row(projects: List[Dict]) -> None:
        total_projects = len(projects) if projects else 0
        if total_projects == 0:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1: st.metric("Total Objectives", 0)
            with col2: st.metric("Completed", 0)
            with col3: st.metric("In Progress", 0)
            with col4: st.metric("Avg. Completion", "0%")
            with col5: st.metric("Subtasks Done", "0/0")
            with col6: st.metric("Potential Savings", "$0")
            return
        completed = sum(1 for p in projects if p.get('status') == 'Completed')
        in_progress = sum(1 for p in projects if p.get('status') == 'In Progress')
        avg_completion = sum(p.get('completion_percentage', 0) for p in projects) / total_projects
        total_subtasks = sum(len(p.get('subtasks', [])) for p in projects)
        completed_subtasks = sum(sum(1 for s in p.get('subtasks', []) if s.get('completed')) for p in projects)
        total_savings = sum(p.get('potential_savings', 0) for p in projects)
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1: st.metric("Total Objectives", total_projects)
        with col2: st.metric("Completed", completed, f"{completed}/{total_projects}")
        with col3: st.metric("In Progress", in_progress)
        with col4: st.metric("Avg. Completion", f"{avg_completion:.0f}%")
        with col5: st.metric("Subtasks Done", f"{completed_subtasks}/{total_subtasks}")
        with col6: st.metric("Potential Savings", f"${total_savings:,.0f}")


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
    # Use path relative to the app.py file location
    data_dir = os.path.join(ROOT_DIR, "data")
    return DataManager(data_dir=data_dir)


def load_projects():
    """Load projects from storage into session state."""
    dm = get_data_manager()
    
    if 'projects' not in st.session_state:
        loaded = dm.load_projects()
        if loaded:
            st.session_state.projects = loaded
        else:
            # Only use defaults if file is truly empty/missing
            st.session_state.projects = get_default_projects()
            # Save defaults to file
            dm.save_projects(st.session_state.projects)
    
    return st.session_state.projects


def get_default_projects():
    """Return default Q1 2026 supply chain projects if data file is missing."""
    return [
        {
            "id": "proj_001", "name": "CMY Color Strategy Implementation", "objective_number": 1,
            "description": "Implement process for utilizing CMY color strategy and have a documented process for decision making to improve run speeds on HP and gain WIP rate efficiencies.",
            "priority": "High", "status": "Not Started", "owner": "Greg Furner",
            "team_members": ["Greg Furner", "HP Technician", "Production Team"],
            "start_date": "2026-01-06", "due_date": "2026-03-21",
            "estimated_hours": 240, "actual_hours": 0, "budget": 15000, "budget_spent": 0,
            "completion_percentage": 0, "category": "Production Optimization",
            "tags": ["HP Press", "Color Management", "Efficiency"],
            "subtasks": [
                {"id": "task_001_1", "name": "CMY Color Calibration Audit", "description": "Conduct CMY color calibration audit and document current HP press color profiles", "start_date": "2026-01-06", "due_date": "2026-01-24", "owner": "Greg Furner", "completed": False, "completion_criteria": "Completed audit report with baseline color profiles", "success_metric": "100% of active substrate profiles documented", "dependencies": "Access to HP press", "notes": []},
                {"id": "task_001_2", "name": "CMY Decision Matrix Development", "description": "Develop and pilot CMY decision matrix with standardized workflows", "start_date": "2026-01-27", "due_date": "2026-02-21", "owner": "Greg Furner", "completed": False, "completion_criteria": "Written SOP document approved", "success_metric": "10% improvement in setup time", "dependencies": "Completion of audit", "notes": []},
                {"id": "task_001_3", "name": "Production Staff Training", "description": "Train production staff on CMY protocol and implement tracking system", "start_date": "2026-02-24", "due_date": "2026-03-21", "owner": "Greg Furner", "completed": False, "completion_criteria": "All HP press operators trained", "success_metric": "15%+ improvement vs Q4 baseline", "dependencies": "Decision matrix complete", "notes": []}
            ], "notes": []
        },
        {
            "id": "proj_002", "name": "Premium White to Standard White Transition", "objective_number": 2,
            "description": "Validate the ability to switch from Premium White to Standard White when running all print jobs.",
            "priority": "High", "status": "Not Started", "owner": "Greg Furner",
            "team_members": ["Greg Furner", "QA Team", "Cory Timmons"],
            "start_date": "2026-01-06", "due_date": "2026-03-28",
            "estimated_hours": 200, "actual_hours": 0, "budget": 8000, "budget_spent": 0,
            "completion_percentage": 0, "category": "Cost Reduction", "tags": ["Materials", "Cost Savings"],
            "subtasks": [
                {"id": "task_002_1", "name": "Standard White Quality Validation", "description": "Conduct quality validation testing across job types", "start_date": "2026-01-06", "due_date": "2026-01-31", "owner": "Greg Furner", "completed": False, "completion_criteria": "Testing on 15 job types", "success_metric": "90%+ pass rate", "dependencies": "Sample materials", "notes": []},
                {"id": "task_002_2", "name": "Inventory Transition Planning", "description": "Develop inventory transition plan", "start_date": "2026-02-03", "due_date": "2026-02-28", "owner": "Greg Furner", "completed": False, "completion_criteria": "Written transition plan", "success_metric": "80% inventory reduction", "dependencies": "Quality validation", "notes": []},
                {"id": "task_002_3", "name": "Full Production Cutover", "description": "Execute full production cutover to Standard White", "start_date": "2026-03-03", "due_date": "2026-03-28", "owner": "Greg Furner", "completed": False, "completion_criteria": "100% using Standard White", "success_metric": "Zero quality complaints", "dependencies": "Transition plan", "notes": []}
            ], "notes": []
        },
        {
            "id": "proj_003", "name": "30\" Thermal Laminator Acquisition", "objective_number": 3,
            "description": "Work with Print Rush to take on ownership of 30\" China Thermal Laminator.",
            "priority": "High", "status": "Not Started", "owner": "Cory Timmons",
            "team_members": ["Cory Timmons", "Greg Furner", "Legal", "Facilities"],
            "start_date": "2026-01-06", "due_date": "2026-03-28",
            "estimated_hours": 280, "actual_hours": 0, "budget": 25000, "budget_spent": 0,
            "completion_percentage": 0, "category": "Equipment Acquisition", "tags": ["Lamination", "Print Rush"],
            "subtasks": [
                {"id": "task_003_1", "name": "Equipment Transfer Negotiation", "description": "Negotiate equipment transfer terms with Print Rush", "start_date": "2026-01-06", "due_date": "2026-01-31", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Signed agreement", "success_metric": "Favorable terms", "dependencies": "Print Rush confirmation", "notes": []},
                {"id": "task_003_2", "name": "Facility Preparation", "description": "Prepare facility for laminator installation", "start_date": "2026-02-03", "due_date": "2026-02-21", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Site prepared", "success_metric": "Zero delays", "dependencies": "Equipment specs", "notes": []},
                {"id": "task_003_3", "name": "Equipment Installation & Training", "description": "Execute equipment transfer, installation, and training", "start_date": "2026-02-24", "due_date": "2026-03-28", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Equipment operational", "success_metric": "Operational within 2 weeks", "dependencies": "Facility ready", "notes": []}
            ], "notes": []
        },
        {
            "id": "proj_004", "name": "Growve Partnership as 30\" Print Partner", "objective_number": 4,
            "description": "Establish partnership with Growve as 30\" print partner.",
            "priority": "High", "status": "Not Started", "owner": "Cory Timmons",
            "team_members": ["Cory Timmons", "Legal", "Finance", "Greg Furner"],
            "start_date": "2026-01-06", "due_date": "2026-03-31",
            "estimated_hours": 200, "actual_hours": 0, "budget": 12000, "budget_spent": 0,
            "completion_percentage": 0, "category": "Vendor Partnership", "tags": ["Growve", "Printing"],
            "subtasks": [
                {"id": "task_004_1", "name": "Partnership Agreement", "description": "Establish formal partnership agreement with Growve", "start_date": "2026-01-06", "due_date": "2026-02-07", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Signed agreement", "success_metric": "15% below current rates", "dependencies": "Growve capacity confirmation", "notes": []},
                {"id": "task_004_2", "name": "Integrated Workflow Development", "description": "Develop integrated workflow for Growve-printed material", "start_date": "2026-02-10", "due_date": "2026-03-07", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Workflow SOP approved", "success_metric": "Pilot batch processed", "dependencies": "Partnership agreement", "notes": []},
                {"id": "task_004_3", "name": "Production Ramp-Up", "description": "Execute production ramp-up with Growve", "start_date": "2026-03-10", "due_date": "2026-03-31", "owner": "Cory Timmons", "completed": False, "completion_criteria": "50,000 MSI processed", "success_metric": "20% cost savings", "dependencies": "Workflow complete", "notes": []}
            ], "notes": []
        },
        {
            "id": "proj_005", "name": "Dazpak Material Cost Optimization", "objective_number": 5,
            "description": "Work with Dazpak to finalize lowest cost Material through sourcing and Group Buying strategies.",
            "priority": "High", "status": "Not Started", "owner": "Cory Timmons",
            "team_members": ["Cory Timmons", "Finance", "Legal"],
            "start_date": "2026-01-06", "due_date": "2026-03-28",
            "estimated_hours": 160, "actual_hours": 0, "budget": 5000, "budget_spent": 0,
            "completion_percentage": 0, "category": "Procurement", "tags": ["Dazpak", "Materials"],
            "subtasks": [
                {"id": "task_005_1", "name": "Pricing Negotiation", "description": "Conduct formal pricing negotiation with Dazpak", "start_date": "2026-01-06", "due_date": "2026-01-31", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Written proposal submitted", "success_metric": "Within 10% of $0.30/MSI target", "dependencies": "Volume forecasts", "notes": []},
                {"id": "task_005_2", "name": "Supply Agreement Execution", "description": "Finalize supply agreement with Dazpak", "start_date": "2026-02-03", "due_date": "2026-02-28", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Signed agreement", "success_metric": "$0.30/MSI or better", "dependencies": "Negotiation complete", "notes": []},
                {"id": "task_005_3", "name": "Inventory Tracking Implementation", "description": "Implement inventory tracking system at Growve", "start_date": "2026-03-03", "due_date": "2026-03-28", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Tracking system live", "success_metric": "Zero stockouts", "dependencies": "Agreement signed", "notes": []}
            ], "notes": []
        },
        {
            "id": "proj_006", "name": "26\" Flexo Setup with Dazpak", "objective_number": 6,
            "description": "Ensure that Dazpak can quote all standard prelams and laminates on their 26\" Flexographic press.",
            "priority": "Medium", "status": "Not Started", "owner": "Cory Timmons",
            "team_members": ["Cory Timmons", "Sales Team", "Dazpak Technical"],
            "start_date": "2026-01-06", "due_date": "2026-03-28",
            "estimated_hours": 180, "actual_hours": 0, "budget": 10000, "budget_spent": 0,
            "completion_percentage": 0, "category": "Vendor Setup", "tags": ["Dazpak", "Flexo"],
            "subtasks": [
                {"id": "task_006_1", "name": "Product Catalog Audit", "description": "Audit current product catalog for 26\" Flexo compatibility", "start_date": "2026-01-06", "due_date": "2026-01-24", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Product matrix complete", "success_metric": "50+ SKUs identified", "dependencies": "Product master list", "notes": []},
                {"id": "task_006_2", "name": "Press Configuration & Trials", "description": "Configure 26\" Flexo press and conduct print trials", "start_date": "2026-01-27", "due_date": "2026-02-21", "owner": "Cory Timmons", "completed": False, "completion_criteria": "10+ SKUs approved", "success_metric": "Color match within spec", "dependencies": "Catalog audit", "notes": []},
                {"id": "task_006_3", "name": "Quoting & Ordering Workflow", "description": "Establish quoting and ordering workflow", "start_date": "2026-02-24", "due_date": "2026-03-28", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Pricing matrix finalized", "success_metric": "5+ orders by end of Q1", "dependencies": "Print trials", "notes": []}
            ], "notes": []
        },
        {
            "id": "proj_007", "name": "Brand My Bags Vendor Evaluation", "objective_number": 7,
            "description": "Vet Brand My Bags as potential External Vendor for mid web digital print.",
            "priority": "Medium", "status": "Not Started", "owner": "Cory Timmons",
            "team_members": ["Cory Timmons", "QA Team", "Sales Team"],
            "start_date": "2026-01-06", "due_date": "2026-03-28",
            "estimated_hours": 120, "actual_hours": 0, "budget": 3000, "budget_spent": 0,
            "completion_percentage": 0, "category": "Vendor Evaluation", "tags": ["Brand My Bags", "Digital Print"],
            "subtasks": [
                {"id": "task_007_1", "name": "Vendor Qualification", "description": "Conduct initial vendor qualification", "start_date": "2026-01-06", "due_date": "2026-01-31", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Qualification checklist complete", "success_metric": "Pricing 10% below alternatives", "dependencies": "Vendor engagement", "notes": []},
                {"id": "task_007_2", "name": "Sample Order & Validation", "description": "Execute sample order and quality validation", "start_date": "2026-02-03", "due_date": "2026-02-28", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Samples inspected", "success_metric": "95%+ acceptance rate", "dependencies": "Qualification complete", "notes": []},
                {"id": "task_007_3", "name": "Go/No-Go Decision", "description": "Make go/no-go decision and onboard if validated", "start_date": "2026-03-03", "due_date": "2026-03-28", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Decision documented", "success_metric": "10,000 MSI if approved", "dependencies": "Sample validation", "notes": []}
            ], "notes": []
        },
        {
            "id": "proj_008", "name": "Alternative CR Zipper Implementation", "objective_number": 8,
            "description": "Implement alternative CR Zipper setup with External Vendors.",
            "priority": "High", "status": "Not Started", "owner": "Cory Timmons",
            "team_members": ["Cory Timmons", "Legal", "Greg Furner", "Dazpak", "Ross"],
            "start_date": "2026-01-06", "due_date": "2026-03-28",
            "estimated_hours": 200, "actual_hours": 0, "budget": 8000, "budget_spent": 0,
            "completion_percentage": 0, "category": "Product Development", "tags": ["CR Zipper", "Compliance"],
            "subtasks": [
                {"id": "task_008_1", "name": "Legal Patent Review", "description": "Complete legal review for patent infringement", "start_date": "2026-01-06", "due_date": "2026-02-07", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Legal opinion received", "success_metric": "Zero patent conflicts", "dependencies": "Zipper specifications", "notes": []},
                {"id": "task_008_2", "name": "Final Design Validation", "description": "Complete internal design validation", "start_date": "2026-02-03", "due_date": "2026-02-28", "owner": "Greg Furner", "completed": False, "completion_criteria": "Design approved", "success_metric": "90%+ customer acceptance", "dependencies": "Legal review progress", "notes": []},
                {"id": "task_008_3", "name": "Dazpak Training", "description": "Train Dazpak on new CR zipper process", "start_date": "2026-03-03", "due_date": "2026-03-21", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Training complete", "success_metric": "Pilot run within spec", "dependencies": "Design validation", "notes": []},
                {"id": "task_008_4", "name": "Ross Training", "description": "Train Ross on new CR zipper process", "start_date": "2026-03-10", "due_date": "2026-03-28", "owner": "Cory Timmons", "completed": False, "completion_criteria": "Training complete", "success_metric": "Network-wide consistency", "dependencies": "Design validation", "notes": []}
            ], "notes": []
        }
    ]


def save_projects():
    """Save projects from session state to storage."""
    if 'projects' in st.session_state:
        dm = get_data_manager()
        success = dm.save_projects(st.session_state.projects)
        if not success:
            st.error("Failed to save projects!")
        return success
    return False


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
            ["📊 Dashboard", "📋 Projects", "⚙️ Settings"],
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
        if page in ["📋 Projects"]:
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
    
    # Charts Row: Completion Progress and Savings Projection
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            create_completion_chart(projects),
            use_container_width=True,
            key="dashboard_completion"
        )
    
    with col2:
        st.plotly_chart(
            create_savings_chart(projects),
            use_container_width=True,
            key="dashboard_savings"
        )
    
    # Upcoming Deadlines
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
        upcoming_df['Due Date'] = upcoming_df['Due Date'].apply(lambda x: x.strftime('%m/%d/%Y'))
        st.dataframe(
            upcoming_df[['Project', 'Subtask', 'Due Date', 'Owner', 'Status']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("🎉 All subtasks completed!")
    
    # Completion Tracker (collapsed)
    st.divider()
    
    with st.expander("✅ Completion Tracker", expanded=False):
        # Overall Progress
        total_subtasks = sum(len(p.get('subtasks', [])) for p in projects)
        completed_subtasks = sum(
            sum(1 for s in p.get('subtasks', []) if s.get('completed'))
            for p in projects
        )
        overall_percentage = int((completed_subtasks / total_subtasks * 100)) if total_subtasks > 0 else 0
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(render_progress_bar(overall_percentage, height=30), unsafe_allow_html=True)
        with col2:
            st.metric("Subtasks Complete", f"{completed_subtasks}/{total_subtasks}")
        with col3:
            projects_complete = sum(1 for p in projects if p.get('status') == 'Completed')
            st.metric("Objectives Complete", f"{projects_complete}/{len(projects)}")
        
        st.markdown("---")
        
        # Project-by-project breakdown (all collapsed by default)
        for project in sorted(projects, key=lambda x: x.get('objective_number', 999)):
            subtasks = project.get('subtasks', [])
            completed = sum(1 for s in subtasks if s.get('completed'))
            percentage = int((completed / len(subtasks) * 100)) if subtasks else 0
            
            with st.expander(
                f"**Obj {project.get('objective_number', '?')}: {project.get('name', 'Unnamed')}** — {percentage}%",
                expanded=False
            ):
                st.markdown(render_progress_bar(percentage), unsafe_allow_html=True)
                st.caption(f"Owner: {project.get('owner', 'Unassigned')} | Due: {project.get('due_date', 'Not set')}")
                
                if subtasks:
                    for i, subtask in enumerate(subtasks):
                        due_date = subtask.get('due_date')
                        if isinstance(due_date, str):
                            try:
                                due_date = datetime.fromisoformat(due_date).date()
                            except:
                                due_date = None
                        
                        is_completed = subtask.get('completed', False)
                        is_overdue = due_date and due_date < date.today() and not is_completed
                        
                        col1, col2 = st.columns([0.08, 0.92])
                        
                        with col1:
                            new_completed = st.checkbox(
                                "",
                                value=is_completed,
                                key=f"dash_tracker_{project.get('id')}_{i}",
                                label_visibility="collapsed"
                            )
                        
                        with col2:
                            status_icon = "✅" if new_completed else "🔴" if is_overdue else "⬜"
                            style = "text-decoration: line-through; color: #888;" if new_completed else ""
                            due_str = due_date.strftime('%m/%d') if due_date else 'Not set'
                            st.markdown(f"""
                            <span style="{style}">
                                {status_icon} {subtask.get('name', 'Unnamed')}
                                <span style="color: #888; font-size: 0.8rem;">(Due: {due_str})</span>
                            </span>
                            """, unsafe_allow_html=True)
                        
                        # Update if changed
                        if new_completed != is_completed:
                            for pi, p in enumerate(st.session_state.projects):
                                if p.get('id') == project.get('id'):
                                    st.session_state.projects[pi]['subtasks'][i]['completed'] = new_completed
                                    completed_count = sum(1 for s in st.session_state.projects[pi]['subtasks'] if s.get('completed'))
                                    total_count = len(st.session_state.projects[pi]['subtasks'])
                                    st.session_state.projects[pi]['completion_percentage'] = int((completed_count / total_count) * 100) if total_count > 0 else 0
                                    break
                            save_projects()
                            st.rerun()
                else:
                    st.info("No subtasks defined.")


def create_savings_chart(projects: list):
    """Create a bar chart showing potential savings by objective."""
    import plotly.graph_objects as go
    
    # Extract savings data
    obj_names = []
    savings = []
    colors = []
    
    for p in sorted(projects, key=lambda x: x.get('objective_number', 999)):
        obj_num = p.get('objective_number', '?')
        name = p.get('name', 'Unnamed')
        potential_savings = p.get('potential_savings', 0)
        
        obj_names.append(f"Obj {obj_num}")
        savings.append(potential_savings)
        
        # Color based on completion
        completion = p.get('completion_percentage', 0)
        if completion >= 75:
            colors.append('#198754')  # Green
        elif completion >= 25:
            colors.append('#ffc107')  # Yellow
        else:
            colors.append('#6c757d')  # Gray
    
    total_savings = sum(savings)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=obj_names,
        y=savings,
        marker_color=colors,
        text=[f"${s:,.0f}" for s in savings],
        textposition='outside',
        hovertemplate='%{x}<br>Potential Savings: $%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=f"💰 Total Projected Savings: ${total_savings:,.0f}",
            font=dict(size=16)
        ),
        xaxis_title="Objective",
        yaxis_title="Potential Savings ($)",
        yaxis=dict(tickformat="$,.0f"),
        showlegend=False,
        height=350,
        margin=dict(t=60, b=40, l=60, r=20)
    )
    
    return fig


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
# PROJECTS PAGE - ASANA STYLE
# =============================================================================

def render_projects():
    """Render the projects in an Asana-style board with collapsible items and detail sidebar."""
    projects = load_projects()
    
    # Initialize session state for expanded project
    if 'expanded_project_id' not in st.session_state:
        st.session_state.expanded_project_id = None
    
    # Sort by objective number
    projects_sorted = sorted(projects, key=lambda x: x.get('objective_number', 999))
    
    # Global styles for highlighting
    st.markdown("""
    <style>
    .selected-row {
        background: rgba(45, 55, 72, 0.15) !important;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 4px 0;
        border-left: 4px solid #2d3748;
    }
    .normal-row {
        padding: 8px 12px;
        margin: 4px 0;
        border-bottom: 1px solid #eee;
    }
    .normal-row:hover {
        background: rgba(45, 55, 72, 0.05);
        border-radius: 4px;
    }
    .owner-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: bold;
        color: white;
    }
    .drag-handle {
        cursor: grab;
        color: #999;
        padding: 4px;
    }
    .drag-handle:hover {
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create two-column layout: main content (left) and detail sidebar (right)
    if st.session_state.expanded_project_id:
        col_main, col_sidebar = st.columns([2, 2])
    else:
        col_main = st.container()
        col_sidebar = None
    
    # MAIN CONTENT - Project List
    with col_main:
        st.markdown("## 📋 Q1 2026 Supply Chain Objectives")
        
        # Iterate through each project
        for proj_idx, project in enumerate(projects_sorted):
            project_id = project.get('id', f'proj_{proj_idx}')
            obj_num = project.get('objective_number', '?')
            owner = project.get('owner', 'Unassigned')
            owner_initials = ''.join([n[0] for n in owner.split()[:2]]) if owner else '??'
            owner_color = "#4A90D9" if "Greg" in owner else "#50C878" if "Cory" in owner else "#888"
            
            is_expanded = st.session_state.expanded_project_id == project_id
            completion = project.get('completion_percentage', 0)
            status = project.get('status', 'Not Started')
            
            # Status colors
            status_colors = {
                'Not Started': ('#6c757d', 'white'),
                'In Progress': ('#0d6efd', 'white'),
                'Completed': ('#198754', 'white'),
                'On Hold': ('#ffc107', 'black')
            }
            bg_color, text_color = status_colors.get(status, ('#6c757d', 'white'))
            progress_color = "#198754" if completion >= 75 else "#ffc107" if completion >= 25 else "#6c757d"
            
            # Row styling based on selection
            row_class = "selected-row" if is_expanded else "normal-row"
            
            # Render row with columns
            col_num, col_title, col_owner, col_progress, col_status = st.columns([0.4, 4, 0.6, 1, 1])
            
            with col_num:
                st.markdown(f"<span style='font-weight: bold; color: #1E3A5F; font-size: 16px;'>{obj_num}</span>", unsafe_allow_html=True)
            
            with col_title:
                # Clickable title button
                btn_type = "primary" if is_expanded else "secondary"
                if st.button(
                    project.get('name', 'Unnamed'),
                    key=f"select_{project_id}",
                    use_container_width=True,
                    type=btn_type
                ):
                    if is_expanded:
                        st.session_state.expanded_project_id = None
                    else:
                        st.session_state.expanded_project_id = project_id
                    st.rerun()
            
            with col_owner:
                st.markdown(f"""
                <div style="display: flex; justify-content: center; padding-top: 6px;">
                    <span class="owner-avatar" style="background: {owner_color};">{owner_initials}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col_progress:
                st.markdown(f"""
                <div style="text-align: center; padding-top: 4px;">
                    <div style="background: #e9ecef; border-radius: 10px; height: 8px; width: 100%; margin-bottom: 4px;">
                        <div style="background: {progress_color}; width: {completion}%; height: 100%; border-radius: 10px;"></div>
                    </div>
                    <span style="font-size: 11px; color: #666;">{completion}%</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col_status:
                st.markdown(f"""
                <div style="text-align: center; padding-top: 6px;">
                    <span style="background: {bg_color}; color: {text_color}; padding: 3px 10px; border-radius: 12px; font-size: 11px;">
                        {status}
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    # SIDEBAR - Project Details (only shows when expanded)
    if st.session_state.expanded_project_id and col_sidebar:
        with col_sidebar:
            render_project_sidebar(projects_sorted)


def render_project_sidebar(projects: list):
    """Render the detail sidebar for the expanded project."""
    project_id = st.session_state.expanded_project_id
    project = None
    
    for i, p in enumerate(projects):
        if p.get('id') == project_id:
            project = p
            break
    
    if not project:
        st.session_state.expanded_project_id = None
        st.rerun()
        return
    
    obj_num = project.get('objective_number', '?')
    
    # Sidebar background styling
    st.markdown("""
    <style>
    [data-testid="column"]:last-child {
        background: rgba(45, 55, 72, 0.1);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(45, 55, 72, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with close button
    col_title, col_close = st.columns([5, 1])
    with col_title:
        st.markdown(f"### 📌 Objective {obj_num}")
    with col_close:
        if st.button("✕", key="close_sidebar"):
            st.session_state.expanded_project_id = None
            st.rerun()
    
    st.markdown(f"**{project.get('name', 'Unnamed')}**")
    
    # Dependency dropdown - get all subtasks from all projects using actual subtask IDs
    all_subtasks = []
    for p in projects:
        p_num = p.get('objective_number', '?')
        for s_idx, s in enumerate(p.get('subtasks', [])):
            subtask_label = f"{p_num}.{s_idx + 1} - {s.get('name', 'Unnamed')}"
            actual_subtask_id = s.get('id', f"{p.get('id')}_{s_idx}")
            all_subtasks.append((actual_subtask_id, subtask_label))
    
    # Current dependencies
    current_deps = project.get('dependencies', [])
    
    # Create options list
    dep_options = ["None"] + [label for _, label in all_subtasks]
    dep_ids = [None] + [sid for sid, _ in all_subtasks]
    
    # Find current selection index
    current_idx = 0
    if current_deps and len(current_deps) > 0:
        for i, sid in enumerate(dep_ids):
            if sid == current_deps[0]:
                current_idx = i
                break
    
    new_dep = st.selectbox(
        "🔗 Dependency",
        options=dep_options,
        index=current_idx,
        key=f"dep_{project_id}",
        help="Select a subtask this objective depends on"
    )
    
    # Update dependencies
    new_dep_idx = dep_options.index(new_dep)
    new_dep_id = dep_ids[new_dep_idx] if new_dep_idx > 0 else None
    new_deps = [new_dep_id] if new_dep_id else []
    if new_deps != current_deps:
        update_project_field(project_id, 'dependencies', new_deps)
    
    # Potential Savings field
    current_savings = project.get('potential_savings', 0)
    new_savings = st.number_input(
        "💰 Potential Savings ($)",
        min_value=0,
        value=current_savings,
        step=100,
        key=f"savings_{project_id}"
    )
    if new_savings != current_savings:
        update_project_field(project_id, 'potential_savings', new_savings)
    
    st.divider()
    
    # Goal
    st.markdown("##### 📝 Goal")
    new_desc = st.text_area(
        "Goal",
        value=project.get('description', ''),
        key=f"sidebar_desc_{project_id}",
        height=80,
        label_visibility="collapsed"
    )
    if new_desc != project.get('description', ''):
        update_project_field(project_id, 'description', new_desc)
    
    st.divider()
    
    # Collect all dependency IDs across all projects (using actual subtask IDs)
    all_dependency_ids = set()
    for p in projects:
        deps = p.get('dependencies', [])
        for dep_id in deps:
            if dep_id:
                all_dependency_ids.add(dep_id)
    
    # SUBTASKS with integrated reorder
    st.markdown("##### ✅ Subtasks")
    
    subtasks = project.get('subtasks', [])
    
    # Show legend if any subtasks are dependencies
    if subtasks and any(s.get('id') in all_dependency_ids for s in subtasks):
        st.caption("* = dependency for another objective")
    
    if subtasks:
        for sub_idx, subtask in enumerate(subtasks):
            is_completed = subtask.get('completed', False)
            subtask_id = subtask.get('id', f'subtask_{sub_idx}')
            
            due_date = subtask.get('due_date')
            if isinstance(due_date, str):
                try:
                    due_date = datetime.fromisoformat(due_date).date()
                except:
                    due_date = None
            elif isinstance(due_date, datetime):
                due_date = due_date.date()
            
            # Check if this subtask is a dependency (using actual subtask ID)
            is_dependency = subtask_id in all_dependency_ids
            
            # Calculate height based on text length (roughly 35 chars per line)
            name_text = subtask.get('name', '')
            num_lines = max(1, len(name_text) // 35 + 1)
            text_height = max(68, num_lines * 25 + 20)
            
            # Single row: star | checkbox | name (text_area) | date | position | delete
            col_star, col_check, col_name, col_date, col_move, col_del = st.columns([0.04, 0.06, 0.40, 0.22, 0.15, 0.13])
            
            with col_star:
                if is_dependency:
                    st.markdown("<span style='color: #f59e0b; font-size: 14px;'>*</span>", unsafe_allow_html=True)
            
            with col_check:
                new_completed = st.checkbox(
                    "✓",
                    value=is_completed,
                    key=f"chk_{subtask_id}",
                    label_visibility="collapsed"
                )
                if new_completed != is_completed:
                    update_subtask_field(project_id, sub_idx, 'completed', new_completed)
                    recalculate_completion(project_id)
                    st.rerun()
            
            with col_name:
                new_name = st.text_area(
                    "Name",
                    value=name_text,
                    key=f"name_{subtask_id}",
                    label_visibility="collapsed",
                    height=text_height
                )
                if new_name != name_text:
                    update_subtask_field(project_id, sub_idx, 'name', new_name)
            
            with col_date:
                new_due = st.date_input(
                    "Due",
                    value=due_date or date(2026, 3, 31),
                    key=f"due_{subtask_id}",
                    label_visibility="collapsed",
                    format="MM/DD/YYYY"
                )
                if new_due != due_date:
                    update_subtask_field(project_id, sub_idx, 'due_date', new_due)
            
            with col_move:
                positions = list(range(1, len(subtasks) + 1))
                current_pos = sub_idx + 1
                pos_key = f"pos_{subtask_id}"
                new_pos = st.selectbox(
                    "Pos",
                    options=positions,
                    index=sub_idx,
                    key=pos_key,
                    label_visibility="collapsed"
                )
                if new_pos != current_pos:
                    move_subtask_to_position(project_id, sub_idx, new_pos - 1)
                    # Clear all position keys for this project to avoid stale state
                    keys_to_clear = [k for k in st.session_state.keys() if k.startswith('pos_')]
                    for k in keys_to_clear:
                        del st.session_state[k]
                    st.rerun()
            
            with col_del:
                if st.button("🗑️", key=f"del_{subtask_id}", help="Delete"):
                    delete_subtask(project_id, sub_idx)
                    st.rerun()
    
    # Add subtask
    if st.button("➕ Add Subtask", key=f"add_{project_id}"):
        add_new_subtask(project_id, obj_num, len(subtasks))
    
    st.divider()
    
    # Settings
    st.markdown("##### ⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_status = st.selectbox(
            "Status",
            options=['Not Started', 'In Progress', 'Completed', 'On Hold'],
            index=['Not Started', 'In Progress', 'Completed', 'On Hold'].index(
                project.get('status', 'Not Started')) if project.get('status') in 
                ['Not Started', 'In Progress', 'Completed', 'On Hold'] else 0,
            key=f"status_{project_id}"
        )
        if new_status != project.get('status'):
            update_project_field(project_id, 'status', new_status)
        
        new_priority = st.selectbox(
            "Priority",
            options=['High', 'Medium', 'Low'],
            index=['High', 'Medium', 'Low'].index(project.get('priority', 'Medium')),
            key=f"priority_{project_id}"
        )
        if new_priority != project.get('priority'):
            update_project_field(project_id, 'priority', new_priority)
    
    with col2:
        new_owner = st.selectbox(
            "Owner",
            options=['Greg Furner', 'Cory Timmons'],
            index=0 if 'Greg' in project.get('owner', '') else 1,
            key=f"owner_{project_id}"
        )
        if new_owner != project.get('owner'):
            update_project_field(project_id, 'owner', new_owner)
        
        subtask_completion = 0
        if subtasks:
            completed_count = sum(1 for s in subtasks if s.get('completed'))
            subtask_completion = int((completed_count / len(subtasks)) * 100)
        st.metric("Completion", f"{project.get('completion_percentage', subtask_completion)}%")
    
    col3, col4 = st.columns(2)
    
    with col3:
        start_date = project.get('start_date')
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date).date()
            except:
                start_date = date(2026, 1, 6)
        new_start = st.date_input("Start", value=start_date or date(2026, 1, 6), key=f"start_{project_id}", format="MM/DD/YYYY")
        if new_start != start_date:
            update_project_field(project_id, 'start_date', new_start)
    
    with col4:
        due_date_proj = project.get('due_date')
        if isinstance(due_date_proj, str):
            try:
                due_date_proj = datetime.fromisoformat(due_date_proj).date()
            except:
                due_date_proj = date(2026, 3, 31)
        new_due_proj = st.date_input("Due", value=due_date_proj or date(2026, 3, 31), key=f"projdue_{project_id}", format="MM/DD/YYYY")
        if new_due_proj != due_date_proj:
            update_project_field(project_id, 'due_date', new_due_proj)
    
    st.divider()
    
    # Notes
    st.markdown("##### 💬 Notes")
    
    new_note = st.text_area(
        "Note",
        key=f"note_{project_id}",
        height=60,
        placeholder="Add a note...",
        label_visibility="collapsed"
    )
    
    if st.button("➕ Add Note", key=f"addnote_{project_id}", type="primary", use_container_width=True):
        if new_note.strip():
            add_note_to_project(project_id, new_note.strip())
            st.rerun()
    
    notes = project.get('notes', [])
    if notes:
        for note in sorted(notes, key=lambda x: x.get('timestamp', ''), reverse=True):
            ts = note.get('timestamp', '')
            time_str = ""
            if ts:
                try:
                    time_str = datetime.fromisoformat(ts).strftime('%b %d • %I:%M %p')
                except:
                    pass
            st.markdown(f"""
            <div style="background: white; border-radius: 6px; padding: 10px; margin: 8px 0; border-left: 3px solid #4A90D9;">
                <div style="font-size: 10px; color: #888;">{time_str}</div>
                <div style="font-size: 13px; color: #333;">{note.get('text', '')}</div>
            </div>
            """, unsafe_allow_html=True)


def move_subtask_to_position(project_id: str, from_idx: int, to_idx: int):
    """Move a subtask to a specific position."""
    for i, p in enumerate(st.session_state.projects):
        if p.get('id') == project_id:
            subtasks = st.session_state.projects[i].get('subtasks', [])
            if 0 <= from_idx < len(subtasks) and 0 <= to_idx < len(subtasks):
                # Remove from current position and insert at new position
                item = subtasks.pop(from_idx)
                subtasks.insert(to_idx, item)
                st.session_state.projects[i]['subtasks'] = subtasks
            break
    save_projects()


def move_subtask(project_id: str, from_idx: int, to_idx: int):
    """Move a subtask from one position to another (swap)."""
    for i, p in enumerate(st.session_state.projects):
        if p.get('id') == project_id:
            subtasks = st.session_state.projects[i].get('subtasks', [])
            if 0 <= from_idx < len(subtasks) and 0 <= to_idx < len(subtasks):
                subtasks[from_idx], subtasks[to_idx] = subtasks[to_idx], subtasks[from_idx]
                st.session_state.projects[i]['subtasks'] = subtasks
            break
    save_projects()


def delete_subtask(project_id: str, sub_idx: int):
    """Delete a subtask from a project."""
    for i, p in enumerate(st.session_state.projects):
        if p.get('id') == project_id:
            subtasks = st.session_state.projects[i].get('subtasks', [])
            if 0 <= sub_idx < len(subtasks):
                subtasks.pop(sub_idx)
                st.session_state.projects[i]['subtasks'] = subtasks
                # Recalculate completion
                if subtasks:
                    completed_count = sum(1 for s in subtasks if s.get('completed'))
                    st.session_state.projects[i]['completion_percentage'] = int((completed_count / len(subtasks)) * 100)
                else:
                    st.session_state.projects[i]['completion_percentage'] = 0
            break
    save_projects()


def add_note_to_project(project_id: str, note_text: str):
    """Add a new note to a project's notes trail."""
    for i, p in enumerate(st.session_state.projects):
        if p.get('id') == project_id:
            if 'notes' not in st.session_state.projects[i]:
                st.session_state.projects[i]['notes'] = []
            
            new_note = {
                'id': f"note_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                'text': note_text,
                'timestamp': datetime.now().isoformat()
            }
            st.session_state.projects[i]['notes'].append(new_note)
            st.session_state.projects[i]['updated_at'] = datetime.now().isoformat()
            break
    save_projects()


def update_project_field(project_id: str, field: str, value):
    """Update a single field in a project and save."""
    for i, p in enumerate(st.session_state.projects):
        if p.get('id') == project_id:
            st.session_state.projects[i][field] = value
            st.session_state.projects[i]['updated_at'] = datetime.now().isoformat()
            break
    save_projects()


def update_subtask_field(project_id: str, subtask_idx: int, field: str, value):
    """Update a single field in a subtask and save."""
    for i, p in enumerate(st.session_state.projects):
        if p.get('id') == project_id:
            if 'subtasks' in st.session_state.projects[i] and subtask_idx < len(st.session_state.projects[i]['subtasks']):
                st.session_state.projects[i]['subtasks'][subtask_idx][field] = value
                st.session_state.projects[i]['updated_at'] = datetime.now().isoformat()
            break
    save_projects()


def recalculate_completion(project_id: str):
    """Recalculate project completion percentage based on subtasks."""
    for i, p in enumerate(st.session_state.projects):
        if p.get('id') == project_id:
            subtasks = p.get('subtasks', [])
            if subtasks:
                completed_count = sum(1 for s in subtasks if s.get('completed'))
                percentage = int((completed_count / len(subtasks)) * 100)
                st.session_state.projects[i]['completion_percentage'] = percentage
            break
    save_projects()


def add_new_subtask(project_id: str, obj_num: int, current_count: int):
    """Add a new subtask to a project."""
    new_subtask = {
        'id': generate_subtask_id(),
        'name': f'New Subtask {obj_num}.{current_count + 1}',
        'description': '',
        'completion_criteria': '',
        'start_date': date.today().isoformat(),
        'due_date': date(2026, 3, 31).isoformat(),
        'owner': '',
        'dependencies': '',
        'success_metric': '',
        'completed': False,
        'notes': []
    }
    for i, p in enumerate(st.session_state.projects):
        if p.get('id') == project_id:
            if 'subtasks' not in st.session_state.projects[i]:
                st.session_state.projects[i]['subtasks'] = []
            st.session_state.projects[i]['subtasks'].append(new_subtask)
            break
    save_projects()
    st.rerun()


def render_single_project(project: dict):
    """Legacy function - no longer used but kept for compatibility."""
    pass


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
    elif page == "📋 Projects":
        render_projects()
    elif page == "⚙️ Settings":
        render_settings()


if __name__ == "__main__":
    main()
