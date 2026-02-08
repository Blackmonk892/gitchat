import sqlite3
import hashlib
from pathlib import Path
from typing import Optional, Dict

class StateManager:
    def __init__(self, db_path: str = ".codebase_index.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_registry (
                filepath TEXT PRIMARY KEY,
                file_hash TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def calculate_hash(self, file_path: Path) -> str:
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.reaf(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except FileNotFoundError:
            return ""
        
    def should_process(self, file_path: str, current_hash: str) -> bool:
        self.cursor.execute("SELECT file_hash FROM file_registry WHERE filepath = ?", (file_path,))
        result = self.cursor.fetchone()

        if result is None:
            return True  
        return result[0] != current_hash
    
    def update_registry(self, file_path: str, new_hash: str):
        self.cursor.execute("""
            INSERT INTO file_registry (filepath, file_hash)
            VALUES (?, ?)
            ON CONFLICT(filepath) DO UPDATE SET
            file_hash = excluded.file_hash,
            last_updated = CURRENT_TIMESTAMP
        """, (file_path, new_hash))
        self.conn.commit()

    def get_all_indexed_files(self)-> set:
        self.cursor.execute("SELECT filepath FROM file_registry")
        return {row[0] for row in self.cursor.fetchall()}
    
    def remove_files(self, file_paths: list):
        if not file_paths: return
        self.cursor.executemany("DELETE FROM file_registry WHERE filepath = ?", [(fp,) for fp in file_paths])
        self.conn.commit()

    def close(self):
        self.conn.close()