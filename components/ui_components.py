"""
UI Components Module
Contains reusable Streamlit UI components for project management.
"""

import streamlit as st
from datetime import datetime, date
from typing import Dict, List, Optional, Callable
from utils.data_manager import generate_subtask_id


def render_status_badge(status: str) -> str:
    """Return HTML for a colored status badge."""
    colors = {
        'Not Started': '#6c757d',
        'In Progress': '#0d6efd',
        'Completed': '#198754',
        'Overdue': '#dc3545',
        'On Hold': '#ffc107'
    }
    color = colors.get(status, '#6c757d')
    return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{status}</span>'


def render_priority_badge(priority: str) -> str:
    """Return HTML for a colored priority badge."""
    colors = {
        'High': '#dc3545',
        'Medium': '#ffc107',
        'Low': '#198754'
    }
    color = colors.get(priority, '#6c757d')
    text_color = 'white' if priority != 'Medium' else 'black'
    return f'<span style="background-color: {color}; color: {text_color}; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{priority}</span>'


def render_progress_bar(percentage: int, height: int = 20) -> str:
    """Return HTML for a progress bar."""
    color = '#198754' if percentage >= 75 else '#ffc107' if percentage >= 50 else '#dc3545' if percentage > 0 else '#6c757d'
    return f'''
    <div style="background-color: #e9ecef; border-radius: 4px; height: {height}px; width: 100%;">
        <div style="background-color: {color}; width: {percentage}%; height: 100%; border-radius: 4px; 
                    display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">
            {percentage}%
        </div>
    </div>
    '''


def render_project_card(project: Dict, on_edit: Optional[Callable] = None) -> None:
    """Render a project card with summary information."""
    status = project.get('status', 'Not Started')
    
    # Check for overdue
    due_date = project.get('due_date')
    if isinstance(due_date, str):
        due_date = datetime.fromisoformat(due_date).date()
    if due_date and due_date < date.today() and status != 'Completed':
        status = 'Overdue'
    
    completion = project.get('completion_percentage', 0)
    
    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; background: white;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                <div>
                    <h4 style="margin: 0; color: #1E3A5F;">Objective {project.get('objective_number', '?')}: {project.get('name', 'Unnamed')}</h4>
                    <p style="color: #666; font-size: 13px; margin: 5px 0;">{project.get('description', '')[:150]}{'...' if len(project.get('description', '')) > 150 else ''}</p>
                </div>
                <div style="text-align: right;">
                    {render_status_badge(status)}
                    <br><br>
                    {render_priority_badge(project.get('priority', 'Medium'))}
                </div>
            </div>
            <div style="display: flex; gap: 20px; font-size: 13px; color: #666; margin-bottom: 10px;">
                <span>👤 {project.get('owner', 'Unassigned')}</span>
                <span>📅 Due: {due_date.strftime('%b %d, %Y') if due_date else 'Not set'}</span>
                <span>💰 ${project.get('budget', 0):,.0f}</span>
                <span>⏱️ {project.get('estimated_hours', 0)}h estimated</span>
            </div>
            {render_progress_bar(completion)}
        </div>
        """, unsafe_allow_html=True)


def render_project_editor(project: Dict, key_prefix: str = "") -> Dict:
    """
    Render editable fields for a project and return updated values.
    
    Args:
        project: The project dictionary to edit
        key_prefix: Prefix for Streamlit widget keys to ensure uniqueness
    
    Returns:
        Dictionary with updated project values
    """
    updates = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        updates['name'] = st.text_input(
            "Project Name",
            value=project.get('name', ''),
            key=f"{key_prefix}_name"
        )
        
        updates['description'] = st.text_area(
            "Description",
            value=project.get('description', ''),
            height=100,
            key=f"{key_prefix}_desc"
        )
        
        updates['owner'] = st.selectbox(
            "Owner",
            options=['Greg Furner', 'Cory Timmons', 'Other'],
            index=['Greg Furner', 'Cory Timmons', 'Other'].index(project.get('owner', 'Other')) 
                  if project.get('owner') in ['Greg Furner', 'Cory Timmons', 'Other'] else 2,
            key=f"{key_prefix}_owner"
        )
        
        # Team members as multiselect
        all_team_members = ['Greg Furner', 'Cory Timmons', 'Legal', 'Finance', 'QA Team', 
                           'Sales Team', 'Production Team', 'IT', 'Facilities', 'HP Technician',
                           'Dazpak Technical', 'Ross']
        updates['team_members'] = st.multiselect(
            "Team Members",
            options=all_team_members,
            default=project.get('team_members', []),
            key=f"{key_prefix}_team"
        )
    
    with col2:
        updates['priority'] = st.selectbox(
            "Priority",
            options=['High', 'Medium', 'Low'],
            index=['High', 'Medium', 'Low'].index(project.get('priority', 'Medium')),
            key=f"{key_prefix}_priority"
        )
        
        updates['status'] = st.selectbox(
            "Status",
            options=['Not Started', 'In Progress', 'Completed', 'On Hold'],
            index=['Not Started', 'In Progress', 'Completed', 'On Hold'].index(
                project.get('status', 'Not Started')) if project.get('status') in 
                ['Not Started', 'In Progress', 'Completed', 'On Hold'] else 0,
            key=f"{key_prefix}_status"
        )
        
        # Date inputs
        start_date = project.get('start_date')
        due_date = project.get('due_date')
        
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date).date()
        
        updates['start_date'] = st.date_input(
            "Start Date",
            value=start_date or date(2026, 1, 6),
            key=f"{key_prefix}_start"
        )
        
        updates['due_date'] = st.date_input(
            "Due Date",
            value=due_date or date(2026, 3, 31),
            key=f"{key_prefix}_due"
        )
    
    # Additional fields in expandable section
    with st.expander("Additional Details", expanded=False):
        col3, col4 = st.columns(2)
        
        with col3:
            updates['estimated_hours'] = st.number_input(
                "Estimated Hours",
                min_value=0,
                value=project.get('estimated_hours', 0),
                key=f"{key_prefix}_est_hours"
            )
            
            updates['actual_hours'] = st.number_input(
                "Actual Hours Spent",
                min_value=0,
                value=project.get('actual_hours', 0),
                key=f"{key_prefix}_act_hours"
            )
            
            updates['completion_percentage'] = st.slider(
                "Completion %",
                min_value=0,
                max_value=100,
                value=project.get('completion_percentage', 0),
                key=f"{key_prefix}_completion"
            )
        
        with col4:
            updates['budget'] = st.number_input(
                "Budget ($)",
                min_value=0,
                value=project.get('budget', 0),
                key=f"{key_prefix}_budget"
            )
            
            updates['budget_spent'] = st.number_input(
                "Budget Spent ($)",
                min_value=0,
                value=project.get('budget_spent', 0),
                key=f"{key_prefix}_spent"
            )
            
            updates['category'] = st.text_input(
                "Category",
                value=project.get('category', ''),
                key=f"{key_prefix}_category"
            )
        
        # Tags
        current_tags = project.get('tags', [])
        tags_str = st.text_input(
            "Tags (comma-separated)",
            value=', '.join(current_tags) if current_tags else '',
            key=f"{key_prefix}_tags"
        )
        updates['tags'] = [t.strip() for t in tags_str.split(',') if t.strip()]
    
    return updates


def render_subtask_editor(subtask: Dict, key_prefix: str = "") -> Dict:
    """
    Render editable fields for a subtask and return updated values.
    """
    updates = {}
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        updates['name'] = st.text_input(
            "Subtask Name",
            value=subtask.get('name', ''),
            key=f"{key_prefix}_name"
        )
    
    with col2:
        updates['completed'] = st.checkbox(
            "Completed",
            value=subtask.get('completed', False),
            key=f"{key_prefix}_completed"
        )
    
    updates['description'] = st.text_area(
        "Description",
        value=subtask.get('description', ''),
        height=80,
        key=f"{key_prefix}_desc"
    )
    
    col3, col4 = st.columns(2)
    
    with col3:
        updates['completion_criteria'] = st.text_area(
            "Completion Criteria",
            value=subtask.get('completion_criteria', ''),
            height=80,
            key=f"{key_prefix}_criteria"
        )
        
        start_date = subtask.get('start_date')
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        updates['start_date'] = st.date_input(
            "Start Date",
            value=start_date or date(2026, 1, 6),
            key=f"{key_prefix}_start"
        )
    
    with col4:
        updates['success_metric'] = st.text_area(
            "Success Metric",
            value=subtask.get('success_metric', ''),
            height=80,
            key=f"{key_prefix}_metric"
        )
        
        due_date = subtask.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date).date()
        updates['due_date'] = st.date_input(
            "Due Date",
            value=due_date or date(2026, 1, 31),
            key=f"{key_prefix}_due"
        )
    
    updates['owner'] = st.text_input(
        "Owner",
        value=subtask.get('owner', ''),
        key=f"{key_prefix}_owner"
    )
    
    updates['dependencies'] = st.text_area(
        "Dependencies",
        value=subtask.get('dependencies', ''),
        height=60,
        key=f"{key_prefix}_deps"
    )
    
    return updates


def render_subtask_list(subtasks: List[Dict], project_id: str) -> List[Dict]:
    """
    Render a list of subtasks with checkboxes and return updated list.
    """
    updated_subtasks = []
    
    for i, subtask in enumerate(subtasks):
        due_date = subtask.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date).date()
        
        # Determine status
        is_completed = subtask.get('completed', False)
        is_overdue = due_date and due_date < date.today() and not is_completed
        
        status_icon = "✅" if is_completed else "🔴" if is_overdue else "⏳"
        
        col1, col2, col3 = st.columns([0.5, 4, 1])
        
        with col1:
            completed = st.checkbox(
                "",
                value=is_completed,
                key=f"subtask_{project_id}_{i}_check",
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown(f"""
            <div style="{'text-decoration: line-through; color: #888;' if completed else ''}">
                <strong>{status_icon} {subtask.get('name', 'Unnamed Subtask')}</strong>
                <br><span style="font-size: 12px; color: #666;">
                    Due: {due_date.strftime('%b %d') if due_date else 'Not set'} | 
                    Owner: {subtask.get('owner', 'Unassigned')}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("📝", key=f"edit_subtask_{project_id}_{i}", help="Edit subtask"):
                st.session_state[f'editing_subtask_{project_id}'] = i
        
        updated_subtask = subtask.copy()
        updated_subtask['completed'] = completed
        updated_subtasks.append(updated_subtask)
    
    return updated_subtasks


def render_notes_section(notes: List[Dict], key_prefix: str) -> List[Dict]:
    """
    Render notes section with add/view functionality.
    """
    st.markdown("#### Notes & Comments")
    
    # Display existing notes
    if notes:
        for i, note in enumerate(notes):
            timestamp = note.get('timestamp', '')
            if isinstance(timestamp, str) and timestamp:
                try:
                    timestamp = datetime.fromisoformat(timestamp).strftime('%b %d, %Y %H:%M')
                except:
                    pass
            
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 8px; border-left: 3px solid #1E3A5F;">
                <div style="font-size: 11px; color: #666; margin-bottom: 4px;">{timestamp}</div>
                <div>{note.get('text', '')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No notes yet")
    
    # Add new note
    new_note = st.text_area(
        "Add a note",
        key=f"{key_prefix}_new_note",
        height=80,
        placeholder="Type your note here..."
    )
    
    if st.button("Add Note", key=f"{key_prefix}_add_note"):
        if new_note.strip():
            notes = notes.copy() if notes else []
            notes.append({
                'text': new_note.strip(),
                'timestamp': datetime.now().isoformat()
            })
            return notes
    
    return notes


def render_metrics_row(projects: List[Dict]) -> None:
    """Render key metrics in a row of cards."""
    total_projects = len(projects)
    completed = sum(1 for p in projects if p.get('status') == 'Completed')
    in_progress = sum(1 for p in projects if p.get('status') == 'In Progress')
    
    # Calculate overdue
    overdue = 0
    for p in projects:
        if p.get('status') != 'Completed':
            due_date = p.get('due_date')
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date).date()
            if due_date and due_date < date.today():
                overdue += 1
    
    total_budget = sum(p.get('budget', 0) for p in projects)
    total_spent = sum(p.get('budget_spent', 0) for p in projects)
    avg_completion = sum(p.get('completion_percentage', 0) for p in projects) / total_projects if total_projects > 0 else 0
    
    total_subtasks = sum(len(p.get('subtasks', [])) for p in projects)
    completed_subtasks = sum(
        sum(1 for s in p.get('subtasks', []) if s.get('completed'))
        for p in projects
    )
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Projects", total_projects)
    with col2:
        st.metric("Completed", completed, f"{completed}/{total_projects}")
    with col3:
        st.metric("In Progress", in_progress)
    with col4:
        st.metric("Overdue", overdue, delta_color="inverse")
    with col5:
        st.metric("Avg. Completion", f"{avg_completion:.0f}%")
    with col6:
        st.metric("Subtasks Done", f"{completed_subtasks}/{total_subtasks}")
