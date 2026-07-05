#!/usr/bin/env python3
"""
🎬 AUTOCUT TERMUX - GitHub Version (WITH LICENSE)
Menu-driven interface dengan license activation
HANYA untuk versi GitHub public - JANGAN dipake untuk personal use!
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
from license_manager import LicenseManager
from scene_detector import SceneDetector, detect_scenes_interactive

# Constants
VERSION = "1.0.0-GITHUB"
CONFIG_PATH = Path(__file__).parent / "config.json"
PRESETS_DIR = Path(__file__).parent / "presets"

BANNER = """
╔═══════════════════════════════════════════════════════════╗
║     🎬 AUTOCUT TERMUX v{version} - Viral Clip Generator     ║
║     AI-Powered Video Segmenter & Cutter                   ║
║     ⚠️  LICENSE REQUIRED - GitHub Version                 ║
╚═══════════════════════════════════════════════════════════╝
""".format(version=VERSION)

BANNER_TRIAL = """
╔═══════════════════════════════════════════════════════════╗
║     🎬 AUTOCUT TERMUX - TRIAL MODE                        ║
║     {days_remaining:>3} hari lagi sebelum expired                  ║
║     Ketik 'activate' untuk activate full license          ║
╚═══════════════════════════════════════════════════════════╝
"""

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

def check_license_requirement() -> bool:
    """
    Check license requirement di awal
    Returns: True jika valid, False jika harus exit
    """
    lm = LicenseManager()
    
    is_valid, message, info = lm.check()
    
    if is_valid:
        # License valid - show status singkat
        license_type = info.get('type', 'unknown') if info else 'unknown'
        print(f"\n🔐 License: {license_type} ✓")
        return True
    
    # License tidak valid - tampilkan menu activation
    print("\n" + "═" * 60)
    print("🔐 LICENSE REQUIRED")
    print("═" * 60)
    print(f"\n{message}")
    print("\nAutoCut Termux memerlukan license key untuk berjalan.")
    print("\n💡 Opsi:")
    print("  1. Masukkan license key (activate)")
    print("  2. Gunakan trial gratis 7 hari")
    print("  3. Exit")
    print("\n" + "─" * 60)
    
    while True:
        choice = input("\nPilih opsi [1-3]: ").strip().lower()
        
        if choice == '1' or choice == 'activate':
            key = input("\nMasukkan license key: ").strip()
            if key:
                success, msg = lm.activate(key)
                print(msg)
                if success:
                    print("\n✅ License activated! Restarting...")
                    return True
                else:
                    print("\n⚠️  Activation gagal. Coba lagi atau gunakan trial.")
        
        elif choice == '2' or choice == 'trial':
            # Generate trial key otomatis
            import hashlib
            device_id = lm.get_device_id()
            email = f"trial_{device_id[:8]}@local"
            trial_key = lm.generate_server_key(email, "trial", days=7)
            
            print(f"\n🎁 Trial key generated:")
            print(f"   {trial_key}")
            print(f"\n   Valid: 7 hari")
            print(f"   Email: {email}")
            
            success, msg = lm.activate(trial_key)
            if success:
                print("\n✅ Trial activated! Starting...")
                return True
            else:
                print("\n❌ Trial activation gagal.")
        
        elif choice == '3' or choice == 'exit' or choice == 'q':
            print("\n👋 Bye!")
            sys.exit(0)
        
        else:
            print("❌ Invalid option. Pilih 1, 2, atau 3.")

def print_banner():
    """Print application banner dengan license info"""
    print(BANNER)

def print_menu(trial_mode: bool = False, days_left: int = 0):
    """Print main menu"""
    print("\n" + "─" * 60)
    print("📋 MAIN MENU")
    print("─" * 60)
    print("  1. 📥 Download & Cut (URL + AI Output)")
    print("  2. ✂️  Cut Local Video (Paste AI Output)")
    print("  3. 🚀 AUTO MODE: Download → Detect → Cut (No AI!)")
    print("  4. 🎬 Auto-Detect Scenes (Local Video)")
    print("  5. 📊 View Queue Stats")
    print("  6. 📋 Process Pending Queue")
    print("  7. 🗑️  Clear Completed Videos")
    print("  8. ⚙️  Settings")
    print("  9. 🔐 License Status")
    print(" 10. ℹ️  About / Help")
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

def option_license_status(lm: LicenseManager):
    """Option: Show license status"""
    print("\n" + lm.status())

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

def option_auto_download_detect_cut(config: dict, downloader: VideoDownloader,
                                     cutter: VideoCutter, queue: QueueManager):
    """Option 3: FULL AUTO - Download → Detect Scenes → Cut (No AI needed!)"""
    print("\n" + "═" * 60)
    print("🚀 AUTO MODE: Download → Detect → Cut")
    print("═" * 60)
    print("\n💡 Flow: URL → Download → Auto-Detect Scenes → Cut")
    print("   Gak perlu AI output! Semuanya otomatis.\n")
    
    # Get URL
    url = input("📌 Masukkan URL (YouTube/TikTok/Instagram): ").strip()
    if not url:
        print("❌ URL kosong!")
        return
    
    # Get detection settings upfront
    print("\n⚙️  Scene Detection Settings:")
    try:
        threshold = input("   Threshold (0.1-0.9, default 0.3): ").strip()
        threshold = float(threshold) if threshold else 0.3
        
        min_length = input("   Min scene length (sec, default 3.0): ").strip()
        min_length = float(min_length) if min_length else 3.0
        
        max_clips = input("   Max clips to cut (default 10): ").strip()
        max_clips = int(max_clips) if max_clips else 10
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        return
    
    # Select preset
    print("\n🎨 Select preset:")
    presets = list_presets()
    for i, p in enumerate(presets, 1):
        default = " (default)" if p.get('is_default') else ""
        print(f"  [{i}] {p['name']}{default}")
    
    try:
        preset_idx = int(input("   Pilih preset [1-{}]: ".format(len(presets))).strip())
        preset_name = presets[preset_idx - 1]['name'] if 1 <= preset_idx <= len(presets) else 'default'
    except:
        preset_name = 'default'
    
    preset = load_preset(preset_name)
    print(f"   Using preset: {preset_name}")
    
    # Confirm
    print("\n" + "─" * 60)
    print("📋 SUMMARY:")
    print(f"   URL: {url[:60]}...")
    print(f"   Threshold: {threshold}")
    print(f"   Min length: {min_length}s")
    print(f"   Max clips: {max_clips}")
    print(f"   Preset: {preset_name}")
    print("─" * 60)
    
    confirm = input("\n🚀 Gas auto-cut? [y/n]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # STEP 1: Download
    print("\n" + "═" * 60)
    print("📥 STEP 1: Downloading...")
    print("═" * 60)
    
    try:
        video_info = downloader.get_video_info(url)
        print(f"  Title: {video_info['title']}")
        print(f"  Duration: {video_info['duration']}s")
        print(f"  Uploader: {video_info['uploader']}")
    except Exception as e:
        print(f"⚠️  Can't get info: {e}")
    
    print(f"\n⏳ Downloading {url}...")
    try:
        video_path = downloader.download(url)
        print(f"✅ Downloaded: {video_path}")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return
    
    # STEP 2: Auto-detect scenes
    print("\n" + "═" * 60)
    print("🎬 STEP 2: Auto-Detecting Scenes...")
    print("═" * 60)
    
    detector = SceneDetector(threshold=threshold, min_scene_length=min_length)
    
    def progress(current, total):
        pct = (current / total * 100) if total > 0 else 0
        print(f"   Scanning: {pct:.1f}%", end='\r')
    
    try:
        segments_raw = detector.detect_scenes(video_path, progress_callback=progress)
        print(f"\n✅ Found {len(segments_raw)} scenes!")
    except Exception as e:
        print(f"\n❌ Error detecting scenes: {e}")
        return
    
    # Limit max clips
    if len(segments_raw) > max_clips:
        print(f"⚠️  Limiting to {max_clips} clips (from {len(segments_raw)})")
        segments_raw = segments_raw[:max_clips]
    
    # Show detected scenes
    print("\n📊 Detected scenes:")
    print("─" * 50)
    for i, seg in enumerate(segments_raw, 1):
        start_ts = detector.format_timestamp(seg.start)
        end_ts = detector.format_timestamp(seg.end)
        duration = seg.end - seg.start
        print(f"  [{i}] {start_ts} - {end_ts} | {seg.title} ({duration:.1f}s)")
    print("─" * 50)
    
    # Final confirm
    confirm = input(f"\n✂️  Cut {len(segments_raw)} clips? [y/n]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # STEP 3: Cut
    print("\n" + "═" * 60)
    print("✂️  STEP 3: Cutting clips...")
    print("═" * 60)
    
    seg_data = [
        {'start': detector.format_timestamp(s.start), 
         'end': detector.format_timestamp(s.end), 
         'title': s.title}
        for s in segments_raw
    ]
    
    results = cutter.cut_batch(
        input_path=video_path,
        segments=seg_data,
        preset=preset,
        fast_cut=preset.get('fast_cut', True)
    )
    
    success_count = sum(1 for r in results if r)
    print(f"\n✅ Done! {success_count}/{len(results)} clips berhasil")
    
    # Show output
    if success_count > 0:
        print("\n📁 Output files:")
        for r in results:
            if r:
                print(f"  ✓ {r}")
        
        output_dir = config.get('output_dir', './output')
        print(f"\n💾 All clips saved to: {output_dir}/")

def option_auto_detect_scenes(config: dict, cutter: VideoCutter, queue: QueueManager):
    """Option 4: Auto-detect scenes from local video (no AI needed)"""
    print("\n" + "─" * 60)
    print("🎬 AUTO-DETECT SCENES")
    print("─" * 60)
    print("\nScan video dan auto-detect scene changes...")
    print("Tidak perlu AI output!\n")
    
    # Get video path
    video_path = input("📁 Path ke video file: ").strip().strip('"')
    
    if not Path(video_path).exists():
        print(f"\n❌ Video tidak ditemukan: {video_path}")
        return
    
    print(f"\n✓ Video found: {Path(video_path).name}")
    
    # Get detection settings
    print("\n⚙️  Detection Settings:")
    try:
        threshold = input("   Scene threshold (0.1-0.9, default 0.3): ").strip()
        if not threshold:
            threshold = 0.3
        else:
            threshold = float(threshold)
        
        min_length = input("   Min scene length in seconds (default 3.0): ").strip()
        if not min_length:
            min_length = 3.0
        else:
            min_length = float(min_length)
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        return
    
    # Detect scenes
    print("\n🔍 Scanning video...")
    
    detector = SceneDetector(threshold=threshold, min_scene_length=min_length)
    
    try:
        segments = detector.detect_scenes(video_path)
        print(f"\n✅ Found {len(segments)} scenes!\n")
    except Exception as e:
        print(f"\n❌ Error detecting scenes: {e}")
        return
    
    # Show results
    print("📊 Detected scenes:\n")
    print("─" * 50)
    for i, seg in enumerate(segments, 1):
        start_ts = detector.format_timestamp(seg.start)
        end_ts = detector.format_timestamp(seg.end)
        duration = seg.end - seg.start
        print(f"  [{i}] {start_ts} - {end_ts} | {seg.title} ({duration:.1f}s)")
    print("─" * 50)
    
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
    
    # Confirm cut
    confirm = input(f"\n✂️  Cut {len(segments)} scenes? [y/n]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Cut video
    print(f"\n⏳ Cutting scenes...")
    seg_data = [
        {'start': detector.format_timestamp(s.start), 
         'end': detector.format_timestamp(s.end), 
         'title': s.title}
        for s in segments
    ]
    
    results = cutter.cut_batch(
        input_path=video_path,
        segments=seg_data,
        preset=preset,
        fast_cut=preset.get('fast_cut', True)
    )
    
    success_count = sum(1 for r in results if r)
    print(f"\n✅ Done! {success_count}/{len(results)} scenes berhasil")
    
    # Show output
    if success_count > 0:
        print("\n📁 Output files:")
        for r in results:
            if r:
                print(f"  ✓ {r}")

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
    """Option 8: About / Help"""
    print("\n" + "─" * 60)
    print("ℹ️  ABOUT / HELP")
    print("─" * 60)
    
    print("""
🎬 AUTOCUT TERMUX v1.0.0 (GitHub Version)

LICENSED VERSION - Requires activation

FEATURES:
  • Download video from YouTube/TikTok/Instagram
  • Parse AI output from Gemini/Claude/ChatGPT
  • Auto-cut video based on AI timestamps
  • Batch processing with queue system
  • Customizable presets (zoom, fps, effects)
  • SQLite-based queue for resume capability

LICENSE:
  • Trial: 7 days gratis
  • Full: 1 tahun (365 hari)
  • 1 license = 1 device

ACTIVATION:
  1. Beli license di: (your website)
  2. Dapatkan license key via email
  3. Pilih menu 7 (License) → Activate
  4. Paste license key

SUPPORT:
  • Email: support@yourdomain.com
  • Docs: README.md
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
    """Main entry point - dengan license check di awal"""
    # CHECK LICENSE FIRST
    if not check_license_requirement():
        print("\n❌ License validation failed. Exiting.")
        sys.exit(1)
    
    # License valid - lanjut ke main app
    print_banner()
    
    # Load config
    config = load_config()
    
    # Initialize components
    downloader = VideoDownloader(config.get('temp_dir', './temp'))
    cutter = VideoCutter(config.get('output_dir', './output'))
    queue = QueueManager()
    lm = LicenseManager()
    
    # Check trial mode
    is_valid, _, info = lm.check()
    trial_mode = info and info.get('type') == 'trial' if info else False
    days_left = 0
    if info and 'expiry' in info:
        try:
            expiry = datetime.fromisoformat(info['expiry'])
            days_left = max(0, (expiry - datetime.now()).days)
        except:
            pass
    
    if trial_mode:
        print(BANNER_TRIAL.format(days_remaining=days_left))
    
    # Main loop
    while True:
        print_menu(trial_mode, days_left)
        
        try:
            choice = input("\nPilih opsi [0-8]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Bye!")
            sys.exit(0)
        
        if choice == '1':
            option_download_and_cut(config, downloader, cutter, queue)
        
        elif choice == '2':
            option_cut_local(config, cutter, queue)
        
        elif choice == '3':
            # NEW: Full auto mode
            option_auto_download_detect_cut(config, downloader, cutter, queue)
        
        elif choice == '4':
            option_auto_detect_scenes(config, cutter, queue)
        
        elif choice == '5':
            option_view_stats(queue)
        
        elif choice == '6':
            option_process_queue(queue, cutter)
        
        elif choice == '7':
            option_clear_completed(queue)
        
        elif choice == '8':
            option_settings(config, queue)
        
        elif choice == '9':
            option_license_status(lm)
        
        elif choice == '10':
            option_about()
        
        elif choice == '0':
            print("\n👋 Bye!")
            sys.exit(0)
        
        else:
            print("❌ Invalid option. Choose 0-10.")
        
        # Pause before next iteration
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()