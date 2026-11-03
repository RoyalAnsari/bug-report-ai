# Bug Report AI

A course project that helps triage bug reports. It does two things:

1. **Severity prediction**: predicts how severe a bug report is (6 classes) and lets a person confirm or correct the prediction.
2. **Duplicate detection**: finds reports that look similar to a given report, using sentence embeddings, and lets a person confirm or reject each suggestion.

Around these two models there is a web app: upload reports from a CSV file, browse and search them, predict severity for one report or for all reports at once, review predictions and duplicate suggestions, and look at model performance.

> **Status: course prototype, not production-ready.**
> There is no authentication, and the severity model is weak (see [Model quality](#model-quality)). Do not use it to make real decisions.

---

## Contents

- [Tech stack](#tech-stack) (a longer explanation is in [HOW_IT_WORKS.md](HOW_IT_WORKS.md))
- [Project structure](#project-structure)
- [Data](#data)
- [Model quality](#model-quality)
- [Features](#features)
- [Setup on Windows](#setup-on-windows)
- [Running the project](#running-the-project)
- [Running the tests](#running-the-tests)
- [Bulk predict](#bulk-predict)
- [Troubleshooting](#troubleshooting)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)

---

## Tech stack

| Part | Technology |
| --- | --- |
| Severity model | TF-IDF + LinearSVC (scikit-learn) |
| Duplicate model | `sentence-transformers/all-MiniLM-L6-v2` embeddings + cosine similarity |
| Backend | FastAPI (Python), MongoDB Atlas |
| Frontend | React, TypeScript, Tailwind CSS (Vite) |
| Tests | pytest (backend and ML), Vitest (frontend) |

## Project structure

```
bug-report-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # API routes (reports, uploads, predictions, reviews, duplicates, dashboard, settings, ...)
│   │   ├── repositories/       # all MongoDB access
│   │   ├── schemas/            # request and response models
│   │   ├── services/           # business logic
│   │   └── main.py             # FastAPI app
│   ├── tests/                  # backend tests
│   ├── check_db.py             # checks the MongoDB connection
│   ├── init_db.py              # creates database indexes, can import sample reports
│   ├── register_models.py      # stores model metrics for the Model performance page
│   ├── demo_inference.py       # small prediction demo
│   └── .env.example            # copy to .env and fill in
├── frontend/
│   └── src/                    # pages, components, services, tests
├── ml/
│   ├── data/                   # raw and processed (train / val / test) data
│   ├── artifacts/              # trained models and the duplicate-search index
│   └── tests/                  # data and model tests
├── sample_data/                # small example CSV files for testing the upload page
└── README.md
```

## Data

- Source: the Bugzilla / Eclipse bug report dataset from Hugging Face.
- Raw file: `ml\data\raw\bugzilla_eclipse\filtered_data.xlsx - Sheet1.csv`. Cleaned splits are in `ml\data\processed` (`train.csv`, `val.csv`, `test.csv`).
- Raw dataset: 88,682 rows, 5 columns, 6 severity labels, no missing values.
- Class balance is very uneven: `normal` is about 81.4% of the rows and `blocker` only about 0.9%.
- After cleaning: 87,716 rows.
- Split (stratified, seed 42, no overlap between sets): 70,172 train, 8,772 validation, 8,772 test.

The severity labels are: `blocker`, `critical`, `major`, `normal`, `minor`, `trivial`.

## Model quality

**Severity model (TF-IDF + LinearSVC)**

- Test macro F1: **0.416** (0.422 with the improved version).
- `critical` and `normal` work reasonably well. `major`, `minor` and `trivial` are weak.
- Class weights helped. Resampling did not.
- Because of this, the app marks low-confidence predictions as **Needs review** and asks a person to confirm or correct them. The review margin can be changed on the Settings page.

**Duplicate model (MiniLM embeddings)**

- Embeddings were built for all 87,716 reports and a cosine-similarity index is used to find candidates.
- The dataset has **no verified duplicate pairs**, so precision and recall could not be measured.
- The default similarity threshold (`0.80`) has not been tested. The score is a cosine similarity, **not a probability**.
- Every suggestion therefore needs a human to confirm or reject it.

## Features

**Backend (FastAPI)**

- Health check and model metadata.
- Reports: list, filter, search, sort, pagination, create, update, delete. Deleting a report also deletes its predictions, duplicate suggestions and review feedback.
- CSV upload with preview and import. Importing the same file again does not create duplicates.
- Severity prediction for one report, and review (confirm or correct).
- Bulk severity prediction (see [Bulk predict](#bulk-predict)).
- Duplicate candidates for a report, and a duplicate review queue.
- Dashboard numbers.
- Settings (review margin and duplicate defaults).
- Consistent error format, CORS, and OpenAPI docs (the app header has an **API docs** link).

**Frontend (React)**

- **Dashboard**: totals, severity chart, pending reviews, duplicate suggestions.
- **Reports**: search, filters, sorting, pagination, detail page with *Predict severity* and *Review*.
- **Upload**: drag and drop, preview, column mapping, row errors, import.
- **Bulk predict**: predict all reports that have no prediction yet, with progress and a Stop button.
- **Duplicates**: candidates per report, plus a separate review queue.
- **Model performance**: F1, precision, recall, confusion matrix.
- **Settings**, **System status**.

## Setup on Windows

You need: Python 3, Node.js (with npm), and a MongoDB Atlas cluster (the free tier is enough).

The commands below work in **cmd**. In PowerShell, replace `%USERPROFILE%` with `$env:USERPROFILE`, and use `.venv\Scripts\Activate.ps1` to activate the virtual environment.

**1. Open a terminal in the project folder**

```
cd path\to\bug-report-ai
```

**2. Create and activate a virtual environment**

```
python -m venv .venv
.venv\Scripts\activate
```

**3. Install the Python packages**

```
pip install -r requirements.txt
```

(`requirements.txt` is in the project root.)

**4. Install the frontend packages**

```
npm --prefix frontend install
```

**5. Configure the database**

Copy `backend\.env.example` to `backend\.env` and fill in your MongoDB Atlas connection details:

```
copy backend\.env.example backend\.env
```

Settings in `backend\.env`:

| Variable | Meaning | Example |
| --- | --- | --- |
| `MONGODB_URI` | MongoDB Atlas connection string (contains your password) | `mongodb+srv://...` |
| `MONGODB_DB` | Database name | `bug_report_ai` |
| `CORS_ORIGINS` | Frontend address that may call the API | `http://localhost:5173` |
| `REVIEW_MARGIN` | Predictions with a margin below this value are marked *Needs review* (can also be changed on the Settings page) | `0.25` |
| `LOAD_MODELS` | Whether the backend loads the ML models when it starts | `true` |

Never commit `backend\.env` to Git, because it contains your database password. It is already listed in `.gitignore`.

In Atlas you must also:

- create a database user (username and password), and
- add your current IP address under **Network Access** (see [Troubleshooting](#troubleshooting)).

**6. Check the database connection**

```
cd backend
python check_db.py
cd ..
```

It should connect without an error before you start the backend.

**7. Create the database indexes and (optionally) load sample reports**

Run this once from the `backend` folder:

```
cd backend
python init_db.py --import-sample 2000
cd ..
```

- `init_db.py` creates the collections' indexes in MongoDB and prints them.
- `--import-sample 2000` also imports 2,000 randomly chosen reports from `ml\data\processed` (train, validation and test files), so the app has data to show. Use another number for more or fewer reports, or leave the option out to create only the indexes. Running it again does not create duplicates.

**8. Register the trained models**

This stores the model information (such as test macro F1) that the *Model performance* page shows. It needs the trained models in `ml\artifacts` (see [Data and model files are not in Git](#data-and-model-files-are-not-in-git)).

```
cd backend
python register_models.py
cd ..
```

It prints one line per model, for example the severity model with its test macro F1. If it says a file was not found, the files in `ml\artifacts` are missing.

## Data and model files are not in Git

`.gitignore` excludes `ml\data\raw\` (the raw dataset) and `ml\artifacts\` (trained models and the duplicate-search index) because they are large. After cloning the repository you must copy these folders from the original machine, or download the dataset and rebuild the models, before the backend can predict and before the ML tests can pass.

## Running the project

Use two terminals.

**Terminal 1: backend** (from the `backend` folder, with the virtual environment active)

```
cd backend
uvicorn app.main:app --reload --port 8000
```

The backend must be started with the models loaded; the first start can take a while because the embedding model is loaded.

**Terminal 2: frontend**

```
npm --prefix frontend run dev
```

Open the address that Vite prints (usually `http://localhost:5173`).

For a production build of the frontend: `npm --prefix frontend run build`.

## Running the tests

From the project root:

```
python -m pytest ml\tests backend\tests -q
npm --prefix frontend run test
npm --prefix frontend run build
```

Latest results: **192** backend and ML tests passed, **90** frontend tests passed, and the frontend build succeeds. The backend tests do not use a real MongoDB; they use fakes. There are no integration tests against a real database yet.

## Bulk predict

Page: `/predict`.

1. Open **Bulk predict**. Three cards show total reports, reports with a prediction, and reports without one.
2. Choose **Reports per step** (100, 200 or 500). The page calls the backend repeatedly in small steps, so a laptop with 8 GB of RAM is not overloaded.
3. Click **Predict all unpredicted reports**. A progress bar shows how many reports are done.
4. **Stop** finishes the current step and then stops.
5. It is safe to run again: only reports that have no prediction are predicted, so after a Stop it continues where it left off.
6. At the end a summary shows how many reports were predicted, how many need review, and how many are still without a prediction.

Backend endpoints:

- `GET /api/v1/predictions/bulk/status`
- `POST /api/v1/predictions/bulk` (1 to 500 reports per call; the model works in batches of 256 internally)

## Troubleshooting

**The backend cannot connect to MongoDB Atlas**

- Open Atlas, go to **Network Access**, and add your current IP address. Home and mobile networks often change IP address, so this has to be updated when it changes. For a quick test you can allow `0.0.0.0/0`, but remove it afterwards.
- Check that the username and password in your connection string are correct. If the password contains special characters, URL-encode them.
- Some networks block port **27017**, which MongoDB uses. If `python check_db.py` hangs or times out, try another network (for example a phone hotspot).
- Run `python check_db.py` again after each change.

**"No module named ..." or import errors**

- The virtual environment is probably not active. The prompt should start with `(.venv)`. Activate it and try again.
- Run the tests from the project root, not from inside `backend`.

**`%USERPROFILE%` or `Select-String` "is not recognized"**

- You are mixing cmd and PowerShell. `%USERPROFILE%` and `findstr` are cmd; `$env:USERPROFILE` and `Select-String` are PowerShell.

**The page shows old content or a menu item is missing**

- Restart both the backend and the frontend, then hard refresh the browser with `Ctrl + Shift + R`. New API endpoints only appear after the backend restarts.

**Port already in use**

- Another copy is still running. Stop it with `Ctrl + C`, or run on another port (for example `--port 8001`).

**Bulk predict cards do not load**

- The cards read from MongoDB. Check the database connection first.

## Known limitations

- No authentication or authorization. Anyone who can reach the backend can read and change data.
- Severity model quality is low (macro F1 about 0.42), especially for `major`, `minor` and `trivial`.
- Duplicate detection is untested against labelled data; precision and recall are unknown.
- Backend tests use fakes; there are no integration tests against a real MongoDB yet.
- The main frontend JavaScript file is large (about 691 kB); route-level lazy loading is not done yet.
- Docker is not set up yet.

## Roadmap

- Lazy loading for the frontend routes.
- Integration tests with a real MongoDB.
- EDA notebook for the dataset (missing values, duplicates, class balance).
- Docker and Docker Compose (backend, frontend, MongoDB, health checks).
- Optional: fine-tune a DistilBERT model for severity (slow on a CPU-only laptop).
- Optional: train a duplicate model once labelled duplicate pairs are available.
