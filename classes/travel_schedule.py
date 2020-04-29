# Michael Craig, 000955248


# Tracks start and end times of trucks leaving hub, along with keeping record
# of partial distance and each location.
class TravelSchedule:
    def __init__(self, start_vertex):
        self.start_time = 0
        self.end_time = 0
        self.total_distance = 0
        self.locations = {0: start_vertex}  # distance: vertex
        self.starting_location = start_vertex
        self.last_location = start_vertex
        self.next_location = start_vertex

    # Stores time of arrival to a particular location after a certain amount of distance travelled.
    # O(1)
    def schedule_location(self, vertex):
        current_total = self.total_distance
        leg_distance = vertex.distance
        self.total_distance += leg_distance
        new_total = current_total + leg_distance
        self.locations[new_total] = vertex
        self.total_distance = new_total
        self.end_time = vertex.arrival_time
        self.last_location = vertex
        return

    # Appends delivery to end of schedule
    # O(1)
    def schedule_delivery(self, delivery, arrival_time):
        start_time = self.end_time
        delivery.assign_start(start_time)
        end_time = arrival_time
        delivery.assign_end(end_time)
        return

    # Schedules new start time for current itinerary.
    # O(1)
    def schedule_start(self, start_time):
        self.start_time = start_time
        self.end_time = start_time
        return
