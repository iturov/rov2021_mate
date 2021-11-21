import cv2
import numpy as np
import math

#Faik Eren Altun - altunf19@itu.edu.tr - eren0altun@gmail.com
class Ring:
    def __init__(self):
        cv2.namedWindow("trackbar")
        cv2.createTrackbar("Lower_H", "trackbar", 0, 179, self.nothing)
        cv2.createTrackbar("Lower_S", "trackbar", 0, 255, self.nothing)
        cv2.createTrackbar("Lower_V", "trackbar", 0, 255, self.nothing)

        cv2.createTrackbar("Upper_H", "trackbar", 0, 179, self.nothing)
        cv2.createTrackbar("Upper_S", "trackbar", 0, 255, self.nothing)
        cv2.createTrackbar("Upper_V", "trackbar", 0, 255, self.nothing)

        self.move_to_contour_flag = True
        self.counter_of_finish = 0

    def get_photo(self, img):
        (self.height, self.width, _) = img.shape
        self.frame = img

    def nothing(self, x):
        pass

    def get_trackbar_data(self):
        self.hsv_img = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)

        lh = cv2.getTrackbarPos("Lower_H", "trackbar")
        ls = cv2.getTrackbarPos("Lower_S", "trackbar")
        lv = cv2.getTrackbarPos("Lower_V", "trackbar")

        uh = cv2.setTrackbarPos("Upper_H", "trackbar", 179)
        us = cv2.setTrackbarPos("Upper_S", "trackbar", 255)
        uv = cv2.setTrackbarPos("Upper_V", "trackbar", 85)

        uh = cv2.getTrackbarPos("Upper_H", "trackbar")
        us = cv2.getTrackbarPos("Upper_S", "trackbar")
        uv = cv2.getTrackbarPos("Upper_V", "trackbar")

        self.lower_color = np.array([lh, ls, lv])
        self.upper_color = np.array([uh, us, uv])

    def detect_rings(self):
        mask = cv2.inRange(self.hsv_img, self.lower_color, self.upper_color)
        eroded = cv2.erode(mask, np.ones((11, 11), np.uint8), iterations=1)
        dilated = cv2.dilate(eroded, np.ones((11, 11), np.uint8), iterations=1)
        self.xor = cv2.bitwise_xor(mask, dilated)

    def contour_and_sort_xor(self):
        contours, im2 = cv2.findContours(self.xor, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        self.ring_contours = sorted(contours, key=cv2.contourArea, reverse=True)

    def move_to_contour(self):
        #ring contours stores 3 ring segments in sorted order.
        if len(self.ring_contours) != 0 and self.move_to_contour_flag and 600 < cv2.contourArea(self.ring_contours[0]) < 1200: #
            rect = cv2.minAreaRect(self.ring_contours[0])
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            #cv2.drawContours(frame, [box], 0, (255, 0, 255), 2)

            self.center_pt = rect[0]

            cv2.circle(self.frame, (int(self.center_pt[0]), int(self.center_pt[1])), 10, (100, 100, 255), 5) #goal

            cv2.line(self.frame, (int(self.width / 2), 0), (int(self.width / 2), self.height), (0, 0, 255), 3)       #cartesian
            cv2.line(self.frame, (0, int(self.height / 2)), (int(self.width), int(self.height / 2)), (0, 0, 255), 3)

            #easy way to find the direction according to ring segments. Calculates which quarter the rings are and then sets direc.
            if int(self.center_pt[0]) < int(self.width / 2) and int(self.center_pt[1]) < int(self.height / 2):
                self.direc = -45
            elif int(self.center_pt[0]) < int(self.width / 2) and int(self.center_pt[1]) < int(self.height):
                self.direc = -135
            elif int(self.center_pt[0]) > int(self.width / 2) and int(self.center_pt[1]) < int(self.height / 2):
                self.direc = +45
            elif int(self.center_pt[0]) > int(self.width / 2) and int(self.center_pt[1]) < int(self.height):
                self.direc = +135
            print(self.direc)

    def draw_ortogonal_line(self):
        i = 0
        self.direction_lines = []

        for c in self.ring_contours:
            if cv2.contourArea(c) > 800: # if line segment is large enough
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(frame, [box], 0, (255, 0, 255), 2)

                center_pt = rect[0]
                self.center_pt = center_pt

                # cv2.circle(frame, (int(center_pt[0]), int(center_pt[1])), 3, (150, 150, 0), 2)
                tl, tr, br, bl = self._order_points_new(box)

                long_line = []
                short_line = []

                if self.get_distance(tl, tr) > self.get_distance(tl, bl):
                    long_line.append(tl)
                    long_line.append(tr)
                    short_line.append(tl)
                    short_line.append(bl)
                else:
                    long_line.append(tl)
                    long_line.append(bl)
                    short_line.append(tl)
                    short_line.append(tr)

                middle_of_short_line = self.find_middle(short_line[0][0], short_line[0][1], short_line[1][0],
                                                   short_line[1][1])

                cX, cY, dX, dY = self.getPerpCoord(middle_of_short_line[0], middle_of_short_line[1], center_pt[0],
                                              center_pt[1], 500, 0)

                blank_for_line = np.zeros(self.xor.shape, np.uint8)

                cv2.line(blank_for_line, (cX, cY), (dX, dY), 1, 1)

                blank_for_contour = np.zeros(self.xor.shape, np.uint8)

                cv2.drawContours(blank_for_contour, self.ring_contours, i, 1)

                #we test whether or not the line we draw from the ring segment to the center intersects with the ring itself.
                intersection_for_direction = cv2.bitwise_and(blank_for_line, blank_for_contour)

                #if there is white bits in intersection_for_direction then the line we test is in the wrong direction so we reverse it 180 degrees.
                if cv2.countNonZero(intersection_for_direction) == 0:
                    # 'getPerpCoord' calculates starting and finishing points of our ortogonal line. The last parameter changes the direction of the line 180 degrees.
                    cX, cY, dX, dY = self.getPerpCoord(middle_of_short_line[0], middle_of_short_line[1], center_pt[0],
                                                  center_pt[1], 500, 0)
                    cv2.line(frame, (cX, cY), (dX, dY), (255, 255, 0), 15)  # ortogonal line
                else:
                    cX, cY, dX, dY = self.getPerpCoord(middle_of_short_line[0], middle_of_short_line[1], center_pt[0],
                                                  center_pt[1], 500, 1)
                    cv2.line(frame, (cX, cY), (dX, dY), (255, 255, 0), 15)  # ortogonal line

                i += 1
                self.direction_lines.append([cX, cY, dX, dY])

    #draws intersection points of the ortogonal lines.
    def draw_intersection(self):
        image_of_lines = []
        last = np.zeros(self.frame.shape, np.uint8)

        if len(self.direction_lines) > 2:
            i = 0
            for d in self.direction_lines:
                i = i + 1
                blank = np.zeros(frame.shape[0:2])
                cv2.line(blank, (int(d[0]), int(d[1])), (int(d[2]), int(d[3])), 1, 25)
                image_of_lines.append(blank)

        images_to_or = []
        last = np.zeros(frame.shape[0:2])

        if len(image_of_lines) > 1:
            for i in range(0, len(image_of_lines)):
                for j in range(i + 1, len(image_of_lines)):
                    images_to_or.append(cv2.bitwise_and(image_of_lines[i], image_of_lines[j]))

        for k in images_to_or:
            last = cv2.bitwise_or(k, last)

        #if there is intersection of ortogonal lines it is drawn on 'last'
        self.last = last
        if cv2.countNonZero(self.last) != 0:
            self.move_to_contour_flag = False
        self.intersection_point_img = last.astype(np.uint8)

    def move_rov_to_intersection_pt(self):
        if self.move_to_contour_flag == False:
            cnts, im2 = cv2.findContours(self.intersection_point_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            self.direc = ""

            for c in cnts:
                # if cv2.contourArea(c) > 100
                rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(frame, [box], 0, (0, 255, 255), 5)

                center_pt = rect[0]

                self.direc = self.get_direction(center_pt)
            if self.counter_of_finish > 4 and self.direc == "FINISH":
                print(self.direc)
            elif self.direc:
                print(self.direc)

    def show_frame(self):
        cv2.imshow("frame", self.frame)
        cv2.imshow("xor", self.xor)
        cv2.imshow("intersection_point_img", self.last)
        cv2.waitKey(5)
        return frame


    # helpers
    def _order_points_new(self, pts):
        # sort the points based on their x-coordinates
        xSorted = pts[np.argsort(pts[:, 0]), :]

        # grab the left-most and right-most points from the sorted
        # x-roodinate points
        leftMost = xSorted[:2, :]
        rightMost = xSorted[2:, :]

        # now, sort the left-most coordinates according to their
        # y-coordinates so we can grab the top-left and bottom-left
        # points, respectively
        leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
        (tl, bl) = leftMost

        # if use Euclidean distance, it will run in error when the object
        # is trapezoid. So we should use the same simple y-coordinates order method.

        # now, sort the right-most coordinates according to their
        # y-coordinates so we can grab the top-right and bottom-right
        # points, respectively
        rightMost = rightMost[np.argsort(rightMost[:, 1]), :]
        (tr, br) = rightMost

        # return the coordinates in top-left, top-right,
        # bottom-right, and bottom-left order
        return tl, tr, br, bl
        # np.array([tl, tr, br, bl], dtype="float32")


    def get_distance(self, pt1, pt2):
        return math.sqrt(math.pow(pt1[0] - pt2[0], 2) + math.pow(pt1[1] - pt2[1], 2))


    def find_middle(self, x1, y1, x2, y2):
        xt = (int)((x1 + x2) / 2)
        yt = (int)((y1 + y2) / 2)
        return xt, yt


    def find_angle(self, origin, pt1):
        delta_y = pt1[1] - origin[1]
        delta_x = pt1[0] - origin[0]

        self.angle = 180*(math.atan(delta_y / delta_x))/math.pi


    def getPerpCoord(self, aX, aY, bX, bY, length, prop_for_direction):
        vX = bX - aX
        vY = bY - aY
        # print(str(vX)+" "+str(vY))
        if (vX == 0 or vY == 0):
            return 0, 0, 0, 0
        mag = math.sqrt(vX * vX + vY * vY)
        vX = vX / mag
        vY = vY / mag
        temp = vX
        vX = 0 - vY
        vY = temp
        if prop_for_direction == 0:  # sağ
            cX = bX + vX * length
            cY = bY + vY * length
            dX = bX - vX * 1
            dY = bY - vY * 1
        elif prop_for_direction == 1:  # sol
            cX = bX + vX * 1
            cY = bY + vY * 1
            dX = bX - vX * length
            dY = bY - vY * length
        elif prop_for_direction == 2:
            cX = bX + vX * 70
            cY = bY + vY * 70
            dX = bX - vX * 70
            dY = bY - vY * 70

        return int(cX), int(cY), int(dX), int(dY)


    def get_direction(self, collision_pt):
        direc = "Search Algorithm"
        if collision_pt[0] < 213 and collision_pt[1] < 160:
            direc = "-30"
        elif collision_pt[0] < 427 and collision_pt[1] < 160:
            direc = "0"
        elif collision_pt[0] < 640 and collision_pt[1] < 160:
            direc = "30"
        elif collision_pt[0] < 213 and collision_pt[1] < 320:
            direc = "-90"
        elif collision_pt[0] < 213 and collision_pt[1] < 480:
            direc = "-135"
        elif collision_pt[0] < 426 and collision_pt[1] < 320:  # important
            direc = "FINISH"
        elif collision_pt[0] < 640 and collision_pt[1] < 320:
            direc = "+90"
        elif collision_pt[0] < 426 and collision_pt[1] < 480:
            direc = "-180"
        elif collision_pt[0] < 640 and collision_pt[1] < 480:
            direc = "+135"

        return direc


if __name__ == "__main__":
    cap = cv2.VideoCapture("video5.avi")
    #cap.set(1, 200)
    ring = Ring()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640, 480))
        # frame = cv2.flip(frame, -1)
        # frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        ring.get_photo(frame)
        ring.get_trackbar_data()
        ring.detect_rings()
        ring.contour_and_sort_xor()
        ring.move_to_contour()
        ring.draw_ortogonal_line()
        ring.draw_intersection()
        ring.move_rov_to_intersection_pt()
        ring.show_frame()

        # if cv2.waitKey(0) & 0xFF == ord("q"):
        #     break

    cap.release()
    cv2.destroyAllWindows()
