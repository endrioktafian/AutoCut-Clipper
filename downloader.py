#!/usr/bin/env python3
"""
📥 AUTOCUT TERMUX - Video Downloader
Download video dari YouTube/TikTok/Instagram menggunakan yt-dlp
"""

import yt_dlp
import os
import re
from pathlib import Path
from typing import Optional, Dict

class VideoDownloader:
    """
    Universal video downloader dengan yt-dlp
    Support: YouTube, TikTok, Instagram, Twitter, Facebook
    """
    
    def __init__(self, output_dir: str = "./temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cookie file untuk bypass age-restricted content
        self.cookie_file = self.output_dir.parent / "cookies.txt"
        
    def _get_ydl_opts(self, output_template: str) -> Dict:
        """
        Get yt-dlp options
        """
        opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'retries': 3,
            'fragment_retries': 3,
            'http_chunk_size': 10485760,  # 10MB
        }
        
        # Use cookies if available
        if self.cookie_file.exists():
            opts['cookiefile'] = str(self.cookie_file)
        
        return opts
    
    def download(self, url: str, output_name: Optional[str] = None) -> str:
        """
        Download video dari URL
        Returns: path ke file video
        """
        # Sanitize output name
        if output_name:
            output_name = re.sub(r'[^\w\-_]', '_', output_name)[:50]
            output_template = str(self.output_dir / f"{output_name}.%(ext)s")
        else:
            output_template = str(self.output_dir / "%(title)s.%(ext)s")
        
        opts = self._get_ydl_opts(output_template)
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Get filename
                filename = ydl.prepare_filename(info)
                
                # Handle merge output (video+audio)
                if filename.endswith('.webm'):
                    filename = filename.replace('.webm', '.mp4')
                elif filename.endswith('.mkv'):
                    filename = filename.replace('.mkv', '.mp4')
                
                # Check if file exists
                if not os.path.exists(filename):
                    # Try alternative extensions
                    for ext in ['.mp4', '.webm', '.mkv', '.avi']:
                        alt_filename = filename.rsplit('.', 1)[0] + ext
                        if os.path.exists(alt_filename):
                            filename = alt_filename
                            break
                
                return filename
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            
            # Handle specific errors
            if "Sign in" in error_msg or "confirm your age" in error_msg:
                raise Exception("Video requires login. Add cookies.txt file.")
            elif "Private video" in error_msg:
                raise Exception("Video is private.")
            elif "unavailable" in error_msg:
                raise Exception("Video is unavailable or deleted.")
            else:
                raise Exception(f"Download error: {error_msg}")
    
    def download_with_progress(self, url: str, output_name: Optional[str] = None, 
                               progress_callback=None) -> str:
        """
        Download dengan progress callback
        """
        
        def progress_hook(d):
            if progress_callback:
                if d['status'] == 'downloading':
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                    if total > 0:
                        percent = (downloaded / total) * 100
                        progress_callback(percent, downloaded, total)
                elif d['status'] == 'finished':
                    progress_callback(100, 0, 0)
        
        if output_name:
            output_name = re.sub(r'[^\w\-_]', '_', output_name)[:50]
            output_template = str(self.output_dir / f"{output_name}.%(ext)s")
        else:
            output_template = str(self.output_dir / "%(title)s.%(ext)s")
        
        opts = self._get_ydl_opts(output_template)
        opts['progress_hooks'] = [progress_hook]
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if filename.endswith('.webm'):
                filename = filename.replace('.webm', '.mp4')
            
            return filename
    
    def get_video_info(self, url: str) -> Dict:
        """
        Get video info tanpa download
        """
        opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return {
                'id': info.get('id', ''),
                'title': info.get('title', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'uploader': info.get('uploader', ''),
                'thumbnail': info.get('thumbnail', ''),
                'description': info.get('description', '')[:500] if info.get('description') else '',
            }
    
    def get_duration(self, url: str) -> int:
        """
        Get video duration in seconds
        """
        info = self.get_video_info(url)
        return info.get('duration', 0)
    
    def extract_audio(self, video_path: str, output_name: Optional[str] = None) -> str:
        """
        Extract audio dari video ke MP3
        """
        import subprocess
        
        video_path = Path(video_path)
        
        if output_name:
            output_path = self.output_dir / f"{output_name}.mp3"
        else:
            output_path = self.output_dir / f"{video_path.stem}.mp3"
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-vn',
            '-acodec', 'libmp3lame',
            '-ab', '192k',
            str(output_path)
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        return str(output_path)
    
    def cleanup(self, keep_last: int = 5):
        """
        Cleanup temp files, keep only last N files
        """
        files = sorted(
            self.output_dir.glob('*.*'),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        for f in files[keep_last:]:
            try:
                f.unlink()
            except Exception as e:
                print(f"⚠️  Failed to delete {f}: {e}")


# Test module
if __name__ == "__main__":
    downloader = VideoDownloader()
    
    # Test get video info
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        print(f"📊 Getting info for: {test_url}")
        info = downloader.get_video_info(test_url)
        print(f"  Title: {info['title']}")
        print(f"  Duration: {info['duration']}s")
        print(f"  Views: {info['view_count']}")
        
        # Test download (commented out - uncomment to test)
        # print("\n📥 Downloading...")
        # path = downloader.download(test_url, "test_video")
        # print(f"✅ Downloaded: {path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")