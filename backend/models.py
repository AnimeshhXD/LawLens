from pydantic import BaseModel, EmailStr, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ClauseType(str, Enum):
    LIABILITY = "liability"
    INDEMNITY = "indemnity"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    PAYMENT = "payment"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    DISPUTE_RESOLUTION = "dispute_resolution"
    OTHER = "other"

# Request Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER
    
    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class DocumentUpload(BaseModel):
    filename: str
    
    @validator("filename")
    def validate_filename(cls, v):
        if not v or len(v) > 255:
            raise ValueError("Invalid filename")
        # Prevent path traversal
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Invalid filename")
        return v

class ClauseClassification(BaseModel):
    clause_type: ClauseType
    risk_score: float
    key_entities: List[str]
    obligations: List[str]
    confidence: float
    
    @validator("risk_score", "confidence")
    def validate_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        return v

class RiskFactor(BaseModel):
    category: str
    score: float
    description: str
    
    @validator("score")
    def validate_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        return v

class Recommendation(BaseModel):
    priority: RiskLevel
    action: str

class RiskAssessmentRequest(BaseModel):
    clauses: List[Dict[str, Any]]
    
    @validator("clauses")
    def validate_clauses(cls, v):
        if len(v) == 0:
            raise ValueError("At least one clause is required")
        if len(v) > 50:
            raise ValueError("Too many clauses (max 50)")
        return v

class RegulatoryChangeCreate(BaseModel):
    title: str
    description: str
    category: str
    effective_date: datetime
    impact_level: RiskLevel
    affected_industries: List[str]
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    
    @validator("title", "description")
    def validate_text_length(cls, v):
        if len(v) > 1000:
            raise ValueError("Text too long")
        return v

class ImpactAnalysisRequest(BaseModel):
    document_id: int
    regulatory_change_id: int

class SentimentAnalysisRequest(BaseModel):
    text: str
    
    @validator("text")
    def validate_text(cls, v):
        if len(v) > 10000:
            raise ValueError("Text too long")
        return v

# Response Models
class UserResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class ClauseResponse(BaseModel):
    id: int
    clause_type: ClauseType
    content: str
    risk_score: float
    extracted_at: datetime
    
    class Config:
        from_attributes = True

class RiskAssessmentResponse(BaseModel):
    id: int
    overall_score: float
    risk_factors: List[RiskFactor]
    recommendations: List[Recommendation]
    created_at: datetime
    
    class Config:
        from_attributes = True

class RegulatoryChangeResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    effective_date: datetime
    impact_level: RiskLevel
    affected_industries: List[str]
    
    class Config:
        from_attributes = True

class ImpactAnalysisResponse(BaseModel):
    id: int
    affected_clauses: List[int]
    compliance_cost_estimate: float
    penalty_exposure: float
    operational_friction_index: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReputationRiskResponse(BaseModel):
    id: int
    risk_score: float
    risk_category: str
    sentiment_score: float
    key_phrases: List[str]
    justification: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class RegulatoryImpactAnalysisRequest(BaseModel):
    old_text: str
    new_text: str
    
    @validator("old_text", "new_text")
    def validate_texts(cls, v):
        if not v or len(v) > 50000:
            raise ValueError("Text must be between 1 and 50000 characters")
        return v

# Secure Response Wrapper
class SecureResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime
    
    @validator("error")
    def sanitize_error(cls, v):
        if v:
            # Remove potential sensitive information
            import re
