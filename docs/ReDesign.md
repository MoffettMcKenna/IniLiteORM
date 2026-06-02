## Redesign Notes

# Goal
Need to represent the query not as a string but an object right up to execution.
stringify right at the edge before execution

`select * from tableA`
`select * from tableA where field = value`
`select col1, col2, col3, from tableA where field < value and field != value`
`update tableA set field = (select field from tableB where field = value)`

# Tables
a collection of rows and columns
- Rows hold the data
- Column objects provide the validation and filtering
The operation methods return a query object setup to perform the base operation.  More can be accumulated onto it as needed.


# Columns
Tracks the metadata about the data in that column
- knows type
- primary key, foreign key
- default?

# Queries
Gathers the elements for a single execution of a query with the possibility of being re-used.
- each query runs against a primary table and however many secondaries
- knows the operation being performed, and the set of columns from each table
This is the muscle of the library, and will be the objects interacted with the most. 


# Filters
Filters are the where clauses
- use Columns 

# Concerns
- **Performance** A complicated query will 
