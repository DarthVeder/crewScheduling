'''
crew scheduler. It generates a fictitious scheduling.
Author: Marco Messina
Copyright: 2019 -
Licence: GNU 3.0
'''

import collections
import logging.config
import argparse
from pilot import Pilot
from airline import Airline

MAJOR = 2
MINOR = 0
PATCH = 0
VERSION = '.'.join(
    [str(x) for x in [MAJOR, MINOR, PATCH]]
)

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
    try:
        if args.log_level == 'debug':
            LOGGING_DICT['handlers']['console_handler']['level'] = logging.DEBUG
    except Exception as e:
        print(e)
        exit(1)

    logging.config.dictConfig(LOGGING_DICT)
    logger = logging.getLogger('crew_scheduler')
    logger.info('starting')

    load = False
    if not load:
        company_config_file = r'..\data\royal_air_maroc\RoyalAirMaroc.cfg'
        company_schedule_file = r'..\data\royal_air_maroc\RoyalAirMaroc_schedule.txt'
        company_fleet_file = r'..\data\royal_air_maroc\fleet.yml'

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
