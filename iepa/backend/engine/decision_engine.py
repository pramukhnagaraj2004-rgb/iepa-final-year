import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

class DecisionEngine:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.learner_id = user_id  # Backward compatibility alias
        self.history: List[Dict[str, Any]] = []
        self.mastery: Dict[str, float] = {}

    def record_error(self, concept: str, confidence: float, tier: Optional[str] = None):
        # Count occurrences for this concept (including current attempt)
        concept_count = sum(1 for h in self.history if h["concept"] == concept) + 1
        
        # Update mastery score
        if concept not in self.mastery:
            # First time seeing this error concept
            self.mastery[concept] = 0.4
        else:
            if concept_count == 2:
                self.mastery[concept] -= 0.1
            elif concept_count >= 3:
                self.mastery[concept] -= 0.15
                
        # Clamp between 0.0 and 1.0
        self.mastery[concept] = max(0.0, min(1.0, self.mastery[concept]))
        
        computed_tier = tier or self.get_feedback_tier(concept)

        # Append to history
        self.history.append({
            "concept": concept,
            "confidence": confidence,
            "tier": computed_tier,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_feedback_tier(self, concept: str) -> str:
        score = self.mastery.get(concept, 0.5)
        if score >= 0.4:
            return "hint"
        elif score >= 0.2:
            return "explain"
        else:
            return "exercise"

    def get_mastery_report(self) -> Dict[str, float]:
        return dict(sorted(self.mastery.items(), key=lambda item: item[1]))

    def save(self, path: Optional[str] = None):
        """
        Saves state to local JSON file for dev fallback and local persistence.
        """
        if path:
            data = {
                "user_id": self.user_id,
                "learner_id": self.user_id,
                "history": self.history,
                "mastery": self.mastery
            }
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def load(self, path: Optional[str] = None):
        """
        Loads state from local JSON file.
        """
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.user_id = data.get("user_id", data.get("learner_id", self.user_id))
            self.learner_id = self.user_id
            self.history = data.get("history", [])
            self.mastery = data.get("mastery", {})
