import paho.mqtt.client as mqtt
from time import sleep

import pyodbc
from numpy.random import normal
from random import uniform

SPREAD = 0.01  # 0.02
LENGTH = 1000  # 1000
LENGTH_BETWEEN = 5  # 5
HEIGHT = 5  # 5
HEIGHT_BETWEEN = 1  # 1
DELAY = 0.01  # 0.01s
BREAK_WIDTH = 200  # 200m (left side + right side)

MQTT_KEEPALIVE_INTERVAL = 45
MQTT_HOST = "localhost"
MQTT_PORT = 1883

SQL_CONNECTION_STRING = 'DRIVER={SQL SERVER};Server=localhost\SQLEXPRESS;Database=master;Trusted_Connection=True;'


def generate_random_temperature(this_height):
    return normal(14, 10 * SPREAD) - this_height


def generate_temperature_difference():
    diff = 0
    for meter in range(LENGTH_BETWEEN // 1):
        diff += uniform(-SPREAD, SPREAD)
    diff += (LENGTH_BETWEEN - LENGTH_BETWEEN // 1) * uniform(-SPREAD, SPREAD)
    return diff


def generate_single_value(this_height, last_value):
    if last_value is None:
        return generate_random_temperature(this_height)
    else:
        diff = generate_temperature_difference()
        return last_value + diff


class Sensor:
    def __init__(self, height, neighbour_temperature):
        self.model = ""
        self.temperature = generate_single_value(height, neighbour_temperature)


class Sector:
    def __init__(self, embankment, length, heights, last_temperatures, sql_cursor):
        self.embankment = embankment
        self.length = length
        self.heights = []  # tuple (height, Sensor)
        for height in heights:
            last_value = None
            if last_temperatures is not None:
                for previous in last_temperatures:
                    if previous[0] == height:
                        last_value = previous[1]
                        break
            self.heights.append((height, Sensor(height, last_value)))
        self.id = None
        self.register_to_database(sql_cursor)

    def register_to_database(self, sql_cursor):
        sql_cursor.execute("insert into Sector (length, embankment) values (?, ?)", (float(self.length), self.embankment))
        sql_cursor.execute('select sectorID from Sector where length = ? and embankment = ?', (float(self.length), self.embankment))
        for row in sql_cursor:
            self.id = row[0]
            break
        for height in self.heights:
            sql_cursor.execute("insert into Sensor (sectorID, height) values (?, ?)", (self.id, float(height[0])))

    def update_temperatures(self, left_temperatures, right_temperatures):
        for height in self.heights:
            average = 10 * height[1].temperature
            average_count = 10
            if left_temperatures is not None:
                for temperature in left_temperatures:
                    if temperature[0] == height[0]:
                        average += temperature[1]
                        average_count += 1
                        break
            if right_temperatures is not None:
                for temperature in right_temperatures:
                    if temperature[0] == height[0]:
                        average += temperature[1]
                        average_count += 1
                        break
            average /= average_count
            height[1].temperature = average + generate_temperature_difference()

    def get_temperatures(self):
        temperatures = []
        for height in self.heights:
            temperatures.append((height[0], height[1].temperature))
        return temperatures

    def send_temperature(self, left_temperatures, right_temperatures, mqttc):
        self.update_temperatures(left_temperatures, right_temperatures)
        temperatures = self.get_temperatures()
        for temperature in temperatures:
            mqtt_send(self.id, temperature[0], temperature[1], mqttc)

    def break_wall(self, center, break_strength):
        for height in range(len(self.heights)):
            if self.heights[height][0] < HEIGHT - 1 and 1 - (2 * (abs(center - self.length)) / BREAK_WIDTH) > 0:
                self.heights[height][1].temperature += min(1, break_strength * (
                            1 - (2 * (abs(center - self.length)) / BREAK_WIDTH)) ** 2) * \
                                        (self.heights[height + 1][1].temperature - self.heights[height][1].temperature)


def program_loop(break_time, break_place, sectors, mqttc):
    current_time = 0
    while True:
        break_strength = (current_time - break_time) / 10
        if break_strength <= 0.0:
            break_strength = 0.0
        elif break_strength > 0.8:
            break_strength = 0.03
        else:
            break_strength = 0.1

        for sector in sectors:
            sector.break_wall(break_place, break_strength)

        # update + send temperatures
        for sector_index in range(len(sectors)):
            this_sector = sectors[sector_index]
            left_temperatures = None
            right_temperatures = None
            if sector_index > 0:
                left_sector = sectors[sector_index - 1]
                left_temperatures = left_sector.get_temperatures()
            if sector_index < len(sectors) - 1:
                right_sector = sectors[sector_index + 1]
                right_temperatures = right_sector.get_temperatures()
            this_sector.send_temperature(left_temperatures, right_temperatures, mqttc)

        current_time += 1


def create_primary_embankment(sql_cursor):
    lengths = [x * LENGTH_BETWEEN for x in range(0, LENGTH // LENGTH_BETWEEN)]
    heights = [x * HEIGHT_BETWEEN for x in range(0, HEIGHT // HEIGHT_BETWEEN)]
    sectors = []
    last_temperatures = None
    for length in lengths:
        if length == 800.0:
            new_sector = Sector("Primary Embankment", length, heights[1:], last_temperatures, sql_cursor)
            sectors.append(new_sector)
            last_temperatures = new_sector.get_temperatures()
            new_sector = Sector("Primary Embankment", 803.0, heights, last_temperatures, sql_cursor)
            sectors.append(new_sector)
            last_temperatures = new_sector.get_temperatures()
        else:
            new_sector = Sector("Primary Embankment", length, heights, last_temperatures, sql_cursor)
            sectors.append(new_sector)
            last_temperatures = new_sector.get_temperatures()
    return sectors


def mqtt_init():
    mqttc = mqtt.Client()
    mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
    mqttc.loop_start()
    return mqttc


def mqtt_send(sensor_id, height, temperature, mqttc):
    topic = "/monitoring/" + str(sensor_id) + "/" + str(height)
    mqttc.publish(topic, temperature, qos=0)
    print(topic)
    sleep(DELAY)


def sql_connect():
    conn = pyodbc.connect(SQL_CONNECTION_STRING)
    return conn.cursor()


def sql_create_database(sql_cursor):
    sql_cursor.execute('drop table Sensor')
    sql_cursor.execute('drop table Sector')
    sql_cursor.execute("create table Sector ( sectorID int not null identity(1,1), embankment varchar(50) not null, length decimal(30, 20) not null, constraint Sector_pk primary key (sectorID));")
    sql_cursor.execute("create table Sensor ( sectorID int not null, height decimal(30, 20) not null, constraint Sensor_pk primary key (sectorID, height));")
    sql_cursor.execute("ALTER TABLE Sensor ADD CONSTRAINT Sensor_fk FOREIGN KEY (sectorID) REFERENCES Sector (sectorID);")


client = mqtt_init()
cursor = sql_connect()
sql_create_database(cursor)
primary_embankment = create_primary_embankment(cursor)
cursor.commit()
cursor.close()
program_loop(1, 400, primary_embankment, client)
