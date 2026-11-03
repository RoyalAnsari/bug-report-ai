from app.db.collections import DUPLICATE_SUGGESTIONS, INDEXES, MODEL_VERSIONS


def test_all_five_collections_have_indexes():
    assert set(INDEXES) == {
        "bug_reports",
        "predictions",
        "duplicate_suggestions",
        "review_feedback",
        "model_versions",
    }


def test_duplicate_pair_index_is_unique():
    documents = {i.document["name"]: i.document for i in INDEXES[DUPLICATE_SUGGESTIONS]}
    assert documents["pair_unique_idx"].get("unique") is True


def test_model_version_index_is_unique():
    documents = {i.document["name"]: i.document for i in INDEXES[MODEL_VERSIONS]}
    assert documents["name_version_unique_idx"].get("unique") is True