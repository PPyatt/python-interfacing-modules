'''
Bosch BMP390 sensor driver built around the smbus2 library for I2C.
The variables used match the ones in the Bosch documentation - bst-bmp390-ds002.pdf from Bosch.
for a 40 pin header Raspberry Pi ( 4, zero, etc..)
'''

import smbus2

bus = smbus2.SMBus( bus = 1 ) # initializes the I2C system to use GPIO02 SDA / GPIO03 SCL

DEVICE_ADDRESS = 0x77

# Register addresses for the calibration data
NVM_PAR_T1 = 0x31 # 16 bit
NVM_PAR_T2 = 0x33 # 16 bit
NVM_PAR_T3 = 0x35 #  8 bit
NVM_PAR_P1 = 0x36 # 16 bit
NVM_PAR_P2 = 0x38 # 16 bit
NVM_PAR_P3 = 0x3A #  8 bit
NVM_PAR_P4 = 0x3B #  8 bit
NVM_PAR_P5 = 0x3C # 16 bit
NVM_PAR_P6 = 0x3E # 16 bit
NVM_PAR_P7 = 0x40 #  8 bit
NVM_PAR_P8 = 0x41 #  8 bit
NVM_PAR_P9 = 0x42 # 16 bit
NVM_PAR_P10 = 0x44 # 8 bit
NVM_PAR_P11 = 0x45 # 8 bit

# Register addresses for the pressure and temperature raw data
DATA_0 = 0x04 # Pressure xlsb 8 bit
DATA_1 = 0x05 # Pressure lsb  8 bit
DATA_2 = 0x06 # Pressure msb  8 bit

DATA_3 = 0x07 # Temperature xlsb 8 bit
DATA_4 = 0x08 # Temperature lsb  8 bit
DATA_5 = 0x09 # Temperature msb  8 bit

#IIR filter - Momentary pulses in pressure compensation setting.
CONFIG = 0x1F # A setting of 2 or 4 ( 010 or 100 ) is recommended for drone applications.

# ODR - odr_sel
ODR = 0x1D # sampling rate
'''
odr_sel prescaler sampling period
0x00       1        5 ms / 200 Hz
0x01       2        10 ms/ 100 Hz
0x02       4        20 ms/ 50 Hz
0x03       8        40 ms/ 25 Hz
...
0x0A       1024     5.120 s
...
0x11       131072   655.36 s
'''

OSR = 0x1C # OSR - osr_p, osr_t - 3 bits each
'''
Oversampling setting  osr_p Press sampl Rec.Temp sampl
Ultra low power       000       x1              x1
Low power             001       x2              x1
Standard resolution   010       x4              x1
High resolution       011       x8              x1
Ultra high resolution 100       x16             x2
Highest resolution    101       x32             x2

                      osr_t Temp sampl  resolution
                      000       x1       16 bit /0.005 C
                      001       x2       17 bit /0.0025 C
                      010       x4       18 bit /0.0012 C
                      011       x8       19 bit /0.0006 C
                      100       x16      20 bit /0.0003 C
                      101       x32      21 bit /0.00015 C

When writing ODR format it as follows ( 00 osr_t osr_p ) for a total of 8 bits.
'''

# Power control / mode set
PWR_CTRL = 0x1B # 2 bits - 11, normal mode; 01 or 10, Forced mode; 00, sleep mode
# press_en is PWR_CTRL bit 0 - enables pressure measurement
# temp_en is PWR_CRTL bit 1 - enables temperature measurement

# IF_CONF is set by a physical connection on the adafruit and diymall pcb.
# FIFO not used.

class Bmp390:
    def __init__(self):
        bus.write_byte_data( DEVICE_ADDRESS, PWR_CTRL, 0x33 ) # 00110011 (reserved, normal mode, reserved, enable temp, enable press)
        self.PAR_T1 = ( bus.read_word_data( DEVICE_ADDRESS, NVM_PAR_T1 )) / (2**(-8))
        self.PAR_T2 = ( bus.read_word_data( DEVICE_ADDRESS, NVM_PAR_T2 )) / (2**(30))
        self.PAR_T3 = ( bus.read_byte_data( DEVICE_ADDRESS, NVM_PAR_T3 )) / (2**(48))
        self.PAR_P1 = ( bus.read_word_data( DEVICE_ADDRESS, NVM_PAR_P1 ) - 2**(14)) / (2**(20))
        self.PAR_P2 = ( bus.read_word_data( DEVICE_ADDRESS, NVM_PAR_P2 ) - 2**(14)) / (2**(29))
        self.PAR_P3 = ( bus.read_byte_data( DEVICE_ADDRESS, NVM_PAR_P3 )) / (2**(32))
        self.PAR_P4 = ( bus.read_byte_data( DEVICE_ADDRESS, NVM_PAR_P4 )) / (2**(37))
        self.PAR_P5 = ( bus.read_word_data( DEVICE_ADDRESS, NVM_PAR_P5 )) / (2**(-3))
        self.PAR_P6 = ( bus.read_word_data( DEVICE_ADDRESS, NVM_PAR_P6 )) / (2**(6))
        self.PAR_P7 = ( bus.read_byte_data( DEVICE_ADDRESS, NVM_PAR_P7 )) / (2**(8))
        self.PAR_P8 = ( bus.read_byte_data( DEVICE_ADDRESS, NVM_PAR_P8 )) / (2**(15))
        self.PAR_P9 = ( bus.read_word_data( DEVICE_ADDRESS, NVM_PAR_P9 )) / (2**(48))
        self.PAR_P10 = ( bus.read_byte_data( DEVICE_ADDRESS, NVM_PAR_P10 )) / (2**(48))
        self.PAR_P11 = ( bus.read_byte_data( DEVICE_ADDRESS, NVM_PAR_P11 )) / (2**(65))


    def read_temp(self):
        # Read raw temp data
        xlsb = bus.read_byte_data( DEVICE_ADDRESS, DATA_3 )
        lsb = bus.read_byte_data( DEVICE_ADDRESS, DATA_4 )
        msb = bus.read_byte_data( DEVICE_ADDRESS, DATA_5 )

        uncomp_temp = ( msb << 16 | lsb << 8 | xlsb )

        # Calculate compensated temperature.
        partial_data1 = uncomp_temp - self.PAR_T1
        partial_data2 = partial_data1 * self.PAR_T2
        temperature = partial_data2 + (( partial_data1**2) * self.PAR_T3 )

        return temperature


    def read(self):

        temperature = self.read_temp()

        # Read raw pressure data
        xlsb = bus.read_byte_data( DEVICE_ADDRESS, DATA_0 )
        lsb = bus.read_byte_data( DEVICE_ADDRESS, DATA_1 )
        msb = bus.read_byte_data( DEVICE_ADDRESS, DATA_2 )

        uncomp_press = ( msb << 16 | lsb << 8 | xlsb )

        # Calculate compensated pressure
        partial_data1 = self.PAR_P6 * temperature
        partial_data2 = self.PAR_P7 * ( temperature**2 )
        partial_data3 = self.PAR_P8 * ( temperature**3 )
        partial_out1 = self.PAR_P5 + partial_data1 + partial_data2 + partial_data3

        partial_data1 = self.PAR_P2 * temperature
        partial_data2 = self.PAR_P3 * ( temperature**2 )
        partial_data3 = self.PAR_P4 * ( temperature**3 )
        partial_out2 = uncomp_press * ( self.PAR_P1 + partial_data1 + partial_data2 + partial_data3 )

        partial_data1 = uncomp_press * uncomp_press
        partial_data2 = self.PAR_P9 + ( self.PAR_P10 * temperature )
        partial_data3 = partial_data1 * partial_data2
        partial_data4 = partial_data3 + (( uncomp_press**3 ) * self.PAR_P11 )
        pressure = partial_out1 + partial_out2 + partial_data4

        return temperature, pressure

if __name__ == "__main__":
    demo = Bmp390()
    temperature, pressure = demo.read()
    print(f" Temperature: {temperature:<5.2f} C, {temperature*9/5+32:<5.2f} F, Pressure: {pressure:<10.2f} Pa")
