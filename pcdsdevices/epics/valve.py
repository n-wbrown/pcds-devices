"""
Standard classes for LCLS Gate Valves
"""
import logging
from enum import Enum
from functools import partial

from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   FormattedComponent as FC)

from .mps import MPS, mps_factory
from ..state import PVStatePositioner

logger = logging.getLogger(__name__)


class Commands(Enum):
    """
    Command aliases for opening and closing valves
    """
    close_valve = 0
    open_valve = 1


class InterlockError(PermissionError):
    """
    Error when request is blocked by interlock logic
    """
    pass


class Stopper(PVStatePositioner):
    """
    Controls Stopper

    Similar to the :class:`.GateValve`, the Stopper class provides basic
    support for Controls stoppers i.e stoppers that can be commanded from
    outside the PPS system

    Parameters
    ----------
    prefix : str
        Full PPS Stopper PV

    name : str, optional
        Alias for the stopper
    """
    # Limit-based states
    open_limit = C(EpicsSignalRO, ':OPEN')
    closed_limit = C(EpicsSignalRO, ':CLOSE')

    # Information on device control
    command = C(EpicsSignal, ':CMD')
    commands = Commands

    _state_logic = {'open_limit': {0: 'defer',
                                   1: 'OUT'},
                    'closed_limit': {0: 'defer',
                                     1: 'IN'}}

    def _do_move(self, state):
        if state.name == 'IN':
            self.command.put(self.commands.close_valve.value)
        elif state.name == 'OUT':
            self.command.put(self.commands.open_valve.value)

    def open(self, wait=False, timeout=None):
        """
        Open the stopper

        Parameters
        ----------
        wait : bool, optional
            Wait for the command to finish

        timeout : float, optional
            Default timeout to wait mark the request as a failure

        Returns
        -------
        StateStatus:
            Future that reports the completion of the request
        """
        return self.move('OUT', wait=wait, timeout=timeout)

    def close(self, wait=False, timeout=None):
        """
        Close the stopper

        Parameters
        ----------
        wait : bool, optional
            Wait for the command to finish

        timeout : float, optional
            Default timeout to wait mark the request as a failure

        Returns
        -------
        StateStatus:
            Future that reports the completion of the request
        """
        return self.move('IN', wait=wait, timeout=timeout)

    # Lightpath Interface
    def insert(self, *args, **kwargs):
        """
        Alias for :meth:`.close` for lightpath interface
        """
        return self.close(*args, **kwargs)

    def remove(self, *args, **kwargs):
        """
        Alias for :meth:`.open` for lightpath interface
        """
        return self.open(*args, **kwargs)

    @property
    def inserted(self):
        """
        Whether the stopper is in the beamline
        """
        return self.position == 'IN'

    @property
    def removed(self):
        """
        Whether the stopper is removed from the beamline
        """
        return self.position == 'OUT'


class GateValve(Stopper):
    """
    Basic Vacuum Valve

    Attributes
    ----------
    commands : Enum
        Command aliases for valve
    """
    # Limit based states
    open_limit = C(EpicsSignalRO, ':OPN_DI')
    closed_limit = C(EpicsSignalRO, ':CLS_DI')

    # Commands and Interlock information
    command = C(EpicsSignal,   ':OPN_SW')
    interlock = C(EpicsSignalRO, ':OPN_OK')

    _default_read_attrs = ['state', 'interlock']

    @property
    def interlocked(self):
        """
        Whether the interlock on the valve is active, preventing the valve from
        opening
        """
        return bool(self.interlock.get())

    def open(self, wait=False, timeout=None, **kwargs):
        """
        Open the valve

        Parameters
        ----------
        wait : bool, optional
            Wait for the command to finish

        timeout : float, optional
            Default timeout to wait mark the request as a failure

        Raises
        ------
        InterlockError:
            When the gate valve can not be opened due to a vacuum interlock

        Returns
        -------
        StateStatus:
            Future that reports the completion of the request
        """
        if self.interlocked:
            raise InterlockError('Valve is currently forced closed')

        return super().open(wait=wait, timeout=timeout, **kwargs)


MPSGateValve = partial(mps_factory, 'MPSGateValve', GateValve)
MPSStopper = partial(mps_factory, 'MPSStopper', Stopper)


class PPSStopper(Device):
    """
    PPS Stopper

    Control of this device only available to PPS systems. This class merely
    interprets the summary of limit switches to let the controls system know
    the current position

    Parameters
    ----------
    prefix : str
        Full PPS Stopper PV

    name : str, optional
        Alias for the stopper

    in_state : str, optional
        String associatted with in enum value

    out_state :str, optional
        String associatted with out enum value
    """
    summary = C(EpicsSignalRO, '')
    SUB_STATE = 'sub_state_changed'
    _default_sub = SUB_STATE

    # MPS Information
    mps = FC(MPS, '{self._mps_prefix}', veto=True)

    def __init__(self, prefix, *, name=None,
                 read_attrs=None, in_state='IN',
                 out_state='OUT', mps_prefix=None, **kwargs):
        # Store state information
        self.in_state, self.out_state = in_state, out_state
        self._has_subscribed = False
        # Store MPS information
        self._mps_prefix = mps_prefix

        if not read_attrs:
            read_attrs = ['summary']

        super().__init__(prefix,
                         read_attrs=read_attrs,
                         name=name, **kwargs)

    @property
    def inserted(self):
        """
        Inserted limit of PPS stopper
        """
        return self.summary.get(as_string=True) == self.in_state

    @property
    def removed(self):
        """
        Removed limit of the PPS Stopper
        """
        return self.summary.get(as_string=True) == self.out_state

    def subscribe(self, cb, event_type=None, run=True):
        """
        Subscribe to changes of the PPSStopper

        Parameters
        ----------
        cb : callable
            Callback to be run

        event_type : str, optional
            Type of event to run callback on

        run : bool, optional
            Run the callback immediatelly
        """
        if not self._has_subscribed:
            self.summary.subscribe(self._on_state_change, run=False)
            self._has_subscribed = True
        super().subscribe(cb, event_type=event_type, run=run)

    def _on_state_change(self, **kwargs):
        """
        Callback run on state change
        """
        kwargs.pop('sub_type', None)
        kwargs.pop('obj', None)
        self._run_subs(sub_type=self.SUB_STATE, obj=self, **kwargs)
