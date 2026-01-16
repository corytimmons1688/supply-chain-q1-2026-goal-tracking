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
                serialized = self._serialize_dates(projects)
                with open(self.projects_file, 'w') as f:
                    json.dump(serialized, f, indent=2)
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
        data = [{'Project': f"Obj {p.get('objective_number', '?')}: {p.get('name', 'Unnamed')[:30]}",
                 'Completion': p.get('completion_percentage', 0), 'Status': get_status_with_overdue(p),
                 'Owner': p.get('owner', 'Unassigned')} for p in projects]
        df = pd.DataFrame(data).sort_values('Completion', ascending=True)
        fig = px.bar(df, x='Completion', y='Project', orientation='h', color='Status',
                     color_discrete_map=COLORS, custom_data=['Owner', 'Status'])
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Completion: %{x}%<br>Owner: %{customdata[0]}<extra></extra>")
        fig.update_layout(title=dict(text="Project Completion Progress", font=dict(size=18, color=COLORS['primary'])),
                          xaxis_title="Completion %", yaxis_title="", xaxis=dict(range=[0, 100]),
                          height=max(300, len(data) * 40), showlegend=True, margin=dict(l=10, r=10, t=50, b=30))
        return fig
    
    def create_status_pie_chart(projects: List[Dict]) -> go.Figure:
        status_counts = {}
        for p in projects:
            status = get_status_with_overdue(p)
            status_counts[status] = status_counts.get(status, 0) + 1
        fig = go.Figure(data=[go.Pie(labels=list(status_counts.keys()), values=list(status_counts.values()), hole=0.4,
                                      marker_colors=[COLORS.get(s, '#999') for s in status_counts.keys()])])
        fig.update_layout(title=dict(text="Status Distribution", font=dict(size=16, color=COLORS['primary'])),
                          height=300, margin=dict(l=20, r=20, t=50, b=20))
        return fig
    
    def create_owner_workload_chart(projects: List[Dict]) -> go.Figure:
        owner_data = {}
        for p in projects:
            owner = p.get('owner', 'Unassigned')
            if owner not in owner_data:
                owner_data[owner] = {'projects': 0, 'hours': 0}
            owner_data[owner]['projects'] += 1
            owner_data[owner]['hours'] += p.get('estimated_hours', 0)
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
            all_team_members = ['Greg Furner', 'Cory Timmons', 'Legal', 'Finance', 'QA Team', 'Sales Team', 'Production Team', 'IT', 'Facilities', 'HP Technician', 'Dazpak Technical', 'Ross']
            updates['team_members'] = st.multiselect("Team Members", options=all_team_members, default=project.get('team_members', []), key=f"{key_prefix}_team")
        with col2:
            updates['priority'] = st.selectbox("Priority", options=['High', 'Medium', 'Low'],
                index=['High', 'Medium', 'Low'].index(project.get('priority', 'Medium')), key=f"{key_prefix}_priority")
            updates['status'] = st.selectbox("Status", options=['Not Started', 'In Progress', 'Completed', 'On Hold'],
                index=['Not Started', 'In Progress', 'Completed', 'On Hold'].index(project.get('status', 'Not Started')) if project.get('status') in ['Not Started', 'In Progress', 'Completed', 'On Hold'] else 0, key=f"{key_prefix}_status")
            start_date = project.get('start_date')
            due_date = project.get('due_date')
            if isinstance(start_date, str): start_date = datetime.fromisoformat(start_date).date()
            if isinstance(due_date, str): due_date = datetime.fromisoformat(due_date).date()
            updates['start_date'] = st.date_input("Start Date", value=start_date or date(2026, 1, 6), key=f"{key_prefix}_start")
            updates['due_date'] = st.date_input("Due Date", value=due_date or date(2026, 3, 31), key=f"{key_prefix}_due")
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
            updates['start_date'] = st.date_input("Start Date", value=start_date or date(2026, 1, 6), key=f"{key_prefix}_start")
        with col4:
            updates['success_metric'] = st.text_area("Success Metric", value=subtask.get('success_metric', ''), height=80, key=f"{key_prefix}_metric")
            due_date = subtask.get('due_date')
            if isinstance(due_date, str): due_date = datetime.fromisoformat(due_date).date()
            updates['due_date'] = st.date_input("Due Date", value=due_date or date(2026, 1, 31), key=f"{key_prefix}_due")
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
        total_projects = len(projects)
        completed = sum(1 for p in projects if p.get('status') == 'Completed')
        in_progress = sum(1 for p in projects if p.get('status') == 'In Progress')
        overdue = sum(1 for p in projects if p.get('status') != 'Completed' and p.get('due_date') and 
                      (datetime.fromisoformat(p.get('due_date')).date() if isinstance(p.get('due_date'), str) else p.get('due_date')) < date.today())
        avg_completion = sum(p.get('completion_percentage', 0) for p in projects) / total_projects if total_projects > 0 else 0
        total_subtasks = sum(len(p.get('subtasks', [])) for p in projects)
        completed_subtasks = sum(sum(1 for s in p.get('subtasks', []) if s.get('completed')) for p in projects)
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1: st.metric("Total Projects", total_projects)
        with col2: st.metric("Completed", completed, f"{completed}/{total_projects}")
        with col3: st.metric("In Progress", in_progress)
        with col4: st.metric("Overdue", overdue, delta_color="inverse")
        with col5: st.metric("Avg. Completion", f"{avg_completion:.0f}%")
        with col6: st.metric("Subtasks Done", f"{completed_subtasks}/{total_subtasks}")


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
