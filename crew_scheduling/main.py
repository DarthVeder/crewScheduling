import logging.config
import argparse
from crew_scheduling.airline import Airline
from crew_scheduling.pilot import Pilot
from datetime import datetime, timedelta
# from crew_scheduling.menu import main_menu

MAJOR = 4
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

logging.config.dictConfig(LOGGING_DICT)
logger = logging.getLogger('crew_scheduler')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='crew scheduler'
    )
    # parser.add_argument(
    #     '--company',
    #     '-c',
    #     help='company FSC cfg file',
    #     dest='company',
    #     required=True
    # )
    parser.add_argument(
        '--pilot',
        '-p',
        help='pilot configuration file',
        dest='pilot_file',
        required=True
    )
    # parser.add_argument(
    #     '--load',
    #     '-l',
    #     help='load company save file',
    #     dest='load',
    #     action='store_true',
    #     default=False
    # )
    # parser.add_argument(
    #     '--load-file',
    #     help='company save file to load',
    #     dest='file_save',
    #     default=None
    # )
    parser.add_argument(
        '--log-level',
        dest='log_level',
        choices=['info', 'debug'],
        default='info'
    )
    parser.add_argument(
        '--log-dir',
        dest='log_dir',
        default=r'C:\home\FSXTools\crewScheduling\crew_scheduling'
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
        required=False
    )

    args = parser.parse_args()
    try:
        if args.log_level == 'debug':
            LOGGING_DICT['handlers']['console_handler']['level'] = logging.DEBUG
    except Exception as e:
        print(e)
        exit(1)

    logger.info('starting')
    logger.debug('args: {}'.format(args))

    # try:
        # if args.load:
        #     if not args.file_save:
        #         logger.error('--load needs --load-file')
        #         exit(1)
        #     logger.info('loading')
        #     company = Airline.unpickle(args.file_save)
        #     print(company.nsave)
        #     logger.debug(company.get_company_data())
        #     logger.debug('done')
        # else:
        #     logger.info('starting new company')
        #     company = Airline(args.hub, args.company)
    try:
        logging.info(
            'loading pilot file {}'
            .format(args.pilot_file)
        )
        pilot = Pilot(args.pilot_file)
        pilot.view_data()

    except Exception as e:
        logger.error(
            'starting error. err={}'
            .format(e)
        )
        exit(1)

    # while True:
    #     try:
    #         main_menu.show()
    #         choice = input('Choice? ')
    #         main_menu.action(choice, company=company)
    #     except Exception as e:
    #         print('wrong choice. err={}'.format(e))
