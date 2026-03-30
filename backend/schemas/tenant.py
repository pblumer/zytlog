from pydantic import BaseModel


class TenantRead(BaseModel):
    id: int
    name: str
    slug: str
