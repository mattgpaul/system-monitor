#!/bin/bash
# Development startup script

set -e  # Exit on any error

echo "🚀 Starting development environment..."

# Set environment
export ENV=dev

# Check if dev.env exists
if [ ! -f "dev.env" ]; then
    echo "❌ Error: dev.env file not found!"
    echo "Please create dev.env with your configuration"
    exit 1
fi

echo "📁 Using environment file: dev.env"

# Source environment variables
source dev.env

# Function to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up..."
    if [ ! -z "$AGENT_PID" ]; then
        kill $AGENT_PID 2>/dev/null
    fi
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null
    fi
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Start agent in background
echo "🤖 Starting agent on $AGENT_HOST:$AGENT_PORT..."
ENV=dev python app/agent/main.py --server &
AGENT_PID=$!

# Give agent time to start
sleep 3

# Start Django server in background
echo "🌐 Starting Django server on $SERVER_HOST:$SERVER_PORT..."
ENV=dev python app/server/manage.py runserver $SERVER_HOST:$SERVER_PORT &
SERVER_PID=$!

# Give server time to start
sleep 2

echo "✅ Development environment running!"
echo "📊 Agent GraphQL: http://$AGENT_HOST:$AGENT_PORT/graphql"
echo "🔧 Django Server: http://$SERVER_HOST:$SERVER_PORT/api/v1/health/"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for user interrupt
wait
