"""
Authentication service for CallPilot.

Handles:
- Google OAuth authentication flow
- JWT token generation and validation
- User session management
- OAuth token storage and refresh
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from src import config
from src import database
from colorama import Fore, init

init(autoreset=True)

OAUTH_USERINFO_API_NAME = "oauth2"
OAUTH_USERINFO_API_VERSION = "v2"

# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Claims to include in token (e.g., {"user_id": "user_123"})
        expires_delta: Token expiration time (defaults to config)

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        config.SECRET_KEY,
        algorithm=config.ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User ID for the token

    Returns:
        str: Encoded JWT refresh token
    """
    data = {"user_id": user_id, "type": "refresh"}
    expire = datetime.utcnow() + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire})

    encoded_jwt = jwt.encode(
        data,
        config.SECRET_KEY,
        algorithm=config.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        dict: Token claims if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM]
        )
        return payload
    except JWTError as e:
        if config.DEBUG:
            print(f"{Fore.YELLOW}[DEBUG] Token verification failed: {e}")
        return None


# ============================================================================
# GOOGLE OAUTH FLOW
# ============================================================================

def get_google_oauth_url() -> tuple[str, str]:
    """
    Generate Google OAuth authorization URL.

    Returns:
        tuple: (authorization_url, state_token)
    """
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_secrets_file(
        config.GOOGLE_CREDENTIALS_PATH,
        scopes=config.GOOGLE_OAUTH_SCOPES,
        redirect_uri=f"{config.API_BASE_URL}/api/auth/google/callback"
    )

    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")

    return auth_url, state


def exchange_oauth_code_for_token(code: str, state: str) -> Optional[Dict[str, Any]]:
    """
    Exchange Google OAuth authorization code for access token.

    Args:
        code: Authorization code from Google
        state: State token from authorization URL

    Returns:
        dict: Token data with access_token, refresh_token, etc.
    """
    try:
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_secrets_file(
            config.GOOGLE_CREDENTIALS_PATH,
            scopes=config.GOOGLE_OAUTH_SCOPES,
            redirect_uri=f"{config.API_BASE_URL}/api/auth/google/callback",
            state=state
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Extract token data
        token_data = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }

        return token_data

    except Exception as e:
        error_msg = f"Failed to exchange OAuth code: {str(e)}"
        print(f"{Fore.RED}❌ {error_msg}")
        return None


def get_user_info_from_google(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Get user info from Google using access token.

    Args:
        access_token: Google OAuth access token

    Returns:
        dict: User info (email, name, picture, etc.)
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        credentials = Credentials(token=access_token)
        request = Request()

        from googleapiclient.discovery import build

        service = build(OAUTH_USERINFO_API_NAME, OAUTH_USERINFO_API_VERSION, credentials=credentials)
        user_info = service.userinfo().get().execute()

        return user_info

    except Exception as e:
        error_msg = f"Failed to get user info from Google: {str(e)}"
        print(f"{Fore.RED}❌ {error_msg}")
        return None


# ============================================================================
# USER MANAGEMENT
# ============================================================================

def create_or_update_user(
    db: Session,
    email: str,
    name: str,
    oauth_token_data: Dict[str, Any]
) -> Optional[database.User]:
    """
    Create or update user with Google OAuth token.

    Args:
        db: Database session
        email: User email
        name: User name
        oauth_token_data: Token data from Google OAuth

    Returns:
        User: Created or updated user object
    """
    try:
        # Check if user exists
        user = db.query(database.User).filter(
            database.User.email == email
        ).first()

        if user:
            # Update existing user
            user.name = name
            user.google_oauth_token = json.dumps(oauth_token_data)
            user.google_refresh_token = oauth_token_data.get("refresh_token")
            if oauth_token_data.get("expiry"):
                user.google_token_expiry = datetime.fromisoformat(
                    oauth_token_data["expiry"]
                )
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            user = database.User(
                id=user_id,
                email=email,
                name=name,
                google_oauth_token=json.dumps(oauth_token_data),
                google_refresh_token=oauth_token_data.get("refresh_token"),
                timezone=config.DOCTOR_TIMEZONE
            )
            if oauth_token_data.get("expiry"):
                user.google_token_expiry = datetime.fromisoformat(
                    oauth_token_data["expiry"]
                )
            db.add(user)

        db.commit()
        db.refresh(user)

        if config.DEBUG:
            print(f"{Fore.CYAN}[DEBUG] User {email} created/updated: {user.id}")

        return user

    except Exception as e:
        error_msg = f"Failed to create/update user: {str(e)}"
        print(f"{Fore.RED}❌ {error_msg}")
        db.rollback()
        return None


def get_user_by_id(db: Session, user_id: str) -> Optional[database.User]:
    """Get user by ID"""
    return db.query(database.User).filter(
        database.User.id == user_id
    ).first()


def get_user_by_email(db: Session, email: str) -> Optional[database.User]:
    """Get user by email"""
    return db.query(database.User).filter(
        database.User.email == email
    ).first()


# ============================================================================
# OAUTH TOKEN MANAGEMENT
# ============================================================================

def get_user_oauth_token(db: Session, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's Google OAuth token.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        dict: OAuth token data
    """
    user = get_user_by_id(db, user_id)
    if not user or not user.google_oauth_token:
        return None

    try:
        token_data = json.loads(user.google_oauth_token)

        # Check if token is expired and refresh if needed
        if user.google_token_expiry and datetime.utcnow() >= user.google_token_expiry:
            # Token is expired, attempt refresh
            refreshed = refresh_user_oauth_token(db, user_id)
            if refreshed:
                token_data = json.loads(user.google_oauth_token)
            else:
                return None

        return token_data

    except json.JSONDecodeError:
        return None


def refresh_user_oauth_token(db: Session, user_id: str) -> bool:
    """
    Refresh user's Google OAuth token using refresh token.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.service_account import Credentials as SACredentials

        user = get_user_by_id(db, user_id)
        if not user or not user.google_refresh_token:
            return False

        # Load client secrets to get token_uri
        with open(config.GOOGLE_CREDENTIALS_PATH, "r") as f:
            client_secrets = json.load(f)

        token_uri = client_secrets.get("token_uri", "https://oauth2.googleapis.com/token")

        # Refresh the token
        from google.oauth2.credentials import Credentials

        credentials = Credentials(
            token=None,
            refresh_token=user.google_refresh_token,
            token_uri=token_uri,
            client_id=client_secrets.get("client_id"),
            client_secret=client_secrets.get("client_secret")
        )

        request = Request()
        credentials.refresh(request)

        # Update user with new token
        token_data = {
            "access_token": credentials.token,
            "refresh_token": user.google_refresh_token,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
            "token_uri": token_uri,
            "client_id": client_secrets.get("client_id"),
            "client_secret": client_secrets.get("client_secret"),
            "scopes": credentials.scopes
        }

        user.google_oauth_token = json.dumps(token_data)
        user.google_token_expiry = credentials.expiry
        user.updated_at = datetime.utcnow()
        db.commit()

        if config.DEBUG:
            print(f"{Fore.CYAN}[DEBUG] OAuth token refreshed for user {user_id}")

        return True

    except Exception as e:
        error_msg = f"Failed to refresh OAuth token: {str(e)}"
        print(f"{Fore.RED}❌ {error_msg}")
        return False


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def create_session(db: Session, user_id: str) -> Optional[database.UserSession]:
    """
    Create a new user session with tokens.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        UserSession: Created session object
    """
    try:
        session_id = f"sess_{uuid.uuid4().hex[:20]}"

        # Create JWT tokens
        access_token = create_access_token({"user_id": user_id})
        refresh_token = create_refresh_token(user_id)

        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(
            minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        # Create session record
        session = database.UserSession(
            id=session_id,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        if config.DEBUG:
            print(f"{Fore.CYAN}[DEBUG] Session created for user {user_id}: {session_id}")

        return session

    except Exception as e:
        error_msg = f"Failed to create session: {str(e)}"
        print(f"{Fore.RED}❌ {error_msg}")
        db.rollback()
        return None


def get_session(db: Session, session_id: str) -> Optional[database.UserSession]:
    """Get active session"""
    return db.query(database.UserSession).filter(
        database.UserSession.id == session_id,
        database.UserSession.is_active == True,
        database.UserSession.expires_at > datetime.utcnow()
    ).first()


def invalidate_session(db: Session, session_id: str) -> bool:
    """Invalidate a session"""
    try:
        session = get_session(db, session_id)
        if session:
            session.is_active = False
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to invalidate session: {str(e)}")
        return False
