from sqlalchemy import types, exceptions

from datetime import datetime
import struct
import socket
import time
import ferrox.lib.inet as inet

class DateTime(types.TypeDecorator):
    """Implements a Unix timestamp as an integer."""
    impl = types.Integer

    def __init__(self):
        pass

    def process_bind_param(self, value, engine):
        return int(time.mktime(value.timetuple()))

    def process_result_value(self, value, engine):
        if value == None:
            return None
        else:
            return datetime.fromtimestamp(value)

    def is_mutable(self):
        return False

    def compare_values(self, x, y):
        if type(x) == type(datetime.now()):
            x = self.process_bind_param(x, None)
        if type(y) == type(datetime.now()):
            y = self.process_bind_param(y, None)
        return x == y


# Taken from http://www.sqlalchemy.org/trac/wiki/UsageRecipes/Enum
class Enum(types.TypeDecorator):
    impl = types.SmallInteger

    def __init__(self, *values):
        """Emulate an Enum type.

        values:
           A list of valid values for this column
        """

        if values is None or len(values) is 0:
            raise exceptions.AssertionError('Enum requires a list of values')
        self.values = list(values)

    def process_bind_param(self, value, engine):
        if value not in self.values:
            raise exceptions.AssertionError('"%s" not in Enum.values' % value)
        return self.values.index(value)

    def process_result_value(self, value, engine):
        if value == None:
            return None
        return self.values[value]

    def is_mutable(self):
        return False

    def compare_values(self, x, y):
        if type(x) == type(str()):
            x = self.process_bind_param(x, None)
        if type(y) == type(str()):
            y = self.process_bind_param(y, None)
        return x == y

class IP(types.TypeDecorator):
    """Implements an IP as an integer."""
    impl = types.Binary(length=16)

    def __init__(self):
        pass

    def process_bind_param(self, value, engine):
        try:
            return inet.pton(value);
        except:
            l = len (value)
            if l == 4: return inet.IPV4PREFIX + value
            if l == 16: return value
        raise Exception ('Invalid IP:(' + value +')')

    def process_result_value(self, value, engine):
        return inet.ntop(value);

    def is_mutable(self):
        return False