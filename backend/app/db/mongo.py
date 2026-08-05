import logging

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger("lexassist.db")

_client: AsyncIOMotorClient | None = None


def connect() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.mongo_uri)


def disconnect() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_database() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("Mongo client not initialized — connect() must run at app startup.")
    return _client[settings.mongo_db_name]


async def ensure_indexes() -> None:
    """Creates all required indexes at startup (idempotent — a no-op once
    they exist). Without these, every owner_id/token lookup is a full
    collection scan, and — critically — registration has a race that lets
    two concurrent requests create duplicate accounts for the same email.
    The unique indexes enforce data integrity the app logic assumes."""
    db = get_database()

    # --- users ---
    # Unique email closes the register TOCTOU race (find_one-then-insert)
    # AND enforces the "one account per email" invariant at the DB level.
    await db.users.create_index("email", unique=True)
    # Password-reset / e-mail-verification look users up by hashed token on
    # a security-hot path — sparse because most user docs have no token set.
    await db.users.create_index("reset_token_hash", sparse=True)
    await db.users.create_index("verification_token_hash", sparse=True)

    # --- per-user collections (every query filters by owner_id) ---
    await db.cases.create_index("owner_id")
    await db.uploads.create_index("owner_id")
    await db.uploads.create_index("case_id")
    await db.activity.create_index([("owner_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
    await db.activity.create_index("case_id")
    await db.notifications.create_index([("owner_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
    await db.chat_messages.create_index(
        [("owner_id", pymongo.ASCENDING), ("case_id", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)]
    )
    # ai_results is upserted on (owner_id, case_id, type) — the unique index
    # makes that upsert key enforced, so a case can't accumulate duplicate
    # summary/risk/draft rows.
    await db.ai_results.create_index(
        [("owner_id", pymongo.ASCENDING), ("case_id", pymongo.ASCENDING), ("type", pymongo.ASCENDING)],
        unique=True,
    )
    # preferences is one doc per user, upserted on owner_id.
    await db.preferences.create_index("owner_id", unique=True)
    # folders: fast per-user listing + a folder slug is unique within a user.
    await db.folders.create_index([("owner_id", pymongo.ASCENDING), ("slug", pymongo.ASCENDING)], unique=True)

    logger.info("MongoDB indexes ensured.")
