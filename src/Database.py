import configparser
import os
from Tables import *
from sqlparse import engine, tokens as Token


class Database:
    """
    Manages the ini file and initiates the processing on load.  Since the ini
    file is the source of truth, examine the current db schema and update as
    needed.
    """

    def __init__(self, file: str):
        # load the configuration
        config = configparser.ConfigParser()
        config.read(file)

        self._tables = {}
        tokens = {}

        # grab the file path and see if already exists
        self.DatabasePath = config['global']['File']
        file_existed = os.path.isfile(self.DatabasePath)

        # creates the file if it isn't present
        self._client = sqlite3.connect(self.DatabasePath)

        # prep for the comparison
        if file_existed:
            # read all the sql creates from the metadata
            sqlstmts = self._client.execute("select sql from sqlite_master where type = 'table'").fetchall()

            for sql in sqlstmts:
                tname, tdata = self._parse_create(sql[0])
                tokens[tname] = tdata

        # this will make the system attempt to run some alter scripts to correct
        # differences between the found and spec'd DB
        if 'update' in config['global'].keys():
            self._updating = config['global']['update']
        else:
            self._updating = False

        # load the sections into table entries
        for table in config.sections():
            # the globals section is not an actual table
            if table.lower() == 'global':
                continue

            # create new table - pass in empty dict instead of the tokens dict for the table if not found in db
            ntable = Table(table, self._client, tokens[table] if table in tokens.keys() else {})
            self._tables[ntable.TableName] = ntable

            if file_existed:
                #update the table if needed
                if not ntable.IsValid:
                    ntable.Sync()
            else:
                # empty db, need to create the table
                Table.Create()
        # end for table in config.sections

        # are there any tables in the db which aren't in the file?  backup before delete?
    # end __init__()

    def _parse_create(self, sql: str):
        """
        Converts a create statement into a data structure (format still TBD)
        :return: A tuple of the table name and the data structure.
        """
        tdata = {}
        stack = engine.FilterStack()
        # returns a generator to the list of tokens
        parsed = stack.run(sql.replace('\r', '').replace('\n', '').replace('\t', ' '))

        # get the
        stmt = next(parsed)

        # setup to remove the whitespace as tehy're not needed
        toks = [tok for tok in stmt if not tok.is_whitespace]  # convert to generator?

        # long winded (refactor?), but matching pattern "Create Table <name> (...."
        if toks[0].match(Token.Keyword.DDL, 'create') and toks[1].match(Token.Keyword, 'table') and toks[3].match(
                Token.Punctuation, '('):
            # save the table name
            tname = toks[2].value.strip('[').strip(']')

            # first column name is index 4
            i = 4

            # collect the columns
            while not toks[i].match(Token.Punctuation, ')'):
                # get the column name
                cname = toks[i].value.strip('[').strip(']')
                i += 1

                cdata = []
                # grab all the column properties
                while not toks[i].match(Token.Punctuation, ',') and not toks[i].match(Token.Punctuation, ')'):
                    tok_text = toks[i].value.strip('[').strip(']')

                    # handle the special cases
                    if toks[i].is_keyword:
                        if tok_text.lower() == 'primary':
                            if toks[i + 1].value.lower() == 'key':
                                tok_text = "primarykey"
                                i += 1
                        # end primary key handling

                        if tok_text.lower() == 'references':
                            # next token is the table name
                            i += 1
                            fk_table = toks[i].value.strip('[').strip(']')

                            # skip past any junk before the opening (
                            while not toks[i].match(Token.Punctuation, '('):
                                i += 1

                            key_cols = []
                            i += 1  # skip the (
                            # now everything up until the ) is a column in the fk
                            while not toks[i].match(Token.Punctuation, ')'):
                                if not toks[i].match(Token.Punctuation, ','):
                                    key_cols.append(toks[i].value.strip('[').strip(']'))
                                i += 1
                            # end while not ) closing fk columns

                            tok_text = f"foreignkey {fk_table}.{','.join(key_cols)}"
                        # end references handling

                        if tok_text.lower() == 'default':
                            i += 1
                            def_val = toks[i].value.strip('\'').strip('\"')
                            tok_text = f"default {def_val}"
                        # end default processing

                    # end if is_keyword/special processing

                    cdata.append(tok_text)
                    i += 1
                # end while not comma
                tdata[cname] = cdata

                # advance past the comma but leave alone when exited the above while due to ')'
                if toks[i].match(Token.Punctuation, ','):
                    i += 1
            # end while not close-paran
        # end if tok chain

        return tname, tdata
    # end parse_create()

    def __getattr__(self, item):
        if item in self._tables.keys():
            return self._tables[item]
        else:
            raise ValueError(f"Table {str(item)} does not exist in this database.")

