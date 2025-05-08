'''
MTK3333 gps driver ( also used on UltimateGPS from adafruit).
This specific setup is for a raspberry pi with 40 pin header, but should 
usable on any installation by changing the SERIAL_PORT and BAUD_RATE.
UART needs to be enabled.

Calling the "process_gps_data()" funcrtion returns the following;
valid, lat, lon, speed_knots, course, date_time

valid only reports if the gps data is valid or not. 1 = yes, 0 = no.

If desired or needed you can process GPGGA or GPGLL by adding an if statement similar to what 
is on line 64. Look on the web for examples of the nmea sentence strucure.

'''

import serial
from datetime import datetime, time

# Specify the serial port to use.
SERIAL_PORT = "/dev/ttyS0"
BAUD_RATE = 9600


def parse_nmea(sentence):
    """Basic NMEA sentence parser"""
    if not sentence.startswith('$') or '*' not in sentence:
        return None

    # Validate checksum
    try:
        data, checksum = sentence.split('*')
        calculated = 0
        for char in data[1:]:  # Skip initial $
            calculated ^= ord(char)
        if int(checksum, 16) != calculated:
            return None
    except e:
        return None

    fields = data.split(',')
    return {
        'type': fields[0][1:],  # Remove leading $
        'fields': fields[1:],
        'full': sentence
    }

def process_gps_data():
    # reads and processes gps information
    ser = serial.Serial( SERIAL_PORT , BAUD_RATE, timeout=1)
    buffer = ""

    try:
        while True:
            # Read raw data
            raw = ser.read(ser.in_waiting or 1).decode('ascii', errors='ignore')
            buffer += raw

            # Process complete sentences
            while '\r\n' in buffer:
                sentence, buffer = buffer.split('\r\n', 1)
                parsed = parse_nmea(sentence.strip())
                if parsed:
                    if parsed['type'] == 'GPRMC': # Recommended minimum data
                        '''
                        Order of data in 'fields';
                        fields =    0        1       2     3      4     5     6     7      8       9         10       11       12
                        GPRMC,<Timestamp>,<Status>,<Lat>,<N/S>,<Long>,<E/W>,<SOG>,<COG>,<Date>,<MagVar>,<MagVarDir>,<mode>,<NavStatus>
                        '''
                        try:
                            time = datetime.strptime(parsed['fields'][0], '%H%M%S.%f').time() if parsed['fields'][0] else None
                            valid = 1 if parsed['fields'][1] else 0
                            lat = convert_coord(parsed['fields'][2], parsed['fields'][3]) if parsed['fields'][2] else None
                            lon = convert_coord(parsed['fields'][4], parsed['fields'][5]) if parsed['fields'][4] else None
                            speed_knots = float(parsed['fields'][6]) if parsed['fields'][6] else None
                            course = float(parsed['fields'][7]) if parsed['fields'][7] else None
                            date = datetime.strptime(parsed['fields'][8], '%m%d%y').date()
                            date_time = datetime.combine(date, time)
                            return valid, lat, lon, speed_knots, course, date_time
                        except:
                            print("Error")
                            pass
                    
    except KeyboardInterrupt:
        ser.close()

def convert_coord(coord, direction):
    """Convert NMEA coordinate to decimal degrees"""
    if not coord or not direction:
        return None
    degrees = float(coord[:2]) if direction in ['N','S'] else float(coord[:3])
    minutes = float(coord[2 if direction in ['N','S'] else 3:])
    return round(degrees + (minutes / 60), 6) * (-1 if direction in ['S','W'] else 1)

def main():
    # This is used to demo the code and make sure the gpd is connected correctly.
    valid, lat, lon, speed_knots, course, date_time = process_gps_data()
    adj_hour = int(lon / 15)
    newhour = int(date_time.hour + adj_hour)
    if newhour < 0:
        newhour = newhour +12
    # adj_time is the local time based on your physical location/timezone, (not political time zone) 
    adj_time = time(hour=newhour, minute=date_time.minute, second=date_time.second)

    print(f"\nSpeed: {speed_knots} knots\nCourse: {course}°")
    print(f"Latitude: {lat}\nLongitude: {lon}")
    print(f"Time: {date_time} UTC")
    print(f"Local time: {adj_time}")
    print("Data valid") if valid else print("Data may be flawed")




if __name__ == "__main__":
    main()
