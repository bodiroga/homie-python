#!/usr/bin/env python
"""Provide helper functions."""
import re
import logging
from uuid import getnode as get_mac

logger = logging.getLogger(__name__)


def generateDeviceId():
    """Generate device Id."""
    logger.debug("generateDeviceId")
    return "{:02x}".format(get_mac())


def isValidId(idString):
    """Validate device Id."""
    logger.debug("isIdFormat")
    if isinstance(idString, str):
        r = re.compile('(^(?!\-)[a-z0-9\-]+(?<!\-)$)')
        return True if r.match(idString) else False

def isValidDatatype(datatype):
    """Validate datatype"""
    valid_datatypes = ("integer", "float", "boolean", "string", "enum", "color")
    if datatype in valid_datatypes:
        return True
    return False

def isValidFormat(datatype, format):
    """Validate format"""
    # False if there is a format without datatype
    if not datatype and format:
        return False
    if not format:
        format = ""
    if datatype == "color":
        allowed_formats = ("rgb", "hsv")
        return True if format in allowed_formats else False
    elif datatype == "enum":
        # Expression: value,value,value
        # Examples: A,B,C or ON,OFF,PAUSE
        r = re.compile(r'^(\w+,)*\w+$')
        return True if r.match(format) else False
    elif datatype == "integer":
        # Expression: int:int
        # Examples: 10:15 or -1:5
        r = re.compile(r'^[-]?\d+[:][-]?\d+$')
        return True if r.match(format) else False
    elif datatype == "float":
        # Expression: float:float
        # Example: 3.14:15 or -1.1:-1.2
        r = re.compile(r'^[+-]?([0-9]*[.])?[0-9]+[:][+-]?([0-9]*[.])?[0-9]+$')
        return True if r.match(format) else False
    return True

def isValidUnit(unit):
    """Validate unit"""
    recommended_units = ("ºC", "ºF", "º", "L", "gal", "V", "W", "A", "%", "m",
                        "ft", "Pa", "psi", "#")
    if unit not in recommended_units:
        logger.warning("Unit '{}' is not one of the recommended ones".format(unit))
    return True
    