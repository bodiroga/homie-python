#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
from homie.helpers import isIdFormat
logger = logging.getLogger(__name__)

class HomieNodeProperty(object):
    """docstring for HomieNodeProp"""

    def setSubscribe(self, func):
        self.subscribe = func

    def __init__(self, node, id, name=None, unit=None, datatype=None, format=None):
        super(HomieNodeProperty, self).__init__()
        self.node = node  # stores ref to node
        self._id = None
        self.id = id
        self.propertyName = name
        self.propertyUnit = unit
        self.propertyDatatype = datatype
        self.propertyFormat = format
        self.handler = None
        self._settable = False

    def settable(self, handler):
        self.handler = handler
        self.subscribe(self.node, self.id, handler)
        self._settable = True

    def send(self, value):
        self.node.homie.publish(
            "/".join([
                self.node.homie.baseTopic,
                self.node.homie.deviceId,
                self.node.nodeId,
                self.id,
            ]),
            value,
        )

    def representation(self):
        repr = self.id
        if self._settable:
            repr += ":settable"
        return repr

    def publishAttribute(self, name, value):
        self.node.homie.publish(
            "/".join([
                self.node.homie.baseTopic,
                self.node.homie.deviceId,
                self.node.nodeId,
                self.id,
                "${}".format(name)
            ]),
            value,
        )

    def publishAttributes(self):
        if self.propertyName:
            self.publishAttribute("name", self.propertyName)
        if self._settable:
            self.publishAttribute("settable", self._settable)
        if self.propertyUnit:
            self.publishAttribute("unit", self.propertyUnit)
        if self.propertyDatatype:
            self.publishAttribute("datatype", self.propertyDatatype)
        if self.propertyFormat:
            self.publishAttribute("format", self.propertyFormat)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        if isIdFormat(id):
            self._id = id
        else:
            logger.warning("'{}' has no valid ID-Format".format(id))

    @property
    def propertyName(self):
        return self.propertyName

    @propertyName.setter
    def propertyName(self, propertyName):
        self.propertyName = propertyName

    @property
    def propertyUnit(self):
        return self.propertyUnit

    @propertyUnit.setter
    def propertyUnit(self, propertyUnit):
        self.propertyUnit = propertyUnit

    @property
    def propertyDatatype(self):
        return self.propertyDatatype

    @propertyDatatype.setter
    def propertyDatatype(self, propertyDatatype):
        self.propertyDatatype = property

    @property
    def propertyFormat(self):
        return self.propertyFormat

    @propertyFormat.setter
    def propertyFormat(self, propertyFormat):
        self.propertyFormat = propertyFormat 


class HomieNodePropertyRange(HomieNodeProperty):
    """docstring for HomieNodeRange"""

    def __init__(self, node, id, lower, upper, name=None, unit=None, datatype=None, format=None):
        super(HomieNodePropertyRange, self).__init__(node, id, name, unit, datatype, format)
        self.node = node
        self._range = range(lower, upper + 1)
        self.range = None
        self.lower = lower
        self.upper = upper
        self.range_names = [(id + "_" + str(x)) for x in self._range]

    def settable(self, handler):
        self.handler = handler
        for x in self._range:
            self.subscribe(self.node, "{}_{}".format(self.id, x), handler)

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
                    self.id + "_" + str(x),
                ]),
                value,
            )

    def representation(self):
        repr = "{}[{}-{}]".format(self.id, self.lower, self.upper)
        if self._settable:
            repr += ":settable"
        return repr

