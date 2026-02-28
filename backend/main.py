import logging
import os
import hashlib
import aiofiles
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from config import settings
from database import DatabaseManager, User, Document, Clause, RiskAssessment, RegulatoryChange, ImpactAnalysis, ReputationRisk
from models import *
from security import SecurityValidator, SecureResponse, RateLimiter
from engines import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI with security metadata
app = FastAPI(
    title="LawLens API",
    description="Legal Risk & Regulatory Intelligence Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.lawlens.com"]
)

# CORS middleware with strict origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize components
db_manager = DatabaseManager(settings.database_url)
security = SecurityValidator()
rate_limiter = RateLimiter()
security_scheme = HTTPBearer()

# Dependency to get database session
def get_db():
    return next(db_manager.get_db())

# Security dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    try:
        payload = security.verify_token(
            credentials.credentials, 
            settings.secret_key, 
            settings.jwt_algorithm
        )
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_admin_user(current_user: User = Depends(get_current_user)):
    """Get current admin user"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Utility functions
def create_secure_response(success: bool, data: Any = None, error: str = None) -> SecureResponse:
    """Create secure response"""
    return SecureResponse(
        success=success,
        data=data,
        error=error,
        timestamp=datetime.utcnow()
    )

async def validate_file_upload(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded file"""
    # Check file size
    if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
        return False, f"File too large (max {settings.max_file_size_mb}MB)"
    
    # Check MIME type
    if file.content_type not in settings.allowed_mime_types:
        return False, f"File type not allowed: {file.content_type}"
    
    # Check filename
    if not file.filename or ".." in file.filename or "/" in file.filename:
        return False, "Invalid filename"
    
    return True, "Valid"

# Authentication endpoints
@app.post("/api/auth/register", response_model=SecureResponse)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            return create_secure_response(False, error="User already exists")
        
        # Hash password
        hashed_password = security.hash_password(user_data.password)
        
        # Create user
        user = db_manager.create_user(
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role
        )
        
        return create_secure_response(True, {
            "user_id": user.id,
            "email": user.email,
            "role": user.role
        })
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return create_secure_response(False, error="Registration failed")

@app.post("/api/auth/login", response_model=SecureResponse)
@limiter.limit("10/minute")
async def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    try:
        # Get user
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user:
            return create_secure_response(False, error="Invalid credentials")
        
        # Verify password
        if not security.verify_password(user_data.password, user.hashed_password):
            return create_secure_response(False, error="Invalid credentials")
        
        # Create access token
        access_token = security.create_access_token(
            data={"sub": user.email},
            secret_key=settings.secret_key,
            algorithm=settings.jwt_algorithm,
            expires_delta=timedelta(minutes=settings.jwt_expiration_minutes)
        )
        
        return create_secure_response(True, {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return create_secure_response(False, error="Login failed")

@app.get("/api/auth/validate", response_model=SecureResponse)
@limiter.limit("30/minute")
async def validate_token(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Validate current user token"""
    try:
        return create_secure_response(True, {
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "role": current_user.role
            }
        })
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return create_secure_response(False, error="Token validation failed")

# Document endpoints
@app.post("/api/documents/upload", response_model=SecureResponse)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and analyze document"""
    try:
        # Validate file
        is_valid, message = await validate_file_upload(file)
        if not is_valid:
            return create_secure_response(False, error=message)
        
        # Read file content
        content = await file.read()
        
        # Validate content
        content_str = content.decode('utf-8', errors='ignore')
        is_valid, validation_message = security.validate_file_content(content_str, file.content_type)
        if not is_valid:
            return create_secure_response(False, error=validation_message)
        
        # Calculate content hash
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Create document record
        document = db_manager.create_document(
            filename=f"{datetime.utcnow().timestamp()}_{file.filename}",
            original_filename=file.filename,
            mime_type=file.content_type,
            file_size=len(content),
            content_hash=content_hash,
            user_id=current_user.id
        )
        
        # Extract and classify clauses
        clauses = await clause_engine.extract_and_classify_clauses(content, file.content_type)
        
        # Save clauses
        saved_clauses = db_manager.save_clauses(document.id, clauses)
        
        return create_secure_response(True, {
            "document_id": document.id,
            "filename": document.original_filename,
            "clauses_extracted": len(saved_clauses),
            "clauses": [
                {
                    "id": clause.id,
                    "type": clause.clause_type,
                    "content": clause.content[:200] + "...",
                    "risk_score": clause.risk_score
                }
                for clause in saved_clauses
            ]
        })
        
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        return create_secure_response(False, error="Document processing failed")

@app.get("/api/documents", response_model=SecureResponse)
@limiter.limit("30/minute")
async def get_documents(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user documents"""
    try:
        documents = db.query(Document).filter(Document.user_id == current_user.id).all()
        
        return create_secure_response(True, {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.original_filename,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "file_size": doc.file_size
                }
                for doc in documents
            ]
        })
        
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        return create_secure_response(False, error="Failed to retrieve documents")

# new endpoint for individual document metadata
@app.get("/api/documents/{document_id}", response_model=SecureResponse)
@limiter.limit("30/minute")
async def get_document(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single document by id"""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        if not document:
            return create_secure_response(False, error="Document not found")
        return create_secure_response(True, {
            "document": {
                "id": document.id,
                "filename": document.original_filename,
                "uploaded_at": document.uploaded_at.isoformat(),
                "file_size": document.file_size
            }
        })
    except Exception as e:
        logger.error(f"Get document error: {e}")
        return create_secure_response(False, error="Failed to retrieve document")

# Risk assessment endpoints
@app.post("/api/risk/assess/{document_id}", response_model=SecureResponse)
@limiter.limit("20/minute")
async def assess_risk(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assess risk for document"""
    try:
        # Get document and verify ownership
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            return create_secure_response(False, error="Document not found")
        
        # Get clauses
        clauses = db.query(Clause).filter(Clause.document_id == document_id).all()
        clause_data = [
            {
                "id": clause.id,
                "content": clause.content,
                "type": clause.clause_type,
                "risk_score": clause.risk_score
            }
            for clause in clauses
        ]
        
        # Assess risk
        risk_result = await risk_engine.assess_risk(clause_data)
        
        # Save risk assessment
        assessment = db_manager.create_risk_assessment(
            document_id=document_id,
            user_id=current_user.id,
            overall_score=risk_result["overall_risk_score"],
            risk_factors=risk_result["risk_factors"],
            recommendations=risk_result["recommendations"]
        )
        
        return create_secure_response(True, {
            "assessment_id": assessment.id,
            "overall_risk_score": risk_result["overall_risk_score"],
            "risk_factors": risk_result["risk_factors"],
            "recommendations": risk_result["recommendations"],
            "clause_scores": risk_result["clause_scores"]
        })
        
    except Exception as e:
        logger.error(f"Risk assessment error: {e}")
        return create_secure_response(False, error="Risk assessment failed")

# Regulatory simulation endpoints
@app.post("/api/regulatory/simulate/{document_id}", response_model=SecureResponse)
@limiter.limit("15/minute")
async def simulate_regulatory_impact(
    request: Request,
    document_id: int,
    regulatory_change: RegulatoryChangeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simulate regulatory impact on document"""
    try:
        # Get document and verify ownership
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            return create_secure_response(False, error="Document not found")
        
        # Get clauses
        clauses = db.query(Clause).filter(Clause.document_id == document_id).all()
        clause_data = [
            {
                "id": clause.id,
                "content": clause.content,
                "type": clause.clause_type,
                "risk_score": clause.risk_score
            }
            for clause in clauses
        ]
        
        # Simulate impact
        regulatory_data = {
            "id": 1,  # Mock ID
            "title": regulatory_change.title,
            "description": regulatory_change.description,
            "impact_level": regulatory_change.impact_level,
            "affected_industries": regulatory_change.affected_industries
        }
        
        impact_result = regulatory_engine.simulate_regulatory_impact(clause_data, regulatory_data)
        
        return create_secure_response(True, impact_result)
        
    except Exception as e:
        logger.error(f"Regulatory simulation error: {e}")
        return create_secure_response(False, error="Simulation failed")

# Reputation risk endpoints
@app.post("/api/reputation/analyze/{document_id}", response_model=SecureResponse)
@limiter.limit("15/minute")
async def analyze_reputation_risk(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze reputation risk for document"""
    try:
        # Get document and verify ownership
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            return create_secure_response(False, error="Document not found")
        
        # Get full document content
        clauses = db.query(Clause).filter(Clause.document_id == document_id).all()
        full_text = " ".join(clause.content for clause in clauses)
        
        # Analyze reputation risk
        reputation_result = await reputation_engine.analyze_reputation_risk(full_text)
        
        # Save reputation risk
        reputation_risk = ReputationRisk(
            document_id=document_id,
            risk_score=reputation_result["risk_score"],
            risk_category=", ".join(reputation_result["risk_categories"]),
            sentiment_score=reputation_result["sentiment_score"],
            key_phrases=json.dumps(reputation_result["key_phrases"]),
            justification=reputation_result["justification"]
        )
        db.add(reputation_risk)
        db.commit()
        
        return create_secure_response(True, reputation_result)
        
    except Exception as e:
        logger.error(f"Reputation analysis error: {e}")
        return create_secure_response(False, error="Reputation analysis failed")

# Impact analysis endpoints
@app.post("/api/impact/analyze/{document_id}", response_model=SecureResponse)
@limiter.limit("15/minute")
async def analyze_regulatory_diff(
    request: Request,
    document_id: int,
    impact_request: RegulatoryImpactAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze impact of regulatory changes"""
    try:
        # Get document and verify ownership
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            return create_secure_response(False, error="Document not found")
        
        # Get clauses
        clauses = db.query(Clause).filter(Clause.document_id == document_id).all()
        clause_data = [
            {
                "id": clause.id,
                "content": clause.content,
                "type": clause.clause_type,
                "risk_score": clause.risk_score
            }
            for clause in clauses
        ]
        
        # Analyze impact
        impact_result = impact_engine.analyze_regulatory_impact(clause_data, impact_request.old_text, impact_request.new_text)
        
        return create_secure_response(True, impact_result)
        
    except Exception as e:
        logger.error(f"Impact analysis error: {e}")
        return create_secure_response(False, error="Impact analysis failed")

# Health check endpoint
@app.get("/health", response_model=SecureResponse)
async def health_check():
    """Health check endpoint"""
    return create_secure_response(True, {"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return create_secure_response(False, error="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
