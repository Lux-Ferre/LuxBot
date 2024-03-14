from fastapi import APIRouter, Depends, Request, HTTPException

from ..internal import security
from ..models import AutomodTrigger, PlayerMute

router = APIRouter(
    prefix="/mod",
    dependencies=[Depends(security.get_current_active_user)],
    tags=["moderation"]
)


@router.get("/triggers")
async def get_all_automoderation_triggers(request: Request) -> list[str]:
    flag_words_dict = request.app.db.read_config_row({"key": "automod_flag_words"})
    trigger_list = flag_words_dict["word_list"].split(",")

    return trigger_list


@router.post("/trigger")
async def add_new_trigger_to_db(request: Request, payload: AutomodTrigger) -> AutomodTrigger:
    flag_words_dict = request.app.db.read_config_row({"key": "automod_flag_words"})
    trigger_list = flag_words_dict["word_list"].split(",")

    trigger_list.append(payload.trigger_word)
    trigger_dict = {"word_list": ",".join(trigger_list)}
    db_payload = {
        "key": "automod_flag_words",
        "value": trigger_dict
    }
    request.app.db.set_config_row(db_payload)

    return payload


@router.delete("/trigger")
async def remove_trigger_from_db(request: Request, payload: AutomodTrigger) -> list[str]:
    flag_words_dict = request.app.db.read_config_row({"key": "automod_flag_words"})
    trigger_list = flag_words_dict["word_list"].split(",")

    try:
        trigger_list.remove(payload.trigger_word)
    except ValueError:
        raise HTTPException(status_code=204, detail="Trigger does not exist.")

    trigger_dict = {"word_list": ",".join(trigger_list)}
    db_payload = {
        "key": "automod_flag_words",
        "value": trigger_dict
    }
    request.app.db.set_config_row(db_payload)

    return trigger_list


@router.post("/mute")
async def mute_player(request: Request, payload: PlayerMute) -> PlayerMute:
    if not 0 <= payload.length < 999999:
        raise HTTPException(status_code=422, detail="Length must be between 0 and 999999 inclusive.")

    mute_data = f"MUTE={payload.target}~{payload.length}~{payload.reason}~{payload.is_ip}"

    mute_action = {
        "target": "game",
        "action": "send_ws_message",
        "payload": mute_data,
        "source": "webapp",
    }

    request.app.p_q.put(mute_action)
    return payload
