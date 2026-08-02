from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Ad
from app.schemas.ad import AdOut

router = APIRouter(prefix="/ads", tags=["ads"])


@router.get("", response_model=list[AdOut])
async def list_ads(db: AsyncSession = Depends(get_db)) -> list[AdOut]:
    result = await db.execute(select(Ad).order_by(Ad.title))
    ads = result.scalars().all()
    return [
        AdOut(
            ad_id=ad.ad_id,
            title=ad.title,
            body=ad.body,
            image_url=f"/static/ads/{ad.path}" if ad.path else None,
        )
        for ad in ads
    ]
