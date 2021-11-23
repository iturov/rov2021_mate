import cv2
import numpy as np
from PIL import Image
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

font = cv2.FONT_HERSHEY_SIMPLEX


class Subway_car:
    def __init__(self):
        self._white_lower = np.array([0, 0, 114], np.uint8)     # [0, 0, 114]
        self._white_upper = np.array([114, 55, 255], np.uint8) # [110, 50, 255]
        self._thresh_lower = 180
        self._thresh_upper = 255
        self.face_lis = []
        self.k_means_faces = []
        self.sorted_faces = []

    def get_photo(self, img):
        (self.height, self.width, _) = img.shape
        self.img = img

    def thresh_operation(self):
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        self.contour_photo = cv2.threshold(gray, self._thresh_lower, self._thresh_upper, cv2.THRESH_BINARY)[1]

    def hsv_operation(self):
        self.hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        self.white_mask = cv2.inRange(self.hsv, self._white_lower, self._white_upper)
        self.masked_img = cv2.bitwise_and(self.img, self.img, mask=self.white_mask)
        self.contour_photo = cv2.cvtColor(self.masked_img, cv2.COLOR_BGR2GRAY)

    def find_contour(self):
        self.cnt, _ = cv2.findContours(self.contour_photo, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if self.cnt is not None:
            self.big_cnt = sorted(self.cnt, key=cv2.contourArea, reverse=True)[:1]

            self.rect = cv2.minAreaRect(self.big_cnt[0])
            box = cv2.boxPoints(self.rect)
            self.box = np.int0(box)
            #cv2.drawContours(self.img, [self.box], 0, (255, 255, 0), 2) #croppped photo

    def crop_minAreaRect(self):
        # rotate img
        angle = self.rect[2]
        deg = 90
        if abs(angle) > 45:
            angle = 90 - abs(angle)
        else:
            deg = 0

        rows, cols = self.img.shape[0], self.img.shape[1]
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
        self.img_rot = cv2.warpAffine(self.img, M, (cols, rows))
        # rotate bounding box
        rect0 = (self.rect[0], self.rect[1], deg)
        box = cv2.boxPoints(rect0)
        self.box = np.int0(box) # kırpılacak pixeller
        #cv2.drawContours(self.img_rot, [self.box], 0, (0, 0, 255), 2)  # croppped photo

    def crop_face(self):
        x1 = self.width
        y1 = self.height
        x2 = 0
        y2 = 0
        for x in self.box:
            if x[0] < x1:
                x1 = x[0]

        for h in self.box:
            if h[1] < y1:
                y1 = h[1]

        for x in self.box:
            if x[0] > x2:
                x2 = x[0]

        for h in self.box:
            if h[1] > y2:
                y2 = h[1]

        if not self._return_shape(y2-y1, x2-x1):
            self.img_cropped = self.img_rot[y1:y2, x1:x2]
        else:
            self.img_cropped = self.img_rot[y1:y2, x1:x2]

    def _return_shape(self, height, width):
        if 0.7 < height / width < 1.85:
            return True
        elif 1.85 < height / width:
            return False
        elif height / width < 0.7:
            return False

    def _resize_image_unknown(self):
        (height, width, _) = self.img_cropped.shape
        if not self._return_shape(height, width): #rectangle
            width = 550
            height = 250
        else:# square
            width = 250
            height = 250

        dim = (width, height)
        # resize image
        resized = cv2.resize(self.img_cropped, dim, interpolation=cv2.INTER_AREA)
        self.img_cropped = resized

    # Formats frames to appropriate width and heights. if 'square_or_rect' = 1 => square ; 'square_or_rect' = 2 => rect
    def resize_image_known(self, square_or_rect):
        (height, width, _) = self.img_cropped.shape
        if square_or_rect == 1:
            width = 250
            height = 250
        elif square_or_rect == 2:
            width = 550
            height = 250
        dim = (width, height)
        # resize image
        resized = cv2.resize(self.img_cropped, dim, interpolation=cv2.INTER_AREA)
        self.img_cropped = resized

    #using k_means with K=2 clustures the pixels to 2 colors. White and wanted color.
    def get_kmeans_top(self):
        (y, x, _) = self.img_cropped.shape
        img_up = self.img_cropped[10:50, 10:x-10]
        img_down = self.img_cropped[y-60: y-10, 0: x-10]
        img_right = self.img_cropped[10:y-10, x-100:1-10]
        img_left = self.img_cropped[10:y - 10, 0: 40]

        #cv2.imshow("up", img_up)
        #cv2.imshow("down", img_down)
        #cv2.imshow("right", img_right)
        #cv2.imshow("left", img_left)

        ar = [img_up, img_right, img_down, img_left]
        self.face_col = []
        for i in range(len(ar)):
            K = 2
            Z = ar[i].reshape((-1, 3))
            # convert to np.float32
            Z = np.float32(Z)
            # define criteria, number of clusters(K) and apply kmeans()
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            ret, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            # Now convert back into uint8, and make original image
            center = np.uint8(center)
            res = center[label.flatten()]

            index_white = 0
            white = 0
            for a in range(len(center)):
                if white < int(center[a][0]) + int(center[a][1]) + int(center[a][2]):
                    white = int(center[a][0]) + int(center[a][1]) + int(center[a][2])
                    index_white = a
                col = np.delete(center, index_white, axis=0)
            self.face_col.append(col)
        self._resize_image_known(1)
        self.face_lis.append([self.img_cropped, self.face_col])

    #using k_means with K=2 clustures the pixels to 2 colors. White and wanted color.
    def get_kmeans_side(self):
        (y, x, _) = self.img_cropped.shape

        if not self._return_shape(y, x):
            img_up = self.img_cropped[30:70, 100:x - 150]
        else:
            img_up = self.img_cropped[30:70, 100:x - 60]

        #cv2.imshow("cropped", self.img_cropped)
        #cv2.imshow("up", img_up)
        #cv2.waitKey(0)

        colours = [img_up]
        self.face_col = []
        for i in range(len(colours)):
            K = 2
            Z = colours[i].reshape((-1, 3))
            # convert to np.float32
            Z = np.float32(Z)
            # define criteria, number of clusters(K) and apply kmeans()
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            ret, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            # Now convert back into uint8, and make original image
            center = np.uint8(center)
            res = center[label.flatten()]

            index_white = 0
            white = 0
            for a in range(len(center)):
                if white < int(center[a][0]) + int(center[a][1]) + int(center[a][2]):
                    white = int(center[a][0]) + int(center[a][1]) + int(center[a][2])
                    index_white = a
                col = np.delete(center, index_white, axis=0)
            self.face_col.append(col)
        self._resize_image_unkown()
        self.face_lis.append([self.img_cropped, self.face_col])

    #compares to colors with given thresh 'delta_e'.
    def compare_col(self, col1, col2):
        color1_rgb = sRGBColor(col1[2], col1[1], col1[0])

        #print(col1[2], col1[1], col1[0])
        # Blue Color
        color2_rgb = sRGBColor(col2[2], col2[1], col2[0])

        # Convert from RGB to Lab Color Space
        color1_lab = convert_color(color1_rgb, LabColor)

        # Convert from RGB to Lab Color Space
        color2_lab = convert_color(color2_rgb, LabColor)

        # Find the color difference
        delta_e = delta_e_cie2000(color1_lab, color2_lab)

        if delta_e < 35:
            return True
        return False

    def correct_photo(self):
        a = 0 # no error
        col = self.face_lis[4][1]
        sq_det = 0

        square_sides = []
        rect_sides = []

        for side in self.face_lis[0:4]:
            if side[0].shape[1] == 250:
                square_sides.append(side)
            else:
                rect_sides.append(side)

        square_black = np.zeros([250, 250, 3], dtype=np.uint8)
        square_black.fill(0)  # or img[:] = 255

        rect_black = np.zeros([250, 550, 3], dtype=np.uint8)
        rect_black.fill(0)  # or img[:] = 255

        for main_col in col:
            if sq_det % 2 == 0: #rectangular surfaces
                for side in rect_sides:
                    colour = side[1][0][0]
                    if self.compare_col(main_col[0], colour):
                        face = side[0]
                        self.sorted_faces.append(face)
                        a = 1
                if a == 0:
                    self.sorted_faces.append(rect_black)

            else:#square surfaces
                for side in square_sides:
                    colour = side[1][0][0]
                    if self.compare_col(main_col[0], colour):
                        face = side[0]
                        self.sorted_faces.append(face)
                        a = 1
                if a == 0:
                    self.sorted_faces.append(square_black)
            sq_det = sq_det + 1
            a = 0
        self.sorted_faces.append(self.face_lis[4][0])

    def save_face(self):
        #cv2.imshow("face", self.img_cropped)
        #cv2.waitKey(0)
        self.sorted_faces.append(self.img_cropped)

    #add white to images for concatation
    def add_white_order(self):
        # create new image of desired size and color (blue) for padding
        ww = 1600
        hh = 250
        color = (255, 255, 255)
        self.result_upper = np.full((hh, ww, 3), color, dtype=np.uint8)

        # compute center offset
        xx = 250
        yy = 0

        # copy img image into center of result image
        self.result_upper[yy:yy + 250, xx:xx + 550] = self.sorted_faces[0]
        self.sorted_faces[0] = self.result_upper

    #add white to images for concatation
    def add_white_kmeans(self):
        # create new image of desired size and color (blue) for padding
        img1 = self.sorted_faces[0]
        img2 = self.sorted_faces[1]
        img3 = self.sorted_faces[2]
        img4 = self.sorted_faces[3]
        imgtop = self.sorted_faces[4]

        ww = 1600
        hh = 250
        color = (255, 255, 255)
        self.result_upper = np.full((hh, ww, 3), color, dtype=np.uint8)

        # compute center offset
        xx = 250
        yy = 0

        # copy img image into center of result image
        self.result_upper[yy:yy + 250, xx:xx + 550] = self.sorted_faces[4]
        self.sorted_faces[4] = self.result_upper

    #concate photos for kmeans algoritm
    def concate_kmeans(self):
        img_up = self.sorted_faces[0]
        img_middle = self.sorted_faces[4]
        img_down = self.sorted_faces[2]
        img_left = self.sorted_faces[3]
        img_right = self.sorted_faces[1]

        horizontal = np.concatenate((img_left, img_down, img_right, img_up), axis=1)
        self.result = np.concatenate((img_middle, horizontal), axis=0)

    #concates photos in desired order
    def concate_order(self):
        img1 = self.sorted_faces[1]
        img2 = self.sorted_faces[2]
        img3 = self.sorted_faces[3]
        img4 = self.sorted_faces[4]
        imgtop_and_white = self.sorted_faces[0]

        horizontal = np.concatenate((img1, img2, img3, img4), axis=1)
        self.result = np.concatenate((imgtop_and_white, horizontal), axis=0)

    def show_kmeans(self):
        #cv2.imshow("img_cropped", self.img_cropped)
        #cv2.imshow("real", self.img)
        cv2.imshow("Photomosaic generated using k-means", self.result)
        cv2.waitKey(0)

    def show_order(self):
        # cv2.imshow("img_cropped", self.img_cropped)
        # cv2.imshow("real", self.img)
        cv2.imshow("Photomosaic", self.result)
        cv2.waitKey(0)

    def draw_thresh(self, img):
        _thresh_lower = 130
        _thresh_upper = 255
        (height, width, _) = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        contour_photo = cv2.threshold(gray, _thresh_lower, _thresh_upper, cv2.THRESH_BINARY)[1]
        cnt, _ = cv2.findContours(contour_photo, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if cnt is not None:
            big_cnt = sorted(cnt, key=cv2.contourArea, reverse=True)[:1]

            rect = cv2.minAreaRect(big_cnt[0])
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            thresh_frame = cv2.drawContours(img, [box], 0, (255, 255, 0), 2)  # croppped photo

        return thresh_frame

    def draw_hsv(self, img):
        _white_lower = np.array([0, 0, 114], np.uint8)  # [0, 0, 114]
        _white_upper = np.array([114, 55, 255], np.uint8)  # [110, 50, 255]
        (height, width, _) = img.shape
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        white_mask = cv2.inRange(hsv, _white_lower, _white_upper)
        masked_img = cv2.bitwise_and(img, img, mask=white_mask)
        contour_photo = cv2.cvtColor(masked_img, cv2.COLOR_BGR2GRAY)
        cnt, _ = cv2.findContours(contour_photo, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if cnt is not None:
            big_cnt = sorted(cnt, key=cv2.contourArea, reverse=True)[:1]

            rect = cv2.minAreaRect(big_cnt[0])
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            hsv_frame = cv2.drawContours(img, [box], 0, (255, 255, 0), 2)  # croppped photo

        return hsv_frame

   def kmeans_remove_noise(self):
      K = 2
      self.img_kmean = self.img_cropped[0:150, 0:1000]
      cv2.imshow("kmean", self.img_kmean)
      Z = self.img_kmean.reshape((-1, 3))
      # convert to np.float32
      Z = np.float32(Z)
      # define criteria, number of clusters(K) and apply kmeans()
      criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
      ret, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
      # Now convert back into uint8, and make original image
      center = np.uint8(center)
      res = center[label.flatten()]
      #self.face = res.reshape(self.img_cropped.shape)

      index_white = 0
      white = 0
      for a in range(len(center)):
          if white < int(center[a][0])+int(center[a][1])+int(center[a][2]):
              white = int(center[a][0])+int(center[a][1])+int(center[a][2])
              index_white = a
      col = np.delete(center, index_white, axis=0)

  def get_rgb_from_kmeans(self):
      lis_face = []
      a = np.zeros((self.face.shape[0], self.face.shape[1]))
      for c in range(len(self.arr_col)):
          for row in range(self.face.shape[0]):
              for col in range(self.face.shape[1]):
                  if self.face[row, col][0] == self.arr_col[c][0]:
                      a[row, col] = 1
          center_cord, color_cord = self._contour_col(a)
          a = np.zeros((self.face.shape[0], self.face.shape[1]))
          lis_face.append([center_cord, color_cord])
      self.car.append([self.face, lis_face])  # car list for all faces of the car. Holds the image, RGB and positions

  def get_rgb_from_coor(self):
      if self.img_cropped.shape[0] > 0 and self.img_cropped.shape[1] > 0:
          (height, width, _) = self.img_cropped.shape
      else:
          height = 500
          width = 500
      if 0.6 <= height/width <= 1.85:
          #print("kare")
          sens_vert = 15
          sens_hor = 15
      elif 1.85 < height/width:
          #print("dikeydikdortgen")
          sens_vert = 23
          sens_hor = 15
      elif height/width < 0.6:
          #print("yataydikdortgen")
          sens_vert = 13
          sens_hor = 19

      up = [width / 2, (height / sens_vert) * 1]
      #down = [width / 2, (height / sens_vert) * (sens_vert - 1)]
      left = [(width / sens_hor) * 1, (height / 2)]
      right = [(width / sens_hor) * (sens_hor - 1), (height / 2)]

      li = [up, right, left]
      ar = np.array(li)
      ref_points = ar.astype(int)

      last_pts = tuple(row for row in ref_points)

      for p in last_pts:
          cv2.circle(self.img_cropped, tuple(p), 4, (0, 0, 255), 2)

