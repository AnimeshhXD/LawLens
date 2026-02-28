import logging
import difflib
from typing import List, Dict, Any, Optional, Tuple
from models import RiskLevel

logger = logging.getLogger(__name__)

class ImpactDiffEngine:
    """Secure impact analysis engine for regulatory changes"""
    
    def __init__(self):
        # Keywords that indicate significant changes
        self.significant_change_keywords = [
            "shall", "must", "required", "prohibited", "forbidden",
            "penalty", "fine", "liability", "enforcement", "compliance",
            "mandatory", "obligation", "restriction", "limitation"
        ]
        
        # Change impact weights
        self.change_type_weights = {
            "addition": 0.6,
            "removal": 0.8,
            "modification": 0.7,
            "restructuring": 0.5
        }
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text for processing"""
        if not text:
            return ""
        
        # Remove potentially malicious content
        text = text.strip()
        # Limit length
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        return text
    
    def _classify_change_type(self, old_text: str, new_text: str) -> str:
        """Classify the type of change between old and new text"""
        if not old_text and new_text:
            return "addition"
        elif old_text and not new_text:
            return "removal"
        elif old_text and new_text:
            # Check if it's a major restructuring
            old_words = set(old_text.lower().split())
            new_words = set(new_text.lower().split())
            
            similarity = len(old_words.intersection(new_words)) / len(old_words.union(new_words))
            
            if similarity < 0.3:
                return "restructuring"
            else:
                return "modification"
        else:
            return "unknown"
    
    def _calculate_change_significance(self, diff_line: str) -> float:
        """Calculate significance score for a diff line"""
        significance = 0.0
        line_lower = diff_line.lower()
        
        # Check for significant keywords
        for keyword in self.significant_change_keywords:
            if keyword in line_lower:
                significance += 0.2
        
        # Check for numerical values (often indicate thresholds or limits)
        import re
        if re.search(r'\b\d+(?:\.\d+)?\b', diff_line):
            significance += 0.1
        
        # Check for dates (often indicate deadlines)
        if re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', diff_line):
            significance += 0.1
        
        return min(significance, 1.0)
    
    def _generate_secure_diff(self, old_text: str, new_text: str) -> List[Dict[str, Any]]:
        """Generate secure diff between old and new text"""
        old_text = self._sanitize_text(old_text)
        new_text = self._sanitize_text(new_text)
        
        if not old_text and not new_text:
            return []
        
        # Generate unified diff
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        diff_lines = list(difflib.unified_diff(
            old_lines, new_lines,
            fromfile="old_regulation",
            tofile="new_regulation",
            lineterm=""
        ))
        
        # Process diff lines
        processed_diff = []
        line_number = 0
        
        for line in diff_lines:
            if line.startswith('@@'):
                # Parse line numbers from diff header
                import re
                match = re.search(r'-(\d+)', line)
                if match:
                    line_number = int(match.group(1))
                continue
            
            if line.startswith('---') or line.startswith('+++'):
                continue
            
            change_type = "context"
            if line.startswith('-'):
                change_type = "removal"
            elif line.startswith('+'):
                change_type = "addition"
            
            # Calculate significance
            significance = self._calculate_change_significance(line)
            
            processed_diff.append({
                "line_number": line_number,
                "change_type": change_type,
                "content": line[1:] if line.startswith(('+', '-')) else line,
                "raw_line": line,
                "significance": round(significance, 3)
            })
            
            if change_type != "removal":  # Don't increment for removals
                line_number += 1
        
        return processed_diff
    
    def _analyze_contract_clause_impact(self, clause: Dict[str, Any], 
                                      diff_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze impact of regulatory change on a specific clause"""
        clause_content = clause.get("content", "").lower()
        
        # Count relevant changes
        relevant_changes = []
        total_significance = 0.0
        
        for diff_line in diff_analysis:
            if diff_line["change_type"] == "context":
                continue
            
            # Check if diff line is relevant to clause
            diff_content = diff_line["content"].lower()
            
            # Simple keyword matching
            clause_words = set(clause_content.split())
            diff_words = set(diff_content.split())
            
            overlap = len(clause_words.intersection(diff_words))
            if overlap > 0:
                relevant_changes.append(diff_line)
                total_significance += diff_line["significance"]
        
        # Calculate impact score
        impact_score = min(total_significance / max(len(relevant_changes), 1), 1.0) if relevant_changes else 0.0
        
        return {
            "clause_id": clause.get("id"),
            "clause_type": clause.get("type"),
            "impact_score": round(impact_score, 3),
            "relevant_changes_count": len(relevant_changes),
            "affected": impact_score > 0.1  # Threshold for considering clause affected
        }
    
    def analyze_regulatory_impact(self, clauses: List[Dict[str, Any]], 
                                old_text: str, new_text: str) -> Dict[str, Any]:
        """Analyze the impact of regulatory text changes on contract clauses"""
        try:
            # Generate secure diff
            diff_analysis = self._generate_secure_diff(old_text, new_text)
            
            # Classify overall change type
            change_type = self._classify_change_type(old_text, new_text)
            
            # Calculate overall change significance
            total_significance = sum(line["significance"] for line in diff_analysis)
            overall_significance = min(total_significance / max(len(diff_analysis), 1), 1.0)
            
            # Analyze impact on each clause
            clause_impacts = []
            affected_clauses = []
            
            for clause in clauses:
                impact = self._analyze_contract_clause_impact(clause, diff_analysis)
                clause_impacts.append(impact)
                
                if impact["affected"]:
                    affected_clauses.append(impact)
            
            # Calculate summary statistics
            total_clauses = len(clauses)
            affected_count = len(affected_clauses)
            affected_percentage = (affected_count / total_clauses * 100) if total_clauses > 0 else 0.0
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_significance, affected_percentage)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                change_type, overall_significance, affected_clauses
            )
            
            return {
                "change_analysis": {
                    "change_type": change_type,
                    "overall_significance": round(overall_significance, 3),
                    "total_lines_changed": len([l for l in diff_analysis if l["change_type"] != "context"]),
                    "high_significance_changes": len([l for l in diff_analysis if l["significance"] > 0.7])
                },
                "impact_summary": {
                    "total_clauses": total_clauses,
                    "affected_clauses": affected_count,
                    "affected_percentage": round(affected_percentage, 1),
                    "risk_level": risk_level
                },
                "clause_impacts": clause_impacts,
                "detailed_diff": diff_analysis[:50],  # Limit to first 50 lines for security
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Impact analysis error: {e}")
            raise
    
    def _determine_risk_level(self, significance: float, affected_percentage: float) -> str:
        """Determine risk level based on significance and affected percentage"""
        # Combined risk score
        risk_score = (significance * 0.6) + (affected_percentage / 100.0 * 0.4)
        
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_recommendations(self, change_type: str, significance: float, 
                                affected_clauses: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on impact analysis"""
        recommendations = []
        
        # High-level recommendations based on change type
        if change_type == "addition":
            recommendations.append("Review new requirements for compliance gaps")
        elif change_type == "removal":
            recommendations.append("Assess opportunities from deregulation")
        elif change_type == "modification":
            recommendations.append("Update existing processes to reflect changes")
        elif change_type == "restructuring":
            recommendations.append("Comprehensive policy review required")
        
        # Severity-based recommendations
        if significance >= 0.7:
            recommendations.append("HIGH PRIORITY: Immediate legal review required")
            recommendations.append("Allocate resources for rapid compliance implementation")
        elif significance >= 0.4:
            recommendations.append("MEDIUM PRIORITY: Develop compliance timeline")
            recommendations.append("Conduct impact assessment on business operations")
        
        # Clause-specific recommendations
        if len(affected_clauses) > 10:
            recommendations.append("Large number of clauses affected - consider systematic approach")
        
        high_impact_clauses = [c for c in affected_clauses if c["impact_score"] > 0.7]
        if high_impact_clauses:
            recommendations.append(f"Priority review of {len(high_impact_clauses)} high-impact clauses")
        
        return recommendations

# Singleton instance
impact_engine = ImpactDiffEngine()
