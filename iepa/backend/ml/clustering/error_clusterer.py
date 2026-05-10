import os
import json
from pathlib import Path
from collections import Counter

import numpy as np
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
import umap

# Setup Paths
CURRENT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "labeled_dataset.json"
if not DATA_PATH.exists():
    DATA_PATH = PROJECT_ROOT / "iepa" / "data" / "labeled_dataset.json"

EVAL_DIR = PROJECT_ROOT / "iepa" / "evaluation"
EMBEDDINGS_PATH = CURRENT_DIR / "embeddings.npy"
METRICS_PATH = EVAL_DIR / "cluster_metrics.json"
PLOT_PATH = EVAL_DIR / "cluster_plot.png"

class ErrorClusterer:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dataset = []
        self.corpus = []
        self.concepts = []
        self.embeddings = None
        
        self.dbscan = DBSCAN(eps=0.5, min_samples=2, metric='cosine')
        self.kmeans = KMeans(n_clusters=10, random_state=42)
        
        self.dbscan_labels_ = None
        self.kmeans_labels_ = None

    def load_data(self):
        print(f"[*] Loading dataset from {DATA_PATH}...")
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            self.dataset = json.load(f)
            
        self.corpus = [item.get("error_raw", "") for item in self.dataset]
        self.concepts = [item.get("concept_label", "unknown") for item in self.dataset]
        print(f"[*] Loaded {len(self.corpus)} samples.")

    def embed_corpus(self):
        print("[*] Encoding corpus with sentence-transformers...")
        if EMBEDDINGS_PATH.exists():
            print("    -> Found existing embeddings.npy, loading...")
            self.embeddings = np.load(EMBEDDINGS_PATH)
            # Make sure it matches our current dataset size
            if self.embeddings.shape[0] != len(self.corpus):
                print("    -> Dataset size changed, re-encoding...")
                self.embeddings = self.model.encode(self.corpus, show_progress_bar=True)
                np.save(EMBEDDINGS_PATH, self.embeddings)
        else:
            self.embeddings = self.model.encode(self.corpus, show_progress_bar=True)
            CURRENT_DIR.mkdir(parents=True, exist_ok=True)
            np.save(EMBEDDINGS_PATH, self.embeddings)
            print(f"    -> Saved embeddings to {EMBEDDINGS_PATH}")

    def cluster(self):
        print("\n[*] Running DBSCAN clustering...")
        self.dbscan_labels_ = self.dbscan.fit_predict(self.embeddings)
        dbscan_n_clusters = len(set(self.dbscan_labels_)) - (1 if -1 in self.dbscan_labels_ else 0)
        noise_points = list(self.dbscan_labels_).count(-1)
        
        print(f"    -> DBSCAN found {dbscan_n_clusters} clusters and {noise_points} noise points.")
        print("    -> DBSCAN distribution:", Counter(self.dbscan_labels_))
        
        print("\n[*] Running KMeans clustering (k=10)...")
        self.kmeans_labels_ = self.kmeans.fit_predict(self.embeddings)
        print("    -> KMeans distribution:", Counter(self.kmeans_labels_))
        
        return dbscan_n_clusters, noise_points

    def evaluate(self, dbscan_n_clusters, noise_points):
        print("\n[*] Evaluating clusters...")
        # Calculate KMeans Silhouette
        kmeans_sil = silhouette_score(self.embeddings, self.kmeans_labels_, metric='cosine')
        
        # Calculate DBSCAN Silhouette
        dbscan_sil = None
        if noise_points / len(self.embeddings) <= 0.5 and dbscan_n_clusters > 1:
            dbscan_sil = silhouette_score(self.embeddings, self.dbscan_labels_, metric='cosine')
            
        print(f"    -> KMeans Silhouette Score: {kmeans_sil:.4f}")
        if dbscan_sil is not None:
            print(f"    -> DBSCAN Silhouette Score: {dbscan_sil:.4f}")
        else:
            print("    -> DBSCAN Silhouette Score: Skipped (>50% noise or insufficient clusters)")

        metrics = {
            "dbscan": {
                "n_clusters": dbscan_n_clusters,
                "noise_points": noise_points,
                "silhouette": dbscan_sil
            },
            "kmeans": {
                "n_clusters": 10,
                "silhouette": float(kmeans_sil)
            },
            "total_samples": len(self.embeddings)
        }
        
        EVAL_DIR.mkdir(parents=True, exist_ok=True)
        with open(METRICS_PATH, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        print(f"[+] Saved cluster metrics to {METRICS_PATH}")

    def visualize(self):
        print("\n[*] Reducing dimensions with UMAP for visualization...")
        reducer = umap.UMAP(n_components=2, random_state=42, metric='cosine')
        embedding_2d = reducer.fit_transform(self.embeddings)
        
        print(f"[*] Generating plot...")
        plt.figure(figsize=(12, 10))
        scatter = plt.scatter(embedding_2d[:, 0], embedding_2d[:, 1], 
                              c=self.kmeans_labels_, cmap='tab10', alpha=0.7, s=50)
        
        # Add tiny labels
        for i, concept in enumerate(self.concepts):
            plt.annotate(concept, (embedding_2d[i, 0], embedding_2d[i, 1]), 
                         fontsize=6, alpha=0.6)
            
        plt.title('UMAP Projection of Error String Embeddings (Colored by KMeans)')
        plt.colorbar(scatter, label='KMeans Cluster ID')
        plt.tight_layout()
        
        plt.savefig(PLOT_PATH, dpi=150)
        print(f"[+] Saved UMAP plot to {PLOT_PATH}")

    def cluster_namer(self):
        print("\n--- KMeans Cluster to Concept Mapping Summary ---")
        cluster_map = {}
        for i in range(10):
            # Get all indices belonging to this cluster
            indices = np.where(self.kmeans_labels_ == i)[0]
            # Get concepts for these indices
            cluster_concepts = [self.concepts[idx] for idx in indices]
            # Count them
            counts = Counter(cluster_concepts)
            # Top 3
            top3 = counts.most_common(3)
            cluster_map[i] = top3
            
            top3_str = ", ".join([f"{c} x{cnt}" for c, cnt in top3])
            print(f"Cluster {i}: [{top3_str}]")

    def get_cluster(self, error_string: str) -> dict:
        """
        Embeds input error string, assigns to nearest KMeans cluster centroid,
        and returns nearest actual errors from dataset.
        """
        if self.embeddings is None or self.kmeans_labels_ is None:
            raise RuntimeError("Clusterer has not been fitted or loaded.")
            
        emb = self.model.encode([error_string])
        
        # Find nearest centroid
        distances = cosine_similarity(emb, self.kmeans.cluster_centers_)
        cluster_id = int(np.argmax(distances[0]))
        
        # Find top 3 nearest actual errors in corpus
        similarities = cosine_similarity(emb, self.embeddings)[0]
        top3_idx = np.argsort(similarities)[::-1][:3]
        nearest_errors = [self.corpus[i] for i in top3_idx]
        
        return {
            "cluster_id": cluster_id,
            "nearest_errors": nearest_errors
        }

if __name__ == "__main__":
    clusterer = ErrorClusterer()
    clusterer.load_data()
    clusterer.embed_corpus()
    
    db_clusters, db_noise = clusterer.cluster()
    clusterer.evaluate(db_clusters, db_noise)
    clusterer.visualize()
    clusterer.cluster_namer()
    
    print("\n--- Testing get_cluster() ---")
    test_err = "TypeError: object of type 'NoneType' has no len()"
    print(f"Input: {test_err}")
    res = clusterer.get_cluster(test_err)
    print(f"Assigned Cluster ID: {res['cluster_id']}")
    print(f"Nearest Errors in Dataset: {res['nearest_errors']}")
