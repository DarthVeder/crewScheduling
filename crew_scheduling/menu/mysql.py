import sqlite3
from datetime import time, timedelta, datetime, date





def create(conn):
    file_in = 'flights_structure'
    with open(file_in, 'r') as fin:
        sql_script = fin.readlines()

    sql_script = ''.join(sql_script)

    conn.executescript(sql_script)



def load_data(conn):
    file_in = 'data'

    with open(file_in, 'r') as fin:
        data = fin.readlines()

    conn.executescript(''.join(data))


def extract(conn, pilot):
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('select * from flights where UserName = ?', (pilot,))
    r = c.fetchone()
    print(r.keys())
    
    c.execute('select * from flights where UserName = ?', (pilot,))

    return c.fetchall()

    

if __name__ == '__main__':

    conn = sqlite3.connect('my_mrk.db')

#    create(conn)

#    load_data(conn)

    pilot = 'AT1368'
    data = extract(conn, pilot)


#    for d in data:
#        print(tuple(d))

    total_time = datetime.combine(date.today(), time(hour=0))
    for d in data:
        #print(time.fromisoformat(d['TotalBlockTime']))
        timeobj = time.fromisoformat(d['TotalBlockTime'])
        total_time = total_time + \
        (datetime.combine(date.min, timeobj) - datetime.min)


    print('{}h {}m'.format(total_time.time().hour, total_time.time().minute))
    conn.close()
