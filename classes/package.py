# Michael Craig, 000955248


# Package object for housing package information.
class Package:
    def __init__(self, p_id, address, deadline, city, state, p_zip, weight, note):
        self.id = p_id
        self.address = address
        self.deadline = deadline
        self.city = city
        self.state = state
        self.zip = p_zip
        self.weight = weight
        self.note = note
        self.status = ""
        self.arrival_time = 86399

    # String override for memory location.
    def __str__(self):
        row_format = '|\t{:<3}\t|\t{:<70}\t|\t{:<6}\t|\t{:<8}\t|\t{:<9} [{:<5}]\t|\n'
        address = "{}, {} {}".format(self.address.label, self.city, str(self.zip))
        arrival = clock_time(self.arrival_time)
        late_check = str(self.arrival_time <= self.deadline)
        row_format = row_format.format(str(self.id), address, self.weight, self.status, arrival, late_check)
        return str(row_format)


# Converts seconds count to HH:MM format
def clock_time(seconds):
    hour = int(seconds / 3600)
    if hour > 12:
        hour = hour - 12
    minute = int(seconds % 3600 / 60)
    if minute < 10:
        minute = "0" + str(minute)
    if seconds >= 43200:
        display_time = "%d:%s PM" % (hour, str(minute))
    else:
        display_time = "%d:%s AM" % (hour, str(minute))
    return display_time
