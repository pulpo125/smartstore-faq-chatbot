from fastapi import APIRouter

# ==================================================
router = APIRouter()
# ==================================================


@router.get("", tags=["healthcheck"])
def healthcheck():
    msg = "OK"
    return {"success": True, "message": msg}
