'''
Test py file for reading json format from flightrada24.com
'''
import json
import random

random.seed()
file = 'routes.json'
#file = 'test.json'

company_code = 'AT'

if __name__ == '__main__':
    with open(file, 'r') as file:
        data = json.load(file)

    for d in data:
        dep = d['airport1']['icao']
        arr = d['airport2']['icao']
        dep_h = random.randint(0,23)
        dep_m = random.randrange(0,59,5)
        dep_time_lt = '{:02}{:02}'.format(dep_h,dep_m)
        flight_number = company_code + str(random.randint(1,9999))
        flight_string = f'{flight_number} {dep} {dep_time_lt} -> {arr}'
        print(flight_string)
