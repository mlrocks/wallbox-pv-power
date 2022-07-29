from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import encode_ieee, decode_ieee, long_list_to_word, word_list_to_long


class FloatModbusClient(ModbusClient):
    def read_float(self, address, number=1):
        reg_l = False
        while not reg_l:
            reg_l = self.read_holding_registers(address, number * 2)
        if reg_l:
            return [decode_ieee(f) for f in word_list_to_long(reg_l)]
        else:
            return None

    def write_float(self, address, floats_list):
        """Write float(s) with write multiple registers."""
        b32_l = [encode_ieee(f) for f in floats_list]
        b16_l = long_list_to_word(b32_l)
        reg_w = False
        while not reg_w:
            reg_w = self.write_multiple_registers(address, b16_l)
        return reg_w