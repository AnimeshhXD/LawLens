import re
import hashlib
import hmac
import bleach
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel, validator

# Password hashing
# we will use the bcrypt module directly to avoid passlib backend issues
try:
    import bcrypt as _bcrypt
except ImportError:
    _bcrypt = None

# keep passlib context as fallback for compatibility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Prompt injection detection patterns
PROMPT_INJECTION_PATTERNS = [
    r"(?i)(ignore|forget|disregard).*(previous|above|earlier).*(instruction|prompt|rule)",
    r"(?i)(instead|rather|alternatively).*(do|execute|perform)",
    r"(?i)(system|admin|root).*(access|privilege|override)",
    r"(?i)(jailbreak|escape|bypass).*(restriction|limit|filter)",
    r"(?i)(act|behave|pretend).*(as|like).*(different|another)",
    r"(?i)(translate|convert|transform).*(to|into).*(json|code|script)",
    r"(?i)(execute|run|eval).*(this|the).*(code|script|command)",
    r"(?i)(show|display|reveal).*(system|internal|hidden)",
    r"(?i)(new|different|changed).*(instruction|prompt|rule)",
    r"(?i)(override|replace|substitute).*(previous|above|earlier)",
]

# XSS patterns
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>",
    r"<object[^>]*>",
    r"<embed[^>]*>",
    r"<link[^>]*>",
    r"<meta[^>]*>",
]

class SecurityValidator:
    @staticmethod
    def detect_prompt_injection(text: str) -> tuple[bool, List[str]]:
        """Detect potential prompt injection attempts"""
        detected_patterns = []
        
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text):
                detected_patterns.append(pattern)
        
        # Check for excessive special characters (potential encoding attacks)
        special_char_ratio = len(re.findall(r'[^\w\s]', text)) / max(len(text), 1)
        if special_char_ratio > 0.3:
            detected_patterns.append("High special character ratio")
        
        # Check for base64 encoding (potential payload hiding)
        base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
        if re.search(base64_pattern, text):
            detected_patterns.append("Potential base64 encoded content")
        
        return len(detected_patterns) > 0, detected_patterns
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        
        # Truncate if too long
        text = text[:max_length]
        
        # Remove HTML tags
        text = bleach.clean(text, tags=[], strip=True)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def validate_file_content(content: str, mime_type: str) -> tuple[bool, str]:
        """Validate file content for security threats"""
        # Check for suspicious content
        suspicious_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'<?php',
            r'<%',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"Suspicious content detected: {pattern}"
        
        # Check file size
        if len(content) > 10 * 1024 * 1024:  # 10MB
            return False, "File too large"
        
        return True, "Valid"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt -- prefer direct bcrypt if available."""
        if _bcrypt:
            # bcrypt requires bytes
            hashed = _bcrypt.hashpw(password.encode('utf-8'), _bcrypt.gensalt())
            return hashed.decode('utf-8')
        # fallback to passlib if bcrypt module missing
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            if _bcrypt:
                return _bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            # log error and return False to avoid leaking details
            logging.getLogger(__name__).error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def create_access_token(data: dict, secret_key: str, algorithm: str, expires_delta: timedelta) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, secret_key, algorithm=algorithm)
    
    @staticmethod
    def verify_token(token: str, secret_key: str, algorithm: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

class SecureResponse(BaseModel):
    """Secure response model that prevents data leakage"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime
    
    @validator("error")
    def validate_error(cls, v):
        # Sanitize error messages to prevent information disclosure
        if v:
            # Remove potential stack traces or system paths
            v = re.sub(r'File ".*?"', 'File "[REDACTED]"', v)
            v = re.sub(r'line \d+', 'line [REDACTED]', v)
            v = re.sub(r'\b(?:0x)?[a-f0-9]{8,}\b', '[HEX_REDACTED]', v)
        return v

class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).seconds < window
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
