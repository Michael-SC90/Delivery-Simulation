# Michael Craig, 000955248


# Dijkstra's Algorithm:
# Adds all possible routes to an unvisited queue from an
# initial vertex, iterating through list of vertices to
# determine potentially shorter routes to each other vertex.
# O(N^2), where N = total number of locations in map (all vertices are connected via edges)
def dsp(g, start_vertex):
    unvisited_queue = []
    for current_vertex in g.adjacency_lst:
        current_vertex.distance = float('inf')
        current_vertex.predecessor = None
        unvisited_queue.append(current_vertex)
    start_vertex.distance = 0
    while len(unvisited_queue) > 0:
        smallest_index = 0
        for i in range(1, len(unvisited_queue)):
            if unvisited_queue[i].distance < unvisited_queue[smallest_index].distance:
                smallest_index = i
        current_vertex = unvisited_queue.pop(smallest_index)
        for adj_vertex in g.adjacency_lst[current_vertex]:
            edge_distance = g.edge_weights[(current_vertex, adj_vertex)]
            alternative_total_distance = round(current_vertex.distance + edge_distance, 4)
            if alternative_total_distance < adj_vertex.distance:
                adj_vertex.distance = alternative_total_distance
                adj_vertex.predecessor = current_vertex
    return


# Creates list of all visited vertices en route to a location
# in order from last vertex to first; reverses order of list
# before returning to caller.
# O(N), where N = number of vertices (leafs in tree) through tour (branch)
def shortest_tour(start_vertex, end_vertex):
    path = []
    current_vertex = end_vertex
    while current_vertex is not start_vertex:
        path.append(current_vertex)
        current_vertex = current_vertex.predecessor
    path.append(start_vertex)
    path = path[::-1]
    return path


# Returns total distance over shortest tour by utilizing
# Dijkstra's algorithm to produce the shortest path to a
# node, then returning the distance to that node.
# O(N^2) with dsp
def shortest_distance(graph, start_vertex, end_vertex):
    dsp(graph, start_vertex)
    tour_leg = shortest_tour(start_vertex, end_vertex)
    return tour_leg[-1].distance
