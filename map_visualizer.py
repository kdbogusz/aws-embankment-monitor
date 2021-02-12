import plotly.graph_objects as go
from random import random

START_LAT = 50.008517
START_LON = 19.125959
END_LAT = 50.012123
END_LON = 19.127879

NODE_COUNT = 500

METERS_PER_DEGREE_LAT = 111194.927
METERS_PER_DEGREE_LON = 71459.853

MIN_HEIGHT = 0
MAX_HEIGHT = 5

HEIGHT_COUNT = 6


def create_embankment():
    avg_jump_lat = (END_LAT - START_LAT) / NODE_COUNT
    min_jump_lat = avg_jump_lat / 3
    max_jump_lat = min_jump_lat * 5
    lat_to_lon_multiplier = (END_LON - START_LON) / (END_LAT - START_LAT)

    current_lat = START_LAT
    current_lon = START_LON
    lat = []
    lon = []
    while current_lat < END_LAT:
        lat.append(current_lat)
        lon.append(current_lon)
        lat_diff = random() * (max_jump_lat - min_jump_lat) + min_jump_lat
        current_lat += lat_diff
        current_lon += lat_diff * lat_to_lon_multiplier

    lat.append(END_LAT)
    lon.append(END_LON)

    current_height = MIN_HEIGHT
    heights = []
    while current_height < MAX_HEIGHT:
        heights.append(current_height)
        current_height += random() * 4 * (MAX_HEIGHT - MIN_HEIGHT) / HEIGHT_COUNT / 3 \
                          + (MAX_HEIGHT - MIN_HEIGHT) / HEIGHT_COUNT / 3
    heights.append(MAX_HEIGHT)

    sensors = []
    for i in range(len(lat)):
        if i == 0 or i == len(lat) - 1:
            sensors.append(heights)
        else:
            new_heights = []
            for j in range(len(heights)):
                if random() < 0.99:
                    new_heights.append(heights[j])
            sensors.append(new_heights)

    lat_diff = list(map(lambda x: x - START_LAT, lat))
    lon_diff = list(map(lambda x: x - START_LON, lon))

    lat_diff_meters = list(map(lambda x: x * METERS_PER_DEGREE_LAT, lat_diff))
    lon_diff_meters = list(map(lambda x: x * METERS_PER_DEGREE_LON, lon_diff))

    lengths = []
    for i in range(len(lat_diff_meters)):
        lengths.append((lat_diff_meters[i] ** 2 + lon_diff_meters[i] ** 2) ** (1 / 2))

    fig = go.Figure(go.Scattermapbox(
        mode="markers+lines",
        lat=lat,
        lon=lon,
        marker={'size': 10}
    ))

    fig.update_layout(
        margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
        mapbox={
            'center': {'lat': lat[len(lat) // 2], 'lon': lon[len(lon) // 2]},
            'style': "open-street-map",
            'zoom': 15
        }
    )

    fig.show()

    return lengths, sensors
