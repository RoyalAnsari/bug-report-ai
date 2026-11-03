# How Bug Report AI works, and why these technologies

This document explains the flow of the project and the reason for each technology choice. For setup and commands, see [README.md](README.md).

## Overall flow

```
Browser (React)  ──►  FastAPI backend  ──►  MongoDB Atlas
                            │
                            └──►  ML models (severity, duplicates)
```

1. **Data comes in.** Bug reports are uploaded from a CSV file (or created by hand on the Reports page). The backend saves them in MongoDB Atlas. Importing the same file twice does not create duplicates.
2. **Severity is predicted.** The report text is turned into numbers with TF-IDF. A LinearSVC model then picks one of six labels: `blocker`, `critical`, `major`, `normal`, `minor`, `trivial`. The model also gives a *margin*, which shows how sure it is. If the margin is low, the prediction is marked **Needs review**. The margin limit can be changed on the Settings page.
3. **A person reviews.** The reviewer confirms the prediction or gives the correct label. The review is saved, and the report's severity is updated.
4. **Duplicates are suggested.** The MiniLM model turns each report into an embedding (a list of numbers). Reports with a higher cosine similarity are more alike. The backend returns the most similar reports as candidates, and a person confirms or rejects each one.
5. **The frontend shows everything.** The React pages call the backend API and display dashboards, tables and charts.
6. **Bulk predict.** After a CSV import, the Bulk predict page predicts all reports that have no prediction yet, in small steps with a progress bar and a Stop button.

## Technology choices

| Technology | Used for | Why it was chosen |
| --- | --- | --- |
| **TF-IDF + LinearSVC** | Severity prediction | A classic and fast text-classification method. It runs on a CPU and trains in minutes, so it works on an 8 GB laptop. Larger neural models such as DistilBERT would be very slow on this machine. |
| **all-MiniLM-L6-v2** | Text embeddings for duplicate search | A small, fast, pre-trained model that captures meaning, not only matching words. It needs no training of its own and runs on a laptop CPU. |
| **Cosine similarity** | Comparing two embeddings | The standard way to compare embeddings. The score is a similarity, **not a probability**. |
| **scikit-learn** | TF-IDF and LinearSVC | The most common Python toolkit for classical machine learning. |
| **FastAPI** | Backend API | Written in Python, so the ML models run directly inside it. It validates requests and generates the API documentation automatically. |
| **MongoDB Atlas** | Database | Reports, predictions and suggestions have flexible shapes (for example a list of scores), which suits a document database. Atlas is hosted in the cloud and has a free tier, so no local database is needed. |
| **React + TypeScript** | Frontend | React makes pages and components easy to build. TypeScript catches mistakes such as wrong names or types before the app runs. |
| **Tailwind CSS** | Styling | Styling is written directly in the components, which gives a clean layout quickly. |
| **Vite** | Frontend dev server and build | A fast development server, and `npm run build` creates the production files. |
| **pytest and Vitest** | Tests | pytest for the backend and ML code, Vitest for the frontend. They show that new changes did not break existing behaviour. |

## Honest limitations

- **The severity model is weak.** Macro F1 is about 0.42, and about 81% of reports are `normal`, so the model leans toward `normal` and is poor at `major`, `minor` and `trivial`. This is why low-confidence predictions are marked for human review.
- **Duplicate detection was not measured.** The dataset has no verified duplicate pairs, so precision and recall are unknown, and the default similarity threshold of 0.80 is untested.
- **No authentication.** Anyone who can reach the backend can read and change data.
- **Backend tests use fakes**, not a real MongoDB, so database behaviour is not covered by integration tests yet.

This is a course prototype. It should not be presented as production-ready.
