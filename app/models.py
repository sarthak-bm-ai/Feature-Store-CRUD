from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class FeatureMetadata(BaseModel):
    created_at: datetime
    updated_at: datetime
    source: str
    compute_id: Optional[str] = None
    ttl: Optional[int] = None  # TTL in seconds

class Features(BaseModel):
    data: Dict[str, Any]  # actual feature values
    metadata: FeatureMetadata

class Item(BaseModel):
    bright_uid: str
    category: str
    features: Features
