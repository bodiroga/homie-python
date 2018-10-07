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
humidityNode = device.addNode("humidity", "humidity", "humidity")
temperatureProperty = temperatureNode.addProperty("temperature", "Temperature value", "ºC", "float")
humidityProperty = humidityNode.addProperty("humidity", "Humidity value", "%", "float", "0.0:100.0")


def main():
    device.setFirmware("awesome-temperature", "1.0.0")

    device.setup()

    while True:
        temperature = 22.0
        humidity = 60.0

        logger.info("Temperature: {:0.2f} °C".format(temperature))
        temperatureProperty.update(temperature)

        logger.info("Humidity: {:0.2f} %".format(humidity))
        humidityProperty.update(humidity)

        time.sleep(TEMPERATURE_INTERVAL)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")
