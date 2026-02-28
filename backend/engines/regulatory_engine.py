import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from models import RiskLevel, RegulatoryChangeCreate

logger = logging.getLogger(__name__)

class RegulatoryShockSimulator:
    """Regulatory change impact simulator with deterministic calculations"""
    
    def __init__(self):
        # Industry compliance cost multipliers
        self.industry_cost_multipliers = {
            "financial": 2.5,
            "healthcare": 2.2,
            "technology": 1.8,
            "manufacturing": 1.6,
            "retail": 1.4,
            "professional_services": 1.3,
            "other": 1.0
        }
        
        # Penalty exposure multipliers by risk level
        self.penalty_multipliers = {
            RiskLevel.LOW: 0.1,
            RiskLevel.MEDIUM: 0.3,
            RiskLevel.HIGH: 0.6,
            RiskLevel.CRITICAL: 1.0
        }
        
        # Operational friction factors
        self.operational_friction_factors = {
            "reporting_requirements": 0.3,
            "compliance_certification": 0.4,
            "third_party_audit": 0.5,
            "data_protection": 0.6,
            "cross_border_compliance": 0.7,
            "real_time_monitoring": 0.8
        }
    
    def _calculate_clause_compliance_impact(self, clause: Dict[str, Any], regulatory_change: Dict[str, Any]) -> float:
        """Calculate impact score for a single clause against regulatory change"""
        clause_content = clause.get("content", "").lower()
        regulatory_text = f"{regulatory_change.get('title', '')} {regulatory_change.get('description', '')}".lower()
        
        # Simple keyword overlap for impact calculation
        clause_words = set(clause_content.split())
        regulatory_words = set(regulatory_text.split())
        
        # Calculate Jaccard similarity
        intersection = len(clause_words.intersection(regulatory_words))
        union = len(clause_words.union(regulatory_words))
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        
        # Adjust by clause risk score
        clause_risk = clause.get("calculated_risk_score", clause.get("risk_score", 0.0))
        
        return similarity * clause_risk
    
    def _estimate_compliance_cost(self, affected_clauses: List[Dict[str, Any]], 
                                 regulatory_change: Dict[str, Any]) -> float:
        """Estimate compliance cost using deterministic formula"""
        if not affected_clauses:
            return 0.0
        
        # Base cost per affected clause
        base_cost_per_clause = 5000.0
        
        # Adjust by impact level
        impact_level = regulatory_change.get("impact_level", RiskLevel.MEDIUM)
        impact_multiplier = self.penalty_multipliers.get(impact_level, 0.3)
        
        # Adjust by industry
        affected_industries = regulatory_change.get("affected_industries", ["other"])
        industry_multiplier = max(
            self.industry_cost_multipliers.get(industry, 1.0) 
            for industry in affected_industries
        )
        
        # Calculate total cost
        total_cost = len(affected_clauses) * base_cost_per_clause * impact_multiplier * industry_multiplier
        
        return round(total_cost, 2)
    
    def _calculate_penalty_exposure(self, affected_clauses: List[Dict[str, Any]], 
                                   regulatory_change: Dict[str, Any]) -> float:
        """Calculate potential penalty exposure"""
        if not affected_clauses:
            return 0.0
        
        # Base penalty calculation
        base_penalty = 100000.0  # $100k base penalty
        
        # Adjust by number of affected clauses
        clause_multiplier = min(len(affected_clauses) / 5.0, 3.0)  # Max 3x multiplier
        
        # Adjust by impact level
        impact_level = regulatory_change.get("impact_level", RiskLevel.MEDIUM)
        impact_multiplier = self.penalty_multipliers.get(impact_level, 0.3)
        
        # Adjust by clause risk scores
        avg_clause_risk = sum(
            clause.get("calculated_risk_score", clause.get("risk_score", 0.0)) 
            for clause in affected_clauses
        ) / len(affected_clauses)
        
        total_penalty = base_penalty * clause_multiplier * impact_multiplier * (1 + avg_clause_risk)
        
        return round(total_penalty, 2)
    
    def _calculate_operational_friction_index(self, affected_clauses: List[Dict[str, Any]], 
                                            regulatory_change: Dict[str, Any]) -> float:
        """Calculate operational friction index (0.0-1.0)"""
        if not affected_clauses:
            return 0.0
        
        # Analyze regulatory text for friction factors
        regulatory_text = f"{regulatory_change.get('title', '')} {regulatory_change.get('description', '')}".lower()
        
        friction_score = 0.0
        for factor, multiplier in self.operational_friction_factors.items():
            if factor.replace("_", " ") in regulatory_text:
                friction_score += multiplier
        
        # Normalize to 0.0-1.0 range
        max_possible_friction = sum(self.operational_friction_factors.values())
        normalized_friction = min(friction_score / max_possible_friction, 1.0)
        
        # Adjust by number of affected clauses
        clause_factor = min(len(affected_clauses) / 10.0, 1.0)
        
        final_friction = normalized_friction * clause_factor
        
        return round(final_friction, 3)
    
    def _identify_affected_clauses(self, clauses: List[Dict[str, Any]], 
                                 regulatory_change: Dict[str, Any], 
                                 impact_threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Identify clauses affected by regulatory change"""
        affected_clauses = []
        
        for clause in clauses:
            impact_score = self._calculate_clause_compliance_impact(clause, regulatory_change)
            
            if impact_score >= impact_threshold:
                clause["impact_score"] = impact_score
                affected_clauses.append(clause)
        
        # Sort by impact score (highest first)
        affected_clauses.sort(key=lambda x: x["impact_score"], reverse=True)
        
        return affected_clauses
    
    def simulate_regulatory_impact(self, clauses: List[Dict[str, Any]], 
                                regulatory_change: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the impact of a regulatory change on contract clauses"""
        try:
            # Identify affected clauses
            affected_clauses = self._identify_affected_clauses(clauses, regulatory_change)
            
            # Calculate metrics
            total_clauses = len(clauses)
            affected_clause_count = len(affected_clauses)
            percentage_affected = (affected_clause_count / total_clauses * 100) if total_clauses > 0 else 0.0
            
            # Estimate costs and penalties
            compliance_cost = self._estimate_compliance_cost(affected_clauses, regulatory_change)
            penalty_exposure = self._calculate_penalty_exposure(affected_clauses, regulatory_change)
            operational_friction = self._calculate_operational_friction_index(affected_clauses, regulatory_change)
            
            # Calculate overall impact score
            impact_level = regulatory_change.get("impact_level", RiskLevel.MEDIUM)
            impact_weight = self.penalty_multipliers.get(impact_level, 0.3)
            
            # Combine factors for overall impact
            cost_factor = min(compliance_cost / 1000000.0, 1.0)  # Normalize to $1M
            penalty_factor = min(penalty_exposure / 500000.0, 1.0)  # Normalize to $500k
            friction_factor = operational_friction
            
            overall_impact = (cost_factor * 0.4 + penalty_factor * 0.3 + friction_factor * 0.3) * impact_weight
            overall_impact = min(overall_impact, 1.0)
            
            return {
                "regulatory_change_id": regulatory_change.get("id"),
                "regulatory_title": regulatory_change.get("title"),
                "total_clauses": total_clauses,
                "affected_clauses": affected_clause_count,
                "percentage_affected": round(percentage_affected, 1),
                "compliance_cost_estimate": compliance_cost,
                "penalty_exposure": penalty_exposure,
                "operational_friction_index": operational_friction,
                "overall_impact_score": round(overall_impact, 3),
                "affected_clause_details": [
                    {
                        "clause_id": clause.get("id"),
                        "clause_type": clause.get("type"),
                        "impact_score": round(clause.get("impact_score", 0.0), 3),
                        "content_preview": clause.get("content", "")[:100] + "..."
                    }
                    for clause in affected_clauses[:10]  # Limit to top 10
                ],
                "risk_level": self._determine_risk_level(overall_impact),
                "recommendations": self._generate_regulatory_recommendations(
                    affected_clauses, regulatory_change, overall_impact
                )
            }
            
        except Exception as e:
            logger.error(f"Regulatory impact simulation error: {e}")
            raise
    
    def _determine_risk_level(self, impact_score: float) -> str:
        """Determine risk level based on impact score"""
        if impact_score >= 0.8:
            return RiskLevel.CRITICAL
        elif impact_score >= 0.6:
            return RiskLevel.HIGH
        elif impact_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_regulatory_recommendations(self, affected_clauses: List[Dict[str, Any]], 
                                          regulatory_change: Dict[str, Any], 
                                          impact_score: float) -> List[str]:
        """Generate recommendations based on regulatory impact"""
        recommendations = []
        
        if impact_score >= 0.8:
            recommendations.append("CRITICAL: Immediate legal and compliance review required")
            recommendations.append("Consider contract renegotiation or termination")
        
        if impact_score >= 0.6:
            recommendations.append("HIGH: Develop comprehensive compliance plan")
            recommendations.append("Allocate budget for compliance implementation")
        
        if impact_score >= 0.3:
            recommendations.append("MEDIUM: Monitor regulatory developments closely")
            recommendations.append("Update internal policies and procedures")
        
        if len(affected_clauses) > 5:
            recommendations.append("Multiple clauses affected - consider systematic contract review")
        
        # Specific recommendations based on regulatory content
        regulatory_text = f"{regulatory_change.get('title', '')} {regulatory_change.get('description', '')}".lower()
        
        if "data" in regulatory_text and "protection" in regulatory_text:
            recommendations.append("Review data handling and privacy clauses")
        
        if "financial" in regulatory_text or "reporting" in regulatory_text:
            recommendations.append("Update financial reporting and disclosure clauses")
        
        if "employment" in regulatory_text or "labor" in regulatory_text:
            recommendations.append("Review employment and contractor clauses")
        
        return recommendations

# Singleton instance
regulatory_engine = RegulatoryShockSimulator()
