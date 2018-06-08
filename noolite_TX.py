# -*- coding: utf-8 -*-

import serial

class mtrf():
    
    def __init__(self):
        self.cmd = {0:"Off",
                    2:"On", 
                    6:"Dimmable"}
    
    def tx_command(channel, cmd, fmt, dat):
        port = serial.Serial("/dev/ttyUSB0", baudrate=9600, timeout=None)
        
        crc = sum([171, channel, cmd, fmt, dat])%256
    
        command = [171,0,0,0,channel,cmd,fmt,dat,0,0,0,0,0,0,0,crc,172]  
        port.write(command)
