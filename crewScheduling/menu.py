from crewScheduling.pilot import Pilot


class Menu:
    def __init__(self, choices):
        self.choices = choices

    def action(self, selection, **kwargs):
        if self.check(selection):
            self.choices[selection][1](**kwargs)

    def check(self, selection):
        print(selection)
        if selection not in self.choices.keys():
            print('wrong choice')
            return False

        return True

    def show(self):
        for m, ca in self.choices.items():
           print(m, ca[0])


def show_pilots(**kwargs):
    kwargs['company'].show_pilots()


def create_pilot(**kwargs):
    name = input('Name? ')
    pilot = Pilot(name)
    kwargs['company'].assign_pilot(pilot)
    kwargs['company'].set_active_pilot(pilot)
    kwargs['company'].assign_aircraft_to_active_pilot()
    kwargs['company'].assign_grade()


def set_active_pilot(**kwargs):
    kwargs['company'].set_active_pilot(kwargs['pilot'])


def save(**kwargs):
    print('save company')


def end_menu(**kwargs):
    exit(0)


def change_active_pilot(**kwargs):
    pilots = kwargs['company'].get_pilots()
    d_pilots = {}
    for i, p in enumerate(pilots):
        d_pilots[str(i)] = (p.name, set_active_pilot)

    pilot_lists = Menu(d_pilots)
    pilot_lists.show()
    pilot_id = input('Choice? ')
    pilot_lists.action(pilot_id, company=kwargs['company'],
                       pilot=pilots[int(pilot_id)])


pilot_submenu = Menu({
    '1': ('Select active pilot', change_active_pilot),
    '2': ('Show Pilots', show_pilots),
    '3': ('Exit', end_menu)
})


def show_pilot_submenu(**kwargs):
    while True:
        pilot_submenu.show()
        choice = input('Choice? ')
        pilot_submenu.action(choice, **kwargs)


main_menu = Menu({
    '1': ('Show Pilots', show_pilots),
    '2': ('Create Pilots', create_pilot),
    '3': ('Save', save),
    '4': ('Change Active Pilot', show_pilot_submenu),
    '5': ('Exit', end_menu)
})
