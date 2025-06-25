from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pathlib import Path

from app.auth.decorators import require_admin

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
router = APIRouter(prefix="/admin", tags=["system_settings"])

@router.get("/system-settings", response_class=HTMLResponse)
async def system_settings(
    request: Request,
    current_user: dict = Depends(require_admin())
):
    return templates.TemplateResponse(
        "admin/system_settings.html",
        {"request": request, "user": current_user}
    ) 