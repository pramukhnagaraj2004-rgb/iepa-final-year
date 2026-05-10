# Changelog

All notable changes to this project will be documented in this file.

## [2026-05-02 16:10:00+05:30]
- **Initialized** `CHANGELOG.md` file.
- **Added** full project structure for `iepa/` backend and frontend according to architectural specifications.
- **Added** initial master context prompt details to memory.

## [2026-05-02 16:15:00+05:30]
- **Added** `requirements.txt` containing Phase 1 machine learning, backend, and database dependencies.
- **Initialized** Python `venv` environment.
- **Added** `scripts/fetch_datasets.ps1` for fetching DeepFix and creating placeholder directories for CodeNet and synthetic datasets.
- **Added** `iepa/backend/parser/error_normalizer.py` to parse C and Python compilation/traceback outputs into normalized JSON events.

## [2026-05-02 16:29:00+05:30]
- **Added** `scripts/process_dataset.py` to recursively scan for `.py` files, execute them to capture `stderr`, and pipe outputs through the normalizer and weak labeler into `labeled_dataset.json`.
- **Fixed** syntax error (escaped triple quotes) in `iepa/backend/parser/error_normalizer.py` test block.
- **Added** `data/` folder directory structure setup.

## [2026-05-02 16:32:00+05:30]
- **Generated** 20 synthetic buggy Python programs across 10 concept gap categories in `data/synthetic/python/`.
- **Updated** `iepa/backend/ml/mapper/weak_labeler.py` and its `ERROR_TO_CONCEPT` regex mapping to successfully achieve 100% "high confidence" mapping against the synthetic error traces.
- **Updated** `scripts/process_dataset.py` to point to the `data/synthetic` directory and executed it to generate `data/labeled_dataset.json` with 20 entries.

## [2026-05-02 16:35:00+05:30]
- **Added** `iepa/backend/ml/mapper/concept_mapper.py` to train a TF-IDF + Logistic Regression model on `labeled_dataset.json`. Includes features for evaluating and serializing the model metrics/artifacts.

## [2026-05-02 16:45:00+05:30]
- **Added** `scripts/augment_dataset.py` containing ~12-15 real-world variations for each of the 10 concept gaps to solve data starvation.
- **Executed** augmentation, expanding `labeled_dataset.json` from 20 entries to 147 entries.
- **Updated** `concept_mapper.py` to revert to standard 80/20 train/test split and integrated `cross_val_score(cv=5)` to evaluate mean F1 macro scores on the larger dataset.

## [2026-05-02 16:50:00+05:30]
- **Added** `iepa/backend/ml/clustering/error_clusterer.py` for unsupervised error pattern discovery. Uses `sentence-transformers` for embeddings, `DBSCAN`/`KMeans` for clustering, and `UMAP` for 2D visualization. Outputs metrics and plots to `iepa/evaluation/`.

## [2026-05-02 17:05:00+05:30]
- **Added** `iepa/backend/engine/decision_engine.py` to track per-learner error history and calculate dynamic mastery scores.
- **Added** `iepa/backend/engine/feedback_generator.py` using Jinja2 templates to provide dynamic hint/explain/exercise feedback across all 10 concepts.
- **Added** `iepa/backend/engine/pipeline.py` to wire the ML classification, decision engine tracking, and feedback generation into a single end-to-end analyzer API.

## [2026-05-04 08:45:00+05:30]
- **Added** `iepa/backend/api/models.py` defining Pydantic schemas for the API request/response format.
- **Added** `iepa/backend/api/main.py` for the FastAPI application, implementing endpoints `/health`, `/analyze`, `/cluster`, `/concepts`, and learner history/mastery. Includes CORS and basic request logging.

## [2026-05-10 11:15:00+05:30]
- **Completed Phase 6 Frontend Development:** Bootstrapped React SPA within `iepa/frontend` using `create-react-app`.
- **Added** `iepa/frontend/src/App.js` implementing a unified dashboard with Monaco Code Editor, dynamic Pedagogical Feedback Panel, Concept Mastery Dashboard (using Recharts), and Error History tracking.
- **Configured** Tailwind CSS via CDN in `iepa/frontend/public/index.html`.
