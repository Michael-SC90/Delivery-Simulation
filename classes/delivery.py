# Michael Craig, 000955248


class Delivery:
    def __init__(self, address):
        self.follows = None
        self.precedes = None
        self.address = address
        self.start_time = 0
        self.end_time = 0

    def assign_start(self, start):
        self.start_time = start

    def assign_end(self, end):
        self.end_time = end

    def __str__(self):
        data = "|\tDelivery to: %s\n" % self.address.label
        start = self.start_time
        data += "|\tTrip begins at: %s\n" % clock_time(start)
        end = self.end_time
        data += "|\tTrip ends at: %s\n" % clock_time(end)
        return str(data)


# Converts seconds count to HH:MM format
def clock_time(seconds):
    hour = seconds / 3600
    minute = seconds % 3600 / 60
    if seconds >= 43200:
        display_time = "%d:%d PM" % ((int(hour) - 12), minute)
    else:
        display_time = "%d:%d AM" % (int(hour), minute)
    return display_time
