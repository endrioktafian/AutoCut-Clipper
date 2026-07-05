#!/usr/bin/env python3
"""
✂️ AUTOCUT TERMUX - Video Cutter
Cut video dengan FFmpeg, support batch processing dan preset
"""

import subprocess
import shlex
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass

@dataclass
class CutSegment:
    start: str
    end: str
    title: str
    hook: Optional[str] = None
    caption: Optional[str] = None

class VideoCutter:
    """
    FFmpeg-based video cutter
    Support: single cut, batch cut, preset application
    """
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # FFmpeg path check
        self.ffmpeg_path = self._find_ffmpeg()
        
    def _find_ffmpeg(self) -> str:
        """Find ffmpeg binary"""
        import shutil
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            raise RuntimeError("FFmpeg not found! Install with: pkg install ffmpeg")
        return ffmpeg
    
    def time_to_seconds(self, time_str: str) -> float:
        """
        Convert time string to seconds
        Support: HH:MM:SS, MM:SS, SS
        """
        time_str = time_str.strip()
        parts = time_str.split(':')
        
        try:
            if len(parts) == 1:
                return float(parts[0])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError:
            pass
        
        return 0.0
    
    def sanitize_filename(self, name: str, max_length: int = 50) -> str:
        """
        Sanitize filename untuk filesystem
        """
        import re
        # Remove invalid chars
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace spaces with underscore
        name = re.sub(r'\s+', '_', name)
        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)
        # Trim length
        if len(name) > max_length:
            name = name[:max_length]
        # Remove trailing underscore
        name = name.strip('_')
        return name
    
    def cut(self, 
            input_path: str, 
            start: str, 
            end: str, 
            output_name: str,
            preset: Optional[Dict] = None,
            fast_cut: bool = True) -> str:
        """
        Cut video segment
        
        Args:
            input_path: Path ke video source
            start: Start time (HH:MM:SS atau MM:SS)
            end: End time (HH:MM:SS atau MM:SS)
            output_name: Nama output file (tanpa ekstensi)
            preset: Preset config (zoom, caption, fps, etc.)
            fast_cut: If True, use -c copy (fast but less precise)
        
        Returns:
            Path ke output file
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")
        
        # Generate output filename
        safe_name = self.sanitize_filename(output_name)
        output_path = self.output_dir / f"{safe_name}.mp4"
        
        # Build FFmpeg command
        if fast_cut:
            # Fast cut dengan -c copy (no re-encode)
            cmd = [
                self.ffmpeg_path, '-y',
                '-i', str(input_path),
                '-ss', start,
                '-to', end,
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                str(output_path)
            ]
        else:
            # Re-encode untuk precise cut
            cmd = [
                self.ffmpeg_path, '-y',
                '-i', str(input_path),
                '-ss', start,
                '-to', end,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'fast',
                '-crf', '23',
                '-avoid_negative_ts', 'make_zero',
                str(output_path)
            ]
        
        # Apply preset jika ada
        if preset:
            cmd = self._apply_preset_to_cmd(cmd, preset)
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr[:200]}")
            
            if not output_path.exists():
                raise Exception("Output file not created")
            
            return str(output_path)
            
        except subprocess.TimeoutExpired:
            raise Exception("Cut timeout (exceeded 5 minutes)")
        except Exception as e:
            raise Exception(f"Cut failed: {str(e)}")
    
    def _apply_preset_to_cmd(self, cmd: List, preset: Dict) -> List:
        """
        Apply preset effects to FFmpeg command
        """
        # Insert filter before output
        filters = []
        
        # Zoom effect
        if preset.get('zoom'):
            zoom_factor = preset.get('zoom_factor', 1.1)
            filters.append(f'scale=iw*{zoom_factor}:ih*{zoom_factor},crop=iw:ih')
        
        # FPS change
        if preset.get('fps'):
            filters.append(f'fps={preset["fps"]}')
        
        # Brightness/contrast
        if preset.get('brightness'):
            filters.append(f'eq=brightness={preset["brightness"]}')
        
        if preset.get('contrast'):
            filters.append(f'eq=contrast={preset["contrast"]}')
        
        # Add filters to command
        if filters:
            filter_complex = ','.join(filters)
            # Insert -vf before output
            output_idx = cmd.index(str(self.output_dir / "*.mp4")) if str(self.output_dir) in cmd else -1
            if output_idx == -1:
                output_idx = len(cmd) - 1
            cmd.insert(output_idx, '-vf')
            cmd.insert(output_idx + 1, filter_complex)
        
        return cmd
    
    def cut_batch(self, 
                  input_path: str, 
                  segments: List[Dict],
                  preset: Optional[Dict] = None,
                  fast_cut: bool = True) -> List[Optional[str]]:
        """
        Cut multiple segments dari 1 video
        
        Returns:
            List of output paths (None jika gagal)
        """
        results = []
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")
        
        for i, seg in enumerate(segments):
            # Extract segment info
            if isinstance(seg, dict):
                start = seg.get('start', '00:00')
                end = seg.get('end', '00:30')
                title = seg.get('title', f'clip_{i+1}')
            elif isinstance(seg, CutSegment):
                start = seg.start
                end = seg.end
                title = seg.title
            else:
                continue
            
            # Generate output name
            output_name = f"clip_{i+1:03d}_{title[:40]}"
            
            try:
                result = self.cut(
                    input_path=str(input_path),
                    start=start,
                    end=end,
                    output_name=output_name,
                    preset=preset,
                    fast_cut=fast_cut
                )
                results.append(result)
                print(f"  ✅ Clip {i+1}/{len(segments)}: {Path(result).name}")
            except Exception as e:
                print(f"  ❌ Clip {i+1}/{len(segments)} failed: {e}")
                results.append(None)
        
        return results
    
    def add_caption(self, 
                    input_path: str, 
                    caption_text: str, 
                    output_path: str,
                    position: str = "bottom",
                    fontsize: int = 24,
                    fontcolor: str = "white") -> str:
        """
        Add text caption ke video
        """
        # Escape special chars untuk FFmpeg
        escaped_caption = caption_text.replace("'", "'\\''").replace(':', '\\:')
        
        # Position mapping
        pos_map = {
            'top': 'y=50',
            'bottom': 'y=h-th-50',
            'middle': 'y=(h-th)/2',
        }
        y_pos = pos_map.get(position, 'y=h-th-50')
        
        cmd = [
            self.ffmpeg_path, '-y',
            '-i', input_path,
            '-vf', f"drawtext=text='{escaped_caption}':fontsize={fontsize}:fontcolor={fontcolor}:x=(w-tw)/2:{y_pos}",
            '-c:a', 'copy',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
    
    def add_caption_from_srt(self,
                             input_path: str,
                             srt_path: str,
                             output_path: str) -> str:
        """
        Add subtitle dari file .srt
        """
        cmd = [
            self.ffmpeg_path, '-y',
            '-i', input_path,
            '-vf', f"subtitles={shlex.quote(srt_path)}",
            '-c:a', 'copy',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
    
    def concatenate_videos(self, 
                           input_paths: List[str], 
                           output_name: str) -> str:
        """
        Concatenate multiple videos jadi 1
        """
        # Create temp file list
        temp_list = self.output_dir / "concat_list.txt"
        
        with open(temp_list, 'w') as f:
            for path in input_paths:
                if Path(path).exists():
                    f.write(f"file '{shlex.quote(str(path))}'\n")
        
        output_path = self.output_dir / f"{output_name}.mp4"
        
        cmd = [
            self.ffmpeg_path, '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(temp_list),
            '-c', 'copy',
            str(output_path)
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Cleanup temp file
        temp_list.unlink()
        
        return str(output_path)
    
    def get_video_duration(self, video_path: str) -> float:
        """
        Get video duration in seconds
        """
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 0.0
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        Get video metadata
        """
        import json
        
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_format', '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}


# Test module
if __name__ == "__main__":
    cutter = VideoCutter()
    
    print("🎬 AutoCut FFmpeg Wrapper")
    print(f"  FFmpeg: {cutter.ffmpeg_path}")
    print(f"  Output: {cutter.output_dir}")
    
    # Test time conversion
    print("\n⏱️  Time conversion test:")
    test_times = ["00:30", "01:30", "00:01:30", "90"]
    for t in test_times:
        print(f"  {t} → {cutter.time_to_seconds(t)}s")