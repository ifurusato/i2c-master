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

from .i2c_master import I2CMaster

class TinyS3Controller(I2CMaster):
    I2C_BUS_ID  = 1
    I2C_ADDRESS = 0x45
    '''
    Extends I2CMaster to remote control an ESP32-S3.
    ''' 
    def __init__(self, i2c_id=None, i2c_address=None, timeset=True):
        I2CMaster.__init__(self, 
            i2c_bus_id  = i2c_id if i2c_id is not None else self.I2C_BUS_ID,
            i2c_address = i2c_address if i2c_address is not None else self.I2C_ADDRESS,
            timeset=timeset
        )

#EOF
