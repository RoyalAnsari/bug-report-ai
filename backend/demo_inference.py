import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from app.ml.inference import DuplicateFinder, SeverityPredictor  # noqa: E402

started = time.time()
severity = SeverityPredictor.from_artifact()
finder = DuplicateFinder.from_artifacts()
print("Models load hone mein seconds:", round(time.time() - started, 1))
print("Index mein reports:", len(finder.reports))

samples = [
    ("Firefox crashes when opening a PDF file", "Firefox"),
    ("Typo in error message", "Bugzilla"),
    ("Several UI packages missing javadoc", "Platform"),
]
for text, project in samples:
    result = severity.predict([text], [project])[0]
    print("\nReport:", text, f"[{project}]")
    print("  Severity:", result["label"], "| margin:", result["margin"], "| needs_review:", result["needs_review"])
    print("  Duplicate candidates (cosine similarity, probability nahi):")
    for hit in finder.find(text, top_k=3, threshold=0.0):
        print(f"    {hit['similarity']:.3f}  [{hit['bug_id']}] {hit['text'][:80]}")