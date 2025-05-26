#!/usr/bin/env python3
"""
Notion Task Notification System

Polls a Notion database for tasks and fires desktop notifications
at the right times to help with ADHD task management.
"""

import os
import time
import logging
from datetime import datetime, timedelta, timezone
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

def ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware, defaulting to local timezone if naive"""
    if dt.tzinfo is None:
        # If naive, assume local timezone
        return dt.replace(tzinfo=timezone.utc)
    return dt

def get_current_time() -> datetime:
    """Get current time as timezone-aware datetime"""
    return datetime.now(timezone.utc)

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
            # Get today's date range in UTC
            now = get_current_time()
            today = now.date()
            start_of_day = datetime.combine(today, datetime.min.time(), timezone.utc)
            end_of_day = datetime.combine(today, datetime.max.time(), timezone.utc)
            
            # Query Notion database for today's tasks
            response = self.notion.databases.query(
                database_id=self.database_id,
                filter={
                    "and": [
                        {
                            "property": "Due",
                            "date": {
                                "on_or_after": start_of_day.isoformat()
                            }
                        },
                        {
                            "property": "Due", 
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
            
            # Debug: Show details of each task
            for i, task in enumerate(tasks, 1):
                logger.info(f"Task {i}: '{task.title}'")
                logger.info(f"  - ID: {task.id}")
                logger.info(f"  - Start Time: {task.start_time}")
                logger.info(f"  - End Time: {task.end_time}")
                logger.info(f"  - Description: {task.description[:100]}{'...' if len(task.description) > 100 else ''}")
                logger.info(f"  - Notion URL: {task.notion_url}")
                logger.info("  ---")
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []
    
    def _parse_task(self, page: Dict) -> Optional[Task]:
        """Parse a Notion page into a Task object"""
        try:
            properties = page['properties']
            
            # Debug: Show raw page properties for this task
            title_prop = properties.get('Name') or properties.get('Title')
            task_title = 'Unknown'
            if title_prop and title_prop['type'] == 'title':
                task_title = ''.join([text['plain_text'] for text in title_prop['title']])
            
            logger.info(f"=== PARSING TASK: {task_title} ===")
            
            # Debug: Show raw Due property data
            due_prop = properties.get('Due') or properties.get('Date')
            if due_prop:
                logger.info(f"Raw Due property: {due_prop}")
            else:
                logger.info("No Due property found")
                
            logger.info("=== END TASK PARSING ===\n")
            
            # Extract title
            title_prop = properties.get('Name') or properties.get('Title')
            if not title_prop:
                return None
            
            if title_prop['type'] == 'title':
                title = ''.join([text['plain_text'] for text in title_prop['title']])
            else:
                title = 'Untitled Task'
            
            # Extract start time and end time from Due property
            start_time = None
            end_time = None
            due_prop = properties.get('Due') or properties.get('Date')
            if due_prop and due_prop['date']:
                date_start = due_prop['date']['start']
                date_end = due_prop['date'].get('end')
                
                logger.info(f"Date start: {date_start}")
                logger.info(f"Date end: {date_end}")
                
                # Check if this is a date-only (no time) or datetime
                # Date-only format: "2025-05-26"
                # DateTime format: "2025-05-26T14:00:00.000-07:00" or similar
                if 'T' in date_start:
                    # This has a time component - parse as datetime
                    start_time = ensure_timezone_aware(parser.parse(date_start))
                    logger.info(f"Parsed as datetime: {start_time}")
                    
                    if date_end:
                        end_time = ensure_timezone_aware(parser.parse(date_end))
                        logger.info(f"Parsed end as datetime: {end_time}")
                    else:
                        # No end time specified - leave as None
                        end_time = None
                        logger.info("No end time specified - leaving as None")
                else:
                    # This is date-only (no time) - treat as all-day/no specific time
                    logger.info("Date-only detected - not setting start/end times")
                    start_time = None
                    end_time = None
            else:
                logger.info("No Due date property - not setting start/end times")
            
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
            # Temporarily disabled - just log what would be sent
            logger.info(f"[NOTIFICATION DISABLED] Would send {notification_type} notification:")
            logger.info(f"  Title: 🔔 {title}")
            logger.info(f"  Message: {message}")
            logger.info(f"  Task: {task.title}")
            logger.info(f"  Notion URL: {task.notion_url}")
            
            # TODO: Re-enable when notification system is working
            # notification.notify(
            #     title=f"🔔 {title}",
            #     message=full_message,
            #     timeout=10,
            #     app_name="Notion Task Sync"
            # )
            
        except Exception as e:
            logger.error(f"Error in notification logic: {e}")
    
    def check_notifications(self):
        """Check if any tasks need notifications"""
        now = get_current_time()
        
        for task in self.active_tasks.values():
            # Handle tasks with start time only (no end time)
            if task.start_time and not task.end_time:
                # Check for start notification
                if (not task.soft_stop_notified and 
                    now >= task.start_time):
                    
                    self.send_notification(
                        "Start Now",
                        f"Time to begin: {task.title}\nStarted at {task.start_time.strftime('%H:%M')}",
                        task,
                        "start_now"
                    )
                    task.soft_stop_notified = True  # Reuse this flag to avoid repeat notifications
                continue
            
            # Handle tasks with both start and end times
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

def test_connection():
    """Test Notion API connection and database access"""
    
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_token:
        print("❌ NOTION_TOKEN not found in .env file")
        return False
        
    if not database_id:
        print("❌ NOTION_DATABASE_ID not found in .env file")
        return False
    
    print("✅ Environment variables loaded")
    
    try:
        # Initialize Notion client
        notion = Client(auth=notion_token)
        print("✅ Notion client initialized")
        
        # Test database access
        response = notion.databases.retrieve(database_id=database_id)
        print(f"✅ Database found: {response['title'][0]['plain_text']}")
        
        # Test querying database
        query_response = notion.databases.query(database_id=database_id)
        print(f"✅ Database query successful: {len(query_response['results'])} pages found")
        
        # Show database properties
        print("\n📋 Database Properties:")
        for prop_name, prop_data in response['properties'].items():
            prop_type = prop_data['type']
            print(f"  - {prop_name}: {prop_type}")
        
        print("\n🎉 Connection test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure your Notion integration token is correct")
        print("2. Verify the database ID is correct")
        print("3. Ensure the integration has access to the database")
        return False

def main():
    """Entry point"""
    print("🧪 Testing Notion connection...\n")
    
    # Test connection first
    if not test_connection():
        print("\n❌ Connection test failed. Please fix the issues above before running.")
        print("\nMake sure you have:")
        print("1. Created a .env file with NOTION_TOKEN and NOTION_DATABASE_ID")
        print("2. Set up your Notion integration and database properly")
        return
    
    print("\n🚀 Starting Notion Task Sync...\n")
    
    try:
        sync = NotionTaskSync()
        sync.run()
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 