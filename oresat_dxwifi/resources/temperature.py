# Purpose:
#       The contents of this file solve: https://github.com/oresat/oresat-dxwifi-software/issues/1.
#       The temperature "read" by an NTC thermistor is calculated based on the voltage recieved at the ADC input pin.
#       The calculations of this file are based on https://docs.google.com/document/d/16b_Qd6Pj2IAk5HQQl7JAP1T9Qd6QbKICMd-0swd9L6Y/edit
#       The resource then sends the calculated temperature to the Object Directory upon resource start. An SDO read callback is also implemented

from olaf.common.resource import Resource

from numpy import log as ln
from olaf.common.adc import Adc

# Olaf Constants ----------------------------------------------------------------------------------

TEMPERATURE_INDEX = 0x6001

# Olaf Related Components -------------------------------------------------------------------------

class TemperatureResource(Resource):
    '''Resource for getting the temperature of the NTC thermistor connected at AIN6'''

    def __init__(self):
        super().__init__()
        self.index = TEMPERATURE_INDEX

    def on_start(self):
        # Not sure if an initial set temperature value is necessary here, but I suppose it doesn't hurt
        self.node.od[self.index].value = find_temperature()

        self.node.add_sdo_read_callback(self.index, self.on_read)
        # self.node.add_sdo_write_callback(self.index, self.on_write) # To be uncommented when necessary and properly implemented

    def on_read(self, index: int, subindex: int):

        ret = None

        if index != self.index:
            return ret
        
        ret = find_temperature()

    # As far as I can tell, the write callback will add the data into the OD
    # Not sure if the precedent here is to provide the data on the call, or just retrieve it
    def on_write(self, index: int, subindex: int, data):
        ret = None

        if index != self.index:
            return ret
        
        ret = data
        

# Temperature Calculation Constants ---------------------------------------------------------------

KELVIN_OFFSET = 273.15

# Thermistor values at specific standard temperature (25 C)
T25= 298.15 # kelvin
R25 = 10000 # ohms

B25 = 3435 # kelvin

# This should be the same as the ADC_VIN value in the Adc class. This is the reference voltage
ADC_VIN = 1.8 # volts

# This is the pin where the resulting voltage is being read
ADC_THERMISTOR_PIN = 6

# Temperature Calulation Functions ----------------------------------------------------------------

def find_temperature():
    
    temperature = None
    
    try:
        voltage = retrieve_input_voltage()
        resistance = calculate_resistance_from_voltage(voltage)
        temperature = calculate_temperature_from_resistance(resistance)

    except:
        # In theory this should be the only reason for an exception to occur in this situation
        print("Unable to reach ADC")

    return temperature

def retrieve_input_voltage():
    ADC = Adc(ADC_THERMISTOR_PIN)
    return ADC.value
    
def calculate_resistance_from_voltage(voltage):
    resistance = voltage * R25 / (ADC_VIN - voltage)
    return resistance

def calculate_temperature_from_resistance(resistance):
    temperature_in_kelvin = 1 / ( 
                        (ln(resistance/R25) / B25) 
                        + (1 / T25)
                      )

    temperature_in_celsius = temperature_in_kelvin - KELVIN_OFFSET 

    return temperature_in_celsius