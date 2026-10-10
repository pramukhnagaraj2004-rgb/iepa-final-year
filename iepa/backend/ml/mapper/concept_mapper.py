import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List

import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer as SklearnTfidf
from sklearn.linear_model import LogisticRegression as SklearnLogReg
import joblib

# Setup paths dynamically based on file location
CURRENT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent.parent

# Support import whether executed directly or as a module
sys.path.insert(0, str(PROJECT_ROOT))
try:
    from iepa.backend.ml.mapper.tfidf_scratch import TFIDFVectorizer, LogisticRegressionScratch
except ImportError:
    from tfidf_scratch import TFIDFVectorizer, LogisticRegressionScratch

# Data paths
DATA_PATH = PROJECT_ROOT / "data" / "labeled_dataset.json"
if not DATA_PATH.exists():
    DATA_PATH = PROJECT_ROOT / "iepa" / "data" / "labeled_dataset.json"

EVAL_DIR = PROJECT_ROOT / "iepa" / "evaluation"
METRICS_PATH = EVAL_DIR / "mapper_metrics.json"
HELDOUT_METRICS_PATH = EVAL_DIR / "mapper_heldout_metrics.json"

# Model paths (JSON for scratch models, pkl for backward compatibility)
SCRATCH_TFIDF_PATH = CURRENT_DIR / "tfidf_scratch.json"
SCRATCH_LOGREG_PATH = CURRENT_DIR / "logreg_scratch.json"
LEGACY_VECTORIZER_PATH = CURRENT_DIR / "tfidf_vectorizer.pkl"
LEGACY_CLASSIFIER_PATH = CURRENT_DIR / "logistic_classifier.pkl"

# File paths inside tracebacks can contain the answer (e.g. ...\off_by_one_3.py),
# which lets the model read the label instead of learning the error pattern.
# They are replaced with <FILE> for both training and prediction.
_PATH_RE = re.compile(r'[A-Za-z]:\\[^\s"]*?\.py|/[^\s"]*?\.py')


def scrub_paths(text: str) -> str:
    return _PATH_RE.sub("<FILE>", text)


def extract_error_line(error_text: str) -> str:
    """
    Same rule the live sandbox executor uses: the last line containing 'Error:',
    otherwise the last non-empty line. Training and prediction both use it, so the
    model is trained on exactly the kind of text it receives at runtime.
    """
    lines = [l.strip() for l in error_text.splitlines() if l.strip()]
    if not lines:
        return ""
    for line in reversed(lines):
        if "Error:" in line:
            return line
    return lines[-1]


def build_features(error_text: str, code: str = None) -> str:
    """Feature string = scrubbed error line (+ the student's code, when available)."""
    line = extract_error_line(scrub_paths(error_text or ""))
    code = (code or "").strip()
    if code:
        return f"{line} [CODE] {code}"
    return line


class ConceptMapper:
    def __init__(self):
        self.vectorizer = TFIDFVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=5000)
        self.classifier = LogisticRegressionScratch(learning_rate=1.0, max_iter=2000, C=1.0, random_state=42)
        self.classes_ = []

    @staticmethod
    def _parse(data: list) -> Tuple[List[str], List[str], List[str]]:
        """Turns raw dataset rows into feature strings, labels, and split tags."""
        X, y, split = [], [], []
        for item in data:
            X.append(build_features(item.get("error_raw", ""), item.get("code", "")))
            y.append(item.get("concept_label", "unknown"))
            # Older samples have no 'split' field -> they count as training data
            split.append(item.get("split", "train"))
        return X, y, split

    def load_data(self, json_path: Path) -> Tuple[np.ndarray, np.ndarray]:
        """
        Reads labeled_dataset.json and extracts input feature strings and concept targets.
        """
        if not json_path.exists():
            raise FileNotFoundError(f"Dataset not found at {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        X, y, _ = self._parse(data)
        return np.array(X), np.array(y)

    def train_and_evaluate(self, X: np.ndarray, y: np.ndarray):
        """
        Trains Scratch TF-IDF and Scratch LogisticRegression, then compares
        side-by-side with Sklearn equivalents to validate precision and accuracy.
        """
        print("[*] Vectorizing features using Scratch TF-IDF...")
        X_vec_scratch = self.vectorizer.fit_transform(X.tolist())
        self.classes_ = self.vectorizer.feature_names_

        print("[*] Splitting dataset (80/20 train/test split, stratified)...")
        X_train_sc, X_test_sc, y_train, y_test = train_test_split(
            X_vec_scratch, y, test_size=0.2, stratify=y, random_state=42
        )

        print("[*] Training Scratch Logistic Regression (OvR with L2 Regularization)...")
        self.classifier.fit(X_train_sc, y_train)
        self.classes_ = self.classifier.classes_

        # Train Sklearn baseline on same split for side-by-side validation
        print("[*] Training Sklearn equivalents for side-by-side comparison...")
        sk_vec = SklearnTfidf(analyzer="char_wb", ngram_range=(2, 4), max_features=5000)
        X_vec_sk = sk_vec.fit_transform(X.tolist()).toarray().astype(np.float32)
        X_train_sk, X_test_sk, _, _ = train_test_split(
            X_vec_sk, y, test_size=0.2, stratify=y, random_state=42
        )
        sk_clf = SklearnLogReg(max_iter=1000, C=1.0, random_state=42)
        sk_clf.fit(X_train_sk, y_train)

        # 5-fold CV for Sklearn baseline
        sk_cv_scores = cross_val_score(sk_clf, X_vec_sk, y, cv=5, scoring="f1_macro")
        sk_mean_cv_f1 = float(sk_cv_scores.mean())

        # Predictions
        y_pred_scratch = self.classifier.predict(X_test_sc)
        y_pred_sklearn = sk_clf.predict(X_test_sk)

        acc_scratch = accuracy_score(y_test, y_pred_scratch)
        acc_sklearn = accuracy_score(y_test, y_pred_sklearn)
        acc_diff_pct = abs(acc_sklearn - acc_scratch) * 100.0

        report_scratch = classification_report(y_test, y_pred_scratch, output_dict=True, zero_division=0)
        report_sklearn = classification_report(y_test, y_pred_sklearn, output_dict=True, zero_division=0)

        print("\n===========================================================")
        print("  SIDE-BY-SIDE MODEL VALIDATION (Scratch vs Sklearn)")
        print("===========================================================")
        print(f"Sklearn Model Accuracy:  {acc_sklearn * 100:.2f}% (5-Fold CV Macro F1: {sk_mean_cv_f1:.2f})")
        print(f"Scratch Model Accuracy:  {acc_scratch * 100:.2f}%")
        print(f"Accuracy Difference:     {acc_diff_pct:.2f}% (Requirement: <= 5.0%)")
        print("-----------------------------------------------------------")
        print("\n--- Scratch Classification Report ---")
        print(classification_report(y_test, y_pred_scratch, zero_division=0))

        # Save validation metrics
        EVAL_DIR.mkdir(parents=True, exist_ok=True)
        metrics = {
            "scratch_accuracy": acc_scratch,
            "sklearn_accuracy": acc_sklearn,
            "accuracy_difference_pct": acc_diff_pct,
            "sklearn_cv_mean_f1_macro": sk_mean_cv_f1,
            "scratch_classification_report": report_scratch,
            "sklearn_classification_report": report_sklearn
        }
        with open(METRICS_PATH, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"[+] Validation metrics saved to {METRICS_PATH}")

    def evaluate_heldout(self, json_path: Path):
        """
        Honest test: train only on samples with split != 'heldout', test only on
        samples with split == 'heldout' (bug patterns the model has never seen).
        Fresh models are used, so the saved production model is not affected.
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        X, y, split = self._parse(data)

        tr = [i for i, s in enumerate(split) if s != "heldout"]
        te = [i for i, s in enumerate(split) if s == "heldout"]
        if not te:
            print("[!] No samples with split='heldout' found; skipping held-out evaluation.")
            return

        X_tr, y_tr = [X[i] for i in tr], np.array([y[i] for i in tr])
        X_te, y_te = [X[i] for i in te], np.array([y[i] for i in te])

        # Scratch models (vectorizer fitted on training data only)
        vec = TFIDFVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=5000)
        A = vec.fit_transform(X_tr)
        B = vec.transform(X_te)
        clf = LogisticRegressionScratch(learning_rate=1.0, max_iter=2000, C=1.0, random_state=42)
        clf.fit(A, y_tr)
        pred_scratch = clf.predict(B)

        # Sklearn equivalents
        sk_vec = SklearnTfidf(analyzer="char_wb", ngram_range=(2, 4), max_features=5000)
        A_sk = sk_vec.fit_transform(X_tr).toarray().astype(np.float32)
        B_sk = sk_vec.transform(X_te).toarray().astype(np.float32)
        sk_clf = SklearnLogReg(max_iter=1000, C=1.0, random_state=42).fit(A_sk, y_tr)
        pred_sk = sk_clf.predict(B_sk)

        acc_scratch = accuracy_score(y_te, pred_scratch)
        acc_sklearn = accuracy_score(y_te, pred_sk)

        print("\n===========================================================")
        print("  HELD-OUT EVALUATION (unseen bug patterns, paths scrubbed)")
        print("===========================================================")
        print(f"Train samples: {len(tr)} | Held-out test samples: {len(te)}")
        print(f"Sklearn Held-out Accuracy:  {acc_sklearn * 100:.2f}%")
        print(f"Scratch Held-out Accuracy:  {acc_scratch * 100:.2f}%")
        print("\n--- Scratch Held-out Classification Report ---")
        print(classification_report(y_te, pred_scratch, zero_division=0))

        EVAL_DIR.mkdir(parents=True, exist_ok=True)
        out = {
            "train_samples": len(tr),
            "heldout_samples": len(te),
            "scratch_heldout_accuracy": acc_scratch,
            "sklearn_heldout_accuracy": acc_sklearn,
            "scratch_classification_report": classification_report(y_te, pred_scratch, output_dict=True, zero_division=0),
            "sklearn_classification_report": classification_report(y_te, pred_sk, output_dict=True, zero_division=0),
        }
        with open(HELDOUT_METRICS_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"[+] Held-out metrics saved to {HELDOUT_METRICS_PATH}")

    def evaluate_grouped_cv(self, json_path: Path, folds: int = 5):
        """
        5-fold CV where samples that share a template (or identical code) always stay
        in the same fold, so the score is not inflated by near-duplicate programs.
        """
        import hashlib
        from sklearn.model_selection import GroupKFold
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        X, y, _ = self._parse(data)
        groups = [
            item.get("template_id")
            or hashlib.md5((item.get("code") or item.get("error_raw", "")).encode()).hexdigest()
            for item in data
        ]
        vec = SklearnTfidf(analyzer="char_wb", ngram_range=(2, 4), max_features=5000)
        M = vec.fit_transform(X).toarray().astype(np.float32)
        clf = SklearnLogReg(max_iter=1000, C=1.0, random_state=42)
        acc = cross_val_score(clf, M, np.array(y), cv=GroupKFold(folds), groups=groups, scoring="accuracy")
        f1 = cross_val_score(clf, M, np.array(y), cv=GroupKFold(folds), groups=groups, scoring="f1_macro")
        print("\n===========================================================")
        print("  GROUPED 5-FOLD CV (sklearn; template twins kept together)")
        print("===========================================================")
        print(f"Accuracy: {acc.mean() * 100:.2f}% (+/- {acc.std() * 100:.2f})   Macro F1: {f1.mean():.2f}")
        EVAL_DIR.mkdir(parents=True, exist_ok=True)
        with open(EVAL_DIR / "mapper_grouped_cv.json", "w", encoding="utf-8") as f:
            json.dump({"folds": folds, "accuracy_mean": float(acc.mean()), "accuracy_std": float(acc.std()),
                       "macro_f1_mean": float(f1.mean())}, f, indent=2)

    def save_model(self):
        """
        Saves scratch models as JSON files.
        """
        self.vectorizer.save(str(SCRATCH_TFIDF_PATH))
        self.classifier.save(str(SCRATCH_LOGREG_PATH))
        print(f"[+] Scratch models saved to JSON at {CURRENT_DIR}")

    def load_model(self) -> bool:
        """
        Loads models from JSON (scratch). Falls back to pickle if JSON not found.
        """
        if SCRATCH_TFIDF_PATH.exists() and SCRATCH_LOGREG_PATH.exists():
            self.vectorizer.load(str(SCRATCH_TFIDF_PATH))
            self.classifier.load(str(SCRATCH_LOGREG_PATH))
            self.classes_ = self.classifier.classes_
            return True
        elif LEGACY_VECTORIZER_PATH.exists() and LEGACY_CLASSIFIER_PATH.exists():
            # Legacy fallback
            self.vectorizer = joblib.load(LEGACY_VECTORIZER_PATH)
            self.classifier = joblib.load(LEGACY_CLASSIFIER_PATH)
            self.classes_ = getattr(self.classifier, "classes_", [])
            return True
        return False

    def predict_concept(self, error_string: str, code: str = None) -> Dict[str, Any]:
        """
        Predicts concept gap category for a given error string.
        """
        # Ensure model is loaded or trained
        if not hasattr(self.vectorizer, "vocabulary_") or not self.vectorizer.vocabulary_:
            if not self.load_model():
                raise RuntimeError("Model is not trained or loaded yet.")

        # Identical feature construction to training (path scrubbing, error line, optional code)
        error_string = build_features(error_string, code)

        # Vectorize input
        if isinstance(self.vectorizer, TFIDFVectorizer):
            x_vec = self.vectorizer.transform([error_string])
            probas = self.classifier.predict_proba(x_vec)[0]
            classes = self.classifier.classes_
        else:
            # Fallback for sklearn vectorizer
            x_vec = self.vectorizer.transform([error_string])
            probas = self.classifier.predict_proba(x_vec)[0]
            classes = list(self.classifier.classes_)

        # Top 1 prediction
        best_idx = int(np.argmax(probas))
        concept = classes[best_idx]
        confidence = float(probas[best_idx])

        # Top 3 predictions
        top3_indices = np.argsort(probas)[::-1][:3]
        top3 = [{"concept": classes[int(i)], "confidence": float(probas[int(i)])} for i in top3_indices]

        return {
            "concept": concept,
            "confidence": confidence,
            "top3": top3
        }

if __name__ == "__main__":
    mapper = ConceptMapper()

    print("--- Phase 3: Concept Mapper Training & Side-by-Side Validation ---")
    X, y = mapper.load_data(DATA_PATH)
    print(f"[*] Loaded {len(X)} samples from {DATA_PATH}")

    mapper.train_and_evaluate(X, y)
    mapper.save_model()
    mapper.evaluate_heldout(DATA_PATH)
    mapper.evaluate_grouped_cv(DATA_PATH)

    print("\n--- Testing predict_concept() on Unseen Errors ---")
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
        print(f"  -> Top 3: {[(r['concept'], round(r['confidence'], 2)) for r in result['top3']]}\n")
