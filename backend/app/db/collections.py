from pymongo import ASCENDING, DESCENDING, IndexModel

BUG_REPORTS = "bug_reports"
PREDICTIONS = "predictions"
DUPLICATE_SUGGESTIONS = "duplicate_suggestions"
REVIEW_FEEDBACK = "review_feedback"
MODEL_VERSIONS = "model_versions"
USERS = "users"

INDEXES = {
    BUG_REPORTS: [
        IndexModel([("external_id", ASCENDING)], name="external_id_idx"),
        IndexModel([("severity", ASCENDING)], name="severity_idx"),
        IndexModel([("project", ASCENDING)], name="project_idx"),
        IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
        IndexModel([("text", "text")], name="text_search_idx"),
    ],
    PREDICTIONS: [
        IndexModel([("report_id", ASCENDING), ("created_at", DESCENDING)], name="report_created_idx"),
        IndexModel([("needs_review", ASCENDING)], name="needs_review_idx"),
    ],
    DUPLICATE_SUGGESTIONS: [
        IndexModel([("report_id", ASCENDING), ("candidate_id", ASCENDING)], name="pair_unique_idx", unique=True),
        IndexModel([("status", ASCENDING)], name="status_idx"),
    ],
    REVIEW_FEEDBACK: [
        IndexModel([("target_type", ASCENDING), ("target_id", ASCENDING)], name="target_idx"),
        IndexModel([("created_at", DESCENDING)], name="created_at_idx"),
    ],
    MODEL_VERSIONS: [
        IndexModel([("name", ASCENDING), ("version", ASCENDING)], name="name_version_unique_idx", unique=True),
    ],
    USERS: [
        IndexModel([("email", ASCENDING)], name="email_unique_idx", unique=True),
    ],
}


async def ensure_indexes(db):
    """Saare indexes banata hai. Dobara chalane se koi nuqsan nahi hota."""
    for collection_name, indexes in INDEXES.items():
        await db[collection_name].create_indexes(indexes)
