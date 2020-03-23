import logging
import logging.config
import json
import argparse

MAJOR = 1
MINOR = 0
PATCH = 0
VERSION = '.'.join(
    [str(x) for x in [MAJOR, MINOR, PATCH]]
)
MAX_HUBS = 10
MAX_FLIGHTS_IN_SCHEDULE = 5

logging_dict = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s'  # noqa: E501
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'bnu': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': 'no'
        }
    }
}


def read_flightradar_data(file_in):
    with open(file_in, 'r') as fin:
        data = json.load(fin)

    return data


def find_probable_hubs(network):
    conn = {}
    for apt in network:
        if len(network[apt]) > 1:
            conn[apt] = len(network[apt])
    probable_hubs = {
        k: v for k, v in sorted(
            conn.items(), key=lambda x: x[1], reverse=True
        )
    }
    while len(probable_hubs) > MAX_HUBS:
        probable_hubs.popitem()

    while len(probable_hubs) > MAX_HUBS:
        probable_hubs.popitem()

    return list(probable_hubs.keys())


def generate_schedule(dep_apt, pilot_network):
    flights = []
    visited = {}
    apt = dep_apt
    while len(flights) < MAX_FLIGHTS_IN_SCHEDULE:
        lnetwork = pilot_network.get(apt)
        arr = random.choice(lnetwork)
        flights.append(
            [apt, arr]
        )
        visited[apt] = visited.get(apt, 0) + 1
        apt = arr

    end_apt = apt

    return flights, visited, end_apt


def build_network(data):
    network = {}
    for i in data:
        dep = i.get("airport1")['icao']
        arr = i.get("airport2")['icao']
        if dep not in network.keys():
            network[dep] = [arr]
        else:
            network[dep].append(arr)

    return network


def show_data(network):
    conn = {}
    for k, v in network.items():
        conn[k] = len(v)

    total_conn = sum(conn.values())
    header = 'Network data:'
    logger.info(
        '\n'.join([
            header, '\n'.join([
                '{}: {} ({:0.2f}%)'
                .format(k, v, v / total_conn * 100)
                for k, v in conn.items()
            ])
        ])
    )
    probable_hubs = find_probable_hubs(network)
    logger.info(
        'possible hubs:\n' +
        '\n'.join(probable_hubs)
    )

    for hub in probable_hubs:
        connections = network.get(hub, None)
        if connections:
            logger.debug('HUB: {}\n  Destinations: {}'
                         .format(hub, connections))

def format_schedule(flights):
    header = ['Flight duty       Duty start      Duty end      Dep. time      Arr. Time    Dep.    Arr.',
              '----------------------------------------------------------------------------------------']
    line = []
    for d, a in flights:
        line.append(
            '{dep}  {arr}'.format(dep=d, arr=a)
        )

    text = '\n'.join(header + line)

    return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Building airline network from Flightradar24 json file.'
    )

    parser.add_argument(
        '--version',
        default='%(prog)s {}'.format(VERSION),
        action='version')
    parser.add_argument(
        '--stats',
        '-s',
        help='print on screen some network stats',
        action='store_const',
        dest='stats',
        const=True
    )
    parser.add_argument(
        '--verbosity',
        help='verbosity level',
        dest='verbosity',
        choices=['info', 'debug', 'error'],
        default='INFO'
    )
    parser.add_argument(
        '-i',
        dest='file_in',
        default=None,
        required=True,
        help='input json file from Flightradar24'
    )
    parser.add_argument(
        '-o',
        help='output ASCII schedule file',
        default=None,
        dest='file_out'
    )
    parser.add_argument(
        '-n',
        help='print network json file',
        default=None,
        dest='file_network_out'
    )
    parser.add_argument(
        '--from',
        dest='from_date',
        default=None
    )
    parser.add_argument(
        '--to',
        dest='to_date',
        default=None
    )

    args = parser.parse_args()

    try:
        if args.verbosity == 'debug':
            logging_dict['handlers']['console']['level'] = 'DEBUG'
        elif args.verbosity == 'error':
            logging_dict['handlers']['console']['level'] = 'ERROR'

        logging.config.dictConfig(logging_dict)

    except Exception as e:
        print(e)
        exit(1)

    logger = logging.getLogger('bnu')
    logger.info('staring building network utility')
    logger.debug('args: {}'.format(args))
    file_in = args.file_in
    try:
        logger.info('reading file "{}"'.format(file_in))
        data = read_flightradar_data(file_in)
    except Exception as e:
        logger.error(str(e))
        exit(1)

    network = build_network(data)

    if args.stats:
        logger.info('building network statistics')
        show_data(network)
        exit(0)

    if args.file_network_out:
        try:
            logger.info('writing network json file "{}'.
                        format(args.file_network_out))
            fout = open(args.file_network_out, 'w')
            json.dump(network, fout, indent=4)
            fout.close()
        except Exception as e:
            logger.error('error in writing json network file "{}". {}'
                         .format(args.file_network_out, str(e)))
    import random

    random.seed()
    hubs = ['SKBO', 'MSLP', 'SPJC', 'MROC', 'SEQM']
    # hubs = None
    if not hubs:
        logger.info('no hub data. Guessing hubs')
        hubs = find_probable_hubs(network)
        logger.info('proposed hubs: {}'.format(' '.join(hubs)))

    assigned_hub = 'SPJC'
    # assigned_hub = None
    if not assigned_hub:
        logger.info('assigning random hub')
        assigned_hub = random.choice(hubs)

    if assigned_hub not in hubs:
       logger.error('assigned hub "{}" not in company hubs "{}'
                    .format(assigned_hub, ' '.join(hubs)))
    logger.info('Assigned hub: {}'.format(assigned_hub))

    logger.info('computing assigned hub network')

    pilot_network = network.copy()
    for hub in [h for h in hubs if h not in assigned_hub]:
        flights_to_remove = [x for x in pilot_network[hub]
                             if x not in assigned_hub]
        for f in flights_to_remove:
            pilot_network[hub].remove(f)

    logger.info('generating schedule')
    if args.from_date is None:
        logger.error('need from date for generating a schedule')
        exit(1)

    apt = assigned_hub
    for n in range(3):
        logger.debug('Schedule {}'.format(n+1))
        logger.debug('From {}'.format(apt))
        flights, visited, last_apt = generate_schedule(apt, pilot_network)
        apt = last_apt

        schedule = format_schedule(flights)
        print(schedule)
        print()

        # for d, a in flights:
        #     logger.debug('{}[{}] - {}[{}]'
        #                  .format(d, visited.get(d, 0), a, visited.get(a, 0)))
