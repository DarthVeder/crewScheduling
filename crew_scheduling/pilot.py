import logging
import configparser
import pickle

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

        self.save_name = pilot_file.split('.')[0]
        self.nsave = 0
        self.name = config.get('DEFAULT', 'name')
        self.grade = None if 'None' in config.get('DEFAULT', 'grade') \
            else config.get('DEFAULT', 'grade')
        self.aircraft_id = None if 'None' in config.get('DEFAULT', 'aircraft_id') \
            else config.get('DEFAULT', 'aircraft_id')
        self.company_file = config.get('DEFAULT', 'company_file')
        self.hours = 0.0
        self.hub = config.get('DEFAULT', 'hub')
        self.id = config.get('DEFAULT', 'id')
        self.last_airport = None

    def get_company_file(self):
        return self.company_file

    def get_hub(self):
        return self.hub

    def create(self, name):
        self.name = name

    def view_data(self):
        for k, v in self.get_data().items():
            logger.info('{}: {}'.format(k, v))

    def get_data(self):
        return {
            'name': self.name,
            'id': self.id,
            'aircraft_id': self.aircraft_id,
            'grade': self.grade,
            'hours': self.hours,
            'hub': self.hub
        }

    # def pickle(self):
    #     file_save = '{}.{}.cs'.format(self.save_name, self.nsave)
    #     self.nsave += 1
    #     f = open(file_save, 'wb')
    #     pickle.dump(self, f)
    #     f.close()
    #     logger.info('dumpig pilot file "{}"'.format(self.save_name))
    #
    # @staticmethod
    # def unpickle(file_save):
    #     try:
    #         with open(file_save, 'rb') as f:
    #             return pickle.load(f)
    #     except Exception as e:
    #         logger.error('unpickle err={}'.format(e))
    #         exit(1)
    #     logger.info('unpickled pilot file {}'.format(file_save))


if __name__ == '__main__':
    file = r'C:\home\FSXTools\crewScheduling\data\pilots\ram_malik.cfg'
    pilot = Pilot(file)

    for k, v in pilot.get_data().items():
        print('{}: {}'.format(k, v))

    # pilot.pickle()
    #
    # print('unpickling')
    # pilot = Pilot.unpickle(r'C:\home\FSXTools\crewScheduling\data\pilots\ram_malik.0.cs')
    #
    # for k, v in pilot.get_data().items():
    #     print('{}: {}'.format(k, v))
