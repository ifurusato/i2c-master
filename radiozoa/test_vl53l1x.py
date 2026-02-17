#!/micropython
# -*- coding: utf-8 -*-
#
# diagnostic test script for VL53L1X sensor

import sys
import time
import gc
from machine import I2C, Pin
from vl53l1x import VL53L1X

for mod in ['vl53l1x', 'vl_test']:
    if mod in sys.modules:
        del sys.modules[mod]
gc.collect()

print('cleared.')

def detailed_sensor_check(sensor):
    '''check sensor registers and state'''
    print("\n=== Detailed Sensor Diagnostics ===")
    
    try:
        # check sensor ID
        sensor_id = sensor.get_sensor_id()
        print("sensor ID: 0x{:04X} (expected 0xEEAC)".format(sensor_id))
        if sensor_id != 0xEEAC:
            print("  WARNING: Unexpected sensor ID!")
        
        # check boot state
        boot_state = sensor.boot_state()
        print("boot state: {} (1=booted, 0=not booted)".format(boot_state))
        
        # check distance mode
        distance_mode = sensor.get_distance_mode()
        print("distance mode: {} (1=short, 2=long)".format(distance_mode))
        
        # check timing budget
        timing_budget = sensor.get_timing_budget_in_ms()
        print("timing budget: {}ms".format(timing_budget))
        
        # check if data is ready
        data_ready = sensor.check_for_data_ready()
        print("data ready: {} (1=ready, 0=not ready)".format(data_ready))
        
        # check range status
        range_status = sensor.get_range_status()
        print("range status: {} (0=good)".format(range_status))
        
        # check signal rate
        signal_rate = sensor.get_signal_rate()
        print("signal rate: {} kcps".format(signal_rate))
        
        # check ambient rate
        ambient_rate = sensor.get_ambient_rate()
        print("ambient rate: {} kcps".format(ambient_rate))
        
        # check SPAD count
        spad_count = sensor.get_spad_nb()
        print("SPAD count: {}".format(spad_count))
        
    except Exception as e:
        print("error in diagnostics: {}".format(e))
        sys.print_exception(e)

def test_manual_ranging(sensor):
    '''manually step through the ranging process'''
    print("\n=== Manual Ranging Test ===")
    
    try:
        print("1. starting ranging...")
        sensor.start_ranging()
        time.sleep_ms(200)
        
        print("2. waiting for data ready...")
        timeout = 0
        while not sensor.check_for_data_ready():
            time.sleep_ms(10)
            timeout += 10
            if timeout > 2000:
                print("  TIMEOUT waiting for data ready!")
                sensor.stop_ranging()
                return
            if timeout % 200 == 0:
                print("  still waiting... ({}ms)".format(timeout))
        
        print("3. data ready! reading distance...")
        distance = sensor.get_distance()
        print("  raw distance: {}mm".format(distance))
        
        # get additional info
        range_status = sensor.get_range_status()
        signal_rate = sensor.get_signal_rate()
        
        print("  range status: {}".format(range_status))
        print("  signal rate: {} kcps".format(signal_rate))
        
        print("4. clearing interrupt...")
        sensor.clear_interrupt()
        
        print("5. stopping ranging...")
        sensor.stop_ranging()
        
        print("\nmanual ranging complete.")
        
    except Exception as e:
        print("error in manual ranging: {}".format(e))
        sys.print_exception(e)
        sensor.stop_ranging()

def test_raw_distance_register(sensor):
    '''directly read the distance register'''
    print("\n=== Raw Register Read Test ===")
    
    try:
        sensor.start_ranging()
        time.sleep_ms(200)
        
        # wait for data
        timeout = 0
        while not sensor.check_for_data_ready():
            time.sleep_ms(10)
            timeout += 10
            if timeout > 2000:
                print("timeout waiting for data")
                sensor.stop_ranging()
                return
        
        # read raw distance
        distance = sensor.get_distance()
        print("raw distance value: {}mm (0x{:04X})".format(distance, distance))
        
        # check if it's a valid range
        if distance == 0:
            print("  WARNING: distance is 0!")
            print("  possible causes:")
            print("    - sensor not properly initialized")
            print("    - no target in range")
            print("    - sensor configuration issue")
        elif distance >= 8190:
            print("  WARNING: distance at max/error value")
            print("  possible causes:")
            print("    - no target detected")
            print("    - target out of range")
        else:
            print("  distance looks valid")
        
        sensor.clear_interrupt()
        sensor.stop_ranging()
        
    except Exception as e:
        print("error reading register: {}".format(e))
        sys.print_exception(e)

def test_repeated_reads(sensor):
    '''take multiple readings with full diagnostics'''
    print("\n=== Repeated Readings Test ===")
    
    try:
        sensor.start()
        time.sleep_ms(100)
        
        for i in range(10):
            print("\nreading {}:".format(i+1))
            
            # check data ready
            ready = sensor.check_for_data_ready()
            print("  data ready: {}".format(ready))
            
            # wait if not ready
            if not ready:
                timeout = 0
                while not sensor.check_for_data_ready():
                    time.sleep_ms(10)
                    timeout += 10
                    if timeout > 500:
                        print("  timeout!")
                        break
                print("  waited {}ms".format(timeout))
            
            # read distance
            distance = sensor.get_distance()
            range_status = sensor.get_range_status()
            signal = sensor.get_signal_rate()
            
            print("  distance: {}mm".format(distance))
            print("  status: {}".format(range_status))
            print("  signal: {} kcps".format(signal))
            
            sensor.clear_interrupt()
            time.sleep_ms(100)
        
        sensor.stop()
        
    except Exception as e:
        print("error in repeated reads: {}".format(e))
        sys.print_exception(e)
        sensor.stop()

def main():
    print("VL53L1X Diagnostic Test")
    print("=" * 50)
    
    try:
        # initialize I2C
        print("\ninitializing I2C...")
        i2c = I2C(1, scl=Pin(9), sda=Pin(8), freq=400_000)
        
        devices = i2c.scan()
        print("I2C devices found: {}".format([hex(d) for d in devices]))
        
        if 0x29 not in devices:
            print("\nERROR: Sensor not found at 0x29")
            return
        
        # create sensor with debug enabled
        print("\ninitializing sensor with debug enabled...")
        sensor = VL53L1X(i2c, address=0x29, distance_mode=2, 
                        timing_budget_ms=100, debug=True)
        
        # run diagnostics
        detailed_sensor_check(sensor)
        test_raw_distance_register(sensor)
        test_manual_ranging(sensor)
        test_repeated_reads(sensor)
        
        print("\n" + "=" * 50)
        print("diagnostics complete")
        
    except Exception as e:
        print("\nerror: {}".format(e))
        sys.print_exception(e)

#if __name__ == "__main__":
main()

#EOF
