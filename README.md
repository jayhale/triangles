# Triangles
*Identify solutions to the classic triangle+pegs bar game*

## Usage

1. Install the package and requirements

	```shell
	$ pip install git+git://github.com/jayhale/triangles.git#egg=triangles
	```

2. Initialize the database to save results

	```shell
	$ triangle db init
	Initializing the database at triangles.db
	```

3. Find all feasible board configurations and all solutions (~2 hrs, mostly to build the DB)

	```bash
	$ triangle solve
	Finding all feasible solutions with position 14 initially empty
	   Incrementing boards (1     ):  [####################################]  100%
	...
	   Incrementing boards (162558):  [####################################]  100%
	Saving results to the database
	   Saving boards (won=1):         [####################################]  100%
	   Saving boards (won=0):         [####################################]  100%
	```

4. View a configuration (the "bowtie" configuration is `b'111111111101000'` or 32744)

	```bash
	$ triangle view configuration 32744
	Configuration 32744: 111111111101000
    ●   ●   ●   ●   ●
      ●   ●   ●   ●
        ●   ○   ●
          ○   ○
            ○
   ```

5. List sequences for a configuration
