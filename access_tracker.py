import json
from datetime import datetime
from typing import Dict, List
import os

class AccessTracker:
    def __init__(self):
        self.file_path = 'access_attempts.json'
        self.attempts = self._load_attempts()
        
    def _load_attempts(self) -> Dict:
        """Load existing attempts from file"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
        
    def _save_attempts(self):
        """Save attempts to file"""
        with open(self.file_path, 'w') as f:
            json.dump(self.attempts, f, indent=4)
            
    def record_attempt(self, user_id: int, username: str = None, first_name: str = None):
        """Record an unauthorized access attempt"""
        user_id = str(user_id)  # Convert to string for JSON compatibility
        
        if user_id not in self.attempts:
            self.attempts[user_id] = {
                'username': username,
                'first_name': first_name,
                'attempts': []
            }
            
        self.attempts[user_id]['attempts'].append(datetime.now().isoformat())
        self.attempts[user_id]['last_attempt'] = datetime.now().isoformat()
        self.attempts[user_id]['total_attempts'] = len(self.attempts[user_id]['attempts'])
        
        # Update user info in case it changed
        if username:
            self.attempts[user_id]['username'] = username
        if first_name:
            self.attempts[user_id]['first_name'] = first_name
            
        self._save_attempts()
        
    def get_all_attempts(self) -> Dict:
        """Get all recorded attempts"""
        return self.attempts
        
    def get_user_attempts(self, user_id: int) -> Dict:
        """Get attempts for a specific user"""
        return self.attempts.get(str(user_id), {})
