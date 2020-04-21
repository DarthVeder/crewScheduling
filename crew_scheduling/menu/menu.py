import sqlite3
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from datetime import datetime, timedelta, date, time

def donothing():
   filewin = Toplevel(root)
   button = Button(filewin, text="Do nothing button")
   button.pack()


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
   filemenu = Menu(menubar, tearoff=0)
   filemenu.add_command(label="New", command=donothing)
   filemenu.add_command(label="Open", command=donothing)
   filemenu.add_command(label="Save", command=donothing)
   filemenu.add_command(label="Save as...", command=donothing)
   filemenu.add_command(label="Close", command=donothing)

   filemenu.add_separator()

   filemenu.add_command(label="Exit", command=root.quit)
   menubar.add_cascade(label="File", menu=filemenu)
   editmenu = Menu(menubar, tearoff=0)
   editmenu.add_command(label="Undo", command=donothing)
   
   editmenu.add_separator()

   editmenu.add_command(label="Cut", command=donothing)
   editmenu.add_command(label="Copy", command=donothing)
   editmenu.add_command(label="Paste", command=donothing)
   editmenu.add_command(label="Delete", command=donothing)
   editmenu.add_command(label="Select All", command=donothing)

   menubar.add_cascade(label="Edit", menu=editmenu)
   helpmenu = Menu(menubar, tearoff=0)
   helpmenu.add_command(label="Help Index", command=donothing)
   helpmenu.add_command(label="About...", command=donothing)
   menubar.add_cascade(label="Help", menu=helpmenu)

   conn = sqlite3.connect('my_mrk.db', detect_types=sqlite3.PARSE_DECLTYPES |
                           sqlite3.PARSE_COLNAMES)
   pilot_id = 'AT1368'
   pilot_data = extract(conn, pilot_id)

   w=ScrolledText(root, undo=True)
   
   total_time = datetime.combine(date.today(), time(hour=0))
   for d in pilot_data:
      #print(time.fromisoformat(d['TotalBlockTime']))
      timeobj = time.fromisoformat(d['TotalBlockTime'])
      total_time = total_time + \
      (datetime.combine(date.min, timeobj) - datetime.min)
   print(total_time)

   text = ''
   for p in pilot_data:
      text = ' '.join([p['datestamp'], p['FlightId'],
                p['DepartureIcaoName'], p['ArrivalIcaoName']])
      w.insert(END, text + '\n')

     # for pp in p:
     #    text = ' '.join([text, str(pp)])
#      text = ''.join([text, r'\n'])
         
   w.pack(expand=True, fill='both')



   root.config(menu=menubar)
   root.mainloop()
