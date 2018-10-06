#!/usr/bin/env python
import logging
from homie.helpers import isIdFormat
from homie.property import HomieNodeProperty
from homie.property import HomieNodeRange
logger = logging.getLogger(__name__)

class HomieNode(object):
    """docstring for HomieNode"""

    def __init__(self, homie, nodeId, nodeType):
        super(HomieNode, self).__init__()
        self.homie = homie
        self.nodeId = nodeId
        self.nodeType = nodeType
        self.properties = {}

    def advertise(self, propertyId):
        if propertyId not in self.properties:
            homieNodeProperty = HomieNodeProperty(self, propertyId)
            homieNodeProperty.setSubscribe(self.homie.subscribe)
            if homieNodeProperty:
                self.properties[propertyId] = homieNodeProperty
                return(homieNodeProperty)
        else:
            logger.warning("Property '{}' already announced.".format(propertyId))

    def advertiseRange(self, propertyId, lower, upper):
        if propertyId not in self.properties:
            homieNodeRange = HomieNodeRange(self, propertyId, lower, upper)
            homieNodeRange.setSubscribe(self.homie.subscribe)
            if homieNodeRange:
                self.properties[propertyId] = homieNodeRange
                return(homieNodeRange)
        else:
            logger.warning("Property '{}' already announced.".format(propertyId))

    def setProperty(self, propertyId):
        if propertyId not in self.properties:
            raise ValueError("Property '{}' does not exist".format(propertyId))
        return self.properties[propertyId]

    def sendProperties(self):
        nodeTopic = "/".join([self.homie.baseTopic, self.homie.deviceId, self.nodeId])

        self.homie.publish(nodeTopic + "/$type", self.nodeType)

        payload = ",".join([property.representation() for id, property in self.properties.items()])
        self.homie.publish(nodeTopic + "/$properties", payload)

    @property
    def nodeId(self):
        return self._nodeId

    @nodeId.setter
    def nodeId(self, nodeId):
        self._nodeId = nodeId

    @property
    def nodeType(self):
        return self._nodeType

    @nodeType.setter
    def nodeType(self, nodeType):
        self._nodeType = nodeType


def main():
    pass


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
