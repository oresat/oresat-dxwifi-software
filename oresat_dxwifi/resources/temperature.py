# Purpose:
#       Issue: https://github.com/oresat/oresat-dxwifi-software/issues/1.
#       The temperature "read" by an NTC thermistor is calculated based on
#           the voltage recieved at the ADC input pin.
#       The calculations are based on:
#           https://gist.github.com/bpranaw/ea0a1a00b98d4be98b3d2d03dd31d530
#       The resource then sends the calculated temperature to the Object Directory upon
#           resource start. An SDO read callback is also implemented

import math as m

from olaf import Adc, Resource, logger


class TemperatureResource(Resource):
    """Resource for getting the temperature of the NTC thermistor connected at AIN6

    Attributes:
        index: The index of the temperature data in the object dictionary. OD uses hexadecimal
        adc: An instance of an olaf ADC that allows retrieval of voltage value from specified pin.
    """

    # Olaf Constants ------------------------------------------------------------------------------

    # Resource Related ----------------------------------------------------------------------------

    def __init__(self, adc_thermistor_pin: int = 6, is_mock_adc: bool = False):
        """Sets up the ADC. Inputs set which pin to use and whether the ADC is a real or mock ADC.

        Args:
            adc_thermistor_pin: Pin where the voltage is read.
            is_mock_adc: False = real world ADC, True = mock ADC.
        """
        super().__init__()

        self.adc = Adc(adc_thermistor_pin, is_mock_adc)

    def on_start(self):
        """Sets up an SDO read callback"""

        self.node.add_sdo_callbacks("radio", "temperature", self._on_read_temperature, None)

    def _on_read_temperature(self) -> int:
        """Returns temperature value

        Returns:
            ret: Calculated temperature value
        """
        ret = int(self.find_temperature())

        # The OD uses int8 for temperatures
        if not (ret >= -128 and ret <= 127):
            ret = -128
            logger.error("Temperature outside int8 range or unable to reach ADC.")

        return ret

    # Temperature Calculation Constants -----------------------------------------------------------

    KELVIN_OFFSET = 273.15  # Offset for converting from Kelvin to Celsius

    # Thermistor values at specific temperature (25 C)
    T25 = 298.15  # Temperature (Kelvin)
    R25 = 10_000  # Resistance (Ohms)
    B25 = 3435  # Beta (B) value (Kelvin)

    # Temperature Calculation Functions -----------------------------------------------------------

    def find_temperature(self) -> float:
        """Retrieves ADC PIN voltage to calculate resistance and return temperature

        Returns:
            temperature: Calculated temperature value
        """
        temperature = -1000.0

        try:
            voltage = self.adc.value
            resistance = self.calculate_resistance_from_voltage(voltage)
            temperature = self.calculate_temperature_from_resistance(resistance)
        except Exception:
            # In theory this should be the only reason for an exception to occur in this situation
            logger.error("Unable to reach ADC")

        return temperature

    def calculate_resistance_from_voltage(self, voltage: float) -> float:
        """Calculates the resistance based on the given voltage

        Args:
            voltage: Voltage retrieved from ADC input

        Returns:
            resistance: Resistance of the connected thermistor
        """
        resistance = voltage * self.R25 / (self.adc.ADC_VIN - voltage)
        return resistance

    def calculate_temperature_from_resistance(self, resistance: float) -> float:
        """Calculates the temperature based on the resistance shown by the thermistor

        Args:
            resistance: Resistance of the connected thermistor

        Returns:
            temperature_in_celsius: Temperature of the outside environment, in celsius
        """
        temperature_in_kelvin = 1 / ((m.log(resistance / self.R25) / self.B25) + (1 / self.T25))

        temperature_in_celsius = temperature_in_kelvin - self.KELVIN_OFFSET

        return temperature_in_celsius
