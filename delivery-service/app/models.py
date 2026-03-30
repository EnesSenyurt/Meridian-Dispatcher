from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DeliveryCreate(BaseModel):
    sender_id: str
    recipient_name: str
    recipient_address: str
    recipient_phone: str
    package_description: str
    status: Literal["pending", "in_transit", "delivered", "cancelled"] = "pending"


class DeliveryUpdate(BaseModel):
    recipient_name: Optional[str] = None
    recipient_address: Optional[str] = None
    recipient_phone: Optional[str] = None
    package_description: Optional[str] = None
    status: Optional[Literal["pending", "in_transit", "delivered", "cancelled"]] = None


class DeliveryResponse(BaseModel):
    id: str
    sender_id: str
    recipient_name: str
    recipient_address: str
    recipient_phone: str
    package_description: str
    status: str
    created_at: datetime
    updated_at: datetime
