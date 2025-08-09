#!/bin/bash
# Development environment setup script

set -e  # Exit on any error

echo "Setting up development environment..."

# Set environment
export ENV=dev

# Check if dev.env exists
if [ ! -f "dev.env" ]; then
    echo "Error: dev.env file not found!"
    echo "Please create dev.env with your configuration"
    exit 1
fi

echo "Using environment file: dev.env"

# Source environment variables
source dev.env

# Verify environment variables are loaded
echo "Environment configuration:"
echo "  Agent Host: $AGENT_HOST"
echo "  Agent Port: $AGENT_PORT"
echo "  Server Host: $SERVER_HOST"
echo "  Server Port: $SERVER_PORT"
echo "  Agent Base URL: $AGENT_BASE_URL"

echo ""
echo "Development environment ready!"
echo ""
echo "To start services:"
echo "  Agent:  make dev-agent"
echo "  Server: make dev-server"
echo "  Both:   make dev (after dependencies)"
echo ""
echo "Available endpoints when running:"
echo "  Agent GraphQL: http://$AGENT_HOST:$AGENT_PORT/graphql"
echo "  Django Server: http://$SERVER_HOST:$SERVER_PORT/api/v1/health/"
