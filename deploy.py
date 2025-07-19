#!/usr/bin/env python3
"""
Production deployment script for YouTube Downloader
Handles yt-dlp optimization and environment-specific configurations
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_ytdlp():
    """Update yt-dlp to the latest version"""
    try:
        logger.info("Updating yt-dlp to latest version...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], check=True)
        logger.info("yt-dlp updated successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to update yt-dlp: {e}")
        return False
    return True

def setup_production_env():
    """Setup production environment variables and configurations"""
    logger.info("Setting up production environment...")
    
    # Set production environment variables
    os.environ['FLASK_ENV'] = 'production'
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Optimize Python for production
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    
    # Set yt-dlp specific optimizations
    os.environ['YTDL_CACHE_DIR'] = '/tmp/ytdl-cache'
    
    logger.info("Production environment configured")

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = ['flask', 'yt-dlp', 'sqlalchemy', 'requests']
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✓ {package} is installed")
        except ImportError:
            logger.error(f"✗ {package} is not installed")
            return False
    return True

def main():
    """Main deployment function"""
    logger.info("Starting production deployment...")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Missing dependencies. Deployment failed.")
        sys.exit(1)
    
    # Update yt-dlp
    if not update_ytdlp():
        logger.warning("Failed to update yt-dlp, continuing with existing version...")
    
    # Setup production environment
    setup_production_env()
    
    # Import and run the Flask app
    logger.info("Starting Flask application...")
    
    try:
        from app import app
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        logger.info(f"Starting server on {host}:{port}")
        app.run(host=host, port=port, debug=False)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
