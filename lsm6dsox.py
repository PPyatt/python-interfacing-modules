'''
A class / driver for interfacing with a LSM6DSOX Accelerometer / Gyroscope and 
LIS3MDL Magnetometer / Compass based on the smbus2 module over I2C.

NOTES:
LPF - Low Pass Filter - smoothes high-frequency noise
HPF - High Pass Filter - removes DC offsets
'''

import smbus2
import struct

bus = smbus2.SMBus( bus = 1) # Initializes the I2C pins for GPIO02 SDA/GPIO03 SCL

DEVICE_ADDRESS = 0x6A

A_CALIB = 0.122 / 1000 # 16g:0.488 ; 8g:0.244 : 4g:0.122 : 2g:0.061 
G_CALIB = 35 / 1000 # 2000dps:70 ; 1000dps:35 ; 500dps:17.50 ; 250dps:8.75 ; 125dps:4.375

'''
From the manufacturer's documentation section 6 - Functionality

Acceleromter page 26.

To activate the accelerometer write " ODR_XL[3:0] " in CRTL1_XL (0x10)
Next set the operating mode of the accerlometer.
Accelerometer

The accelerometer has 5 operating modes:
0 - powered down
1 - ultralow power
2 - low power
3 - nomral
4 - high performance

High performance mode is enable when Mode4_EN = 1 in UI_CRTL1_OIS (0x70)

The output values can be read as a 2 byte word using bus.read_word_data() instead of each individually.
The values can also be read as a block using bus.read_block_data() and then unpacked into variables.

Gyroscope page 30.

To activate the gyroscope write " ODR_G[3:0] " in CTRL2_G (0x11)
Next set the operating mode of the accelerometer.

# FIFO - If reading individual registers takes to much time or resources,
    it may be better to perform one chip read from FIFO and then unpack from that.
    Otherwise skip FIFO.

The UI - OIS output register can be used also but do not seem to be as ideally suited for 
controlling balance applications (i.e. drones) according to reading materials availible.
'''

FUNC_CFG_ACCESS = 0x01
WHO_AM_I = 0x0F
CTRL1_XL = 0x10
CTRL2_G = 0x11
CTRL3_C = 0x12
CTRL4_C = 0x13
CTRL5_C = 0x14
CTRL6_C = 0x15
CTRL7_G = 0x16
CTRL8_XL = 0x17
CRTL9_XL = 0x18
CRTL10_C = 0x19

OUT_TEMP_L = 0x20
OUT_TEMP_H = 0x21
OUTX_L_G = 0x22
OUTX_H_G = 0x23
OUTY_L_G = 0x24
OUTY_H_G = 0x25
OUTZ_L_G = 0x26
OUTZ_H_G = 0x27
OUTX_L_A = 0x28
OUTX_H_A = 0x29
OUTY_L_A = 0x2A
OUTY_H_A = 0x2B
OUTZ_L_A = 0x2C
OUTZ_H_A = 0x2D

# Configuration section - The binary in the comment is the configuration needed. ( I think. )
class Lsm6dsox:
    def __init__(self):

        # Intialize the accelerometer and gyroscope.
        bus.write_byte_data( DEVICE_ADDRESS, FUNC_CFG_ACCESS, 0x00 ) # "0000 0000" 9.1 in Doc.
        bus.write_byte_data( DEVICE_ADDRESS, CTRL1_XL, 0x9A ) # "1001 1010" 9.15 in Documentation (3.33kHz HP)
        bus.write_byte_data( DEVICE_ADDRESS, CTRL6_C, 0x45 ) # "0100 0101" XL_HM_MODE = 0 - needed by CRTL1_XL
        bus.write_byte_data( DEVICE_ADDRESS, CTRL8_XL, 0xE8 ) #  "1110 1000" XL_FS_MODE = 0 - needed by CRTL1_XL
        bus.write_byte_data( DEVICE_ADDRESS, CTRL2_G, 0x98 ) # "1001 1000" ( 3.33kHz , 1000 dps )
        bus.write_byte_data( DEVICE_ADDRESS, CTRL7_G, 0x50 ) # "0101 0000"
        bus.write_byte_data( DEVICE_ADDRESS, CTRL8_XL, 0xA0 ) # "1010 0000"

    def read_lsm6dsox(self):

        # read the acceleromter and gyroscope.
        try:
            data = bytearray(bus.read_i2c_block_data( DEVICE_ADDRESS, OUT_TEMP_L, 14))
            temp, g_x, g_y, g_z, a_x, a_y, a_z = struct.unpack('<hhhhhhh', data)
            g_x = g_x * G_CALIB
            g_y = g_y * G_CALIB
            g_z = g_z * G_CALIB
            a_x = a_x * A_CALIB
            a_y = a_y * A_CALIB
            a_z = a_z * A_CALIB
            temp = ((temp / 256) + 25)*9/5+32

            return g_x, g_y, g_z, a_x, a_y, a_z, temp

        except e:
            bus.write_byte_data(DEVICE_ADDRESS, CTRL1_XL, 0x00 ) # "0000 0000" power down accelerometer
            bus.write_byte_data(DEVICE_ADDRESS, CTRL2_G, 0x00 ) # "0000 0000" power down the gyroscope

if __name__ == "__main__":
    x = 0
    while x < 10:
        demo = Lsm6dsox()
        g_x, g_y, g_z, a_x, a_y, a_z, temp = demo.read_lsm6dsox()
        print(f"Temp {temp:0.2f} F, Accel x: {a_x:<6.2f}, y: {a_y:<6.2f}, z: {a_z:<6.2f}, Gyro x: {g_x:<6.2f}, y: {g_y:6.2f}, z: {g_z:<6.2f}")
        x += 1
