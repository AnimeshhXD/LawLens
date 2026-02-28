import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from PyPDF2 import PdfReader
import docx
from llm_layer import llm_client
from security import SecurityValidator
from models import ClauseType, ClauseClassification

logger = logging.getLogger(__name__)

class ClauseIntelligenceEngine:
    """Secure clause extraction and classification engine"""
    
    def __init__(self):
        # Predefined clause patterns for deterministic extraction
        self.clause_patterns = {
            ClauseType.LIABILITY: [
                r"(?i)liability.{0,100}(limit|limitation|cap|maximum)",
                r"(?i)limit.{0,50}liability",
                r"(?i)damages.{0,100}(consequential|indirect|special)",
                r"(?i)total.{0,50}liability.{0,50}(exceed|not exceed)"
            ],
            ClauseType.INDEMNITY: [
                r"(?i)indemnif(y|ies|ication)",
                r"(?i)hold harmless",
                r"(?i)defend.{0,100}(claim|lawsuit|proceeding)",
                r"(?i)reimburse.{0,100}(cost|expense|fee)"
            ],
            ClauseType.TERMINATION: [
                r"(?i)terminat(e|ion|ing).{0,100}(agreement|contract)",
                r"(?i)terminate.{0,100}(cause|without cause)",
                r"(?i)breach.{0,100}(material|substantial)",
                r"(?i)notice.{0,100}terminat(e|ion)"
            ],
            ClauseType.CONFIDENTIALITY: [
                r"(?i)confidential.{0,100}information",
                r"(?i)proprietary.{0,100}information",
                r"(?i)trade secret",
                r"(?i)non-disclos(e|ure|ure agreement)"
            ],
            ClauseType.PAYMENT: [
                r"(?i)payment.{0,100}(term|schedule|due)",
                r"(?i)invoice.{0,100}(due|payment)",
                r"(?i)fee.{0,100}(payment|compensation)",
                r"(?i)compensat(e|ion|ing)"
            ],
            ClauseType.INTELLECTUAL_PROPERTY: [
                r"(?i)intellectual.{0,100}property",
                r"(?i)copyright.{0,100}(ownership|license)",
                r"(?i)patent.{0,100}(right|license)",
                r"(?i)trademark.{0,100}(right|license)"
            ],
            ClauseType.DISPUTE_RESOLUTION: [
                r"(?i)dispute.{0,100}(resolution|settlement)",
                r"(?i)arbitration",
                r"(?i)mediation",
                r"(?i)jurisdiction",
                r"(?i)governing.{0,100}law"
            ]
        }
        
        # Risk keywords for initial scoring
        self.risk_keywords = {
            "high": [
                "unlimited", "unlimited liability", "no limit", "without limitation",
                "perpetual", "irrevocable", "exclusive", "sole discretion",
                "material adverse", "breach", "default", "penalty", "liquidated damages"
            ],
            "medium": [
                "reasonable", "commercially reasonable", "best efforts", "good faith",
                "indemnify", "hold harmless", "defend", "reimburse"
            ],
            "low": [
                "mutual", "reciprocal", "subject to", "conditioned upon", "provided that"
            ]
        }
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PdfReader(file_content)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise ValueError("Failed to extract text from PDF")
    
    def _extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_content)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            raise ValueError("Failed to extract text from DOCX")
    
    def _extract_text_from_txt(self, file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_content.decode('latin-1')
            except Exception as e:
                logger.error(f"Text extraction error: {e}")
                raise ValueError("Failed to extract text from file")
    
    def extract_text(self, file_content: bytes, mime_type: str) -> str:
        """Extract text from various file types"""
        if mime_type == "application/pdf":
            return self._extract_text_from_pdf(file_content)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return self._extract_text_from_docx(file_content)
        elif mime_type == "text/plain":
            return self._extract_text_from_txt(file_content)
        else:
            raise ValueError(f"Unsupported file type: {mime_type}")
    
    def _calculate_initial_risk_score(self, text: str) -> float:
        """Calculate initial risk score using deterministic rules"""
        text_lower = text.lower()
        score = 0.0
        
        # High-risk keywords
        for keyword in self.risk_keywords["high"]:
            if keyword in text_lower:
                score += 0.3
        
        # Medium-risk keywords
        for keyword in self.risk_keywords["medium"]:
            if keyword in text_lower:
                score += 0.2
        
        # Low-risk keywords (reduce score)
        for keyword in self.risk_keywords["low"]:
            if keyword in text_lower:
                score -= 0.1
        
        # Cap the score
        return min(max(score, 0.0), 1.0)
    
    def _extract_clauses_deterministic(self, text: str) -> List[Dict[str, Any]]:
        """Extract clauses using deterministic patterns"""
        clauses = []
        
        # Split text into potential clauses
        # Look for numbered sections, paragraphs, or distinct clauses
        clause_patterns = [
            r'\d+\.\s*[^.]*[.!?](?:\s[^.]*[.!?])*',  # Numbered sections
            r'[A-Z][^.]*[.!?](?:\s[^.]*[.!?])*',      # Sentences starting with capital
            r'(?:(?:Section|Clause|Article)\s+\d+[^.]*[.!?])',  # Explicit section markers
        ]
        
        for pattern in clause_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                # Clean and validate the clause
                clause_text = match.strip()
                if len(clause_text) < 50:  # Too short to be meaningful
                    continue
                
                # Check for prompt injection
                is_injection, _ = SecurityValidator.detect_prompt_injection(clause_text)
                if is_injection:
                    logger.warning("Prompt injection detected in clause, skipping")
                    continue
                
                # Classify clause type using patterns
                clause_type = self._classify_clause_type_deterministic(clause_text)
                
                # Calculate initial risk score
                risk_score = self._calculate_initial_risk_score(clause_text)
                
                clauses.append({
                    "content": clause_text,
                    "type": clause_type,
                    "risk_score": risk_score,
                    "extraction_method": "deterministic"
                })
        
        # Remove duplicates and limit to reasonable number
        unique_clauses = []
        seen_content = set()
        
        for clause in clauses:
            content_hash = hashlib.sha256(clause["content"].encode()).hexdigest()
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_clauses.append(clause)
        
        return unique_clauses[:20]  # Limit to 20 clauses
    
    def _classify_clause_type_deterministic(self, text: str) -> ClauseType:
        """Classify clause type using deterministic patterns"""
        text_lower = text.lower()
        
        # Score each clause type
        type_scores = {}
        for clause_type, patterns in self.clause_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            type_scores[clause_type] = score
        
        # Return the type with highest score, or OTHER if no matches
        if not any(type_scores.values()):
            return ClauseType.OTHER
        
        return max(type_scores, key=type_scores.get)
    
    async def extract_and_classify_clauses(self, file_content: bytes, mime_type: str) -> List[Dict[str, Any]]:
        """Extract and classify clauses from document"""
        try:
            # Extract text
            text = self.extract_text(file_content, mime_type)
            
            # Validate extracted text
            is_valid, message = SecurityValidator.validate_file_content(text, mime_type)
            if not is_valid:
                raise ValueError(f"File validation failed: {message}")
            
            # Extract clauses deterministically
            clauses = self._extract_clauses_deterministic(text)
            
            # Enhance with LLM classification for top 10 clauses
            enhanced_clauses = []
            for i, clause in enumerate(clauses[:10]):
                try:
                    # Use LLM for better classification
                    llm_result = await llm_client.classify_clause(clause["content"])
                    
                    # Merge deterministic and LLM results
                    enhanced_clause = {
                        "content": clause["content"],
                        "type": llm_result.get("clause_type", clause["type"]),
                        "risk_score": llm_result.get("risk_score", clause["risk_score"]),
                        "key_entities": llm_result.get("key_entities", []),
                        "obligations": llm_result.get("obligations", []),
                        "confidence": llm_result.get("confidence", 0.5),
                        "extraction_method": "hybrid"
                    }
                    enhanced_clauses.append(enhanced_clause)
                    
                except Exception as e:
                    logger.error(f"LLM classification failed for clause {i}: {e}")
                    # Fall back to deterministic result
                    enhanced_clauses.append(clause)
            
            # Add remaining clauses with deterministic classification
            enhanced_clauses.extend(clauses[10:])
            
            return enhanced_clauses
            
        except Exception as e:
            logger.error(f"Clause extraction error: {e}")
            raise

# Singleton instance
clause_engine = ClauseIntelligenceEngine()
