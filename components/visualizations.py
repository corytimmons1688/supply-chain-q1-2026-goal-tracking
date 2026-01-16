"""
Visualization Components Module
Contains functions for creating charts, timelines, and visual elements.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional


# Color scheme for consistent styling
COLORS = {
    'Not Started': '#6c757d',      # Gray
    'In Progress': '#0d6efd',      # Blue
    'Completed': '#198754',        # Green
    'Overdue': '#dc3545',          # Red
    'On Hold': '#ffc107',          # Yellow
    'High': '#dc3545',             # Red
    'Medium': '#ffc107',           # Yellow
    'Low': '#198754',              # Green
    'primary': '#1E3A5F',          # Dark blue
    'secondary': '#2B547E',        # Medium blue
    'accent': '#4A90D9',           # Light blue
    'background': '#f8f9fa',       # Light gray
}


def get_status_with_overdue(project: Dict) -> str:
    """
    Determine project status, marking as Overdue if past due date and not completed.
    """
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
    """
    Create an interactive Gantt chart for projects and optionally subtasks.
    
    Args:
        projects: List of project dictionaries
        filter_owner: Filter by owner name
        filter_status: Filter by status
        filter_priority: Filter by priority
        show_subtasks: Whether to include subtasks in the chart
    
    Returns:
        Plotly Figure object
    """
    tasks = []
    
    for project in projects:
        # Apply filters
        if filter_owner and filter_owner != "All" and project.get('owner') != filter_owner:
            continue
        if filter_status and filter_status != "All":
            actual_status = get_status_with_overdue(project)
            if actual_status != filter_status:
                continue
        if filter_priority and filter_priority != "All" and project.get('priority') != filter_priority:
            continue
        
        # Parse dates
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
        
        # Add project bar
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
            'Description': project.get('description', '')[:100] + '...' if len(project.get('description', '')) > 100 else project.get('description', '')
        })
        
        # Add subtasks if enabled
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
                    'Description': subtask.get('description', '')[:80] + '...' if len(subtask.get('description', '')) > 80 else subtask.get('description', '')
                })
    
    if not tasks:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No projects match the selected filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#666")
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=200
        )
        return fig
    
    df = pd.DataFrame(tasks)
    
    # Create Gantt chart
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Resource",
        color_discrete_map=COLORS,
        custom_data=['Owner', 'Completion', 'Priority', 'Budget', 'Type', 'Description']
    )
    
    # Update hover template
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>" +
                      "Start: %{x}<br>" +
                      "End: %{base}<br>" +
                      "Owner: %{customdata[0]}<br>" +
                      "Completion: %{customdata[1]}%<br>" +
                      "Priority: %{customdata[2]}<br>" +
                      "Budget: %{customdata[3]}<br>" +
                      "<br>%{customdata[5]}<extra></extra>"
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Q1 2026 Supply Chain Timeline",
            font=dict(size=20, color=COLORS['primary'])
        ),
        xaxis_title="Date",
        yaxis_title="",
        showlegend=True,
        legend_title_text="Status",
        height=max(400, len(tasks) * 35),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(
            tickformat="%b %d",
            dtick="D7",
            tickangle=-45,
            range=[
                datetime(2026, 1, 1),
                datetime(2026, 4, 7)
            ]
        ),
        margin=dict(l=10, r=10, t=60, b=80)
    )
    
    # Add today line
    today = date.today()
    if datetime(2026, 1, 1).date() <= today <= datetime(2026, 4, 7).date():
        fig.add_vline(
            x=today,
            line_dash="dash",
            line_color="red",
            annotation_text="Today",
            annotation_position="top"
        )
    
    return fig


def create_completion_chart(projects: List[Dict]) -> go.Figure:
    """
    Create a horizontal bar chart showing completion percentage for all projects.
    """
    data = []
    for project in projects:
        data.append({
            'Project': f"Obj {project.get('objective_number', '?')}: {project.get('name', 'Unnamed')[:30]}",
            'Completion': project.get('completion_percentage', 0),
            'Status': get_status_with_overdue(project),
            'Owner': project.get('owner', 'Unassigned')
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('Completion', ascending=True)
    
    fig = px.bar(
        df,
        x='Completion',
        y='Project',
        orientation='h',
        color='Status',
        color_discrete_map=COLORS,
        custom_data=['Owner', 'Status']
    )
    
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>" +
                      "Completion: %{x}%<br>" +
                      "Owner: %{customdata[0]}<br>" +
                      "Status: %{customdata[1]}<extra></extra>"
    )
    
    fig.update_layout(
        title=dict(
            text="Project Completion Progress",
            font=dict(size=18, color=COLORS['primary'])
        ),
        xaxis_title="Completion %",
        yaxis_title="",
        xaxis=dict(range=[0, 100]),
        height=max(300, len(data) * 40),
        showlegend=True,
        legend_title_text="Status",
        margin=dict(l=10, r=10, t=50, b=30)
    )
    
    return fig


def create_status_pie_chart(projects: List[Dict]) -> go.Figure:
    """
    Create a pie chart showing project status distribution.
    """
    status_counts = {}
    for project in projects:
        status = get_status_with_overdue(project)
        status_counts[status] = status_counts.get(status, 0) + 1
    
    fig = go.Figure(data=[go.Pie(
        labels=list(status_counts.keys()),
        values=list(status_counts.values()),
        hole=0.4,
        marker_colors=[COLORS.get(s, '#999') for s in status_counts.keys()]
    )])
    
    fig.update_layout(
        title=dict(
            text="Status Distribution",
            font=dict(size=16, color=COLORS['primary'])
        ),
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


def create_owner_workload_chart(projects: List[Dict]) -> go.Figure:
    """
    Create a bar chart showing workload distribution by owner.
    """
    owner_data = {}
    for project in projects:
        owner = project.get('owner', 'Unassigned')
        if owner not in owner_data:
            owner_data[owner] = {'projects': 0, 'hours': 0, 'subtasks': 0}
        owner_data[owner]['projects'] += 1
        owner_data[owner]['hours'] += project.get('estimated_hours', 0)
        owner_data[owner]['subtasks'] += len(project.get('subtasks', []))
    
    df = pd.DataFrame([
        {'Owner': owner, 'Projects': data['projects'], 'Estimated Hours': data['hours'], 'Subtasks': data['subtasks']}
        for owner, data in owner_data.items()
    ])
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Projects by Owner", "Estimated Hours by Owner"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    fig.add_trace(
        go.Bar(name='Projects', x=df['Owner'], y=df['Projects'], marker_color=COLORS['primary']),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(name='Hours', x=df['Owner'], y=df['Estimated Hours'], marker_color=COLORS['accent']),
        row=1, col=2
    )
    
    fig.update_layout(
        title=dict(
            text="Workload Distribution",
            font=dict(size=18, color=COLORS['primary'])
        ),
        height=350,
        showlegend=False,
        margin=dict(l=10, r=10, t=80, b=30)
    )
    
    return fig


def create_budget_chart(projects: List[Dict]) -> go.Figure:
    """
    Create a chart comparing budget allocation vs. spent across projects.
    """
    data = []
    for project in projects:
        data.append({
            'Project': f"Obj {project.get('objective_number', '?')}",
            'Budget': project.get('budget', 0),
            'Spent': project.get('budget_spent', 0),
            'Name': project.get('name', 'Unnamed')
        })
    
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Budget',
        x=df['Project'],
        y=df['Budget'],
        marker_color=COLORS['secondary'],
        customdata=df['Name'],
        hovertemplate="<b>%{customdata}</b><br>Budget: $%{y:,.0f}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        name='Spent',
        x=df['Project'],
        y=df['Spent'],
        marker_color=COLORS['accent'],
        customdata=df['Name'],
        hovertemplate="<b>%{customdata}</b><br>Spent: $%{y:,.0f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="Budget vs. Actual Spend",
            font=dict(size=18, color=COLORS['primary'])
        ),
        xaxis_title="Objective",
        yaxis_title="Amount ($)",
        barmode='group',
        height=350,
        margin=dict(l=10, r=10, t=50, b=30)
    )
    
    return fig


def create_priority_chart(projects: List[Dict]) -> go.Figure:
    """
    Create a chart showing project distribution by priority.
    """
    priority_counts = {}
    for project in projects:
        priority = project.get('priority', 'Medium')
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    # Ensure order
    ordered_priorities = ['High', 'Medium', 'Low']
    labels = [p for p in ordered_priorities if p in priority_counts]
    values = [priority_counts[p] for p in labels]
    colors = [COLORS.get(p, '#999') for p in labels]
    
    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker_color=colors
    )])
    
    fig.update_layout(
        title=dict(
            text="Projects by Priority",
            font=dict(size=16, color=COLORS['primary'])
        ),
        xaxis_title="Priority",
        yaxis_title="Count",
        height=300,
        margin=dict(l=10, r=10, t=50, b=30)
    )
    
    return fig


def create_monthly_milestone_chart(projects: List[Dict]) -> go.Figure:
    """
    Create a chart showing milestone distribution across Q1 months.
    """
    monthly_data = {'January': 0, 'February': 0, 'March': 0}
    
    for project in projects:
        for subtask in project.get('subtasks', []):
            due_date = subtask.get('due_date')
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date).date()
            if due_date:
                month = due_date.strftime('%B')
                if month in monthly_data:
                    monthly_data[month] += 1
    
    fig = go.Figure(data=[go.Bar(
        x=list(monthly_data.keys()),
        y=list(monthly_data.values()),
        marker_color=[COLORS['primary'], COLORS['secondary'], COLORS['accent']]
    )])
    
    fig.update_layout(
        title=dict(
            text="Subtask Deadlines by Month",
            font=dict(size=16, color=COLORS['primary'])
        ),
        xaxis_title="Month",
        yaxis_title="Subtasks Due",
        height=300,
        margin=dict(l=10, r=10, t=50, b=30)
    )
    
    return fig
