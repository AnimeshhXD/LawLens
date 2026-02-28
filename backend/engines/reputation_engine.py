import logging
import re
from typing import List, Dict, Any, Optional
from llm_layer import llm_client
from security import SecurityValidator
from models import RiskLevel

logger = logging.getLogger(__name__)

class ReputationRiskScanner:
    """Secure reputation risk analysis engine"""
    
    def __init__(self):
        # ESG risk categories and keywords
        self.esg_keywords = {
            "environmental": [
                "emission", "pollution", "waste", "carbon", "sustainability",
                "climate", "environment", "green", "eco", "renewable",
                "conservation", "recycling", "toxic", "hazardous"
            ],
            "social": [
                "labor", "employee", "worker", "human rights", "discrimination",
                "harassment", "diversity", "inclusion", "safety", "health",
                "community", "stakeholder", "ethics", "fair labor"
            ],
            "governance": [
                "corruption", "bribery", "fraud", "compliance", "ethics",
                "transparency", "accountability", "board", "shareholder",
                "conflict of interest", "insider trading", "whistleblower"
            ]
        }
        
        # Negative sentiment indicators
        self.negative_indicators = [
            "violation", "breach", "non-compliance", "penalty", "fine",
            "lawsuit", "litigation", "controversy", "scandal", "investigation",
            "allegation", "misconduct", "negligence", "failure", "deficiency"
        ]
        
        # Risk severity weights
        self.severity_weights = {
            "environmental": 0.8,
            "social": 0.7,
            "governance": 0.9
        }
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text for analysis"""
        if not text:
            return ""
        
        # Remove potentially malicious content
        text = SecurityValidator.sanitize_input(text, max_length=5000)
        return text
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases using deterministic patterns"""
        text = text.lower()
        key_phrases = []
        
        # Look for ESG-related phrases
        for category, keywords in self.esg_keywords.items():
            for keyword in keywords:
                # Find sentences containing the keyword
                sentences = re.split(r'[.!?]+', text)
                for sentence in sentences:
                    if keyword in sentence:
                        # Extract the phrase around the keyword
                        words = sentence.split()
                        keyword_index = words.index(keyword) if keyword in words else -1
                        
                        if keyword_index >= 0:
                            # Extract 3 words before and after the keyword
                            start = max(0, keyword_index - 3)
                            end = min(len(words), keyword_index + 4)
                            phrase = " ".join(words[start:end])
                            
                            if phrase not in key_phrases:
                                key_phrases.append(phrase)
        
        return key_phrases[:20]  # Limit to 20 phrases
    
    def _calculate_esg_risk_score(self, text: str) -> Dict[str, float]:
        """Calculate ESG risk scores using deterministic rules"""
        text = text.lower()
        esg_scores = {}
        
        for category, keywords in self.esg_keywords.items():
            score = 0.0
            total_words = len(text.split())
            
            if total_words == 0:
                esg_scores[category] = 0.0
                continue
            
            # Count keyword occurrences
            keyword_count = 0
            for keyword in keywords:
                occurrences = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
                keyword_count += occurrences
            
            # Calculate base score
            base_score = min(keyword_count / total_words * 10, 1.0)  # Normalize to 0-1
            
            # Apply severity weight
            weighted_score = base_score * self.severity_weights[category]
            
            # Check for negative indicators
            negative_count = sum(1 for indicator in self.negative_indicators if indicator in text)
            negative_multiplier = 1.0 + (negative_count * 0.2)
            
            final_score = min(weighted_score * negative_multiplier, 1.0)
            esg_scores[category] = round(final_score, 3)
        
        return esg_scores
    
    def _determine_risk_categories(self, esg_scores: Dict[str, float]) -> List[str]:
        """Determine risk categories based on scores"""
        risk_categories = []
        
        for category, score in esg_scores.items():
            if score > 0.3:  # Threshold for considering it a risk
                risk_categories.append(category)
        
        return risk_categories
    
    def _calculate_overall_risk_score(self, esg_scores: Dict[str, float]) -> float:
        """Calculate overall reputation risk score"""
        if not esg_scores:
            return 0.0
        
        # Weighted average
        total_weight = sum(self.severity_weights.values())
        weighted_sum = sum(
            score * self.severity_weights[category]
            for category, score in esg_scores.items()
        )
        
        overall_score = weighted_sum / total_weight
        return round(min(overall_score, 1.0), 3)
    
    def _generate_deterministic_sentiment(self, text: str) -> Dict[str, Any]:
        """Generate deterministic sentiment analysis"""
        text = text.lower()
        
        # Count positive and negative indicators
        positive_words = ["compliant", "ethical", "responsible", "sustainable", "fair", "transparent"]
        negative_words = self.negative_indicators
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        total_indicators = positive_count + negative_count
        if total_indicators == 0:
            sentiment_score = 0.0  # Neutral
        else:
            sentiment_score = (positive_count - negative_count) / total_indicators
        
        return {
            "sentiment_score": round(sentiment_score, 3),
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
            "confidence": min(total_indicators / 10.0, 1.0)  # Confidence based on indicator count
        }
    
    def _generate_justification(self, esg_scores: Dict[str, float], 
                               sentiment_data: Dict[str, Any], 
                               key_phrases: List[str]) -> str:
        """Generate justification for risk assessment"""
        justifications = []
        
        # ESG risk justification
        high_risk_categories = [cat for cat, score in esg_scores.items() if score > 0.6]
        if high_risk_categories:
            justifications.append(f"High risk identified in {', '.join(high_risk_categories)} categories")
        
        # Sentiment justification
        if sentiment_data["sentiment_score"] < -0.3:
            justifications.append("Negative sentiment indicates potential reputation concerns")
        elif sentiment_data["negative_indicators"] > sentiment_data["positive_indicators"]:
            justifications.append("More negative than positive indicators detected")
        
        # Key phrase justification
        if key_phrases:
            justifications.append(f"Identified {len(key_phrases)} relevant ESG-related phrases")
        
        if not justifications:
            justifications.append("Low reputation risk based on content analysis")
        
        return "; ".join(justifications)
    
    async def analyze_reputation_risk(self, text: str) -> Dict[str, Any]:
        """Analyze reputation risk for given text"""
        try:
            # Sanitize input
            text = self._sanitize_text(text)
            
            if not text:
                return {
                    "risk_score": 0.0,
                    "risk_categories": [],
                    "sentiment_score": 0.0,
                    "key_phrases": [],
                    "justification": "No content provided for analysis"
                }
            
            # Extract key phrases
            key_phrases = self._extract_key_phrases(text)
            
            # Calculate ESG risk scores
            esg_scores = self._calculate_esg_risk_score(text)
            
            # Determine risk categories
            risk_categories = self._determine_risk_categories(esg_scores)
            
            # Calculate overall risk score
            overall_risk_score = self._calculate_overall_risk_score(esg_scores)
            
            # Generate deterministic sentiment
            sentiment_data = self._generate_deterministic_sentiment(text)
            
            # Generate justification
            justification = self._generate_justification(esg_scores, sentiment_data, key_phrases)
            
            # Enhance with LLM sentiment analysis if available
            try:
                llm_result = await llm_client.analyze_sentiment(text)
                
                # Blend deterministic and LLM results (70% deterministic, 30% LLM)
                blended_sentiment = (
                    sentiment_data["sentiment_score"] * 0.7 + 
                    llm_result.get("sentiment_score", 0.0) * 0.3
                )
                
                # Update with LLM insights if they add value
                if llm_result.get("risk_categories"):
                    risk_categories = list(set(risk_categories + llm_result["risk_categories"]))
                
                sentiment_data["sentiment_score"] = round(blended_sentiment, 3)
                
                # Add LLM key phrases if they provide additional insights
                llm_phrases = llm_result.get("key_phrases", [])
                for phrase in llm_phrases:
                    if phrase not in key_phrases and len(key_phrases) < 20:
                        key_phrases.append(phrase)
                
            except Exception as e:
                logger.warning(f"LLM sentiment analysis failed, using deterministic only: {e}")
            
            return {
                "risk_score": overall_risk_score,
                "risk_categories": risk_categories,
                "sentiment_score": sentiment_data["sentiment_score"],
                "key_phrases": key_phrases[:15],  # Limit to 15 phrases
                "justification": justification,
                "esg_breakdown": esg_scores,
                "sentiment_breakdown": {
                    "positive_indicators": sentiment_data["positive_indicators"],
                    "negative_indicators": sentiment_data["negative_indicators"],
                    "confidence": sentiment_data["confidence"]
                }
            }
            
        except Exception as e:
            logger.error(f"Reputation risk analysis error: {e}")
            raise

# Singleton instance
reputation_engine = ReputationRiskScanner()
