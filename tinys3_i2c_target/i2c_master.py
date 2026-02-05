#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2025-11-16
# modified: 2026-02-05

import time
from datetime import datetime as dt, timezone
import smbus2

from .message_util import pack_message, unpack_message

class I2CMaster:
    I2C_BUS_ID  = 1     # the I2C bus number; on a Raspberry Pi the default is 1
    I2C_ADDRESS = 0x43  # the default I2C address
    WRITE_READ_DELAY_SEC = 0.011 # this may need adjusting for packet length and reliability
    '''
    Abstract base class for an I2C master controller.
    '''
    def __init__(self, i2c_bus_id=None, i2c_address=None, timeset=True):
        self._i2c_bus_id  = i2c_bus_id if i2c_bus_id else I2CMaster.I2C_BUS_ID
        self._i2c_address = i2c_address if i2c_address else I2CMaster.I2C_ADDRESS
        self._enabled = False
        self._timeset = timeset
        self._fail_on_exception = False
        try:
            print('opening I2C bus {} at address {:#04x}'.format(self._i2c_bus_id, self._i2c_address))
            self._bus = smbus2.SMBus(self._i2c_bus_id)
            print('ready.')
        except Exception as e:
            print('ERROR: {} raised opening smbus: {}'.format(type(e), e))
            raise

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def set_fail_on_exception(self, fail):
        self._fail_on_exception = fail

    def _i2c_write_and_read(self, out_msg):
        if out_msg is None:
            raise ValueError('null message.')
        elif len(out_msg) == 0:
            print('WARNING: did not send empty message.')
            return
        # write command to register 0
        msg_with_addr = [0x00] + list(out_msg)
        write_msg = smbus2.i2c_msg.write(self._i2c_address, msg_with_addr)
        self._bus.i2c_rdwr(write_msg)
        time.sleep(I2CMaster.WRITE_READ_DELAY_SEC)
        # write register address 0, then read
        write_addr = smbus2.i2c_msg.write(self._i2c_address, [0x00])
        read_msg = smbus2.i2c_msg.read(self._i2c_address, 64)
        self._bus.i2c_rdwr(write_addr, read_msg)
        resp_buf = list(read_msg)
        if resp_buf and len(resp_buf) >= 2:
            msg_len = resp_buf[0]
            if 1 <= msg_len <= 62:
                return bytes(resp_buf[:msg_len+2])
        raise RuntimeError("bad message length or slave not ready.")

    def send_request(self, message):
        '''
        Send a message and return the response.
        '''
        if self._enabled:
            if message.startswith('time set'):
#               now = dt.now() # as local time
                now = dt.now(timezone.utc) # as UTC time
                print('setting time to: {}'.format(now.isoformat()))
                ts = now.strftime("%Y%m%d-%H%M%S")
                message = message.replace("now", ts)
            out_msg = pack_message(message)
            try:
                resp_bytes = self._i2c_write_and_read(out_msg)
                response = unpack_message(resp_bytes)
                return response
            except Exception as e:
                print('ERROR: {} raised by send request: {}'.format(type(e), e))
                if self._fail_on_exception:
                    raise
                return None
            finally:
                # don't repeat too quickly
                time.sleep(0.05)
        else:
            print('WARNING: cannot send request: disabled.')

    def enable(self):
        '''
        Enable the I2CMaster.
        '''
        if not self._enabled:
            self._enabled = True
            time.sleep(0.3)
            if self._timeset:
                print('setting RTC time…')
                self.send_request('time set now')
        else:
            print('WARNING: already enabled.')

    def disable(self):
        '''
        Disable the I2CMaster.
        '''
        if self._enabled:
            self._enabled = False
        else:
            print('WARNING: already disabled.')

    def close(self):
        '''
        Disable and close the I2CMaster.
        '''
        if not self.closed:
            self.disable()
            self._bus.close()
        else:
            print('WARNING: already closed.')

#EOF
