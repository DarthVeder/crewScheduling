import json


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
            print('ll')
            print(apt)
            print(iarr)
            print(lnetwork)
            print(pnetwork.get(apt))
        
        # pnetwork[apt].pop(iarr)
        flights.update(
            {apt: arr}
            )
        visited[apt] = visited.get(apt, 0) + 1
        apt = arr

    return flights, visited, apt


if __name__ == '__main__':
    file_in = './data/avianca_routes.json'

    data = read_flightradar_data(file_in)


    network = {}    
    for i in data:
        dep = i.get("airport1")['icao']
        arr = i.get("airport2")['icao']
        # print('{} -> {}'.format(dep, arr))
        if dep not in network.keys():
            network[dep] = [arr]
        else:
            network[dep].append(arr)


 #   phubs = find_probable_hubs(network)
 #   print(phubs)

    hubs = ['SKBO', 'MSLP', 'SPJC', 'MROC', 'SEQM']
    for hub in hubs:
        connections = network.get(hub, None)
        if connections:
            print('HUB: {}\n  Destinations: {}'
                  .format(hub, connections))

    fout = open('test.json', 'w')
    json.dump(network, fout, indent=4)
    fout.close()


    import random
    random.seed()
    assigned_hub = 'SPJC'
     # hubs[
     #   random.randrange(len(hubs))
     #   ]
    print('Assigned hub: {}'.format(assigned_hub))

    pnetwork = network.copy()

    for hub in [h for h in hubs if h not in assigned_hub]:
        flights_to_remove = [x for x in pnetwork[hub]
                             if x not in assigned_hub]
        for f in flights_to_remove:
            pnetwork[hub].remove(f)

 #   print(
 #       json.dumps(pnetwork, indent=4)
 #       )

    apt = assigned_hub
    for n in range(3):
        print('Schedule {}'.format(n))
        print('From {}'.format(apt))
        flights, visited, end = generate_schedule(apt, pnetwork)
        apt = end
        

        for d, a in flights.items():
            print('{}[{}] - {}[{}]'.format(d, visited.get(d, 0),
                                           a, visited.get(a, 0)))





