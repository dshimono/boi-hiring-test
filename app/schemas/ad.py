from pydantic import BaseModel


class AdOut(BaseModel):
    ad_id: str
    title: str
    body: str | None
    image_url: str | None
