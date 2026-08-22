import json
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import numpy as np

class KMeansScratch:
    """
    K-Means clustering implemented from scratch.
    Uses K-Means++ initialization, spherical Cosine distance for assignments,
    L2-normalized centroid updates, multi-restart optimization (n_init),
    and custom Cosine Silhouette score calculation.
    Serializes to and loads from human-readable JSON.
    """
    def __init__(
        self,
        n_clusters: int = 10,
        max_iter: int = 300,
        tol: float = 1e-4,
        random_state: int = 42,
        n_init: int = 10
    ):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state
        self.n_init = n_init
        
        self.centroids_: Optional[np.ndarray] = None
        self.labels_: Optional[np.ndarray] = None
        self.inertia_: float = 0.0
        self.n_iter_: int = 0

    def _normalize(self, X: np.ndarray) -> np.ndarray:
        """
        L2 normalizes each row of X to lie on the unit hypersphere.
        """
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        return X / norms

    def _init_centroids(self, X: np.ndarray, rng: np.random.RandomState) -> np.ndarray:
        """
        K-Means++ initialization algorithm using Cosine distance-squared (D^2) weighting.
        """
        n_samples, n_features = X.shape
        centroids = np.zeros((self.n_clusters, n_features), dtype=np.float32)
        
        # 1. Pick first centroid randomly
        first_idx = rng.randint(0, n_samples)
        centroids[0] = X[first_idx]
        
        # 2. Pick remaining centroids using D^2 weighting
        for c_idx in range(1, self.n_clusters):
            current_centroids = centroids[:c_idx]  # (c_idx, n_features)
            sims = X @ current_centroids.T         # (n_samples, c_idx)
            
            # Cosine distance = 1 - sim (clamped >= 0)
            cos_dists = np.clip(1.0 - sims, 0.0, 2.0)
            
            # Minimum distance to any chosen centroid
            min_dists = np.min(cos_dists, axis=1)  # (n_samples,)
            dist_sq = min_dists ** 2
            
            total_dist_sq = np.sum(dist_sq)
            if total_dist_sq > 0:
                probs = dist_sq / total_dist_sq
            else:
                probs = np.ones(n_samples) / n_samples
                
            next_idx = rng.choice(n_samples, p=probs)
            centroids[c_idx] = X[next_idx]
            
        return centroids

    def _assign_clusters(self, X: np.ndarray, centroids: np.ndarray) -> np.ndarray:
        """
        Assigns each point to the nearest centroid using Cosine distance.
        Nearest centroid corresponds to maximum cosine similarity.
        """
        sims = X @ centroids.T  # (n_samples, n_clusters)
        return np.argmax(sims, axis=1)

    def _update_centroids(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        rng: np.random.RandomState
    ) -> np.ndarray:
        """
        Updates centroids to the mean of assigned points and normalizes to unit sphere.
        Handles empty clusters by re-initializing from a random point.
        """
        n_features = X.shape[1]
        new_centroids = np.zeros((self.n_clusters, n_features), dtype=np.float32)
        
        for k in range(self.n_clusters):
            cluster_points = X[labels == k]
            if len(cluster_points) > 0:
                mean_vec = np.mean(cluster_points, axis=0)
                norm = np.linalg.norm(mean_vec)
                new_centroids[k] = mean_vec / (norm if norm > 0 else 1e-10)
            else:
                # Re-initialize empty cluster from random sample
                rand_idx = rng.randint(0, len(X))
                new_centroids[k] = X[rand_idx]
                
        return new_centroids

    def _has_converged(self, old_centroids: np.ndarray, new_centroids: np.ndarray) -> bool:
        """
        Checks if the maximum centroid movement is below tolerance.
        """
        shift = np.max(np.linalg.norm(old_centroids - new_centroids, axis=1))
        return shift < self.tol

    def fit(self, X: np.ndarray) -> "KMeansScratch":
        """
        Fits K-Means clustering on feature matrix X across n_init restarts.
        """
        rng = np.random.RandomState(self.random_state)
        X_norm = self._normalize(X.astype(np.float32))
        
        best_inertia = float("inf")
        best_centroids = None
        best_labels = None
        best_n_iter = 0
        
        for init in range(self.n_init):
            centroids = self._init_centroids(X_norm, rng)
            labels = np.zeros(len(X_norm), dtype=np.int32)
            
            for it in range(self.max_iter):
                labels = self._assign_clusters(X_norm, centroids)
                new_centroids = self._update_centroids(X_norm, labels, rng)
                
                if self._has_converged(centroids, new_centroids):
                    centroids = new_centroids
                    n_iter = it + 1
                    break
                centroids = new_centroids
            else:
                n_iter = self.max_iter
                
            sims = np.sum(X_norm * centroids[labels], axis=1)
            inertia = float(np.sum(np.clip(1.0 - sims, 0.0, 2.0)))
            
            if inertia < best_inertia:
                best_inertia = inertia
                best_centroids = centroids
                best_labels = labels
                best_n_iter = n_iter
                
        self.centroids_ = best_centroids
        self.labels_ = best_labels
        self.inertia_ = best_inertia
        self.n_iter_ = best_n_iter
        
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Assigns new samples in X to nearest cluster centroids.
        """
        if self.centroids_ is None:
            raise ValueError("KMeansScratch is not fitted yet.")
        X_norm = self._normalize(X.astype(np.float32))
        return self._assign_clusters(X_norm, self.centroids_)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """
        Fits model and returns cluster labels.
        """
        return self.fit(X).labels_

    @staticmethod
    def silhouette_score(X: np.ndarray, labels: np.ndarray) -> float:
        """
        Computes Cosine Silhouette Score from scratch.
        s(i) = (b(i) - a(i)) / max(a(i), b(i))
        """
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        X_norm = X / norms
        
        n_samples = len(X_norm)
        unique_labels = np.unique(labels)
        if len(unique_labels) <= 1 or len(unique_labels) >= n_samples:
            return 0.0
            
        # Cosine distance matrix: D[i, j] = 1 - (x_i . x_j)
        dist_matrix = np.clip(1.0 - (X_norm @ X_norm.T), 0.0, 2.0)
        
        s_scores = np.zeros(n_samples, dtype=np.float32)
        
        for i in range(n_samples):
            c_i = labels[i]
            
            # Intra-cluster mean distance a(i)
            same_mask = (labels == c_i)
            same_count = np.sum(same_mask)
            if same_count > 1:
                # Exclude point i itself
                a_i = (np.sum(dist_matrix[i, same_mask]) - dist_matrix[i, i]) / (same_count - 1)
            else:
                a_i = 0.0
                
            # Inter-cluster mean distance b(i) = min over all other clusters
            other_means = []
            for other_c in unique_labels:
                if other_c == c_i:
                    continue
                other_mask = (labels == other_c)
                if np.sum(other_mask) > 0:
                    other_means.append(np.mean(dist_matrix[i, other_mask]))
                    
            if other_means:
                b_i = min(other_means)
            else:
                b_i = 0.0
                
            denom = max(a_i, b_i)
            if denom > 0:
                s_scores[i] = (b_i - a_i) / denom
            else:
                s_scores[i] = 0.0
                
        return float(np.mean(s_scores))

    def save(self, path: str):
        """
        Serializes model parameters, centroids, and labels to JSON.
        """
        data = {
            "n_clusters": self.n_clusters,
            "max_iter": self.max_iter,
            "tol": self.tol,
            "random_state": self.random_state,
            "n_init": self.n_init,
            "inertia": self.inertia_,
            "n_iter": self.n_iter_,
            "centroids": self.centroids_.tolist() if self.centroids_ is not None else [],
            "labels": self.labels_.tolist() if self.labels_ is not None else []
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> "KMeansScratch":
        """
        Loads model from JSON file.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.n_clusters = data.get("n_clusters", 10)
        self.max_iter = data.get("max_iter", 300)
        self.tol = data.get("tol", 1e-4)
        self.random_state = data.get("random_state", 42)
        self.n_init = data.get("n_init", 10)
        self.inertia_ = data.get("inertia", 0.0)
        self.n_iter_ = data.get("n_iter", 0)
        
        centroids_list = data.get("centroids", [])
        if centroids_list:
            self.centroids_ = np.array(centroids_list, dtype=np.float32)
        labels_list = data.get("labels", [])
        if labels_list:
            self.labels_ = np.array(labels_list, dtype=np.int32)
        return self


if __name__ == "__main__":
    print("=== Testing KMeansScratch in Isolation ===")
    from sklearn.cluster import KMeans as SklearnKMeans
    from sklearn.metrics import silhouette_score as sklearn_silhouette_score
    
    current_dir = Path(__file__).resolve().parent
    embeddings_path = current_dir / "embeddings.npy"
    
    if embeddings_path.exists():
        X_emb = np.load(embeddings_path)
        print(f"[*] Loaded embeddings shape: {X_emb.shape}")
    else:
        print("[*] Generating synthetic unit hypersphere embeddings for validation...")
        rng = np.random.RandomState(42)
        X_raw = rng.randn(147, 384)
        X_emb = X_raw / np.linalg.norm(X_raw, axis=1, keepdims=True)

    # 1. Train Scratch KMeans
    print("\n--- Step 1: Fitting KMeansScratch (k=10) ---")
    kmeans_scratch = KMeansScratch(n_clusters=10, max_iter=300, random_state=42, n_init=10)
    scratch_labels = kmeans_scratch.fit_predict(X_emb)
    scratch_sil = KMeansScratch.silhouette_score(X_emb, scratch_labels)
    
    print(f"Scratch Iterations:              {kmeans_scratch.n_iter_}")
    print(f"Scratch Cosine Silhouette Score: {scratch_sil:.4f}")

    # 2. Train Sklearn KMeans on same data
    print("\n--- Step 2: Fitting Sklearn KMeans (k=10) ---")
    norms = np.linalg.norm(X_emb, axis=1, keepdims=True)
    X_norm = X_emb / np.where(norms == 0, 1e-10, norms)
    sk_kmeans = SklearnKMeans(n_clusters=10, random_state=42, n_init=10)
    sk_labels = sk_kmeans.fit_predict(X_norm)
    sk_sil = sklearn_silhouette_score(X_norm, sk_labels, metric="cosine")
    
    print(f"Sklearn Cosine Silhouette Score: {sk_sil:.4f}")
    
    sil_diff = abs(scratch_sil - sk_sil)
    print(f"Silhouette Difference:           {sil_diff:.4f} (Target: <= 0.02)")
    assert sil_diff <= 0.02, f"Silhouette difference {sil_diff:.4f} exceeds 0.02 target"

    # 3. Test Save & Load JSON roundtrip
    print("\n--- Step 3: JSON Model Serialization Roundtrip ---")
    save_path = current_dir / "test_kmeans.json"
    kmeans_scratch.save(str(save_path))
    
    loaded_km = KMeansScratch().load(str(save_path))
    test_preds_orig = kmeans_scratch.predict(X_emb[:10])
    test_preds_loaded = loaded_km.predict(X_emb[:10])
    assert np.array_equal(test_preds_orig, test_preds_loaded), "Predictions from loaded model do not match!"
    print("[+] Model serialization verified successfully.")
    
    if save_path.exists():
        save_path.unlink()
        
    print("\n[+] All KMeansScratch isolation tests passed successfully!")
