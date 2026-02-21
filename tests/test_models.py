from cbspy.models import Column, TableMetadata


def test_column_creation():
    col = Column(
        id="TotalPopulation_1",
        name="Total population",
        unit="number",
        datatype="Double",
        description="The total population.",
    )
    assert col.id == "TotalPopulation_1"
    assert col.name == "Total population"
    assert col.unit == "number"
    assert col.datatype == "Double"
    assert col.description == "The total population."


def test_column_empty_name():
    col = Column(
        id="Foo_1",
        name="",
        unit="",
        datatype="Long",
        description="",
    )
    assert col.name == ""


def test_table_metadata_creation():
    meta = TableMetadata(
        id="37296eng",
        title="Population; key figures",
        description="A description.",
        period="1950 - 2022",
        frequency="Perjaar",
        properties=[],
    )
    assert meta.id == "37296eng"
    assert meta.title == "Population; key figures"
    assert meta.properties == []


def test_table_metadata_with_columns():
    col = Column(
        id="TotalPopulation_1",
        name="Total population",
        unit="number",
        datatype="Double",
        description="",
    )
    meta = TableMetadata(
        id="37296eng",
        title="Population; key figures",
        description="",
        period="1950 - 2022",
        frequency="Perjaar",
        properties=[col],
    )
    assert len(meta.properties) == 1
    assert meta.properties[0].id == "TotalPopulation_1"
