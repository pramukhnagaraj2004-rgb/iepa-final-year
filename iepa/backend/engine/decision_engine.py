import os
import json
from datetime import datetime
from pathlib import Path

class DecisionEngine:
    def __init__(self, learner_id: str):
        self.learner_id = learner_id
        self.history = []
        self.mastery = {}

    def record_error(self, concept: str, confidence: float):
        # Append to history
        self.history.append({
            "concept": concept,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update mastery score
        if concept not in self.mastery:
            # First time seeing this error concept
            self.mastery[concept] = 0.4
        else:
            # Count how many times this concept has appeared in history
            concept_count = sum(1 for h in self.history if h["concept"] == concept)
            
            if concept_count == 2:
                self.mastery[concept] -= 0.1
            elif concept_count >= 3:
                self.mastery[concept] -= 0.15
                
        # Clamp between 0.0 and 1.0
        self.mastery[concept] = max(0.0, min(1.0, self.mastery[concept]))

    def get_feedback_tier(self, concept: str) -> str:
        score = self.mastery.get(concept, 0.5) # Default to 0.5 if somehow missing
        if score >= 0.4:
            return "hint"
        elif score >= 0.2:
            return "explain"
        else:
            return "exercise"

    def get_mastery_report(self) -> dict:
        # Return dict sorted by score ascending
        return dict(sorted(self.mastery.items(), key=lambda item: item[1]))

    def save(self, path: str):
        data = {
            "learner_id": self.learner_id,
            "history": self.history,
            "mastery": self.mastery
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load(self, path: str):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.learner_id = data.get("learner_id", self.learner_id)
            self.history = data.get("history", [])
            self.mastery = data.get("mastery", {})
