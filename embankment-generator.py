import paho.mqtt.client as mqtt
import ssl
from time import sleep
import matplotlib
from numpy.random import normal
from random import uniform
import matplotlib.pyplot as plt

SPREAD = 0.02  # 0.02
LENGTH = 100  # 1000
LENGTH_BETWEEN = 10  # 5
HEIGHT = 5  # 5
HEIGHT_BETWEEN = 1  # 1
DELAY = 5  # 1s
BREAK_WIDTH = 20  # 80m (left side + right side)

MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_HOST = "a3r21ql3ppgl2q-ats.iot.us-east-2.amazonaws.com"
CA_ROOT_CERT_FILE = "C:/Users/nuttard/Desktop/AAA/root-CA.crt"
THING_CERT_FILE = "C:/Users/nuttard/Desktop/AAA/embankment-monitor.cert.pem"
THING_PRIVATE_KEY = "C:/Users/nuttard/Desktop/AAA/embankment-monitor.private.key"


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


def generate_single_height(this_height):
    current_length = 0
    last_value = None
    values = []
    while current_length < LENGTH:
        last_value = generate_single_value(this_height, last_value)
        values.append(last_value)
        current_length += LENGTH_BETWEEN
    return values


def generate_data():
    current_height = 0
    values = []
    while current_height < HEIGHT:
        values.append(generate_single_height(current_height))
        current_height += HEIGHT_BETWEEN
    return values


def update_data(data):
    for i in range(len(data)):
        for j in range(len(data[0])):
            average = data[i][j] * 10
            average_count = 10
            if j > 0:
                if abs(data[i][j - 1] - data[i][j]) < 0.3:
                    average += data[i][j - 1]
                    average_count += 1
            if j < len(data[0]) - 1:
                if abs(data[i][j + 1] - data[i][j]) < 0.3:
                    average += data[i][j + 1]
                    average_count += 1
            data[i][j] = average / average_count + generate_temperature_difference()


def break_wall(data, center, break_strength):
    for height in range(len(data)):
        for length in range(len(data[0])):
            current_length = length * LENGTH_BETWEEN
            if height < HEIGHT - 1 and 1 - (2 * (abs(center - current_length)) / BREAK_WIDTH) > 0:
                data[height][length] += min(1, break_strength * (1 - (2 * (abs(center - current_length)) / BREAK_WIDTH)) ** 2) * \
                                        (data[height + 1][length] - data[height][length])


def program_loop(break_time, break_place, break_side, mqttc):
    sensor_readings_1 = generate_data()
    sensor_readings_2 = generate_data()
    current_time = 0
    while True:
        break_strength = (current_time - break_time) / 10
        if break_strength <= 0.0:
            break_strength = 0.0
        elif break_strength > 0.8:
            break_strength = 0.03
        else:
            break_strength = 0.1
        if break_side == 'left':
            break_wall(sensor_readings_1, break_place, break_strength)
        else:
            break_wall(sensor_readings_2, break_place, break_strength)
        update_data(sensor_readings_1)
        update_data(sensor_readings_2)
        current_time += 1
        mqtt_send("left", sensor_readings_1, mqttc)
        mqtt_send("right", sensor_readings_2, mqttc)
        # plt.imshow(sensor_readings_1, extent=[0, 995, 0, 400], cmap=matplotlib.cm.autumn_r)
        # plt.gca().invert_yaxis()
        # plt.show()
        sleep(DELAY)


def mqtt_init():
    mqttc = mqtt.Client()
    mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
    mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
    mqttc.loop_start()
    return mqttc


def mqtt_send(side, data, mqttc):
    topic_layer_1 = "/monitoring/" + side
    for i in range(len(data)):
        topic_layer_2 = topic_layer_1 + "/" + str(i * HEIGHT_BETWEEN)
        for j in range(len(data[0])):
            topic_layer_3 = topic_layer_2 + "/" + str(j * LENGTH_BETWEEN)
            mqttc.publish(topic_layer_3, str(data[i][j]), qos=0)
            print(topic_layer_3)


program_loop(3, 50, "left", mqtt_init())
