import cv2
import numpy as np
import math
import time
import uinput
# from pymavlink import mavutil

font = cv2.FONT_HERSHEY_SIMPLEX


class RovDrive:
    def __init__(self):
        self.joystick = None
        self.min_value = -100
        self.max_value = 100
        self.mid_value = int((self.max_value + self.min_value) / 2)
        self.is_rov_armed = False

        self.events = (uinput.ABS_X + (self.min_value, self.max_value, 0, 0),
                       uinput.ABS_Y + (self.min_value, self.max_value, 0, 0),
                       uinput.ABS_BRAKE + (self.min_value, self.max_value, 0, 0),
                       uinput.ABS_DISTANCE + (self.min_value, self.max_value, 0, 0),
                       uinput.ABS_GAS + (self.min_value, self.max_value, 0, 0),
                       uinput.ABS_THROTTLE + (self.min_value, self.max_value, 0, 0),
                       uinput.ABS_PRESSURE + (self.min_value, self.max_value, 0, 0),
                       uinput.BTN_0, uinput.BTN_1, uinput.BTN_2, uinput.BTN_3,
                       uinput.BTN_4, uinput.BTN_5, uinput.BTN_6, uinput.BTN_7,
                       uinput.BTN_8, uinput.BTN_9, uinput.BTN_A, uinput.BTN_B,
                       uinput.BTN_C, uinput.BTN_X, uinput.BTN_Y, uinput.BTN_Z,
                       uinput.BTN_TOP, uinput.BTN_TOP2)

        self.axis_0 = uinput.ABS_X
        self.axis_1 = uinput.ABS_Y
        self.axis_2 = uinput.ABS_THROTTLE
        self.axis_3 = uinput.ABS_GAS
        self.axis_4 = uinput.ABS_BRAKE
        self.axis_5 = uinput.ABS_PRESSURE
        self.axis_6 = uinput.ABS_DISTANCE

        self.button_0 = uinput.BTN_TOP
        self.button_1 = uinput.BTN_TOP2
        self.button_2 = uinput.BTN_A
        self.button_3 = uinput.BTN_B
        self.button_4 = uinput.BTN_C
        self.button_5 = uinput.BTN_X
        self.button_6 = uinput.BTN_Y
        self.button_7 = uinput.BTN_Z
        self.button_8 = uinput.BTN_0
        self.button_9 = uinput.BTN_1
        self.button_10 = uinput.BTN_2
        self.button_11 = uinput.BTN_3
        self.button_12 = uinput.BTN_4
        self.button_13 = uinput.BTN_5
        self.button_14 = uinput.BTN_6
        self.button_15 = uinput.BTN_7
        self.button_16 = uinput.BTN_8
        self.button_17 = uinput.BTN_9

    def connect_joystick(self):
        self.joystick = uinput.Device(self.events, name="python-joystick")
        time.sleep(0.5)
        self.joystick.emit(self.axis_0, self.mid_value, syn=False)
        self.joystick.emit(self.axis_1, self.mid_value, syn=False)
        self.joystick.emit(self.axis_2, self.mid_value, syn=False)
        self.joystick.emit(self.axis_3, self.mid_value, syn=False)
        self.joystick.emit(self.axis_4, self.mid_value, syn=False)
        self.joystick.emit(self.axis_5, self.mid_value, syn=False)
        self.joystick.emit(self.axis_6, self.mid_value)

    def disconnect_joystick(self):
        self.joystick.destroy()

    def configure_joystick(self):
        print("Configuration started")
        while True:
            key = input()
            if key == "c":
                print("Configuration ended")
                break

            if key == "w":
                self.forward(30)
            elif key == "s":
                self.forward(-30)
            else:
                self.forward(self.mid_value)

            if key == "a":
                self.lateral(-30)
            elif key == "d":
                self.lateral(30)
            else:
                self.lateral(self.mid_value)

            if key == "q":
                self.yaw(-30)
            elif key == "e":
                self.yaw(30)
            else:
                self.yaw(self.mid_value)

            if key == "f":
                self.altitude(-37)
            elif key == "r":
                self.altitude(30)
            else:
                self.altitude(self.mid_value)

            if key == "z":
                self.joystick.emit(self.axis_0, self.mid_value)
                self.joystick.emit(self.axis_1, self.mid_value)
                self.joystick.emit(self.axis_2, self.mid_value)
                self.joystick.emit(self.axis_6, self.mid_value)

            self.joystick.emit(self.axis_3, self.mid_value)
            self.joystick.emit(self.axis_4, self.mid_value)
            self.joystick.emit(self.axis_5, self.mid_value)

    def arm_rov(self):
        self.is_rov_armed = True
        self.joystick.emit(self.button_11, 0)
        self.joystick.emit(self.button_12, 1)

    def disarm_rov(self):
        self.is_rov_armed = False
        self.joystick.emit(self.button_12, 0)
        self.joystick.emit(self.button_11, 1)

    def forward(self, value):
        value = -1 * value
        self.joystick.emit(self.axis_1, value)

    def lateral(self, value):
        self.joystick.emit(self.axis_0, value)

    def yaw(self, value):
        self.joystick.emit(self.axis_2, value)

    def altitude(self, value):
        self.joystick.emit(self.axis_6, value)


class LineDetect:
    """
    def mavlink_connection(self):
        self.master = mavutil.mavlink_connection('udpin:0.0.0.0:15000')
        self.master.wait_heartbeat()

        self.master.arducopter_arm()
    """
    def __init__(self):
        # self.mavlink_connection()                     # Create Mavlink Connection
        self.rov_drive = RovDrive()
        # self.rov_drive.connect_joystick()

        self.image_read = 1
        self.__blue_lower = np.array([100, 50, 70], np.uint8)
        self.__blue_upper = np.array([140, 250, 250], np.uint8)         ##mask values for blue lines

        self.__min_red1 = np.array([123, 30, 30], np.uint8)
        self.__max_red1 = np.array([10, 250, 250], np.uint8)            ##mask values for red lines
        self.__min_red2 = np.array([140, 30, 30], np.uint8)
        self.__max_red2 = np.array([180, 250, 250], np.uint8)

        # For Mapping
        self.yellow_square = cv2.imread("yellow_square.png")
        self.red_star = cv2.imread("red_star.png")
        self.empty_box = cv2.imread("empty.png")

        self.mapping_screen = np.zeros((900, 450, 3), dtype=np.uint8)
        self.mapping_screen[:] = [255, 255, 255]

        self.mapping_x_pixel = 90
        self.mapping_y_pixel = 810

    def operation(self, frame):
        self.frame = frame
        self.canvas = np.copy(self.frame)
        self.roi_frame = np.copy(self.frame)

        (self.height, self.width, _) = frame.shape
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        self.blue_mask = cv2.inRange(hsv, self.__blue_lower, self.__blue_upper)
        #red_mask1 = cv2.inRange(hsv, self.__min_red1, self.__max_red1)
        self.red_mask2 = cv2.inRange(hsv, self.__min_red2, self.__max_red2)
        #self.red_mask = cv2.bitwise_or(red_mask1, self.red_mask2)

        #self.masked_frame = cv2.bitwise_and(frame, frame, mask=self.blue_mask)
        #self.red_masked_frame = cv2.bitwise_and(frame, frame, mask=self.red_mask)
        #cv2.imshow("Red mask", self.red_masked_frame)

    def line_detect(self):
        self.horizontal_lines = np.zeros((self.height, self.width),dtype=np.uint8)
        self.vertical_lines = np.zeros((self.height, self.width), dtype=np.uint8)

        red_lines = cv2.HoughLinesP(self.red_mask2, 1, np.pi / 180, 50, None, 50, 10)
        blue_lines = cv2.HoughLinesP(self.blue_mask, 1, np.pi / 180, 50, None, 50, 10)
        if blue_lines is not None:
            for i in range(0, len(blue_lines)):
                l = blue_lines[i][0]
                if round(l[2] - l[0], 4) <= 0.001:
                    theta = 90                        ## if block to find  angle
                else:
                    m = (l[3] - l[1]) / (round(l[2] - l[0], 4))
                    theta = math.atan(m) * 180 / 3.14


                if theta > 60 or theta < -60:           ##  if block for drawing vertical lines
                    cv2.line(self.vertical_lines, (l[0], l[1]), (l[2], l[3]), (255, 255, 255), 3, cv2.LINE_AA)

        if red_lines is not None:
            for i in range(0, len(red_lines)):
                l = red_lines[i][0]
                if round(l[2] - l[0], 4) <= 0.001:
                    theta = 90                        ## if block to find  angle
                else:
                    m = (l[3] - l[1]) / (round(l[2] - l[0], 4))
                    theta = math.atan(m) * 180 / 3.14


                if theta < 40 and theta > -40:           ##  if block for drawing vertical lines
                    cv2.line(self.horizontal_lines, (l[0], l[1]), (l[2], l[3]), (255, 255, 255), 3, cv2.LINE_AA)

    def contour_operation(self):
        two_rect = list()     ## two biggest rectangle that is found out via contour operation
        ver_cnts, _ = cv2.findContours(self.vertical_lines, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]
        self.horiz_cnts, _ = cv2.findContours(self.horizontal_lines, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]
        self.ver_cnt_len = len(ver_cnts)

        if ver_cnts is not None:
            if self.ver_cnt_len >= 2:
                ver_cnts = sorted(ver_cnts, key=cv2.contourArea, reverse=True)[:2] ## in terms of contour area , we pick two biggest contour

                # Blue Rectangle Center
                M1 = cv2.moments(ver_cnts[0])
                self.cx1 = int(M1['m10'] / M1['m00'])
                self.cy1 = int(M1['m01'] / M1['m00'])

                M2 = cv2.moments(ver_cnts[1])
                self.cx2 = int(M2['m10'] / M2['m00'])
                self.cy2 = int(M2['m01'] / M2['m00'])

                # The cordinates points of two biggest contour
                self.distance_x = abs(self.cx1 - self.cx2) # ## distance between x-axis
                #print(self.cx1, self.cx2, self.distance_x, sep="\t\t")


                cv2.circle(self.canvas, (self.cx1, self.cy1), 3, (255, 255, 0), -1)
                cv2.circle(self.canvas, (self.cx2, self.cy2), 3, (255, 255, 0), -1)

                for cnt in ver_cnts:         ## for loop to encapsulate the contours  in terms of area
                    rect = cv2.minAreaRect(cnt)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)    # detect four corner of rectangle

                    two_rect.append(box)
                    cv2.drawContours(self.canvas, [box], 0, (0, 0, 255), 2)

                if two_rect[0][0][0] > two_rect[1][0][0]:  # comparing x values and detect which one is left side and which one is right sided
                    placeholder = two_rect[1]
                    two_rect[1] = two_rect[0]
                    two_rect[0] = placeholder

                try:
                    self.left_angle, self.right_angle = self.find_angle_box_two_rect(two_rect, self.canvas)
                except:
                    pass

            elif self.ver_cnt_len == 1: ## if one line is detected
                M1_one_side = cv2.moments(ver_cnts[0])
                self.cx1_one_side = int(M1_one_side['m10'] / M1_one_side['m00'])
                self.cy1_one_side = int(M1_one_side['m01'] / M1_one_side['m00'])
                for cnt in ver_cnts:
                    rect = cv2.minAreaRect(cnt)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    cv2.drawContours(self.canvas, [box], 0, (0, 0, 255), 2)
                    self.one_rect_angle, self.one_rect_side = self.find_angle_box_one_rect(box, self.canvas)
        ##############################
        raw_h_box = list()
        if self.horiz_cnts is not None:
            for cnt in self.horiz_cnts:  ## for loop to encapsulate the contours  in terms of area
                h_rect = cv2.minAreaRect(cnt)
                h_box = cv2.boxPoints(h_rect)
                h_box = np.int0(h_box)  # detect four corner of rectangle
                raw_h_box.append(h_box)
                #cv2.drawContours(self.frame, [h_box], 0, (0, 255, 255), 5)
            for i in range(len(raw_h_box)):
                for j in range(len(raw_h_box)):
                    if not self.same_bounding_rect(raw_h_box[i], raw_h_box[j]):
                        if raw_h_box[i][0][1]+30 > raw_h_box[j][0][1] and raw_h_box[i][0][1]-30 < raw_h_box[j][0][1]:
                            raw_h_box[i], raw_h_box[j] = self.conc_bounding_rect(raw_h_box[i], raw_h_box[j])
            i = 0
            try:
                while True:
                    if raw_h_box[i][0][0] == 0 and raw_h_box[i][0][1] == 0 and raw_h_box[i][1][0] == 0 and raw_h_box[i][1][1] == 0:
                        raw_h_box.pop(i)
                        i -= 1
                    i += 1
                    if i >= len(raw_h_box):
                        break
            except:
                pass

            for h_box in raw_h_box:
                i = np.int0(h_box)
                cv2.drawContours(self.canvas, [i], 0, (255, 255, 0), 2)

    def drive_rotation(self):
        self.rotation_information = np.zeros((200, 300, 3), dtype=np.uint8)

        self.drive_yaw_degree = 0

        if self.left_angle < 0:
            self.left_angle = 180 - abs(self.left_angle)

        if self.right_angle < 0:
            self.right_angle = 180 - abs(self.right_angle)


        print("--------------------------------\n")
        if self.ver_cnt_len >= 2: #if two or more line are detected

            if self.right_angle - self.left_angle > 3:
                cv2.putText(self.rotation_information, "Turn Right", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)
                self.drive_yaw_degree = 1

            elif self.right_angle - self.left_angle > 5:
                cv2.putText(self.rotation_information, "Turn Right", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)
                self.drive_yaw_degree = 2

            elif self.left_angle - self.right_angle > 3:
                cv2.putText(self.rotation_information, "Turn Left", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)
                self.drive_yaw_degree = -1

            elif self.left_angle - self.right_angle > 5:
                cv2.putText(self.rotation_information, "Turn Left", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)
                self.drive_yaw_degree = -2
            else:
                cv2.putText(self.rotation_information, "Straight", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)
                self.drive_yaw_degree = 0

        elif self.ver_cnt_len == 1: # if one line is  detected
            if self.one_rect_angle < 0 and self.one_rect_side == 0:
                cv2.putText(self.rotation_information, "Turn Left", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)

            elif self.one_rect_angle < 0 and self.one_rect_side == 1:
                cv2.putText(self.rotation_information, "Turn Left", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)

            elif self.one_rect_angle < 85 and self.one_rect_side == 0:
                cv2.putText(self.rotation_information, "Turn Right", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)

            elif self.one_rect_angle < 85 and self.one_rect_side == 1:
                cv2.putText(self.rotation_information, "Turn Right", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)
            else:
                cv2.putText(self.rotation_information, "Straight", (0, 50), font, 1, (0, 250, 0), cv2.LINE_4)

    def drive_altitude(self):
        self.drive_height_degree = 0
        print(self.distance_x)
        try:
            if self.distance_x < 440: # if distance between x-axis is smaller than 440
                print("degree -1")
                #cv2.putText(self.rotation_information, "Down", (0, 150), font, 1, (0, 250, 0), cv2.LINE_4)
                self.drive_height_degree = -1
            elif self.distance_x > 460:     # if distance between x-axis is bigger than 510
                #cv2.putText(self.rotation_information, "Up", (0, 150), font, 1, (0, 250, 0), cv2.LINE_4)
                self.drive_height_degree = 1
                print("degree 1")
            else:
                self.drive_height_degree=0
                print("degree 0")
                #cv2.putText(self.rotation_information, "Straight", (0, 150), font, 1, (0, 250, 0), cv2.LINE_4)
        except:
            print("yükseklik except")
            pass

    def drive_yaw(self):
        if self.ver_cnt_len >= 2: # if two or more line are detected, we decide the yaw movement in terms of left center
            if self.cx1 < self.cx2: # if cx2 is on the right
                self.left_center_x =self.cx1

            elif self.cx2 <= self.cx1:
                self.left_center_x =self.cx2

            if self.left_center_x < 30:
                cv2.putText(self.rotation_information, "Yaw Left", (0, 250), font, 1, (0, 250, 0), cv2.LINE_4)

            elif self.left_center_x > 100:
                cv2.putText(self.rotation_information, "Yaw Right", (0, 250), font, 1, (0, 250, 0), cv2.LINE_4)

            else:
                cv2.putText(self.rotation_information, "Straight", (0, 250), font, 1, (0, 250, 0), cv2.LINE_4)

        elif self.ver_cnt_len == 1:
            if self.one_rect_side== 0:  ##for left line
                self.left_center_x= self.cx1_one_side

                if self.left_center_x < 30:
                    cv2.putText(self.rotation_information, "Yaw Left", (0, 250), font, 1, (0, 250, 0), cv2.LINE_4)

                elif self.left_center_x > 100:
                    cv2.putText(self.rotation_information, "Yaw Right", (0, 250), font, 1, (0, 250, 0), cv2.LINE_4)

                else:
                    cv2.putText(self.rotation_information, "Straight", (0, 250), font, 1, (0, 250, 0), cv2.LINE_4)

            else:
                self.right_center_x= self.cx1_one_side


                if self.right_center_x < 540:
                        cv2.putText(self.rotation_information, "Yaw Left", (0, 250), font, 1, (0, 250, 0), cv2.LINE_4)

                elif self.right_center_x > 610:
                    cv2.putText(self.rotation_information, "Yaw Right", (0, 250), font, 1, (0, 250, 0), cv2.LINE_4)

                else:
                    cv2.putText(self.rotation_information, "Straight", (0, 250), font, 1, (0, 250, 0), cv2.LINE_4)

        # Bunlar kenardaki dikdörtgenler - Aybala
        cv2.rectangle(self.canvas, (30,0), (100, 480),(255, 0, 0), 2)
        cv2.rectangle(self.canvas, (540, 0), (610, 480), (255, 0, 0), 2)

    def mapping(self):
        try:
            if self.horiz_cnts is not None:
                M1 = cv2.moments(self.horiz_cnts[0])
                self.cx1_horizontal = int(M1['m10'] / M1['m00'])
                self.cy1_horizontal = int(M1['m01'] / M1['m00'])
                i = 1
                while True:
                    M2 = cv2.moments(self.horiz_cnts[i])
                    self.cx2_horizontal = int(M2['m10'] / M2['m00'])
                    self.cy2_horizontal = int(M2['m01'] / M2['m00'])
                    i += 1
                    if self.cy1_horizontal - 30 > self.cy2_horizontal:
                        break

                cv2.circle(self.canvas, (self.cx1_horizontal, self.cy1_horizontal), 5, (255, 255, 255), -1)
                cv2.circle(self.canvas, (self.cx2_horizontal, self.cy2_horizontal), 5, (0, 0, 0), -1)


                if self.cx1 > self.cx2:
                    self.cx1, self.cx2 = self.cx2, self.cx1
                    self.cy1, self.cy2 = self.cy2, self.cy1

                x = self.cx2 - self.cx1
                x = int(x / 3)

                if self.image_read == 1:
                    if 390 < self.cy1_horizontal < 430:
                        self.image_read = 0
                        self.left_bot = self.roi_frame[ self.cy1_horizontal-150:self.cy1_horizontal, self.cx1:self.cx1+x]
                        self.center_bot = self.roi_frame[ self.cy1_horizontal-150:self.cy1_horizontal, self.cx1+x:self.cx2-x]
                        self.right_bot = self.roi_frame[self.cy1_horizontal-150:self.cy1_horizontal, self.cx2-x:self.cx2]
                        self.box_list = [self.left_bot, self.center_bot, self.right_bot]
                        self.printmap()

                if 470 < self.cy1_horizontal:
                    self.image_read = 1
        except:
            pass

    def printmap(self):
        self.min_star_red= np.array([0, 220, 200], np.uint8)
        self.max_star_red = np.array([10, 255, 255], np.uint8)
        self.min_square_yellow= np.array([10, 150, 200], np.uint8)
        self.max_square_yellow = np.array([30, 199, 255], np.uint8)

        for box in self.box_list:
            box = cv2.cvtColor(box, cv2.COLOR_BGR2HSV)


            red_mask = cv2.inRange(box, self.min_star_red, self.max_star_red)
            yellow_mask =cv2.inRange(box, self.min_square_yellow, self.max_square_yellow)

            red_cnt, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]
            yellow_cnt, _ = cv2.findContours(yellow_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]

            if len(red_cnt):
                self.mapping_screen[self.mapping_y_pixel : self.mapping_y_pixel + 90, self.mapping_x_pixel : self.mapping_x_pixel + 90] = self.red_star
            elif len(yellow_cnt):
                self.mapping_screen[self.mapping_y_pixel : self.mapping_y_pixel + 90, self.mapping_x_pixel : self.mapping_x_pixel + 90] = self.yellow_square
            else:
                self.mapping_screen[self.mapping_y_pixel : self.mapping_y_pixel + 90, self.mapping_x_pixel : self.mapping_x_pixel + 90] = self.empty_box

            self.mapping_x_pixel += 90

        self.mapping_x_pixel = 90
        self.mapping_y_pixel -= 90

    def show(self):
        cv2.imshow("frame", self.frame)
        #cv2.imshow("Vertical Blue", self.vertical_lines)
        #cv2.imshow("Horizontal", self.horizontal_lines)        # Red Lines
        cv2.imshow("Mapping", self.mapping_screen)
        cv2.imshow("Canvas", self.canvas)
        cv2.imshow("Rotation Info", self.rotation_information)

    def drive(self):
        # self.drive_forward = 500
        # self.drive_lateral = 500
        # self.drive_upDown = 500
        # self.drive_yaw = 500
        #self.rov_drive.altitude(-80)

        # self.drive_yaw_degree = 3
        self.drive_height_degree = 3
        self.rov_drive.altitude(-37)

        if self.drive_yaw_degree == 2:
            # Sağa Yaw
            self.rov_drive.yaw(20)
            self.rov_drive.forward(50)
            # self.drive_yaw = 650
            # self.drive_forward = 550

        elif self.drive_yaw_degree == 1:
            # Hafif Sağa Yaw
            self.rov_drive.yaw(10)
            self.rov_drive.forward(30)
            # self.drive_yaw = 550
            # self.drive_forward = 650

        elif self.drive_yaw_degree == 0:
            # Düz
            self.rov_drive.yaw(0)
            self.rov_drive.forward(70)
            # self.drive_forward = 700

        elif self.drive_yaw_degree == -1:
            # Hafif Sola Yaw
            self.rov_drive.yaw(-10)
            self.rov_drive.forward(30)
            # self.drive_yaw = 450
            # self.drive_forward = 650

        elif self.drive_yaw_degree == -2:
            # Sola Yaw
            self.rov_drive.yaw(-20)
            self.rov_drive.forward(50)
            # self.drive_yaw = 350
            # self.drive_forward = 550

        elif self.drive_height_degree == 1:
            print("yukarı çıkıyom")
            self.rov_drive.altitude(-40)
            # self.drive_upDown = 600

        elif self.drive_height_degree == -1:
            print("aşağı iniyom")
            self.rov_drive.altitude(-70)
            # self.drive_upDown = 400

        elif self.drive_height_degree == 0:
            print("hop burdayım")
            self.rov_drive.altitude(-50)
            # self.drive_upDown = 500

        """
        self.master.mav.manual_control_send(
            self.master.target_system,
            self.drive_forward,  # forward
            self.drive_lateral,  # lateral
            self.drive_upDown,  # up-down
            self.drive_yaw,  # yaw
            0)
        """

    def same_bounding_rect(self, x, y):
        for i in range(4):
            for j in range(2):
                if x[i][j] != y[i][j]:
                    return False
        return True

    def conc_bounding_rect(self, x, y):
        dots = list()
        edges = list()
        edges.extend(x)
        edges.extend(y)

        sortFirst = lambda x: x[0]
        edges_left = sorted(edges, key=sortFirst, reverse=False)[:2]
        edges_right = sorted(edges, key=sortFirst, reverse=False)[6:8]

        if edges_left[0][1] > edges_left[1][1]:
            bot_left = edges_left[0]
            top_left = edges_left[1]
        else:
            top_left = edges_left[0]
            bot_left = edges_left[1]

        if edges_right[0][1] > edges_right[1][1]:
            bot_right = edges_right[0]
            top_right = edges_right[1]
        else:
            top_right = edges_right[0]
            bot_right = edges_right[1]

        dots.append(top_left)
        dots.append(top_right)
        dots.append(bot_right)
        dots.append(bot_left)
        zero = [[0, 0], [0, 0], [0, 0], [0, 0]]

        return dots, zero

    def find_angle_box_two_rect(self, box, canvas):  ## If two line is detected, this function returns left and right angle
        left = box[0]
        right = box[1]
        sortSecond = lambda x:x[1]
        left = sorted(left, key=sortSecond, reverse=False) ## Sort function regarding y axis
        if left[0][0] < left[1][0]:
            left_top = left[1]
        else:
            left_top = left[0]

        if left[2][0] < left[3][0]:
            left_bottom = left[3]
        else:
            left_bottom = left[2]

        cv2.circle(canvas, tuple(left_top), 3, (255,255,0),-1)    ##  it puts a dot to left top of line
        cv2.circle(canvas, tuple(left_bottom), 3, (255, 255, 0), -1) ##  it puts a dot to left bottom of line

        right = sorted(right, key=sortSecond, reverse=False) ## Sort function regarding y axis
        if right[0][0] > right[1][0]:
            right_top = right[1]
        else:
            right_top = right[0]

        if right[2][0] > right[3][0]:
            right_bottom = right[3]
        else:
            right_bottom = right[2]

        cv2.circle(canvas, tuple(right_top), 3, (255,255,0),-1)          ##  it puts a dot to right top of line
        cv2.circle(canvas, tuple(right_bottom), 3, (255, 255, 0), -1)  ##  it puts a dot to right bottom of line

        left_cotangent = (left_top[0] - left_bottom[0]) / (left_bottom[1] - left_top[1] ) # it finds cotangent for left line
        right_cotangent = (right_bottom[0] - right_top[0]) / (right_bottom[1] - right_top[1]) # it finds cotangent for right line

        left_degree = math.degrees((math.atan(1/left_cotangent)))   # it shows that the angle value of cotangent of left line
        right_degree = math.degrees((math.atan(1/right_cotangent))) # it shows that the angle value of cotangent of right line

        return left_degree, right_degree

    def find_angle_box_one_rect(self, box, canvas):  # If one line is detected ,
        # first we detect the side of line and then we find the angle of line,
        # finally it returns side and degree
        side = 0  # 0 -> Left, 1-> Right
        sortSecond = lambda x: x[1]
        if (box[0][0] < 320):  # if line is on the left side
            box = sorted(box, key=sortSecond, reverse=False)
            if box[0][0] < box[1][0]:
                box_top = box[1]
            else:
                box_top = box[0]
            if box[2][0] < box[3][0]:
                box_bottom = box[3]
            else:
                box_bottom = box[2]
            cv2.circle(canvas, tuple(box_top), 3, (255, 255, 0), -1)  ##  it puts a dot to top of the line
            cv2.circle(canvas, tuple(box_bottom), 3, (255, 255, 0), -1)  ##  it puts a dot to bottom of the line

            box_cotangent = (box_top[0] - box_bottom[0]) / (box_bottom[1] - box_top[1])
            box_degree = math.degrees((math.atan(1 / box_cotangent)))
        else:  # if line is on the right side
            if box[0][0] > box[1][0]:
                box_top = box[1]
            else:
                box_top = box[0]

            if box[2][0] > box[3][0]:
                box_bottom = box[3]
            else:
                box_bottom = box[2]

            cv2.circle(canvas, tuple(box_top), 3, (255, 255, 0), -1)
            cv2.circle(canvas, tuple(box_bottom), 3, (255, 255, 0), -1)

            box_cotangent = (box_bottom[0] - box_top[0]) / (box_bottom[1] - box_top[1])
            box_degree = math.degrees((math.atan(1 / box_cotangent)))
            side = 1

        return box_degree, side

# Video üzerinde çalışan hali
"""
if __name__ == "__main__":

    cap = cv2.VideoCapture("/home/ibrahim/Masaüstü/rov_videolar/rovvideo2.avi")
    # ret, frame = cap.read()
    line_detect = LineDetect()

    while True:
        ret, frame = cap.read()
        if not ret:
            cv2.waitKey(0)
            break

        # frame = cv2.rotate(frame, cv2.cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.resize(frame, (640, 480))
        line_detect.operation(frame)
        line_detect.line_detect()
        line_detect.contour_operation()
        line_detect.mapping()
        line_detect.drive_rotation()
        line_detect.drive_altitude()
        line_detect.drive_yaw()
        line_detect.show()
        line_detect.drive()

        if cv2.waitKey(10) & 0xFF == ord("q"):
            break
"""

# RovDrive konfigürasyonu

if __name__ == "__main__":
    rov_drive = RovDrive()
    rov_drive.connect_joystick()
    rov_drive.arm_rov()
    rov_drive.configure_joystick()
    rov_drive.disarm_rov()
    rov_drive.disconnect_joystick()
