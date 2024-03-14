from fastapi import APIRouter, Depends, Request, HTTPException

from ..internal import security
from ..models import NewStat

router = APIRouter(
    prefix="/stats",
    dependencies=[Depends(security.get_current_active_user)],
    tags=["stats"]
)


@router.get("/")
async def get_stats(request: Request, stat: str | None = None) -> dict:
    chat_stats = request.app.db.read_config_row({"key": "chat_stats"})

    if stat:
        requested_stat = chat_stats.get(stat, None)
        if requested_stat is None:
            raise HTTPException(status_code=402, detail="Requested stat does not exist.")
        else:
            return {stat: chat_stats[stat]}
    else:
        return chat_stats


@router.post("/")
async def create_new_tracking_point(request: Request, payload: NewStat) -> NewStat:
    current_stats = request.app.db.read_config_row({"key": "chat_stats"})
    if payload.stat in current_stats:
        raise HTTPException(status_code=400, detail="Stat already exists.")

    current_stats[payload.stat] = 0

    update_data = {
        "key": "chat_stats",
        "value": current_stats
    }
    request.app.db.set_config_row(update_data)

    return payload


@router.get("/one_life_deaths")
async def get_one_life_deaths(request: Request, stat: str | None = None) -> dict:
    chat_stats = request.app.db.read_config_row({"key": "one_life_killers"})
    chat_stats["total"] = request.app.db.read_config_row({"key": "chat_stats"})["oneLifeDeaths"]

    if stat:
        requested_stat = chat_stats.get(stat, None)

        if requested_stat is None:
            raise HTTPException(status_code=402, detail="Requested stat does not exist.")
        else:
            return {stat: chat_stats[stat]}
    else:
        return chat_stats
