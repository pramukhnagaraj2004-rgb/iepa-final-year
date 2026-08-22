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

## [2026-08-15 08:30:00+05:30]
- **Added** `iepa/backend/sandbox/executor.py` implementing `CodeExecutor` for isolated dynamic execution of student code inside Docker containers (`python:3.11-slim`) with `--network none`, `--memory 128m`, `--cpus 0.5`, `--pids-limit 64`, 10-second timeout enforcement, and automatic exception extraction (`error_raw`).
- **Added** `iepa/backend/ml/mapper/tfidf_scratch.py` implementing `TFIDFVectorizer` (character n-grams with word boundary padding `char_wb`, smooth IDF, L2 vector normalization) and `LogisticRegressionScratch` (multiclass One-vs-Rest, numerical clipping, L2 weight decay regularization, vectorized gradient descent) with human-readable JSON model persistence.
- **Updated** `iepa/backend/ml/mapper/concept_mapper.py` to use scratch ML models (`tfidf_scratch.json`, `logreg_scratch.json`), preserving the exact `predict_concept(error_string)` interface and adding side-by-side validation against scikit-learn (matching vocabulary within 0.00% and test accuracy within 3.33%, well within the 5% target).
- **Updated** `iepa/backend/api/models.py` and `iepa/backend/api/main.py`:
  - Updated `POST /analyze` to execute submitted code in the Docker sandbox, automatically extract runtime/syntax exceptions, route them through the ML feedback pipeline, and return clean execution feedback if error-free.
  - Added `POST /analyze/manual` accepting `error_raw` directly for backward compatibility and automated testing.
- **Fixed** `iepa/backend/engine/decision_engine.py` to persist `tier` in error history records.
- **Updated** `requirements.txt` to include `numpy`, `jinja2`, and `httpx`.

## [2026-08-22 11:40:00+05:30]
- **Added** `iepa/backend/ml/clustering/kmeans_scratch.py` implementing `KMeansScratch` with K-Means++ $D^2$ distance initialization, spherical cosine distance assignment, explicit centroid L2 normalization ($\|c\|_2 = 1$), multi-restart (`n_init=10`) inertia optimization, custom Cosine Silhouette Score calculation, and JSON model persistence (`kmeans_scratch.json`).
- **Updated** `iepa/backend/ml/clustering/error_clusterer.py` to replace scikit-learn with `KMeansScratch`. Side-by-side evaluation verified cosine silhouette score within 0.0070 of scikit-learn (0.2319 vs 0.2388, well within the $\le 0.02$ requirement).
- **Added** `iepa/backend/db/mongo.py` using `motor` for asynchronous MongoDB Atlas operations across `users`, `learner_state`, and `analyses` collections with seamless local JSON fallback handlers.
- **Added** `iepa/backend/auth/oauth.py` integrating Authlib Google OAuth 2.0 and `python-jose` for signed JWT creation (`create_access_token`), token verification (`decode_access_token`), and FastAPI authentication dependencies (`get_current_user`, `get_optional_current_user`).
- **Updated** `iepa/backend/api/main.py`:
  - Added `GET /auth/google` (initiating OAuth with explicit HTTP 302 redirect).
  - Added `GET /auth/google/callback` (exchanging code, creating user in MongoDB Atlas, signing JWT, redirecting to frontend).
  - Added `GET /auth/me` (returning user profile and remaining monthly quota).
  - Enforced Freemium tier gating on `POST /analyze` (returns HTTP 429 when 20 monthly analyses are exceeded on free tier).
  - Configured `SessionMiddleware` for OAuth CSRF state handling.
- **Updated** `iepa/backend/sandbox/executor.py` with automatic daemon connection failure detection and direct subprocess execution fallback for cloud environments (Render) and local environments where Docker daemon is unreachable.
- **Updated** Frontend React SPA (`iepa/frontend`):
  - Added `src/context/AuthContext.jsx` with memoized callbacks (`useCallback`), ref guards (`useRef`), and token hydration to eliminate infinite `/auth/me` render loops.
  - Added `src/pages/Landing.jsx` with Google OAuth login CTA and platform architecture summary.
  - Added `src/pages/AuthCallback.jsx` with single-fire token extraction and protected route redirection.
  - Configured `react-router-dom` in `src/App.js` with `ProtectedRoute`, dynamic user avatar, remaining analyses quota display, and 429 quota limit banner handling.
- **Added** Cloud Deployment Configurations:
  - `render.yaml` at project root for Render Python 3.11 web service deployment.
  - `iepa/frontend/.env.production` configuring `REACT_APP_API_URL`.
  - `iepa/frontend/vercel.json` configuring SPA routing rewrites.
- **Added** Automated Test Suites:
  - `scripts/test_week2_pipeline.py` (KMeans scratch vs sklearn silhouette validation, MongoDB CRUD, JWT, Freemium gating).
  - `scripts/test_week2_final.py` (end-to-end live pipeline verification).
- **Updated** `requirements.txt` with `authlib`, `python-jose[cryptography]`, `motor`, `pymongo`, `dnspython`, `python-dotenv`, `itsdangerous`.
