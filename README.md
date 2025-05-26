# Notion Task Sync

An ADHD-friendly task notification system that bridges Notion's excellent task management with reliable desktop notifications.

## What it does

- **Polls your Notion database** for today's tasks
- **Fires desktop notifications** at the right times:
  - **Soft Stop**: 15 minutes before task end time (start wrapping up)
  - **Hard Stop**: At task end time (time to disengage)
- **Links back to Notion** - click notification to open the specific task page
- **Runs continuously** in the background, no babysitting required

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Give it a name like "Task Sync"
4. Copy the "Internal Integration Token" - you'll need this

### 3. Set up your Notion Database

Your database needs these properties:
- **Name/Title** (title property)
- **Start Time** (date property with time)
- **End Time** (can be part of the date range in Start Time property)
- **Description/Notes** (rich text property) - optional

Example database structure:
```
| Name          | Start Time           | Description        |
|---------------|---------------------|--------------------|
| Morning Gym   | Dec 15, 9:00-10:30  | Cardio + weights   |
| Code Review   | Dec 15, 14:00-15:00 | Review PR #123     |
```

### 4. Share Database with Integration

1. Open your Notion database
2. Click the "..." menu in very top right
3. Click "Connections"
4. Select your integration

### 5. Get Database ID
1. Open your Notion database
2. Click the "..." menu in very top right
3. Click "Copy link"
4. From your database URL: `https://notion.so/your-workspace/DATABASE_ID?v=...`
5. Copy the `DATABASE_ID` part (32 character string)

### 6. Configure Environment

```bash
cp env.example .env
```

Edit `.env` file:
```
NOTION_TOKEN=your_integration_token_here
NOTION_DATABASE_ID=your_database_id_here
```

## Usage

### Option 1: Docker (Recommended)

First, install [Task](https://taskfile.dev/installation/) if you don't have it:

```bash
# macOS
brew install go-task

# Or download from https://taskfile.dev/installation/
```

Then use the Taskfile commands:

```bash
# Initial setup
task setup

# Test connection
task test

# Run in foreground (development)
task run

# Run in background (production)
task start

# View logs
task logs

# Stop the service
task stop

# See all available commands
task help
```

### Option 2: Direct Python

```bash
python notion_sync.py
```

The system will:
- Start monitoring your database
- Log activity to console
- Send desktop notifications when tasks are ending
- Run until you stop it (Ctrl+C)

### Run in background (macOS/Linux):

```bash
nohup python notion_sync.py > sync.log 2>&1 &
```

## How it works

1. **Every 5 minutes**: Fetches today's tasks from your Notion database
2. **Every 30 seconds**: Checks if any tasks need notifications
3. **15 min before end**: Sends "Soft Stop" notification to start wrapping up
4. **At end time**: Sends "Hard Stop" notification to disengage

## Notification Examples

**Soft Stop (15 min warning):**
```
🔔 Soft Stop - 15 min warning
Start wrapping up: Morning Gym
Ends at 10:30

Click to open in Notion: https://notion.so/...
```

**Hard Stop (time's up):**
```
🔔 Hard Stop - Time's up!
Stop now: Morning Gym
Time to disengage and move on.

Click to open in Notion: https://notion.so/...
```

## Troubleshooting

### No notifications appearing?
- Check that your integration has access to the database
- Verify your `.env` file has correct tokens
- Make sure tasks have both start and end times

### Wrong property names?
The system looks for these property names (case-insensitive):
- Title: "Name" or "Title"
- Time: "Start Time" or "Date"
- Description: "Description" or "Notes"

### Tasks not showing up?
- Only shows tasks for today
- Tasks must have a start time
- Check the console logs for errors

## Future Enhancements

- [ ] Mobile notifications (push notifications)
- [ ] Start time notifications (not just end time)
- [ ] Configurable warning times (not just 15 min)
- [ ] Support for recurring tasks
- [ ] Better error handling and retry logic
- [ ] GUI for easier setup 