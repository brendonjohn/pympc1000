#!/usr/bin/env python
from .utils import class_factory, indent, int_in_range_validator, pass_validator
from .Sample import Sample
import struct

pad_format = (
    '<'  # Little-endian
    '2x'  # Padding
    'b'  # Voice Overlap    0="Poly", 1="Mono"
    'b'  # Mute Group       0="Off", 1 to 32
    'x'  # Padding
    'B'  # Unknown
    'B'  # Attack
    'B'  # Decay
    'B'  # Decay Mode       0="End", 1="Start"
    '2x'  # Padding
    'B'  # Velocity to Level
    '5x'  # Padding
    'b'  # Filter 1 Type    0="Off", 1="Lowpass", 2="Bandpass", 3="Highpass"
    'B'  # Filter 1 Freq
    'B'  # Filter 1 Res
    '4x'  # Padding
    'B'  # Filter 1 Velocity to Frequency
    'B'  # Filter 2 Type    0="Off", 1="Lowpass", 2="Bandpass", 3="Highpass", 4="Link"
    'B'  # Filter 2 Freq
    'B'  # Filter 2 Res
    '4x'  # Padding
    'B'  # Filter 2 Velocity to Frequency
    '14x'  # Padding
    'B'  # Mixer Level
    'B'  # Mixer Pan    0 to 49=Left, 50=Center, 51 to 100=Right
    'B'  # Output       0="Stereo", 1="1-2", 2="3-4"
    'B'  # FX Send      0="Off", 1="1", 2="2"
    'B'  # FX Send Level
    'B'  # Filter Attenuation   0="0dB", 1="-6dB", 2="-12dB"
    '15x'  # Padding
)

pad_format_attrs = (
    ("voice_overlap", int_in_range_validator(0, 1)),
    ("mute_group", int_in_range_validator(0, 32)),
    ("unknown", int_in_range_validator(0, 255)),
    ("attack", int_in_range_validator(0, 100)),
    ("decay", int_in_range_validator(0, 100)),
    ("decay_mode", int_in_range_validator(0, 1)),
    ("vel_to_level", int_in_range_validator(0, 100)),
    ("filter_1_type", int_in_range_validator(0, 3)),
    ("filter_1_freq", int_in_range_validator(0, 100)),
    ("filter_1_res", int_in_range_validator(0, 100)),
    ("filter_1_vel_to_freq", int_in_range_validator(0, 100)),
    ("filter_2_type", int_in_range_validator(0, 4)),
    ("filter_2_freq", int_in_range_validator(0, 100)),
    ("filter_2_res", int_in_range_validator(0, 100)),
    ("filter_2_vel_to_freq", int_in_range_validator(0, 100)),
    ("mixer_level", int_in_range_validator(0, 100)),
    ("mixer_pan", int_in_range_validator(0, 100)),
    ("output", int_in_range_validator(0, 2)),
    ("fx_send", int_in_range_validator(0, 2)),
    ("fx_send_level", int_in_range_validator(0, 100)),
    ("filter_attenuation", int_in_range_validator(0, 2)),
)


def pad_init(self, data):
    self.samples = []
    offset = 0
    for i in xrange(0, 4):
        s = Sample(data[offset:])
        self.samples.append(s)
        offset += Sample.size
    self.unpack(data[offset:])


def pad_str(self):
    out = [self.format_str()]
    for i, s in enumerate(self.samples):
        out.append('Sample {0}:'.format(i))
        out.append(indent(str(s)))
    return '\n'.join(out)


def pad_data(self):
    data_str_list = [s.data for s in self.samples]
    data_str_list.append(self.pack())
    return ''.join(data_str_list)


Pad = class_factory(
    class_name='Pad',
    doc='MPC 1000 Pad',
    format=pad_format,
    format_attrs=pad_format_attrs,
    additional_attrs=(
        ("midi_note", int_in_range_validator(0, 127)),
        ("samples", pass_validator),
    ),
    size=struct.calcsize(pad_format) + 4 * Sample.size,
    __init__=pad_init,
    __str__=pad_str,
    data=property(pad_data),
)