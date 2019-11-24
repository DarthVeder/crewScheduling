"""
Class to manage an airline company.

Author: MM
Copyright: 2019 -
Licensce: GPL 3.0
"""
import pickle
from pilot import Pilot
import collections
import yaml

Grade = collections.namedtuple('Grade', 'hours title')

class Airline:
    def __init__(self, config_file = None):
        if config_file is None:
            name = None
            code = None
            grades = {}
        else:
            name, code, grades = self.readConfigurationFile(config_file)

        self.name = name
        self.code = code
        self.grades = grades
        self.pilots = []
        self.aircrafts = {}
        self.flights = {}
        self.active_pilot = None
        self.__routes_tree = {}
        self.hub = 'GMMN'

    def readConfigurationFile(self, config_file):
        company_name = ''
        code = ''
        grades = {}
        with open(config_file, 'r') as fin:
            for line in fin:
                # avoiding line staring with ";"
                if line[0]!=';':
                    # trashing out part of line after inline comment starting with ";"
                    line = line.split(';')[0]
                    key, value = line.split('=')
                    if key == 'NAME':
                        company_name = value
                    elif key == 'CODE':
                        code = value
                    elif key == 'PAYLEVEL':
                        level,hours,title = value.split(',')
                        level = int(level)
                        hours = float(hours)
                        grades[level] = Grade(hours=hours, title=title.rstrip())
                
        print('Defining new company with:\nName: {}\nCode: {}\nGrades:'.format(company_name, code))
        for key, value in grades.items():
            print('{} Minimum hours: {}'.format(value.title, value.hours))
            
        return company_name, code, grades

    def retrieve(self):
        return (self.name, self.code, [x.retrieve() for x in self.pilots],
                self.grades, self.aircrafts, self.flights)

    def assignAircraftToRoutes(self, aircrafts, distance):
        regulated_distance = 1.1 * distance # 10% margin to include challenging apts
        # First loop to select all aircraft that can make this distance
        proposed_aircraft = {}
        for (ida, aircraft) in aircrafts.items():
            if aircraft['range'] > regulated_distance:
                proposed_aircraft[ida] = aircraft['name']

        # Second loop to select the aircraft with smaller range
        assigned_aircraft = None
        range_min = 1e12
        for k in proposed_aircraft.keys():
            if aircrafts[k]['range'] < range_min:
                assigned_aircraft = aircrafts[k]['name']
        
        return assigned_aircraft    

    def loadFleet(self, fleet_file):
        # Parsing Fleet file and saving the fleet in dictionary aircrafts.
        # Usage: aircrafts[id]['name' or 'ktas' or 'range']
        print('Loading fleet...', end="", flush=True)
        with open(fleet_file, 'r') as file:
            aircrafts = yaml.full_load(file)
        self.aircrafts = aircrafts
        print('[OK]')
        
    def pickle(self):
        f = open('airline.ms', 'wb')
        pickle.dump(self, f)
        f.close()

    def unpickle():
        with open('airline.ms', 'rb') as f:
            return pickle.load(f)

    def buildRoutes(self, file_schedule):
        FSX_DIRECTORY = 'C:\\Microsoft Flight Simulator X'
        import os
        from point import Point, distance

        print("Building routes....", end="", flush=True)
        # Loading FSX airports from MakeRunways file r5.csv. Storing data in airports
        # dictionary. Usage: airports[icao] = (lat, lon)
        file = 'r5.csv'
        airports = {}
        with open(FSX_DIRECTORY + os.sep+ file, 'r') as fin:
            for line in fin:
                # Inserting only the first runway and its lat, lon. It is assumed 
                # the airport has the same coordinates.
                (icao, hdg, lat, lon, *trash ) = line.split(',')
                if icao not in airports:
                    airports[icao] = (float(lat), float(lon))
                    
        # Reading full flight schedule from FSC scheduling file format
        comments = [';']
        # flights are stored in a dictionary as
        # flights[id] = (flight_id, dep, arr, hhmm_lt). If no local
        # departure time is given a -1 is set. id is just an integer index.
        flights = {}
        key = 0
        with open(file_schedule, 'r') as fin:
            for line in fin:
                line = line.rstrip() # Removing final \n in line
                if (line[0] not in comments):
                    flight_text = line.split('=')[1]
                    (flight_number, dep, arr, size, hhmm_l, *other) = flight_text.split(',')
                    # other can contain other flight info, so it should be checked
                    flights[key] = (flight_number, dep, arr, int(hhmm_l))
                    key = key + 1
        
                    new_flights = [x for x in other[1:] if x != '']
                    if new_flights:
                        flights[key] = (flight_number, arr, new_flights[0], -1)
                        key = key + 1
                        for i in range(1, len(new_flights)):
                            flights[key] = (flight_number, new_flights[i-1], new_flights[i], -1)
                            key = key + 1

        file_out = 'aircraft_routes.txt'
        fout = open(file_out, 'w')

        for (k,value) in flights.items():
            #print(k, value)
            flight_no, dep, arr, etd_lt = value
            #dep = value[1]
            Pdep = Point(airports[dep][0], airports[dep][1])
            #arr = value[2]
            Parr = Point(airports[arr][0], airports[arr][1])
            D = distance(Pdep, Parr)
        
            aircraft = self.assignAircraftToRoutes(self.aircrafts, D)
        
            #line = '{} {} ({:04d} LT)->{} {} nm {}'.format(value[0], value[1], value[3], value[2], D, aircraft)
            line = '{} {} ({:04d} LT)->{} {} nm {}'.format(flight_no, dep, etd_lt, arr, D, aircraft)
            fout.write(line+'\n')

            # Building routes tree
            if dep in self.__routes_tree.keys():
                # ok, alredy in the tree, adding the new destination tuple (fligh_no, arr)
                self.__routes_tree[dep].append((flight_no, arr))              
            else:
                self.__routes_tree[dep] = [(flight_no, arr)]


        #for k, value in routes_tree.items():
        #    print(k,value)

        fout.close()
        
        self.flights = flights
        print('[OK]')
        
#### PILOT UTILITIES
    def setActivePilot(self, active_pilot):
        self.active_pilot = active_pilot

    def assignPilot(self, new_pilot):
        self.pilots.append(new_pilot)
        
    def assignAircraftToPilot(self, pilot=None, aircraft=None):
        if aircraft is None and pilot is None:
            # assign by default first aircraft in fleet.yml file
            self.active_pilot.aircraft = list(self.aircrafts.keys())[0] 
        else:
            for p in range(len(self.pilots)):
                if pilot.name == self.pilots[p].name:
                    self.pilots[p].aircraft = aircraft

    def assignGrade(self):
        # Check to see if an active pilot exists
        if self.active_pilot is None:
            print('ERROR: assign an active pilot first')
            sys.exit()

        diff = (self.active_pilot.hours) * \
                   (-self.active_pilot.hours + self.grades[1].hours)
        if diff >= 0:
            self.active_pilot.grade = self.grades[1].title
            return
        for i in range(1,len(self.grades)):
            diff = (self.active_pilot.hours - self.grades[i-1].hours) * \
                   (-self.active_pilot.hours + self.grades[i].hours)
            if diff >= 0:
                self.active_pilot.grade = self.grades[i].title
                return 
            
    def assignRoster(self, pilot):
        start_apt = self.hub
        

        


if __name__ == '__main__':
    import sys
    load = False
    if not load:
        file_config = 'RoyalAirMaroc.cfg'
        file_schedule = 'RoyalAirMaroc_schedule.txt'
        fleet_file = 'fleet.yml'
        
        #new_company = Airline('Royal Air Maroc', 'AT')
        new_company = Airline(file_config)
        
        pilot1 = Pilot('Giovannino Liguori')
        new_company.assignPilot(pilot1)
        pilot2 = Pilot('Ibrahim Mustafà')
        new_company.assignPilot(pilot2)

        #new_company.assignAircraftToPilot(pilot1, 'B744')
        new_company.loadFleet(fleet_file)
        new_company.buildRoutes(file_schedule)
        new_company.setActivePilot(pilot1)
   
        # To save to file
        new_company.pickle()
    else:
        # To recover from file:
        new_company = Airline()
        new_company = Airline.unpickle()

        new_company.assignAircraftToPilot()
        new_company.assignGrade() 

    #print(new_company.retrieve())
    print('Active pilot: {}'.format(new_company.active_pilot.retrieve()))

 
