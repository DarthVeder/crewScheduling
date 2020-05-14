import logging
import configparser
from datetime import datetime, time, date, timedelta
import sqlite3
import json

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
        self.db_data = {}
        self.data = {}
        self.cfg_file = pilot_file
        self.data.setdefault('name', config.get('DEFAULT', 'name'))
        self.data.setdefault('upgraded', config.getboolean('DEFAULT', 'upgraded'))
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
        self.data.setdefault(
            'tree', dict() if 'None' in config.get('DEFAULT', 'tree')
            else json.loads(config.get('DEFAULT', 'tree'))
        )
        self._fetch_data_from_db()

    def upgrade(self):
        self.data['upgrade'] = True

    def get_visited(self):
        return self.data.get('tree')

    def update_visited(self, new_visited):
        visited = self.data.get('tree', {})
        for k, v in new_visited.items():
            if k in visited:
                visited.update({k: v})
            else:
                visited[k] = v

        self.data.update({'tree': visited})

    def _fetch_data_from_db(self):
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
            h, m, s = f['TotalBlockTime'].split(':')
            total_time = total_time + timedelta(hours=int(h), minutes=int(m),
                                                seconds=int(s))
            aircraft_id = f['AircraftName'].split()[0]
            nf = self.db_data.setdefault(aircraft_id, 0) + 1
            self.db_data.update({aircraft_id: nf})

        conn.close()
        self.db_data.setdefault('total_time', total_time)

    def get_flight_with_aircraft(self, aircraft_id):
        return self.db_data.get(aircraft_id, 0)

    def _get_total_hours(self):
        return self.db_data['total_time'].total_seconds()/3600.0

    def save_status(self):
        config = configparser.ConfigParser()
        tree = self.data.pop('tree')
        config['DEFAULT']['tree'] = json.dumps(tree)
        for k, v in self.data.items():
            config['DEFAULT'][k] = str(v)
        file_out = self.cfg_file
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
