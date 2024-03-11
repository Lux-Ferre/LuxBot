from fastapi import APIRouter, Depends, Request

from ..internal import security
from ..models import GameInstruction, Permission

router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(security.get_current_active_user)],
    responses={404: {"description": "Not found"}},
)


@router.put("/game")
async def game_instruction(request: Request, payload: GameInstruction) -> str:
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


@router.get("/permission")
async def get_permission(request: Request, name: str) -> Permission:
    level = request.app.db.permission_level({"player": name})

    response = Permission(player=name, level=level)
    return response


@router.put("/permission")
async def put_permission(request: Request, payload: Permission) -> Permission:
    update_data = {
        "updated_player": payload.player,
        "level": payload.level
    }

    request.app.db.update_permission(update_data)

    return payload
