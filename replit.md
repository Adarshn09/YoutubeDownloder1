# YouTube Downloader

## Overview

This is a Flask-based YouTube video downloader application that allows users to input YouTube URLs and download videos in various qualities. The application uses yt-dlp for video processing and provides a web interface for user interaction.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a simple client-server architecture:
- **Frontend**: HTML templates with Bootstrap for styling, JavaScript for dynamic interactions
- **Backend**: Flask web framework with Python
- **Video Processing**: yt-dlp library for YouTube video extraction and download
- **File Serving**: Temporary file handling for download delivery

## Key Components

### Backend (Flask Application)
- **Main Application** (`app.py`): Core Flask application with URL validation, video info extraction, and download endpoints
- **Entry Point** (`main.py`): Application runner for development server
- **URL Validation**: Regex-based YouTube URL validation and video ID extraction
- **Video Processing**: Integration with yt-dlp for fetching video metadata and download options

### Frontend
- **Templates** (`templates/index.html`): Main user interface with Bootstrap dark theme
- **Static Assets**: 
  - CSS styling (`static/css/style.css`) for custom appearance
  - JavaScript (`static/js/main.js`) for client-side interactions and AJAX requests
- **UI Components**: Form for URL input, video information display, format selection, and download functionality

### Core Features
- YouTube URL validation using regex patterns
- Video information extraction (title, thumbnail, available formats)
- Format selection interface
- File download with temporary file handling
- Error handling and user feedback via Flash messages

## Data Flow

1. User enters YouTube URL in the web interface
2. Client-side JavaScript validates URL format
3. AJAX request sent to `/get_video_info` endpoint
4. Backend validates URL and extracts video ID
5. yt-dlp processes the URL to fetch video metadata
6. Available formats are returned to the frontend
7. User selects desired format and quality
8. Download request triggers video processing and file serving
9. Temporary files are created and served to the user

## External Dependencies

### Python Libraries
- **Flask**: Web framework for HTTP handling and templating
- **yt-dlp**: YouTube video downloading and metadata extraction
- **Werkzeug**: WSGI utilities including ProxyFix for deployment

### Frontend Libraries
- **Bootstrap**: UI framework (loaded from CDN)
- **Font Awesome**: Icon library for UI elements
- **Custom CSS/JS**: Application-specific styling and functionality

### Infrastructure
- **Temporary File System**: For storing downloaded videos before serving
- **Environment Variables**: Session secret configuration

## Deployment Strategy

The application is configured for development with:
- Debug mode enabled
- Host binding to `0.0.0.0:5000`
- ProxyFix middleware for reverse proxy compatibility
- Environment-based configuration for session secrets

**Key Architecture Decisions:**

1. **yt-dlp Choice**: Selected over youtube-dl for better maintenance and feature support
2. **Temporary File Strategy**: Downloads stored temporarily to avoid persistent storage requirements
3. **Client-Side Validation**: Reduces server load by validating URLs before submission
4. **Flash Message System**: Provides user feedback without complex state management
5. **Bootstrap Integration**: Ensures responsive design with minimal custom CSS

The application is designed to be lightweight and stateless, making it suitable for containerized deployment or simple hosting environments.

## Recent Changes: Latest modifications with dates

### July 14, 2025 - Migration and Authentication Improvements
- **Migration Complete**: Successfully migrated from Replit Agent to Replit environment
- **Security Enhancement**: Removed hardcoded cookie file references for better security
- **Bot Detection Prevention**: Added comprehensive YouTube bot detection prevention:
  - Updated User-Agent strings to latest Chrome version
  - Added HTTP headers to mimic real browser behavior
  - Implemented sleep intervals to avoid rate limiting
  - Added specialized YouTube extractor arguments
  - Enhanced error handling for authentication challenges
- **Error Handling**: Improved error messages for YouTube authentication issues
- **Configuration**: Created centralized `get_yt_dlp_config()` function for consistent settings

### July 14, 2025 - Database Integration
- **Database Setup**: Added SQLite database with Flask-SQLAlchemy
- **Data Models**: Created comprehensive models for videos, downloads, popularity tracking, and app settings
- **Video Tracking**: Automatically saves video metadata when users fetch video information
- **Download Analytics**: Tracks all download attempts with success/failure status, file sizes, and user data
- **Statistics Page**: Added `/stats` route with visual analytics and popular video tracking
- **API Endpoints**: Added `/api/stats` for programmatic access to download statistics
- **Navigation**: Enhanced navigation with statistics page link

### July 14, 2025 - Error Handling and Stability Improvements
- **Enhanced Error Handling**: Added comprehensive error detection for DRM-protected videos, private videos, and format availability issues
- **Fallback Formats**: Added fallback video quality options when specific formats are unavailable
- **Input Validation**: Improved URL validation and video ID extraction with better error messages
- **Database Resilience**: Added rollback mechanisms for database operations to prevent crashes
- **User Experience**: Added informative messages about video restrictions and availability
- **Format Selection**: Improved download format selection with better fallback logic