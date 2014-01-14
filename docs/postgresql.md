# Save a local PostgreSQL database

PostgreSQL database saving require an additionnal setup.
Indeed, PostgreSQL dump client require you to have a `.pgpass` file under your `home` directory.

This file must contain informations on your host, database, username and password.

[An example .pgpass)](../install/.pgpass) file can be found under [install directory](../install).

Just run (under savior directory): 
	
	cp install/.pgpass ~
	nano ~/.pgpass 			# Provide your own credentials
	chmod 0600 ~/.pgpass 	# If you don't set this permissions, your pgpass file will be ignored by PostgreSQL