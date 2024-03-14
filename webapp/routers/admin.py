from fastapi import APIRouter, Depends, Request, HTTPException

from ..internal import security
from ..models import GameInstruction, Permission

router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(security.get_current_active_user)],
    tags=["admin"]
)


@router.put("/game")
async def issue_game_instruction(request: Request, payload: GameInstruction) -> str:
    new_instruction = payload.instruction

    if new_instruction == "close":
        action = {
            "target": "main",
            "action": "main_close",
            "payload": "",
            "source": "webui",
        }
        request.app.p_q.put(action)
        return "Close instruction issued to game."
    elif new_instruction == "restart":
        action = {
            "target": "main",
            "action": "main_restart",
            "payload": "",
            "source": "webui",
        }
        request.app.p_q.put(action)
        return "Reset instruction issued to game."
    else:
        raise HTTPException(status_code=422, detail="Invalid instruction")


@router.get("/permission")
async def get_permission_by_name(request: Request, name: str) -> Permission:
    level = request.app.db.permission_level({"player": name})

    response_body = Permission(player=name, level=level)
    return response_body


@router.put("/permission")
async def set_permission(request: Request, payload: Permission) -> Permission:
    if not -2 <= payload.level <= 3:
        raise HTTPException(status_code=422, detail="Permission must be between -2 and 3 inclusive.")

    update_data = {
        "updated_player": payload.player,
        "level": payload.level
    }

    request.app.db.update_permission(update_data)

    return payload
