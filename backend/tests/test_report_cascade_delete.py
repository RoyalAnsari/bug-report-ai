import asyncio
from types import SimpleNamespace

from app.db.collections import (
    BUG_REPORTS,
    DUPLICATE_SUGGESTIONS,
    PREDICTIONS,
    REVIEW_FEEDBACK,
)
from app.repositories import report_crud


class FakeCollection:
    """Chhota sa in-memory collection, sirf delete ke tests ke liye."""

    def __init__(self, docs):
        self.docs = list(docs)

    @staticmethod
    def _matches(doc, query):
        return all(doc.get(key) == value for key, value in query.items())

    async def delete_one(self, query):
        for doc in self.docs:
            if self._matches(doc, query):
                self.docs.remove(doc)
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    async def delete_many(self, query):
        keep = [doc for doc in self.docs if not self._matches(doc, query)]
        removed = len(self.docs) - len(keep)
        self.docs = keep
        return SimpleNamespace(deleted_count=removed)


class FakeDb:
    def __init__(self, data):
        self.collections = {name: FakeCollection(docs) for name, docs in data.items()}

    def __getitem__(self, name):
        return self.collections[name]


def make_db():
    return FakeDb(
        {
            BUG_REPORTS: [{"_id": "br_1"}, {"_id": "br_2"}],
            PREDICTIONS: [
                {"_id": "pred_a", "report_id": "br_1"},
                {"_id": "pred_b", "report_id": "br_1"},
                {"_id": "pred_c", "report_id": "br_2"},
            ],
            DUPLICATE_SUGGESTIONS: [
                {"_id": "dup_a", "report_id": "br_1"},
                {"_id": "dup_b", "report_id": "br_2"},
            ],
            REVIEW_FEEDBACK: [
                {"_id": "fb_pred_a", "report_id": "br_1"},
                {"_id": "fb_pred_c", "report_id": "br_2"},
            ],
        }
    )


def ids(db, name):
    return [doc["_id"] for doc in db[name].docs]


def test_delete_report_removes_its_predictions_suggestions_and_feedback():
    db = make_db()
    assert asyncio.run(report_crud.delete_report(db, "br_1")) is True

    assert ids(db, BUG_REPORTS) == ["br_2"]
    assert ids(db, PREDICTIONS) == ["pred_c"]
    assert ids(db, DUPLICATE_SUGGESTIONS) == ["dup_b"]
    assert ids(db, REVIEW_FEEDBACK) == ["fb_pred_c"]


def test_delete_missing_report_returns_false_and_keeps_other_reports_data():
    db = make_db()
    assert asyncio.run(report_crud.delete_report(db, "br_missing")) is False

    assert ids(db, BUG_REPORTS) == ["br_1", "br_2"]
    assert len(ids(db, PREDICTIONS)) == 3
    assert len(ids(db, DUPLICATE_SUGGESTIONS)) == 2
    assert len(ids(db, REVIEW_FEEDBACK)) == 2
