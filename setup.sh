#!/bin/bash

# Notion Sync Setup Script
# Installs all dependencies needed for development

set -e  # Exit on any error

echo "🚀 Setting up Notion Sync development environment..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Don't run this script as root/sudo!"
   echo "Run it as your regular user: ./setup.sh"
   exit 1
fi

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Detected macOS"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "🍺 Installing Homebrew (this may ask for your password)..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for this session
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    else
        echo "✅ Homebrew already installed"
    fi
    
    # Install Task runner
    if ! command -v task &> /dev/null; then
        echo "📦 Installing Task runner..."
        brew install go-task
    else
        echo "✅ Task runner already installed"
    fi
    
    # Install Docker Desktop
    if ! command -v docker &> /dev/null; then
        echo "🐳 Installing Docker Desktop (this may take a few minutes)..."
        brew install --cask docker
        echo "✅ Docker Desktop installed"
        echo "📝 Please start Docker Desktop from Applications and wait for it to finish starting"
        echo "   Then run this script again to continue setup"
        exit 0
    else
        echo "✅ Docker is installed"
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux"
    
    # Install Task runner on Linux
    if ! command -v task &> /dev/null; then
        echo "📦 Installing Task runner..."
        
        # Create a local bin directory if it doesn't exist
        mkdir -p ~/.local/bin
        
        # Download and install Task
        curl -sL https://taskfile.dev/install.sh | sh -s -- -d ~/.local/bin
        
        # Add to PATH if not already there
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            export PATH="$HOME/.local/bin:$PATH"
        fi
    else
        echo "✅ Task runner already installed"
    fi
    
    # Install Docker on Linux
    if ! command -v docker &> /dev/null; then
        echo "🐳 Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        echo "✅ Docker installed"
        echo "📝 Please log out and log back in for Docker permissions to take effect"
        echo "   Then run this script again to continue setup"
        exit 0
    else
        echo "✅ Docker is installed"
    fi
    
else
    echo "❌ Unsupported operating system: $OSTYPE"
    echo "Please install Task and Docker manually:"
    echo "  Task: https://taskfile.dev/installation/"
    echo "  Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running!"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Please start Docker Desktop from Applications and wait for it to finish starting"
    else
        echo "Please start Docker service: sudo systemctl start docker"
    fi
    echo "Then run this script again to continue setup"
    exit 1
else
    echo "✅ Docker is running"
fi

# Set up environment file
if [ ! -f .env ]; then
    cp env.example .env
    echo "✅ Created .env file from template"
    echo "📝 Please edit .env with your Notion credentials:"
    echo "   NOTION_TOKEN=your_integration_token"
    echo "   NOTION_DATABASE_ID=your_database_id"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete! You can now use:"
echo "   task --list          # Show all available tasks"
echo "   task test            # Test Notion connection"
echo "   task build           # Build Docker image"
echo "   task run             # Run in development mode"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env with your Notion credentials"
echo "2. Run: task test"
echo "3. If test passes, run: task run" 