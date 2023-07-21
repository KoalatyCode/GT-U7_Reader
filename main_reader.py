import serial
import time
import datetime
import os
import pytz

# Create the "gps_data" folder if it doesn't exist
folder_path = "gps_data"
os.makedirs(folder_path, exist_ok=True)

# Get current date and time
current_datetime = datetime.datetime.now()

# Get the Central Time Zone
local_timezone = pytz.timezone('US/Central')

# Define the time offset
time_offset = datetime.timedelta(hours=5)

# Generate file name with current date and time
file_path = os.path.join(folder_path, current_datetime.strftime('gps_data_%Y-%m-%d_%H-%M-%S.txt'))

# Open file in append mode
file = open(file_path, 'a')

# Flag to track if a connection is found
connection_found = False

# Serial port variable
port = None

# Main loop to search for an open connection
while not connection_found:
    print('Looking for open connection...')
    for port_number in range(1, 101):
        try:
            # Configure serial port
            port_name = f'COM{port_number}'
            port = serial.Serial(port_name, 9600, timeout=1)

            line = port.readline().decode('utf-8').strip()
            if line.startswith('$GPRMC'):
                # If the connection is successful and the port has gps data,
                # set the flag and break out of the loop
                connection_found = True
                print(f'Connection made on {port_name}')
                break

        except serial.SerialException:
            # If connection fails, continue to the next port
            continue

    # Delay before attempting to connect again
    time.sleep(1)

# Connection is successful, proceed with data reading and writing

# Main loop
while True:
    try:
        # Check if it's time to save the file with a new timestamp
        current_datetime = datetime.datetime.now()
        if current_datetime.hour == 0 and current_datetime.minute == 0:
            # Close the current file
            file.close()

            # Generate new file name with updated timestamp
            file_path = os.path.join(folder_path, current_datetime.strftime('gps_data_%Y-%m-%d_%H-%M-%S.txt'))

            # Open new file in append mode
            file = open(file_path, 'a')

            print("New file created.")

        # Discard all previous lines
        port.reset_input_buffer()

        # Read data from serial port until $GPGGA or $GPRMC is encountered
        line = ""
        while not line.startswith('$GPGGA'):
            line = port.readline().decode('utf-8').strip()

        # Process GPS data
        data = line.split(',')
        if line.startswith('$GPGGA') and len(data) >= 10:
            latitude_raw = data[2]
            latitude_dir = data[3]
            longitude_raw = data[4]
            longitude_dir = data[5]
            altitude = data[9]
            num_satellites = data[7]

            # Check if latitude_raw value is empty
            if not latitude_raw:
                continue

            # Convert latitude to DD format
            latitude_deg = float(latitude_raw[:2])
            latitude_min = float(latitude_raw[2:]) / 60.0
            latitude_dd = latitude_deg + latitude_min
            if latitude_dir == 'S':
                latitude_dd *= -1

            # Convert longitude to DD format
            longitude_deg = float(longitude_raw[:3])
            longitude_min = float(longitude_raw[3:]) / 60.0
            longitude_dd = longitude_deg + longitude_min

            if longitude_dir == 'W':
                longitude_dd *= -1

            # Get current timestamp from computer time
            current_time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

            # Write data to file
            file.write(
                f"Timestamp: {current_time}, Latitude: {latitude_dd:.6f}, Longitude: {longitude_dd:.6f}, Altitude: {altitude}, Satellites: {num_satellites}\n")
            file.flush()  # Flush the buffer to ensure immediate write to file

            # Print data to console
            print(f"Timestamp: {current_time}, Latitude: {latitude_dd:.6f}, Longitude: {longitude_dd:.6f}, Altitude: {altitude}, Satellites: {num_satellites}")

            # Add a delay of 60 seconds
            time.sleep(60)

    except serial.SerialException as e:
        print(f"Serial Exception occurred: {str(e)}")
        # Handle the exception here, e.g., reconnect to the serial port or perform necessary actions

        # Write a line to the file indicating the exception
        current_time = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"Exception occurred at {current_time}: {str(e)}\n")
        file.flush()  # Flush the buffer to ensure immediate write to file

        # Close the current file
        file.close()

        # Reset the flag
        connection_found = False

        # Main loop to search for a new open connection
        while not connection_found:
            print('Looking for a new connection...')
            for port_number in range(1, 101):
                try:
                    # Configure serial port
                    port_name = f'COM{port_number}'
                    port = serial.Serial(port_name, 9600, timeout=1)

                    line = port.readline().decode('utf-8').strip()
                    if line.startswith('$GPRMC'):
                        # If the connection is successful and the port has gps data,
                        # set the flag and break out of the loop
                        connection_found = True
                        print(f'Connection made on {port_name}')
                        break

                except serial.SerialException:
                    # If connection fails, continue to the next port
                    continue

            # Delay before attempting to connect again
            time.sleep(1)

        # Generate new file name with updated timestamp
        file_path = os.path.join(folder_path,
                                 datetime.datetime.now(tz=local_timezone).strftime('gps_data_%Y-%m-%d_%H-%M-%S.txt'))

        # Re-open the file in append mode
        file = open(file_path, 'a')
        print("Connection re-established.")

# Close file and serial port
file.close()
port.close()
