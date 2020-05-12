import logging
import configparser
from datetime import datetime, time, date, timedelta
import sqlite3

logger = logging.getLogger('crew_scheduler.' + __name__)


class Pilot:
    def __init__(self, pilot_file=None):
        if not pilot_file:
            logger.error('Pilot class need a file as argument')
            exit(1)
        config = configparser.ConfigParser()
        found = config.read(pilot_file)
        if not found:
            logger.error(
                'pilot file "{}" not found'
                .format(pilot_file)
            )
            exit(1)
        self.data = {}
        self.data.setdefault('cfg_file', pilot_file)
        self.data.setdefault('name', config.get('DEFAULT', 'name'))
        self.data.setdefault('grade', None if 'None' in config.get('DEFAULT', 'grade') \
            else config.get('DEFAULT', 'grade'))
        self.data.setdefault('aircraft_id', None if 'None' in config.get('DEFAULT', 'aircraft_id') \
            else config.get('DEFAULT', 'aircraft_id'))
        self.data.setdefault('company_file', config.get('DEFAULT', 'company_file'))
        self.data.setdefault('hours', 0.0)
        self.data.setdefault('hub', config.get('DEFAULT', 'hub'))
        self.data.setdefault('id', config.get('DEFAULT', 'id'))
        self.data.setdefault(
            'last_airport', config.get('DEFAULT', 'hub')
            if 'None' in config.get('DEFAULT', 'last_airport')
            else config.get('DEFAULT', 'last_airport'))
        self.data.setdefault('pilot_db', config.get('DEFAULT', 'pilot_db'))

    def get_total_hours(self):
        try:
            conn = sqlite3.connect(self.get('pilot_db'))
            conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.error(
                'pilots db connection error. err={}'
                .format(e)
            )
            exit(1)

        c = conn.cursor()
        flights = c.execute('select * from flights where UserName = ?',
                            (self.get('id'),))

        total_time = timedelta(seconds=0)
        for f in flights:
            h, m , s = f['TotalBlockTime'].split(':')
            total_time = total_time + timedelta(hours=int(h), minutes=int(m),
                                                seconds=int(s))

        conn.close()

        return total_time.total_seconds()/3600.0

    def save_status(self):
        config = configparser.ConfigParser()
        for k, v in self.data.items():
            config['DEFAULT'][k] = str(v)
        file_out = self.data.get('cfg_file')
        with open(file_out, 'w') as fout:
            config.write(fout)

    def set_aircraft(self, new_aircraft_id):
        self.data['aircraft_id'] = new_aircraft_id

    def get(self, key):
        return self.data.get(key, None)

    def set_last_airport(self, new_last_airport):
        self.data.update(
            {
                'last_airport': new_last_airport
            }
        )

    def create(self, name):
        self.data.update(
            {
                'name': name
            }
        )

    def view_data(self):
        for k, v in self.data.items():
            logger.info('{}: {}'.format(k, v))

    def get_data(self):
        return self.data
