#!/bin/bash
# Push script for Customer Experience Data Pipeline
# This script pushes the project to GitHub

set -e

echo "🚀 Pushing Customer Experience Data Pipeline to GitHub..."
echo ""

# Check if remote exists
if ! git remote | grep -q origin; then
    echo "❌ No remote 'origin' found. Please configure first:"
    echo "   git remote add origin https://github.com/your-username/your-repo.git"
    exit 1
fi

echo "✅ Remote configured:"
git remote -v
echo ""

# Push to main branch
echo "📡 Pushing to origin/main..."
git push -u origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo "🌐 View your repository at: https://github.com/cesaraugustobr2014-oss/GCP_Airflow_project"
