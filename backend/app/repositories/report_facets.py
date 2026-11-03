from app.db.collections import BUG_REPORTS


def clean_projects(values):
    """Removes empty values and repeats, and sorts the project names (ignoring capital letters)."""
    names = {str(value).strip() for value in values if value is not None and str(value).strip()}
    return sorted(names, key=str.lower)


async def list_projects(db):
    values = await db[BUG_REPORTS].distinct("project")
    return clean_projects(values)
