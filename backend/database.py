from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
from typing import Dict, Any

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="owner")
    risk_assessments = relationship("RiskAssessment", back_populates="user")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_hash = Column(String, nullable=False)  # SHA-256 hash
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    clauses = relationship("Clause", back_populates="document")
    risk_assessments = relationship("RiskAssessment", back_populates="document")

class Clause(Base):
    __tablename__ = "clauses"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    clause_type = Column(String, nullable=False)  # liability, indemnity, termination, etc.
    content = Column(Text, nullable=False)
    risk_score = Column(Float, default=0.0)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="clauses")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    risk_factors = Column(Text)  # JSON string
    recommendations = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="risk_assessments")
    user = relationship("User", back_populates="risk_assessments")

class RegulatoryChange(Base):
    __tablename__ = "regulatory_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # privacy, employment, financial, etc.
    effective_date = Column(DateTime, nullable=False)
    impact_level = Column(String, nullable=False)  # low, medium, high, critical
    affected_industries = Column(Text)  # JSON array
    old_text = Column(Text)
    new_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class ImpactAnalysis(Base):
    __tablename__ = "impact_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    regulatory_change_id = Column(Integer, ForeignKey("regulatory_changes.id"), nullable=False)
    affected_clauses = Column(Text)  # JSON array of clause IDs
    compliance_cost_estimate = Column(Float)
    penalty_exposure = Column(Float)
    operational_friction_index = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class ReputationRisk(Base):
    __tablename__ = "reputation_risks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_category = Column(String, nullable=False)  # environmental, social, governance, etc.
    sentiment_score = Column(Float)
    key_phrases = Column(Text)  # JSON array
    justification = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def create_user(self, email: str, hashed_password: str, role: str = "user") -> User:
        db = self.SessionLocal()
        try:
            user = User(email=email, hashed_password=hashed_password, role=role)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()
    
    def get_user_by_email(self, email: str) -> User:
        db = self.SessionLocal()
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()
    
    def create_document(self, filename: str, original_filename: str, mime_type: str, 
                       file_size: int, content_hash: str, user_id: int) -> Document:
        db = self.SessionLocal()
        try:
            document = Document(
                filename=filename,
                original_filename=original_filename,
                mime_type=mime_type,
                file_size=file_size,
                content_hash=content_hash,
                user_id=user_id
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        finally:
            db.close()
    
    def save_clauses(self, document_id: int, clauses: list) -> list:
        db = self.SessionLocal()
        try:
            clause_objects = []
            for clause_data in clauses:
                clause = Clause(
                    document_id=document_id,
                    clause_type=clause_data["type"],
                    content=clause_data["content"],
                    risk_score=clause_data.get("risk_score", 0.0)
                )
                db.add(clause)
                clause_objects.append(clause)
            
            db.commit()
            for clause in clause_objects:
                db.refresh(clause)
            
            return clause_objects
        finally:
            db.close()
    
    def create_risk_assessment(self, document_id: int, user_id: int, overall_score: float,
                             risk_factors: Dict[str, Any], recommendations: Dict[str, Any]) -> RiskAssessment:
        db = self.SessionLocal()
        try:
            assessment = RiskAssessment(
                document_id=document_id,
                user_id=user_id,
                overall_score=overall_score,
                risk_factors=json.dumps(risk_factors),
                recommendations=json.dumps(recommendations)
            )
            db.add(assessment)
            db.commit()
            db.refresh(assessment)
            return assessment
        finally:
            db.close()
