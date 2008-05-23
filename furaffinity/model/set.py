## The MIT License

## Copyright (c) <year> <copyright holders>

## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:

## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.

## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
## THE SOFTWARE.


from sqlalchemy import types, exceptions

class Set(types.TypeDecorator):
    impl = types.Integer
    
    def __init__(self, values):
        """Emulate a Set type.

        values:
           A list of valid values for this column
        """

        if values is None or len(values) is 0:
            raise exceptions.AssertionError('Set requires a list of values')
        self.values = values[:]

        
        
    def convert_bind_param(self, value, engine):
        bind_value = 0
        for v in value:
            if v not in self.values:
                raise exceptions.AssertionError('"%s" not in Set.values' % v)
            bind_value |= 2 ** self.values.index(v)
        return bind_value
        
        
    def convert_result_value(self, value, engine):
        result_value = []
        for i in xrange(0,len(self.values)):
            if (2**i)&value:
                result_value.append(self.values[i])
        return set(result_value)
        
    def is_mutable(self):
        return False
        
    def compare_values(self, x, y):
        if type(x) == type(str()):
            x = self.convert_bind_param([x], None)
        if type(y) == type(str()):
            y = self.convert_bind_param([y], None)
    
        return x == y


