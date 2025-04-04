
# grab the setup for the DB from here
from Fixtures import *

from Tables import Table
from Tables import ComparisonOps
import Errors


# region Get Tests

def test_Get_AllColumns(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)
    data = t.GetAll()

    assert data[0][1] == "Joe"
    assert data[0][2] == "Smith"
    assert data[0][3] == "daddy"
    assert data[0][4] == '1911-11-11'

    assert data[1][1] == "June"
    assert data[1][2] == "Smith"
    assert data[1][3] == "Mommy"
    assert data[1][4] == '2222-02-22'

    assert data[2][1] == "Jack"
    assert data[2][2] == "Smith"
    assert data[2][3] is None
    assert data[2][4] == '2001-10-01'

    assert data[3][1] == "Jill"
    assert data[3][2] == "Smith"
    assert data[3][3] is None
    assert data[3][4] == '2011-04-11'

    assert data[4][1] == "Joanna"
    assert data[4][2] == "Dane"
    assert data[4][3] == "Mimi"
    assert data[4][4] == '2019-12-13'

    assert data[5][1] == "John"
    assert data[5][2] == "Doe"
    assert data[5][3] == "Pops"
    assert data[5][4] == '1909-03-10'

    assert data[6][1] == "Jane"
    assert data[6][2] == "Doe"
    assert data[6][3] == "Grams"
    assert data[6][4] == '1024-01-28'


def test_Get_OneColumn(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)
    data = t.Get(["fname"])

    assert data[0][0] == "Joe"
    assert data[1][0] == "June"
    assert data[2][0] == "Jack"
    assert data[3][0] == "Jill"
    assert data[4][0] == "Joanna"
    assert data[5][0] == "John"
    assert data[6][0] == "Jane"


def test_Get_MultipleColumns(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)
    data = t.Get(["fname", "id"])

    assert data[0][0] == "Joe"
    assert data[0][1] == 1
    assert data[1][0] == "June"
    assert data[1][1] == 2
    assert data[2][0] == "Jack"
    assert data[2][1] == 3
    assert data[3][0] == "Jill"
    assert data[3][1] == 4
    assert data[4][0] == "Joanna"
    assert data[4][1] == 5
    assert data[5][0] == "John"
    assert data[5][1] == 6
    assert data[6][0] == "Jane"
    assert data[6][1] == 7


def test_Get_DNE_Column(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    with pytest.raises(Errors.ImaginaryColumn):
        data = t.Get(["name"])

    with pytest.raises(Errors.ImaginaryColumn):
        data = t.Get(["id, fname, name"])

    with pytest.raises(Errors.ImaginaryColumn):
        data = t.Get(["id, name, lname"])


# endregion

# region Filter Tests

def test_Filter_Null_Nickname(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)
    t.Filter("nickname", ComparisonOps.IS, None)
    data = t.GetAll()

    assert len(data) == 2
    assert data[0][1] == "Jack"
    assert data[0][2] == "Smith"
    assert data[0][3] is None

    assert data[1][1] == "Jill"
    assert data[1][2] == "Smith"
    assert data[1][3] is None

    t.ClearFilters()


def test_Filter_LastName(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)
    t.Filter("lname", ComparisonOps.IS, 'Doe')
    data = t.GetAll()

    assert len(data) == 2
    assert data[0][1] == "John"
    assert data[0][2] == "Doe"
    assert data[0][3] == "Pops"
    assert data[0][4] == "1909-03-10"

    assert data[1][1] == "Jane"
    assert data[1][2] == "Doe"
    assert data[1][3] == "Grams"
    assert data[1][4] == "1024-01-28"

    t.ClearFilters()


def test_ClearFilters(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)
    t.Filter("nickname", ComparisonOps.IS, None)
    data = t.GetAll()

    assert len(data) == 2

    t.ClearFilters()

    data2 = t.GetAll()
    assert len(data2) == 7


def test_Filter_InvalidValue(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    with pytest.raises(Errors.InvalidColumnValue):
        t.Filter("id", ComparisonOps.IS, '20')

    with pytest.raises(Errors.InvalidColumnValue):
        t.Filter("nickname", ComparisonOps.IS, 20)

    # just to be safe
    t.ClearFilters()

# endregion

# region Validator Tests

def startsJ(value: str) -> bool:
    return value.startswith('J')


def test_Validator(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    # check the string validator - don't run these queries they return nothing
    t.UpdateValidators('fname', startsJ)
    # these should work
    t.Filter('fname', ComparisonOps.LIKE, 'Jacob')
    t.Filter('fname', ComparisonOps.IS, 'June')
    # this will fail
    with pytest.raises(Errors.InvalidColumnValue):
        t.Filter('fname', ComparisonOps.LIKE, 'Issac')

    # now clear the filters for future tests
    t.ClearFilters()


# endregion

# region Add Tests

def test_Add_AllValues(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    t.Add({'fname': 'TestGuy', 'lname': 'Testing', 'nickname': 'QA', 'birthday': '1111-01-01'})
    t.Filter('fname', ComparisonOps.LIKE, 'Test%')
    data = t.GetAll()

    assert len(data) == 1
    assert data[0][1] == "TestGuy"
    assert data[0][2] == "Testing"
    assert data[0][3] == 'QA'
    assert data[0][4] == '1111-01-01'

    # clear the filters
    t.ClearFilters()

    # clean up the database
    t.Delete('fname', ComparisonOps.EQUALS, 'TestGuy')


def test_Add_DefaultDefaults(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    t.Add({})
    t.Filter('fname', ComparisonOps.IS, '')
    data = t.GetAll()

    assert len(data) == 1
    assert data[0][1] == ""
    assert data[0][2] == ""
    assert data[0][3] == ''
    assert data[0][4] == ''

    # clean up the filters
    t.ClearFilters()

    # clean up the database
    t.Delete('fname', ComparisonOps.EQUALS, '')


def test_Add_NewDefault(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)
    t.SetDefault('fname', 'Tony')
    t.SetDefault('lname', 'Testing')

    t.Add({})
    t.Filter('fname', ComparisonOps.IS, 'Tony')
    data = t.GetAll()

    assert len(data) == 1
    assert data[0][1] == "Tony"
    assert data[0][2] == "Testing"
    assert data[0][3] == ''
    assert data[0][4] == ''

    # erase filters
    t.ClearFilters()

    # clean up the database
    t.Delete('fname', ComparisonOps.EQUALS, 'Tony')


# verify the order of the values doesn't matter to the add
def test_Add_ValueOrder(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    t.Add({'nickname': 'QA', 'lname': 'Testing', 'fname': 'TestGuy', 'birthday': '1111-01-01'})
    t.Filter('fname', ComparisonOps.LIKE, 'Test%')
    data = t.GetAll()

    assert len(data) == 1
    assert data[0][1] == "TestGuy"
    assert data[0][2] == "Testing"
    assert data[0][3] == 'QA'
    assert data[0][4] == '1111-01-01'

    # erase filters
    t.ClearFilters()

    # clean up the database
    t.Delete('fname', ComparisonOps.EQUALS, 'TestGuy')


def test_Add_InvalidColumn(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    with pytest.raises(Errors.ImaginaryColumn):
        t.Add({'name': 'TestGuy', 'lname': 'Testing', 'nickname': 'QA', 'birthday': '1111-01-01'})

    with pytest.raises(Errors.ImaginaryColumn):
        t.Add({'fname': 'TestGuy', 'lname': 'Testing', 'nick': 'QA', 'birthday': '1111-01-01'})

    with pytest.raises(Errors.ImaginaryColumn):
        t.Add({'fname': 'TestGuy', 'lname': 'Testing', 'nickname': 'QA', 'birthday': '1111-01-01', 'age': 10})


# endregion

# region Delete Tests

def test_DeleteOne(config, buildDBFile, dirtyDB):
    t = Table(config["Person"], buildDBFile)

    # confirm the expected number of entries
    data1 = t.GetAll()
    assert len(data1) == 7

    # operation under test
    t.Delete('nickname', ComparisonOps.IS, 'Mimi')

    # confirm the expected number of entries
    data2 = t.GetAll()
    assert len(data2) == 6

    # ensure only one was deleted
    assert len(data1) == len(data2) + 1


def test_DeleteMultiple(config, buildDBFile, dirtyDB):
    t = Table(config["Person"], buildDBFile)

    # confirm the expected number of entries
    data1 = t.GetAll()
    assert len(data1) == 7

    # operation under test
    t.Delete('nickname', ComparisonOps.IS, None)

    # confirm the expected number of entries
    data2 = t.GetAll()
    assert len(data2) == 5

    # ensure only one was deleted
    assert len(data1) == len(data2) + 2


def test_Delete_ClassFilter(config, buildDBFile, dirtyDB):
    t = Table(config["Person"], buildDBFile)

    # confirm the expected number of entries
    data1 = t.GetAll()
    assert len(data1) == 7

    # set the filter
    t.Filter('lname', ComparisonOps.IS, 'Smith')

    # operation under test
    t.Delete()

    # clear the filter so the get reads all
    t.ClearFilters()

    # confirm the expected number of entries
    data2 = t.GetAll()
    assert len(data2) == 3

    # ensure only one was deleted
    assert len(data1) == len(data2) + 4


def test_Delete_BadColumn(config, buildDBFile, dirtyDB):
    t = Table(config["Person"], buildDBFile)

    # confirm the expected number of entries
    data1 = t.GetAll()
    assert len(data1) == 7

    # try to delete based on a non-existant column
    with pytest.raises(Errors.ImaginaryColumn):
        t.Delete('name', ComparisonOps.IS, 'Mimi')

    # confirm the expected number of entries
    data2 = t.GetAll()
    assert len(data2) == len(data1)


def test_Delete_BadFilterValue(config, buildDBFile, dirtyDB):
    t = Table(config["Person"], buildDBFile)

    # confirm the expected number of entries
    data1 = t.GetAll()
    assert len(data1) == 7

    # try to delete based on a non-existant column
    with pytest.raises(Errors.InvalidColumnValue):
        t.Delete('nickname', ComparisonOps.IS, 10)

    # confirm the expected number of entries
    data2 = t.GetAll()
    assert len(data2) == len(data1)


# test running with both inline and class filters
def test_Delete_DualFilterType(config, buildDBFile, dirtyDB):
    t = Table(config["Person"], buildDBFile)

    # set the filter
    t.Filter('lname', ComparisonOps.IS, 'Doe')

    # confirm the expected number of entries with last name Doe
    data1 = t.GetAll()
    assert len(data1) == 2

    # operation under test
    t.Delete('nickname', ComparisonOps.EQUALS, 'Pops')

    # clear the filter so the get reads all
    t.ClearFilters()

    # confirm the expected number of entries
    data2 = t.GetAll()
    assert len(data2) == 6

    # make sure the correct one was deleted
    assert data2[0][1] == "Joe"
    assert data2[0][2] == "Smith"
    assert data2[0][3] == "daddy"
    assert data2[0][4] == '1911-11-11'

    assert data2[1][1] == "June"
    assert data2[1][2] == "Smith"
    assert data2[1][3] == "Mommy"
    assert data2[1][4] == '2222-02-22'

    assert data2[2][1] == "Jack"
    assert data2[2][2] == "Smith"
    assert data2[2][3] is None
    assert data2[2][4] == '2001-10-01'

    assert data2[3][1] == "Jill"
    assert data2[3][2] == "Smith"
    assert data2[3][3] is None
    assert data2[3][4] == '2011-04-11'

    assert data2[4][1] == "Joanna"
    assert data2[4][2] == "Dane"
    assert data2[4][3] == "Mimi"
    assert data2[4][4] == '2019-12-13'

    assert data2[5][1] == "Jane"
    assert data2[5][2] == "Doe"
    assert data2[5][3] == "Grams"
    assert data2[5][4] == '1024-01-28'


# endregion

# region Update Tests

def test_UpdateOne(config, buildDBFile, dirtyDB):
    t = Table(config["Person"], buildDBFile)

    # perform the operation under test
    t.UpdateValue("nickname", "Gram", "lname", ComparisonOps.IS, "Dane")

    # isolate the changed field and read it
    data = t.GetAll()

    # verify the changes, and only the changes
    assert len(data) == 7

    assert data[0][1] == "Joe"
    assert data[0][2] == "Smith"
    assert data[0][3] == "daddy"
    assert data[0][4] == '1911-11-11'

    assert data[1][1] == "June"
    assert data[1][2] == "Smith"
    assert data[1][3] == "Mommy"
    assert data[1][4] == '2222-02-22'

    assert data[2][1] == "Jack"
    assert data[2][2] == "Smith"
    assert data[2][3] is None
    assert data[2][4] == '2001-10-01'

    assert data[3][1] == "Jill"
    assert data[3][2] == "Smith"
    assert data[3][3] is None
    assert data[3][4] == '2011-04-11'

    assert data[4][1] == "Joanna"
    assert data[4][2] == "Dane"
    assert data[4][3] == "Gram"
    assert data[4][4] == '2019-12-13'

    assert data[5][1] == "John"
    assert data[5][2] == "Doe"
    assert data[5][3] == "Pops"
    assert data[5][4] == '1909-03-10'

    assert data[6][1] == "Jane"
    assert data[6][2] == "Doe"
    assert data[6][3] == "Grams"
    assert data[6][4] == '1024-01-28'


def test_UpdateMultiple(config, buildDBFile, dirtyDB):
    t = Table(config["Person"], buildDBFile)

    # perform the operation under test
    t.UpdateValue("nickname", "Test", "lname", ComparisonOps.IS, "Doe")

    data = t.GetAll()

    # verify the changes, and only the changes
    assert len(data) == 7

    assert data[0][1] == "Joe"
    assert data[0][2] == "Smith"
    assert data[0][3] == "daddy"
    assert data[0][4] == '1911-11-11'

    assert data[1][1] == "June"
    assert data[1][2] == "Smith"
    assert data[1][3] == "Mommy"
    assert data[1][4] == '2222-02-22'

    assert data[2][1] == "Jack"
    assert data[2][2] == "Smith"
    assert data[2][3] is None
    assert data[2][4] == '2001-10-01'

    assert data[3][1] == "Jill"
    assert data[3][2] == "Smith"
    assert data[3][3] is None
    assert data[3][4] == '2011-04-11'

    assert data[4][1] == "Joanna"
    assert data[4][2] == "Dane"
    assert data[4][3] == "Mimi"
    assert data[4][4] == '2019-12-13'

    assert data[5][1] == "John"
    assert data[5][2] == "Doe"
    assert data[5][3] == "Test"
    assert data[5][4] == '1909-03-10'

    assert data[6][1] == "Jane"
    assert data[6][2] == "Doe"
    assert data[6][3] == "Test"
    assert data[6][4] == '1024-01-28'


def test_Update_PresetFilter(config, buildDBFile, dirtyDB):
    t = Table(config["Person"], buildDBFile)

    t.Filter('lname', ComparisonOps.IS, 'Doe')

    # perform the operation under test
    t.UpdateValue("nickname", "Test")

    data = t.GetAll()

    # verify the changes, and only the changes
    assert len(data) == 2

    assert data[0][1] == "John"
    assert data[0][2] == "Doe"
    assert data[0][3] == "Test"
    assert data[0][4] == '1909-03-10'

    assert data[1][1] == "Jane"
    assert data[1][2] == "Doe"
    assert data[1][3] == "Test"
    assert data[1][4] == '1024-01-28'


def test_Update_BadUpdateColumn(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    # try to update a non-existant column
    with pytest.raises(Errors.ImaginaryColumn):
        # perform the operation under test
        t.UpdateValue("nick", "Test", "lname", ComparisonOps.IS, "Doe")

    # apply the filter and read the db
    t.Filter("lname", ComparisonOps.IS, 'Doe')
    data = t.GetAll()

    # confirm no changes
    assert len(data) == 2
    assert data[0][1] == "John"
    assert data[0][2] == "Doe"
    assert data[0][3] == "Pops"
    assert data[0][4] == "1909-03-10"

    assert data[1][1] == "Jane"
    assert data[1][2] == "Doe"
    assert data[1][3] == "Grams"
    assert data[1][4] == "1024-01-28"


def test_Update_BadUpdateValue(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    # try to update a non-existant column
    with pytest.raises(Errors.InvalidColumnValue):
        # perform the operation under test
        t.UpdateValue("nickname", 10, "lname", ComparisonOps.IS, "Doe")

    # apply the filter and read the db
    t.Filter("lname", ComparisonOps.IS, 'Doe')
    data = t.GetAll()

    # confirm no changes
    assert len(data) == 2
    assert data[0][1] == "John"
    assert data[0][2] == "Doe"
    assert data[0][3] == "Pops"
    assert data[0][4] == "1909-03-10"

    assert data[1][1] == "Jane"
    assert data[1][2] == "Doe"
    assert data[1][3] == "Grams"
    assert data[1][4] == "1024-01-28"


def test_Update_BadFilterColumn(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    # try to update a non-existant column
    with pytest.raises(Errors.ImaginaryColumn):
        # perform the operation under test
        t.UpdateValue("nickname", "Test", "lame", ComparisonOps.IS, "Doe")

    # and read the db
    data = t.GetAll()

    # confirm no changes
    assert len(data) == 7
    assert data[0][1] == "Joe"
    assert data[0][2] == "Smith"
    assert data[0][3] == "daddy"
    assert data[0][4] == '1911-11-11'

    assert data[1][1] == "June"
    assert data[1][2] == "Smith"
    assert data[1][3] == "Mommy"
    assert data[1][4] == '2222-02-22'

    assert data[2][1] == "Jack"
    assert data[2][2] == "Smith"
    assert data[2][3] is None
    assert data[2][4] == '2001-10-01'

    assert data[3][1] == "Jill"
    assert data[3][2] == "Smith"
    assert data[3][3] is None
    assert data[3][4] == '2011-04-11'

    assert data[4][1] == "Joanna"
    assert data[4][2] == "Dane"
    assert data[4][3] == "Mimi"
    assert data[4][4] == '2019-12-13'

    assert data[5][1] == "John"
    assert data[5][2] == "Doe"
    assert data[5][3] == "Pops"
    assert data[5][4] == '1909-03-10'

    assert data[6][1] == "Jane"
    assert data[6][2] == "Doe"
    assert data[6][3] == "Grams"
    assert data[6][4] == '1024-01-28'


def test_Update_BadFilterValue(config, buildDBFile):
    t = Table(config["Person"], buildDBFile)

    # try to update a non-existant column
    with pytest.raises(Errors.InvalidColumnValue):
        # perform the operation under test
        t.UpdateValue("nickname", "Test", "lname", ComparisonOps.IS, 10)

    # read the db
    data = t.GetAll()

    # confirm no changes
    assert len(data) == 7
    assert data[0][1] == "Joe"
    assert data[0][2] == "Smith"
    assert data[0][3] == "daddy"
    assert data[0][4] == '1911-11-11'

    assert data[1][1] == "June"
    assert data[1][2] == "Smith"
    assert data[1][3] == "Mommy"
    assert data[1][4] == '2222-02-22'

    assert data[2][1] == "Jack"
    assert data[2][2] == "Smith"
    assert data[2][3] is None
    assert data[2][4] == '2001-10-01'

    assert data[3][1] == "Jill"
    assert data[3][2] == "Smith"
    assert data[3][3] is None
    assert data[3][4] == '2011-04-11'

    assert data[4][1] == "Joanna"
    assert data[4][2] == "Dane"
    assert data[4][3] == "Mimi"
    assert data[4][4] == '2019-12-13'

    assert data[5][1] == "John"
    assert data[5][2] == "Doe"
    assert data[5][3] == "Pops"
    assert data[5][4] == '1909-03-10'

    assert data[6][1] == "Jane"
    assert data[6][2] == "Doe"
    assert data[6][3] == "Grams"
    assert data[6][4] == '1024-01-28'

# endregion

# region SQL Tests

def test_BuildSQL(config, buildDBFile):

    t = Table(config["Person"], buildDBFile)

    tsql = t.Build_SQL()
    actual = "Create Table Person (id integer primary key, fname text not null, lname text not null, nickname text, birthday text);"

    assert tsql.lower() == actual.lower()

# endregion