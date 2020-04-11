'''
crew scheduler. It generates a fictitious scheduling.
Author: Marco Messina
Copyright: 2019 -
Licence: GNU 3.0
'''

import collections
import logging.config
import argparse

MINIMUM_AIRCRAFT_PREPARATION_TIME_HRS = 1.0
MINIMUM_FLIGHT_TIME_DISTANCE_HRS = 5/60
FSX_DIRECTORY = './data/'
MAXIMUM_FLIGHT_TIME_HRS = 14.0

MAJOR = 2
MINOR = 0
PATCH = 0
VERSION = '.'.join(
    [str(x) for x in [MAJOR, MINOR, PATCH]]
)
MAX_HUBS = 10
MAX_FLIGHTS_IN_SCHEDULE = 5

LOGGING_DICT = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s], %(asctime)s, %(module)s, %(name)s, %(message)s'  # noqa: E501
        },
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        }
    },
    'handlers': {
        'console_handler': {
            'class': 'logging.StreamHandler',
            'level': logging.INFO,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'level': logging.INFO,
            'maxBytes': 1000000,
            'filename': 'crew_scheduler.log'
        }
    },
    'loggers': {
        'crew_scheduler': {
            'level': logging.DEBUG,
            'handlers': ['console_handler', 'file_handler'],
            'propagate': 'no'
        }
    }
}

logging.config.dictConfig(LOGGING_DICT)
logger = logging.getLogger('crew_scheduler')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='crew scheduler'
    )
    parser.add_argument(
        '--log-level',
        dest='log_level',
        choices=['info', 'debug'],
        default='info'
    )
    parser.add_argument(
        '--log-dir',
        dest='log_dir',
        default=r'C:\home\FSXTools\crewScheduling\crewScheduling'
    )
    args = parser.parse_args()
    if args.log_level == 'debug':
        LOGGING_DICT['handlers']['console_handler']['level'] = logging.DEBUG

    logging.config.dictConfig(LOGGING_DICT)
    logger = logging.getLogger('crew_scheduler')
    logger.info('starting')
    logger.debug('ola')

    load = False
    if not load:
        company_config_file = 'RoyalAirMaroc.cfg'
        company_schedule_file = 'RoyalAirMaroc_schedule.txt'
        company_fleet_file = 'fleet.yml'

        new_company = Airline(company_config_file)

        pilot1 = Pilot('Giovannino Liguori')
        new_company.assignPilot(pilot1)
        pilot2 = Pilot('Ibrahim Mustafà')
        new_company.assignPilot(pilot2)

        new_company.loadFleet(company_fleet_file)
        new_company.buildRoutes(company_schedule_file)
        new_company.setActivePilot(pilot1)
        new_company.assignAircraftToActivePilot()
        new_company.assignGrade()

        # Saving to file
        new_company.pickle()
    else:
        # To recover from file:
        new_company = Airline()
        new_company = Airline.unpickle()

        # new_company.assignAircraftToPilot()
        # new_company.assignGrade()

    print('Active pilot: {}'.format(new_company.active_pilot.retrieve()))

    new_company.assignRoster()
