import asyncio
import json
import redis.asyncio as redis
import psycopg2
import psycopg2.extras
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib

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
    """Manages persistent memory using PostgreSQL and Redis"""
    
    def __init__(self, db_url: str = "postgresql://atsawin:password123@localhost:5433/atsawin_ai",
                 redis_url: str = "redis://localhost:6380"):
        self.db_url = db_url
        self.redis_url = redis_url
        self.redis_client = None
        self.db_conn = None
        self.logger = self._setup_logger()
        self._initialized = False
    
    def _setup_logger(self):
        logger = logging.getLogger("memory_manager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def initialize(self):
        """Initialize database and Redis connections"""
        try:
            # Initialize PostgreSQL
            self.db_conn = psycopg2.connect(self.db_url)
            self._create_tables()
            
            # Initialize Redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            self._initialized = True
            self.logger.info("Memory manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory manager: {str(e)}")
            raise
    
    def _create_tables(self):
        """Create necessary database tables"""
        with self.db_conn.cursor() as cur:
            # Memory entries table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id VARCHAR(255) PRIMARY KEY,
                    key VARCHAR(255) NOT NULL,
                    value TEXT NOT NULL,
                    memory_type VARCHAR(50) NOT NULL,
                    tags TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP WITH TIME ZONE
                )
            """)
            
            # Create indexes for better performance
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_entries_key ON memory_entries(key)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_entries_type ON memory_entries(memory_type)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_entries_created_at ON memory_entries(created_at)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_entries_expires_at ON memory_entries(expires_at)
            """)
            
            # Tag search index
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_entries_tags ON memory_entries USING gin(tags)
            """)
            
            self.db_conn.commit()
    
    def _generate_id(self, key: str, memory_type: str) -> str:
        """Generate unique ID for memory entry"""
        content = f"{key}:{memory_type}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    async def store_memory(self, key: str, value: Union[str, Dict, List], 
                          memory_type: str = "general", tags: List[str] = None,
                          metadata: Dict[str, None] = None, 
                          ttl_seconds: Optional[int] = None) -> str:
        """Store a memory entry"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate ID
            entry_id = self._generate_id(key, memory_type)
            
            # Prepare data
            if isinstance(value, (dict, list)):
                value_json = json.dumps(value, default=str)
            else:
                value_json = str(value)
            
            # Calculate expiration
            expires_at = None
            if ttl_seconds:
                expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
            
            # Create memory entry
            memory_entry = MemoryEntry(
                id=entry_id,
                key=key,
                value=value_json,
                memory_type=memory_type,
                tags=tags or [],
                metadata=metadata or {},
                created_at=datetime.now().isoformat(),
                expires_at=expires_at
            )
            
            # Store in PostgreSQL
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memory_entries 
                    (id, key, value, memory_type, tags, metadata, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        value = EXCLUDED.value,
                        tags = EXCLUDED.tags,
                        metadata = EXCLUDED.metadata,
                        expires_at = EXCLUDED.expires_at
                """, (
                    memory_entry.id,
                    memory_entry.key,
                    memory_entry.value,
                    memory_entry.memory_type,
                    memory_entry.tags,
                    json.dumps(memory_entry.metadata),
                    memory_entry.created_at,
                    memory_entry.expires_at
                ))
                
                self.db_conn.commit()
            
            # Cache in Redis
            await self._cache_memory(memory_entry)
            
            self.logger.info(f"Memory stored: {entry_id} - {key}")
            return entry_id
            
        except Exception as e:
            self.logger.error(f"Failed to store memory: {str(e)}")
            raise
    
    async def retrieve_memory(self, key: str, memory_type: str = None) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by key"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # First try Redis cache
            cached_entry = await self._get_cached_memory(key, memory_type)
            if cached_entry:
                await self._update_access_stats(cached_entry.id)
                return cached_entry
            
            # If not in cache, query database
            with self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                if memory_type:
                    cur.execute("""
                        SELECT * FROM memory_entries 
                        WHERE key = %s AND memory_type = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (key, memory_type))
                else:
                    cur.execute("""
                        SELECT * FROM memory_entries 
                        WHERE key = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (key,))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                # Convert to MemoryEntry
                memory_entry = MemoryEntry(
                    id=row['id'],
                    key=row['key'],
                    value=row['value'],
                    memory_type=row['memory_type'],
                    tags=row['tags'] or [],
                    metadata=row['metadata'] or {},
                    created_at=row['created_at'].isoformat(),
                    expires_at=row['expires_at'].isoformat() if row['expires_at'] else None,
                    access_count=row['access_count'],
                    last_accessed=row['last_accessed'].isoformat() if row['last_accessed'] else None
                )
                
                # Cache the result
                await self._cache_memory(memory_entry)
                
                # Update access stats
                await self._update_access_stats(memory_entry.id)
                
                return memory_entry
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve memory: {str(e)}")
            raise
    
    async def search_memories(self, query: str, memory_type: str = None, 
                            tags: List[str] = None, limit: int = 10) -> List[MemoryEntry]:
        """Search memories by various criteria"""
        if not self._initialized:
            await self.initialize()
        
        try:
            with self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                conditions = []
                params = []
                
                # Add conditions
                if memory_type:
                    conditions.append("memory_type = %s")
                    params.append(memory_type)
                
                if tags:
                    tag_conditions = []
                    for tag in tags:
                        tag_conditions.append(f"%s = ANY(tags)")
                        params.append(tag)
                    conditions.append(f"({' OR '.join(tag_conditions)})")
                
                # Add text search on key and value
                conditions.append("(key ILIKE %s OR value ILIKE %s)")
                params.extend([f"%{query}%", f"%{query}%"])
                
                # Build query
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                
                cur.execute(f"""
                    SELECT * FROM memory_entries 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s
                """, params + [limit])
                
                rows = cur.fetchall()
                memories = []
                
                for row in rows:
                    memory_entry = MemoryEntry(
                        id=row['id'],
                        key=row['key'],
                        value=row['value'],
                        memory_type=row['memory_type'],
                        tags=row['tags'] or [],
                        metadata=row['metadata'] or {},
                        created_at=row['created_at'].isoformat(),
                        expires_at=row['expires_at'].isoformat() if row['expires_at'] else None,
                        access_count=row['access_count'],
                        last_accessed=row['last_accessed'].isoformat() if row['last_accessed'] else None
                    )
                    memories.append(memory_entry)
                
                return memories
                
        except Exception as e:
            self.logger.error(f"Failed to search memories: {str(e)}")
            raise
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            with self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Total entries
                cur.execute("SELECT COUNT(*) as total FROM memory_entries")
                total_entries = cur.fetchone()['total']
                
                # Entries by type
                cur.execute("""
                    SELECT memory_type, COUNT(*) as count 
                    FROM memory_entries 
                    GROUP BY memory_type
                """)
                by_type = dict(cur.fetchall())
                
                # Recent entries (last 24 hours)
                cur.execute("""
                    SELECT COUNT(*) as recent 
                    FROM memory_entries 
                    WHERE created_at > NOW() - INTERVAL '1 day'
                """)
                recent_entries = cur.fetchone()['recent']
                
                # Total memory usage
                cur.execute("""
                    SELECT SUM(LENGTH(value)) as total_size 
                    FROM memory_entries
                """)
                total_size = cur.fetchone()['total_size'] or 0
                
                return {
                    "total_entries": total_entries,
                    "by_type": by_type,
                    "recent_entries": recent_entries,
                    "total_size_bytes": total_size,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get memory stats: {str(e)}")
            raise
    
    async def cleanup_expired_memories(self):
        """Clean up expired memory entries"""
        if not self._initialized:
            await self.initialize()
        
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM memory_entries 
                    WHERE expires_at IS NOT NULL AND expires_at < NOW()
                """)
                
                deleted_count = cur.rowcount
                self.db_conn.commit()
                
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} expired memories")
                
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired memories: {str(e)}")
            raise
    
    async def _cache_memory(self, memory_entry: MemoryEntry):
        """Cache memory entry in Redis"""
        try:
            cache_key = f"memory:{memory_entry.key}:{memory_entry.memory_type}"
            cache_data = {
                "id": memory_entry.id,
                "value": memory_entry.value,
                "memory_type": memory_entry.memory_type,
                "tags": memory_entry.tags,
                "metadata": memory_entry.metadata,
                "created_at": memory_entry.created_at,
                "expires_at": memory_entry.expires_at
            }
            
            await self.redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                json.dumps(cache_data, default=str)
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to cache memory: {str(e)}")
    
    async def _get_cached_memory(self, key: str, memory_type: str = None) -> Optional[MemoryEntry]:
        """Get cached memory entry"""
        try:
            if memory_type:
                cache_key = f"memory:{key}:{memory_type}"
            else:
                # Try to find any cached version
                patterns = await self.redis_client.keys(f"memory:{key}:*")
                if not patterns:
                    return None
                cache_key = patterns[0]
            
            cached_data = await self.redis_client.get(cache_key)
            if not cached_data:
                return None
            
            data = json.loads(cached_data)
            return MemoryEntry(
                id=data['id'],
                key=key,
                value=data['value'],
                memory_type=data['memory_type'],
                tags=data['tags'],
                metadata=data['metadata'],
                created_at=data['created_at'],
                expires_at=data['expires_at']
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to get cached memory: {str(e)}")
            return None
    
    async def _update_access_stats(self, entry_id: str):
        """Update access statistics for a memory entry"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE memory_entries 
                    SET access_count = access_count + 1, 
                        last_accessed = NOW()
                    WHERE id = %s
                """, (entry_id,))
                
                self.db_conn.commit()
                
        except Exception as e:
            self.logger.warning(f"Failed to update access stats: {str(e)}")

# Global instance
memory_manager = PersistentMemoryManager()