#!/usr/bin/env python


__version__ = '0.2'
__author__ = 'Stephen Norum <stephen@mybunnyhug.org>'
# http://www.mybunnyhug.org/


import struct
import bz2
import base64
import re


attr_value_sep = ' = '
attr_value_fmt = attr_value_sep.join(('{0}', '{1}'))

def indent(string, amount=4):
    line_start = re.compile(r'^', re.MULTILINE)
    return re.sub(line_start, ' ' * amount, string)

DEFAULT_PGM_DATA_BZ2_B64 = '''
QlpoOTFBWSZTWdr3EiAABa3/xH////////////////QAAECAQAABMAE4RBpSTNpQ
wIaGCbQmj0BHk0NNCMBoEG1PRAMCZMcADQGgaABppkABo0yADRkwQGIAACqSRNMg
CaZkTCYjIaNGNCYAjIyGCYjE8oaep6aWAFkDLmgEwEaM6IiInoAUgMaZACqBnzQC
jIBSAkBKUQERMpOEAoLaiBo26dpTAYsgKnomgCnUqYVPBoVJYtX1Y88D3SgEZNX0
+aH2c1tNGYrOdERESqKEv0SPAAA7pSmRV7R71HlLEq0txUluNahUoKS0Ha/JALtQ
bN15uFu5qgAAf4NJXs+Cfi2sA1k9K0a2Lgui8GD74TBYNp2XGcaC9mAAAEkRERHe
bJvJyyzkUaqtZc0SVmYzPz19nb+q1f9/z+93+sf+zTArgS2QJRWAtJkAWZWngLuS
KcKEhte4kQA=
'''

DEFAULT_PGM_DATA = bz2.decompress(base64.b64decode(DEFAULT_PGM_DATA_BZ2_B64))

def indented_byte_list_string(byte_list, indent_amount=0, items_per_row=8):
    """
    Return an indented multi-line string representation of a byte list.
    """
    str_list = []
    sub_str_list = []
    
    indent_amount = int(indent_amount)
    
    if indent_amount > 0:
        indent_spaces = ' ' * indent_amount
    else:
        indent_spaces = ''
    
    indent_string = ''.join(('\n', indent_spaces))
    
    for byte in byte_list:
        sub_str_list.append('{0:02X}'.format(byte))
        if len(sub_str_list) == items_per_row:
            str_list.append(' '.join(sub_str_list))
            sub_str_list = []
            
    if sub_str_list:
        str_list.append(' '.join(sub_str_list))
                
    return ''.join((indent_spaces, indent_string.join(str_list)))

def pass_validator(value):
    return value

def int_in_range_validator(lower, upper):
    def f(value):
        value = int(value)
        if value < lower or value > upper:
            raise ValueError('out of range ({0} to {1}): {2!r}'.format(lower, upper, value))
        return value    
    return f
    
def setter_factory(name, validator):
    def f(self, val):
        val = validator(val)
        setattr(self, '_' + name, val)
    return f

def getter_factory(name):
    def f(self):
        return getattr(self, '_' + name)
    return f        

def class_factory(class_name='', format='', doc='', format_attrs=None, additional_attrs=None, **kwarg):
    dct = {}
    dct['format'] = format
    dct['__doc__'] = doc
    dct['size'] = struct.calcsize(format)
    dct['format_attrs'] = format_attrs or []
    dct['additional_attrs'] = additional_attrs or []
        
    def unpack(self, data_str=None):
        unpacked_data = struct.unpack(self.format, data_str[0:struct.calcsize(self.format)])
        for i, val in enumerate(unpacked_data):
            setattr(self, self.format_attrs[i][0], val)        
    dct['unpack'] = unpack
    
    def format_str(self):
        out = []
        for name, validator in self.format_attrs:
            out.append(attr_value_fmt.format(name, getattr(self, name)))
        return '\n'.join(out)
        out.append(')')
    dct['format_str'] = format_str

    def pack(self):
        vals = [getattr(self, a[0]) for a in self.format_attrs]
        return struct.pack(self.format, *vals)
    dct['pack'] = pack
    
    for attr_name, validator in dct['format_attrs']:
        g = getter_factory(attr_name)
        s = setter_factory(attr_name, validator)
        dct[attr_name] = property(g, s)
    
    for attr_name, validator in dct['additional_attrs']:
        g = getter_factory(attr_name)
        s = setter_factory(attr_name, validator)
        dct[attr_name] = property(g, s)
    
    dct['__init__'] = unpack        
    dct['__str__'] = format_str
    dct['data'] = property(pack)
        
    dct.update(kwarg)
    return type(class_name, (object,), dct)