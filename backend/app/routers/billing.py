from fastapi import APIRouter, Depends

from app.db.mongo import get_database
from app.deps import get_current_user
from app.models.user import UserPublic
from app.routers.auth import _to_public
from app.services.activity import log_activity
from app.services.notifications import create_notification

router = APIRouter(prefix="/billing", tags=["billing"])

# No payment gateway is wired up yet (no Stripe/iyzico keys configured) —
# these endpoints flip `plan` directly so the rest of the app has a real,
# persistent plan to read instead of a client-side-only fake. Swap the
# body for a real checkout/webhook flow when a gateway is introduced.


@router.post("/upgrade", response_model=UserPublic)
async def upgrade_plan(current_user: dict = Depends(get_current_user)):
    db = get_database()
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": {"plan": "premium"}})
    current_user["plan"] = "premium"
    await log_activity(db, current_user["_id"], "plan_upgraded", "Premium plana yükseltildi")
    await create_notification(
        db, current_user["_id"], "system", "Premium'a Yükseltildi", "Hesabınız Premium plana yükseltildi."
    )
    return _to_public(current_user)


@router.post("/downgrade", response_model=UserPublic)
async def downgrade_plan(current_user: dict = Depends(get_current_user)):
    db = get_database()
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": {"plan": "free"}})
    current_user["plan"] = "free"
    return _to_public(current_user)
