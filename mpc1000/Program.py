#!/usr/bin/env python
from .utils import class_factory, DEFAULT_PGM_DATA, int_in_range_validator, attr_value_fmt, indent, indented_byte_list_string, attr_value_sep
from .Pad import Pad
import struct


program_format = (
    '<'   #  Little-endian
    'B'   #  MIDI Program Change   0="Off", 1 to 128
    'B'   #  Slider 1 Pad
    'B'   #  Unknown
    'B'   #  Slider 1 Parameter    0="Tune", 1="Filter", 2="Layer", 3="Attack", 4="Decay"
    'b'   #  Slider 1 Tune Low
    'b'   #  Slider 1 Tune High
    'b'   #  Slider 1 Filter Low
    'b'   #  Slider 1 Filter High
    'B'   #  Slider 1 Layer Low
    'B'   #  Slider 1 Layer High
    'B'   #  Slider 1 Attack Low
    'B'   #  Slider 1 Attack High
    'B'   #  Slider 1 Decay Low
    'B'   #  Slider 1 Decay High
    'B'   #  Slider 2 Pad
    'B'   #  Unknown
    'B'   #  Slider 2 Parameter    0="Tune", 1="Filter", 2="Layer", 3="Attack", 4="Decay"
    'b'   #  Slider 2 Tune Low
    'b'   #  Slider 2 Tune High
    'b'   #  Slider 2 Filter Low
    'b'   #  Slider 2 Filter High
    'B'   #  Slider 2 Layer Low
    'B'   #  Slider 2 Layer High
    'B'   #  Slider 2 Attack Low
    'B'   #  Slider 2 Attack High
    'B'   #  Slider 2 Decay Low
    'B'   #  Slider 2 Decay High
    '17x' #  Padding
)

program_format_attrs = (
    ('midi_program_change'  , int_in_range_validator(0, 128)),
    ('slider_1_pad'         , int_in_range_validator(0, 63)),
    ('slider_1_unknown'     , int_in_range_validator(0, 255)),
    ('slider_1_parameter'   , int_in_range_validator(0, 4)),
    ('slider_1_tune_low'    , int_in_range_validator(-120, 120)),
    ('slider_1_tune_high'   , int_in_range_validator(-120, 120)),
    ('slider_1_filter_low'  , int_in_range_validator(-50, 50)),
    ('slider_1_filter_high' , int_in_range_validator(-50, 50)),
    ('slider_1_layer_low'   , int_in_range_validator(0, 127)),
    ('slider_1_layer_high'  , int_in_range_validator(0, 127)),
    ('slider_1_attack_low'  , int_in_range_validator(0, 100)),
    ('slider_1_attack_high' , int_in_range_validator(0, 100)),
    ('slider_1_decay_low'   , int_in_range_validator(0, 100)),
    ('slider_1_decay_high'  , int_in_range_validator(0, 100)),
    ('slider_2_pad'         , int_in_range_validator(0, 63)),
    ('slider_2_unknown'     , int_in_range_validator(0, 255)),
    ('slider_2_parameter'   , int_in_range_validator(0, 4)),
    ('slider_2_tune_low'    , int_in_range_validator(-120, 120)),
    ('slider_2_tune_high'   , int_in_range_validator(-120, 120)),
    ('slider_2_filter_low'  , int_in_range_validator(-50, 50)),
    ('slider_2_filter_high' , int_in_range_validator(-50, 50)),
    ('slider_2_layer_low'   , int_in_range_validator(0, 127)),
    ('slider_2_layer_high'  , int_in_range_validator(0, 127)),
    ('slider_2_attack_low'  , int_in_range_validator(0, 100)),
    ('slider_2_attack_high' , int_in_range_validator(0, 100)),
    ('slider_2_decay_low'   , int_in_range_validator(0, 100)),
    ('slider_2_decay_high'  , int_in_range_validator(0, 100)),
)

def program_init(self, data=None):
    if data is None:
        data = DEFAULT_PGM_DATA

    offset = 0

    # Header
    fmt = self.addl_formats['header']
    size = struct.calcsize(fmt)
    unpacked_data = struct.unpack(fmt, data[offset:offset+size])
    self.file_size = unpacked_data[0]
    self.file_type = unpacked_data[1]
    offset += size

    # Pads and samples
    size = Pad.size
    self.pads = []
    for i in xrange(0, 64):
        p = Pad(data[offset:offset+size])
        self.pads.append(p)
        offset += size

    # Pad MIDI Note data
    fmt = self.addl_formats['pad_midi_note']
    size = struct.calcsize(fmt)
    pad_midi_notes = struct.unpack(fmt, data[offset:offset+size])
    for i, p in enumerate(pad_midi_notes):
        self.pads[i].midi_note = p
    offset += size

    # MIDI Note Pad data
    fmt = self.addl_formats['midi_note_pad']
    size = struct.calcsize(fmt)
    midi_note_pads = struct.unpack(fmt, data[offset:offset+size])
    # Ignore MIDI Note Pad data -- already have data from Pad MIDI Note data
    offset += size

    self.unpack(data[offset:])

def program_str(self):
    out = []
    for a in ('file_size', 'file_type'):
        print attr_value_fmt.format(a, getattr(self, a))

    for a in ('pad_midi_notes', 'midi_note_pads'):
        val = indented_byte_list_string(getattr(self, a), len(a) + len(attr_value_sep)).strip()
        print attr_value_fmt.format(a, val)

    out.append(self.format_str())
    for i, s in enumerate(self.pads):
        out.append('Pad {0}:'.format(i))
        out.append(indent(str(s)))
    return '\n'.join(out)

def program_data(self):
    header_str = struct.pack(self.addl_formats['header'], self.file_size, self.file_type)
    pad_midi_note_str = struct.pack(self.addl_formats['pad_midi_note'], *(self.pad_midi_notes))
    midi_note_pad_str = struct.pack(self.addl_formats['midi_note_pad'], *(self.midi_note_pads))
    midi_and_sliders_str = self.pack()

    pad_data_str_list = [p.data for p in self.pads]

    data_str_list = [header_str]
    data_str_list.extend(pad_data_str_list)
    data_str_list.extend([pad_midi_note_str, midi_note_pad_str, midi_and_sliders_str])

    return ''.join(data_str_list)

def program_pad_midi_notes(self):
    """
    List of MIDI note numbers (Range: 0 to 127) associated with pads
    """
    return [p.midi_note for p in self.pads]

def program_midi_note_pads(self):
    """
    List of pad numbers (Range: 0 to 63, no pad=64) associated with MIDI notes
    """
    mnpl = [64,] * 128
    for i, p in enumerate(self.pads):
        mnpl[p.midi_note] = i
    return mnpl


Program = class_factory(
    class_name = 'Program',
    doc = 'MPC 1000 Program',
    format = program_format,
    format_attrs = program_format_attrs,
    addl_formats = {
        'header': '<Hxx16s4x',
        'pad_midi_note': '<64B',
        'midi_note_pad': '<128B',
    },
    __init__ = program_init,
    __str__ = program_str,
    data = property(program_data),
    pad_midi_notes = property(program_pad_midi_notes),
    midi_note_pads = property(program_midi_note_pads),
)