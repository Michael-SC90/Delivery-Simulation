# Michael Craig, 000955248


# Vertex for graph.
class Address:
    def __init__(self, address):
        self.label = address
        self.distance = float('inf')
        self.predecessor = None
        self.arrival_time = 0


# Graph data structure
class City:
    def __init__(self):
        self.addresses = {}
        self.adjacency_lst = {}
        self.edge_weights = {}

    # Adds address object as key in a dictionary;
    # Value is list of other address objects.
    # O(1)
    def add_address(self, new_address):
        if isinstance(new_address, Address):
            self.adjacency_lst[new_address] = []
            self.addresses[new_address.label] = new_address
        else:
            raise ValueError('Unknown object %s' % new_address)

    # Appends address object to list value for address object key.
    # O(1)
    def add_directed_road(self, from_address, to_address, weight=1.0):
        self.edge_weights[(from_address, to_address)] = weight
        self.adjacency_lst[from_address].append(to_address)

    # Undirected road.
    # O(1)
    def add_route(self, from_address, to_address, weight=1.0):
        self.add_directed_road(from_address, to_address, weight)
        self.add_directed_road(to_address, from_address, weight)

    # Receives address strings as input, finds associated address objects,
    # and returns distance between the two locations.
    # O(1)
    def distance(self, from_address_string, to_address_string):
        from_address = self.addresses[from_address_string]
        to_address = self.addresses[to_address_string]
        return self.edge_weights[(from_address, to_address)]

    # Returns address object based on string value.
    # O(1)
    def get_vertex(self, label):
        return self.addresses[label]
