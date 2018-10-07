#!/usr/bin/env python
import time
import homie
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = {
    "HOST": "iot.eclipse.org",
    "PORT": 1883,
    "KEEPALIVE": 10,
    "USERNAME": "",
    "PASSWORD": "",
    "CA_CERTS": "",
    "DEVICE_ID": "xxxxxxxx",
    "DEVICE_NAME": "xxxxxxxx",
    "TOPIC": "homie"
}

device = homie.Device(config)
switchNode = device.addNode("switch", "switch", "switch")
switchProperty = switchNode.addProperty("on")

def switchOnHandler(property, value):
    if value == 'true':
        logger.info("Switch: ON")
        property.update("true")
    else:
        logger.info("Switch: OFF")
        property.update("false")


def main():
    device.setFirmware("relay-switch", "1.0.0")
    switchProperty.settable(switchOnHandler)
    device.setup()

    while True:
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")
