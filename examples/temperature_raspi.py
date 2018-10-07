#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
import homie
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPERATURE_INTERVAL = 60

config = homie.loadConfigFile("homie-python.json")
device = homie.Device(config)
temperatureNode = device.addNode("temperature", "temperature", "temperature")
temperatureProperty = temperatureNode.addProperty("temperature", "Temperature value", "ºC", "float")


def getCpuTemperature():
    tempFile = open("/sys/class/thermal/thermal_zone0/temp")
    cpu_temp = tempFile.read()
    tempFile.close()
    return (float(cpu_temp) / 1000)


def main():
    device.setFirmware("raspi-temperature", "1.0.0")

    device.setup()

    while True:
        temperature = getCpuTemperature()
        logger.info("Temperature: {:0.2f} °C".format(temperature))
        temperatureProperty.update(temperature)
        time.sleep(TEMPERATURE_INTERVAL)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")
