#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .signal import EpicsSignal, EpicsSignalRO
from .component import Component as Cmp, FormattedComponent as FCmp
from .device import Device


class EvrChannel(Device):
    """
    A single evr channel for configuring a device's trigger timing.
    """
    link = Cmp(EpicsSignalRO, ':LINK')
    fiducial_rate = Cmp(EpicsSignalRO, ':FIDUCIALRATE')
    pattern_state = Cmp(EpicsSignalRO, ':PATTERNSTATE')
    status = Cmp(EpicsSignalRO, ':STATUS')
    fiducial = Cmp(EpicsSignalRO, ':Fiducial')
    reference_time = Cmp(EpicsSignalRO, ':TREF')

    _trig_base = '{self.prefix}:TRIG{self.ch}:'
    event_code = FCmp(EpicsSignal, _trig_base + 'EC_RBV',
                      write_pv=_trig_base + 'TEC')
    desc = FCmp(EpicsSignal, _trig_base + 'TCTL.DESC')
    event_code_name = FCmp(EpicsSignalRO, _trig_base + 'EC_NAME')
    enable = FCmp(EpicsSignal, _trig_base + 'TCTL')
    acquire = FCmp(EpicsSignal, '{self.prefix}:CTRL.IP{self.ch}E')
    polarity = FCmp(EpicsSignal, _trig_base + 'TPOL')
    width = FCmp(EpicsSignal, _trig_base + 'BW_TWIDCALC',
                 write_pv=_trig_base + 'TWID')
    delay_ns = FCmp(EpicsSignal, _trig_base + 'BW_TDES',
                    write_pv=_trig_base + 'TDES')
    delay_ticks = FCmp(EpicsSignal, _trig_base + 'BW_TDLY',
                       write_pv='{self.prefix}:CTRL.DG{self.ch}D')
    count = FCmp(EpicsSignalRO, _trig_base + 'CNT')
    rate = FCmp(EpicsSignalRO, _trig_base + 'RATE')

    def __init__(self, prefix, channel, *, read_attrs=None,
                 configuration_attrs=None, name=None, parent=None, **kwargs):
        self.ch = channel
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, name=name,
                         parent=parent, **kwargs)
