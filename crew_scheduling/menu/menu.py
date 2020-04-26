import sqlite3
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from datetime import datetime, timedelta, date, time
from tkinter import messagebox


def donothing():
    filewin = Toplevel(root)
    button = Button(filewin, text="Do nothing button")
    button.pack()

def about_data():
   message = [
      'By Marco Messina',
      'Copyright 2020-'
   ]
   message = '\n'.join(message)
   messagebox.showinfo("About", message)



def extract(conn, pilot):
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('select * from flights where UserName = ?', (pilot,))
    r = c.fetchone()
    print(r.keys())

    return c.fetchall()


if __name__ == '__main__':
    root = Tk()
    menubar = Menu(root)

    companymenu = Menu(menubar, tearoff=0)
    companymenu.add_command(label="Open", command=donothing)
    companymenu.add_command(label="Save", command=donothing)

    companymenu.add_command(label="Exit", command=root.quit)

    menubar.add_cascade(label="Company", menu=companymenu)

    pilotmenu = Menu(menubar, tearoff=0)
    pilotmenu.add_command(label="Insert", command=donothing)
    pilotmenu.add_command(label="Activate", command=donothing)
    pilotmenu.add_command(label="Schedule", command=donothing)

    menubar.add_cascade(label="Pilot", menu=pilotmenu)

    aboutmenu = Menu(menubar, tearoff=0)
    aboutmenu.add_command(label="About", command=about_data)

    menubar.add_cascade(label="Help", menu=aboutmenu)

    conn = sqlite3.connect('my_mrk.db', detect_types=sqlite3.PARSE_DECLTYPES |
                                                     sqlite3.PARSE_COLNAMES)
    pilot_id = 'AT1368'
    pilot_data = extract(conn, pilot_id)

    w = ScrolledText(root, undo=True)

    total_time = datetime.combine(date.today(), time(hour=0))
    for d in pilot_data:
        # print(time.fromisoformat(d['TotalBlockTime']))
        timeobj = time.fromisoformat(d['TotalBlockTime'])
        total_time = total_time + \
                     (datetime.combine(date.min, timeobj) - datetime.min)
    print(total_time)

    text = ''
    for p in pilot_data:
        text = ' '.join([p['datestamp'], p['FlightId'],
                         p['DepartureIcaoName'], p['ArrivalIcaoName']])
        w.insert(END, text + '\n')

    w.pack(expand=True, fill='both')

    root.config(menu=menubar)
    root.mainloop()
