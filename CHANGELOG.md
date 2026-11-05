# Changelog

## Version 2 (in progress, branch `version-2-transformer`)

- Goal: try a transformer (DistilBERT) for severity prediction and compare it with version 1 on the same data split.
- Keep version 1 working. The new model files go in their own folder, `ml/artifacts/severity_transformer`.

## Version 1.0

Severity prediction
- TF-IDF (word and character features, project name) with LinearSVC, class weights, and tuned class offsets.
- Validation macro F1 0.433, test macro F1 0.422. `normal` and `critical` work reasonably well; `major`, `minor` and `trivial` are weak.

Duplicate detection
- `all-MiniLM-L6-v2` embeddings of 87,716 reports with cosine similarity.
- Precision and recall are not measured yet (no labelled duplicate pairs). Tools to label pairs and to measure precision from reviewed suggestions are included (`ml/src/make_label_sheet.py`, `ml/src/evaluate_duplicates.py`, `backend/duplicate_review_stats.py`).

Application
- FastAPI and MongoDB Atlas backend, React and TypeScript frontend.
- Reports (search, filters, sorting), CSV upload, single and bulk severity prediction, review of predictions, duplicate suggestions and review queue, dashboard, model performance page, settings.
- Login with admin and reviewer roles, users and account pages, account lock after repeated wrong passwords, security headers, API docs off by default.
- Dockerfiles, Docker Compose, GitHub Actions workflow and a deployment guide are written (`DEPLOY.md`). They have not been used on a real host yet.

Known limits of version 1
- The severity model is weak (macro F1 about 0.42).
- Duplicate detection quality is unknown.
- No email-based password reset, no two-factor login, no per-user datasets.
- The trained model files are not stored in Git (they are in `ml/artifacts`, about 1 GB; the part the backend needs is about 250 MB).
