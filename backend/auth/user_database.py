import psycopg2
import psycopg2.extras
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from .models import UserCreate, UserUpdate, UserInDB, UserStats
from .auth_utils import hash_password, verify_password

class UserDatabase:
    """User database operations"""
    
    def __init__(self, db_url: str = "postgresql://atsawin:***@localhost:5433/atsawin_ai"):
        self.db_url = db_url
        self.logger = logging.getLogger(__name__)
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def create_tables(self):
        """Create user tables"""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                # Users table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL,
                        role VARCHAR(20) NOT NULL DEFAULT 'user',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        is_active BOOLEAN DEFAULT TRUE,
                        last_login TIMESTAMP WITH TIME ZONE
                    )
                """)
                
                # Create indexes
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
                
                conn.commit()
                self.logger.info("User tables created successfully")
                
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to create tables: {e}")
            raise
        finally:
            conn.close()
    
    def create_user(self, user: UserCreate) -> UserInDB:
        """Create new user"""
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Check if user already exists
                cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                          (user.username, user.email))
                if cur.fetchone():
                    raise ValueError("User already exists")
                
                # Create user
                hashed_password = hash_password(user.password)
                cur.execute("""
                    INSERT INTO users (username, email, hashed_password, role)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, username, email, role, created_at, is_active, last_login
                """, (user.username, user.email, hashed_password, user.role.value))
                
                user_data = cur.fetchone()
                conn.commit()
                
                return UserInDB(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role'],
                    hashed_password=user_data['hashed_password'],
                    created_at=user_data['created_at'],
                    is_active=user_data['is_active'],
                    last_login=user_data['last_login']
                )
                
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to create user: {e}")
            raise
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT id, username, email, role, hashed_password, created_at, is_active, last_login
                    FROM users WHERE username = %s
                """, (username,))
                
                user_data = cur.fetchone()
                if not user_data:
                    return None
                
                return UserInDB(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role'],
                    hashed_password=user_data['hashed_password'],
                    created_at=user_data['created_at'],
                    is_active=user_data['is_active'],
                    last_login=user_data['last_login']
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            raise
        finally:
            conn.close()
    
    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT id, username, email, role, hashed_password, created_at, is_active, last_login
                    FROM users WHERE email = %s
                """, (email,))
                
                user_data = cur.fetchone()
                if not user_data:
                    return None
                
                return UserInDB(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role'],
                    hashed_password=user_data['hashed_password'],
                    created_at=user_data['created_at'],
                    is_active=user_data['is_active'],
                    last_login=user_data['last_login']
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            raise
        finally:
            conn.close()
    
    def update_user(self, username: str, user_update: UserUpdate) -> Optional[UserInDB]:
        """Update user information"""
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Build update query
                update_fields = []
                params = []
                
                if user_update.username is not None:
                    update_fields.append("username = %s")
                    params.append(user_update.username)
                
                if user_update.email is not None:
                    update_fields.append("email = %s")
                    params.append(user_update.email)
                
                if user_update.role is not None:
                    update_fields.append("role = %s")
                    params.append(user_update.role.value)
                
                if not update_fields:
                    return self.get_user_by_username(username)
                
                params.append(username)
                
                cur.execute(f"""
                    UPDATE users SET {', '.join(update_fields)}
                    WHERE username = %s
                    RETURNING id, username, email, role, created_at, is_active, last_login
                """, params)
                
                user_data = cur.fetchone()
                conn.commit()
                
                if not user_data:
                    return None
                
                return UserInDB(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role'],
                    hashed_password="",  # Don't return password
                    created_at=user_data['created_at'],
                    is_active=user_data['is_active'],
                    last_login=user_data['last_login']
                )
                
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to update user: {e}")
            raise
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET last_login = NOW()
                    WHERE id = %s
                """, (user.id,))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update last login: {e}")
        finally:
            conn.close()
        
        return user
    
    def get_user_stats(self, username: str) -> Optional[UserStats]:
        """Get user statistics"""
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get user info
                cur.execute("""
                    SELECT created_at, last_login FROM users WHERE username = %s
                """, (username,))
                
                user_info = cur.fetchone()
                if not user_info:
                    return None
                
                # Get task statistics (assuming tasks are tracked in memory system)
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks
                    FROM memory_entries 
                    WHERE key LIKE %s AND memory_type = 'user_task'
                """, (f"user:{username}:task%",))
                
                task_stats = cur.fetchone()
                
                return UserStats(
                    total_tasks=task_stats['total_tasks'] if task_stats else 0,
                    completed_tasks=task_stats['completed_tasks'] if task_stats else 0,
                    failed_tasks=task_stats['failed_tasks'] if task_stats else 0,
                    last_login=user_info['last_login'],
                    created_at=user_info['created_at']
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get user stats: {e}")
            raise
        finally:
            conn.close()
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List all users"""
        conn = self.get_db_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT id, username, email, role, created_at, is_active, last_login
                    FROM users
                    ORDER BY created_at DESC
                    OFFSET %s LIMIT %s
                """, (skip, limit))
                
                users = []
                for row in cur.fetchall():
                    users.append({
                        "id": row['id'],
                        "username": row['username'],
                        "email": row['email'],
                        "role": row['role'],
                        "created_at": row['created_at'],
                        "is_active": row['is_active'],
                        "last_login": row['last_login']
                    })
                
                return users
                
        except Exception as e:
            self.logger.error(f"Failed to list users: {e}")
            raise
        finally:
            conn.close()
    
    def deactivate_user(self, username: str) -> bool:
        """Deactivate user"""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET is_active = FALSE
                    WHERE username = %s
                """, (username,))
                
                rows_affected = cur.rowcount
                conn.commit()
                
                return rows_affected > 0
                
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to deactivate user: {e}")
            raise
        finally:
            conn.close()