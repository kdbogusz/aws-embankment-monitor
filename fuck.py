import paho.mqtt.client as mqtt
import ssl

MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = "/test/python"
MQTT_MSG = "aaaaaaa"

MQTT_HOST = "a3r21ql3ppgl2q-ats.iot.us-east-2.amazonaws.com"
CA_ROOT_CERT_FILE = "C:/Users/nuttard/Desktop/AAA/root-CA.crt"
THING_CERT_FILE = "C:/Users/nuttard/Desktop/AAA/embankment-monitor.cert.pem"
THING_PRIVATE_KEY = "C:/Users/nuttard/Desktop/AAA/embankment-monitor.private.key"


def on_connect(mosq, obj, rc, a):
    mqttc.subscribe(MQTT_TOPIC, 0)


def on_message(mosq, obj, msg):
    print("Topic: " + str(msg.topic))
    print("QoS: " + str(msg.qos))
    print("Payload: " + str(msg.payload))


def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed to Topic: " +
    MQTT_MSG + " with QoS: " + str(granted_qos))


mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)


# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)


# Continue monitoring the incoming messages for subscribed topic
mqttc.loop_forever()