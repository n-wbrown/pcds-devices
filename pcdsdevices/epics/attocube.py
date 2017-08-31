#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Attocube devices
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
import numpy as np

##########
# Module #
##########
from .device import Device
from .component import Component
from .epicsmotor import EpicsMotor
from .signal import (EpicsSignal, EpicsSignalRO)

logger = logging.getLogger(__name__)


class EccController(Device):
    """
    ECC Controller
    """
    _firm_day = Component(EpicsSignalRO, ":CALC:FIRMDAY")
    _firm_month = Component(EpicsSignalRO, ":CALC:FIRMMONTH")
    _firm_year = Component(EpicsSignalRO, ":CALC:FIRMYEAR")
    _flash = Component(EpicsSignal, ":RDB:FLASH", write_pv=":CMD:FLASH")
    
    @property 
    def firmware(self):
        """
        Returns the firmware in the same date format as the EDM screen.
        """
        return "{0}/{1}/{2}".format(
            self._firm_day.value, self._firm_month.value, self._firm_year.value)
    
    @property
    def flash(self):
        """
        Saves the current configuration of the controller.
        """
        return self._flash.set(1)


class EccBase(EpicsMotor):
    """
    ECC Motor Class
    """    
    def moverel(rel_position, *args, **kwargs):
        """
        Move relative to the current position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        rel_position
            Relative position to move to

        moved_cb : callable
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance.

        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used.

        Returns
        -------
        status : MoveStatus        
        	Status object for the move.
        
        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`
        
        ValueError
            On invalid positions
        
        RuntimeError
            If motion fails other than timing out        
        """
        return self.move(rel_position + self.position, *args, **kwargs)


class TranslationEcc(EccBase):
    """
    Class for the translation ecc motor
    """
    pass


class GoniometerEcc(EccBase):
    """
    Class for the goniometer ecc motor
    """
    pass


class DiodeEcc(EccBase):
    """
    Class for the diode insertion ecc motor
    """
    pass





