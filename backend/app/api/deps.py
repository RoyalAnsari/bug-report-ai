from fastapi import HTTPException, Request


def get_db(request: Request):
    """Endpoint ko database deta hai. Na ho to saaf 503 error."""
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    return db