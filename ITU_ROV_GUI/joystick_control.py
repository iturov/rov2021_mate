import pygame
import time
from threading import Thread
from threading import Timer
import os
import socket


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
                print("Button Pressed")
                if self.joystick.get_button(1):
                    self.gripper_open = True
                    print("gripper açık")
                elif self.joystick.get_button(2):
                    self.gripper_close = True
                    print("gripper kapalı")
                if self.joystick.get_button(3):
                    self.fener_ac = True
                    print("fener açık")
                elif self.joystick.get_button(5):
                    self.fener_kapa = True
                    print("fener kapalı")
            elif event.type == pygame.JOYBUTTONUP:
                self.gripper_open = False
                self.gripper_close = False
                self.fener_ac = False
                self.fener_kapa = False

    def which_axes(self):
        # İLERİ GERİ SAĞ SOL HAREKETLERİ
        self.axes = self.joystick.get_numaxes()
        msg = ""
        for i in range(self.axes):
            self.axis = self.joystick.get_axis(i)
            #print(self.axis)
            msg = msg + "Axis {} value: {:>6.3f}    ". format(i, self.axis)
        # print(msg)
        """
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
        """

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

# Joy Thread
joy_timer = Thread(target=joy.joy_get)
joy_timer.start()

joy_axis_list = []
joy_button = []
button = '0'
key = 0

