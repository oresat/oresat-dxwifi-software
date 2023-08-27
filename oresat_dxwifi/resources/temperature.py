# Purpose:
#       Issue: https://github.com/oresat/oresat-dxwifi-software/issues/1.
#       The temperature "read" by an NTC thermistor is calculated based on the voltage recieved at the ADC input pin.
#       The calculations are based on https://docs.google.com/document/d/16b_Qd6Pj2IAk5HQQl7JAP1T9Qd6QbKICMd-0swd9L6Y/edit
#       The resource then sends the calculated temperature to the Object Directory upon resource start. An SDO read callback is also implemented

from olaf.common.resource import Resource

from numpy import log as ln
from olaf.common.adc import Adc

class TemperatureResource(Resource):
    """Resource for getting the temperature of the NTC thermistor connected at AIN6"""

    # Olaf Constants ------------------------------------------------------------------------------

    TEMPERATURE_INDEX = 0x6001
    MOCK_ADC = False # False = real world voltage, True = fake voltage, this constant is for testing

    # Resource Related ----------------------------------------------------------------------------

    def __init__(self):
        super().__init__()
        self.index = self.TEMPERATURE_INDEX
        self.ADC = Adc(self.ADC_THERMISTOR_PIN, self.MOCK_ADC)

    def on_start(self):
        """Finds the temperature and sets the value in the Object dictionary. Sets up an SDO read callback"""
        # Not sure if an initial set temperature value is necessary here, but I suppose it doesn't hurt
        self.node.od[self.index].value = self.find_temperature()
        self.node.add_sdo_read_callback(self.index, self.on_read)

    def on_read(self, index: int, subindex: int) -> float:
        """Returns temperature value

        Args:
            index (int): Index in Object Dictionary
            subindex (int): Subindex of "index" argument

        Returns:
            float: Calculated temperature value
        """
        ret = None

        if index == self.index:
            ret = self.find_temperature()

        return ret

    # Temperature Calculation Constants -----------------------------------------------------------

    KELVIN_OFFSET = 273.15

    # Thermistor values at specific standard temperature (25 C)
    T25= 298.15 # kelvin
    R25 = 10000 # ohms

    B25 = 3435 # kelvin

    # This should be the same as the ADC_VIN value in the Adc class. This is the reference voltage
    ADC_VIN = 1.8 # volts

    # This is the pin where the resulting voltage is being read
    ADC_THERMISTOR_PIN = 6

    # Temperature Calulation Functions ------------------------------------------------------------

    def find_temperature(self) -> float:
        """Retrieves AIN6 voltage to calculate resistance and return temperature

        Returns:
            float: Calculated temperature value
        """
        temperature = None
        
        try:
            voltage = self.retrieve_input_voltage()
            resistance = self.calculate_resistance_from_voltage(voltage)
            temperature = self.calculate_temperature_from_resistance(resistance)

        except:
            # In theory this should be the only reason for an exception to occur in this situation
            print("Unable to reach ADC")

        return temperature

    def retrieve_input_voltage(self) -> float:
        """Retrieves voltage at ADC input"""
        return self.ADC.value
        
    def calculate_resistance_from_voltage(self,voltage) -> float:
        """Calculates the resistance based on the given voltage

        Args:
            voltage (float): Voltage retrieved from ADC input

        Returns:
            float: Resistance of the connected thermistor
        """
        resistance = voltage * self.R25 / (self.ADC_VIN - voltage)
        return resistance

    def calculate_temperature_from_resistance(self,resistance) -> float:
        """Calculates the temperature based on the resistance shown by the thermistor

        Args:
            resistance (float): Resistance of the connected thermistor

        Returns:
            float: Temperature of the outside environment, in celsius
        """
        temperature_in_kelvin = 1 / ( 
                            (ln(resistance/self.R25) / self.B25) 
                            + (1 / self.T25)
                        )

        temperature_in_celsius = temperature_in_kelvin - self.KELVIN_OFFSET 

        return temperature_in_celsius
