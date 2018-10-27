from math import pi

'''             <<<<<<<<<<<   OBJECTS   >>>>>>>>>>>           '''

class Arc(object):
    def __init__(self, t, h, f, mf, c):
        self.tail = t
        self.head = h
        self.flow = f
        self.max_flow = mf
        self.cost = c

    def is_single_order(self):
        return self.max_flow == 1

    def is_double_order(self):
        return self.max_flow == 2

    def set_path(self, path):
        self.path = path

    def get_path(self):
        return self.path

class Station(object):
    def __init__(self, loc):
        validate_location(loc)
        self.location = loc

    def location_in_rad(self):
        return [deg2rad(self.location[0]), deg2rad(self.location[1])]

class Restaurant(Station):
    def __init__(self, r_id, loc):
        Station.__init__(self, loc)
        self.id = r_id
        self.price_range = None
        self.rating  = None
        self.menu = None

    def get_name(self):
        return self.name

    def set_name(self, n):
        self.name = n

    def get_price_range(self):
        return self.price_range

    def set_price_range(self, pr):
        self.price_range = pr

    def get_rating(self):
        return self.rating

    def set_rating(self, r):
        self.rating = r

    def get_menu(self):
        return self.menu

    def set_menu(self, m):
        self.menu = m

class Company(Station):
    def __init__(self, c_id, loc):
        Station.__init__(self, loc)
        self.id = c_id

    def get_name(self):
        return self.id

class Driver(object):
    def __init__(self, d_id, loc, num):
        validate_location(loc)
        self.location = loc
        self.id = d_id
        self.number = num

    def location_in_rad(self):
        return [deg2rad(self.location[0]), deg2rad(self.location[1])]

class Order(object):
    def __init__(self, o_id, c, rs, dl, num):
        self.id = o_id
        self.company = c
        self.restaurants = rs
        self.deadline = dl
        self.number = num

    def set_shortest_path(self, path):
        self.shortest_path = path

    def get_shortest_path(self):
        return self.shortest_path

    def __lt__(self, other):
        return self.number < other.number

    def __eq__(self, other):
        return self.number == other.number


'''             <<<<<<<<<<<   OBJECT FUNCTIONS   >>>>>>>>>>>           '''

def deg2rad(deg):
  return deg * (pi/180)

def validate_location(location):
    (lat, long) = location
    if lat < -90 or lat > 90:
        raise ValueError('Latitudes should range from -90 to 90.')
    if long < -180 or long > 180:
        raise ValueError('Longitudes should range from -180 to 180.')
