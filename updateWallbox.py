import logging
import math
from xmlrpc.client import Boolean
import requests
import sys
import time
from clients import FloatModbusClient


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# timeout to call solaredge api in seconds
api_timeout = 330
# timeout to refresh wallbox via modbus
modbus_timeout = 30
# nr of modbus refreshes till api call
rounds_till_api_call = math.ceil(api_timeout / modbus_timeout)

# solaredge api url
api_url = "https://monitoringapi.solaredge.com/site/2095069/currentPowerFlow.json?&api_key=1B4ACT1XJ4FP1E59L94OIUSY3UTJLSY3"
# threshold in kW - when to change the current / nr. of phases
delta_power = 0.2
# threshold of consecutive violations of power treshold
delta_rounds = 2
# consecutive violations of power treshold
consecutive_violations = 0
excesses = []

# alfen wallbox modbux
c = FloatModbusClient(host="192.168.42.45", port=502, unit_id=1, auto_open=True)
c.open()

# update active values
active_current = c.read_float(1206, 1)[0]
new_current = active_current
active_phases = False
while not active_phases:
    try:
        active_phases = c.read_holding_registers(1215, 1)
    except:
        pass
active_phases = active_phases[0]
new_phases = active_phases

while True:
    # get solar edge api data
    response = requests.get(api_url)
    json = response.json()

    grid_usage = json["siteCurrentPowerFlow"]["GRID"]["currentPower"]
    pv_production = json["siteCurrentPowerFlow"]["PV"]["currentPower"]
    total_usage = json["siteCurrentPowerFlow"]["LOAD"]["currentPower"] # including wallbox (if used)

    logging.debug('GET SOLAREDGE DATA...')
    logging.debug('GRID: {}'.format(grid_usage))
    logging.debug('PV: {}'.format(pv_production))
    logging.debug('LOAD: {}'.format(total_usage))
    logging.debug('')

    # if delta is violated...do something:
    # more or less power, depeinding on average of last meassurements
    if grid_usage > delta_power:
        logging.debug('USAGE VIOLATION')
        consecutive_violations += 1
    else:
        logging.debug('NO VIOLATION')
        consecutive_violations = 0

    # get up-to-date wallbox power in kW (data in W)
    wallbox_power = False
    while wallbox_power is False:
        wallbox_power = c.read_float(344, 1)[0] / 1000
    logging.debug('WALLBOX USAGE: {}'.format(wallbox_power))

    # calculate excess without wallbox usage
    excess = pv_production - total_usage + wallbox_power
    
    excesses.insert(0, excess)
    logging.debug('EXCESS: {}'.format(excess))
    
    # excess average of last 10 meassurements
    excess_avg = sum(excesses[:2]) / len(excesses[:2])
    logging.debug('EXCESS AVERAGE: {}'.format(excess_avg))

    # voltage_1 = c.read_float(306, 1)
    # voltage_2 = c.read_float(308, 1)
    # voltage_3 = c.read_float(310, 1)
    # voltage_avg = sum(voltage_1 + voltage_2 + voltage_3) / 3
    voltage_avg = 0.23

    new_current = excess_avg / voltage_avg / active_phases

    if consecutive_violations >= delta_rounds:
        logging.debug('{} CONSECUTIVE VIOLATIONS'.format(consecutive_violations))
        if new_current < 6.1 and active_phases == 3:
            new_phases = 1
            logging.debug('NEW PHASES: {}'.format(new_phases))
            new_current = excess_avg / voltage_avg / new_phases
        elif new_current > 16.0 and active_phases == 1:
            new_phases = 3
            logging.debug('NEW PHASES: {}'.format(new_phases))
            new_current = excess_avg / voltage_avg / new_phases
        
    new_current = min(new_current, 16.0)
    if new_phases == 1:
        if new_current < 6.1:
            new_current = 0
    else:
        new_current = max(new_current, 6.1)
    
    logging.debug('NEW CURRENT: {}'.format(new_current))

    # write current and set nr of phases
    i = 0
    while i < rounds_till_api_call:
        c.write_float(1210, [new_current])
        if active_current != new_current:
            logging.debug('NEW CURRENT SET TO: {}'.format(new_current))
        else:
            logging.debug('CURRENT SET TO: {}'.format(new_current))
        active_current = new_current

        if active_phases != new_phases:
            reg_w = False
            while not reg_w:
                reg_w = c.write_multiple_registers(1215, [new_phases])
            active_phases = new_phases
            logging.debug('NEW NR OF PHASES SET TO: {}'.format(new_phases))

        i += 1
        time.sleep(30)
