from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import encode_ieee, decode_ieee, long_list_to_word, word_list_to_long


c = ModbusClient(host="192.168.42.45", port=502, unit_id=1, auto_open=True)
c.open()

d = ModbusClient(host="192.168.42.45", port=502, unit_id=200, auto_open=True)

if c.write_multiple_registers(1210, [6,0]):
    print('ok')
else:
    print("write error")
regs = c.read_holding_registers(1210, 2)
regs

regs = d.read_holding_registers(168, 1)
[decode_ieee(f) for f in word_list_to_long(regs)]



import time

while True:
    updated = c.write_float(1210, [7.0])
    if updated:
        time.sleep(30)



from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils


class FloatModbusClient(ModbusClient):
    def read_float(self, address, number=1):
        reg_l = self.read_holding_registers(address, number * 2)
        if reg_l:
            return [utils.decode_ieee(f) for f in utils.word_list_to_long(reg_l)]
        else:
            return None
    def write_float(self, address, floats_list):
        b32_l = [utils.encode_ieee(f) for f in floats_list]
        b16_l = utils.long_list_to_word(b32_l)
        return self.write_multiple_registers(address, b16_l)


c = FloatModbusClient(host="192.168.42.45", port=502, unit_id=1, auto_open=True)

# write 10.0 at @0
c.write_float(0, [10.0])

# read @0 to 9
float_l = c.read_float(0, 10)
print(float_l)