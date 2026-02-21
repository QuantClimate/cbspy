from pydantic import BaseModel


class Column(BaseModel):
    """A column (property) in a CBS dataset."""

    id: str
    name: str
    unit: str
    datatype: str
    description: str


class TableMetadata(BaseModel):
    """Metadata for a CBS dataset table."""

    id: str
    title: str
    description: str
    period: str
    frequency: str
    properties: list[Column]
