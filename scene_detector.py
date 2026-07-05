#!/usr/bin/env python3
"""
🎬 AUTOCUT TERMUX - Scene Detector
Auto-detect scene changes dari video menggunakan FFmpeg
No AI required - purely based on visual changes
"""

import subprocess
import re
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SceneSegment:
    start: float  # seconds
    end: float    # seconds
    frame: int    # frame number where scene starts
    score: float  # scene change score (0-1)
    title: str    # auto-generated title

class SceneDetector:
    """
    Scene detection menggunakan FFmpeg scene filter
    Detects scene changes based on pixel differences between frames
    """
    
    def __init__(self, threshold: float = 0.3, min_scene_length: float = 2.0):
        """
        Args:
            threshold: Scene change threshold (0-1). Lower = more sensitive
            min_scene_length: Minimum scene length in seconds
        """
        self.threshold = threshold
        self.min_scene_length = min_scene_length
        
    def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return float(result.stdout.strip())
        except:
            return 0.0
    
    def get_video_fps(self, video_path: str) -> float:
        """Get video FPS"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            fps_str = result.stdout.strip()
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            return float(fps_str)
        except:
            return 30.0
    
    def detect_scenes(self, video_path: str, progress_callback=None) -> List[SceneSegment]:
        """
        Detect scene changes in video
        
        Args:
            video_path: Path to video file
            progress_callback: Optional callback(current_time, duration)
            
        Returns:
            List of SceneSegment objects
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        duration = self.get_video_duration(str(video_path))
        fps = self.get_video_fps(str(video_path))
        
        if progress_callback:
            progress_callback(0, duration)
        
        # FFmpeg scene detect command
        # detect_scenes filter outputs scene change data
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-vf', f'scene=0.3:2',  # threshold=0.3, blocksize=2
            '-an', '-f', 'null', '-'
        ]
        
        # Run and capture stderr (where scene data is output)
        result = subprocess.run(cmd, capture_output=True, text=True)
        stderr = result.stderr
        
        # Parse scene changes from output
        # Format: "scene:0.852341" lines indicate scene changes
        scene_frames = []
        
        # Alternative: use select filter with scene score
        cmd_select = [
            'ffmpeg', '-i', str(video_path),
            '-vf', f"select='gt(scene,{self.threshold})',metadata=print:file=-",
            '-f', 'null', '-'
        ]
        
        result_select = subprocess.run(cmd_select, capture_output=True, text=True)
        
        # Parse frame numbers from select output
        # Looking for lines like: "lavfi.scene_score=0.852341"
        lines = result_select.stderr.split('\n')
        
        current_frame = 0
        scene_scores = []
        
        for line in lines:
            if 'lavfi.scene_score' in line:
                try:
                    score = float(line.split('=')[1])
                    scene_scores.append((current_frame, score))
                except:
                    pass
            elif 'n:' in line:
                try:
                    current_frame = int(line.split(':')[1].split()[0])
                except:
                    pass
        
        # If no scenes detected with select, try parsing select output differently
        if not scene_scores:
            # Use simpler approach: parse frame numbers directly
            cmd_simple = [
                'ffmpeg', '-i', str(video_path),
                '-vf', f"select='gt(scene,{self.threshold})'",
                '-vsync', 'vfr',
                '-f', 'null', '-'
            ]
            result_simple = subprocess.run(cmd_simple, capture_output=True, text=True)
            
            # Count scene changes from output
            scene_lines = [l for l in result_simple.stderr.split('\n') if 'frame=' in l]
            
            # Estimate scene positions based on output
            if scene_lines:
                # Fallback: divide video into segments based on detected changes
                pass
        
        # Build scene segments
        segments = []
        
        if scene_scores:
            # Sort by frame number
            scene_scores.sort(key=lambda x: x[0])
            
            # Create segments between scene changes
            prev_frame = 0
            for i, (frame, score) in enumerate(scene_scores):
                start_time = prev_frame / fps
                end_time = frame / fps
                
                # Skip scenes that are too short
                if end_time - start_time >= self.min_scene_length:
                    segments.append(SceneSegment(
                        start=start_time,
                        end=end_time,
                        frame=prev_frame,
                        score=score,
                        title=f"Scene {len(segments)+1}"
                    ))
                
                prev_frame = frame
            
            # Add final segment
            if duration - (prev_frame / fps) >= self.min_scene_length:
                segments.append(SceneSegment(
                    start=prev_frame / fps,
                    end=duration,
                    frame=prev_frame,
                    score=1.0,
                    title=f"Scene {len(segments)+1}"
                ))
        else:
            # No scenes detected - divide video into equal segments
            segment_duration = 30.0  # Default 30 seconds per segment
            current_time = 0.0
            scene_num = 1
            
            while current_time < duration:
                end_time = min(current_time + segment_duration, duration)
                if end_time - current_time >= self.min_scene_length:
                    segments.append(SceneSegment(
                        start=current_time,
                        end=end_time,
                        frame=int(current_time * fps),
                        score=0.5,
                        title=f"Segment {scene_num}"
                    ))
                    scene_num += 1
                current_time = end_time
        
        if progress_callback:
            progress_callback(duration, duration)
        
        return segments
    
    def format_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def export_to_clip_format(self, segments: List[SceneSegment]) -> str:
        """Export scenes in format that cutter.py can use"""
        output = []
        for seg in segments:
            start_ts = self.format_timestamp(seg.start)
            end_ts = self.format_timestamp(seg.end)
            duration = seg.end - seg.start
            output.append(f"{start_ts} - {end_ts} | {seg.title} ({duration:.1f}s)")
        return '\n'.join(output)
    
    def export_to_json(self, segments: List[SceneSegment]) -> str:
        """Export scenes as JSON"""
        data = []
        for seg in segments:
            data.append({
                'start': self.format_timestamp(seg.start),
                'end': self.format_timestamp(seg.end),
                'start_seconds': round(seg.start, 2),
                'end_seconds': round(seg.end, 2),
                'title': seg.title,
                'score': round(seg.score, 3)
            })
        return json.dumps(data, indent=2)


def detect_scenes_interactive():
    """Interactive scene detection"""
    print("\n" + "="*60)
    print("🎬 AUTO SCENE DETECTOR")
    print("="*60)
    print("\nScan video dan auto-detect scene changes...")
    print("Tidak perlu AI output!\n")
    
    # Get video path
    video_path = input("📁 Path ke video file: ").strip().strip('"')
    
    if not Path(video_path).exists():
        print(f"\n❌ Video tidak ditemukan: {video_path}")
        return None
    
    # Get detection settings
    print("\n⚙️  Settings:")
    threshold = input("   Scene threshold (0.1-0.9, default 0.3): ").strip()
    if not threshold:
        threshold = 0.3
    else:
        threshold = float(threshold)
    
    min_length = input("   Min scene length in seconds (default 2.0): ").strip()
    if not min_length:
        min_length = 2.0
    else:
        min_length = float(min_length)
    
    # Detect scenes
    print("\n🔍 Scanning video...")
    
    detector = SceneDetector(threshold=threshold, min_scene_length=min_length)
    
    def progress(current, total):
        pct = (current / total * 100) if total > 0 else 0
        print(f"   Progress: {pct:.1f}%", end='\r')
    
    try:
        segments = detector.detect_scenes(video_path, progress_callback=progress)
        print(f"\n   ✅ Scan complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None
    
    # Show results
    print(f"\n📊 Found {len(segments)} scenes:\n")
    print("-" * 50)
    for i, seg in enumerate(segments, 1):
        start_ts = detector.format_timestamp(seg.start)
        end_ts = detector.format_timestamp(seg.end)
        duration = seg.end - seg.start
        print(f"  [{i}] {start_ts} - {end_ts} | {seg.title} ({duration:.1f}s, score: {seg.score:.2f})")
    print("-" * 50)
    
    # Export options
    print("\n💾 Export options:")
    print("  1. Copy timestamps to clipboard format")
    print("  2. Save as JSON")
    print("  3. Cut video with these scenes")
    print("  4. Cancel")
    
    choice = input("\nPilih opsi [1-4]: ").strip()
    
    if choice == '1':
        output = detector.export_to_clip_format(segments)
        print("\n📋 Timestamps (copy-paste ke cutter):")
        print("-" * 50)
        print(output)
        print("-" * 50)
        return segments
    
    elif choice == '2':
        output = detector.export_to_json(segments)
        save_path = input("Save path (default: ./scenes.json): ").strip()
        if not save_path:
            save_path = "./scenes.json"
        Path(save_path).write_text(output)
        print(f"✅ Saved to {save_path}")
        return segments
    
    elif choice == '3':
        # Return segments for cutting
        return segments
    
    return None


if __name__ == "__main__":
    detect_scenes_interactive()