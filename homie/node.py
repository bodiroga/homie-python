#!/usr/bin/env python
import logging
from homie.helpers import isIdFormat
from homie.property import HomieNodeProperty
from homie.property import HomieNodePropertyRange
logger = logging.getLogger(__name__)

class HomieNode(object):
    """docstring for HomieNode"""

    def __init__(self, homie, nodeId, nodeType):
        super(HomieNode, self).__init__()
        self.homie = homie
        self.nodeId = nodeId
        self.nodeType = nodeType
        self.properties = {}

    def addProperty(self, id=None, name=None, unit=None, datatype=None, format=None):
        if not id:
            logger.error("'id' required for HomieNodeProperty")
            return
        if id not in self.properties:
            homieNodeProperty = HomieNodeProperty(id, name, unit, datatype, format)
            homieNodeProperty.setSubscribe(self.homie.subscribe)
            if homieNodeProperty:
                self.properties[id] = homieNodeProperty
            return homieNodeProperty
        else:
            logger.warning("Property '{}' already created.".format(id))
            return self.properties[id]

    def addPropertyRange(self, id=None, lower=None, upper=None, name=None, unit=None, datatype=None, format=None):
        if not id:
            logger.error("'id' value required for HomieNodePropertyRange")
            return
        if not lower or not upper:
            logger.error("'lower' and 'upper' values required for HomieNodePropertyRange")
            return
        if id not in self.properties:
            homieNodePropertyRange = HomieNodePropertyRange(id, lower, upper, name, unit, datatype, format)
            homieNodePropertyRange.setSubscribe(self.homie.subscribe)
            if homieNodePropertyRange:
                self.properties[id] = homieNodePropertyRange
            return homieNodePropertyRange
        else:
            logger.warning("PropertyRange '{}' alread created.".format(id))
            return self.properties[id]

    def getProperty(self, propertyId):
        if propertyId not in self.properties:
            raise ValueError("Property '{}' does not exist".format(propertyId))
        return self.properties[propertyId]

    def sendProperties(self):
        nodeTopic = "/".join([self.homie.baseTopic, self.homie.deviceId, self.nodeId])

        self.homie.publish(nodeTopic + "/$type", self.nodeType)

        payload = ",".join([property.representation() for id, property in self.properties.items()])
        self.homie.publish(nodeTopic + "/$properties", payload)

        for nodeProperty in self.properties.items():
            nodeProperty.publishAttributes()

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
