import cv2
import numpy as np
from PIL import Image
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

font = cv2.FONT_HERSHEY_SIMPLEX


class Subway_car:
    def __init__(self):
        self._white_lower = np.array([0, 0, 123], np.uint8)  # [0, 0, 114]
        self._white_upper = np.array([111, 62, 255], np.uint8)  # [110, 50, 255]
        self._thresh_lower = 135
        self._thresh_upper = 255
        self.face_lis = []
        self.k_means_faces = []
        self.sorted_faces = []
        self.h1 = 250
        self.w1 = 625

    # tepe thresh == > 130, yanlar hsv ve yanların genişlikleri arttırılacak.
    # arayüz entegrasyon

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
        self.cnt, _ = cv2.findContours(self.contour_photo, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]

        if self.cnt is not None:
            self.big_cnt = sorted(self.cnt, key=cv2.contourArea, reverse=True)[:1]

            self.rect = cv2.minAreaRect(self.big_cnt[0])
            box = cv2.boxPoints(self.rect)
            self.box = np.int0(box)
            # cv2.drawContours(self.img, [self.box], 0, (255, 255, 0), 2) #croppped photo

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
        self.box = np.int0(box)  # kırpılacak pixeller
        # cv2.drawContours(self.img_rot, [self.box], 0, (0, 0, 255), 2)  # croppped photo

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

        if not self._return_shape(y2 - y1, x2 - x1):
            self.img_cropped = self.img_rot[y1:y2, x1:x2]
            # cv2.imshow("1",self.img_cropped)
            # cv2.waitKey(0)
        else:
            self.img_cropped = self.img_rot[y1:y2, x1:x2]
            # cv2.imshow("2", self.img_cropped)
            # cv2.waitKey(0)

    def _return_shape(self, height, width):
        if 0.7 < height / width < 1.85:
            return True
        elif 1.85 < height / width:
            return False
        elif height / width < 0.7:
            return False

    def _resize_image(self):
        (height, width, _) = self.img_cropped.shape
        if not self._return_shape(height, width):  # rectangle
            width = self.w1
            height = self.h1
        else:  # square
            width = self.h1
            height = self.h1

        dim = (width, height)
        # resize image
        resized = cv2.resize(self.img_cropped, dim, interpolation=cv2.INTER_AREA)
        self.img_cropped = resized

    # top en son çağırılacak
    def get_kmeans_top(self):
        (y, x, _) = self.img_cropped.shape
        # print(self.img_cropped.shape)
        img_up = self.img_cropped[20:60, 20:x - 20]
        img_down = self.img_cropped[y - 60: y - 20, 20: x - 20]
        # cv2.imshow("up", img_up)
        # cv2.imshow("down", img_down)
        # cv2.waitKey(0)
        img_right = self.img_cropped[20:y - 20, x - 80:x - 50]
        img_left = self.img_cropped[20:y - 20, 20: 60]

        # cv2.imshow("right", img_right)
        # cv2.imshow("left", img_left)
        # cv2.waitKey(0)
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
        self._resize_image()
        self.face_lis.append([self.img_cropped, self.face_col])

    def get_kmeans_side(self):
        (y, x, _) = self.img_cropped.shape

        if not self._return_shape(y, x):
            img_up = self.img_cropped[30:70, 100:x - 150]
        else:
            img_up = self.img_cropped[30:70, 100:x - 60]

        # cv2.imshow("cropped", self.img_cropped)
        # cv2.imshow("up", img_up)
        # cv2.waitKey(0)

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
        self._resize_image()
        self.face_lis.append([self.img_cropped, self.face_col])

    def compare_col(self, col1, col2):
        color1_rgb = sRGBColor(col1[2], col1[1], col1[0])

        # print(col1[2], col1[1], col1[0])
        # Blue Color
        color2_rgb = sRGBColor(col2[2], col2[1], col2[0])

        # Convert from RGB to Lab Color Space
        color1_lab = convert_color(color1_rgb, LabColor)

        # Convert from RGB to Lab Color Space
        color2_lab = convert_color(color2_rgb, LabColor)

        # Find the color difference
        delta_e = delta_e_cie2000(color1_lab, color2_lab)
        # print(delta_e)
        if delta_e < 35:
            return True
        return False

    def correct_photo(self):
        a = 0  # no error
        col = self.face_lis[4][1]
        sq_det = 0

        square_sides = []
        rect_sides = []

        for side in self.face_lis[0:4]:
            if side[0].shape[1] == self.h1:
                square_sides.append(side)
            else:
                rect_sides.append(side)

        square_black = np.zeros([self.h1, self.w1, 3], dtype=np.uint8)
        square_black.fill(0)  # or img[:] = 255

        rect_black = np.zeros([self.h1, self.w1, 3], dtype=np.uint8)
        rect_black.fill(0)  # or img[:] = 255

        for main_col in col:
            if sq_det % 2 == 0:  # dikdörtgen yüzey
                for side in rect_sides:
                    colour = side[1][0][0]
                    if self.compare_col(main_col[0], colour):
                        face = side[0]
                        self.sorted_faces.append(face)
                        a = 1
                if a == 0:
                    self.sorted_faces.append(rect_black)

            else:  # kareler
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

    def add_white_to_photos(self):
        # create new image of desired size and color (blue) for padding
        img1 = self.sorted_faces[0]
        img2 = self.sorted_faces[1]
        img3 = self.sorted_faces[2]
        img4 = self.sorted_faces[3]
        imgtop = self.sorted_faces[4]

        ww = 2 * self.h1 + 2 * self.w1
        hh = self.h1
        color = (255, 255, 255)
        self.result_upper = np.full((hh, ww, 3), color, dtype=np.uint8)
        # print(self.result_upper.shape)
        # compute center offset
        xx = self.h1
        yy = 0

        # copy img image into center of result image
        self.result_upper[yy:yy + self.h1, xx:xx + self.w1] = self.sorted_faces[4]
        self.sorted_faces[4] = self.result_upper

    def concate_photos(self):
        img_up = self.sorted_faces[0]
        img_middle = self.sorted_faces[4]
        img_down = self.sorted_faces[2]
        img_left = self.sorted_faces[3]
        img_right = self.sorted_faces[1]
        # print(img_up.shape)

        horizontal = np.concatenate((img_left, img_down, img_right, img_up), axis=1)
        self.result = np.concatenate((img_middle, horizontal), axis=0)
        # print(self.result.shape)

    def test(self):
        # cv2.imshow("img_cropped", self.img_cropped)
        # cv2.imshow("real", self.img)
        # cv2.imshow("result", self.result)
        # cv2.waitKey(0)
        self.face_lis = []
        self.k_means_faces = []
        self.sorted_faces = []
        return self.result

    def show(self):
        num_face = 4
        photo_or_list = 0
        cv2.namedWindow("frame", cv2.WINDOW_FREERATIO)
        cv2.imshow("frame", self.face_lis[num_face][
            photo_or_list])  # first index which photo, second (0 => get photo , 1=> get list of photo)
        if KeyboardInterrupt() == "q":
            cv2.destroyAllWindows()
        cv2.waitKey(0)


'''
    def _contour_col(self, img):
        img_c = np.uint8(img*255)

        _, binarized = cv2.threshold(img_c, 127, 255, cv2.THRESH_BINARY)

        con_img, _ = cv2.findContours(binarized, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if con_img is not None:
            big_cnt = sorted(con_img, key=cv2.contourArea, reverse=True)[:1]

            rect = cv2.minAreaRect(big_cnt[0])
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            center = np.int0(rect[0])

            cv2.drawContours(self.face, [box], 0, (0, 0, 255), 3)
            cv2.circle(self.face, (cent[0], cent[1]), 3, (0,0,0),3)

            return [[center], [self.face[center[1], center[0]]]]  # return center and color
            # img[x,y] or [y,x] 

    def CLAHE(self):

        lab = cv2.cvtColor(self.img, cv2.COLOR_BGR2LAB)
        lab_planes = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab_planes[0] = clahe.apply(lab_planes[0])
        lab = cv2.merge(lab_planes)
        self.bgr2 = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def histogram_eq(self):
        image = cv2.cvtColor(self.bgr2, cv2.COLOR_BGR2YUV)
        channel = cv2.split(image)
        cv2.equalizeHist(channel[0], channel[0])  # channel[0] = y,  channel[1] = u,  channel[2] = V
        cv2.merge(channel, image)
        self.bgr_frame = cv2.cvtColor(image, cv2.COLOR_YUV2BGR)

    def dilation(self):
        #blur = cv2.blur(self.white_mask,(2,2))
        kernel = np.ones((7, 7), np.uint8)
        self.opening = cv2.morphologyEx(self.white_mask, cv2.MORPH_OPEN, kernel)
        self.bitwise = cv2.bitwise_not(self.opening)
        # final_img = cv2.bitwise_and(self.bgr2, self.bgr2, mask=self.bitwise)

    def trackbar_pos(self):
        lh = cv2.getTrackbarPos("Lower_H", "trackbar")
        ls = cv2.getTrackbarPos("Lower_S", "trackbar")
        lv = cv2.getTrackbarPos("Lower_V", "trackbar")

        uh = cv2.getTrackbarPos("Upper_H", "trackbar")
        us = cv2.getTrackbarPos("Upper_S", "trackbar")
        uv = cv2.getTrackbarPos("Upper_v", "trackbar")

        self._white_lower = np.array([lh, ls, lv])
        self._white_upper = np.array([uh, us, uv])

    def nothing(self, x):
        pass    
        def get_rgb_contours(self):
        work = cv2.cvtColor(self.result, cv2.COLOR_BGR2GRAY)
        work = cv2.threshold(work, 150, 255, cv2.THRESH_TOZERO)[1]

        self.color_cnt, _ = cv2.findContours(work, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if self.color_cnt is not None:
            self.list_cnt = sorted(self.color_cnt, key=cv2.contourArea, reverse=True)

            for c in self.list_cnt:
                self.rect = cv2.minAreaRect(c)
                box = cv2.boxPoints(self.rect)
                self.box = np.int0(box)
                cv2.drawContours(self.result, [self.box], 0, (0, 0, 255), 3)

    def create_mask(self):
        work = cv2.cvtColor(self.face, cv2.COLOR_BGR2HSV)

        accumMask = np.zeros(work.shape[:2], dtype="uint8")

        boundaries = [
            ([0, 0, 127], [105, 185, 215])  # white range
        ]

        for (lower, upper) in boundaries:
            # create NumPy arrays from the boundaries
            lower = np.array(lower, dtype="uint8")
            upper = np.array(upper, dtype="uint8")

            # find the colors within the specified boundaries
            mask = cv2.inRange(work, lower, upper)

            # merge the mask into the accumulated masks
            accumMask = cv2.bitwise_or(accumMask, mask)

        self.hss = cv2.bitwise_not(accumMask)

'''
'''
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
          height = self.w1
          width = self.w1
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
      # print(ref_points)
      last_pts = tuple(row for row in ref_points)
      # print(last_pts)
      for p in last_pts:
          # print(tuple(p))
          # cv2.putText(self.img_cropped, "{}".format(tuple(p)), tuple(p), font, 1, (255, 0, 0), thickness=4)
          cv2.circle(self.img_cropped, tuple(p), 4, (0, 0, 255), 2)

      #col_up = self.img_cropped[int(up[1]), int(up[0])]
      #col_down = self.img_cropped[int(down[1]), int(down[0])]
      #col_left = self.img_cropped[int(left[1]), int(left[0])]
      #col_right = self.img_cropped[int(right[1]), int(right[0])]

      #self.face_col = [col_up, col_right, col_left]

      #self._resize_image()

      #self.face_lis.append([self.img_cropped, self.face_col])

      #cv2.imshow("frame", self.img_cropped)
      #cv2.waitKey(0)

       def get_rgb_from_coor_top(self):
      #print("tepe girdi.")
      if self.img_cropped.shape[0] > 0 and self.img_cropped.shape[1] > 0:
          (height, width, _) = self.img_cropped.shape
      else:
          height = self.w1
          width = self.w1
      if height/width > 0.6:
          sens_vert = 23
          sens_hor = 19
      else: #buraya düzeltme lazım
          pass
      sens_vert = 25
      sens_hor = 15

      up = [width / 2, (height / sens_vert) * 1]
      down = [width / 2, (height / sens_vert) * (sens_vert - 1)]
      left = [(width / sens_hor) * 1, (height / 2)]
      right = [(width / sens_hor) * (sens_hor - 1), (height / 2)]

      li = [up, right, down, left]
      ar = np.array(li)
      ref_points = ar.astype(int)
      last_pts = tuple(row for row in ref_points)
      for p in last_pts:
          cv2.circle(self.img_cropped, tuple(p), 4, (0, 0, 255), 2)
      #col_up = self.img_cropped[int(up[1]), int(up[0])]
      #col_down = self.img_cropped[int(down[1]), int(down[0])]
      #col_left = self.img_cropped[int(left[1]), int(left[0])]
      #col_right = self.img_cropped[int(right[1]), int(right[0])]

      #self.face_col = [col_up, col_right, col_down, col_left]

      #self._resize_image()

      #self.face_lis.append([self.img_cropped, self.face_col])
  '''

if __name__ == "__main__":
    """ 
    cap = cv2.VideoCapture("Video/nisan/2.avi")
    ret, frame = cap.read()
    """
    subway_car = Subway_car()

    '''
        while True:
        #ret, frame = cap.read()
        frame = cv2.imread("Video/nisan/kmeans_1.jpg")
        if not ret:
            break

        subway_car.get_photo(frame)
        subway_car.thresh_operation()
        #subway_car.hsv_operation()
        subway_car.find_contour()
        subway_car.crop_minAreaRect()
        subway_car.crop_face()
        subway_car.get_kmeans_top()
        #subway_car.get_kmeans_side()
        #subway_car.kmeans_remove_noise()
        #subway_car.get_rgb_from_coor_top()
        #subway_car.get_rgb_from_coor()
        subway_car._resize_image()
        subway_car.test()


        if cv2.waitKey(0) & 0xFF == ord("q"):
            break
        break

    '''

    frame = cv2.imread("Photo/J1.png")  # yan_mavi.jpg
    subway_car.get_photo(frame)
    # subway_car.thresh_operation()
    subway_car.hsv_operation()
    subway_car.find_contour()
    subway_car.crop_minAreaRect()
    subway_car.crop_face()
    # subway_car.get_kmeans_top()
    subway_car.get_kmeans_side()

    frame = cv2.imread("Photo/J5.png")  # yan_pembe.jpg
    subway_car.get_photo(frame)
    # subway_car.thresh_operation()
    subway_car.hsv_operation()
    subway_car.find_contour()
    subway_car.crop_minAreaRect()
    subway_car.crop_face()
    # subway_car.get_kmeans_top()
    subway_car.get_kmeans_side()

    frame = cv2.imread("Photo/J2.png")  # yan_sari.jpg
    subway_car.get_photo(frame)
    # subway_car.thresh_operation()
    subway_car.hsv_operation()
    subway_car.find_contour()
    subway_car.crop_minAreaRect()
    subway_car.crop_face()
    # subway_car.get_kmeans_top()
    subway_car.get_kmeans_side()

    frame = cv2.imread("Photo/J4.png")  # yan_kirmizi.jpg
    subway_car.get_photo(frame)
    # subway_car.thresh_operation()
    subway_car.hsv_operation()
    subway_car.find_contour()
    subway_car.crop_minAreaRect()
    subway_car.crop_face()
    # subway_car.get_kmeans_top()
    subway_car.get_kmeans_side()

    frame = cv2.imread("Photo/J3.png")  # kmeans2.jpg
    subway_car.get_photo(frame)
    # subway_car.thresh_operation()
    subway_car.hsv_operation()
    subway_car.find_contour()
    subway_car.crop_minAreaRect()
    subway_car.crop_face()
    subway_car.get_kmeans_top()
    # subway_car.get_kmeans_side()

    # subway_car.control()
    subway_car.correct_photo()

    subway_car.add_white_to_photos()
    subway_car.concate_photos()

    subway_car.test()
