// YouTube Downloader JavaScript

class YouTubeDownloader {
    constructor() {
        this.selectedFormat = null;
        this.currentVideoUrl = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // URL form submission
        document.getElementById('urlForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.fetchVideoInfo();
        });

        // Download button
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.downloadVideo();
        });
    }

    showError(message) {
        const errorAlert = document.getElementById('errorAlert');
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = message;
        errorAlert.classList.remove('d-none');
        
        // Hide video info if shown
        document.getElementById('videoInfo').classList.add('d-none');
    }

    hideError() {
        document.getElementById('errorAlert').classList.add('d-none');
    }

    validateYouTubeUrl(url) {
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=|embed\/|v\/|.+\?v=)?([^&=%\?]{11})/;
        return youtubeRegex.test(url);
    }

    async fetchVideoInfo() {
        const urlInput = document.getElementById('videoUrl');
        const fetchBtn = document.getElementById('fetchBtn');
        const fetchSpinner = document.getElementById('fetchSpinner');
        
        const url = urlInput.value.trim();
        
        if (!url) {
            this.showError('Please enter a YouTube URL');
            return;
        }

        if (!this.validateYouTubeUrl(url)) {
            this.showError('Please enter a valid YouTube URL');
            return;
        }

        // Show loading state
        fetchBtn.disabled = true;
        fetchSpinner.classList.remove('d-none');
        this.hideError();

        try {
            const formData = new FormData();
            formData.append('url', url);

            const response = await fetch('/get_video_info', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch video information');
            }

            this.currentVideoUrl = url;
            this.displayVideoInfo(data);

        } catch (error) {
            console.error('Error fetching video info:', error);
            this.showError(error.message || 'Failed to fetch video information');
        } finally {
            // Hide loading state
            fetchBtn.disabled = false;
            fetchSpinner.classList.add('d-none');
        }
    }

    displayVideoInfo(videoData) {
        // Update video information
        document.getElementById('videoTitle').textContent = videoData.title;
        document.getElementById('videoUploader').textContent = videoData.uploader;
        document.getElementById('videoThumbnail').src = videoData.thumbnail;
        document.getElementById('videoDuration').textContent = this.formatDuration(videoData.duration);
        document.getElementById('videoViews').textContent = this.formatNumber(videoData.view_count);

        // Create format options
        this.createFormatOptions(videoData.formats);

        // Show video info
        document.getElementById('videoInfo').classList.remove('d-none');
        
        // Scroll to video info
        document.getElementById('videoInfo').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }

    createFormatOptions(formats) {
        const container = document.getElementById('formatOptions');
        container.innerHTML = '';

        formats.forEach((format, index) => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            const isAudio = format.quality.includes('Audio');
            let icon, iconColor, badgeClass, fallbackSymbol;
            
            if (isAudio) {
                icon = 'fas fa-music';
                iconColor = 'success';
                badgeClass = 'bg-success';
                fallbackSymbol = '🎵';
            } else {
                // Different icons for different video qualities
                const quality = format.quality.toLowerCase();
                if (quality.includes('4k') || quality.includes('2160p')) {
                    icon = 'fas fa-star';
                    iconColor = 'warning';
                    badgeClass = 'bg-warning';
                    fallbackSymbol = '⭐';
                } else if (quality.includes('1080p') || quality.includes('fhd')) {
                    icon = 'fas fa-play-circle';
                    iconColor = 'info';
                    badgeClass = 'bg-info';
                    fallbackSymbol = '🎬';
                } else if (quality.includes('720p') || quality.includes('hd')) {
                    icon = 'fas fa-play';
                    iconColor = 'primary';
                    badgeClass = 'bg-primary';
                    fallbackSymbol = '▶️';
                } else if (quality.includes('480p') || quality.includes('sd')) {
                    icon = 'fas fa-circle';
                    iconColor = 'secondary';
                    badgeClass = 'bg-secondary';
                    fallbackSymbol = '⚪';
                } else if (quality.includes('360p') || quality.includes('lowest')) {
                    icon = 'fas fa-dot-circle';
                    iconColor = 'muted';
                    badgeClass = 'bg-dark';
                    fallbackSymbol = '🔵';
                } else {
                    icon = 'fas fa-file-video';
                    iconColor = 'primary';
                    badgeClass = 'bg-primary';
                    fallbackSymbol = '📹';
                }
            }

            col.innerHTML = `
                <div class="card format-option" data-format-id="${format.format_id}">
                    <div class="card-body text-center p-3">
                        <div class="format-icon-container mb-3">
                            <i class="${icon} format-icon text-${iconColor}" style="font-size: 2.5rem; display: block;">${fallbackSymbol}</i>
                        </div>
                        <div class="format-quality fw-bold mb-2">${format.quality}</div>
                        <div class="format-details">
                            <span class="badge ${badgeClass} mb-1">${format.ext.toUpperCase()}</span>
                            ${format.filesize ? `<br><small class="text-muted mt-1">${this.formatFileSize(format.filesize)}</small>` : ''}
                            ${format.fps ? `<br><small class="text-muted">${format.fps} FPS</small>` : ''}
                        </div>
                    </div>
                </div>
            `;

            container.appendChild(col);

            // Add click event listener
            const formatOption = col.querySelector('.format-option');
            formatOption.addEventListener('click', () => {
                this.selectFormat(format.format_id, formatOption);
            });
        });
    }

    selectFormat(formatId, element) {
        // Remove previous selection
        document.querySelectorAll('.format-option').forEach(option => {
            option.classList.remove('selected');
        });

        // Add selection to clicked element
        element.classList.add('selected');
        this.selectedFormat = formatId;

        // Enable download button
        document.getElementById('downloadBtn').disabled = false;
    }

    downloadVideo() {
        if (!this.selectedFormat || !this.currentVideoUrl) {
            this.showError('Please select a format and ensure video information is loaded');
            return;
        }

        const downloadBtn = document.getElementById('downloadBtn');
        const downloadSpinner = document.getElementById('downloadSpinner');

        // Show loading state
        downloadBtn.disabled = true;
        downloadSpinner.classList.remove('d-none');

        // Set form data and submit
        document.getElementById('downloadUrl').value = this.currentVideoUrl;
        document.getElementById('selectedFormat').value = this.selectedFormat;
        document.getElementById('downloadForm').submit();

        // Reset loading state after a delay (form submission will redirect)
        setTimeout(() => {
            downloadBtn.disabled = false;
            downloadSpinner.classList.add('d-none');
        }, 3000);
    }

    formatDuration(seconds) {
        if (!seconds) return 'Unknown';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    formatNumber(num) {
        if (!num) return '0';
        
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    formatFileSize(bytes) {
        if (!bytes) return 'Unknown size';
        
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// Initialize the downloader when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeDownloader();
});

// Handle URL input validation
document.getElementById('videoUrl').addEventListener('input', function() {
    const url = this.value.trim();
    const fetchBtn = document.getElementById('fetchBtn');
    
    if (url && url.length > 10) {
        fetchBtn.disabled = false;
    } else {
        fetchBtn.disabled = true;
    }
});
