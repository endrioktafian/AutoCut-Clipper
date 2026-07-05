#!/usr/bin/env python3
"""
📊 AUTOCUT TERMUX - Queue Manager
SQLite-based queue untuk multi-video processing
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

class QueueManager:
    """
    SQLite queue manager untuk track multi-video processing
    Support: resume, batch processing, status tracking
    """
    
    def __init__(self, db_path: str = "./autocut.db"):
        self.db_path = Path(db_path)
        self._init_db()
        
    def _init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Videos table
        c.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                downloaded_path TEXT,
                video_duration INTEGER,
                error_message TEXT
            )
        ''')
        
        # Clips table
        c.execute('''
            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                clip_index INTEGER,
                start TEXT NOT NULL,
                end TEXT NOT NULL,
                title TEXT,
                hook TEXT,
                caption TEXT,
                status TEXT DEFAULT 'pending',
                output_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
        ''')
        
        # Presets table
        c.execute('''
            CREATE TABLE IF NOT EXISTS presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                config TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Settings table
        c.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_clips_video_id ON clips(video_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_clips_status ON clips(status)')
        
        # Insert default preset
        c.execute('''
            INSERT OR IGNORE INTO presets (name, config, is_default)
            VALUES ('default', '{"zoom": false, "caption": false, "fps": 30, "fast_cut": true}', 1)
        ''')
        
        # Insert default settings
        default_settings = {
            'output_dir': './output',
            'temp_dir': './temp',
            'fast_cut': 'true',
            'auto_cleanup': 'true',
            'max_temp_files': '10',
        }
        
        for key, value in default_settings.items():
            c.execute('''
                INSERT OR IGNORE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========== VIDEO OPERATIONS ==========
    
    def add_video(self, url: str, title: str = None) -> int:
        """
        Add video to queue
        Returns: video_id
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute(
            "INSERT INTO videos (url, title, status) VALUES (?, ?, 'pending')",
            (url, title)
        )
        
        video_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return video_id
    
    def update_video(self, video_id: int, **kwargs) -> bool:
        """
        Update video fields
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['url', 'title', 'status', 'downloaded_path', 'video_duration', 'error_message']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            conn.close()
            return False
        
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(video_id)
        
        query = f"UPDATE videos SET {', '.join(fields)} WHERE id = ?"
        c.execute(query, values)
        
        conn.commit()
        conn.close()
        
        return c.rowcount > 0
    
    def get_video(self, video_id: int) -> Optional[Dict]:
        """Get video by ID"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = c.fetchone()
        
        conn.close()
        
        return dict(row) if row else None
    
    def get_pending_videos(self) -> List[Dict]:
        """Get all pending videos"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM videos WHERE status = 'pending' ORDER BY created_at")
        rows = c.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_processing_videos(self) -> List[Dict]:
        """Get all processing videos"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM videos WHERE status = 'processing' ORDER BY updated_at")
        rows = c.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_videos(self, limit: int = 50) -> List[Dict]:
        """Get all videos with limit"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM videos ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_video(self, video_id: int) -> bool:
        """Delete video and its clips"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("DELETE FROM clips WHERE video_id = ?", (video_id,))
        c.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        
        conn.commit()
        conn.close()
        
        return c.rowcount > 0
    
    # ========== CLIP OPERATIONS ==========
    
    def add_clips(self, video_id: int, clips: List[Dict]) -> List[int]:
        """
        Add multiple clips for a video
        Returns: list of clip_ids
        """
        conn = self._get_connection()
        c = conn.cursor()
        
        clip_ids = []
        
        for i, clip in enumerate(clips):
            c.execute('''
                INSERT INTO clips (video_id, clip_index, start, end, title, hook, caption, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (
                video_id,
                i,
                clip.get('start', '00:00'),
                clip.get('end', '00:30'),
                clip.get('title', f'Clip_{i+1}'),
                clip.get('hook'),
                clip.get('caption')
            ))
            clip_ids.append(c.lastrowid)
        
        conn.commit()
        conn.close()
        
        return clip_ids
    
    def update_clip(self, clip_id: int, **kwargs) -> bool:
        """Update clip fields"""
        conn = self._get_connection()
        c = conn.cursor()
        
        fields = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['status', 'output_path', 'error_message']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            conn.close()
            return False
        
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(clip_id)
        
        query = f"UPDATE clips SET {', '.join(fields)} WHERE id = ?"
        c.execute(query, values)
        
        conn.commit()
        conn.close()
        
        return c.rowcount > 0
    
    def get_clips(self, video_id: int, status: str = None) -> List[Dict]:
        """Get clips for a video, optionally filtered by status"""
        conn = self._get_connection()
        c = conn.cursor()
        
        if status:
            c.execute(
                "SELECT * FROM clips WHERE video_id = ? AND status = ? ORDER BY clip_index",
                (video_id, status)
            )
        else:
            c.execute(
                "SELECT * FROM clips WHERE video_id = ? ORDER BY clip_index",
                (video_id,)
            )
        
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_pending_clips(self, video_id: int) -> List[Dict]:
        """Get pending clips for a video"""
        return self.get_clips(video_id, status='pending')
    
    # ========== PRESET OPERATIONS ==========
    
    def save_preset(self, name: str, config: Dict, is_default: bool = False) -> bool:
        """Save or update preset"""
        conn = self._get_connection()
        c = conn.cursor()
        
        # If default, unset other defaults
        if is_default:
            c.execute("UPDATE presets SET is_default = 0")
        
        c.execute('''
            INSERT OR REPLACE INTO presets (name, config, is_default, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (name, json.dumps(config), 1 if is_default else 0))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_preset(self, name: str) -> Optional[Dict]:
        """Get preset by name"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM presets WHERE name = ?", (name,))
        row = c.fetchone()
        
        conn.close()
        
        if row:
            return {
                'name': row['name'],
                'config': json.loads(row['config']),
                'is_default': bool(row['is_default'])
            }
        return None
    
    def get_default_preset(self) -> Optional[Dict]:
        """Get default preset"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM presets WHERE is_default = 1")
        row = c.fetchone()
        
        conn.close()
        
        if row:
            return {
                'name': row['name'],
                'config': json.loads(row['config']),
                'is_default': True
            }
        return None
    
    def list_presets(self) -> List[Dict]:
        """List all presets"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("SELECT name, is_default, created_at FROM presets ORDER BY name")
        rows = c.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ========== SETTINGS OPERATIONS ==========
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get setting value"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        
        conn.close()
        
        return row['value'] if row else default
    
    def set_setting(self, key: str, value: str) -> bool:
        """Set setting value"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute("SELECT key, value FROM settings")
        rows = c.fetchall()
        
        conn.close()
        
        return {row['key']: row['value'] for row in rows}
    
    # ========== STATS ==========
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        conn = self._get_connection()
        c = conn.cursor()
        
        stats = {}
        
        # Video stats
        for status in ['pending', 'processing', 'done', 'error']:
            c.execute("SELECT COUNT(*) FROM videos WHERE status = ?", (status,))
            stats[f'videos_{status}'] = c.fetchone()[0]
        
        # Clip stats
        for status in ['pending', 'processing', 'done', 'error']:
            c.execute("SELECT COUNT(*) FROM clips WHERE status = ?", (status,))
            stats[f'clips_{status}'] = c.fetchone()[0]
        
        # Total counts
        c.execute("SELECT COUNT(*) FROM videos")
        stats['videos_total'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM clips")
        stats['clips_total'] = c.fetchone()[0]
        
        conn.close()
        
        return stats
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Get recent video activity"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT v.id, v.title, v.url, v.status, v.updated_at,
                   COUNT(c.id) as total_clips,
                   SUM(CASE WHEN c.status = 'done' THEN 1 ELSE 0 END) as done_clips
            FROM videos v
            LEFT JOIN clips c ON v.id = c.video_id
            GROUP BY v.id
            ORDER BY v.updated_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def clear_completed(self, older_than_days: int = 7) -> int:
        """Clear completed videos older than N days"""
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute('''
            DELETE FROM videos 
            WHERE status = 'done' 
            AND updated_at < datetime('now', ? || ' days')
        ''', (f'-{older_than_days}',))
        
        deleted = c.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted


# Test module
if __name__ == "__main__":
    qm = QueueManager()
    
    print("📊 Queue Manager Stats:")
    stats = qm.get_stats()
    
    print(f"\n  Videos:")
    print(f"    Total: {stats['videos_total']}")
    print(f"    Pending: {stats['videos_pending']}")
    print(f"    Processing: {stats['videos_processing']}")
    print(f"    Done: {stats['videos_done']}")
    print(f"    Error: {stats['videos_error']}")
    
    print(f"\n  Clips:")
    print(f"    Total: {stats['clips_total']}")
    print(f"    Pending: {stats['clips_pending']}")
    print(f"    Done: {stats['clips_done']}")
    
    print(f"\n  Presets:")
    for preset in qm.list_presets():
        default = " (default)" if preset['is_default'] else ""
        print(f"    - {preset['name']}{default}")