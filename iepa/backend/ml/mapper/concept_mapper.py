import os
import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Setup paths dynamically based on file location
CURRENT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent.parent
# Look for data folder either in iepa/data or project_root/data
DATA_PATH = PROJECT_ROOT / "data" / "labeled_dataset.json"
if not DATA_PATH.exists():
    DATA_PATH = PROJECT_ROOT / "iepa" / "data" / "labeled_dataset.json"

EVAL_DIR = PROJECT_ROOT / "iepa" / "evaluation"
VECTORIZER_PATH = CURRENT_DIR / "tfidf_vectorizer.pkl"
CLASSIFIER_PATH = CURRENT_DIR / "logistic_classifier.pkl"
METRICS_PATH = EVAL_DIR / "mapper_metrics.json"

class ConceptMapper:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
        self.classifier = LogisticRegression(max_iter=1000, C=1.0)
        self.classes_ = []

    def load_data(self, json_path: Path):
        """
        Reads labeled_dataset.json and extracts input feature strings and concept targets.
        """
        if not json_path.exists():
            raise FileNotFoundError(f"Dataset not found at {json_path}")
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        X, y = [], []
        for item in data:
            error_raw = item.get("error_raw", "")
            
            # Extract error_normalized types safely
            normalized_list = item.get("error_normalized", [])
            error_types = []
            for ev in normalized_list:
                if "error_type" in ev:
                    error_types.append(ev["error_type"])
                elif "severity" in ev:
                    error_types.append(ev["severity"])
                    
            error_type_str = " ".join(error_types)
            
            # Input feature string: error_raw + error_normalized.type
            feature_string = f"{error_raw} {error_type_str}".strip()
            
            X.append(feature_string)
            y.append(item.get("concept_label", "unknown"))
            
        return np.array(X), np.array(y)

    def train_and_evaluate(self, X, y):
        """
        Trains TF-IDF and LogisticRegression, then evaluates and saves metrics.
        """
        print("[*] Vectorizing features...")
        X_vec = self.vectorizer.fit_transform(X)
        self.classes_ = np.unique(y)
        
        print("[*] Splitting dataset (80/20)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_vec, y, test_size=0.2, stratify=y, random_state=42
        )
            
        print("[*] Training Logistic Regression...")
        self.classifier.fit(X_train, y_train)
        
        print("[*] Running 5-Fold Cross Validation...")
        cv_scores = cross_val_score(self.classifier, X_vec, y, cv=5, scoring='f1_macro')
        mean_cv_f1 = cv_scores.mean()
        
        print("[*] Evaluating model...")
        y_pred = self.classifier.predict(X_test)
        
        report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        report_str = classification_report(y_test, y_pred, zero_division=0)
        accuracy = accuracy_score(y_test, y_pred)
        
        print("\n--- Classification Report ---")
        print(report_str)
        print(f"Overall Accuracy: {accuracy:.2f}")
        print(f"5-Fold CV Mean F1 (Macro): {mean_cv_f1:.2f}")
        
        # Save metrics
        EVAL_DIR.mkdir(parents=True, exist_ok=True)
        metrics = {
            "accuracy": accuracy,
            "cv_mean_f1_macro": mean_cv_f1,
            "classification_report": report_dict
        }
        with open(METRICS_PATH, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        print(f"[+] Metrics saved to {METRICS_PATH}")

    def save_model(self):
        joblib.dump(self.vectorizer, VECTORIZER_PATH)
        joblib.dump(self.classifier, CLASSIFIER_PATH)
        print(f"[+] Model saved to {CURRENT_DIR}")

    def load_model(self):
        if VECTORIZER_PATH.exists() and CLASSIFIER_PATH.exists():
            self.vectorizer = joblib.load(VECTORIZER_PATH)
            self.classifier = joblib.load(CLASSIFIER_PATH)
            self.classes_ = self.classifier.classes_
            return True
        return False

    def predict_concept(self, error_string: str) -> dict:
        """
        Predicts concept gap category for a given error string.
        """
        # Ensure model is loaded or trained
        if not hasattr(self.vectorizer, 'vocabulary_'):
            if not self.load_model():
                raise RuntimeError("Model is not trained or loaded yet.")
                
        # Vectorize input
        x_vec = self.vectorizer.transform([error_string])
        
        # Get probabilities
        probas = self.classifier.predict_proba(x_vec)[0]
        
        # Top 1 prediction
        best_idx = np.argmax(probas)
        concept = self.classifier.classes_[best_idx]
        confidence = float(probas[best_idx])
        
        # Top 3 predictions
        top3_indices = np.argsort(probas)[::-1][:3]
        top3 = [{"concept": self.classifier.classes_[i], "confidence": float(probas[i])} for i in top3_indices]
        
        return {
            "concept": concept,
            "confidence": confidence,
            "top3": top3
        }

if __name__ == "__main__":
    mapper = ConceptMapper()
    
    print("--- Phase 3: Concept Mapper ---")
    X, y = mapper.load_data(DATA_PATH)
    print(f"[*] Loaded {len(X)} samples from {DATA_PATH}")
    
    mapper.train_and_evaluate(X, y)
    mapper.save_model()
    
    print("\\n--- Testing predict_concept() on Unseen Errors ---")
    test_errors = [
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "NameError: name 'user_id' is not defined",
        "IndexError: list index out of range",
        "RecursionError: maximum recursion depth exceeded while calling a Python object",
        "IndentationError: unexpected indent"
    ]
    
    for idx, err in enumerate(test_errors, 1):
        result = mapper.predict_concept(err)
        print(f"Test {idx}: {err}")
        print(f"  -> Predicted Concept: {result['concept']} (Confidence: {result['confidence']:.2f})")
        print(f"  -> Top 3: {[(r['concept'], round(r['confidence'], 2)) for r in result['top3']]}\\n")
