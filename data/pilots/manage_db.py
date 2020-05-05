import sqlite3
from datetime import time, timedelta, datetime, date
import argparse


def create_db(db_name, file_in):
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("drop table if exists flights;")
        with open(file_in, 'r') as fin:
            sql_script = fin.readlines()

        sql_script = ''.join(sql_script)

        c.execute(sql_script)
        conn.commit()
        conn.close()
    except Exception as e:
        print("error in creating table 'flights'. err={}"
              .format(e))


def load_data(db_name, data_file):
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        with open(data_file, 'r') as fin:
            data = fin.readlines()
        c.execute(''.join(data))
        conn.commit()
        conn.close()
    except Exception as e:
        print("error in inserting data into table 'flights'. err={}"
              .format(e))

def extract(conn, pilot):
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('select * from flights where UserName = ?', (pilot,))
    r = c.fetchone()
    print(r.keys())
    
    c.execute('select * from flights where UserName = ?', (pilot,))

    return c.fetchall()
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Managing pilots DB from altervista')
    parser.add_argument(
        '--db-name',
        dest='db_name',
        required=True
    )
    group_db = parser.add_argument_group('new database')
    group_db.add_argument(
        '--force',
        help='force creation of new db',
        required=False,
        default=None,
        dest='force',
        action='store_true'
    )
    group_db.add_argument(
        '--file-db',
        help='database sql structure file',
        dest='file_db',
        default=None
    )
    group_i = parser.add_argument_group('insert data into the database')
    group_i.add_argument(
        '--insert',
        help='insert data into the db',
        required=False,
        default=None,
        dest='insert',
        action='store_true'
    )
    group_db.add_argument(
        '--data-file',
        help='data to insert as sql command(s)',
        dest='data_file',
        default=None
    )
    args = parser.parse_args()
    print(args)
    if args.force and not args.file_db:
        parser.error('--force requires --file-db')
    if args.insert and not args.data_file:
        parser.error('--insert requires --data-file')

    if args.force:
        create_db(args.db_name, args.file_db)
        exit(0)

    if args.insert:
        load_data(args.db_name, args.data_file)
#
#     pilot = 'AT1368'
#     data = extract(conn, pilot)
#
#
# #    for d in data:
# #        print(tuple(d))
#
#     total_time = datetime.combine(date.today(), time(hour=0))
#     for d in data:
#         #print(time.fromisoformat(d['TotalBlockTime']))
#         timeobj = time.fromisoformat(d['TotalBlockTime'])
#         total_time = total_time + \
#         (datetime.combine(date.min, timeobj) - datetime.min)
#
#
#     print('{}h {}m'.format(total_time.time().hour, total_time.time().minute))
#     conn.close()
