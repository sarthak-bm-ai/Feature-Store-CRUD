from typing import Optional, Union
from pydantic import BaseModel, UUID4


class WriteRequestSchema(BaseModel):
    metadata: WriteMetadataSchema
    data: Dict[str, Any]

class ReadRequestSchema(BaseModel):
    metadata: ReadMetadataSchema
    data: Dict[str, Any]
