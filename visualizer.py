from datetime import datetime

import paho.mqtt.client as mqtt
from time import sleep
import matplotlib
import matplotlib.pyplot as plt
import pyodbc

MQTT_KEEPALIVE_INTERVAL = 45
MQTT_HOST = "localhost"
MQTT_PORT = 1883

SQL_CONNECTION_STRING = 'DRIVER={SQL SERVER};Server=localhost\SQLEXPRESS;Database=master;Trusted_Connection=True;'

DELAY = 30  # 20s
EMBANKMENT_NAME = "Primary Embankment"
SCALE = 10  # how many pixels per meter of height for one pixel per meter of length


def set_data(sql_cursor):
    heights = []
    sql_cursor.execute("select distinct height from Sensor order by height")
    for row in sql_cursor:
        heights.append(float(row[0]))
    lengths = []
    sql_cursor.execute("select distinct length from Sector where embankment = ? order by length", EMBANKMENT_NAME)
    for row in sql_cursor:
        lengths.append(float(row[0]))
    data = [[-1] * len(lengths) for height in range(len(heights))]
    return lengths, heights, data


def draw(lengths, heights, data):
    data_copy = fill_gaps(lengths, data)
    check_for_breaks(lengths, data)
    plt.imshow(data_copy, extent=[min(lengths), max(lengths), min(heights) * SCALE, max(heights) * SCALE], cmap=matplotlib.cm.autumn_r)
    plt.gca().invert_yaxis()
    plt.title = EMBANKMENT_NAME
    plt.show()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    mqttc.subscribe("/monitoring/#")


def on_message(client, userdata, msg):
    sector_id, height = msg.topic.split("/")[2:]
    temperature = float(msg.payload.decode("utf-8"))
    cursor.execute("select distinct length from Sector where sectorID = ?", sector_id)
    length = float(-1.0)
    for row in cursor:
        length = float(row[0])
    array[ys.index(float(height))][xs.index(length)] = temperature


def check_for_breaks(lengths, data):
    new_data = fill_gaps(lengths, data)

    potential_length_indices = []
    for height_index in range(len(new_data)):
        average = sum(new_data[height_index]) / len(new_data[height_index])
        for length_index in range(len(new_data[0])):
            if new_data[height_index][length_index] < average - 1:
                if length_index not in potential_length_indices:
                    potential_length_indices.append(length_index)

    potential_length_indices.sort()
    potential_break_indices = []
    i = -1
    last_index = -2
    for length_index in potential_length_indices:
        if length_index != last_index + 1:
            i += 1
            potential_break_indices.append([])
        potential_break_indices[i].append(length_index)
        last_index = length_index

    for break_list in potential_break_indices:
        first = lengths[break_list[0]]
        last = lengths[break_list[len(break_list) - 1]]
        if first == last:
            print("[" + str(datetime.now()) + "] Potential break around " + str(first))
        else:
            print("[" + str(datetime.now()) + "] Potential break between " + str(first) + " and " + str(last))


def fill_gaps(lengths, data):
    new_data = data.copy()
    for height_index in range(len(new_data)):
        this_index = -1
        go_back = False
        for length_index in range(len(new_data[0])):
            if new_data[height_index][length_index] != -1:
                last_index = this_index
                this_index = length_index
                if go_back:
                    for empty_index in range(last_index + 1, this_index):
                        last_length = lengths[last_index]
                        this_length = lengths[this_index]
                        empty_length = lengths[empty_index]
                        last_temperature = new_data[height_index][last_index]
                        this_temperature = new_data[height_index][this_index]
                        empty_temperature = last_temperature + (this_temperature - last_temperature) * \
                            (empty_length - last_length) / (this_length - last_length)
                        new_data[height_index][empty_index] = empty_temperature
            else:
                go_back = True
    return new_data


def sql_connect():
    conn = pyodbc.connect(SQL_CONNECTION_STRING)
    return conn.cursor()


cursor = sql_connect()
xs, ys, array = set_data(cursor)

mqttc = mqtt.Client()
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
sleep(DELAY * 4)
mqttc.loop_start()


while True:
    sleep(DELAY)
    draw(xs, ys, array)
