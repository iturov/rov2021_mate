import pygame
import time
from threading import Thread
from threading import Timer
import os
import socket
import cv2

# This is a simple class that will help us print to the screen.
# It has nothing to do with the joysticks, just outputting the
# information.
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
            self.pwm_value = 0
            self.gripper_open = False
            self.gripper_close = False
            self.fener_ac = False
            self.fener_kapa = False
            self.ileri_git = False
            self.geri_git = False
            self.sola_don = False
            self.saga_don = False
            self.dur = False
            self.events = []
            self.axes = self.joystick.get_numaxes()
        except:
            self.connected = False

    def joy_get(self):
        while True:
            try:
                self.clock.tick(15)  # tick per second
                self.events = self.pygame.event.get()  # get joystick event
                self.which_button()
                self.which_axes()
            except pygame.error:
                return False

    def which_button(self):
        self.pressed_buttons = []

        for event in self.events:

            if event.type == pygame.JOYBUTTONDOWN:
                self.dur = False
                print("Button Pressed")
                if self.joystick.get_button(2):
                    #self.gripper_open = True
                    #print("gripper açık")
                    self.ileri_git = True
                    print("ileri git")
                if self.joystick.get_button(7):
                    #self.gripper_close = True
                    #print("gripper kapalı")
                    self.geri_git = True
                    print("geri git")
                if self.joystick.get_button(1):
                    #self.fener_ac = True
                    #print("fener açık")
                    self.sola_don = True
                    print("sola don")
                if self.joystick.get_button(6):
                    #self.fener_kapa = True
                    #print("fener kapalı")
                    self.saga_don = True
                    print("saga don")
                if self.joystick.get_button(3):
                    self.gripper_close = True
                    print("gripper kapalı")
                if self.joystick.get_button(8):
                    self.gripper_open = True
                    print("gripper açık")
            else:
                print("DUR")
                self.gripper_open = False
                self.gripper_close = False
                """
                self.fener_ac = False
                self.fener_kapa = False
                """
                self.ileri_git = False
                self.geri_git = False
                self.saga_don = False
                self.sola_don = False
                self.dur = True



    def which_axes(self):
        # İLERİ GERİ SAĞ SOL HAREKETLERİ
        self.axes = self.joystick.get_numaxes()
        for i in range(self.axes):
            self.axis = self.joystick.get_axis(i)
            # print("Axis {} value: {:>6.3f}". format(i, axis))
            if i == 0:
                # birinci eksen X ekseni

                if round((self.axis), 3) > 0.100:
                    print("sağa git")
                    self.saga_don = True
                    pwm_value = round((self.axis), 3)
                    scale()

                elif round(self.axis, 3) < -0.100:
                    print("sola git")
                    self.sola_don = True
                    pwm_value = round(self.axis, 3)
                    scale()
            elif i == 1:
                # ikinci eksen Y ekseni

                if round(self.axis, 3) < -0.100:
                    print("ileri git")
                    self.ileri_git = True
                    joy.pwm_value = round(self.axis, 3)
                    scale()
                    # iki dc motora da round(axis)'e göre oranla güç ver

                elif round(self.axis, 3) > 0.100:
                    print("geri git")
                    self.geri_git = True
                    joy.pwm_value = round(self.axis, 3)
                    scale()
                    # iki dc motora da round(axis)'e göre oranla güç ver

class Server():
    def __init__(self):
        self.host = "192.168.2.1"
        self.port = 5596
        self.buffer_size = 3
        self.axis_list = []
        self.timer = time.time()
        self.i = 0

    def ping(self):
        state = os.system("ping -c 1 raspberrypi.local") == 0
        print("ping atıldı")
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
            print("excepte girdi")
            msg = "Bind Server error : " + str(msg)
        print("Socket bind complete ____________ ServerClass.")

    def setupConnection(self):
        # self.s.bind((self.host, self.port))
        self.s.listen(1)
        print("before accept ______ ServerClass")
        comm_text = "Waiting For Connection"
        self._connection = False
        #print("acceptten once")
        self.conn, self.address = self.s.accept()
        print("accepti gectim")
        self.conn.settimeout(0.5)
        time.sleep(0.5)
        print("CONNECTED")
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
                #print("Sending trying")
                self.conn.send(data)
                #print("Sending Completed")

            except BrokenPipeError as msg:
                print("broken pipe error ")
                msg = "Data Transfer2 BrokenPipe Exception:" + str(msg)
                self.bind_Server()
                self.setupConnection()

            except Exception as msg:
                print("data transfer exception : ", msg)
                msg = "Data Transfer2 Exception: [FATAL]" + str(msg)

def scale():
    value = abs(round((joy.axis), 3))
    joy.conv_PWM = int(value * 100)
    joy.conv_PWM = joy.pwm_value




joy = Joy()
if joy.connected:
    print("JOYSTICK CONNECTED")

else:
    print("NOT CONNECTED")
    joy = Joy()
    pass

# TCP
s = Server()
s.ping()
s.bind_Server()
s.setupConnection()
s.axis_list = []


# Timer utility for TCP to heartbeat in every 0,07352 sec
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
a = 1

while a == 1:
    gripper_comm = []
    if joy.connected:
        #print(gripper_comm)
        joy_axis_list = joy.axis_list
        #print(joy_axis_list)

        try:
            gripper_comm = []
            if joy.gripper_open:
                gripper_comm.append(repr('a').encode('utf-8'))
            else:
                gripper_comm.append(repr('0').encode('utf-8'))

            if joy.gripper_close:
                gripper_comm.append(repr('b').encode('utf-8'))
            else:
                gripper_comm.append(repr('0').encode('utf-8'))
            if joy.fener_ac:
                gripper_comm.append(repr('c').encode('utf-8'))
            else:
                gripper_comm.append(repr('0').encode('utf-8'))

            if joy.fener_kapa:
                gripper_comm.append(repr('d').encode('utf-8'))
                s.conn.close()
            else:
                gripper_comm.append(repr('0').encode('utf-8'))

            if joy.ileri_git:
                gripper_comm.append(repr('e').encode('utf-8'))
            else:
                gripper_comm.append(repr('0').encode('utf-8'))

            if joy.geri_git:
                gripper_comm.append(repr('f').encode('utf-8'))
            else:
                gripper_comm.append(repr('0').encode('utf-8'))

            if joy.saga_don:
                gripper_comm.append(repr('g').encode('utf-8'))
            else:
                gripper_comm.append(repr('0').encode('utf-8'))

            if joy.sola_don:
                gripper_comm.append(repr('h').encode('utf-8'))
            else:
                gripper_comm.append(repr('0').encode('utf-8'))

            if joy.dur:
                gripper_comm.append(repr('i').encode('utf-8'))
            else:
                gripper_comm.append(repr('0').encode('utf-8'))
            time.sleep(0.02)

            """else:
                gripper_comm.append(repr('z').encode('utf-8'))"""
            #print("pwmden once")
            #gripper_comm.append(repr(joy.pwm_value).encode('utf-8'))
            #print("data transferden once")
            s.dataTransfer2(gripper_comm)
            # print(gripper_comm)

            continue

        except Exception as e:
            print(str(e))
            print("hata aldim")
            pass
    if cv2.waitKey(1) & 0xFF == ord('q'):
        a = 2


    else:
        print("baglanti hatasi")
        pass
    break
conn.close()



"""
pygame.init()

# Loop until the user clicks the close button.
done = False

# Initialize the joysticks.
pygame.joystick.init()

# -------- Main Program Loop -----------
while not done:
    #
    # EVENT PROCESSING STEP
    #
    # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
    # JOYBUTTONUP, JOYHATMOTION
    for event in pygame.event.get(): # User did something.
        if event.type == pygame.QUIT: # If user clicked close.
            done = True # Flag that we are done so we exit this loop.
        elif event.type == pygame.JOYBUTTONDOWN:
            print("Joystick button pressed.")
        elif event.type == pygame.JOYBUTTONUP:
            print("Joystick button released.")

    #
    # DRAWING STEP

    # Get count of joysticks.
    joystick_count = pygame.joystick.get_count()

    # For each joystick:
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()

        try:
            jid = joystick.get_instance_id()
        except AttributeError:
            # get_instance_id() is an SDL2 method
            jid = joystick.get_id()

        # Get the name from the OS for the controller/joystick.
        name = joystick.get_name()

        # Usually axis run in pairs, up/down for one, and left/right for
        # the other.

        # print("Number of axes: {}".format(axes))



        buttons = joystick.get_numbuttons()
        # print("Number of buttons: {}".format(buttons))


        for i in range(buttons):
            buttons = joystick.get_button(i)
            #print("Button {:>2} value: {}".format(i, button))

        if joystick.get_button(1):
            print("gripper aç")
        elif joystick.get_button(2):
            print("gripper kapa")
        elif joystick.get_button(3):
            print("fener aç")
        elif joystick.get_button(5):
            print("fener kapa")

        hats = joystick.get_numhats()
        # print("Number of hats: {}".format(hats))

        # Hat position. All or nothing for direction, not a float like
        # get_axis(). Position is a tuple of int values (x, y).
        for i in range(hats):
            hat = joystick.get_hat(i)
            # print("Hat {} value: {}".format(i, str(hat)))

# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
pygame.quit()
"""
