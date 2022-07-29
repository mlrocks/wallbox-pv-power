# Load balancing for Alfen Wallbox to use excess PV charging with a SolarEdge inverter

This Python script uses [pyModbusTCP](https://github.com/sourceperl/pyModbusTCP) to control to the Alfen Eve Single S-line Wallbox.
(To use modbus with the Eve Single you need the licence for „Load Balancing Active“.)

The [SolarEdge Monitoring API](https://www.solaredge.com/sites/default/files/se_monitoring_api.pdf) is used the get the up-to-date values for PV production and usage.

The script calculates the power excess and regulates the wallbox to only use the excess to charge the car...

## Todo

There are a lot improvements to work on....

- Switch to ignore the SolarEdge values and charge with full power
- Calculation of available excess (moving average, ignore outliers, use weather api,...)
- ...
