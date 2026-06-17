# Redesign Notes

## Goal
Need to represent the query not as a string but an object right up to execution.
stringify right at the edge before execution

## Samples

`select * from tableA`

`select * from tableA where field = value`

`select col1, col2, col3, from tableA where field < value and field != value`

`update tableA set field = (select field from tableB where field = value)`

`UPDATE e SET e.salary = e.salary + d.bonus_pool FROM employees e 
INNER JOIN departments d ON e.department_id = d.id 
WHERE d.is_profitable = 1`

`UPDATE employees SET city = 'Toronto', state = 'ON', postalcode = 'M5P 2N7' WHERE employeeid = 4`

`UPDATE employees SET email = LOWER(firstname || '.' || lastname || '@company.com')`

`UPDATE users SET (field1, field2) = ('value1', 'value2') WHERE id = 10;`

`UPDATE departments 
SET total_budget = (
    SELECT SUM(salary) FROM employees WHERE employees.dept_id = departments.id
)
WHERE EXISTS (
    SELECT 1 FROM employees WHERE employees.dept_id = departments.id
)`


## Objects

### Tables
a collection of rows and columns
- Column objects provide the validation and filtering
- Rows are just namedtuples, returned from operations with the data by other objects
- Knows the special metadata - indices, primary keys, foreign keys(?)
The operation methods return a query object setup to perform the base operation.  More can be accumulated onto it as needed.

### Columns
Tracks the metadata about the data in that column
- knows type
- primary key, foreign key
- default?
- performs validation 

### Queries
Gathers the elements for a single execution of a query with the possibility of being re-used.
- each query runs against a primary table and however many secondaries
- knows the operation being performed, and the set of columns from each table
This is the muscle of the library, and will be the objects interacted with the most. 


### Filters
Filters are the where clauses
- use Columns to validation the arguments
- needs to be able to use a query in the right-hand side

## Concerns
- **Performance** A complicated query might require a larger number of objects, representing a heavy memory footprint. 
