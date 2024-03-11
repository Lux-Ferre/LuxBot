from fastapi import APIRouter, Depends, Request, Response, status

from ..internal import security
from ..models import ChatMessage

router = APIRouter(
    prefix="/chat",
    dependencies=[Depends(security.get_current_active_user)],
    responses={404: {"description": "Not found"}},
)


@router.put("/send")
async def game_instruction(request: Request, payload: ChatMessage) -> str:
    action = {
        "target": "chat",
        "action": "send",
        "payload": {"payload": payload.message},
        "source": "webui",
    }
    request.app.p_q.put(action)
    return "Message sent."
