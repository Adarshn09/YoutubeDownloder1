import os
import logging
import json
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import yt_dlp
from urllib.parse import urlparse, parse_qs
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///youtube_downloader.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

def is_valid_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return youtube_regex.match(url) is not None

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    match = youtube_regex.match(url)
    if match:
        return match.group(6)
    return None

def get_yt_dlp_config(for_download=False):
    """Get optimized yt-dlp configuration to avoid bot detection"""
    config = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extractor_args': {
            'youtube': {
                'skip': ['dash'],
                'player_skip': ['js'],
                'innertube_host': ['www.youtube.com', 'youtubei.googleapis.com']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        'sleep_interval': 1,
        'max_sleep_interval': 5,
    }
    
    if not for_download:
        config['extract_flat'] = False
        config['format'] = 'best'
    else:
        config['format'] = 'best[ext=mp4]/best'
        
    return config

# Initialize database
with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    """Get video information from YouTube URL"""
    try:
        url = request.form.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'Please enter a YouTube URL'}), 400
        
        if not is_valid_youtube_url(url):
            return jsonify({'error': 'Please enter a valid YouTube URL'}), 400
        
        # Use simple, reliable yt-dlp configuration
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'format': 'best',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video information
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as extract_error:
                app.logger.error(f"Info extraction failed: {str(extract_error)}")
                return jsonify({'error': 'Could not extract video information. The video may be private, unavailable, or restricted.'}), 400
            
            # Check if we got valid info
            if not info or not isinstance(info, dict):
                return jsonify({'error': 'Could not extract video information. Please check the URL and try again.'}), 400
            
            # Save video info to database
            video_id = extract_video_id(url)
            if not video_id:
                return jsonify({'error': 'Invalid YouTube URL format.'}), 400
                
            video = db.session.query(models.Video).filter_by(video_id=video_id).first()
            
            try:
                if not video:
                    video = models.Video(
                        video_id=video_id,
                        title=info.get('title', 'Unknown Title'),
                        uploader=info.get('uploader', 'Unknown'),
                        duration=info.get('duration', 0),
                        view_count=info.get('view_count', 0),
                        thumbnail_url=info.get('thumbnail', ''),
                        description=info.get('description', ''),
                        upload_date=datetime.fromtimestamp(info.get('timestamp', 0)) if info.get('timestamp') else None
                    )
                    db.session.add(video)
                else:
                    # Update existing video info
                    video.title = info.get('title', video.title)
                    video.uploader = info.get('uploader', video.uploader)
                    video.view_count = info.get('view_count', video.view_count)
                    video.thumbnail_url = info.get('thumbnail', video.thumbnail_url)
                    video.updated_at = datetime.utcnow()
                
                db.session.commit()
            except Exception as db_error:
                app.logger.error(f"Database error: {str(db_error)}")
                db.session.rollback()
                # Continue without database save
            
            # Get available formats with fallback
            formats = []
            seen_qualities = set()
            
            if 'formats' in info and info['formats']:
                for fmt in info['formats']:
                    if fmt.get('vcodec') != 'none' and fmt.get('height'):
                        quality = f"{fmt['height']}p"
                        if quality not in seen_qualities:
                            formats.append({
                                'format_id': fmt['format_id'],
                                'quality': quality,
                                'ext': fmt.get('ext', 'mp4'),
                                'filesize': fmt.get('filesize'),
                                'fps': fmt.get('fps')
                            })
                            seen_qualities.add(quality)
            
            # If no formats found, add common fallback options
            if not formats:
                fallback_formats = [
                    {'format_id': 'best', 'quality': 'Best Available', 'ext': 'mp4', 'filesize': None, 'fps': None},
                    {'format_id': 'worst', 'quality': 'Lowest Quality', 'ext': 'mp4', 'filesize': None, 'fps': None}
                ]
                formats.extend(fallback_formats)
            else:
                # Sort formats by quality (descending)
                formats.sort(key=lambda x: int(x['quality'].replace('p', '')), reverse=True)
            
            # Add audio-only option
            formats.append({
                'format_id': 'bestaudio',
                'quality': 'Audio Only (MP3)',
                'ext': 'mp3',
                'filesize': None,
                'fps': None
            })
            
            video_info = {
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'formats': formats[:10]  # Limit to top 10 formats
            }
            
            return jsonify(video_info)
            
    except yt_dlp.DownloadError as e:
        error_msg = str(e)
        app.logger.error(f"yt-dlp error: {error_msg}")
        
        if 'Sign in to confirm you\'re not a bot' in error_msg:
            return jsonify({'error': 'YouTube is requesting verification. Please try again later or use a different video.'}), 429
        elif 'Video unavailable' in error_msg:
            return jsonify({'error': 'This video is not available for download.'}), 404
        elif 'DRM protected' in error_msg:
            return jsonify({'error': 'This video is DRM protected and cannot be downloaded.'}), 403
        elif 'Requested format is not available' in error_msg:
            return jsonify({'error': 'Video formats are not available. This might be a private or restricted video.'}), 404
        elif 'Private video' in error_msg:
            return jsonify({'error': 'This is a private video and cannot be downloaded.'}), 403
        else:
            return jsonify({'error': 'Failed to fetch video information. Please check the URL and try again.'}), 400
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

@app.route('/download', methods=['POST'])
def download_video():
    """Download video with specified quality"""
    try:
        url = request.form.get('url', '').strip()
        format_id = request.form.get('format_id', 'best')
        
        if not url or not is_valid_youtube_url(url):
            flash('Invalid YouTube URL', 'error')
            return redirect(url_for('index'))
        
        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp()
        
        # Use simple, reliable yt-dlp configuration for download
        if format_id == 'bestaudio':
            ydl_opts = {
                'quiet': True,
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            # Simplified format selection - just use best available
            ydl_opts = {
                'quiet': True,
                'format': 'best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            video_id = extract_video_id(url)
            
            # Create download record
            download_record = models.Download(
                video_id=video_id,
                format_id=format_id,
                quality=format_id if format_id == 'bestaudio' else f"{format_id}p",
                file_extension='mp3' if format_id == 'bestaudio' else 'mp4',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                success=False
            )
            db.session.add(download_record)
            
            try:
                # Download the video
                ydl.download([url])
                
                # Find the downloaded file
                downloaded_files = os.listdir(temp_dir)
                if not downloaded_files:
                    download_record.error_message = 'No file was created'
                    db.session.commit()
                    flash('Download failed. No file was created.', 'error')
                    return redirect(url_for('index'))
                
                file_path = os.path.join(temp_dir, downloaded_files[0])
                file_size = os.path.getsize(file_path)
                
                # Update download record
                download_record.success = True
                download_record.file_size = file_size
                
                # Update popularity tracking
                popularity = db.session.query(models.PopularVideo).filter_by(video_id=video_id).first()
                if popularity:
                    popularity.download_count += 1
                    popularity.last_downloaded = datetime.utcnow()
                else:
                    popularity = models.PopularVideo(video_id=video_id, download_count=1)
                    db.session.add(popularity)
                
                db.session.commit()
                
                # Send file to user
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=downloaded_files[0]
                )
                
            except Exception as e:
                download_record.error_message = str(e)
                db.session.commit()
                raise
            
    except yt_dlp.DownloadError as e:
        error_msg = str(e)
        app.logger.error(f"Download error: {error_msg}")
        
        if 'Sign in to confirm you\'re not a bot' in error_msg:
            flash('YouTube is requesting verification. Please try again later or use a different video.', 'error')
        elif 'Video unavailable' in error_msg:
            flash('This video is not available for download.', 'error')
        elif 'DRM protected' in error_msg:
            flash('This video is DRM protected and cannot be downloaded.', 'error')
        elif 'Requested format is not available' in error_msg:
            flash('Video format is not available. Please try a different quality option.', 'error')
        elif 'Private video' in error_msg:
            flash('This is a private video and cannot be downloaded.', 'error')
        else:
            flash('Download failed. Please try again with a different quality option.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Unexpected download error: {str(e)}")
        flash('An unexpected error occurred during download.', 'error')
        return redirect(url_for('index'))

@app.route('/stats')
def stats():
    """Display download statistics"""
    total_downloads = db.session.query(models.Download).count()
    successful_downloads = db.session.query(models.Download).filter_by(success=True).count()
    total_videos = db.session.query(models.Video).count()
    
    # Get popular videos
    popular_videos = db.session.query(models.PopularVideo, models.Video).join(
        models.Video, models.PopularVideo.video_id == models.Video.video_id
    ).order_by(models.PopularVideo.download_count.desc()).limit(10).all()
    
    # Get recent downloads
    recent_downloads = db.session.query(models.Download, models.Video).join(
        models.Video, models.Download.video_id == models.Video.video_id
    ).filter(models.Download.success == True).order_by(
        models.Download.download_time.desc()
    ).limit(10).all()
    
    stats_data = {
        'total_downloads': total_downloads,
        'successful_downloads': successful_downloads,
        'total_videos': total_videos,
        'success_rate': round((successful_downloads / total_downloads * 100) if total_downloads > 0 else 0, 2),
        'popular_videos': popular_videos,
        'recent_downloads': recent_downloads
    }
    
    return render_template('stats.html', stats=stats_data)

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    total_downloads = db.session.query(models.Download).count()
    successful_downloads = db.session.query(models.Download).filter_by(success=True).count()
    total_videos = db.session.query(models.Video).count()
    
    return jsonify({
        'total_downloads': total_downloads,
        'successful_downloads': successful_downloads,
        'total_videos': total_videos,
        'success_rate': round((successful_downloads / total_downloads * 100) if total_downloads > 0 else 0, 2)
    })

@app.route('/test')
def test_video():
    """Test endpoint with a working video URL"""
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - usually works
    return render_template('test.html', test_url=test_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
