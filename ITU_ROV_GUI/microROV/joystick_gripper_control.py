
import pygame
import time
from threading import Thread
from threading import Timer
import os
import socket

def scale(joy_val, max):
    return int(round((joy_val+1)/2.0*max))

class Joy():
    def __init__(self):
        try:
            self.pressed_buttons = []
            self.pygame = pygame
            self.pygame.init()
            self.clock = pygame.time.Clock()
            self.pygame.joystick.init()
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.axes = self.joystick.get_numaxes()  # num of axes
            self.buttons = self.joystick.get_numbuttons()  # num of buttons
            self.hats = self.joystick.get_numhats()  # num of hats
            self.clock.tick(10)  # tick per second
            self.connected = True
            self.axis_list = []
            self.pressed_buttons = []
            self.gripper_open = False
            self.gripper_close = False
            self.gripper_clockwise = False
            self.gripper_ctr_clockwise = False
            self.events = []
        except:
            self.connected = False

    def joy_get(self):
        while True:
            try:
                self.clock.tick(15)  # tick per second
                self.events = self.pygame.event.get()  # get joystick event
                self.which_button()
            except pygame.error:
                return False

    def which_button(self):
        self.pressed_buttons = []
        for i in range(self.buttons):
            if self.joystick.get_button(i) == 1:
                print(i)
        for event in self.events:
            if event.type == pygame.JOYBUTTONDOWN:
                print("Button Pressed")
                if self.joystick.get_button(5):
                    self.gripper_open = True
                elif self.joystick.get_button(10):
                    self.gripper_close = True
                if self.joystick.get_button(4):
                    self.gripper_clockwise = True
                elif self.joystick.get_button(9):
                    self.gripper_ctr_clockwise = True
            elif event.type == pygame.JOYBUTTONUP:
                self.gripper_open = False
                self.gripper_close = False
                self.gripper_clockwise = False
                self.gripper_ctr_clockwise = False

    def get_hats(self):
        return self.joystick.get_hat(0)


class Server():
    def __init__(self):
        self.host = "192.168.2.1"
        self.port = 5566
        self.buffer_size = 1024
        self.axis_list = []
        self.timer = time.time()
        self.i = 0

    def ping(self):
        state = os.system("ping -c 1 raspberrypi.local") == 0
        return state

    def bind_Server(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("try to connect ___________ ServerClass")
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print("try to bind ___________ ServerClass")
            print("bind :    ", self.s.bind((self.host, self.port)))
            self.s.bind((self.host, self.port))
        except socket.error as msg:
            msg = "Bind Server error : " + str(msg)
        print("Socket bind comlete ____________ ServerClass.")

    def setupConnection(self):
        self.s.listen(1)
        print("before accept ______ ServerClass")
        comm_text = "Waiting For Connection"
        self._connection = False
        self.conn, self.address = self.s.accept()
        self.conn.settimeout(0.5)
        time.sleep(0.5)
        print( "CONNECTED")
        self.axis_list = []
        self.timer = time.time()
        print("Connected to: " + self.address[0] + ":" + str(self.address[1]))
        self._connection = True

    def dataTransfer(self):
        if self.axis_list == []:
             self.axis_list = [str.encode(chr(0))]

        for data in self.axis_list:
            try:
                self.conn.send(data)

            except BrokenPipeError as msg:
                print("thread pipe error")
                msg = "Data Transfer BrokenPipe Exception:" + str(msg)
                self.bind_Server()
                self.setupConnection()

            except Exception as msg:
                msg = "Data Transfer Exception: [FATAL]" + str(msg)

    def dataTransfer2(self, button_liste):
        
        for data in button_liste:
            try:
                print("Sending trying")
                self.conn.send(data)
                print("Sending Completed")

            except BrokenPipeError as msg:
                print("broken pipe error ")
                msg = "Data Transfer2 BrokenPipe Exception:" + str(msg)
                self.bind_Server()
                self.setupConnection()

            except Exception as msg:
                print("data transfer exception : ", msg)
                msg = "Data Transfer2 Exception: [FATAL]" + str(msg)

# Joystick
joy = Joy()
if joy.connected:
    print("JOYSTICK CONNECTED")

else:
    print("NOT CONNECTED")
    joy = Joy()
    pass

# TCP
s = Server()
s.bind_Server()
s.setupConnection()
s.axis_list = []

#Timer utility for TCP to heartbeat in every 0,07352 sec
class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
# Thread
axis_timer = RepeatTimer(0.07, s.dataTransfer)
axis_timer.start()

# Joy Thread
joy_timer = Thread(target=joy.joy_get)
joy_timer.start()

joy_axis_list = []
joy_button = []
button = '0'
key = 0

while True:
    gripper_comm = []
    if joy.connected:
        joy_axis_list = joy.axis_list
        #38 ac, 36 saat tersi, 40 kapat, 32 saat yonu
        try:
            if joy.gripper_open:
                gripper_comm.append(repr(3).encode('utf-8'))
            else:
                gripper_comm.append(repr(1).encode('utf-8'))
            if joy.gripper_close:
                gripper_comm.append(repr(4).encode('utf-8'))
            else:
                gripper_comm.append(repr(0).encode('utf-8'))
            if joy.gripper_clockwise:
                gripper_comm.append(repr(5).encode('utf-8'))
            else:
                gripper_comm.append(repr(7).encode('utf-8'))
            if joy.gripper_ctr_clockwise:
                gripper_comm.append(repr(6).encode('utf-8'))
            else:
                gripper_comm.append(repr(8).encode('utf-8'))
            s.dataTransfer2(gripper_comm)
        except Exception as e:
            print(str(e))
            pass
    else:
        pass

    """
    try:
        s.dataTransfer2(repr(button).encode('utf-8'))
    except Exception as e:
        print(str(e))
        pass
    """
    # JOYSTICK END --------------------------------------------------
