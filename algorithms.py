import random
import math
import pandas as pd
from typing import List
from utils import dist, route_distance



def nearest_neighbor(points: pd.DataFrame) -> List[int]:

    unvisited = set(range(len(points)))
    current = 0
    route = [current]
    unvisited.remove(current)
   
    while len(unvisited) > 0:
        
        closest_point = None
        closest_dist = math.inf

        for point in unvisited:
            distance = dist(points, current, point)
            if distance < closest_dist:
                closest_point = point
        
        route.append(closest_point)
        unvisited.remove(closest_point)

        current = closest_point

    return route


def genetic_algorithm(points: pd.DataFrame, pop_size: int = 60, generations: int = 100) -> List[int]:
    n = len(points)

    def shuffle() -> List[int]:
        a = list(range(n))
        random.shuffle(a)
        return a

    def crossover(p1: List[int], p2: List[int]) -> List[int]:
        s = random.randint(0, n - 1)
        e = random.randint(s, n - 1)
        child: List[int] = [-1] * n
        child[s : e + 1] = p1[s : e + 1]
        ptr = (e + 1) % n
        for g in p2:
            if g not in child:
                child[ptr] = g
                ptr = (ptr + 1) % n
        return child

    def mutate(ind: List[int]) -> List[int]:
        if random.random() < 0.2:
            i, j = random.sample(range(n), 2)
            ind[i], ind[j] = ind[j], ind[i]
        return ind

    pop = [shuffle() for _ in range(pop_size)]
    for _ in range(generations):
        pop.sort(key=lambda r: route_distance(points, r))
        top = pop[: pop_size // 2]
        offspring = top[:]
        while len(offspring) < pop_size:
            p1, p2 = random.sample(top, 2)
            offspring.append(mutate(crossover(p1, p2)))
        pop = offspring
    return pop[0]


def simulated_annealing(points: pd.DataFrame, temp: float = 500, cooling: float = 0.995, iters: int = 1000) -> List[int]:
    n = len(points)
    current = list(range(n))
    random.shuffle(current)
    dist = route_distance(points, current)
    best_route  = current[:]
    best_distance = dist

    for _ in range(iters):
        route = current[:]
        i, j = random.sample(range(n), 2)
        route[i], route[j] = route[j], route[i]
        ndist = route_distance(points, route)
        if ndist < dist or random.random() < math.exp((dist - ndist) / max(temp, 1e-9)):
            current, dist = route, ndist
        if dist <  best_distance:
            best_route,  best_distance = current[:], dist
        temp *= cooling
    return best_route