"""Knowledge storage module using user home directory for data persistence."""

import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import contextmanager
import fcntl
import os


class KnowledgeStorage:
    """Thread-safe knowledge storage with automatic tagging."""

    def __init__(self):
        # Use user home directory to avoid permission issues
        self.data_dir = Path.home() / ".knowledge-vault"
        self.data_file = self.data_dir / "knowledge.jsonl"
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self.data_file.touch()

    @contextmanager
    def file_lock(self, mode="r"):
        """Thread-safe file operations with locking."""
        with open(self.data_file, mode, encoding="utf-8") as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                yield f
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def store(
        self, content: str, title: str = "", tags: str = "", auto_tag: bool = True
    ) -> Dict:
        """Store a knowledge record."""
        record_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Process tags
        manual_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        suggested_tags = self._auto_suggest_tags(content, title) if auto_tag else []
        all_tags = list(set(manual_tags + suggested_tags))

        # Auto-generate title if not provided
        if not title.strip():
            title = self._generate_title(content)

        record = {
            "id": record_id,
            "timestamp": timestamp,
            "title": title.strip(),
            "content": content.strip(),
            "tags": all_tags,
        }

        # Thread-safe write operation
        success = self._safe_append_record(record)
        if not success:
            raise Exception("Storage failed, please try again")

        return {"id": record_id, "title": title, "tags": all_tags}

    def _generate_title(self, content: str) -> str:
        """Auto-generate title from content."""
        title = content[:50].strip()

        # Try to end at sentence boundaries
        for delimiter in ["。", ".", "?", "？", "!", "！"]:
            pos = title.find(delimiter)
            if pos > 10:  # Ensure title isn't too short
                title = content[: pos + 1]
                break

        if len(content) > len(title):
            title += "..."
        return title

    def _auto_suggest_tags(self, content: str, title: str = "") -> List[str]:
        """Auto-suggest tags based on content analysis."""
        text = f"{title} {content}".lower()

        # Simple keyword-based tagging
        tag_keywords = {
            "技术": ["技术", "编程", "代码", "api", "算法", "数据", "开发"],
            "工作": ["工作", "项目", "会议", "任务", "计划", "deadline"],
            "学习": ["学习", "教程", "笔记", "知识", "文档", "课程"],
            "想法": ["想法", "思考", "观点", "感悟", "心得", "反思"],
            "生活": ["生活", "日常", "个人", "健康", "休闲", "娱乐"],
        }

        suggested = []
        for tag, keywords in tag_keywords.items():
            if any(keyword in text for keyword in keywords):
                suggested.append(tag)

        return suggested[:3]  # Limit to 3 suggestions

    def _safe_append_record(self, record: Dict) -> bool:
        """Thread-safe record appending with retry logic."""
        max_retries = 3
        for i in range(max_retries):
            try:
                with self.file_lock("a") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                return True
            except Exception:
                if i == max_retries - 1:
                    return False
                time.sleep(0.1 * (i + 1))  # Exponential backoff
        return False

    def get_all_records(self) -> List[Dict]:
        """Get all knowledge records."""
        records = []
        try:
            with self.file_lock("r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            records.append(record)
                        except json.JSONDecodeError:
                            continue  # Skip corrupted lines
        except FileNotFoundError:
            pass
        return records

    def get_by_id(self, record_id: str) -> Optional[Dict]:
        """Get record by ID."""
        for record in self.get_all_records():
            if record.get("id") == record_id:
                return record
        return None

    def search_by_tags(self, tags: List[str], limit: int = 20) -> List[Dict]:
        """Search records by tags."""
        records = self.get_all_records()
        matching = []

        for record in records:
            record_tags = record.get("tags", [])
            if any(tag.lower() in [t.lower() for t in record_tags] for tag in tags):
                matching.append(record)

        # Sort by timestamp (newest first)
        matching.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return matching[:limit]

    def get_stats(self) -> Dict:
        """Get storage statistics."""
        records = self.get_all_records()
        all_tags = []
        for record in records:
            all_tags.extend(record.get("tags", []))

        from collections import Counter

        tag_counts = Counter(all_tags)

        return {
            "total_records": len(records),
            "total_tags": len(set(all_tags)),
            "top_tags": dict(tag_counts.most_common(10)),
            "data_location": str(self.data_file),
        }
