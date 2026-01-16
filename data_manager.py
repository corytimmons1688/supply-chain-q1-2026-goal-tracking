"""
Data Manager Module
Handles all data persistence operations for the project management tool.
Supports JSON file storage with automatic backup functionality.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import copy


class DataManager:
    """
    Manages project data storage and retrieval.
    Uses JSON files for persistence with automatic date serialization.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the data manager with the specified data directory."""
        self.data_dir = data_dir
        self.projects_file = os.path.join(data_dir, "projects.json")
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _serialize_dates(self, obj: Any) -> Any:
        """Convert date objects to ISO format strings for JSON serialization."""
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_dates(item) for item in obj]
        return obj
    
    def _deserialize_dates(self, obj: Any, date_fields: List[str]) -> Any:
        """Convert ISO format strings back to date objects."""
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
        """
        Save projects list to JSON file.
        Returns True if successful, False otherwise.
        """
        try:
            serialized = self._serialize_dates(projects)
            with open(self.projects_file, 'w') as f:
                json.dump(serialized, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving projects: {e}")
            return False
    
    def load_projects(self) -> List[Dict]:
        """
        Load projects from JSON file.
        Returns empty list if file doesn't exist or on error.
        """
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
    
    def get_project_by_id(self, projects: List[Dict], project_id: str) -> Optional[Dict]:
        """Find and return a project by its ID."""
        for project in projects:
            if project.get('id') == project_id:
                return project
        return None
    
    def update_project(self, projects: List[Dict], project_id: str, updates: Dict) -> List[Dict]:
        """Update a specific project and return the modified list."""
        for i, project in enumerate(projects):
            if project.get('id') == project_id:
                projects[i].update(updates)
                projects[i]['updated_at'] = datetime.now().isoformat()
                break
        return projects
    
    def add_project(self, projects: List[Dict], new_project: Dict) -> List[Dict]:
        """Add a new project to the list."""
        new_project['created_at'] = datetime.now().isoformat()
        new_project['updated_at'] = datetime.now().isoformat()
        projects.append(new_project)
        return projects
    
    def delete_project(self, projects: List[Dict], project_id: str) -> List[Dict]:
        """Remove a project from the list."""
        return [p for p in projects if p.get('id') != project_id]


def generate_project_id() -> str:
    """Generate a unique project ID based on timestamp."""
    return f"proj_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def generate_subtask_id() -> str:
    """Generate a unique subtask ID based on timestamp."""
    return f"task_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
