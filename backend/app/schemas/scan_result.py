from pydantic import BaseModel


class ScanResultResponse(BaseModel):
    id: int
    port: int
    protocol: str
    state: str
    service: str | None = None
    product: str | None = None
    version: str | None = None
    is_ssl: bool

    class Config:
        from_attributes = True
