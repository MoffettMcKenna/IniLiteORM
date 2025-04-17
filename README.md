# IniLiteORM
This project started as LiteDAO, a relatively simple wrapper around sqlite I wanted to use on some other projects.  Then there was one of those lunch-time conversations...

In the domain of embedded engineering there are a mix of engineers with software and hardware backgrounds, including their education.  If a junior engineer with an electrical engineering background had to do something with a database the results would be mixed.  As a QA Engineer, I had first-hand experience with these sorts of errors, and a conversation over pizza lead us to the question "why do they even need to?".

The goal of this project is to create a library capable of providing full access to a sqlite database without needing to know you're accessing a database.  The full schema will be specified in a configuration file (currently only in *.ini files) and a developer can just reference the names there to perform CRUD operations.
