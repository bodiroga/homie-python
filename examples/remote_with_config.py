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
    "DEVICE_ID": "remote-control",
    "DEVICE_NAME": "xxxxxxxx",
    "TOPIC": "homie"
}

device = homie.Device(config)
remoteNode = device.addNode("remote", "Remote", "Buttons")
playButtonProperty = remoteNode.addProperty("play", "Play Button", datatype="enum", format="PRESSED,RELEASED", retained=False)
nextButtonProperty = remoteNode.addProperty("next", "Next Button", datatype="enum", format="PRESSED,RELEASED", retained=False)
prevButtonProperty = remoteNode.addProperty("prev", "Prev Button", datatype="enum", format="PRESSED,RELEASED", retained=False)


def main():
    device.setFirmware("remote-control", "1.0.0")

    device.setup()

    buttonPressFrecuency = 30
    lastButtonPressTime = 0

    while True:
        # We simulate that the button is pressed (and released) every 30 seconds
        if (time.time() - lastButtonPressTime) > buttonPressFrecuency:
            playButtonProperty.update("PRESSED")
            time.sleep(0.3)
            playButtonProperty.update("RELEASED")
            logger.info("Play button pressed and released")
            lastButtonPressTime = time.time()
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Quitting.")