from app import db
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Boolean, Float


class Video(db.Model):
    """Model to store video information"""
    id = db.Column(Integer, primary_key=True)
    video_id = db.Column(String(20), unique=True, nullable=False, index=True)
    title = db.Column(String(500), nullable=False)
    uploader = db.Column(String(200))
    duration = db.Column(Integer)  # in seconds
    view_count = db.Column(Integer)
    thumbnail_url = db.Column(Text)
    description = db.Column(Text)
    upload_date = db.Column(DateTime)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    downloads = db.relationship('Download', backref='video', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Video {self.video_id}: {self.title[:50]}>'


class Download(db.Model):
    """Model to track download history"""
    id = db.Column(Integer, primary_key=True)
    video_id = db.Column(String(20), db.ForeignKey('video.video_id'), nullable=False)
    format_id = db.Column(String(50), nullable=False)
    quality = db.Column(String(50))
    file_extension = db.Column(String(10))
    file_size = db.Column(Integer)  # in bytes
    ip_address = db.Column(String(45))  # IPv6 compatible
    user_agent = db.Column(Text)
    success = db.Column(Boolean, default=False)
    error_message = db.Column(Text)
    download_time = db.Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Download {self.video_id} - {self.quality}>'


class PopularVideo(db.Model):
    """Model to track popular videos based on download count"""
    id = db.Column(Integer, primary_key=True)
    video_id = db.Column(String(20), db.ForeignKey('video.video_id'), nullable=False, unique=True)
    download_count = db.Column(Integer, default=0)
    last_downloaded = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    video_info = db.relationship('Video', backref='popularity', uselist=False)
    
    def __repr__(self):
        return f'<PopularVideo {self.video_id}: {self.download_count} downloads>'


class AppSettings(db.Model):
    """Model to store application settings"""
    id = db.Column(Integer, primary_key=True)
    key = db.Column(String(100), unique=True, nullable=False)
    value = db.Column(Text)
    description = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AppSettings {self.key}: {self.value}>'