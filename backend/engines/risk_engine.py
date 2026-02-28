import logging
from typing import List, Dict, Any, Optional
from llm_layer import llm_client
from models import RiskLevel, RiskFactor, Recommendation

logger = logging.getLogger(__name__)

class RiskScoringEngine:
    """Deterministic risk scoring engine with explainable formulas"""
    
    def __init__(self):
        # Risk weights for different clause types
        self.clause_type_weights = {
            "liability": 0.9,
            "indemnity": 0.85,
            "termination": 0.8,
            "confidentiality": 0.6,
            "payment": 0.7,
            "intellectual_property": 0.75,
            "dispute_resolution": 0.5,
            "other": 0.3
        }
        
        # Risk category weights
        self.risk_category_weights = {
            "financial": 0.4,
            "operational": 0.3,
            "legal": 0.2,
            "reputational": 0.1
        }
        
        # Risk multiplier factors
        self.risk_multipliers = {
            "unlimited_liability": 2.0,
            "perpetual_obligation": 1.5,
            "exclusive_termination": 1.8,
            "material_breach": 1.6,
            "liquidated_damages": 1.4,
            "cross_border": 1.3,
            "regulatory_compliance": 1.2
        }
    
    def _calculate_clause_risk_score(self, clause: Dict[str, Any]) -> float:
        """Calculate risk score for a single clause using deterministic formula"""
        base_score = clause.get("risk_score", 0.0)
        clause_type = clause.get("type", "other")
        
        # Get weight for clause type
        type_weight = self.clause_type_weights.get(clause_type, 0.3)
        
        # Apply risk multipliers based on content analysis
        content = clause.get("content", "").lower()
        multiplier = 1.0
        
        for risk_factor, factor_multiplier in self.risk_multipliers.items():
            # Check if risk factor is present in content
            if risk_factor.replace("_", " ") in content:
                multiplier *= factor_multiplier
        
        # Calculate final score
        final_score = base_score * type_weight * multiplier
        
        # Cap at 1.0
        return min(final_score, 1.0)
    
    def _identify_risk_factors(self, clauses: List[Dict[str, Any]]) -> List[RiskFactor]:
        """Identify risk factors using deterministic rules"""
        risk_factors = []
        
        # Financial risk factors
        liability_clauses = [c for c in clauses if c.get("type") == "liability"]
        if liability_clauses:
            avg_liability_risk = sum(self._calculate_clause_risk_score(c) for c in liability_clauses) / len(liability_clauses)
            risk_factors.append(RiskFactor(
                category="financial",
                score=avg_liability_risk,
                description=f"Liability exposure based on {len(liability_clauses)} liability clauses"
            ))
        
        # Operational risk factors
        termination_clauses = [c for c in clauses if c.get("type") == "termination"]
        if termination_clauses:
            avg_termination_risk = sum(self._calculate_clause_risk_score(c) for c in termination_clauses) / len(termination_clauses)
            risk_factors.append(RiskFactor(
                category="operational",
                score=avg_termination_risk,
                description=f"Operational disruption risk from {len(termination_clauses)} termination clauses"
            ))
        
        # Legal risk factors
        indemnity_clauses = [c for c in clauses if c.get("type") == "indemnity"]
        if indemnity_clauses:
            avg_indemnity_risk = sum(self._calculate_clause_risk_score(c) for c in indemnity_clauses) / len(indemnity_clauses)
            risk_factors.append(RiskFactor(
                category="legal",
                score=avg_indemnity_risk,
                description=f"Legal exposure from {len(indemnity_clauses)} indemnity clauses"
            ))
        
        # Reputational risk factors
        confidentiality_clauses = [c for c in clauses if c.get("type") == "confidentiality"]
        if confidentiality_clauses:
            avg_confidentiality_risk = sum(self._calculate_clause_risk_score(c) for c in confidentiality_clauses) / len(confidentiality_clauses)
            risk_factors.append(RiskFactor(
                category="reputational",
                score=avg_confidentiality_risk,
                description=f"Reputational risk from {len(confidentiality_clauses)} confidentiality clauses"
            ))
        
        return risk_factors
    
    def _generate_recommendations(self, clauses: List[Dict[str, Any]], risk_factors: List[RiskFactor]) -> List[Recommendation]:
        """Generate recommendations based on risk analysis"""
        recommendations = []
        
        # High-risk recommendations
        high_risk_factors = [rf for rf in risk_factors if rf.score > 0.7]
        if high_risk_factors:
            recommendations.append(Recommendation(
                priority=RiskLevel.HIGH,
                action="Immediate legal review required for high-risk clauses"
            ))
        
        # Liability-specific recommendations
        liability_clauses = [c for c in clauses if c.get("type") == "liability"]
        high_risk_liability = [c for c in liability_clauses if self._calculate_clause_risk_score(c) > 0.8]
        if high_risk_liability:
            recommendations.append(Recommendation(
                priority=RiskLevel.HIGH,
                action="Negotiate liability limitations and caps"
            ))
        
        # Indemnity recommendations
        indemnity_clauses = [c for c in clauses if c.get("type") == "indemnity"]
        if indemnity_clauses:
            recommendations.append(Recommendation(
                priority=RiskLevel.MEDIUM,
                action="Review indemnity clauses for mutual obligations"
            ))
        
        # Termination recommendations
        termination_clauses = [c for c in clauses if c.get("type") == "termination"]
        if termination_clauses:
            recommendations.append(Recommendation(
                priority=RiskLevel.MEDIUM,
                action="Ensure termination clauses provide adequate notice periods"
            ))
        
        # General recommendations
        if len(clauses) > 15:
            recommendations.append(Recommendation(
                priority=RiskLevel.LOW,
                action="Consider simplifying contract structure to reduce complexity"
            ))
        
        return recommendations
    
    def _calculate_overall_risk_score(self, clauses: List[Dict[str, Any]], risk_factors: List[RiskFactor]) -> float:
        """Calculate overall risk score using weighted formula"""
        if not risk_factors:
            return 0.0
        
        # Weighted sum of risk factors
        weighted_sum = 0.0
        total_weight = 0.0
        
        for risk_factor in risk_factors:
            category = risk_factor.category
            weight = self.risk_category_weights.get(category, 0.1)
            weighted_sum += risk_factor.score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        base_score = weighted_sum / total_weight
        
        # Adjust based on number of clauses (complexity factor)
        complexity_factor = min(len(clauses) / 20.0, 1.5)  # Max 1.5x multiplier
        
        final_score = base_score * complexity_factor
        
        return min(final_score, 1.0)
    
    async def assess_risk(self, clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess risk for a set of clauses"""
        try:
            # Calculate individual clause risk scores
            scored_clauses = []
            for clause in clauses:
                clause["calculated_risk_score"] = self._calculate_clause_risk_score(clause)
                scored_clauses.append(clause)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(scored_clauses)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(scored_clauses, risk_factors)
            
            # Calculate overall risk score
            overall_score = self._calculate_overall_risk_score(scored_clauses, risk_factors)
            
            # Enhance with LLM analysis if available
            try:
                llm_result = await llm_client.assess_risk(scored_clauses[:10])  # Limit to 10 clauses for LLM
                
                # Merge LLM insights (but prioritize deterministic results)
                if llm_result.get("overall_risk_score"):
                    # Weighted average: 70% deterministic, 30% LLM
                    overall_score = (overall_score * 0.7) + (llm_result["overall_risk_score"] * 0.3)
                
                # Add LLM recommendations if they provide additional insights
                llm_recommendations = llm_result.get("recommendations", [])
                for llm_rec in llm_recommendations:
                    if not any(r.action == llm_rec["action"] for r in recommendations):
                        recommendations.append(Recommendation(
                            priority=RiskLevel(llm_rec.get("priority", "medium")),
                            action=llm_rec["action"]
                        ))
                
            except Exception as e:
                logger.warning(f"LLM risk assessment failed, using deterministic only: {e}")
            
            return {
                "overall_risk_score": round(overall_score, 3),
                "risk_factors": [
                    {
                        "category": rf.category,
                        "score": round(rf.score, 3),
                        "description": rf.description
                    }
                    for rf in risk_factors
                ],
                "recommendations": [
                    {
                        "priority": rec.priority,
                        "action": rec.action
                    }
                    for rec in recommendations
                ],
                "clause_scores": [
                    {
                        "content_preview": clause["content"][:100] + "...",
                        "type": clause["type"],
                        "risk_score": round(clause["calculated_risk_score"], 3)
                    }
                    for clause in scored_clauses
                ]
            }
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            raise

# Singleton instance
risk_engine = RiskScoringEngine()
