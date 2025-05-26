#!/usr/bin/env python3
"""
Test script to verify Notion connection and database setup
"""

import os
from dotenv import load_dotenv
from notion_client import Client

def test_connection():
    """Test Notion API connection and database access"""
    
    # Load environment variables
    load_dotenv()
    
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
        
        print("\n🎉 Everything looks good! You can now run the main script.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure your Notion integration token is correct")
        print("2. Verify the database ID is correct")
        print("3. Ensure the integration has access to the database")
        return False

if __name__ == "__main__":
    print("🧪 Testing Notion connection...\n")
    test_connection() 