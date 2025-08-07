from fastapi import APIRouter, Depends

from app.api.v1.schemas.organism import OrganismResponse
from app.api.v1.schemas.response import ResponseList
from app.db.repositories.organism import OrganismRepository, Filters
from app.db.models.user import User
from app.services.auth import get_current_user_optional

organisms_router = APIRouter(prefix="/organisms", tags=["organisms"])


@organisms_router.get("/")
async def get_organisms(include_public: bool = True,
                        organism_repository: OrganismRepository = Depends(),
                        user: User | None = Depends(get_current_user_optional)) -> ResponseList[OrganismResponse]:
    """
    Get a list of organisms of a logged-in user.
    """

    filters = Filters(
        user_id=user.id if user is not None else None,
        include_public=include_public
    )

    organisms = await organism_repository.get(filters)
    data = [OrganismResponse.model_validate(organism) for organism in organisms]
    return ResponseList(data=data)

# TODO: Add organism creation / deletion via Admin panel
