#!/usr/bin/env python3
"""
🎬 AUTOCUT TERMUX - AI Output Parser
Parse output dari Gemini/Claude/ChatGPT untuk extract klip segmentasi
Support format: KLIP [N], timestamp, hook, caption
"""

import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from pathlib import Path

@dataclass
class ClipSegment:
    start: str
    end: str
    title: str
    hook: Optional[str] = None
    caption: Optional[str] = None
    viral_score: Optional[str] = None
    reason: Optional[str] = None

@dataclass
class VideoAnalysis:
    url: str
    title: str
    clips: List[ClipSegment]
    raw_text: str
    hooks: List[List[str]] = None
    captions: List[str] = None

class AIParser:
    """
    Finite State Machine Parser untuk AI output
    States: IDLE → META → HOOKS → SEO → TIMESTAMP → HALT
    """
    
    def __init__(self):
        # Pattern regex
        self.url_pattern = re.compile(
            r'(https?://(?:www\.)?(?:youtube\.com|youtu\.be|m\.youtube\.com)[^\s>\]\)]+)',
            re.IGNORECASE
        )
        self.time_pattern = re.compile(
            r'\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*(?:\||-|s/d|to|sampai|→)\s*\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?',
            re.IGNORECASE
        )
        self.clip_header_pattern = re.compile(
            r'(?:KLIP|CLIP|SEGMENT|BAGIAN)\s*\[?(\d+)\]?:?\s*(.*)',
            re.IGNORECASE
        )
        self.hook_pattern = re.compile(
            r'(?:Hook|Hooks|Opsi Hook|IDE HOOK|ASET 1):\s*(.*)',
            re.IGNORECASE
        )
        self.caption_pattern = re.compile(
            r'(?:Caption|SEO|Deskripsi|ASET 2):\s*(.*)',
            re.IGNORECASE | re.DOTALL
        )
        self.viral_score_pattern = re.compile(
            r'(?:Skor Viral|Viral Score|Score):\s*(\d+\.?\d*|%?)',
            re.IGNORECASE
        )
        self.reason_pattern = re.compile(
            r'(?:Alasan Viral|Reason|Why):\s*(.*)',
            re.IGNORECASE
        )
        self.halt_pattern = re.compile(
            r'(BAGIAN 2|BAGIAN 3|LANGKAH SELANJUTNYA|NEXT STEP|---)',
            re.IGNORECASE
        )
        
    def parse(self, text: str) -> Optional[VideoAnalysis]:
        """
        Parse AI output text menjadi structured data
        """
        if not text or len(text.strip()) < 50:
            return None
            
        lines = text.split('\n')
        
        # Extract metadata
        metadata = self._extract_metadata(text, lines)
        
        # Extract clips dengan FSM
        clips, hooks_list, captions_list = self._extract_clips_fsm(text, lines)
        
        if not clips:
            # Fallback: cari timestamp langsung
            clips = self._extract_clips_fallback(text)
        
        if not clips:
            return None
            
        return VideoAnalysis(
            url=metadata.get('url', ''),
            title=metadata.get('title', 'Video_Analysis'),
            clips=clips,
            raw_text=text,
            hooks=hooks_list if hooks_list else None,
            captions=captions_list if captions_list else None
        )
    
    def _extract_metadata(self, text: str, lines: List[str]) -> Dict:
        """Extract URL dan judul dari text"""
        metadata = {'url': '', 'title': ''}
        
        # URL
        url_match = self.url_pattern.search(text)
        if url_match:
            metadata['url'] = url_match.group(1).strip()
        
        # Judul - coba berbagai pattern
        title_patterns = [
            r'Judul:\s*(.+?)(?:\n|$)',
            r'Title:\s*(.+?)(?:\n|$)',
            r'Video:\s*(.+?)(?:\n|$)',
            r'📹\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['title'] = match.group(1).strip()
                # Clean title untuk filename
                metadata['title'] = metadata['title'].replace('|', '-')
                break
        
        if not metadata['title']:
            # Generate dari URL
            if metadata['url']:
                video_id = self._extract_video_id(metadata['url'])
                metadata['title'] = f"Video_{video_id}" if video_id else "Video_Analysis"
            else:
                metadata['title'] = "Video_Analysis"
                
        return metadata
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID dari URL"""
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11})',
            r'youtu\.be/([0-9A-Za-z_-]{11})',
            r'embed/([0-9A-Za-z_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _extract_clips_fsm(self, text: str, lines: List[str]) -> tuple:
        """
        FSM extraction: IDLE → META → HOOKS → SEO → TIMESTAMP
        """
        clips = []
        hooks_list = []
        captions_list = []
        
        current_clip = None
        current_state = "IDLE"
        current_hooks = []
        current_caption = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            # Check halt condition
            if self.halt_pattern.search(line_stripped):
                break
            
            # Check clip header
            clip_match = self.clip_header_pattern.match(line_stripped)
            if clip_match:
                # Save previous clip
                if current_clip:
                    if current_hooks:
                        current_clip.hook = current_hooks[0]  # Take first hook
                    if current_caption:
                        current_clip.caption = '\n'.join(current_caption)
                    clips.append(current_clip)
                    hooks_list.append(current_hooks)
                    captions_list.append('\n'.join(current_caption))
                
                # Start new clip
                clip_num = clip_match.group(1)
                clip_info = clip_match.group(2).strip()
                
                current_clip = ClipSegment(
                    start="",
                    end="",
                    title=clip_info or f"Klip_{clip_num}",
                    hook=None,
                    caption=None
                )
                current_hooks = []
                current_caption = []
                current_state = "META"
                continue
            
            if current_clip is None:
                continue
            
            # Parse timestamp
            time_match = self.time_pattern.search(line_stripped)
            if time_match and not current_clip.start:
                current_clip.start = time_match.group(1).strip()
                current_clip.end = time_match.group(2).strip()
                # Extract title dari sisa line
                remaining = line_stripped[time_match.end():].strip()
                if remaining and not remaining.startswith('|'):
                    remaining = remaining.lstrip('|').strip()
                    if remaining and len(remaining) > 2:
                        current_clip.title = remaining
                current_state = "TIMESTAMP"
                continue
            
            # Parse hooks
            if self.hook_pattern.search(line_stripped) or "hook" in line_stripped.lower():
                if "hook" in line_stripped.lower() and len(line_stripped) > 10:
                    # Clean hook text
                    hook_text = re.sub(r'^[-•*]\s*', '', line_stripped)
                    hook_text = re.sub(r'^\d+\.\s*', '', hook_text)
                    if len(hook_text) > 5 and len(hook_text) < 200:
                        current_hooks.append(hook_text)
                current_state = "HOOKS"
                continue
            
            # Parse caption/SEO
            if self.caption_pattern.search(line_stripped) or any(kw in line_stripped.lower() for kw in ['caption', 'seo', 'deskripsi', 'hashtag']):
                if not any(kw in line_stripped.lower() for kw in ['hook', 'hook']):
                    caption_text = line_stripped
                    if len(caption_text) > 10:
                        current_caption.append(caption_text)
                current_state = "SEO"
                continue
            
            # Collect additional info berdasarkan state
            if current_state == "HOOKS" and len(line_stripped) > 5:
                if not any(kw in line_stripped.lower() for kw in ['caption', 'seo', 'durasi', 'waktu']):
                    current_hooks.append(line_stripped)
            
            elif current_state == "SEO" and len(line_stripped) > 5:
                if not any(kw in line_stripped.lower() for kw in ['hook', 'clip', 'klip']):
                    current_caption.append(line_stripped)
        
        # Save last clip
        if current_clip:
            if current_hooks:
                current_clip.hook = current_hooks[0]
            if current_caption:
                current_clip.caption = '\n'.join(current_caption)
            clips.append(current_clip)
            hooks_list.append(current_hooks)
            captions_list.append('\n'.join(current_caption))
        
        return clips, hooks_list if hooks_list else None, captions_list if captions_list else None
    
    def _extract_clips_fallback(self, text: str) -> List[ClipSegment]:
        """
        Fallback: extract clips hanya dari timestamp pattern
        """
        clips = []
        
        for match in self.time_pattern.finditer(text):
            start = match.group(1)
            end = match.group(2)
            
            # Ambil text setelah timestamp sebagai title
            remaining = text[match.end():].split('\n')[0].strip()
            remaining = remaining.lstrip('|').strip()
            
            if remaining and len(remaining) > 2 and len(remaining) < 100:
                # Clean remaining dari pattern lain
                remaining = re.sub(r'^[-•*]\s*', '', remaining)
                remaining = re.sub(r'^\d+\.\s*', '', remaining)
                
                if not re.match(r'^\d{1,2}:\d{2}', remaining):  # Not another timestamp
                    clips.append(ClipSegment(
                        start=start,
                        end=end,
                        title=remaining[:80]  # Max 80 chars
                    ))
        
        return clips
    
    def to_dict(self, result: VideoAnalysis) -> Dict:
        """Convert VideoAnalysis ke dictionary untuk JSON"""
        return {
            'url': result.url,
            'title': result.title,
            'clips': [asdict(c) for c in result.clips],
            'hooks': result.hooks,
            'captions': result.captions
        }
    
    def save_to_file(self, result: VideoAnalysis, output_path: str):
        """Save parsed result ke JSON file"""
        import json
        data = self.to_dict(result)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Test module
if __name__ == "__main__":
    parser = AIParser()
    
    sample_text = """
    https://www.youtube.com/watch?v=dQw4w9WgXcQ
    Judul: Cara Trading Crypto Pemula
    
    KLIP [1]:
    00:00 - 00:30 | Intro yang menarik
    Hook: "Tahu gak sih 90% trader crypto rugi di tahun pertama?"
    Caption: #trading #crypto #bitcoin #tutorial
    
    KLIP [2]:
    01:15 - 02:00 | Tips penting memilih exchange
    Hook: "3 exchange ini paling aman untuk pemula!"
    Caption: Pilih exchange yang sudah teregulasi Bappebti
    
    KLIP [3]:
    03:45 - 04:30 | Cara setting stop loss
    Hook: "Stop loss wrong = auto cuan!"
    
    BAGIAN 2
    """
    
    result = parser.parse(sample_text)
    
    if result:
        print(f"✅ Parsed successfully!")
        print(f"URL: {result.url}")
        print(f"Title: {result.title}")
        print(f"Clips: {len(result.clips)}")
        for i, clip in enumerate(result.clips, 1):
            print(f"\n  [{i}] {clip.start} → {clip.end}")
            print(f"      Title: {clip.title}")
            if clip.hook:
                print(f"      Hook: {clip.hook}")
            if clip.caption:
                print(f"      Caption: {clip.caption[:50]}...")
    else:
        print("❌ Failed to parse")