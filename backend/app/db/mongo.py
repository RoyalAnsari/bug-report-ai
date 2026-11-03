from pymongo import AsyncMongoClient


def create_client(uri, timeout_ms=5000):
    """MongoDB client banata hai. Connection tab tak nahi banta jab tak pehli query na ho."""
    if not uri:
        raise ValueError("MONGODB_URI is not set")
    return AsyncMongoClient(uri, serverSelectionTimeoutMS=timeout_ms, tz_aware=True)

async def ping(client, db_name):
    """Database se rabta check karta hai."""
    await client[db_name].command("ping")
    return True