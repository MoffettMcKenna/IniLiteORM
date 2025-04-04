import configparser

import pytest
import sqlite3
import os

test_db_version = 2

@pytest.fixture
def buildDBFile():
    create = False

    if not os.path.exists('./test.db'):
        # db doesn't exist, we need to create it
        create = True
    else:
        con = sqlite3.connect('./test.db')
        try:
            # try to read the the database version
            version = con.execute('Select version from Version').fetchall()[0][0]

            # if the db isn't the correct version, set create
            if version != test_db_version:
                create = True

        except (sqlite3.OperationalError, IndexError):
            # if the tables is DNE, we have the wrong db, set create
            create = True

    # if any of the above triggered, rebuild the db
    if create:
        con = sqlite3.connect('./test.db')
        cur = con.cursor()

        cur.execute('Drop Table If Exists Version')
        cur.execute("""Create Table Version (version integer)""")
        ins_ver = "Insert into Version (version) values ({0})".format(test_db_version)
        cur.execute(ins_ver)

        cur.execute('Drop Table If Exists Person')
        cur.execute("""Create Table Person (
                        id integer primary key,
                        fname text not null,
                        lname text not null,
                        nickname text,
                        birthday text
                    );""")

        # bday format -> YYYY-MM-DD

        insperson = 'Insert into Person (fname, lname, nickname, birthday) values (?, ?, ?, ?)'
        cur.execute(insperson, ('Joe', 'Smith', 'daddy', '1911-11-11'))
        cur.execute(insperson, ('June', 'Smith', 'Mommy', '2222-02-22'))
        cur.execute(insperson, ('Jack', 'Smith', None, '2001-10-01'))
        cur.execute(insperson, ('Jill', 'Smith', None, '2011-04-11'))
        cur.execute(insperson, ('Joanna', 'Dane', 'Mimi', '2019-12-13'))
        cur.execute(insperson, ('John', 'Doe', 'Pops', '1909-03-10'))
        cur.execute(insperson, ('Jane', 'Doe', 'Grams', '1024-01-28'))

        cur.execute('Drop Table If Exists Wallet')
        cur.execute("""Create table Wallet(
                        id integer primary key, 
                        personid integer, 
                        amount real, 
                        lastTransdate text
                    );""")

        inswallet = 'insert into Wallet(personid, amount, lastTransDate) values (?, ?, ?)'
        cur.execute(inswallet, (1, 100.00, '2021-12-22'))
        cur.execute(inswallet, (2, 654.85, '3032-03-10'))
        cur.execute(inswallet, (6, 1010.12, '1808-08-09'))

        #  Create Table PhoneNumber (
        #         id integer primary key,
        #         number text not null unique
        # )

        con.commit()

    return con

@pytest.fixture
def dirtyDB():
    yield
    con = sqlite3.connect('./test.db')
    try:
        cur = con.cursor()
        cur.execute('update Version set version = 0')
        con.commit()
    except (sqlite3.OperationalError, IndexError):
        # if the tables is DNE, we have the wrong db, set create
        create = True
    finally:
        con.close()

@pytest.fixture
def config():
    cp = configparser.ConfigParser()
    file = 'test.ini'
    cp.read(file)
    return cp
