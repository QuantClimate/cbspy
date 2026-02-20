from pydantic import BaseModel, computed_field


class Column(BaseModel):
    """A column (property) in a CBS dataset."""

    id: str
    name: str
    dutch_name: str
    unit: str
    datatype: str
    description: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_name(self) -> str:
        """Return English name if available, otherwise Dutch."""
        return self.name if self.name else self.dutch_name


class TableMetadata(BaseModel):
    """Metadata for a CBS dataset table."""

    id: str
    title: str
    description: str
    period: str
    frequency: str
    properties: list[Column]
