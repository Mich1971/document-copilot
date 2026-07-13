import logging

from fastapi import APIRouter, Depends

from app.auth.dependencies import CurrentUser, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/me")
async def me(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, object]:
    logger.info("Auth /me called for user %s", current_user.email)
    return {
        "ok": True,
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
        },
    }
