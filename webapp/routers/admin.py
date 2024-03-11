from fastapi import APIRouter, Depends, Request

from ..internal import security
from..models import GameInstruction, NewPermission

router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(security.get_current_active_user)],
    responses={404: {"description": "Not found"}},
)


@router.put("/game")
async def game_instruction(payload: GameInstruction, request: Request):
    new_instruction = payload.instruction

    if new_instruction == "close":
        action = {
            "target": "main",
            "action": "main_close",
            "payload": "",
            "source": "webui",
        }
        request.app.p_q.put(action)
        return {"description": "Close instruction issued to game."}
    elif new_instruction == "restart":
        action = {
            "target": "main",
            "action": "main_restart",
            "payload": "",
            "source": "webui",
        }
        request.app.p_q.put(action)
        return {"description": "Reset instruction issued to game."}


@router.get("/permission")
async def get_permission(name: str | None = None):
    if not name:
        name = "test"
    return {"permissions": [{name: 0}, {"player2": 1}]}


@router.put("/permission")
async def put_permission(payload: NewPermission):
    print(f"{payload.player} permission level updated to {payload.level}")
    return {payload.player: payload.level}
