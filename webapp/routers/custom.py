from fastapi import APIRouter, Depends, Request, Response, status

from ..internal import security
from ..models import AnwinCustomMessage

router = APIRouter(
    prefix="/custom",
    dependencies=[Depends(security.get_current_active_user)],
    responses={404: {"description": "Not found"}},
    tags=["customs"]
)


@router.put("/send")
async def send_custom(request: Request, payload: AnwinCustomMessage) -> str:
    action_payload = {}
    for data_point in payload:
        if data_point[1]:
            action_payload[data_point[0]] = data_point[1]

    action = {
        "target": "custom",
        "action": "send",
        "payload": action_payload,
        "source": "webui",
    }
    request.app.p_q.put(action)
    return "Message sent."
