#!/usr/bin/env python

# Stephen Norum
# stephen@mybunnyhug.org
# http://www.mybunnyhug.org/

"""
load, edit, and export Akai MPC 1000 program file data
"""

import sys
import struct
import bz2
import base64

__all__ = ('Program', 'Pad', 'Sample', 'DEFAULT_PGM_DATA', 'DEFAULT_PAD_DATA', 'DEFAULT_SAMPLE_DATA')

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

DEFAULT_PAD_DATA = DEFAULT_PGM_DATA[24:(24 + 164)]
DEFAULT_SAMPLE_DATA = DEFAULT_PGM_DATA[24:(24 + 24)]

def int_in_range(value, lower, upper):
    value = int(value)
    if value < lower or value > upper:
        raise ValueError('out of range ({0} to {1}): {2!r}'.format(lower, upper, value))
    return value    

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

def int_in_range_validator(lower, upper):
    def f(value):
        value = int(value)
        if value < lower or value > upper:
            raise ValueError('out of range ({0} to {1}): {2!r}'.format(lower, upper, value))
        return value    
    return f

def sample_name_validator(value):
    valid_name_characters = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "1234567890"
        "!#$%&'()-@_{} \x00"
    )
    value = str(value)
    if len(value) > 16:
        raise ValueError('string too long')
    for c in value:
        if c not in valid_name_characters:
            raise ValueError('invalid character: {0!r}'.format(c))
    return value
    
def setter_factory(name, validator):
    def f(self, val):
        val = validator(val)
        setattr(self, '_' + name, val)
    return f

def getter_factory(name):
    def f(self):
        return getattr(self, '_' + name)
    return f        

def class_factory(name='', format='', doc='', attrs=None, **kwarg):
    dct = {}
    dct.update(kwarg)
    dct['format'] = format
    dct['__doc__'] = doc
    dct['size'] = struct.calcsize(format)
    dct['attrs'] = attrs
    
    def init(self, data_str=None):
        unpacked_data = struct.unpack(self.format, data_str[0:self.size])
        for i, (name, validator) in enumerate(attrs):
            setattr(self, name, unpacked_data[i])        
    dct['__init__'] = init
    
    def str_rep(self):
        out = []
        for name, validator in attrs:
            out.append('{0} = {1}'.format(name, getattr(self, name)))
        return '\n'.join(out)
    dct['__str__'] = str_rep
    
    def data(self):
        vals = [getattr(self, a[0]) for a in self.attrs]
        return struct.pack(self.format, *vals)
    dct['data'] = property(data)
    
    if attrs:
        for name, validator in attrs:
            g = getter_factory(name)
            s = setter_factory(name, validator)
            dct[name] = property(g, s)
    
    return type(name, (object,), dct)

Sample = class_factory(
    name = 'Sample',
    doc = 'MPC 1000 sample settings',
    format = (
        '<'   #     Little-endian
        '16s' #  0  Sample Name
        'x'   #  -  Padding
        'B'   #  1  Level
        'B'   #  2  Range Upper
        'B'   #  3  Range Lower
        'h'   #  4  Tuning
        'B'   #  5  Play Mode       0="One Shot", 1="Note On"
        'x'   #  -  Padding
    ),
    attrs = (
        ('name', sample_name_validator),
        ('level', int_in_range_validator(0, 100)),
        ('range_upper', int_in_range_validator(0, 127)),
        ('range_lower', int_in_range_validator(0, 127)),
        ('tuning', int_in_range_validator(-3600, 3600)),
        ('play_mode', int_in_range_validator(0, 1)),
    )
)


class Pad(object):
    """
    MPC 1000 pad settings
    """
    length = 164
    format = (
        '<'     #       Little-endian
        '2x'    #   -   Padding
        'b'     #   0   Voice Overlap    0="Poly", 1="Mono"
        'b'     #   1   Mute Group       0="Off", 1 to 32
        'x'     #   -   Padding
        'B'     #   2   Unknown
        'B'     #   3   Attack   
        'B'     #   4   Decay 
        'B'     #   5   Decay Mode       0="End", 1="Start"
        '2x'    #   -   Padding 
        'B'     #   6   Velocity to Level    
        '5x'    #   -   Padding 
        'b'     #   7   Filter 1 Type    0="Off", 1="Lowpass", 2="Bandpass", 3="Highpass"
        'B'     #   8   Filter 1 Freq    
        'B'     #   9   Filter 1 Res 
        '4x'    #   -   Padding
        'B'     #  10   Filter 1 Velocity to Frequency   
        'B'     #  11   Filter 2 Type    0="Off", 1="Lowpass", 2="Bandpass", 3="Highpass", 4="Link"
        'B'     #  12   Filter 2 Freq    
        'B'     #  13   Filter 2 Res 
        '4x'    #  --   Padding
        'B'     #  14   Filter 2 Velocity to Frequency   
        '14x'   #  --   Padding  
        'B'     #  15   Mixer Level 
        'B'     #  16   Mixer Pan    0 to 49=Left, 50=Center, 51 to 100=Right
        'B'     #  17   Output       0="Stereo", 1="1-2", 2="3-4"
        'B'     #  18   FX Send      0="Off", 1="1", 2="2"
        'B'     #  19   FX Send Level 
        'B'     #  20   Filter Attenuation   0="0dB", 1="-6dB", 2="-12dB"
        '15x'   #  --   Padding
    )
    
    def __init__(self, data_str=None):
        """
        Initialize Pad object with data_str.  Initialized with
        DEFAULT_PAD_DATA if data_str is None.
        """
        if not data_str:
            data_str = DEFAULT_PAD_DATA
        
        self.parse_data(data_str)

    def parse_data(self, data_str):
        #
        # Samples
        #
        self.sample_list = []
        sample_data_start = 0
        sample_data_size = Sample.size
        for i in range(0, 4):
            sample_data_end = sample_data_start + sample_data_size
            s = Sample(data_str[sample_data_start:sample_data_end])
            self.sample_list.append(s)
            sample_data_start = sample_data_end
        
        #
        # Pad data
        #
        pad_data_start = sample_data_end
        pad_data_size = Pad.length - (4 * Sample.size)
        pad_data_end = pad_data_start + pad_data_size
        
        unpacked_data = struct.unpack(Pad.format, data_str[pad_data_start:pad_data_end])
        self.voice_overlap        = unpacked_data[0]
        self.mute_group           = unpacked_data[1]
        self.unknown              = unpacked_data[2]
        self.attack               = unpacked_data[3]
        self.decay                = unpacked_data[4]
        self.decay_mode           = unpacked_data[5]
        self.vel_to_level         = unpacked_data[6]
        self.filter_1_type        = unpacked_data[7]
        self.filter_1_freq        = unpacked_data[8]
        self.filter_1_res         = unpacked_data[9]
        self.filter_1_vel_to_freq = unpacked_data[10]
        self.filter_2_type        = unpacked_data[11]
        self.filter_2_freq        = unpacked_data[12]
        self.filter_2_res         = unpacked_data[13]
        self.filter_2_vel_to_freq = unpacked_data[14]
        self.mixer_level          = unpacked_data[15]
        self.mixer_pan            = unpacked_data[16]
        self.output               = unpacked_data[17]
        self.fx_send              = unpacked_data[18]
        self.fx_send_level        = unpacked_data[19]
        self.filter_attenuation   = unpacked_data[20]

    def __str__(self):
        str_list = []
        for i, s in enumerate(self.sample_list):
            str_list.append('Sample {0}'.format(i))
            str_list.append(str(s))

        str_list.append('Pad Data')
        sub_str_list = ['']
        sub_str_list.append('MIDI Note                  {0}\n'.format(self.midi_note))
        sub_str_list.append('Voice Overlap              {0}\n'.format(self.voice_overlap))
        sub_str_list.append('Mute Group                 {0}\n'.format(self.mute_group))
        sub_str_list.append('Attack                     {0}\n'.format(self.attack))
        sub_str_list.append('Decay                      {0}\n'.format(self.decay))
        sub_str_list.append('Decay Mode                 {0}\n'.format(self.decay_mode))
        sub_str_list.append('Vel to Level               {0}\n'.format(self.vel_to_level))
        sub_str_list.append('Filter 1 Type              {0}\n'.format(self.filter_1_type))
        sub_str_list.append('Filter 1 Freq              {0}\n'.format(self.filter_1_freq))
        sub_str_list.append('Filter 1 Res               {0}\n'.format(self.filter_1_res))
        sub_str_list.append('Filter 1 Vel to Freq       {0}\n'.format(self.filter_1_vel_to_freq))
        sub_str_list.append('Filter 2 Type              {0}\n'.format(self.filter_2_type))
        sub_str_list.append('Filter 2 Freq              {0}\n'.format(self.filter_2_freq))
        sub_str_list.append('Filter 2 Res               {0}\n'.format(self.filter_2_res))
        sub_str_list.append('Filter 2 Vel to Freq       {0}\n'.format(self.filter_2_vel_to_freq))
        sub_str_list.append('Mixer Level                {0}\n'.format(self.mixer_level))
        sub_str_list.append('Mixer Pan                  {0}\n'.format(self.mixer_pan))
        sub_str_list.append('Output                     {0}\n'.format(self.output))
        sub_str_list.append('FX Send                    {0}\n'.format(self.fx_send))
        sub_str_list.append('FX Send Level              {0}\n'.format(self.fx_send_level))
        sub_str_list.append('Filter Attenuation         {0}\n'.format(self.filter_attenuation))
        sub_str_list.append('Unknown                    {0}\n'.format(self.unknown))
        str_list.append('    '.join(sub_str_list))

        return '\n'.join(str_list)

    @property
    def voice_overlap(self):
        """
        Range: 0="Poly", 1="Mono"
        """
        return self._voice_overlap
    
    @voice_overlap.setter
    def voice_overlap(self, value):
        self._voice_overlap = int_in_range(value, 0, 1)
    
    @property
    def mute_group(self):
        """
        Range: 0="Off", 1 to 32
        """
        return self._mute_group
    
    @mute_group.setter
    def mute_group(self, value):
        self._mute_group = int_in_range(value, 0, 32)

    @property
    def attack(self):
        """
        Range: 0 to 100
        """
        return self._attack
    
    @attack.setter
    def attack(self, value):
        self._attack = int_in_range(value, 0, 100)

    @property
    def decay(self):
        """
        Range: 0 to 100
        """
        return self._decay
    
    @decay.setter
    def decay(self, value):
        self._decay = int_in_range(value, 0, 100)
        
    @property
    def decay_mode(self):
        """
        Range: 0="End", 1="Start"
        """
        return self._decay_mode
    
    @decay_mode.setter
    def decay_mode(self, value):
        self._decay_mode = int_in_range(value, 0, 1)
        
    @property
    def vel_to_level(self):
        """
        Range: 0 to 100
        """
        return self._vel_to_level
    
    @vel_to_level.setter
    def vel_to_level(self, value):
        self._vel_to_level = int_in_range(value, 0, 100)
        
    @property
    def filter_1_type(self):
        """
        Range: 0="Off", 1="Lowpass", 2="Bandpass", 3="Highpass"
        """
        return self._filter_1_type
    
    @filter_1_type.setter
    def filter_1_type(self, value):
        self._filter_1_type = int_in_range(value, 0, 3)

    @property
    def filter_1_freq(self):
        """
        Range: 0 to 100
        """
        return self._filter_1_freq
    
    @filter_1_freq.setter
    def filter_1_freq(self, value):
        self._filter_1_freq = int_in_range(value, 0, 100)

    @property
    def filter_1_res(self):
        """
        Range: 0 to 100
        """
        return self._filter_1_res
    
    @filter_1_res.setter
    def filter_1_res(self, value):
        self._filter_1_res = int_in_range(value, 0, 100)

    @property
    def filter_1_vel_to_freq(self):
        """
        Range: 0 to 100
        """
        return self._filter_1_vel_to_freq
    
    @filter_1_vel_to_freq.setter
    def filter_1_vel_to_freq(self, value):
        self._filter_1_vel_to_freq = int_in_range(value, 0, 100)

    @property
    def filter_2_type(self):
        """
        Range: 0="Off", 1="Lowpass", 2="Bandpass", 3="Highpass", 4="Link"
        """
        return self._filter_2_type
    
    @filter_2_type.setter
    def filter_2_type(self, value):
        self._filter_2_type = int_in_range(value, 0, 4)

    @property
    def filter_2_freq(self):
        """
        Range: 0 to 100
        """
        return self._filter_2_freq
    
    @filter_2_freq.setter
    def filter_2_freq(self, value):
        self._filter_2_freq = int_in_range(value, 0, 100)

    @property
    def filter_2_res(self):
        """
        Range: 0 to 100
        """
        return self._filter_2_res
    
    @filter_2_res.setter
    def filter_2_res(self, value):
        self._filter_2_res = int_in_range(value, 0, 100)

    @property
    def filter_2_vel_to_freq(self):
        """
        Range: 0 to 100
        """
        return self._filter_2_vel_to_freq
    
    @filter_2_vel_to_freq.setter
    def filter_2_vel_to_freq(self, value):
        """
        Range: 0 to 100
        """
        self._filter_2_vel_to_freq = int_in_range(value, 0, 100)

    @property
    def mixer_level(self):
        """
        Range: 0 to 100
        """
        return self._mixer_level
    
    @mixer_level.setter
    def mixer_level(self, value):
        self._mixer_level = int_in_range(value, 0, 100)

    @property
    def mixer_pan(self):
        """
        Range: 0 to 100
        Left: 0 to 49
        Center: 50
        Right: 51 to 100
        """
        return self._mixer_pan
    
    @mixer_pan.setter
    def mixer_pan(self, value):
        self._mixer_pan = int_in_range(value, 0, 100)

    @property
    def output(self):
        """
        0="Stereo", 1="1-2", 2="3-4"
        """
        return self._output
    
    @output.setter
    def output(self, value):
        self._output = int_in_range(value, 0, 2)

    @property
    def fx_send(self):
        """
        Range: 0="Off", 1="1", 2="2"
        """
        return self._fx_send
    
    @fx_send.setter
    def fx_send(self, value):
        self._fx_send = int_in_range(value, 0, 2)

    @property
    def fx_send_level(self):
        """
        Range: 0 to 100
        """
        return self._fx_send_level
    
    @fx_send_level.setter
    def fx_send_level(self, value):
        self._fx_send_level = int_in_range(value, 0, 100)

    @property
    def filter_attenuation(self):
        """
        Range: 0="0dB", 1="-6dB", 2="-12dB"
        """
        return self._filter_attenuation
    
    @filter_attenuation.setter
    def filter_attenuation(self, value):
        self._filter_attenuation = int_in_range(value, 0, 2)

    @property
    def midi_note(self):
        """
        Range: 0 to 127
        """
        return self._midi_note
    
    @midi_note.setter
    def midi_note(self, value):
        self._midi_note = int_in_range(value, 0, 127)

    @property
    def unknown(self):
        """
        Unknown value.  Default pgm value is 1.
        """
        return self._unknown
    
    @unknown.setter
    def unknown(self, value):
        self._unknown = int_in_range(value, 0, 255)
    
    @property
    def data(self):
        """
        Return MPC1000 v1.00 formatted data string for object
        """
        pad_data_str = struct.pack(Pad.format,
            self.voice_overlap,
            self.mute_group,
            self.unknown,
            self.attack,
            self.decay,
            self.decay_mode,
            self.vel_to_level,
            self.filter_1_type,
            self.filter_1_freq,
            self.filter_1_res,
            self.filter_1_vel_to_freq,
            self.filter_2_type,
            self.filter_2_freq,
            self.filter_2_res,
            self.filter_2_vel_to_freq,
            self.mixer_level,
            self.mixer_pan,
            self.output,
            self.fx_send,
            self.fx_send_level,
            self.filter_attenuation
        )
        
        sample_str_list = [s.data for s in self.sample_list]
        data_str_list = sample_str_list
        data_str_list.append(pad_data_str)

        return ''.join(data_str_list)


class Program(object):
    """
    MPC 1000 program settings
    """

    format = {
        'header': '<Hxx16s4x',
        'pad_midi_note': '<64B',
        'midi_note_pad': '<128B',
        'midi_and_sliders': (
            '<'   #         Little-endian
            'B'   #    0    MIDI Program Change   0="Off", 1 to 128
            'B'   #    1    Slider 1 Pad
            'B'   #    2    Unknown
            'B'   #    3    Slider 1 Parameter    0="Tune", 1="Filter", 2="Layer", 3="Attack", 4="Decay"
            'b'   #    4    Slider 1 Tune Low  
            'b'   #    5    Slider 1 Tune High
            'b'   #    6    Slider 1 Filter Low   
            'b'   #    7    Slider 1 Filter High  
            'B'   #    8    Slider 1 Layer Low    
            'B'   #    9    Slider 1 Layer High   
            'B'   #   10    Slider 1 Attack Low   
            'B'   #   11    Slider 1 Attack High  
            'B'   #   12    Slider 1 Decay Low    
            'B'   #   13    Slider 1 Decay High   
            'B'   #   14    Slider 2 Pad   
            'B'   #   15    Unknown 
            'B'   #   16    Slider 2 Parameter    0="Tune", 1="Filter", 2="Layer", 3="Attack", 4="Decay"
            'b'   #   17    Slider 2 Tune Low  
            'b'   #   18    Slider 2 Tune High     
            'b'   #   19    Slider 2 Filter Low        
            'b'   #   20    Slider 2 Filter High   
            'B'   #   21    Slider 2 Layer Low     
            'B'   #   22    Slider 2 Layer High    
            'B'   #   23    Slider 2 Attack Low        
            'B'   #   24    Slider 2 Attack High   
            'B'   #   25    Slider 2 Decay Low     
            'B'   #   26    Slider 2 Decay High   
            '17x' #   --    Padding
        )
    }

    def __init__(self, data_str=None):
        """
        Initialize Pad object with data_str.  Initialized with
        DEFAULT_PGM_DATA if data_str is None.
        """
        
        self._slider_1_tune_low    = -120
        self._slider_1_tune_high   = 120
        self._slider_1_filter_low  = -50
        self._slider_1_filter_high = 50
        self._slider_1_layer_low   = 0
        self._slider_1_layer_high  = 127
        self._slider_1_attack_low  = 0
        self._slider_1_attack_high = 100
        self._slider_1_decay_low   = 0
        self._slider_1_decay_high  = 100
        self._slider_2_tune_low    = -120
        self._slider_2_tune_high   = 120
        self._slider_2_filter_low  = -50
        self._slider_2_filter_high = 50
        self._slider_2_layer_low   = 0
        self._slider_2_layer_high  = 127
        self._slider_2_attack_low  = 0
        self._slider_2_attack_high = 100
        self._slider_2_decay_low   = 0
        self._slider_2_decay_high  = 100

        if not data_str:
            data_str = DEFAULT_PGM_DATA
        
        self.load(data_str)
    
    def load(self, data_str):
        #
        # Header
        #
        header_start = 0
        header_size = 24
        header_end = header_start + header_size
        unpacked_data = struct.unpack(Program.format['header'], data_str[header_start:header_end])
        self.file_size = unpacked_data[0]
        self.file_type = unpacked_data[1]
        
        #
        # Pad and samples
        #
        pad_data_start = header_end
        pad_data_size = Pad.length
        self.pad_list = []
        for i in range(0, 64):
            pad_data_end = pad_data_start + pad_data_size
            p = Pad(data_str[pad_data_start:pad_data_end])
            self.pad_list.append(p)
            pad_data_start = pad_data_end
        
        #
        # Pad MIDI Note data
        #
        pad_midi_note_start = pad_data_start
        pad_midi_note_size = 64
        pad_midi_note_end = pad_midi_note_start + pad_midi_note_size
        pad_midi_note_list = struct.unpack(Program.format['pad_midi_note'], data_str[pad_midi_note_start:pad_midi_note_end])
        for i, p in enumerate(pad_midi_note_list):
            self.pad_list[i].midi_note = p
        
        #
        # MIDI Note Pad data
        #
        midi_note_pad_start = pad_midi_note_end
        midi_note_pad_size = 128
        midi_note_pad_end = midi_note_pad_start + midi_note_pad_size
        midi_note_pad_list = struct.unpack(Program.format['midi_note_pad'], data_str[midi_note_pad_start:midi_note_pad_end])
        # Ignore MIDI Note Pad data -- already have data from Pad MIDI Note data
                
        #
        # MIDI and Sliders
        #        
        program_data_start = midi_note_pad_end
        program_data_size = 44
        program_data_end = program_data_start + program_data_size
        unpacked_data = struct.unpack(Program.format['midi_and_sliders'], data_str[program_data_start:program_data_end])

        self.midi_program_change  = unpacked_data[0]
        self.slider_1_pad         = unpacked_data[1]
        self.slider_1_unknown     = unpacked_data[2]
        self.slider_1_parameter   = unpacked_data[3]
        self.slider_1_tune_low    = unpacked_data[4]
        self.slider_1_tune_high   = unpacked_data[5]
        self.slider_1_filter_low  = unpacked_data[6]
        self.slider_1_filter_high = unpacked_data[7]
        self.slider_1_layer_low   = unpacked_data[8]
        self.slider_1_layer_high  = unpacked_data[9]
        self.slider_1_attack_low  = unpacked_data[10]
        self.slider_1_attack_high = unpacked_data[11]
        self.slider_1_decay_low   = unpacked_data[12]
        self.slider_1_decay_high  = unpacked_data[13]
        self.slider_2_pad         = unpacked_data[14]
        self.slider_2_unknown     = unpacked_data[15]
        self.slider_2_parameter   = unpacked_data[16]
        self.slider_2_tune_low    = unpacked_data[17]
        self.slider_2_tune_high   = unpacked_data[18]
        self.slider_2_filter_low  = unpacked_data[19]
        self.slider_2_filter_high = unpacked_data[20]
        self.slider_2_layer_low   = unpacked_data[21]
        self.slider_2_layer_high  = unpacked_data[22]
        self.slider_2_attack_low  = unpacked_data[23]
        self.slider_2_attack_high = unpacked_data[24]
        self.slider_2_decay_low   = unpacked_data[25]
        self.slider_2_decay_high  = unpacked_data[26]

    def __str__(self):
        str_list = []
        str_list.append('=' * 50)
        str_list.append('Program'.center(50))
        str_list.append('=' * 50)
        
        str_list.append('File Size                      {0}'.format(self.file_size))
        str_list.append('File Type                      {0}'.format(self.file_type))
        
        str_list.append('')
        str_list.append('MIDI Program Change            {0}'.format(self.midi_program_change))
        
        str_list.append('Slider 1')        
        sub_str_list = ['']
        sub_str_list.append('Pad                        {0}\n'.format(self.slider_1_pad))
        sub_str_list.append('Parameter                  {0}\n'.format(self.slider_1_parameter))
        sub_str_list.append('Tune Low                   {0}\n'.format(self.slider_1_tune_low))
        sub_str_list.append('Tune High                  {0}\n'.format(self.slider_1_tune_high))
        sub_str_list.append('Filter Low                 {0}\n'.format(self.slider_1_filter_low))
        sub_str_list.append('Filter High                {0}\n'.format(self.slider_1_filter_high))
        sub_str_list.append('Layer Low                  {0}\n'.format(self.slider_1_layer_low))
        sub_str_list.append('Layer High                 {0}\n'.format(self.slider_1_layer_high))
        sub_str_list.append('Attack Low                 {0}\n'.format(self.slider_1_attack_low))
        sub_str_list.append('Attack High                {0}\n'.format(self.slider_1_attack_high))
        sub_str_list.append('Decay Low                  {0}\n'.format(self.slider_1_decay_low))
        sub_str_list.append('Decay High                 {0}\n'.format(self.slider_1_decay_high))
        sub_str_list.append('Unknown                    {0}\n'.format(self.slider_1_unknown))
        str_list.append('    '.join(sub_str_list))
        
        str_list.append('Slider 2')        
        sub_str_list = ['']
        sub_str_list.append('Pad                        {0}\n'.format(self.slider_2_pad))
        sub_str_list.append('Parameter                  {0}\n'.format(self.slider_2_parameter))
        sub_str_list.append('Tune Low                   {0}\n'.format(self.slider_2_tune_low))
        sub_str_list.append('Tune High                  {0}\n'.format(self.slider_2_tune_high))
        sub_str_list.append('Filter Low                 {0}\n'.format(self.slider_2_filter_low))
        sub_str_list.append('Filter High                {0}\n'.format(self.slider_2_filter_high))
        sub_str_list.append('Layer Low                  {0}\n'.format(self.slider_2_layer_low))
        sub_str_list.append('Layer High                 {0}\n'.format(self.slider_2_layer_high))
        sub_str_list.append('Attack Low                 {0}\n'.format(self.slider_2_attack_low))
        sub_str_list.append('Attack High                {0}\n'.format(self.slider_2_attack_high))
        sub_str_list.append('Decay Low                  {0}\n'.format(self.slider_2_decay_low))
        sub_str_list.append('Decay High                 {0}\n'.format(self.slider_2_decay_high))
        sub_str_list.append('Unknown                    {0}\n'.format(self.slider_2_unknown))
        str_list.append('    '.join(sub_str_list))

        str_list.append('Pad MIDI Note Values')
        str_list.append(indented_byte_list_string(self.pad_midi_note_list, 4, 8))

        str_list.append('')
        str_list.append('MIDI Note Pad Values')
        str_list.append(indented_byte_list_string(self.midi_note_pad_list, 4, 8))
        
        for i, p in enumerate(self.pad_list):
            str_list.append('')
            str_list.append('=' * 50)
            str_list.append('Pad {0}'.format(i).center(50))
            str_list.append('=' * 50)
            str_list.append(str(p))
        
        return '\n'.join(str_list)

    @property
    def pad_midi_note_list(self):
        """
        List of MIDI note numbers (Range: 0 to 127) associated with Pads
        in pad_list
        """
        return [p.midi_note for p in self.pad_list]

    @property
    def midi_note_pad_list(self):
        """
        List of Pad numbers (Range: 0 to 63, no pad=64) associated with MIDI
        notes
        """
        mnpl = [64,] * 128
        for i, p in enumerate(self.pad_list):
            mnpl[p.midi_note] = i
        return mnpl

    @property
    def midi_program_change(self):
        """
        Range: 0="Off", 1 to 128
        """
        return self._midi_program_change
    
    @midi_program_change.setter
    def midi_program_change(self, value):
        self._midi_program_change = int_in_range(value, 0, 128)

    @property
    def slider_1_pad(self):
        """
        Range: 0 to 63
        """
        return self._slider_1_pad
    
    @slider_1_pad.setter
    def slider_1_pad(self, value):
        self._slider_1_pad = int_in_range(value, 0, 63)

    @property
    def slider_1_unknown(self):
        """
        Unknown value.  Default pgm value is 1.
        """
        return self._slider_1_unknown
    
    @slider_1_unknown.setter
    def slider_1_unknown(self, value):
        self._slider_1_unknown = int_in_range(value, 0, 255)

    @property
    def slider_1_parameter(self):
        """
        Range: 0="Tune", 1="Filter", 2="Layer", 3="Attack", 4="Decay"
        """
        return self._slider_1_parameter
    
    @slider_1_parameter.setter
    def slider_1_parameter(self, value):
        self._slider_1_parameter = int_in_range(value, 0, 4)

    @property
    def slider_1_tune_low(self):
        """
        Range: -120 to 120.  Sets slider_1_tune_high to slider_1_tune_low
        if slider_1_tune_low is greater than slider_1_tune_high.
        """
        return self._slider_1_tune_low
    
    @slider_1_tune_low.setter
    def slider_1_tune_low(self, value):
        self._slider_1_tune_low = int_in_range(value, -120, 120)
        if value > self.slider_1_tune_high:
            self.slider_1_tune_high = value

    @property
    def slider_1_tune_high(self):
        """
        Range: -120 to 120.  Sets slider_1_tune_low to slider_1_tune_high
        if slider_1_tune_high is less than slider_1_tune_low.
        """
        return self._slider_1_tune_high
    
    @slider_1_tune_high.setter
    def slider_1_tune_high(self, value):
        self._slider_1_tune_high = int_in_range(value, -120, 120)
        if value < self.slider_1_tune_low:
            self.slider_1_tune_low = value
            
    @property
    def slider_1_filter_low(self):
        """
        Range: -50 to 50.  Sets slider_1_filter_high to slider_1_filter_low
        if slider_1_filter_low is greater than slider_1_filter_high.
        """
        return self._slider_1_filter_low
    
    @slider_1_filter_low.setter
    def slider_1_filter_low(self, value):
        self._slider_1_filter_low = int_in_range(value, -50, 50)
        if value > self.slider_1_filter_high:
            self.slider_1_filter_high = value

    @property
    def slider_1_filter_high(self):
        """
        Range: -50 to 50.  Sets slider_1_filter_low to slider_1_filter_high
        if slider_1_filter_high is less than slider_1_filter_low.
        """
        return self._slider_1_filter_high
    
    @slider_1_filter_high.setter
    def slider_1_filter_high(self, value):
        self._slider_1_filter_high = int_in_range(value, -50, 50)
        if value < self.slider_1_filter_low:
            self.slider_1_filter_low = value

    @property
    def slider_1_layer_low(self):
        """
        Range: 0 to 127.  Sets slider_1_layer_high to slider_1_layer_low
        if slider_1_layer_low is greater than slider_1_layer_high.
        """
        return self._slider_1_layer_low
    
    @slider_1_layer_low.setter
    def slider_1_layer_low(self, value):
        self._slider_1_layer_low = int_in_range(value, 0, 127)
        if value > self.slider_1_layer_high:
            self.slider_1_layer_high = value

    @property
    def slider_1_layer_high(self):
        """
        Range: 0 to 127.  Sets slider_1_layer_low to slider_1_layer_high
        if slider_1_layer_high is less than slider_1_layer_low.
        """
        return self._slider_1_layer_high
    
    @slider_1_layer_high.setter
    def slider_1_layer_high(self, value):
        self._slider_1_layer_high = int_in_range(value, 0, 127)
        if value < self.slider_1_layer_low:
            self.slider_1_layer_low = value

    @property
    def slider_1_attack_low(self):
        """
        Range: 0 to 100.  Sets slider_1_attack_high to slider_1_attack_low
        if slider_1_attack_low is greater than slider_1_attack_high.
        """
        return self._slider_1_attack_low
    
    @slider_1_attack_low.setter
    def slider_1_attack_low(self, value):
        self._slider_1_attack_low = int_in_range(value, 0, 100)
        if value > self.slider_1_attack_high:
            self.slider_1_attack_high = value

    @property
    def slider_1_attack_high(self):
        """
        Range: 0 to 100.  Sets slider_1_attack_low to slider_1_attack_high
        if slider_1_attack_high is less than slider_1_attack_low.
        """
        return self._slider_1_attack_high
    
    @slider_1_attack_high.setter
    def slider_1_attack_high(self, value):
        self._slider_1_attack_high = int_in_range(value, 0, 100)
        if value < self.slider_1_attack_low:
            self.slider_1_attack_low = value

    @property
    def slider_1_decay_low(self):
        """
        Range: 0 to 100.  Sets slider_1_decay_high to slider_1_decay_low
        if slider_1_decay_low is greater than slider_1_decay_high.
        """
        return self._slider_1_decay_low
    
    @slider_1_decay_low.setter
    def slider_1_decay_low(self, value):
        self._slider_1_decay_low = int_in_range(value, 0, 100)
        if value > self.slider_1_decay_high:
            self.slider_1_decay_high = value

    @property
    def slider_1_decay_high(self):
        """
        Range: 0 to 100.  Sets slider_1_decay_low to slider_1_decay_high
        if slider_1_decay_high is less than slider_1_decay_low.
        """
        return self._slider_1_decay_high
    
    @slider_1_decay_high.setter
    def slider_1_decay_high(self, value):
        self._slider_1_decay_high = int_in_range(value, 0, 100)
        if value < self.slider_1_decay_low:
            self.slider_1_decay_low = value


    @property
    def slider_2_pad(self):
        """
        Range: 0 to 63
        """
        return self._slider_2_pad
    
    @slider_2_pad.setter
    def slider_2_pad(self, value):
        self._slider_2_pad = int_in_range(value, 0, 63)

    @property
    def slider_2_unknown(self):
        """
        Unknown value.  Default pgm value is 1.
        """
        return self._slider_2_unknown
    
    @slider_2_unknown.setter
    def slider_2_unknown(self, value):
        self._slider_2_unknown = int_in_range(value, 0, 255)

    @property
    def slider_2_parameter(self):
        """
        Range: 0="Tune", 1="Filter", 2="Layer", 3="Attack", 4="Decay"
        """
        return self._slider_2_parameter
    
    @slider_2_parameter.setter
    def slider_2_parameter(self, value):
        self._slider_2_parameter = int_in_range(value, 0, 4)

    @property
    def slider_2_tune_low(self):
        """
        Range: -120 to 120.  Sets slider_2_tune_high to slider_2_tune_low
        if slider_2_tune_low is greater than slider_2_tune_high.
        """
        return self._slider_2_tune_low
    
    @slider_2_tune_low.setter
    def slider_2_tune_low(self, value):
        self._slider_2_tune_low = int_in_range(value, -120, 120)
        if value > self.slider_2_tune_high:
            self.slider_2_tune_high = value

    @property
    def slider_2_tune_high(self):
        """
        Range: -120 to 120.  Sets slider_2_tune_low to slider_2_tune_high
        if slider_2_tune_high is less than slider_2_tune_low.
        """
        return self._slider_2_tune_high
    
    @slider_2_tune_high.setter
    def slider_2_tune_high(self, value):
        self._slider_2_tune_high = int_in_range(value, -120, 120)
        if value < self.slider_2_tune_low:
            self.slider_2_tune_low = value
            
    @property
    def slider_2_filter_low(self):
        """
        Range: -50 to 50.  Sets slider_2_filter_high to slider_2_filter_low
        if slider_2_filter_low is greater than slider_2_filter_high.
        """
        return self._slider_2_filter_low
    
    @slider_2_filter_low.setter
    def slider_2_filter_low(self, value):
        self._slider_2_filter_low = int_in_range(value, -50, 50)
        if value > self.slider_2_filter_high:
            self.slider_2_filter_high = value

    @property
    def slider_2_filter_high(self):
        """
        Range: -50 to 50.  Sets slider_2_filter_low to slider_2_filter_high
        if slider_2_filter_high is less than slider_2_filter_low.
        """
        return self._slider_2_filter_high
    
    @slider_2_filter_high.setter
    def slider_2_filter_high(self, value):
        self._slider_2_filter_high = int_in_range(value, -50, 50)
        if value < self.slider_2_filter_low:
            self.slider_2_filter_low = value

    @property
    def slider_2_layer_low(self):
        """
        Range: 0 to 127.  Sets slider_2_layer_high to slider_2_layer_low
        if slider_2_layer_low is greater than slider_2_layer_high.
        """
        return self._slider_2_layer_low
    
    @slider_2_layer_low.setter
    def slider_2_layer_low(self, value):
        self._slider_2_layer_low = int_in_range(value, 0, 127)
        if value > self.slider_2_layer_high:
            self.slider_2_layer_high = value

    @property
    def slider_2_layer_high(self):
        """
        Range: 0 to 127.  Sets slider_2_layer_low to slider_2_layer_high
        if slider_2_layer_high is less than slider_2_layer_low.
        """
        return self._slider_2_layer_high
    
    @slider_2_layer_high.setter
    def slider_2_layer_high(self, value):
        self._slider_2_layer_high = int_in_range(value, 0, 127)
        if value < self.slider_2_layer_low:
            self.slider_2_layer_low = value

    @property
    def slider_2_attack_low(self):
        """
        Range: 0 to 100.  Sets slider_2_attack_high to slider_2_attack_low
        if slider_2_attack_low is greater than slider_2_attack_high.
        """
        return self._slider_2_attack_low
    
    @slider_2_attack_low.setter
    def slider_2_attack_low(self, value):
        self._slider_2_attack_low = int_in_range(value, 0, 100)
        if value > self.slider_2_attack_high:
            self.slider_2_attack_high = value

    @property
    def slider_2_attack_high(self):
        """
        Range: 0 to 100.  Sets slider_2_attack_low to slider_2_attack_high
        if slider_2_attack_high is less than slider_2_attack_low.
        """
        return self._slider_2_attack_high
    
    @slider_2_attack_high.setter
    def slider_2_attack_high(self, value):
        self._slider_2_attack_high = int_in_range(value, 0, 100)
        if value < self.slider_2_attack_low:
            self.slider_2_attack_low = value

    @property
    def slider_2_decay_low(self):
        """
        Range: 0 to 100.  Sets slider_2_decay_high to slider_2_decay_low
        if slider_2_decay_low is greater than slider_2_decay_high.
        """
        return self._slider_2_decay_low
    
    @slider_2_decay_low.setter
    def slider_2_decay_low(self, value):
        self._slider_2_decay_low = int_in_range(value, 0, 100)
        if value > self.slider_2_decay_high:
            self.slider_2_decay_high = value

    @property
    def slider_2_decay_high(self):
        """
        Range: 0 to 100.  Sets slider_2_decay_low to slider_2_decay_high
        if slider_2_decay_high is less than slider_2_decay_low.
        """
        return self._slider_2_decay_high
    
    @slider_2_decay_high.setter
    def slider_2_decay_high(self, value):
        self._slider_2_decay_high = int_in_range(value, 0, 100)
        if value < self.slider_2_decay_low:
            self.slider_2_decay_low = value

    @property
    def data(self):
        """
        Return MPC1000 v1.00 formatted data string for object
        """
        
        header_str = struct.pack(Program.format['header'], self.file_size, self.file_type)
        pad_midi_note_str = struct.pack(Program.format['pad_midi_note'], *(self.pad_midi_note_list))
        midi_note_pad_str = struct.pack(Program.format['midi_note_pad'], *(self.midi_note_pad_list))
        midi_and_sliders_str = struct.pack(Program.format['midi_and_sliders'],
            self.midi_program_change,
            self.slider_1_pad,
            self.slider_1_unknown,
            self.slider_1_parameter,
            self.slider_1_tune_low,
            self.slider_1_tune_high,
            self.slider_1_filter_low,
            self.slider_1_filter_high,
            self.slider_1_layer_low,
            self.slider_1_layer_high,
            self.slider_1_attack_low,
            self.slider_1_attack_high,
            self.slider_1_decay_low,
            self.slider_1_decay_high,
            self.slider_2_pad,
            self.slider_2_unknown,
            self.slider_2_parameter,
            self.slider_2_tune_low,
            self.slider_2_tune_high,
            self.slider_2_filter_low,
            self.slider_2_filter_high,
            self.slider_2_layer_low,
            self.slider_2_layer_high,
            self.slider_2_attack_low,
            self.slider_2_attack_high,
            self.slider_2_decay_low,
            self.slider_2_decay_high            
        )
        
        pad_data_str_list = [p.data for p in self.pad_list]

        data_str_list = [header_str]
        data_str_list.extend(pad_data_str_list)
        data_str_list.extend([pad_midi_note_str, midi_note_pad_str, midi_and_sliders_str])
        
        return ''.join(data_str_list)


def main():
    pgm_data_str = DEFAULT_PGM_DATA
    
    pgm = Program(pgm_data_str)
    
    if pgm:
        print 'Program loaded'
    else:
        print 'Program failed to load'
        return 1
    
    pgm_data = pgm.data
    
    if pgm_data == pgm_data_str:
        print 'Program data matches original'
    else:
        print 'Program data differs from original'
        print repr(pgm_data)
        return 2

    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)

