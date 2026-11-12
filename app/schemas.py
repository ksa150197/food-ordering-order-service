from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class OrderLineRequest(BaseModel):
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=50)

class OrderCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=80)
    items: list[OrderLineRequest] = Field(min_length=1)

class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: str
    items: list[dict]
    total_amount: float
    status: str
    created_at: datetime

class StatusUpdate(BaseModel):
    status: str
