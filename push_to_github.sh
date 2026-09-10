#!/bin/bash

# GitHub Push Script for YouTube Transcript Extractor
# This script automates the process of pushing your code to GitHub

set -e  # Exit on error

echo "🚀 GitHub Push Script"
echo "===================="
echo ""

# Configuration
REPO_NAME="video-transcript-extractor"
REPO_DESCRIPTION="AI-powered web app for extracting and summarizing video transcripts using Whisper and Ollama"

# Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI detected"
    echo ""
    echo "Creating repository and pushing code..."
    echo ""
    
    # Create repo and push in one command
    gh repo create "$REPO_NAME" \
        --public \
        --description "$REPO_DESCRIPTION" \
        --source=. \
        --remote=origin \
        --push
    
    echo ""
    echo "✅ Repository created and code pushed successfully!"
    echo ""
    echo "🌐 Your repository is now live at:"
    gh repo view --web
    
else
    echo "❌ GitHub CLI not found"
    echo ""
    echo "Please choose an option:"
    echo ""
    echo "Option 1: Install GitHub CLI (Recommended)"
    echo "  brew install gh"
    echo "  gh auth login"
    echo "  Then run this script again"
    echo ""
    echo "Option 2: Manual Push"
    echo "  1. Create a new repository at: https://github.com/new"
    echo "     - Name: $REPO_NAME"
    echo "     - Description: $REPO_DESCRIPTION"
    echo "     - DO NOT initialize with README"
    echo ""
    echo "  2. Then run these commands:"
    echo "     git remote add origin https://github.com/YOUR_USERNAME/$REPO_NAME.git"
    echo "     git branch -M main"
    echo "     git push -u origin main"
    echo ""
    exit 1
fi
