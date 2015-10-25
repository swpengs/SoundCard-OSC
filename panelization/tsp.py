#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import random
import itertools
import time



cities = []

def plot_tour(tour):
    "Plot the cities as circles and the tour as lines between them."
    plot_lines(list(tour) + [tour[0]])

def plot_lines(points, style='bo-'):
    "Plot lines to connect a series of points."
    plt.plot(map(X, points), map(Y, points), style)
    plt.axis('scaled'); plt.axis('off')

def plot_tsp(algorithm, cities):
    "Apply a TSP algorithm to cities, plot the resulting tour, and print information."
    # Find the solution and time how long it takes
    t0 = time.clock()
    tour = algorithm(cities)
    t1 = time.clock()
    assert valid_tour(tour, cities)
    #plot_tour(tour); plt.show()
    print("{} city tour with length {:.1f} in {:.3f} secs for {}" .format(len(tour), tour_length(tour), t1 - t0, algorithm.__name__))
    return tour

def valid_tour(tour, cities):
    "Is tour a valid tour for these cities?"
    return set(tour) == set(cities) and len(tour) == len(cities)

# Cities are represented as Points, which are represented as complex numbers
Point = complex
City  = Point

def X(point):
    "The x coordinate of a point."
    return point.real

def Y(point):
    "The y coordinate of a point."
    return point.imag

def distance(A, B):
    "The distance between two points."
    dist = A - B
    return max(abs(dist.real), abs(dist.imag))


def altered_greedy_tsp(cities):
    "Run greedy TSP algorithm, and alter the results by reversing segments."
    return alter_tour(greedy_tsp(cities))

def alter_tour(tour):
    "Try to alter tour for the better by reversing segments."
    original_length = tour_length(tour)
    for (start, end) in all_segments(len(tour)):
        reverse_segment_if_better(tour, start, end)
    # If we made an improvement, then try again; else stop and return tour.
    if tour_length(tour) < original_length:
        return alter_tour(tour)
    return tour

def reverse_segment_if_better(tour, i, j):
    "If reversing tour[i:j] would make the tour shorter, then do it."
    # Given tour [...A-B...C-D...], consider reversing B...C to get [...A-C...B-D...]
    A, B, C, D = tour[i-1], tour[i], tour[j-1], tour[j % len(tour)]
    # Are old edges (AB + CD) longer than new ones (AC + BD)? If so, reverse segment.
    if distance(A, B) + distance(C, D) > distance(A, C) + distance(B, D):
        tour[i:j] = reversed(tour[i:j])

def all_segments(N):
    "Return (start, end) pairs of indexes that form segments of tour of length N."
    return [(start, start + length) for length in range(N, 2-1, -1) for start in range(N - length + 1)]


def greedy_tsp(cities):
    """Go through edges, shortest first. Use edge to join segments if possible."""
    edges = shortest_edges_first(cities) # A list of (A, B) pairs
    endpoints = {c: [c] for c in cities} # A dict of {endpoint: segment}
    for (A, B) in edges:
        if A in endpoints and B in endpoints and endpoints[A] != endpoints[B]:
            new_segment = join_endpoints(endpoints, A, B)
            if len(new_segment) == len(cities):
                return new_segment

def tour_length(tour):
    "The total of distances between each pair of consecutive cities in the tour."
    return sum(distance(tour[i], tour[i-1]) for i in range(len(tour)))


def shortest_edges_first(cities):
    "Return all edges between distinct cities, sorted shortest first."
    edges = [(A, B) for A in cities for B in cities if id(A) < id(B)]
    return sorted(edges, key=lambda edge: distance(*edge))

def join_endpoints(endpoints, A, B):
    "Join B's segment onto the end of A's and return the segment. Maintain endpoints dict."
    Asegment, Bsegment = endpoints[A], endpoints[B]
    if Asegment[-1] is not A: Asegment.reverse()
    if Bsegment[0] is not B: Bsegment.reverse()
    Asegment.extend(Bsegment)
    del endpoints[A], endpoints[B]
    endpoints[Asegment[0]] = endpoints[Asegment[-1]] = Asegment
    return Asegment

def Cities(n, width=900, height=600, seed=42):
    "Make a set of n cities, each with random coordinates within a (width x height) rectangle."
    random.seed(seed * n)
    return frozenset(City(random.randrange(width), random.randrange(height)) for c in range(n))


def shortest_tour(tours):
    "Choose the tour with the minimum tour length."
    return min(tours, key=tour_length)

def tour_length(tour):
    "The total of distances between each pair of consecutive cities in the tour."
    return sum(distance(tour[i], tour[i-1]) for i in range(len(tour)))

def add_city(x, y):
    global cities
    cities.append(City(x, y))

"""
def find_start_end():
    global cities, city_start, city_end
    city_start = cities[0]
    city_end = cities[0]
    # 左上角的值
    city_leftupper = City(0, max([c.imag for c in cities]))
    city_leftlower = City(0, 0)
    for city in cities:
        if distance_raw(city, city_leftlower) < distance_raw(city_start, city_leftlower):
            city_start = City(city)
        if distance_raw(city, city_leftupper) < distance_raw(city_end, city_leftupper):
            city_end = City(city)
"""




if __name__ == '__main__':
    #plot_tsp(altered_greedy_tsp, Cities(60*36))
    cities = []
    for i in range(15*36):
        add_city(random.randrange(1000), random.randrange(1000))
    #find_start_end()

    #print city_start
    #print city_end
    tour = plot_tsp(altered_greedy_tsp, frozenset(cities))
    print tour
