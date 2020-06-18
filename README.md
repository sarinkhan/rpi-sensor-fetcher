# what is this program?
This program is made to querry the specified sensors on your raspberry pi to
gather measurements and then store those values in the specified database.

# how to use
## create the configuration file
There are two main sections to setup in the configuration file, described below.
### database configuration
For **MySQL** or **MariaDB**, you can configure it as follows :
```
DATABASE:
  DB_TYPE: mysql
  DB_HOST: mysql_server_host
  DB_USER: database_user
  DB_PASSWORD: database_password
  DB_TABLE: database_table
```

Support for **InfluxDB** and **SQLite** will be added later.

### Sensors configuration
You need to have a section listing each sensor you want to querry.
For each sensor, you need to have a block such as this one :
```
  - name: sakura-temp
    sensor_id: 51
    probe_id: 000005d267c7
    sensor_type: ds18b20
    sensor_class: temperature
```
* name is indicative, and helps the user to remember which sensor is which,
but is not used by the program;
* sensor_id value must correspond to the sensor id of this sensor in your
database (not the measurement id);
* probe_id is the id of the physical sensor (the unique id of the sensor for
a ds18b20, or the i2c adress for an I2C sensor);
* sensor_type tells the program what type of sensor you want to read, and
the word must be a keyword in the list below, among supported sensors;
* sensor_class is indicative for now, but shall be used later. It tells what
type of measure the sensor provides.

The sensors list must be formated properly as yaml. Here is an example :
```
sensors:
  - name: sakura-temp
    sensor_id: 51
    probe_id: 000005d267c7
    sensor_type: ds18b20
    sensor_class: temperature
  - name: guppy-tank-temp
    sensor_id: 52
    probe_id: 0215c23e8fff
    sensor_type: ds18b20
    sensor_class: temperature
  - name: snow-white-temp
    sensor_id: 53
    probe_id: 0316842ceeff
    sensor_type: ds18b20
    sensor_class: temperature
  - name: fishroom-temp
    sensor_id: 1
    probe_id: 0x76
    sensor_type: bme280temperature
    sensor_class: temperature
  - name: fishroom-pressure
    sensor_id: 2
    probe_id: 0x76
    sensor_type: bme280pressure
    sensor_class: atmo-pressure
  - name: fishroom-temp
    sensor_id: 3
    probe_id: 0x76
    sensor_type: bme280humidity
    sensor_class: humidity
```


## launch the script using the config file
To launch the script , simply launch it with as an argument the configuration
file :
`./sensor-fetcher.py /path/to/config.yml`

for each sensor, you will see the value reported and also if the database insert
was successfull or not.

## create a cron job to launch it at regular interval
after checking that the script runs properly, use `crontab -e` , and add
this (edited) line :
```
/path/to/sensor-fetcher.py /path/to/config.yml
```
