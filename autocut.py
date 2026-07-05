#!/usr/bin/env python3
"""
🎬 AUTOCUT TERMUX - Main CLI
Menu-driven interface untuk auto-cut video dari AI output
No license, no expiry, full access
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

from parser import AIParser, VideoAnalysis
from downloader import VideoDownloader
from cutter import VideoCutter
from queue_manager import QueueManager

# Constants
VERSION = "1.0.0"
CONFIG_PATH = Path(__file__).parent / "config.json"
PRESETS_DIR = Path(__file__).parent / "presets"
BANNER = """
╔═══════════════════════════════════════════════════════════╗
║     🎬 AUTOCUT TERMUX v{version} - Viral Clip Generator     ║
║     AI-Powered Video Segmenter & Cutter                   ║
║     No License • No Expiry • Full Access                  ║
╚═══════════════════════════════════════════════════════════╝
""".format(version=VERSION)

def load_config() -> dict:
    """Load configuration"""
    if CONFIG_PATH.exists():
        return json.load(open(CONFIG_PATH, 'r'))
    return {
        "output_dir": "./output",
        "temp_dir": "./temp",
        "default_preset": "default",
        "fast_cut": True,
        "auto_cleanup": True,
        "max_temp_files": 10,
    }

def load_preset(name: str) -> dict:
    """Load preset by name"""
    preset_path = PRESETS_DIR / f"{name}.json"
    if preset_path.exists():
        return json.load(open(preset_path, 'r'))
    return {
        "zoom": False,
        "fast_cut": True,
        "fps": 30
    }

def print_banner():
    """Print application banner"""
    print(BANNER)

def print_menu():
    """Print main menu"""
    print("\n" + "─" * 60)
    print("📋 MAIN MENU")
    print("─" * 60)
    print("  1. 📥 Download & Cut (URL + AI Output)")
    print("  2. ✂️  Cut Local Video (Paste AI Output)")
    print("  3. 📊 View Queue Stats")
    print("  4. 📋 Process Pending Queue")
    print("  5. 🗑️  Clear Completed Videos")
    print("  6. ⚙️  Settings")
    print("  7. ℹ️  About / Help")
    print("  0. 🚪 Exit")
    print("─" * 60)

def input_multiline(prompt: str, stop_word: str = "DONE") -> str:
    """Get multiline input from user"""
    print(prompt)
    print(f"(Ketik '{stop_word}' di baris baru untuk selesai)\n")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == stop_word.upper():
                break
            lines.append(line)
        except EOFError:
            break
    
    return "\n".join(lines)

def option_download_and_cut(config: dict, downloader: VideoDownloader, 
                            cutter: VideoCutter, queue: QueueManager):
    """Option 1: Download video from URL and cut"""
    print("\n" + "─" * 60)
    print("📥 DOWNLOAD & CUT")
    print("─" * 60)
    
    # Get URL
    url = input("\nMasukkan URL YouTube/TikTok/Instagram: ").strip()
    if not url:
        print("❌ URL kosong!")
        return
    
    # Get video info first
    print("\n📊 Getting video info...")
    try:
        video_info = downloader.get_video_info(url)
        print(f"  Title: {video_info['title']}")
        print(f"  Duration: {video_info['duration']}s")
        print(f"  Uploader: {video_info['uploader']}")
    except Exception as e:
        print(f"⚠️  Can't get info: {e}")
    
    # Confirm download
    confirm = input("\nDownload video ini? [y/n]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Download
    print(f"\n⏳ Downloading {url}...")
    try:
        video_path = downloader.download(url)
        print(f"✅ Downloaded: {video_path}")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return
    
    # Get AI output
    ai_text = input_multiline("\n📋 Paste AI output dari Gemini/Claude:")
    
    if not ai_text or len(ai_text.strip()) < 50:
        print("❌ AI output terlalu pendek atau kosong!")
        return
    
    # Parse AI output
    print("\n🔍 Parsing AI output...")
    parser = AIParser()
    result = parser.parse(ai_text)
    
    if not result:
        print("❌ Gak ada klip yang terdeteksi dari AI output!")
        return
    
    print(f"✅ Found {len(result.clips)} clips:")
    for i, clip in enumerate(result.clips, 1):
        print(f"  [{i}] {clip.start} → {clip.end}: {clip.title[:50]}")
        if clip.hook:
            print(f"      Hook: {clip.hook[:50]}...")
    
    # Select preset
    print("\n🎨 Select preset:")
    presets = list_presets()
    for i, p in enumerate(presets, 1):
        default = " (default)" if p.get('is_default') else ""
        print(f"  [{i}] {p['name']}{default}")
    
    try:
        preset_idx = int(input("\nPilih preset [1-{}]: ".format(len(presets))).strip())
        preset_name = presets[preset_idx - 1]['name'] if 1 <= preset_idx <= len(presets) else 'default'
    except:
        preset_name = 'default'
    
    preset = load_preset(preset_name)
    print(f"Using preset: {preset_name}")
    
    # Confirm cut
    confirm = input(f"\n✂️  Cut {len(result.clips)} clips? [y/n]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Cut video
    print(f"\n⏳ Cutting clips...")
    segments = [
        {
            'start': clip.start,
            'end': clip.end,
            'title': clip.title
        }
        for clip in result.clips
    ]
    
    results = cutter.cut_batch(
        input_path=video_path,
        segments=segments,
        preset=preset,
        fast_cut=preset.get('fast_cut', True)
    )
    
    success_count = sum(1 for r in results if r)
    print(f"\n✅ Done! {success_count}/{len(results)} clips berhasil")
    
    # Show output files
    if success_count > 0:
        print("\n📁 Output files:")
        for r in results:
            if r:
                print(f"  ✓ {r}")

def option_cut_local(config: dict, cutter: VideoCutter, queue: QueueManager):
    """Option 2: Cut local video file"""
    print("\n" + "─" * 60)
    print("✂️  CUT LOCAL VIDEO")
    print("─" * 60)
    
    # Get video path
    video_path = input("\nMasukkan path video file: ").strip()
    video_path = Path(video_path)
    
    # Expand ~
    if str(video_path).startswith('~'):
        video_path = Path.home() / str(video_path)[1:]
    
    if not video_path.exists():
        print(f"❌ File not found: {video_path}")
        return
    
    print(f"✓ Video found: {video_path.name}")
    
    # Get AI output
    ai_text = input_multiline("\n📋 Paste AI output dari Gemini/Claude:")
    
    if not ai_text or len(ai_text.strip()) < 50:
        print("❌ AI output terlalu pendek!")
        return
    
    # Parse
    print("\n🔍 Parsing AI output...")
    parser = AIParser()
    result = parser.parse(ai_text)
    
    if not result:
        print("❌ Gak ada klip yang terdeteksi!")
        return
    
    print(f"✅ Found {len(result.clips)} clips:")
    for i, clip in enumerate(result.clips, 1):
        print(f"  [{i}] {clip.start} → {clip.end}: {clip.title[:50]}")
    
    # Select preset
    print("\n🎨 Select preset:")
    presets = list_presets()
    for i, p in enumerate(presets, 1):
        default = " (default)" if p.get('is_default') else ""
        print(f"  [{i}] {p['name']}{default}")
    
    try:
        preset_idx = int(input("\nPilih preset [1-{}]: ".format(len(presets))).strip())
        preset_name = presets[preset_idx - 1]['name'] if 1 <= preset_idx <= len(presets) else 'default'
    except:
        preset_name = 'default'
    
    preset = load_preset(preset_name)
    
    # Confirm
    confirm = input(f"\n✂️  Cut {len(result.clips)} clips? [y/n]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Cut
    print(f"\n⏳ Cutting clips...")
    segments = [
        {'start': c.start, 'end': c.end, 'title': c.title}
        for c in result.clips
    ]
    
    results = cutter.cut_batch(
        input_path=str(video_path),
        segments=segments,
        preset=preset,
        fast_cut=preset.get('fast_cut', True)
    )
    
    success_count = sum(1 for r in results if r)
    print(f"\n✅ Done! {success_count}/{len(results)} clips berhasil")

def option_view_stats(queue: QueueManager):
    """Option 3: View queue statistics"""
    print("\n" + "─" * 60)
    print("📊 QUEUE STATISTICS")
    print("─" * 60)
    
    stats = queue.get_stats()
    
    print("\n📹 VIDEOS:")
    print(f"  Total:     {stats['videos_total']}")
    print(f"  Pending:   {stats['videos_pending']}")
    print(f"  Processing:{stats['videos_processing']}")
    print(f"  Done:      {stats['videos_done']}")
    print(f"  Error:     {stats['videos_error']}")
    
    print("\n✂️  CLIPS:")
    print(f"  Total:     {stats['clips_total']}")
    print(f"  Pending:   {stats['clips_pending']}")
    print(f"  Done:      {stats['clips_done']}")
    print(f"  Error:     {stats['clips_error']}")
    
    # Recent activity
    print("\n📜 RECENT ACTIVITY:")
    recent = queue.get_recent_activity(5)
    if recent:
        for vid in recent:
            status_icon = {'pending': '⏳', 'processing': '⏳', 'done': '✅', 'error': '❌'}.get(vid['status'], '❓')
            done_clips = vid.get('done_clips', 0) or 0
            total_clips = vid.get('total_clips', 0) or 0
            print(f"  {status_icon} {vid['title'] or 'Untitled'} ({done_clips}/{total_clips} clips)")
    else:
        print("  (no activity yet)")

def option_process_queue(queue: QueueManager, cutter: VideoCutter):
    """Option 4: Process pending videos in queue"""
    print("\n" + "─" * 60)
    print("📋 PROCESS PENDING QUEUE")
    print("─" * 60)
    
    pending = queue.get_pending_videos()
    
    if not pending:
        print("✅ No pending videos in queue!")
        return
    
    print(f"Found {len(pending)} pending video(s)")
    
    for video in pending:
        print(f"\n🎬 Processing: {video['title'] or video['url']}")
        
        # Get clips
        clips = queue.get_clips(video['id'])
        
        if not clips:
            print("  ⚠️  No clips found for this video")
            queue.update_video(video['id'], status='error', error_message='No clips')
            continue
        
        # Update status
        queue.update_video(video['id'], status='processing')
        
        # Process each clip
        for clip in clips:
            print(f"  ✂️  Cutting clip: {clip['start']} → {clip['end']}")
            
            try:
                output_name = f"clip_{clip['clip_index']}_{clip['title'][:30]}"
                result = cutter.cut(
                    input_path=video['downloaded_path'],
                    start=clip['start'],
                    end=clip['end'],
                    output_name=output_name
                )
                
                queue.update_clip(clip['id'], status='done', output_path=result)
                print(f"    ✅ Done: {Path(result).name}")
                
            except Exception as e:
                queue.update_clip(clip['id'], status='error', error_message=str(e))
                print(f"    ❌ Failed: {e}")
        
        # Update video status
        done_clips = len([c for c in clips if c.get('status') == 'done'])
        if done_clips == len(clips):
            queue.update_video(video['id'], status='done')
            print(f"✅ Video complete: {done_clips}/{len(clips)} clips")
        else:
            queue.update_video(video['id'], status='error')
            print(f"❌ Video incomplete: {done_clips}/{len(clips)} clips")

def option_clear_completed(queue: QueueManager):
    """Option 5: Clear completed videos"""
    print("\n" + "─" * 60)
    print("🗑️  CLEAR COMPLETED VIDEOS")
    print("─" * 60)
    
    days = input("Clear videos older than N days [7]: ").strip()
    days = int(days) if days.isdigit() else 7
    
    confirm = input(f"Delete completed videos older than {days} days? [y/n]: ").strip().lower()
    
    if confirm == 'y':
        deleted = queue.clear_completed(days)
        print(f"✅ Deleted {deleted} video(s)")
    else:
        print("Cancelled.")

def option_settings(config: dict, queue: QueueManager):
    """Option 6: Settings"""
    print("\n" + "─" * 60)
    print("⚙️  SETTINGS")
    print("─" * 60)
    
    settings = queue.get_all_settings()
    
    print("\nCurrent settings:")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    
    print("\nActions:")
    print("  1. Change default preset")
    print("  2. Change output directory")
    print("  3. Toggle fast cut")
    print("  4. Reset to defaults")
    print("  0. Back")
    
    choice = input("\nPilih [0-4]: ").strip()
    
    if choice == '1':
        presets = list_presets()
        for i, p in enumerate(presets, 1):
            print(f"  [{i}] {p['name']}")
        
        try:
            idx = int(input("Pilih preset [1-{}]: ".format(len(presets))).strip())
            if 1 <= idx <= len(presets):
                queue.set_setting('default_preset', presets[idx-1]['name'])
                print("✅ Default preset updated")
        except:
            pass
    
    elif choice == '2':
        new_dir = input("New output directory [./output]: ").strip()
        if new_dir:
            queue.set_setting('output_dir', new_dir)
            print("✅ Output directory updated")
    
    elif choice == '3':
        current = queue.get_setting('fast_cut', 'true')
        new_val = 'false' if current == 'true' else 'true'
        queue.set_setting('fast_cut', new_val)
        print(f"✅ Fast cut set to: {new_val}")
    
    elif choice == '4':
        confirm = input("Reset all settings to default? [y/n]: ").strip().lower()
        if confirm == 'y':
            queue.set_setting('default_preset', 'default')
            queue.set_setting('output_dir', './output')
            queue.set_setting('fast_cut', 'true')
            print("✅ Settings reset to default")

def option_about():
    """Option 7: About / Help"""
    print("\n" + "─" * 60)
    print("ℹ️  ABOUT / HELP")
    print("─" * 60)
    
    print("""
🎬 AUTOCUT TERMUX v1.0.0

An open-source AI-powered video clipper for Termux.
No license, no expiry, full access.

FEATURES:
  • Download video from YouTube/TikTok/Instagram
  • Parse AI output from Gemini/Claude/ChatGPT
  • Auto-cut video based on AI timestamps
  • Batch processing with queue system
  • Customizable presets (zoom, fps, effects)
  • SQLite-based queue for resume capability

HOW TO USE:
  1. Get AI analysis from Gemini/Claude
     - Paste video URL to AI
     - Ask for viral clip segments with timestamps
     - Copy the output
  
  2. In AutoCut:
     - Option 1: Download + Cut (paste URL + AI output)
     - Option 2: Cut Local (already have video file)
  
  3. Select preset and confirm
  4. Wait for processing
  5. Find output in ./output folder

AI PROMPT TEMPLATE:
  "Analyze this video and identify viral clip segments.
   For each clip, provide:
   - Timestamp (start - end)
   - Title/hook
   - Why it's viral
   
   Format:
   KLIP [1]:
   00:00 - 00:30 | Catchy title
   Hook: \"The hook text\"
   "

SUPPORT:
  • GitHub: (your repo)
  • License: MIT (open source)
  • No warranty - use at your own risk
""")

def list_presets() -> list:
    """List available presets"""
    presets = []
    
    # Default preset
    presets.append({'name': 'default', 'is_default': True})
    
    # File presets
    if PRESETS_DIR.exists():
        for f in PRESETS_DIR.glob('*.json'):
            if f.stem != 'default':
                presets.append({'name': f.stem, 'is_default': False})
    
    return presets

def main():
    """Main entry point"""
    print_banner()
    
    # Load config
    config = load_config()
    
    # Initialize components
    downloader = VideoDownloader(config.get('temp_dir', './temp'))
    cutter = VideoCutter(config.get('output_dir', './output'))
    queue = QueueManager()
    
    # Main loop
    while True:
        print_menu()
        
        try:
            choice = input("\nPilih opsi [0-7]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Bye!")
            sys.exit(0)
        
        if choice == '1':
            option_download_and_cut(config, downloader, cutter, queue)
        
        elif choice == '2':
            option_cut_local(config, cutter, queue)
        
        elif choice == '3':
            option_view_stats(queue)
        
        elif choice == '4':
            option_process_queue(queue, cutter)
        
        elif choice == '5':
            option_clear_completed(queue)
        
        elif choice == '6':
            option_settings(config, queue)
        
        elif choice == '7':
            option_about()
        
        elif choice == '0':
            print("\n👋 Bye!")
            sys.exit(0)
        
        else:
            print("❌ Invalid option. Choose 0-7.")
        
        # Pause before next iteration
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()