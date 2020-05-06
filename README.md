# crew_scheduling

It is a tool to generate a pilot schedule, given a start date, 
and company data (fleet and network).


# Utilities

## Flights schedule generator

This tool generates a schedule file in FSC format using as input
a Flightradar24 json data.

Usage:
```
generator.py [-h] [--version] [--stats] [--verbosity {info,debug,error}] [--log-dir LOG_DIR] [--hub HUB]
                    [--hubs HUBS [HUBS ...]] -i FILE_IN [-o FILE_OUT] [-n FILE_NETWORK_OUT]

Building airline network from Flightradar24 json file.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --stats, -s           print on screen some network stats and exit
  --verbosity {info,debug,error}
                        verbosity level
  --log-dir LOG_DIR
  --hub HUB             hub for network
  --hubs HUBS [HUBS ...]
                        all company hubs
  -i FILE_IN            input json file from Flightradar24
  -o FILE_OUT           output ASCII schedule file
  -n FILE_NETWORK_OUT   print network json file

```

## Pilots database management

This is a tool for creating an sql table flight and inserting the 
data for different pilots. The format is a modified version of the
SQL from altervista (at least for the DB structure). Data can be
imported from a direct download. If a flight with the same id exists
an error is given.

Usage:
```
manage_db.py [-h] --db-name DB_NAME [--force] [--file-db FILE_DB] [--insert] [--data-file DATA_FILE]

Managing pilots DB "flights" table from altervista

optional arguments:
  -h, --help            show this help message and exit
  --db-name DB_NAME

new database:
  --force               force creation of new db
  --file-db FILE_DB     database sql structure file

insert data into the database:
  --insert              insert data into the db
  --data-file DATA_FILE
                        data to insert as sql command(s)
```