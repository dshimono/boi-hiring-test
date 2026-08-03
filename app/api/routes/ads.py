from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import Ad
from app.schemas.ad import AdDetail, AdOut
from app.services import ad

router = APIRouter(prefix="/ads", tags=["ads"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[AdOut])
async def list_ads(db: AsyncSession = Depends(get_db)) -> list[AdOut]:
    result = await db.execute(select(Ad).order_by(Ad.title))
    ads = result.scalars().all()
    return [
        AdOut(
            ad_id=item.ad_id,
            title=item.title,
            body=item.body,
            image_url=f"/static/ads/{item.path}" if item.path else None,
        )
        for item in ads
    ]


@router.get("/{ad_id}", response_model=AdDetail)
async def get_ad_detail(ad_id: str, db: AsyncSession = Depends(get_db)) -> AdDetail:
    return await ad.get_ad_detail(db, ad_id)
