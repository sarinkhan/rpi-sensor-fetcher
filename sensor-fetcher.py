#!/usr/bin/env python3

"""
This program fetches data from sensors and insert them in a database.

It will read the database configuration in the config file and use this as
a database, and will use the sensors definied in the config file and read
those. Then it will insert all values read in the database, and quit.
This behaviour is meant for a use of the program with crontabs.
"""

import subprocess
import pymysql
import signal
import time
import yaml
import datetime as dt
import sys
from w1thermsensor import W1ThermSensor
import board
import busio
import adafruit_tsl2561


if(len(sys.argv) != 2):
    print("ERROR: path of a config required file as first argument.")
    cmdname = sys.argv[0]
    print(f"example : {cmdname} config.yml", )
    exit(0)

with open(r'config.yml') as file:
    config = yaml.full_load(file)

DB_TYPE = config['DATABASE']['DB_TYPE']
DB_HOST = config['DATABASE']['DB_HOST']
DB_USER = config['DATABASE']['DB_USER']
DB_PASSWORD = config['DATABASE']['DB_PASSWORD']
DB_TABLE = config['DATABASE']['DB_TABLE']

SENSORS_POLL_DELAY = config['general']['SENSORS_POLL_DELAY']
SENSORS_POLL_AMOUNT = config['general']['SENSORS_POLL_AMOUNT']


def ds18b20_temperature(probeid):
    """
    Fetch the temperature of the ds18b20 specified.

    Given the probe id, it will return the temperature of this specific
    ds18b20.
    """
    sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, probeid)
    return sensor.get_temperature()


def bme280_temperature(probeid):
    """
    Get temperature from the first BME280 probe, in celcius.

    This method will return the temperature of the first BME280 probe found,
    later on adresses to select will be added, as for now it is 0x27.
    """
    output = subprocess.check_output("/home/pi/.local/bin/read_bme280\
     --temperature | cut -f3 -d' '", shell=True).decode('utf-8')
    return float(output)


def bme280_humidity(probeid):
    """
    Get relative  humidity from the first bme280, in %RH.

    This method will return the relative humidity of the first BME280 probe
    found, later on adresses to select will be added, as for now it is 0x27.
    """
    output = subprocess.check_output("/home/pi/.local/bin/read_bme280\
     --humidity | cut -f3 -d' '", shell=True).decode('utf-8')
    return float(output)


def bme280_pressure(probeid):
    """
    Get the atmospheric pressure from the first bme280, in hPa.

    This method will return the atmospheric pressure of the first BME280 probe
    found, later on adresses to select will be added, as for now it is 0x27.
    """
    output = subprocess.check_output("/home/pi/.local/bin/read_bme280\
     --pressure | cut -f1 -d' '", shell=True).decode('utf-8')
    return float(output)


def tsl2561_illuminance(probeid, gain=0, integ_time=1):
    """
    Get the illuminance pressure from the first tsl2561, in lux.

    This method will return the illuminance of the first tsl2561 probe
    found, later on adresses to select will be added, as for now it is 0x27.
    If the sensor is saturated, it returns the max +1 (40001);
    if it is underexposed, it returns 0.
    """
    tsl.enabled = True
    time.sleep(0.1)
    # Set gain 0=1x, 1=16x
    tsl.gain = gain
    # Set integration time (0=13.7ms, 1=101ms, 2=402ms, or 3=manual)
    tsl.integration_time = integ_time

    # Get raw (luminosity) readings individually
    broadband = tsl.broadband
    infrared = tsl.infrared

    lux = tsl.lux
    if lux is not None:
        return round(lux, 2)
    else:
        # if night time
        if(dt.datetime.now().hour >= config['general']['SUNSET'] or
           dt.datetime.now().hour <= config['general']['SUNRISE']):
            return 0  # return lowest possible value
        # if daytime
        else:
            return 40001  # return max value +1


def insert_measure(value, sensor_id):
    """
    Insert a measure in the database.

    It will insert the "value" for the sensor whose id is "sensor_id", using
    the current timestamp.
    """
    # Open database connection
    try:
        db = pymysql.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_TABLE)
        # prepare a cursor object using cursor() method
        cursor = db.cursor()
    except Exception:
        print("failed to connect to DB, skipping.")
        return None

    req = "INSERT INTO `measures` (`id`, `value`, `sensor_id`, `ts`) VALUES\
     (NULL, '"+str(value)+"', '"+str(sensor_id)+"', current_timestamp()); "
    try:
        # Execute the SQL command
        cursor.execute(req)
        # Commit your changes in the database
        db.commit()
        print("insert successful")
    except Exception:
        # Rollback in case there is any error
        print("insert failed")
        db.rollback()
    db.close()


def insert_node_measures():
    """
    Gather and insert the measures for the current node.

    This method will gather all sensors data from the configured sensors, and
    then insert the values in the database according to config.
    """
    for sensor in config['sensors']:
        print("sensor name : ", sensor['name'])
        print("sensor type : ", sensor['sensor_type'])
        print("sensor id : ", sensor['sensor_id'])
        print("probe id : ", sensor['probe_id'])
        if(sensor['sensor_type'] == "ds18b20"):
            value = ds18b20_temperature(sensor['probe_id'])
            insert_measure(value, sensor['sensor_id'])
        elif(sensor['sensor_type'] == "bme280temperature"):
            value = bme280_temperature(sensor['probe_id'])
            insert_measure(value, sensor['sensor_id'])
        elif(sensor['sensor_type'] == "bme280humidity"):
            value = bme280_humidity(sensor['probe_id'])
            insert_measure(value, sensor['sensor_id'])
        elif(sensor['sensor_type'] == "bme280pressure"):
            value = bme280_pressure(sensor['probe_id'])
            insert_measure(value, sensor['sensor_id'])
        elif(sensor['sensor_type'] == "tsl2561"):
            value = tsl2561_illuminance(sensor['probe_id'])
        print("value : ", value)


def main():
    """Insert the measures a specified number of times."""
    for i in range(SENSORS_POLL_AMOUNT-1):
        insert_node_measures()
        time.sleep(SENSORS_POLL_DELAY)
    insert_node_measures()


if __name__ == "__main__":
    # execute only if run as a script
    main()
