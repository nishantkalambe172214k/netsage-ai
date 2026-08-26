from typing import Dict, Any, List


class ComparisonService:
    """Compares AI Diagnosis findings against Python Deterministic Rule Findings."""

    @staticmethod
    def compare(
        diagnosis: Dict[str, Any],
        rule_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesizes AI and rule checker results into a comparative evaluation."""
        if not rule_findings and not diagnosis:
            return {
                "alignment_score": 1.0,
                "status": "NO_FINDINGS",
                "summary": "No anomalies or rule violations detected.",
                "discrepancies": [],
                "consensus_recommendation": "Network state appears nominal."
            }

        ai_root_cause = (diagnosis.get("root_cause") or "").lower()
        ai_osi = diagnosis.get("osi_layer") or "Layer 3 - Network"
        
        matched_rules = []
        unmatched_rules = []

        for rf in rule_findings:
            r_name = rf.get("rule_name", "").lower()
            r_category = rf.get("category", "").lower()
            r_msg = rf.get("message", "").lower()

            # Check for keyword semantic overlap
            keywords = [r_category, rf.get("rule_id", "").lower()] + r_name.split()
            matched = any(kw in ai_root_cause for kw in keywords if len(kw) > 3)

            if matched:
                matched_rules.append(rf)
            else:
                unmatched_rules.append(rf)

        total_rules = len(rule_findings)
        if total_rules > 0:
            match_ratio = len(matched_rules) / total_rules
            if match_ratio >= 0.7:
                status = "FULL_ALIGNMENT"
                alignment_score = max(0.85, match_ratio)
            elif match_ratio > 0.0:
                status = "PARTIAL_ALIGNMENT"
                alignment_score = 0.65
            else:
                status = "DIVERGENT"
                alignment_score = 0.35
        else:
            status = "AI_ONLY_FINDING"
            alignment_score = 0.75

        discrepancies = []
        if unmatched_rules:
            for ur in unmatched_rules:
                discrepancies.append(
                    f"Deterministic rule flagged '{ur.get('rule_name')}' on {ur.get('affected_device')}, but AI diagnosis focused on '{diagnosis.get('root_cause')}'."
                )

        consensus = (
            f"Consensus: AI diagnosis ({ai_osi}) correlates with {len(matched_rules)} of {total_rules} deterministic rule finding(s). "
            f"Human review required to approve remediation commands."
        )

        return {
            "alignment_score": round(alignment_score, 2),
            "status": status,
            "matched_rules_count": len(matched_rules),
            "total_rules_count": total_rules,
            "discrepancies": discrepancies,
            "consensus_recommendation": consensus,
            "ai_summary": {
                "root_cause": diagnosis.get("root_cause"),
                "confidence": diagnosis.get("confidence") or diagnosis.get("confidence_score"),
                "osi_layer": ai_osi,
                "next_command": diagnosis.get("next_command"),
                "fix_steps": diagnosis.get("fix_steps", [])
            }
        }
