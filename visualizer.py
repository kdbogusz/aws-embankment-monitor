

# Define Variables
import threading

import paho.mqtt.client as mqtt
import ssl
from time import sleep
import struct
import matplotlib
import numpy as np
from numpy.random import normal
from random import uniform
import matplotlib.pyplot as plt

MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 100

MQTT_HOST = "a3r21ql3ppgl2q-ats.iot.us-east-2.amazonaws.com"
#Konrad config
CA_ROOT_CERT_FILE = "C:/Users/nuttard/Desktop/AAA/root-CA.crt"
THING_CERT_FILE = "C:/Users/nuttard/Desktop/AAA/embankment-monitor.cert.pem"
THING_PRIVATE_KEY = "C:/Users/nuttard/Desktop/AAA/embankment-monitor.private.key"

#Bartek config
#CA_ROOT_CERT_FILE = "C:/Users/DP/Desktop/aws-embankment-monitor/aws-stuff-2/root-CA.crt"
#THING_CERT_FILE = "C:/Users/DP/Desktop/aws-embankment-monitor/aws-stuff-2/embankment-monitor.cert.pem"
#THING_PRIVATE_KEY = "C:/Users/DP/Desktop/aws-embankment-monitor/aws-stuff-2/embankment-monitor.private.key"
SPREAD = 0.02  # 0.02
LENGTH = 1000  # 1000
LENGTH_BETWEEN = 5  # 5
HEIGHT = 5  # 5
HEIGHT_BETWEEN = 1  # 1
DELAY = 20  # 20s
BREAK_WIDTH = 80  # 80m (left side + right side)

DATA_LEFT = [[-1]*int(LENGTH//LENGTH_BETWEEN) for i in range(int(HEIGHT//HEIGHT_BETWEEN))]
DATA_RIGHT = [[-1]*int(LENGTH//LENGTH_BETWEEN) for j in range(int(HEIGHT//HEIGHT_BETWEEN))]


def draw(side):
    data = DATA_RIGHT if side == "Right Embankment" else DATA_LEFT
    plt.imshow(data, extent=[0, 995, 0, 400], cmap=matplotlib.cm.autumn_r)
    plt.gca().invert_yaxis()
    plt.title = side
    plt.show()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    mqttc.subscribe("/monitoring/#")


def on_message(client, userdata, msg):
    side, i, j = msg.topic.split("/")[2:]
    temperature = float(msg.payload.decode("utf-8"))
    if side == "left":
        DATA_LEFT[int(i)][int(int(j)//LENGTH_BETWEEN)] = temperature
    else:
        DATA_RIGHT[int(i)][int(int(j)//LENGTH_BETWEEN)] = temperature


mqttc = mqtt.Client()
mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.loop_start()

while True:
    sleep(DELAY)
    draw("Left Embankment")
    draw("Right Embankment")
