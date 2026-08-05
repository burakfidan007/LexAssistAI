"""Folder business logic (seeding defaults, slugging, ownership lookups).

Lives in the service layer so both the folders controller AND cases.move
can use it without a router-to-router import (which previously forced a
lazy in-function import to dodge a circular dependency)."""

import re
from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

# Seeded once per user. Slugs match the values existing cases already store
# in their `folder` field, so old data keeps working after this migration.
DEFAULT_FOLDERS = [
    ("is-hukuku", "İş Hukuku", "briefcase"),
    ("ceza-hukuku", "Ceza Hukuku", "gavel"),
    ("aile-hukuku", "Aile Hukuku", "users"),
    ("ticaret-hukuku", "Ticaret Hukuku", "building-2"),
    ("icra-dosyalari", "İcra Dosyaları", "file-warning"),
]

_TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")


def slugify(name: str) -> str:
    slug = name.translate(_TR_MAP).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug or "klasor"


async def ensure_defaults(db: AsyncIOMotorDatabase, owner_id: ObjectId) -> None:
    if await db.folders.count_documents({"owner_id": owner_id}) > 0:
        return
    now = datetime.now(timezone.utc)
    await db.folders.insert_many([
        {
            "owner_id": owner_id, "slug": slug, "name": name, "icon": icon,
            "is_default": True, "created_at": now,
        }
        for slug, name, icon in DEFAULT_FOLDERS
    ])


async def unique_slug(db: AsyncIOMotorDatabase, owner_id: ObjectId, base: str) -> str:
    slug = base
    n = 2
    while await db.folders.find_one({"owner_id": owner_id, "slug": slug}):
        slug = f"{base}-{n}"
        n += 1
    return slug


async def user_folder_slugs(db: AsyncIOMotorDatabase, owner_id: ObjectId) -> set[str]:
    """Set of folder slugs the user owns — used to validate case moves."""
    await ensure_defaults(db, owner_id)
    folders = await db.folders.find({"owner_id": owner_id}, {"slug": 1}).to_list(200)
    return {f["slug"] for f in folders}
