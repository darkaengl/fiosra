from typing import List, Dict, Any

class DistractorEngine:
    """
    Seeds questions and multiple-choice options with common cognitive traps
    derived from the misconception taxonomy.
    """
    @staticmethod
    def generate_distractors(topic: str, misconceptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        distractors = []
        for m in misconceptions:
            distractors.append({
                "misconception_id": m.get("misconception_id", "GENERIC_ERROR"),
                "distractor_value": f"Trap based on: {m.get('name', 'Common Error')}",
                "diagnostic_rule": m.get("flawed_rule", "Misapplied operator precedence")
            })
        return distractors
