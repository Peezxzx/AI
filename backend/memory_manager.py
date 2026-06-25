import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib

# Try to import Redis/PostgreSQL, fall back to in-memory
try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import psycopg2
    import psycopg2.extras
    HAS_PG = True
except ImportError:
    HAS_PG = False

@dataclass
class MemoryEntry:
    id: str
    key: str
    value: Union[str, Dict, List]
    memory_type: str
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: str
    expires_at: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[str] = None

class PersistentMemoryManager:
    """Manages persistent memory using PostgreSQL and Redis, falls back to in-memory on Windows"""
    
    def __init__(self, db_url: str = None, redis_url: str = None):
        self.db_url = db_url or os.environ.get("DATABASE_URL", "")
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "")
        self.redis_client = None
        self.db_conn = None
        self.logger = self._setup_logger()
        self._initialized = False
        self._memory_store: Dict[str, MemoryEntry] = {}  # In-memory fallback
        self._use_inmemory = not HAS_PG or not HAS_REDIS
    
    def _setup_logger(self):
        logger = logging.getLogger("memory_manager")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    async def initialize(self):
        """Initialize memory backend"""
        try:
            if self._use_inmemory:
                self._initialized = True
                self.logger.info("Memory manager initialized (in-memory mode for Windows)")
                return
            
            # Try PostgreSQL
            if HAS_PG and self.db_url and "postgresql" in self.db_url:
                self.db_conn = psycopg2.connect(self.db_url)
                self._create_tables()
            
            # Try Redis
            if HAS_REDIS and self.redis_url and self.redis_url != "memory://":
                self.redis_client = redis.from_url(self.redis_url)
                await self.redis_client.ping()
            
            self._initialized = True
            self.logger.info("Memory manager initialized (PostgreSQL + Redis)")
            
        except Exception as e:
            self.logger.warning(f"DB init failed ({e}), falling back to in-memory")
            self._use_inmemory = True
            self._initialized = True
    
    def _create_tables(self):
        if not self.db_conn:
            return
        with self.db_conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id VARCHAR(255) PRIMARY KEY, key VARCHAR(255) NOT NULL,
                    value TEXT NOT NULL, memory_type VARCHAR(50) NOT NULL,
                    tags TEXT[], metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP WITH TIME ZONE
                )
            """)
            self.db_conn.commit()
    
    def _generate_id(self, key: str, memory_type: str) -> str:
        content = f"{key}:{memory_type}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    async def store_memory(self, key, value, memory_type="general", tags=None, metadata=None, ttl_seconds=None):
        if not self._initialized:
            await self.initialize()
        entry_id = self._generate_id(key, memory_type)
        value_json = json.dumps(value, default=str) if isinstance(value, (dict, list)) else str(value)
        expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat() if ttl_seconds else None
        entry = MemoryEntry(id=entry_id, key=key, value=value_json, memory_type=memory_type,
                            tags=tags or [], metadata=metadata or {},
                            created_at=datetime.now().isoformat(), expires_at=expires_at)
        if self._use_inmemory:
            self._memory_store[f"{key}:{memory_type}"] = entry
        elif self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO memory_entries (id,key,value,memory_type,tags,metadata,created_at,expires_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (id) DO UPDATE SET value=EXCLUDED.value, tags=EXCLUDED.tags
                    """, (entry.id, entry.key, entry.value, entry.memory_type, entry.tags,
                          json.dumps(entry.metadata), entry.created_at, entry.expires_at))
                    self.db_conn.commit()
            except Exception as e:
                self.logger.warning(f"PG store failed: {e}, using in-memory")
                self._memory_store[f"{key}:{memory_type}"] = entry
        self.logger.info(f"Memory stored: {entry_id} - {key}")
        return entry_id
    
    async def retrieve_memory(self, key, memory_type=None):
        if not self._initialized:
            await self.initialize()
        if self._use_inmemory:
            if memory_type:
                return self._memory_store.get(f"{key}:{memory_type}")
            for k, v in self._memory_store.items():
                if k.startswith(f"{key}:"):
                    return v
            return None
        # PG fallback
        if self.db_conn:
            try:
                with self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    if memory_type:
                        cur.execute("SELECT * FROM memory_entries WHERE key=%s AND memory_type=%s ORDER BY created_at DESC LIMIT 1", (key, memory_type))
                    else:
                        cur.execute("SELECT * FROM memory_entries WHERE key=%s ORDER BY created_at DESC LIMIT 1", (key,))
                    row = cur.fetchone()
                    if row:
                        return MemoryEntry(id=row['id'], key=row['key'], value=row['value'],
                                           memory_type=row['memory_type'], tags=row['tags'] or [],
                                           metadata=row['metadata'] or {}, created_at=str(row['created_at']),
                                           expires_at=str(row['expires_at']) if row['expires_at'] else None)
            except Exception as e:
                self.logger.warning(f"PG retrieve failed: {e}")
        return None
    
    async def search_memories(self, query, memory_type=None, tags=None, limit=10):
        if not self._initialized:
            await self.initialize()
        if self._use_inmemory:
            results = []
            for k, v in self._memory_store.items():
                if memory_type and v.memory_type != memory_type:
                    continue
                if query.lower() in v.key.lower() or query.lower() in str(v.value).lower():
                    results.append(v)
            return results[:limit]
        return []
    
    async def get_memory_stats(self):
        if self._use_inmemory:
            return {
                "total_entries": len(self._memory_store),
                "by_type": {},
                "recent_entries": len(self._memory_store),
                "total_size_bytes": sum(len(str(v.value)) for v in self._memory_store.values()),
                "timestamp": datetime.now().isoformat(),
                "mode": "in-memory"
            }
        return {"total_entries": 0, "mode": "empty"}
    
    async def cleanup_expired_memories(self):
        if self._use_inmemory:
            now = datetime.now().isoformat()
            expired = [k for k, v in self._memory_store.items() if v.expires_at and v.expires_at < now]
            for k in expired:
                del self._memory_store[k]
            return len(expired)
        return 0

# Global instance
memory_manager = PersistentMemoryManager()