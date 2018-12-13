#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
from homie.helpers import isValidId, isValidDatatype, isValidFormat, isValidUnit
logger = logging.getLogger(__name__)

class HomieNodeProperty(object):
    """docstring for HomieNodeProp"""

    def setSubscribe(self, func):
        self.subscribe = func

    def __init__(self, node, id, name=None, unit=None, datatype=None, format=None, retained=True):
        super(HomieNodeProperty, self).__init__()
        self.node = node  # stores ref to node
        self._id = None
        self._propertyName = None
        self._propertyUnit = None
        self._propertyDatatype = None
        self._propertyFormat = None
        self._retained = True
        self.id = id
        self.propertyName = name
        self.propertyUnit = unit
        self.propertyDatatype = datatype
        self.propertyFormat = format
        self.retained = retained
        self.handler = None
        self._settable = False

    def settable(self, handler):
        self.handler = handler
        self.subscribe(self.node, self.id, handler)
        self._settable = True

    def update(self, value):
        self.node.homie.publish(
            "/".join([
                self.node.homie.baseTopic,
                self.node.homie.deviceId,
                self.node.nodeId,
                self.id,
            ]),
            value,
            self._retained
        )

    def representation(self):
        return self.id

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
        if self._propertyName:
            self.publishAttribute("name", self._propertyName)
        if self._settable:
            self.publishAttribute("settable", str(self._settable).lower())
        if self._propertyUnit:
            self.publishAttribute("unit", self._propertyUnit)
        if self._propertyDatatype:
            self.publishAttribute("datatype", self._propertyDatatype)
        if self._propertyFormat:
            self.publishAttribute("format", self._propertyFormat)
        if not self._retained:
            self.publishAttribute("retained", str(self._retained).lower())

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        if isValidId(id):
            self._id = id
        else:
            raise ValueError("'{}' is not a valid ID for a property".format(id))

    @property
    def propertyName(self):
        return self._propertyName

    @propertyName.setter
    def propertyName(self, name):
        self._propertyName = name

    @property
    def propertyUnit(self):
        return self._propertyUnit

    @propertyUnit.setter
    def propertyUnit(self, unit):
        if unit:
            if isValidUnit(unit):
                self._propertyUnit = unit
            else:
                logger.warning("'{}' is not a valid unit".format(unit))

    @property
    def propertyDatatype(self):
        return self._propertyDatatype

    @propertyDatatype.setter
    def propertyDatatype(self, datatype):
        if datatype:
            if isValidDatatype(datatype):
                self._propertyDatatype = datatype
            else:
                logger.warning("'{}' is not a valid datatype".format(datatype))

    @property
    def propertyFormat(self):
        return self._propertyFormat

    @propertyFormat.setter
    def propertyFormat(self, format):
        if format or self._propertyDatatype:
            if isValidFormat(self._propertyDatatype, format):
                self._propertyFormat = format 
            else:
                logger.warning("'{}' is not a valid format for {}".format(format, self._propertyDatatype))

    @property
    def retained(self):
        return self._retained

    @retained.setter
    def retained(self, retained):
        self._retained = retained

class HomieNodePropertyRange(HomieNodeProperty):
    """docstring for HomieNodeRange"""

    def __init__(self, node, id, lower, upper, name=None, unit=None, datatype=None, format=None, retained=True):
        super(HomieNodePropertyRange, self).__init__(node, id, name, unit, datatype, format, retained)
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
        return repr

