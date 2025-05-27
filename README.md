# Notion Task Alerts

A powerful notification system that bridges Notion's excellent task management with reliable Discord notifications. Get real-time alerts for tasks with smart timing and rich formatting - perfect for ADHD-friendly task management with explicit triggers and cognitive transition support.

## 🎯 What it does

- **Polls your Notion database** every 5 minutes for today's tasks
- **Checks for notifications** every 30 seconds for precise timing
- **Fires 4-tier alert system** with ADHD-optimized cognitive transitions:
  - 🧠 **Prepare Alert**: X minutes before start (customizable per task)
  - 🎯 **Start Alert**: At task start time
  - 🔄 **Soft Stop Alert**: X minutes before end (customizable per task) 
  - 🛑 **End Alert**: At task end time
- **Rich Discord notifications** with color coding, emojis, and clickable Notion links
- **Cross-platform delivery** - works on desktop and mobile Discord
- **Runs continuously** in Docker container, no babysitting required

## 🏗️ Setup

### 1. Install Task Runner

First, install [Task](https://taskfile.dev/installation/) for easy Docker management:

```bash
# macOS
brew install go-task

# Linux
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d

# Or download from https://taskfile.dev/installation/
```

### 2. Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"New integration"**
3. Give it a name like **"Task Alerts"**
4. Copy the **"Internal Integration Token"** - you'll need this for `.env`

### 3. Set up your Notion Database

Your database needs these specific properties:

#### Required Properties:
- **Name** (Title property) - Task title
- **Due** (Date property) - Must include **time**, not just date
- **Status** (Status property) - Must have "To Do" option

#### Custom Properties (Create these):
- **Prepare Mins** (Number property) - Minutes before start to send prepare alert
- **Soft Stop Mins** (Number property) - Minutes before end to send wind-down alert
- **Description** (Rich text property) - Optional task details

#### Example Database Structure:
```
| Name          | Due                     | Status | Prepare Mins | Soft Stop Mins | Description        |
|---------------|-------------------------|--------|--------------|----------------|--------------------|
| Morning Gym   | Dec 15, 2024 9:00 AM   | To Do  | 5            | 10             | Cardio + weights   |
| Code Review   | Dec 15, 2024 2:00 PM   | To Do  | 10           | 5              | Review PR #123     |
| Team Meeting  | Dec 15, 2024 3:00-4:00 | To Do  | 15           | 5              | Weekly standup     |
```

#### Important Notes:
- **Due property must have TIME** (e.g., "Dec 15, 2024 9:00 AM"), not just date
- **Date-only tasks are ignored** (no notifications sent)
- **Prepare Mins and Soft Stop Mins** should be pinned properties for easy access
- **Status must be "To Do"** for tasks to be processed

### 4. Share Database with Integration

1. Open your Notion database
2. Click the **"..."** menu in top right
3. Click **"Connections"** 
4. Select your integration to give it access

### 5. Get Database ID

1. Open your Notion database
2. Click **"..."** menu in top right
3. Click **"Copy link"**
4. From URL `https://notion.so/your-workspace/DATABASE_ID?v=...`
5. Copy the `DATABASE_ID` part (32-character string)

### 6. Set up Discord Webhook

#### Create Discord Server & Channel:
1. Create a personal Discord server (or use existing)
2. Create a dedicated channel like **#task-alerts** (or use #general)
3. Right-click the channel → **"Edit Channel"**
4. Go to **"Integrations"** → **"Webhooks"**
5. Click **"New Webhook"**
6. Copy the **Webhook URL** - you'll need this for `.env`

#### Configure Discord Notifications:

**On Desktop Discord:**
1. Go to **Settings** → **Notifications**
2. Set **"Push Notification Inactive Timeout"** to **"1 minute"** (lowest setting)
3. Right-click your notification channel → **"Notification Settings"**
4. Set to **"All Messages"** (ensures you get all task alerts)

**On Mobile Discord:**
1. Open Discord app → **Settings** → **Notifications**
2. Enable **"Push Notifications"**
3. Go to your notification channel
4. Tap channel name → **"Notification Settings"**
5. Set to **"All Messages"** (critical for mobile alerts)
6. Make sure **"Suppress @everyone and @here"** is **OFF**

### 7. Configure Environment

```bash
# Copy the example environment file
cp env.example .env
```

Edit `.env` file with your credentials:
```bash
# Notion Integration
NOTION_TOKEN=secret_your_integration_token_here
NOTION_DATABASE_ID=your_32_character_database_id_here

# Discord Webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url_here
```

**Security Note:** Never commit your `.env` file to version control. It contains sensitive tokens.

## 🚀 Usage

### Quick Start

```bash
# Initial setup (copies env file, installs task runner)
task setup

# Test Notion connection and database access
task test

# Build Docker image
task build

# Run in development mode (foreground with logs)
task dev

# Or run in production mode (background daemon)
task start
```

### Available Commands

```bash
# Development
task dev          # Run in foreground with live logs
task run          # Run container in foreground
task test         # Test Notion connection

# Production
task start        # Start in background (daemon mode)
task stop         # Stop the running container
task restart      # Restart the container
task status       # Show container status
task logs         # View container logs

# Maintenance
task build        # Build/rebuild Docker image
task clean        # Clean up Docker images and containers
task shell        # Open shell in running container
task help         # Show all available commands
```

### Development Workflow

```bash
# Start development mode
task dev

# Make code changes (files are mounted, changes reflect immediately)
# View logs in real-time
# Stop with Ctrl+C

# For production deployment
task stop    # Stop dev container
task start   # Start in background
task logs    # Monitor logs
```

## 🧠 How it Works

### Timing Strategy
1. **Every 5 minutes**: Fetches fresh tasks from Notion database
2. **Every 30 seconds**: Checks if any notifications are due
3. **Smart filtering**: Only processes tasks with datetime (ignores date-only)
4. **State preservation**: Remembers which alerts have been sent

### 4-Tier Alert System

#### 🧠 Prepare Alert (Orange)
- **When**: X minutes before start time (customizable per task)
- **Message**: "Start getting ready to shift gears"
- **Purpose**: ADHD cognitive transition preparation
- **Example**: 5 minutes before 2:00 PM meeting

#### 🎯 Start Alert (Green)  
- **When**: At exact start time
- **Message**: "Lock in and begin the task"
- **Purpose**: Clear action trigger
- **Example**: Exactly at 2:00 PM

#### 🔄 Soft Stop Alert (Yellow)
- **When**: X minutes before end time (customizable per task)
- **Message**: "Start winding down your CPUs"
- **Purpose**: Gradual task conclusion preparation
- **Example**: 5 minutes before 3:00 PM end time

#### 🛑 End Alert (Red)
- **When**: At exact end time
- **Message**: "Disengage now"
- **Purpose**: Hard stop signal
- **Example**: Exactly at 3:00 PM

### Rich Discord Notifications

Each notification includes:
- **Color-coded embeds** (Orange → Green → Yellow → Red)
- **Contextual emojis** (🧠🎯🔄🛑)
- **Task details** (name, timing, description)
- **Clickable Notion links** (direct access to task)
- **@here mentions** (ensures visibility across devices)
- **Cognitive context** (explains what transition is happening)

## 📱 Cross-Platform Delivery

### Desktop Notifications
- Appear immediately when Discord is active
- Rich formatting with clickable links
- Sound notifications (configurable in Discord)

### Mobile Notifications  
- Delivered after 1-minute desktop inactivity (Discord's limitation)
- Push notifications with full context
- Works on both iOS and Android Discord apps
- Includes direct links to Notion tasks

### Troubleshooting Mobile Notifications

If mobile notifications don't work:

1. **Check Discord Settings**:
   - Settings → Notifications → Push Notifications (ON)
   - Channel Settings → All Messages (not "Only @mentions")
   - Suppress @everyone/@here (OFF)

2. **Check Phone Settings**:
   - Allow Discord notifications in system settings
   - Disable Do Not Disturb for Discord
   - Enable sounds/badges/banners

3. **Test with Manual Message**:
   - Send `@here test` in your notification channel
   - Should appear on phone after 1 minute of desktop inactivity

## 🔧 Customization

### Per-Task Timing
- **Prepare Mins**: 0-60 minutes (how early to start mental preparation)
- **Soft Stop Mins**: 0-30 minutes (how early to begin wrapping up)
- **Leave empty**: Skip that alert type for the task

### Notification Preferences
- **Channel**: Use dedicated #task-alerts or existing #general
- **Timing**: Adjust Prepare/Soft Stop minutes per your workflow
- **Frequency**: System checks every 30 seconds (not configurable)

## 🎯 ADHD-Optimized Features

### Event-Driven Architecture
- **Explicit triggers** instead of self-initiated task switching
- **Clear timing specifications** (when/how long/what)
- **Cognitive transition support** (prepare → start → wind down → stop)

### Visual & Contextual Cues
- **Color progression** for visual cognitive mapping
- **Emoji consistency** for quick recognition  
- **Contextual messaging** explaining what each alert means
- **Direct action paths** (click to open task)

### Reliable Delivery
- **Cross-platform notifications** (desktop + mobile)
- **Redundant timing** (30-second check frequency)
- **State persistence** (won't spam duplicate alerts)
- **Error recovery** (continues running despite API issues)

## 🐛 Troubleshooting

### Common Issues

**No tasks found:**
- Check Due property has TIME, not just date
- Verify Status is set to "To Do"
- Confirm integration has database access

**No mobile notifications:**
- Set channel to "All Messages"
- Check Discord inactive timeout (1 minute minimum)
- Test with manual @here message

**Notifications not firing:**
- Check system time vs task times
- Verify Prepare/Soft Stop Mins are set
- Look at container logs: `task logs`

**Connection errors:**
- Verify NOTION_TOKEN and DATABASE_ID in .env
- Test connection: `task test`
- Check integration permissions

### Logs and Debugging

```bash
# View real-time logs
task logs

# Check container status  
task status

# Test Notion connection
task test

# Open container shell for debugging
task shell
```

## 🔒 Security

- **Environment variables**: Sensitive tokens stored in `.env` (not committed)
- **Docker isolation**: Application runs in containerized environment
- **Minimal permissions**: Notion integration only needs database access
- **Local execution**: No data sent to external services (except Discord webhooks)

## 🎉 Success Story

This system was built specifically for ADHD task management, addressing the need for:
- **Event-driven task switching** (explicit triggers vs self-initiation)
- **Cognitive transition support** (prepare → execute → wind down → stop)
- **Reliable notification delivery** (cross-platform, redundant timing)
- **Seamless workflow integration** (Notion planning → Discord alerts → direct task access)

Perfect for anyone who needs explicit, well-timed triggers to manage task transitions effectively!