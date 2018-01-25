#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import json
import time
import signal
import socket
import atexit
import logging
import os.path
from os import getenv
from paho.mqtt.client import MQTTv311, MQTTv31
from homie.mqtt import HomieMqtt
from homie.timer import HomieTimer
from homie.node import HomieNode
from homie.helpers import isIdFormat, generateDeviceId
from homie.version import __version__ as HOMIE_PYTHON_VERSION
logger = logging.getLogger(__name__)

HOMIE_VERSION = "2.0.0"
DEFAULT_PREFS = {
    "CA_CERTS": {"key": "ca_certs", "val": None},
    "DEVICE_ID": {"key": "deviceId", "val": None},
    "DEVICE_NAME": {"key": "deviceName", "val": "xxxxxxxx"},
    "HOST": {"key": "host", "val": None},
    "KEEPALIVE": {"key": "keepalive", "val": 60},
    "PASSWORD": {"key": "password", "val": None},
    "PORT": {"key": "port", "val": 1883},
    "PROTOCOL": {"key": "protocol", "val": "MQTTv311"},
    "QOS": {"key": "qos", "val": 1},
    "SUBSCRIBE_ALL": {"key": "subscribe_all", "val": False},
    "TOPIC": {"key": "baseTopic", "val": "homie"},
    "USERNAME": {"key": "username", "val": None},
}


class Homie(object):
    """docstring for Homie"""

    def __init__(self, configFile):
        super(Homie, self).__init__()
        # define our exit-strategy
        atexit.register(self._exitus)
        signal.signal(signal.SIGTERM, self._sigTerm)
        signal.signal(signal.SIGHUP, self._sigHup)

        self.implementation_config = {}
        self._initAttrs(configFile)

        if not self.host:
            raise ValueError("No host specified.")

        self.statsUptime = time.time()    # $stats/uptime
        self.fwname = None
        self.fwversion = None
        self.nodes = []
        self.timers = []
        self.subscriptions = []
        self.subscribe_all_forced = False
        self.statsInterval = 60

        self.mqtt_topic = str("/".join([
            self.baseTopic,
            self.deviceId,
        ]))

        self._setupCalled = False       # call setup first
        self._mqtt_connected = False    # connected
        self._mqtt_subscribed = False   # subscribed

        clientId = "Homie-" + str(self.deviceId)
        try:
            self.mqtt = HomieMqtt(self, clientId, protocol=self.protocol)
        except Exception as e:
            raise e

    def Timer(self, *args, **kwargs):
        homieTimer = HomieTimer(*args, **kwargs)
        self.timers.append(homieTimer)
        return(homieTimer)

    def Node(self, *args):
        homeNode = HomieNode(self, *args)
        self.nodes.append(homeNode)
        return(homeNode)

    def _loadConfig(self, configFile):
        """ load configuration from configFile """
        config = {}
        configFile = os.path.realpath(configFile)
        try:
            fp = open(configFile)
        except EnvironmentError as e:
            logger.debug(e)
        else:
            try:
                config = json.load(fp)
            except Exception as e:
                raise e
            finally:
                fp.close()
        logger.debug("config: {}".format(config))
        return config

    def _initAttrs(self, configFile):
        """ Initialize homie attributes from env/config/defaults """

        # load configuration from configFile
        config = self._loadConfig(configFile)

        # iterate through DEFAULT_PREFS
        for pref in DEFAULT_PREFS:
            key = DEFAULT_PREFS[pref]['key']
            val = getenv(
                "HOMIE_" + pref,                # env
                config.get(
                    pref,                       # config
                    DEFAULT_PREFS[pref]['val']  # defaults
                )
            )

            if key == "protocol":
                if val == "MQTTv311":
                    val = MQTTv311
                elif val == "MQTTv31":
                    val = MQTTv31
                else:
                    raise ValueError("Invalid protocol")

            # set attr self.key = val
            setattr(self, key, val)
            logger.debug("{}: {}".format(key, getattr(self, key)))
            if val and key is not "password":
                self.implementation_config[key] = val

    def _checkBeforeSetup(self):
        """ checks whether setup() was called before """
        if self._setupCalled:
            raise BaseException(
                "✖ {}(): has to be called before setup()".format(
                    sys._getframe(1).f_code.co_name  # name of caller
                ))
        else:
            pass

    def _initialize(self):
        """ init and connect MQTT """
        # logger.debug("Initializing MQTT")
        self.mqtt.on_connect = self._connected
        self.mqtt.on_subscribe = self._subscribed
        self.mqtt.on_publish = self._published
        self.mqtt.on_disconnect = self._disconnected

        self.mqtt.will_set(
            self.mqtt_topic + "/$online", payload="false", retain=True)

        if self.username:
            self.mqtt.username_pw_set(self.username, password=self.password)

        if self.ca_certs:
            self.mqtt.tls_set(self.ca_certs)

        try:
            self.mqtt.connect(self.host, self.port, self.keepalive)
        except EnvironmentError as e:
            sleepSecs = 10
            logger.warning("{} - retrying in {} seconds.".format(e, sleepSecs))
            time.sleep(sleepSecs)
            self.mqtt.connect(self.host, self.port, self.keepalive)

        self.mqtt.loop_start()

    def _subscribe(self):
        logger.debug("Subscriptions: {}".format(self.subscriptions))
        if self.subscriptions:
            self.mqtt.subscribe(self.subscriptions)
            if self.subscribe_all_forced and not self.subscribe_all:
                self._unsubscribe()
        else:
            self.mqtt.subscribe(self.mqtt_topic + "/#", int(self.qos))
            self.subscribe_all_forced = True

    def _unsubscribe(self, topic=None):
        if not topic:
            topic = self.mqtt_topic + "/#"
        logger.debug("_unsubscribe: {}".format(topic))
        self.mqtt.unsubscribe(str(topic))

    def _connected(self, *args):
        # logger.debug("_connected: {}".format(args))
        self.mqtt_connected = True

        if not self.mqtt_subscribed:
            self._subscribe()

        self.publish(
            self.mqtt_topic + "/$online",
            payload="true", retain=True)
        self.publish(
            self.mqtt_topic + "/$name",
            payload=self.deviceName, retain=True)

        self.publishHomie()
        self.publishFwname()
        self.publishFwversion()
        self.publishNodes()
        self.publishLocalip()
        self.publishUptime()
        self.publishStatsInterval()
        self.publishSignal()
        self.publishImplementation()
        self.publishImplementationVersion()
        self.publishImplementationConfig()

    def _subscribed(self, *args):
        # logger.debug("_subscribed: {}".format(args))
        if not self.mqtt_subscribed:
            self.mqtt_subscribed = True

    def _published(self, *args):
        # logger.debug("_published: {}".format(args))
        pass

    def _disconnected(self, mqtt, obj, rc):
        self.mqtt_connected = False
        self.mqtt_subscribed = False

    def setup(self):
        """ set homie up """
        self._setupCalled = True

        # init and connect MQTT
        self._initialize()

        self.uptimeTimer = self.Timer(
            self.statsInterval, self.publishUptime, name="uptimeTimer")
        self.signalTimer = self.Timer(
            self.statsInterval, self.publishSignal, name="signalTimer")
        self.uptimeTimer.start()
        self.signalTimer.start()

    def setBroadcastHandler(self, callback, level="#", qos=None):
        """
        Homie defines a broadcast channel, so a controller
        is able to broadcast a message to every Homie devices
        """
        topic = "/".join([
            self.mqtt_topic,  # base topic + deviceId
            "$broadcast",
            level
        ])
        self.subscribeTopic(topic, callback, qos)

    def setFirmware(self, fwname, version):
        """docstring for setFirmware"""
        self._checkBeforeSetup()

        if not isIdFormat(fwname):
            raise ValueError("fwname needs to adhere idFormat")

        self.fwname = fwname
        self.fwversion = version
        logger.debug("{}: {}".format(self.fwname, self.fwversion))

    def setNodeProperty(self, homieNode, prop, val, retain=True):
        """ DEPRECATED """
        logger.warning("setNodeProperty() has been deprecated.")
        homieNode.setProperty(prop).send(val)

    def subscribe(self, homieNode, attr, callback, qos=None):
        """ Register new subscription and add a callback """
        topic = str("/".join([
            self.mqtt_topic,    # base topic + deviceId
            homieNode.nodeId,   # nodeId
            attr,               # propertyId
            "set"
        ]))
        self.subscribeTopic(topic, callback, qos)

    def subscribeProperty(self, homieNode, attr, callback, qos=None):
        """ Register new subscription for property and add a callback """
        topic = str("/".join([
            self.mqtt_topic,
            homieNode.nodeId,
            attr
        ]))
        self.subscribeTopic(topic, callback, qos)

    def subscribeTopic(self, topic, callback, qos=None):
        """  """
        self._checkBeforeSetup()

        # user qos prefs
        if qos is None:
            qos = int(self.qos)

        logger.debug("subscribe: {} {}".format(topic, qos))

        if not self.subscribe_all:
            self.subscriptions.append((topic, qos))

        if self.mqtt_connected:
            self._subscribe()

        self.mqtt.message_callback_add(topic, callback)

    def publish(self, topic, payload, retain=True, **kwargs):
        """ Publish messages to MQTT, if connected """
        if self.mqtt_connected:
            msgs = [
                topic,
                str(payload),
                str(retain)
            ]

            (result, mid) = self.mqtt.publish(
                topic,
                payload=payload,
                retain=retain,
                **kwargs)

            logger.debug(str(mid) + " > " + " ".join(msgs))
        else:
            logger.warn("Not connected.")

    def publishNodes(self):
        """ Publish registered nodes to MQTT """
        for node in self.nodes:
            logger.debug("$type: {}:{}".format(node.nodeId, node.nodeType))
            self.publish(
                "{}/{}/{}".format(
                    self.mqtt_topic,
                    node.nodeId,
                    "$type",
                ),
                payload=node.nodeType,
                retain=True
            )

            logger.debug("$properties: {}".format(node.getProperties()))
            self.publish(
                "{}/{}/{}".format(
                    self.mqtt_topic,
                    node.nodeId,
                    "$properties"
                ),
                payload=node.getProperties(),
                retain=True
            )

    def publishLocalip(self):
        """ Publish local IP Address to MQTT """
        payload = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((self.host, self.port))
        except Exception as e:
            logger.warn(e)
        else:
            payload = s.getsockname()[0]
            s.close()

        self.publish(
            self.mqtt_topic + "/$localip",
            payload=payload, retain=True)

    def publishUptime(self):
        """ Publish /$uptime/value to MQTT """
        payload = int(time.time() - self.statsUptime)
        self.publish(
            self.mqtt_topic + "/$stats/uptime",
            payload=payload, retain=True)

    def publishStatsInterval(self):
        """ Publish /$uptime/interval to MQTT """
        payload = self.statsInterval
        self.publish(
            self.mqtt_topic + "/$stats/interval",
            payload=payload, retain=True)

    def publishImplementation(self):
        """ Publish identifier for the Homie implementation to MQTT """
        payload = "python"
        self.publish(
            self.mqtt_topic + "/$implementation",
            payload=payload, retain=True)

    def publishImplementationVersion(self):
        """ Publish identifier for the Homie implementation to MQTT """
        payload = HOMIE_PYTHON_VERSION
        self.publish(
            self.mqtt_topic + "/$implementation/version",
            payload=payload, retain=True)

    def publishImplementationConfig(self):
        """ Publish configuration for the Homie implementation to MQTT """
        payload = json.dumps(self.implementation_config)
        self.publish(
            self.mqtt_topic + "/$implementation/config",
            payload=payload, retain=True)

    def publishHomie(self):
        """ Publish Version of the Homie convention the device conforms to """
        payload = HOMIE_VERSION
        self.publish(
            self.mqtt_topic + "/$homie",
            payload=payload, retain=True)

    def publishFwname(self):
        """ Publish fwname of the script to MQTT """
        payload = str(self.fwname)
        if self.fwname:
            self.publish(
                self.mqtt_topic + "/$fw/name",
                payload=payload, retain=True)

    def publishFwversion(self):
        """ Publish fwversion of the script to MQTT """
        payload = str(self.fwversion)
        if self.fwversion:
            self.publish(
                self.mqtt_topic + "/$fw/version",
                payload=payload, retain=True)

    def publishSignal(self):
        """ Publish current signal strength to MQTT """
        # default payload
        payload = None

        # found on linux
        wireless = "/proc/net/wireless"

        try:
            fp = open(wireless)
        except EnvironmentError as e:
            logger.debug(e)
        else:
            for i, line in enumerate(fp):
                if i == 2:
                    data = line.split()
                    payload = int(float(data[2]))
                elif i > 2:
                    break
            fp.close()

        # publish signal-strength when available
        if payload is not None:
            self.publish(
                self.mqtt_topic + "/$stats/signal",
                payload=payload, retain=True)

    @property
    def baseTopic(self):
        return self._baseTopic

    @baseTopic.setter
    def baseTopic(self, baseTopic):
        self._baseTopic = baseTopic

    @property
    def deviceId(self):
        return self._deviceId

    @deviceId.setter
    def deviceId(self, deviceId):
        if isIdFormat(deviceId):
            self._deviceId = deviceId
        else:
            self._deviceId = generateDeviceId()
            logger.warning(
                "Invalid deviceId specified. Using '{}' instead.".format(
                    self._deviceId))

    @property
    def mqtt_connected(self):
        return self._mqtt_connected

    @mqtt_connected.setter
    def mqtt_connected(self, state):
        logger.debug("connected: {}".format(state))
        self._mqtt_connected = state

    @property
    def mqtt_subscribed(self):
        return self._mqtt_subscribed

    @mqtt_subscribed.setter
    def mqtt_subscribed(self, state):
        logger.debug("subscribed: {}".format(state))
        self._mqtt_subscribed = state

    def _exitus(self):
        """ Clean up before exit """

        self.publish(
            self.mqtt_topic + "/$online",
            payload="false", retain=True)

        self.mqtt.loop_stop()
        self.mqtt.disconnect()

    def _sigTerm(self, signal, frame):
        """ let's do a quit, which atexit will notice """
        logger.debug("Received SIGTERM")
        raise SystemExit

    def _sigHup(self, signal, frame):
        """ let's do a quit, which atexit will notice """
        logger.debug("Received SIGHUP")
        raise SystemExit

    def __del__(self):
        logger.debug("Quitting.")


def main():
    pass


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
