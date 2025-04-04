from Columns import Column, StorageTypes

def test_Int_Column_Init():
    c = Column('id', 'integer, key')
    assert c.Name == 'id'
    assert c.ColumnType == 'integer'
    assert c.Default == 0
    assert c.PrimaryKey
    assert not c.Nullable


def test_Int_Validator():
    c = Column('id', 'integer')
    assert c.Validate(10), 'Failed to validate 10'
    assert c.Validate(-1), 'Failed to validate -1'
    assert c.Validate(0), 'Failed to validate 0'
    assert not c.Validate('one'), 'Why was \"one\" picked as an int?'
    assert not c.Validate(1.6), 'Detected a float as an int'


def test_Float_Column_Init():
    c = Column('measure', 'real, required')
    assert c.Name == 'measure'
    assert c.ColumnType == 'real'
    assert c.Default == 0.0
    assert not c.PrimaryKey
    assert not c.Nullable


def test_Float_Validator():
    c = Column('measure', 'real')
    assert c.Validate(0.1), 'Failed to validate 0.0'
    assert not c.Validate(1), 'Failed to validate 1'
    assert not c.Validate('one'), 'Incorrectly validated \"one\"'


def test_String_Column_Init():
    c = Column('name', 'string')
    assert c.Name == 'name'
    assert not c.PrimaryKey
    assert c.ColumnType == 'string'
    assert c._storageT == StorageTypes.TEXT
    assert c.Validate('testing')
    assert not c.Validate(0.00)


def test_Double_Column_Init():
    c = Column('measure', 'double')
    assert c.ColumnType == 'double'
    assert c._storageT == StorageTypes.REAL
    assert c.Validate(0.1), 'Failed to validate 0.0'
    assert not c.Validate(1), 'Failed to validate 1'
    assert not c.Validate('one'), 'Incorrectly validated \"one\"'
