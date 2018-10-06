#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
from homie.helpers import isIdFormat
logger = logging.getLogger(__name__)

class HomieNodeProperty(object):
    """docstring for HomieNodeProp"""

    def setSubscribe(self, func):
        self.subscribe = func

    def __init__(self, node, propertyId):
        super(HomieNodeProperty, self).__init__()
        self.node = node  # stores ref to node
        self._propertyId = None
        self.propertyId = propertyId
        self.handler = None
        self._settable = False

    def settable(self, handler):
        self.handler = handler
        self.subscribe(self.node, self.propertyId, handler)
        self._settable = True

    def send(self, value):
        self.node.homie.publish(
            "/".join([
                self.node.homie.baseTopic,
                self.node.homie.deviceId,
                self.node.nodeId,
                self.propertyId,
            ]),
            value,
        )

    def representation(self):
        repr = self.propertyId
        if self._settable:
            repr += ":settable"
        return repr

    @property
    def propertyId(self):
        return self._propertyId

    @propertyId.setter
    def propertyId(self, propertyId):
        if isIdFormat(propertyId):
            self._propertyId = propertyId
        else:
            logger.warning("'{}' has no valid ID-Format".format(propertyId))


class HomieNodeRange(HomieNodeProperty):
    """docstring for HomieNodeRange"""

    def __init__(self, node, propertyId, lower, upper):
        super(HomieNodeRange, self).__init__(node, propertyId)
        self.node = node
        self._range = range(lower, upper + 1)
        self.range = None
        self.lower = lower
        self.upper = upper
        self.range_names = [(propertyId + "_" + str(x)) for x in self._range]

    def settable(self, handler):
        self.handler = handler
        for x in self._range:
            self.subscribe(self.node, "{}_{}".format(self.propertyId, x), handler)

    def setRange(self, lower, upper):
        # Todo: validate input
        if lower in self._range and upper in self._range:
            self.range = range(lower, upper + 1)
            return self
        else:
            logger.warning("Specified range out of announced range.")

    def send(self, value):
        if self.range is None:
            raise ValueError("Please specify a range.")

        for x in self.range:
            self.node.homie.publish(
                "/".join([
                    self.node.homie.baseTopic,
                    self.node.homie.deviceId,
                    self.node.nodeId,
                    self.propertyId + "_" + str(x),
                ]),
                value,
            )

    def representation(self):
        repr = "{}[{}-{}]".format(self.propertyId, self.lower, self.upper)
        if self._settable:
            repr += ":settable"
        return repr

