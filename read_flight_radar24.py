import logging
import logging.config
import json


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
            'level': 'DEBUG',
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
    hubs = []
    for dest in network:
        if len(network[dest]) > 5 and dest not in hubs:
            hubs.append(dest)

    return hubs


def generate_schedule(apt, pnetwork):
    flights = {}
    visited = {}
    while len(flights) < 5:
        lnetwork = pnetwork.get(apt)
        if len(lnetwork) > 1:
            iarr = random.randrange(
                len(lnetwork)
                )
        else:
            iarr = 0
        try:
            arr = lnetwork[iarr]
        except IndexError:
            message = []
            message.append(apt)
            message.append(iarr)
            message.append(lnetwork)
            message.append(pnetwork.get(apt))
            logger.error(message)

        flights.update(
            {apt: arr}
            )
        visited[apt] = visited.get(apt, 0) + 1
        apt = arr

    return flights, visited, apt


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


if __name__ == '__main__':
    logging.config.dictConfig(logging_dict)
    logger = logging.getLogger('bnu')
    logger.info('staring building network utility')
    file_in = './data/avianca_routes.json'
    data = read_flightradar_data(file_in)

    network = build_network(data)

    # phubs = find_probable_hubs(network)
    # print(phubs)

    hubs = ['SKBO', 'MSLP', 'SPJC', 'MROC', 'SEQM']
    for hub in hubs:
        connections = network.get(hub, None)
        if connections:
            logger.debug('HUB: {}\n  Destinations: {}'
                         .format(hub, connections))

    fout = open('test.json', 'w')
    json.dump(network, fout, indent=4)
    fout.close()

    import random
    random.seed()
    assigned_hub = 'SPJC'
    logger.info('Assigned hub: {}'.format(assigned_hub))

    pnetwork = network.copy()

    for hub in [h for h in hubs if h not in assigned_hub]:
        flights_to_remove = [x for x in pnetwork[hub]
                             if x not in assigned_hub]
        for f in flights_to_remove:
            pnetwork[hub].remove(f)

    apt = assigned_hub
    for n in range(3):
        logger.debug('Schedule {}'.format(n))
        logger.debug('From {}'.format(apt))
        flights, visited, end = generate_schedule(apt, pnetwork)
        apt = end

        for d, a in flights.items():
            logger.debug('{}[{}] - {}[{}]'
                         .format(d, visited.get(d, 0), a, visited.get(a, 0)))
