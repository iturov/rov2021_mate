import numpy as np
import cv2
import math


class Mapping:
    def __init__(self):
        self.__red_line_min = np.array([168, 46, 164], np.uint8)
        self.__red_line_max = np.array([179, 113, 255], np.uint8)

        self.__blue_line_min = np.array([46, 69, 79], np.uint8)
        self.__blue_line_max = np.array([112, 255, 255], np.uint8)

        self.__yellow_box_min = np.array([17, 72, 127], np.uint8)
        self.__yellow_box_max = np.array([58, 255, 255], np.uint8)

        self.__star_min = np.array([115, 65, 83], np.uint8)
        self.__star_max = np.array([165, 190, 255], np.uint8)

        self.__white_pipe_min = np.array([79, 3, 81], np.uint8)
        self.__white_pipe_max = np.array([125, 65, 249], np.uint8)

        self.__coral_reef_min = np.array([160, 58, 113], np.uint8)
        self.__coral_reef_max = np.array([169, 255, 255], np.uint8)

        self.coral1 = cv2.imread("Coral1.png")
        self.coral1_map = cv2.imread("Coral1_map.png")

        self.coral2 = cv2.imread("Coral2.png")
        self.coral2_map = cv2.imread("Coral2_map.png")

        self.dot = cv2.imread("dot.png")
        self.dot_map = cv2.imread("dot_map.png")

        self.red_star = cv2.imread("RedStar.png")
        self.red_star_map = cv2.imread("RedStar_map.png")

        self.yellow_square = cv2.imread("yellowSquare.png")
        self.yellow_square_map = cv2.imread("yellowSquare_map.png")

        self.empty = cv2.imread("Empty.png")

        self.mapping_screen = np.zeros((450, 900, 3), dtype=np.uint8)
        self.mapping_screen[:] = [255, 255, 255]

        self.mapping_screen_map = np.zeros((450, 900, 3), dtype=np.uint8)
        self.mapping_screen_map[:] = [255, 255, 255]

    def operation(self, img):
        self.img = img
        self.canvas = np.copy(self.img)
        self.roi_frame = np.copy(self.img)

        (self.height, self.width, _) = img.shape
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        self.red_line_mask = cv2.inRange(hsv, self.__red_line_min, self.__red_line_max)
        self.red_line_photo = cv2.bitwise_and(img, img, mask=self.red_line_mask)

        self.blue_line_mask = cv2.inRange(hsv, self.__blue_line_min, self.__blue_line_max)
        self.blue_line_photo = cv2.bitwise_and(img, img, mask=self.blue_line_mask)

        self.yellow_box_mask = cv2.inRange(hsv, self.__yellow_box_min, self.__yellow_box_max)
        self.yellow_box_photo = cv2.bitwise_and(img, img, mask=self.yellow_box_mask)

        self.star_mask = cv2.inRange(hsv, self.__star_min, self.__star_max)
        self.star_photo = cv2.bitwise_and(img, img, mask=self.star_mask)

        self.white_pipe_mask = cv2.inRange(hsv, self.__white_pipe_min, self.__white_pipe_max)
        self.white_pipe_photo = cv2.bitwise_and(img, img, mask=self.white_pipe_mask)

        self.coral_reef_mask = cv2.inRange(hsv, self.__coral_reef_min, self.__coral_reef_max)
        self.coral_reef_photo = cv2.bitwise_and(img, img, mask=self.coral_reef_mask)

        self.masks = [self.yellow_box_mask, self.star_mask, self.white_pipe_mask, self.coral_reef_mask]

    def intersection_detect(self):
        self.vertical_lines = np.zeros((self.height, self.width), dtype=np.uint8)

        blue_lines = cv2.HoughLinesP(self.blue_line_mask, 1, np.pi / 180, 50, None, 50, 10)

        if blue_lines is not None:
            for i in range(0, len(blue_lines)):
                l = blue_lines[i][0]
                if round(l[2] - l[0], 4) <= 0.001:
                    theta = 90  ## if block to find  angle
                else:
                    m = (l[3] - l[1]) / (round(l[2] - l[0], 4))
                    theta = math.atan(m) * 180 / 3.14

                if theta < 30 and theta > -30:  ##  if block for drawing vertical lines
                    cv2.line(self.vertical_lines, (l[0], l[1]), (l[2], l[3]), (255, 255, 255), 3, cv2.LINE_AA)

        ltx, lty, rbx, rby = self.edge_detect(self.vertical_lines)

        mapping_width = rbx - ltx
        mapping_height = rby - lty

        box_width = int(mapping_width / 9)
        box_height = int(mapping_height / 3)

        self.intersection_x = list()
        self.intersection_y = list()

        for i in range(10):
            self.intersection_x.append(ltx + i * box_width)

        for i in range(4):
            self.intersection_y.append(lty + i * box_height)


        for i in range(10):
            for j in range(4):
                cv2.circle(self.canvas, (self.intersection_x[i], self.intersection_y[j]), 5, (0, 0, 128), -1)

    def countours_area(self, mask):
        total_area = 0

        ret, thresh = cv2.threshold(mask, 127, 255, 0)
        contours, hierarchy = cv2.findContours(thresh, 1, 2)[-2:]
        for cnt in contours:
            area = cv2.contourArea(cnt)
            total_area = total_area + area

        return total_area

    def draw_map(self):
        mapping_x_pixel = 45
        mapping_y_pixel = 90

        coral_flag = 0

        # cv2.imshow("BBB", self.canvas)
        for i in range(1, 10):
            for j in range(1, 4):
                areas = []
                for k in range(4):
                    roi_image_mask = self.masks[k][self.intersection_y[j - 1]:self.intersection_y[j],
                                     self.intersection_x[i - 1]:self.intersection_x[i]]

                    areas.append(self.countours_area(roi_image_mask))

                # print(areas)

                if areas[2] > 800:
                    self.mapping_screen[mapping_y_pixel: mapping_y_pixel + 90,
                    mapping_x_pixel: mapping_x_pixel + 90] = self.dot
                    self.mapping_screen_map[mapping_y_pixel: mapping_y_pixel + 90,
                    mapping_x_pixel: mapping_x_pixel + 90] = self.dot_map

                elif areas[0] > 10000:
                    self.mapping_screen[mapping_y_pixel: mapping_y_pixel + 90,
                    mapping_x_pixel: mapping_x_pixel + 90] = self.yellow_square
                    self.mapping_screen_map[mapping_y_pixel: mapping_y_pixel + 90,
                    mapping_x_pixel: mapping_x_pixel + 90] = self.yellow_square_map

                elif areas[1] > 2500:
                    self.mapping_screen[mapping_y_pixel: mapping_y_pixel + 90,
                    mapping_x_pixel: mapping_x_pixel + 90] = self.red_star
                    self.mapping_screen_map[mapping_y_pixel: mapping_y_pixel + 90,
                    mapping_x_pixel: mapping_x_pixel + 90] = self.red_star_map

                elif areas[3] > 1000:
                    if coral_flag:
                        self.mapping_screen[mapping_y_pixel: mapping_y_pixel + 90,
                        mapping_x_pixel: mapping_x_pixel + 90] = self.coral2
                        self.mapping_screen_map[mapping_y_pixel: mapping_y_pixel + 90,
                        mapping_x_pixel: mapping_x_pixel + 90] = self.coral2_map

                    else:
                        self.mapping_screen[mapping_y_pixel: mapping_y_pixel + 90,
                        mapping_x_pixel: mapping_x_pixel + 90] = self.coral1
                        self.mapping_screen_map[mapping_y_pixel: mapping_y_pixel + 90,
                        mapping_x_pixel: mapping_x_pixel + 90] = self.coral1_map
                        coral_flag = 1

                else:
                    self.mapping_screen[mapping_y_pixel: mapping_y_pixel + 90,
                    mapping_x_pixel: mapping_x_pixel + 90] = self.empty
                    self.mapping_screen_map[mapping_y_pixel: mapping_y_pixel + 90,
                    mapping_x_pixel: mapping_x_pixel + 90] = self.empty

                mapping_y_pixel += 90

            mapping_y_pixel = 90
            mapping_x_pixel += 90

        # cv2.imshow("Mapping", self.mapping_screen)
        # cv2.imshow("Mapping Map", self.mapping_screen_map)
        # cv2.waitKey(0)

    def edge_detect(self, vertical_lines):
        top_blue = list()
        bottom_blue = list()
        mid_line = int(self.height / 2)

        for i in range(self.height):
            for j in range(self.width):
                if vertical_lines[i][j]:
                    if i > mid_line:
                        bottom_blue.append([i, j])
                    else:
                        top_blue.append([i, j])

        top_blue = sorted(top_blue, key=lambda x: x[1], reverse=False)[:1]
        bottom_blue = sorted(bottom_blue, key=lambda x: x[1], reverse=True)[:1]

        return top_blue[0][1], top_blue[0][0], bottom_blue[0][1], bottom_blue[0][0]


if __name__ == "__main__":
    img = cv2.imread("i4.jpg")
    img = cv2.resize(img, (1600, 642))

    mapping = Mapping()
    mapping.operation(img)
    mapping.intersection_detect()
    mapping.draw_map()
