import logging.config
import argparse
from crewScheduling.pilot import Pilot
from crewScheduling.airline import Airline
from datetime import datetime, timedelta
import configparser
from crewScheduling.menu import main_menu

logger = logging.getLogger('crew_scheduler')

MAJOR = 3
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
            'level': logging.DEBUG,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'level': logging.DEBUG,
            'maxBytes': 1000000,
            'filename': 'crew_scheduler.log'
        }
    },
    'loggers': {
        'crew_scheduler': {
            'level': logging.DEBUG,
            'handlers': ['console_handler', 'file_handler'],
            'propagate': '0'
        }
    }
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='crew scheduler'
    )
    parser.add_argument(
        '--company',
        '-c',
        help='company FSC cfg file',
        dest='company',
        required=True
    )
    parser.add_argument(
        '--load',
        '-l',
        help='load company status',
        dest='load',
        action='store_true',
        default=False
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
    parser.add_argument(
        '--start-date',
        '-s',
        help='start date, format %Y-%m-%d',
        dest='start_date',
        type=lambda d: datetime.strptime(d, '%Y-%m-%d'),
        required=True
    )
    parser.add_argument(
        '--hub',
        help='hub',
        dest='hub',
        required=True
    )

    args = parser.parse_args()
    try:
        if args.log_level == 'debug':
            LOGGING_DICT['handlers']['console_handler']['level'] = logging.DEBUG
    except Exception as e:
        print(e)
        exit(1)

    logging.config.dictConfig(LOGGING_DICT)
    logger.info('starting')
    logger.debug('args: {}'.format(args))

    config = configparser.ConfigParser()
    try:
        if args.load:
            logger.info('loading')
            # new_company = Airline()
            # new_company = Airline.unpickle()
        else:
            logger.info('starting new company')
            with open(args.company, 'r') as fc:
                config_str = '[DEFAULT]\n' + fc.read()
            new_config_str = []
            for s in config_str.split('\n'):
                if 'PAYLEVEL' in s:
                    _, num_jump_grade = s.split('=')
                    num, jump, grade = num_jump_grade.split(',')
                    s = '='.join(
                        ['PAYLEVEL_{}'.format(num),
                         ','.join([jump, grade])
                        ]
                    )
                new_config_str.append(s)

            config.read_string('\n'.join(new_config_str))
            new_company = Airline(args.hub, config)
    except Exception as e:
        logger.error(
            'error in reading company file {}. err={}'
            .format(args.company, e)
        )
        exit(1)

    while True:
        try:
            main_menu.show()
            choice = input('Choice? ')
            main_menu.action(choice, company=new_company)
        except Exception as e:
            print('wrong choice. err={}'.format(e))

    # load = False
    # if not load:
    #     company_config_file = r'..\data\royal_air_maroc\RoyalAirMaroc.cfg'
    #     company_schedule_file = r'..\data\royal_air_maroc\RoyalAirMaroc_schedule.txt'
    #     company_fleet_file = r'..\data\royal_air_maroc\fleet.yml'
    #
    #     new_company = Airline(company_config_file)
    #
    #     pilot1 = Pilot('Giovannino Liguori')
    #     new_company.assignPilot(pilot1)
    #     pilot2 = Pilot('Ibrahim Mustafà')
    #     new_company.assignPilot(pilot2)
    #
    #     new_company.loadFleet(company_fleet_file)
    #     new_company.buildRoutes(company_schedule_file)
    #     new_company.setActivePilot(pilot1)
    #     new_company.assignAircraftToActivePilot()
    #     new_company.assignGrade()
    #
    #     # Saving to file
    #     new_company.pickle()
    # else:
    #     # To recover from file:
    #     new_company = Airline()
    #     new_company = Airline.unpickle()

        # new_company.assignAircraftToPilot()
        # new_company.assignGrade()

    # print('Active pilot: {}'.format(new_company.active_pilot.retrieve()))

    # new_company.assignRoster()
