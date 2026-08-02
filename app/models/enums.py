import enum

from sqlalchemy.dialects.postgresql import ENUM as PGEnum


class AdPlatform(str, enum.Enum):
    GOOGLE = "Google"
    META = "Meta"
    LINKEDIN = "LinkedIn"


ad_platform_enum = PGEnum(
    AdPlatform,
    name="ad_platform",
    values_callable=lambda enum_cls: [e.value for e in enum_cls],
)
