from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from typing import Dict, Any, List
import logging
from .models import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, 
    Token, RefreshTokenRequest, UserStats
)
from .auth_utils import (
    create_access_token, create_refresh_token, verify_token,
    admin_required, trader_required, user_required
)
from .user_database import UserDatabase

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Initialize database
user_db = UserDatabase()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    try:
        token_data = verify_token(credentials.credentials)
        username = token_data.get("sub")
        
        # Get user from database
        user = user_db.get_user_by_username(username)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register new user"""
    try:
        created_user = user_db.create_user(user)
        return UserResponse(
            id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            role=created_user.role,
            created_at=created_user.created_at,
            is_active=created_user.is_active
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )

@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest):
    """User login"""
    try:
        user = user_db.authenticate_user(login_request.username, login_request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        token_data = verify_token(refresh_request.refresh_token, token_type="refresh")
        username = token_data.get("sub")
        
        # Verify user still exists and is active
        user = user_db.get_user_by_username(username)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        access_token = create_access_token(data={"sub": username})
        refresh_token = create_refresh_token(data={"sub": username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user statistics"""
    try:
        stats = user_db.get_user_stats(current_user["username"])
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update current user information"""
    try:
        updated_user = user_db.update_user(current_user["username"], user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            role=updated_user.role,
            created_at=updated_user.created_at,
            is_active=updated_user.is_active
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.get("/users", response_model=List[Dict[str, Any]])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(admin_required)
):
    """List all users (admin only)"""
    try:
        users = user_db.list_users(skip=skip, limit=limit)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )

@router.get("/users/{username}", response_model=Dict[str, Any])
async def get_user_by_username(
    username: str,
    current_user: Dict[str, Any] = Depends(admin_required)
):
    """Get user by username (admin only)"""
    try:
        user = user_db.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
            "is_active": user.is_active,
            "last_login": user.last_login
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )

@router.put("/users/{username}/deactivate", response_model=Dict[str, Any])
async def deactivate_user(
    username: str,
    current_user: Dict[str, Any] = Depends(admin_required)
):
    """Deactivate user (admin only)"""
    try:
        success = user_db.deactivate_user(username)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )

# Initialize tables on import
try:
    user_db.create_tables()
    logging.info("Auth tables initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize auth tables: {e}")