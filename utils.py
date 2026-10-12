import random
import pandas as pd
from typing import List
from geopy.distance import geodesic


CENTRAL_LAT = 37.9837
CENTRAL_LON = 23.7378

# Generate Data
def generate_points(n: int, seed: int, payload_capacity: float) -> pd.DataFrame:
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        rows.append(
            {
                "id": i,
                "label": f"Point {i + 1}",
                "latitude": CENTRAL_LAT + rnd.uniform(-0.05, 0.05),
                "longitude": CENTRAL_LON + rnd.uniform(-0.05, 0.05),
                "weight": round(rnd.uniform(0.3, payload_capacity), 1),
            }
        )
    return pd.DataFrame(rows)



# Distance calculation between two points of the route and convertion to km.
def dist(points: pd.DataFrame, i: int, j: int) -> float:
    return geodesic(
        (points.iloc[i]["latitude"], points.iloc[i]["longitude"]),
        (points.iloc[j]["latitude"], points.iloc[j]["longitude"]),
    ).kilometers

# Caluclates the distance between all points in a given route.
def route_distance(points: pd.DataFrame, route: List[int]) -> float:
    n = len(route)
    total = 0
    for k in range(n):
        total += dist(points, route[k], route[(k + 1) % n])
    return total

# Metrics and return dictionaries
def compute_metrics(points: pd.DataFrame, r: List[int], max_speed: float,battery_capacity: float) -> dict:
    total_dist = route_distance(points, r)
    total_time = (total_dist / max_speed) * 60  # total mission flight time in minutes
    total_weight = sum(points.iloc[i]["weight"] for i in r)
    
    is_ok = total_time <= battery_capacity

    if is_ok:
        battery_used = total_time
        battery_remaining = battery_capacity - total_time
        status = "OK"
    else:
        battery_used = battery_capacity
        battery_remaining = 0.0
        status = "Fail"

    return {
        "distance": total_dist,
        "time": total_time,
        "weight": total_weight,
        "battery_used": battery_used,
        "battery_remaining": battery_remaining,
        "status": status,
    }