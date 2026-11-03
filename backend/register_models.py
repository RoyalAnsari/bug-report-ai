import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent / ".env")

from app.core.config import Settings  # noqa: E402
from app.db.mongo import create_client  # noqa: E402
from app.repositories.model_versions import (  # noqa: E402
    build_duplicate_document,
    build_severity_document,
    upsert_version,
)

ARTIFACTS = Path(__file__).resolve().parents[1] / "ml" / "artifacts"
SEVERITY_METRICS = ARTIFACTS / "severity_experiments" / "metrics.json"
DUPLICATE_CONFIG = ARTIFACTS / "duplicates" / "config.json"


def read_json(path):
    if not path.exists():
        raise FileNotFoundError(f"{path.parent.name}\\{path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        documents = [
            build_severity_document(read_json(SEVERITY_METRICS)),
            build_duplicate_document(read_json(DUPLICATE_CONFIG)),
        ]
    except FileNotFoundError as error:
        print("File nahi mili:", error)
        raise SystemExit(1)

    settings = Settings.from_env()
    client = create_client(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    try:
        for document in documents:
            await upsert_version(db, document)
            evaluation = document.get("evaluation")
            score = f"test macro F1 = {evaluation['macro_f1']:.4f}" if evaluation else "evaluation: not measured"
            print(f"{document['name']} / {document['version']}: {score}")
    except Exception as error:
        print("Kaam nahi hua:", type(error).__name__, getattr(error, "code", None))
        raise SystemExit(1)
    finally:
        await client.close()


asyncio.run(main())