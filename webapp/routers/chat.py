from fastapi import APIRouter, Depends, Request, Response, status

from ..internal import security
from ..models import ChatMessage

router = APIRouter(
    prefix="/chat",
    dependencies=[Depends(security.get_current_active_user)],
    tags=["chat"]
)


@router.post("/")
async def send_chat_message(request: Request, payload: ChatMessage) -> str:
    action = {
        "target": "chat",
        "action": "send",
        "payload": {"payload": payload.message},
        "source": "webui",
    }
    request.app.p_q.put(action)
    return "Message sent."
