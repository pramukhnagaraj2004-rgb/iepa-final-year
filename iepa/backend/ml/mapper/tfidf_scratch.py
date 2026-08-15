import json
import math
import os
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

class TFIDFVectorizer:
    """
    TF-IDF Vectorizer implemented from scratch.
    Supports character n-grams with word boundary padding ('char_wb'),
    smooth IDF weighting, and L2 vector normalization.
    Serializes to and loads from human-readable JSON.
    """
    def __init__(
        self,
        analyzer: str = "char_wb",
        ngram_range: Tuple[int, int] = (2, 4),
        max_features: Optional[int] = 5000
    ):
        self.analyzer = analyzer
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.vocabulary_: Dict[str, int] = {}
        self.idf_: Dict[str, float] = {}
        self.feature_names_: List[str] = []

    def _get_char_wb_ngrams(self, text: str, n: int) -> List[str]:
        """
        Pads each token with spaces (' ' + token + ' ') and slides a window of size n.
        """
        ngrams = []
        tokens = text.lower().split()
        for token in tokens:
            padded = f" {token} "
            if len(padded) >= n:
                for i in range(len(padded) - n + 1):
                    ngrams.append(padded[i:i + n])
        return ngrams

    def _get_ngrams(self, text: str) -> List[str]:
        """
        Extracts n-grams for each n in ngram_range.
        """
        ngrams = []
        min_n, max_n = self.ngram_range
        for n in range(min_n, max_n + 1):
            ngrams.extend(self._get_char_wb_ngrams(text, n))
        return ngrams

    def _compute_tf(self, ngrams: List[str]) -> Dict[str, float]:
        """
        Computes term frequency (raw counts) of ngrams in a document.
        """
        return dict(Counter(ngrams))

    def _compute_idf(self, corpus_ngrams: List[List[str]]) -> Dict[str, float]:
        """
        Computes smooth IDF for all terms in vocabulary.
        Formula: log((N + 1) / (df + 1)) + 1.0
        """
        n_docs = len(corpus_ngrams)
        df = Counter()
        for doc_ngrams in corpus_ngrams:
            for term in set(doc_ngrams):
                if term in self.vocabulary_:
                    df[term] += 1

        idf_dict = {}
        for term in self.vocabulary_:
            doc_freq = df.get(term, 0)
            idf_dict[term] = math.log((n_docs + 1.0) / (doc_freq + 1.0)) + 1.0
        return idf_dict

    def _build_vocabulary(self, corpus_ngrams: List[List[str]]) -> Dict[str, int]:
        """
        Builds vocabulary mapping term -> column index from corpus.
        Respects max_features if specified.
        """
        df = Counter()
        for doc_ngrams in corpus_ngrams:
            for term in set(doc_ngrams):
                df[term] += 1

        if self.max_features and len(df) > self.max_features:
            # Select top max_features by document frequency, sort alphabetically
            top_terms = sorted(
                [term for term, _ in df.most_common(self.max_features)]
            )
        else:
            top_terms = sorted(df.keys())

        self.feature_names_ = top_terms
        return {term: idx for idx, term in enumerate(top_terms)}

    def fit(self, texts: List[str]) -> "TFIDFVectorizer":
        """
        Fits vectorizer on a corpus of text documents.
        """
        corpus_ngrams = [self._get_ngrams(text) for text in texts]
        self.vocabulary_ = self._build_vocabulary(corpus_ngrams)
        self.idf_ = self._compute_idf(corpus_ngrams)
        return self

    def transform(self, texts: List[str]) -> np.ndarray:
        """
        Transforms texts into L2-normalized TF-IDF matrix of shape (n_docs, vocab_size).
        """
        if not self.vocabulary_:
            raise ValueError("TFIDFVectorizer is not fitted yet.")

        n_docs = len(texts)
        n_features = len(self.vocabulary_)
        matrix = np.zeros((n_docs, n_features), dtype=np.float32)

        for i, text in enumerate(texts):
            doc_ngrams = self._get_ngrams(text)
            tf_counts = self._compute_tf(doc_ngrams)
            for term, count in tf_counts.items():
                if term in self.vocabulary_:
                    col_idx = self.vocabulary_[term]
                    matrix[i, col_idx] = count * self.idf_[term]
            
            # L2 Normalization per row
            norm = np.linalg.norm(matrix[i])
            if norm > 0:
                matrix[i] /= norm

        return matrix

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        return self.fit(texts).transform(texts)

    def save(self, path: str):
        """
        Serializes vocabulary and IDF values to JSON.
        """
        data = {
            "analyzer": self.analyzer,
            "ngram_range": list(self.ngram_range),
            "max_features": self.max_features,
            "vocabulary": self.vocabulary_,
            "idf": self.idf_
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> "TFIDFVectorizer":
        """
        Loads vectorizer state from JSON.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.analyzer = data.get("analyzer", "char_wb")
        self.ngram_range = tuple(data.get("ngram_range", [2, 4]))
        self.max_features = data.get("max_features", 5000)
        self.vocabulary_ = data.get("vocabulary", {})
        self.idf_ = data.get("idf", {})
        self.feature_names_ = [k for k, _ in sorted(self.vocabulary_.items(), key=lambda x: x[1])]
        return self


class LogisticRegressionScratch:
    """
    Multiclass Logistic Regression implemented from scratch via One-vs-Rest (OvR).
    Includes L2 weight regularization and gradient descent optimization.
    Serializes to and loads from human-readable JSON.
    """
    def __init__(
        self,
        learning_rate: float = 1.0,
        max_iter: int = 2000,
        C: float = 1.0,
        random_state: int = 42
    ):
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.C = C
        self.random_state = random_state
        self.weights: Dict[str, Dict[str, Any]] = {}
        self.classes_: List[str] = []

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        """
        Numerically stable sigmoid function.
        """
        z_clipped = np.clip(z, -500.0, 500.0)
        return 1.0 / (1.0 + np.exp(-z_clipped))

    def _cross_entropy_loss(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        weights: np.ndarray
    ) -> float:
        """
        Binary cross-entropy loss with L2 regularization penalty.
        """
        eps = 1e-15
        y_pred_clipped = np.clip(y_pred, eps, 1.0 - eps)
        n_samples = len(y_true)
        bce = -np.mean(
            y_true * np.log(y_pred_clipped) + (1.0 - y_true) * np.log(1.0 - y_pred_clipped)
        )
        l2_penalty = (1.0 / (2.0 * self.C * n_samples)) * np.sum(weights ** 2)
        return float(bce + l2_penalty)

    def _train_binary(
        self,
        X: np.ndarray,
        y_binary: np.ndarray,
        class_label: str
    ) -> Dict[str, Any]:
        """
        Trains a single binary logistic regression model for OvR via gradient descent.
        """
        n_samples, n_features = X.shape
        w = np.zeros(n_features, dtype=np.float32)
        b = 0.0

        for it in range(self.max_iter):
            z = X @ w + b
            p = self._sigmoid(z)
            error = p - y_binary

            # Vectorized gradient computation with L2 regularization
            grad_w = (X.T @ error) / n_samples + (w / (self.C * n_samples))
            grad_b = float(np.mean(error))

            w -= self.learning_rate * grad_w
            b -= self.learning_rate * grad_b

        return {"w": w.tolist(), "b": float(b)}

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegressionScratch":
        """
        Fits One-vs-Rest multiclass logistic regression models.
        """
        self.classes_ = sorted(list(set(y.tolist() if isinstance(y, np.ndarray) else y)))
        self.weights = {}

        for class_label in self.classes_:
            y_binary = (y == class_label).astype(np.float32)
            self.weights[class_label] = self._train_binary(X, y_binary, class_label)

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Computes probability predictions for each class, normalized across classes (L1).
        """
        if not self.weights or not self.classes_:
            raise ValueError("Model is not fitted yet.")

        n_samples = X.shape[0]
        n_classes = len(self.classes_)
        raw_probas = np.zeros((n_samples, n_classes), dtype=np.float32)

        for col_idx, class_label in enumerate(self.classes_):
            w = np.array(self.weights[class_label]["w"], dtype=np.float32)
            b = self.weights[class_label]["b"]
            raw_probas[:, col_idx] = self._sigmoid(X @ w + b)

        # L1 normalize across classes to ensure valid probability distribution
        row_sums = raw_probas.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1e-10
        return raw_probas / row_sums

    def predict(self, X: np.ndarray) -> List[str]:
        """
        Predicts the class label with highest probability.
        """
        probas = self.predict_proba(X)
        best_indices = np.argmax(probas, axis=1)
        return [self.classes_[idx] for idx in best_indices]

    def save(self, path: str):
        """
        Serializes weights and class labels to JSON.
        """
        data = {
            "learning_rate": self.learning_rate,
            "max_iter": self.max_iter,
            "C": self.C,
            "random_state": self.random_state,
            "classes": self.classes_,
            "weights": self.weights
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> "LogisticRegressionScratch":
        """
        Loads weights and parameters from JSON.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.learning_rate = data.get("learning_rate", 1.0)
        self.max_iter = data.get("max_iter", 2000)
        self.C = data.get("C", 1.0)
        self.random_state = data.get("random_state", 42)
        self.classes_ = data.get("classes", [])
        self.weights = data.get("weights", {})
        return self


if __name__ == "__main__":
    print("=== Testing TFIDFVectorizer and LogisticRegressionScratch in Isolation ===")
    from pathlib import Path
    from sklearn.feature_extraction.text import TfidfVectorizer as SklearnTfidf
    from sklearn.linear_model import LogisticRegression as SklearnLogReg
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score

    # Load dataset
    current_dir = Path(__file__).resolve().parent
    data_path = current_dir.parent.parent.parent.parent / "data" / "labeled_dataset.json"
    if not data_path.exists():
        data_path = current_dir.parent.parent.parent / "data" / "labeled_dataset.json"

    with open(data_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    texts = [
        d["error_raw"] + " " + " ".join([ev.get("error_type", ev.get("severity", "")) for ev in d.get("error_normalized", [])])
        for d in dataset
    ]
    labels = np.array([d.get("concept_label", "unknown") for d in dataset])

    print(f"[*] Dataset samples: {len(texts)}")

    # 1. Compare TF-IDF scratch vs sklearn
    print("\n--- Step 1: Validating TF-IDF Scratch vs Sklearn ---")
    scratch_tfidf = TFIDFVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=5000)
    X_scratch = scratch_tfidf.fit_transform(texts)

    sklearn_tfidf = SklearnTfidf(analyzer="char_wb", ngram_range=(2, 4), max_features=5000)
    X_sklearn = sklearn_tfidf.fit_transform(texts).toarray().astype(np.float32)

    vocab_diff_pct = abs(len(scratch_tfidf.vocabulary_) - len(sklearn_tfidf.vocabulary_)) / len(sklearn_tfidf.vocabulary_) * 100.0
    print(f"Scratch Vocab Size: {len(scratch_tfidf.vocabulary_)}")
    print(f"Sklearn Vocab Size: {len(sklearn_tfidf.vocabulary_)}")
    print(f"Vocab size difference: {vocab_diff_pct:.2f}%")
    assert vocab_diff_pct <= 1.0, f"Vocab diff {vocab_diff_pct:.2f}% exceeds 1% tolerance"

    # 2. Compare Logistic Regression scratch vs sklearn
    print("\n--- Step 2: Validating Logistic Regression Scratch vs Sklearn ---")
    X_tr_sc, X_te_sc, y_train, y_test = train_test_split(
        X_scratch, labels, test_size=0.2, stratify=labels, random_state=42
    )
    X_tr_sk, X_te_sk, _, _ = train_test_split(
        X_sklearn, labels, test_size=0.2, stratify=labels, random_state=42
    )

    # Train Sklearn model
    sk_clf = SklearnLogReg(max_iter=1000, C=1.0, random_state=42)
    sk_clf.fit(X_tr_sk, y_train)
    sk_acc = accuracy_score(y_test, sk_clf.predict(X_te_sk))

    # Train Scratch model
    scratch_clf = LogisticRegressionScratch(learning_rate=1.0, max_iter=2000, C=1.0, random_state=42)
    scratch_clf.fit(X_tr_sc, y_train)
    sc_acc = accuracy_score(y_test, scratch_clf.predict(X_te_sc))

    print(f"Sklearn Accuracy: {sk_acc * 100:.2f}%")
    print(f"Scratch Accuracy: {sc_acc * 100:.2f}%")
    acc_diff = abs(sk_acc - sc_acc) * 100.0
    print(f"Accuracy Difference: {acc_diff:.2f}%")
    assert acc_diff <= 5.0, f"Accuracy difference {acc_diff:.2f}% exceeds 5% tolerance"

    # 3. Test JSON Serialization roundtrip
    print("\n--- Step 3: Validating JSON Save and Load ---")
    tfidf_save_path = current_dir / "test_tfidf.json"
    logreg_save_path = current_dir / "test_logreg.json"

    scratch_tfidf.save(str(tfidf_save_path))
    scratch_clf.save(str(logreg_save_path))

    loaded_tfidf = TFIDFVectorizer().load(str(tfidf_save_path))
    loaded_clf = LogisticRegressionScratch().load(str(logreg_save_path))

    X_loaded = loaded_tfidf.transform(texts[:5])
    preds_loaded = loaded_clf.predict(X_loaded)
    preds_orig = scratch_clf.predict(X_scratch[:5])
    assert preds_loaded == preds_orig, "Loaded model predictions do not match original model"
    print("[+] Model serialization roundtrip verified successfully.")

    # Clean up test JSON artifacts
    if tfidf_save_path.exists():
        tfidf_save_path.unlink()
    if logreg_save_path.exists():
        logreg_save_path.unlink()

    print("\n[+] All TF-IDF and Logistic Regression scratch tests passed successfully!")
