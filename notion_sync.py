#!/usr/bin/env python3
"""
Notion Task Notification System

Polls a Notion database for tasks and fires desktop notifications
at the right times to help with ADHD task management.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

from notion_client import Client
from plyer import notification
from dateutil import parser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Task:
    """Represents a task from Notion database"""
    id: str
    title: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    description: str
    notion_url: str
    soft_stop_notified: bool = False
    hard_stop_notified: bool = False

class NotionTaskSync:
    def __init__(self):
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
        if not self.notion_token or not self.database_id:
            raise ValueError("NOTION_TOKEN and NOTION_DATABASE_ID must be set in environment")
        
        self.notion = Client(auth=self.notion_token)
        self.active_tasks: Dict[str, Task] = {}
        
    def fetch_tasks(self) -> List[Task]:
        """Fetch tasks from Notion database"""
        try:
            # Get today's date range
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            # Query Notion database for today's tasks
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "and": [
                        {
                            "property": "Start Time",
                            "date": {
                                "on_or_after": start_of_day.isoformat()
                            }
                        },
                        {
                            "property": "Start Time", 
                            "date": {
                                "on_or_before": end_of_day.isoformat()
                            }
                        }
                    ]
                }
            )
            
            tasks = []
            for page in response['results']:
                task = self._parse_task(page)
                if task:
                    tasks.append(task)
                    
            logger.info(f"Fetched {len(tasks)} tasks from Notion")
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []
    
    def _parse_task(self, page: Dict) -> Optional[Task]:
        """Parse a Notion page into a Task object"""
        try:
            properties = page['properties']
            
            # Extract title
            title_prop = properties.get('Name') or properties.get('Title')
            if not title_prop:
                return None
            
            if title_prop['type'] == 'title':
                title = ''.join([text['plain_text'] for text in title_prop['title']])
            else:
                title = 'Untitled Task'
            
            # Extract start time
            start_time = None
            start_prop = properties.get('Start Time') or properties.get('Date')
            if start_prop and start_prop['date']:
                start_time = parser.parse(start_prop['date']['start'])
            
            # Extract end time
            end_time = None
            if start_prop and start_prop['date'] and start_prop['date'].get('end'):
                end_time = parser.parse(start_prop['date']['end'])
            
            # Extract description
            description = ""
            desc_prop = properties.get('Description') or properties.get('Notes')
            if desc_prop and desc_prop['type'] == 'rich_text' and desc_prop['rich_text']:
                description = ''.join([text['plain_text'] for text in desc_prop['rich_text']])
            
            # Create Notion URL
            notion_url = f"https://notion.so/{page['id'].replace('-', '')}"
            
            return Task(
                id=page['id'],
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                notion_url=notion_url
            )
            
        except Exception as e:
            logger.error(f"Error parsing task: {e}")
            return None
    
    def send_notification(self, title: str, message: str, task: Task, notification_type: str):
        """Send desktop notification"""
        try:
            # Create clickable message with Notion URL
            full_message = f"{message}\n\nClick to open in Notion: {task.notion_url}"
            
            notification.notify(
                title=f"🔔 {title}",
                message=full_message,
                timeout=10,  # Show for 10 seconds
                app_name="Notion Task Sync"
            )
            
            logger.info(f"Sent {notification_type} notification for task: {task.title}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def check_notifications(self):
        """Check if any tasks need notifications"""
        now = datetime.now()
        
        for task in self.active_tasks.values():
            if not task.end_time:
                continue
                
            # Check for soft stop (15 minutes before end)
            soft_stop_time = task.end_time - timedelta(minutes=15)
            if (not task.soft_stop_notified and 
                now >= soft_stop_time and 
                now < task.end_time):
                
                self.send_notification(
                    "Soft Stop - 15 min warning",
                    f"Start wrapping up: {task.title}\nEnds at {task.end_time.strftime('%H:%M')}",
                    task,
                    "soft_stop"
                )
                task.soft_stop_notified = True
            
            # Check for hard stop (at end time)
            if (not task.hard_stop_notified and 
                now >= task.end_time):
                
                self.send_notification(
                    "Hard Stop - Time's up!",
                    f"Stop now: {task.title}\nTime to disengage and move on.",
                    task,
                    "hard_stop"
                )
                task.hard_stop_notified = True
    
    def update_active_tasks(self):
        """Update the list of active tasks"""
        tasks = self.fetch_tasks()
        
        # Update existing tasks and add new ones
        for task in tasks:
            if task.id in self.active_tasks:
                # Preserve notification state
                existing_task = self.active_tasks[task.id]
                task.soft_stop_notified = existing_task.soft_stop_notified
                task.hard_stop_notified = existing_task.hard_stop_notified
            
            self.active_tasks[task.id] = task
        
        # Remove tasks that are no longer in today's list
        current_task_ids = {task.id for task in tasks}
        self.active_tasks = {
            task_id: task for task_id, task in self.active_tasks.items()
            if task_id in current_task_ids
        }
    
    def run(self):
        """Main loop - poll database and check for notifications"""
        logger.info("Starting Notion Task Sync...")
        
        while True:
            try:
                # Update tasks every 5 minutes
                self.update_active_tasks()
                
                # Check for notifications every 30 seconds
                for _ in range(10):  # 10 * 30 seconds = 5 minutes
                    self.check_notifications()
                    time.sleep(30)
                    
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait a minute before retrying

def main():
    """Entry point"""
    try:
        sync = NotionTaskSync()
        sync.run()
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        print(f"Error: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file with NOTION_TOKEN and NOTION_DATABASE_ID")
        print("2. Set up your Notion integration and database properly")

if __name__ == "__main__":
    main() 