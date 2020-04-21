class Pilot:
    def __init__(self, name=None):
        self.name = name
        self.grade = None
        self.aircraft = None
        self.hours = 0.0
        self.hub = None
        self.id = -1

    def create(self, name):
        self.name = name

    def get_data(self):
        return self.name, self.id, self.aircraft, self.grade, self.hours, self.hub


if __name__ == '__main__':

    new_pilot = Pilot()

    new_pilot.create('Marco Messina')

    print(new_pilot.retrieve())
