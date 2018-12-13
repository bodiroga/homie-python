#!/usr/bin/env python
import time
import random
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
thermostatNode = device.addNode("thermostat", "Thermostat", "thermostat")
temperatureProperty = thermostatNode.addProperty("temperature", "Indoor Temperature", "ºC", "float", "0:50")
setpointProperty = thermostatNode.addProperty("setpoint", "Setpoint", "ºC", "float", "10:30")
modeProperty = thermostatNode.addProperty("mode", "Thermostat Mode", datatype="enum", format="NORMAL,COLD,HEAT")

def modeHandler(property, value):
    logger.info("Changing thermostat mode to {}".format(value))
    property.update(value)

def setpointHandler(property, value):
    logger.info("Changing thermostat setpoint to {}ºC".format(value))
    property.update(value)


def main():
    device.setFirmware("thermostat", "1.0.0")
    modeProperty.settable(modeHandler)
    setpointProperty.settable(setpointHandler)

    device.setup()

    reportFrecuency = 60
    lastTemperatureTime = 0

    setpointProperty.update(21.5)
    modeProperty.update("NORMAL")
    while True:
        if (time.time() - lastTemperatureTime) > reportFrecuency:
            temperature = random.uniform(20,25)
            temperatureProperty.update("{0:.2f}".format(temperature))
            logger.info("New temperature value: {0:.2f}ºC".format(temperature))
            lastTemperatureTime = time.time()
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")
