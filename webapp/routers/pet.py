from fastapi import APIRouter, Depends, Request, HTTPException

from ..internal import security
from ..models import PetLink

router = APIRouter(
    prefix="/pet",
    dependencies=[Depends(security.get_current_active_user)],
    tags=["pets"]
)


@router.get("/")
async def get_random_pet_link(request: Request, name: str | None = None) -> PetLink:
    if name:
        request_payload = {"pet": name}
    else:
        request_payload = {}
    pet_data = request.app.db.get_pet_link(request_payload)

    if pet_data:
        response_body = PetLink(title=pet_data[0], name=pet_data[1], url=pet_data[2])
        return response_body
    else:
        raise HTTPException(status_code=204, detail="Pet name does not exist.")


@router.get("/title")
async def get_pet_link_by_title(request: Request, title: str) -> PetLink:

    pet_data = request.app.db.get_pet_link_by_title({"title": title})
    if pet_data:
        response_body = PetLink(title=pet_data[0], name=pet_data[1], url=pet_data[2])
        return response_body
    else:
        raise HTTPException(status_code=204, detail="Photo title does not exist.")


@router.post("/")
async def add_pet_photo_to_db(request: Request, payload: PetLink) -> PetLink:
    if "prnt.sc" not in payload.url:
        raise HTTPException(status_code=400, detail="Photo must be hosted at prnt.sc")
    pet_data = (payload.title, payload.name, payload.url)

    error_data = request.app.db.add_pet(pet_data)

    if error_data["has_error"]:
        raise HTTPException(status_code=400, detail="Integrity error: Title already exists.")
    else:
        return payload
