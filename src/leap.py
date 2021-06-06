import serial
import time
import re
from loguru import logger
import sys

logger.add(sys.stderr, format="{message}", level="DEBUG")

# USB device
#   Product ID:	0x6001
#   Vendor ID:	0x0403  (Future Technology Devices International Limited)
#   Version:	6.00
#   Serial Number:	A506FZBO
#   Speed:	Up to 12 Mb/s
#   Manufacturer:	FTDI
#   Location ID:	0x14120000 / 2
#   Current Available (mA):	500
#   Current Required (mA):	90
#   Extra Operating Current (mA):	0


class Sensor():
    def __init__(self):
        self.factor = 1000
        self.BATTERY_MIN = 2457
        self.BATTERY_MAX = 3440

        # serial connection with settings
        self.conn = serial.Serial(
            port='/dev/tty.usbserial-A506FZBO',
            baudrate=460800,
            timeout=None,  # infinite read timeout
            write_timeout=None,  # infinite write timeout
            bytesize=8,  # data bits per byte
            parity='N',  # parity checking NONE
            stopbits=1,  # one stop bits
            xonxoff=0,  # software flow control OFF
            rtscts=0)  # hardware (RTS/CTS) flow control OFF

    # byte array command with LF and NL characters

    def send_command(self, cmd):
        logger.info(f"Input: {cmd}")
        self.conn.write(cmd)
        readOut = self.conn.readline()
        logger.info(f"Output: {readOut}")
        return readOut

    def check_battery(self):
        self.send_command(b'meas:batt?\r\n')

    def get_stream_method(self):
        self.send_command(b'conf:stream:meth?\r\n')

    def set_stream_method(self, ascii=True):
        if ascii:
            # ascii stream
            self.send_command(b'conf:stream:meth 0\r\n')
        else:
            # binary stream
            self.send_command(b'conf:stream:meth 1\r\n')

    def set_stream(self, stream=False):
        if stream:
            self.send_command(b'stream:bank1 1\r\n')
        else:
            self.send_command(b'stream:bank1 0\r\n')

    def get_stream(self):
        self.send_command(b'stream:bank1?\r\n')

    def set_packet_size(self, size=3):
        self.send_command(b'conf:bank1:pack ' + str(size).encode() + b'\r\n')

    def measure_capacitance(self, channel=1):
        self.send_command(b'meas:ch' + str(channel).encode() + b':cap?\r\n')

    def read_stream(self):
        values = self.conn.readline().decode("utf-8")
        values = list(
            map(lambda v: int(v) / self.factor,
                re.sub("[^0-9^ ]", "", values).split()))
        ch1_values = values[0::2]
        ch2_values = values[1::2]
        return ch1_values, ch2_values


def record_stream(sensor, num_samples, num_packets=5):
    data = []
    sensor.set_packet_size(num_packets)
    sensor.set_stream(0)
    sensor.set_stream(1)
    for i in range(num_samples // num_packets):
        ch1, ch2 = sensor.read_stream()
        data += ch1
    sensor.set_stream(0)
    average = sum([int(c) for c in data]) / (num_samples)
    return average


def calibrate(sensor):
    logger.info("GET SET")
    time.sleep(2)
    logger.info("BREATHE IN")
    time.sleep(2)
    logger.info("HOLD")
    avg_ins = record_stream(sensor, 100)
    logger.info("Mean: ", avg_ins)

    logger.info("GET SET")
    time.sleep(2)
    logger.info("BREATHE OUT")
    time.sleep(2)
    logger.info("HOLD")
    avg_exp = record_stream(sensor, 100)
    logger.info(f"Mean: {avg_exp}")

    return avg_ins, avg_exp


def data_puller(data_q, msg_q):
    sensor = Sensor()
    sensor.set_stream(1)
    while msg_q.empty():
        ch1, ch2 = sensor.read_stream()
        for v in ch1:
            # poor man's ring buffer
            # clear the queue of old stuff
            while data_q.qsize() > 10:
                data_q.get()
            data_q.put(v)
    logger.info(f"MESSAGE: {msg_q.get()}")
    sensor.set_stream(0)


if __name__ == '__main__':
    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    sensor = Sensor()
    baseline = calibrate(sensor)
    logger.info(baseline)
    # print("START")
    # sensor.set_stream(1)
    # for i in range(100):
    #     ch1, ch2 = sensor.read_stream()
    #     for v1, v2 in zip(ch1, ch2):
    #         print((v1 - baseline))
    # sensor.get_stream()
    # sensor.set_stream(0)
    # sensor.get_stream()
