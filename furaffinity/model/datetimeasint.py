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

import time
from datetime import datetime
from sqlalchemy import types, exceptions

class DateTimeAsInteger(types.TypeDecorator):
    impl = types.Integer
    
    def __init__(self):
        """datetime in Python, INTEGER+epoch in SQL
        """
        pass;
        
    def convert_bind_param(self, value, engine):
        return int(time.mktime(value.timetuple()))
        
    def convert_result_value(self, value, engine):
        return datetime.fromtimestamp(value)
        
    def is_mutable(self):
        return False
        
    def compare_values(self, x, y):
        if type(x) == type(datetime.now()):
            x = self.convert_bind_param(x, None)
        if type(y) == type(datetime.now()):
            y = self.convert_bind_param(y, None)
        return x == y
