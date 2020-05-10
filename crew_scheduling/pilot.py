import logging
import configparser

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

    def save_status(self):
        pass

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
        pass
        # for k, v in self.data.items():
        #     logger.info('{}: {}'.format(k, v))

    def get_data(self):
        return self.data


if __name__ == '__main__':
    file = r'C:\home\FSXTools\crewScheduling\data\pilots\ram_malik.cfg'
    pilot = Pilot(file)

    for k, v in pilot.get_data().items():
        print('{}: {}'.format(k, v))

