import cv2
import numpy as np
from skimage import filters
from skimage.morphology import skeletonize
import itertools
import time


class Coral:
    version = "1.0"

    def __init__(self):
        """
            Coral sınıfının tüm değişkenlerinin tanımlandığı __init__ fonksiyonu
        """

        self.image = None
        self.copy_image = None
        self.copy_image_2 = None
        self.hsv_image = None
        self.pink_image = None
        self.white_image = None
        self.bitwise_image = None
        self.mask_sum_image = None
        self.skeleton_image = None
        self.skeleton_warped = None
        self.roi_image = None
        self.roi_mask_image = None
        self.roi_diff = 10
        self.soft_image = None
        self.warped_photo = None
        self.transformed_photo = None
        self.overlapped_image = None
        self.min_pink_area_value = 10000
        self.max_area = 0
        self.points = []
        self.points_end = []
        self.points_warped = []
        self.points_warped_end = []
        self.key_points = []
        self.key_points_photo = []
        self.line_1 = []
        self.line_2 = []

        self.kernel_1_1 = np.ones((1, 1), np.uint8)
        self.kernel_2_2 = np.ones((2, 2), np.uint8)
        self.kernel_1_3 = np.ones((1, 3), np.uint8)
        self.kernel_3_1 = np.ones((3, 1), np.uint8)
        self.kernel_3_3 = np.ones((3, 3), np.uint8)
        self.kernel_5_5 = np.ones((5, 5), np.uint8)
        self.kernel_7_7 = np.ones((7, 7), np.uint8)

        self.lowerPink = np.array([150, 45, 115])
        self.upperPink = np.array([176, 190, 255])
        self.lowerWhite = np.array([63, 0, 180])
        self.upperWhite = np.array([115, 82, 255])

        self.frameSize = (960, 540)
        self.error_msg = ""

    def get_image(self, image):
        """
            Buraya videodan gelen frame ler girilir ve girilen frame self değişkenlere atanır, gerekli kopyaları alınır.
        Ayrı olarak bu fonksiyon her çağrıldığında bir önceki frame e ait olan değişkenler sıfırlanır ve sürekli ayrı
        class tanımlanmaya gerek kalmadan loop başına yazılarak yeniden tanımlanmış hale getirir. İleriki aşamalarda
        canlı çekilen frame ler bu fonksiyona girilecektir.
        """

        self.error_msg = "OK"
        self.image = image
        # self.hsv_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        self.copy_image = np.copy(self.image)
        self.copy_image_2 = np.copy(self.image)
        self.skeleton_image = None
        self.skeleton_warped = None
        self.roi_image = None
        self.transformed_photo = None
        self.roi_mask_image = np.copy(self.image)
        self.roi_diff = 10
        self.points = []
        self.points_end = []
        self.points_warped = []
        self.points_warped_end = []
        self.key_points = []
        self.key_points_photo = []
        self.line_1 = []
        self.line_2 = []

    def transform_hsv(self, input_image):
        """
            Fonksiyon çağrıldığında gelen görüntüyü BGR formundan HSV formuna dönüştürür fakat bunu return le geri
        vermek yerine self.transformed_photo değişkenine kaydederek main loop tan da erişilebilmesini sağlar.
        """

        self.transformed_photo = cv2.cvtColor(input_image, cv2.COLOR_BGR2HSV)

    def apply_bitwise(self, input_image):
        """
            Fonksiyon çağrıldığında gelen görüntüyü apply_mask fonksiyonu sayesinde pembe ve beyaz renkte maskeler ve
        aynı görüntü üstünde bitwise alır fakat bunu return le geri vermek yerine self.bitwise_image değişkenine
        kaydederek main loop tan da erişilebilmesini sağlar.
        """

        self.apply_mask(input_image)
        bitwise_sum = cv2.bitwise_and(input_image, input_image, mask=self.mask_sum_image)
        self.bitwise_image = bitwise_sum

    def apply_white_mask(self, input_image):
        """
            Fonksiyon çağrıldığında gelen görüntüyü beyaz renkte maskeler ve bunu hem return le geri verir hem de main
        looptan kolay erişilebilmesi için self.white_image değişkenine atar.
        """

        hsv_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2HSV)
        mask_white = cv2.inRange(hsv_image, self.lowerWhite, self.upperWhite)
        self.white_image = mask_white
        return mask_white

    def apply_pink_mask(self, input_image):
        """
            Fonksiyon çağrıldığında gelen görüntüyü pembe renkte maskeler ve bunu hem return le geri verir hem de main
        looptan kolay erişilebilmesi için self.pink_image değişkenine atar.
        """

        hsv_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2HSV)
        mask_pink = cv2.inRange(hsv_image, self.lowerPink, self.upperPink)
        self.pink_image = mask_pink
        return mask_pink

    def apply_mask(self, input_image):
        """
            Fonksiyon çağrıldığında gelen görüntüyü beyaz ve pembe renkte maskeler ve bunu hem return le geri verir
        hem de main looptan kolay erişilebilmesi için self.mask_sum_image değişkenine atar.
        """

        hsv_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2HSV)
        mask_white = cv2.inRange(hsv_image, self.lowerWhite, self.upperWhite)
        # cv2.imshow("White Mask", mask_white)
        mask_pink = cv2.inRange(hsv_image, self.lowerPink, self.upperPink)
        # cv2.imshow("Pink Mask", mask_pink)
        self.mask_sum_image = cv2.add(mask_white, mask_pink)
        return self.mask_sum_image

    def get_roi_image(self):  # Farkı bulunacak ilk görsel için
        """
            Bu fonksiyon çağırıldığında get_image fonksiyonunda girilen frame in ROI si alınır. Bunu yapmak için
        öncelikle görüntünün pembe maskesini alır ve konturlar. En Büyük konturlu olan alanı bulur ve
        min_pink_area_value ile karşılaştırır eğer bu değerden büyükse devam eder küçükse False döndürür. Devam eden kod
        bu konturu alınmış en büyük alanın sağ, sol ve alt noktalarını alarak ROI sini çıkarır.
        """

        self.apply_pink_mask(self.image)
        contours, _ = cv2.findContours(self.pink_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]

        area_list = []
        for i in range(len(contours)):
            area_list.append(cv2.contourArea(contours[i]))
        if not area_list == []:
            self.max_area = max(area_list)
            big_area_index = area_list.index(self.max_area)
            if self.max_area < self.min_pink_area_value:
                self.error_msg = "Alan kucuk !!!"
                return False
        else:
            self.error_msg = "Alan hesaplanamadi !!!"
            return False

        x, y, w, h = cv2.boundingRect(contours[big_area_index])

        self.apply_mask(self.image)
        if x - 10 < 0:
            left_value = 0
        else:
            left_value = x - 10

        if x + w + 10 > self.image.shape[1]:
            right_value = self.image.shape[1]
        else:
            right_value = x + w + 10
        self.roi_diff = left_value
        """
            roi_diff değerini ROI nin sol değerine eşitliyoruz. Bu değeri ROI de bulduğumuz kesişimnoktalarının 
        koordinatlarını gerçek fotoğrafta görmek istediğimzde noktaların x değerine ekliyoruz.
        """
        self.roi_mask_image = self.mask_sum_image[0:y + h + 10, left_value:right_value]
        self.roi_image = self.copy_image[0:y + h + 10, left_value:right_value]
        return True

    def get_roi(self):  # Video frameleri için
        """
            Bu fonksiyon çağırıldığında get_image fonksiyonunda girilen frame in ROI si alınır. Bunu yapmak için
        öncelikle görüntünün pembe maskesini alır ve konturlar. En Büyük konturlu olan alanı bulur ve
        min_pink_area_value ile karşılaştırır eğer bu değerden büyükse devam eder küçükse False döndürür. Devam eden kod
        bu konturu alınmış en büyük alanın sağ, sol ve alt noktalarını alarak ROI sini çıkarır.
        """

        self.apply_pink_mask(self.image)

        contours, _ = cv2.findContours(self.pink_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]

        area_list = []
        for i in range(len(contours)):
            area_list.append(cv2.contourArea(contours[i]))
        if not area_list == []:
            self.max_area = max(area_list)
            big_area_index = area_list.index(self.max_area)
            if self.max_area < self.min_pink_area_value:
                self.error_msg = "Alan kucuk !!!"
                return False
        else:
            self.error_msg = "Alan hesaplanamadi !!!"
            return False

        x, y, w, h = cv2.boundingRect(contours[big_area_index])

        self.apply_mask(self.image)

        if x - 10 < 0:
            left_value = 0
        else:
            left_value = x - 10

        if x + w + 10 > self.image.shape[1]:
            right_value = self.image.shape[1]
        else:
            right_value = x + w + 10

        if not x > 200 or not x + w < 760:
            self.error_msg = "Alan disi !!!"
            return False
        self.roi_diff = left_value
        """
            roi_diff değerini ROI nin sol değerine eşitliyoruz. Bu değeri ROI de bulduğumuz kesişimnoktalarının 
        koordinatlarını gerçek fotoğrafta görmek istediğimzde noktaların x değerine ekliyoruz.
        """
        self.roi_mask_image = self.mask_sum_image[0:y + h + 10, left_value:right_value]
        self.roi_image = self.copy_image[0:y + h + 10, left_value:right_value]
        return True

    def soften(self, input_image):
        """
            Fonksiyon çağrıldığında gelen görüntüdeki noise leri giderir ve bunu hem return le geri verir hem de main
        looptan kolay erişilebilmesi için self.soft_image değişkenine atar.
        """
        eroded_image = cv2.erode(input_image, self.kernel_3_3)
        # cv2.imshow("1 Eroded Image", eroded_image)
        closed_image = cv2.morphologyEx(eroded_image, cv2.MORPH_CLOSE, self.kernel_5_5, iterations=2)
        eroded_image = cv2.erode(closed_image, self.kernel_3_3)

        dilated_image = cv2.dilate(eroded_image, self.kernel_3_3, iterations=1)
        opened_image = cv2.morphologyEx(dilated_image, cv2.MORPH_OPEN, self.kernel_3_3, iterations=1)
        # cv2.imshow("2 Opened Image", opened_image)
        closed_image = cv2.morphologyEx(opened_image, cv2.MORPH_CLOSE, self.kernel_5_5)
        # cv2.imshow("3 Closed Image", closed_image)

        blur = cv2.medianBlur(closed_image, 9)
        dilated_image = cv2.dilate(blur, self.kernel_3_3, iterations=0)
        blur = cv2.medianBlur(dilated_image, 9)
        self.soft_image = blur

        # cv2.imshow("4 Softened Image", self.soft_image)
        return blur

    @staticmethod
    def generate_nonadjacent_combination(input_list, take_n):
        """
            Skeletonize alma fonksiyonlarından biri
        """

        all_comb = []
        for comb in itertools.combinations(input_list, take_n):
            comb = np.array(comb)
            d = np.diff(comb)
            if len(d[d == 1]) == 0 and comb[-1] - comb[0] != 7:
                all_comb.append(comb)
        return all_comb

    @staticmethod
    def populate_intersection_kernel(combinations):
        """
            Skeletonize alma fonksiyonlarından biri
        """

        template = np.array((
            [-1, -1, -1],
            [-1, 1, -1],
            [-1, -1, -1]), dtype="int")
        match = [(0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0), (0, 0)]
        kernels = []
        for n in combinations:
            tmp = np.copy(template)
            for m in n:
                tmp[match[m][0], match[m][1]] = 1
            kernels.append(tmp)
        return kernels

    @staticmethod
    def find_endoflines(input_image):
        """
            Skeletonize alma fonksiyonlarından biri
        """

        kernel_0 = np.array((
            [-1, -1, -1],
            [-1, 1, -1],
            [-1, 1, -1]), dtype="int")

        kernel_1 = np.array((
            [-1, -1, -1],
            [-1, 1, -1],
            [1, -1, -1]), dtype="int")

        kernel_2 = np.array((
            [-1, -1, -1],
            [1, 1, -1],
            [-1, -1, -1]), dtype="int")

        kernel_3 = np.array((
            [1, -1, -1],
            [-1, 1, -1],
            [-1, -1, -1]), dtype="int")

        kernel_4 = np.array((
            [-1, 1, -1],
            [-1, 1, -1],
            [-1, -1, -1]), dtype="int")

        kernel_5 = np.array((
            [-1, -1, 1],
            [-1, 1, -1],
            [-1, -1, -1]), dtype="int")

        kernel_6 = np.array((
            [-1, -1, -1],
            [-1, 1, 1],
            [-1, -1, -1]), dtype="int")

        kernel_7 = np.array((
            [-1, -1, -1],
            [-1, 1, -1],
            [-1, -1, 1]), dtype="int")

        kernel = np.array((kernel_0, kernel_1, kernel_2, kernel_3, kernel_4, kernel_5, kernel_6, kernel_7))
        output_image = np.zeros(input_image.shape)
        for i in np.arange(8):
            out = cv2.morphologyEx(input_image, cv2.MORPH_HITMISS, kernel[i, :, :])
            out = cv2.dilate(out, np.ones((3, 3), np.uint8), iterations=3)
            output_image = output_image + out
        return output_image

    def give_intersection_kernels(self):
        """
            Skeletonize alma fonksiyonlarından biri
        """

        input_list = np.arange(8)
        taken_n = [4, 3]
        kernels = []
        for taken in taken_n:
            comb = self.generate_nonadjacent_combination(input_list, taken)
            tmp_ker = self.populate_intersection_kernel(comb)
            kernels.extend(tmp_ker)
        return kernels

    def find_line_intersection(self, input_image):
        """
            Skeletonize alma fonksiyonlarından biri
        """

        kernel = np.array(self.give_intersection_kernels())
        output_image = np.zeros(input_image.shape)
        for i in np.arange(len(kernel)):
            out = cv2.morphologyEx(input_image, cv2.MORPH_HITMISS, kernel[i, :, :])
            out = cv2.dilate(out, np.ones((7, 7), np.uint8), iterations=3)
            output_image = output_image + out

        return output_image

    def apply_skeletonize(self):
        """
            ROI si alınmış görüntünün iskeletini çıkaran ve kesişim noktalarını self.points listesine ekleyen fonksiyon.
        """
        self.apply_mask(self.image)
        self.soften(self.mask_sum_image)

        binary_image = self.soft_image > filters.threshold_otsu(self.soft_image)  # ???

        self.skeleton_image = skeletonize(binary_image, method='lee')

        lint_image = self.find_line_intersection(self.skeleton_image)

        processed_image = np.uint8(lint_image)
        contours, _ = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2:]

        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            self.points.append((int(x + w / 2), int(y + h / 2)))

    def apply_skeletonize_2(self):
        """
            Sadece frameler için geçerli fonksiyon. Daha iyi üst üste getirmek için burada ikinci iskelet alınır ve bu
        seferkinde uç noktalarda hesaba katılır. Uç noktaların da üst üste getirme de hesaba girmesi kameradaki balık
        gözü lensten oluşan yamuklukların kodu bozmasını engeller.
        """

        self.points_end = []

        self.apply_mask(self.warped_photo)
        self.soften(self.mask_sum_image)

        binary_image = self.soft_image > filters.threshold_otsu(self.soft_image)  # ???

        self.skeleton_warped = skeletonize(binary_image, method='lee')

        self.points_warped = list.copy(self.key_points)

        endl_photo = self.find_endoflines(self.skeleton_warped)
        processed_image = np.uint8(endl_photo)

        contours, _ = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2:]

        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            self.points_warped_end.append((int(x + w / 2), int(y + h / 2)))

        endl_frame = self.find_endoflines(self.skeleton_image)
        processed_image = np.uint8(endl_frame)

        contours, _ = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2:]

        for i in range(len(contours)):
            x, y, w, h = cv2.boundingRect(contours[i])
            self.points_end.append((int(x + w / 2), int(y + h / 2)))

    def find_key_points(self):  # ???
        """
            Bu fonksiyon apply_skeletonize fonksiyonundan alınan kesişim noktalarını bir sıraya sokar. Bunun için
        öncelikle self.points içindeki noktaları y değerine göre büyükten küçüğe sıralar. Sonrasında ilk üç noktayı alır
        ve bunları x değerine göre küçükten büyüğe sıralar bunlar bizim 1, 2 ve 3. noktalarımız oluyor. Sonrasında bu üç
        noktayı self.points ten çıkarrıyoruz ve üst satırı bulmak için ilk noktayı alıyoruz ve onun y değerinden 40 px
        üstünü ve altını self.pointste tarıyoruz ve bunlara self.line_2 listesine ekliyoruz. Bu noktaları sıralamak için
        en başta bulduğumuz ilk üç nokta için teker teker şu adımları uyguluyoruz: alt satırdaki noktanın x değerinin
        40 px sağ ve solunun içine giren üst satırdaki noktayı bul ve uygun sayıyı ver. 7 anahtar kesişim noktayı da
        bulunca bunları self.key_points değişkenine ekliyoruz. Bu fonksiyon ayrıca aldığı error lere göre True ve False
        döndürebiliyor.
        """

        input_points = self.points
        last_index = 0

        num = len(input_points)

        for i in range(num):
            x1, y1 = input_points[i]
            x2, y2 = input_points[i + 1]
            e = 50
            if abs(y2 - y1) < e:
                self.line_1.append(input_points[i])
            else:
                self.line_1.append(input_points[i])
                last_index = i
                if len(self.line_1) == 3:
                    break
                else:
                    self.error_msg = "Line 1 Error !!!"
                    return False

        self.line_2.append(input_points[last_index + 1])
        for i in range(last_index + 1, num - 1):
            x1, y1 = input_points[i]
            x2, y2 = input_points[i + 1]
            e = 60
            if abs(y2 - y1) < e:
                self.line_2.append(input_points[i + 1])
            else:
                break

        if len(self.line_2) < 4:
            self.error_msg = "Line 2 Error !!!"
            return False

        self.line_1.sort()
        self.line_2.sort()

        e = 30

        x1, y1 = self.line_1[0]
        for a in range(len(self.line_2)):
            x2, y2 = self.line_2[a]
            if x1 - e < x2 < x1 + e:
                point_4 = (x2, y2)
                break

        x1, y1 = self.line_1[1]
        for a in range(len(self.line_2)):
            x2, y2 = self.line_2[a]
            if x1 - e < x2 < x1 + e:
                point_5 = (x2, y2)
                break

        point_7_list = []
        x1, y1 = self.line_1[2]
        for i in range(len(self.line_2)):
            x2, y2 = self.line_2[i]
            if x1 - e < x2 < x1 + e:
                point_6 = (x2, y2)
                for a in range(len(self.line_2)):
                    x3, y3 = self.line_2[a]
                    if y2 - e < y3 < y2 + e and x2 < x3:
                        point_7_list.append((x3, y3))
                point_7_list.sort()
                if not point_7_list:
                    self.error_msg = "Point 7 Error !!!"
                    return False
                point_7 = point_7_list[0]

        for i in range(len(self.line_1)):
            self.key_points.insert(i, self.line_1[i])

        try:
            self.key_points.insert(3, point_4)
            self.key_points.insert(4, point_5)
            self.key_points.insert(5, point_6)
            self.key_points.insert(6, point_7)
        except UnboundLocalError:
            self.error_msg = "Unbound Local Error !!!"
            return False

        return True

    def find_key_points_end(self):
        """
            Bu fonksiyon birinci kez üst üste gelen önceki mercan ile sonraki mercanın uç noktalarının birbirine en
        yakın olanları bulup ilgili listelere aynı sırada ekliyor
        """

        # self.key_points = self.key_points[:7]
        # self.points_warped = self.points_warped[:7]

        error = 25
        for i in range(len(self.points_warped_end)):
            (xW, yW) = self.points_warped_end[i]
            for a in range(len(self.points_end)):
                (xF, yF) = self.points_end[a]
                if xW - error < xF < xW + error and yW - error < yF < yW + error:  # Ayarlanabilir !!
                    self.key_points.append((xF, yF))
                    cv2.circle(self.copy_image, (xF, yF), error, (0, 0, 255), 1, -1)
                    self.points_warped.append((xW, yW))
                    break
        # print("Key Points Length : ", len(self.key_points))
        # print("Key Points Warped Length : ", len(self.points_warped))

    def overlap(self, before_photo, key_points_photo):
        """
            Bu fonksiyon kesişim noktaları bulunan önceki mercan ile sonraki mercanı homografisini çıkarıp perspektifini
        büküyor.
        """

        self.key_points_photo = key_points_photo
        key_points_photo = np.float32(key_points_photo)
        key_points_frame = np.float32(self.key_points)

        try:
            h, _ = cv2.findHomography(key_points_photo, key_points_frame)
        except Exception as e:
            print("Homografi Error : ", e)
        else:
            height, width, channels = self.copy_image.shape
            self.warped_photo = cv2.warpPerspective(before_photo, h, (width, height))
            self.apply_bitwise(self.warped_photo)
            self.overlapped_image = cv2.addWeighted(self.bitwise_image, 0.5, self.copy_image, 0.5, 0)

    def find_difference(self, photo, input_frame, output_frame):
        """
            Bu fonksiyon perspektifi alınmış önceki mercan ile yeni gelen frame arasındakifarkları bularak ilgili
        renkteki dikdörtgenle görüntü üstünde gösteriyor. Bu işlemler için basit maskelenmiş görüntülere bitwise_xor ve
        bitwise_and uygulayarak çıktı görüntüler üzerindeki beyaz bölgeleri hesaplar ve önceden belirlenmiş değerden
        büyük olanları dikdörtgenle işaretler.
        """
        diff = 10
        # self.transform_hsv(imgFoto)
        mask_photo = self.apply_mask(photo)
        mask_frame = self.apply_mask(input_frame)
        # cv2.imshow("Mask Video", mask_frame)
        xor_mask = cv2.bitwise_xor(mask_photo, mask_frame)
        xor_mask = cv2.erode(xor_mask, self.kernel_3_3)
        xor_mask = self.soften(xor_mask)
        # cv2.imshow("Eklenme - Cikma", xor_mask)

        pink_mask_photo = self.apply_pink_mask(photo)
        pink_mask_frame = self.apply_pink_mask(input_frame)
        xor_pink_mask = cv2.bitwise_xor(pink_mask_photo, pink_mask_frame)
        xor_pink_mask = self.soften(xor_pink_mask)
        white_mask_photo = self.apply_white_mask(photo)
        white_mask_frame = self.apply_white_mask(input_frame)
        xor_white_mask = cv2.bitwise_xor(white_mask_photo, white_mask_frame)
        xor_white_mask = self.soften(xor_white_mask)

        contours, _ = cv2.findContours(xor_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]
        damage_or_recovered = []

        for i in range(len(contours)):
            area = cv2.contourArea(contours[i])
            if area > 600:
                # print(area)
                (x, y, w, h) = cv2.boundingRect(contours[i])
                damage_or_recovered.append((x, y, w, h))

        for i in range(len(damage_or_recovered)):
            (x, y, w, h) = damage_or_recovered[i]
            roi = mask_frame[y:y + h, x:x + w]
            total_point = w * h
            white_points_num = cv2.countNonZero(roi)
            percentage = int(white_points_num / total_point * 100)
            # print(percentage)
            if percentage > 10:
                # EKLEME
                cv2.rectangle(output_frame, (x - diff, y - diff), (x + w + diff, y + h + diff), (0, 255, 0), 2)
            else:
                # ÇIKARTMA
                cv2.rectangle(output_frame, (x - diff, y - diff), (x + w + diff, y + h + diff), (0, 255, 255), 2)

        and_color_change = cv2.bitwise_and(xor_pink_mask, xor_white_mask)
        and_color_change = self.soften(and_color_change)
        # cv2.imshow("Renk Degisimi", and_color_change)

        contours, _ = cv2.findContours(and_color_change, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]
        growth_or_blotching = []
        for i in range(len(contours)):
            area = cv2.contourArea(contours[i])
            if area > 600:
                # print(area)
                (x, y, w, h) = cv2.boundingRect(contours[i])
                growth_or_blotching.append((x, y, w, h))
                cv2.rectangle(output_frame, (x - diff, y - diff), (x + w + diff, y + h + diff), (255, 0, 0), 2)

        for i in range(len(growth_or_blotching)):
            (x, y, w, h) = growth_or_blotching[i]
            roi = pink_mask_frame[y:y + h, x:x + w]
            total_point = w * h
            white_points_num = cv2.countNonZero(roi)
            percentage = int(white_points_num / total_point * 100)
            # print(percentage)
            if percentage > 10:
                # PEMBE DEĞİŞİMİ
                cv2.rectangle(output_frame, (x - diff, y - diff), (x + w + diff, y + h + diff), (255, 0, 0), 2)
            else:
                # BEYAZ DEĞİŞİMİ
                cv2.rectangle(output_frame, (x - diff, y - diff), (x + w + diff, y + h + diff), (0, 0, 255), 2)
        """
        cv2.putText(self.copy_image_2, "Growth", (10, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(self.copy_image_2, "Death", (160, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(self.copy_image_2, "Bleaching", (280, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(self.copy_image_2, "Recovered", (450, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
        """

    def show_image(self):
        """
            Sadece önceki mercan görselini ekran göstermek için kullanılır.
        """

        for i in range(len(self.points)):
            (x, y) = self.points[i]
            cv2.circle(self.copy_image, (x, y), 3, (255, 0, 0), 1, -1)

        for i in range(len(self.key_points)):
            (x, y) = self.key_points[i]
            cv2.putText(self.copy_image, str(i + 1), (x + 2, y + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1, cv2.LINE_AA)
        for i in range(len(self.line_1)):
            (x, y) = self.line_1[i]
            e = 20
            cv2.line(self.copy_image, (x + e, y), (x + e, 0), (0, 0, 255), 1)
            cv2.line(self.copy_image, (x - e, y), (x - e, 0), (0, 0, 255), 1)

        # cv2.imshow("Skeleton Image", self.skeleton_image)
        # cv2.imshow("Image", self.copy_image)

    def show_frame(self, start_time):
        """
            Sadece gelen frame leri ekrana basmak için kullanılır.
        """

        input_frame = self.copy_image
        cv2.line(input_frame, (200, 0), (200, 540), (0, 0, 0), 2)
        cv2.line(input_frame, (760, 0), (760, 540), (0, 0, 0), 2)
        cv2.putText(input_frame, "Ekleme", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(input_frame, "Cikarma", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(input_frame, "Pembeden", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(input_frame, "Beyaza", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(input_frame, "Beyazdan", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(input_frame, "Pembeye", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(input_frame, self.error_msg, (10, 530), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        end_time = time.time()
        diff = 0.03 - (end_time - start_time)
        if diff > 0:
            time.sleep(diff)
        end_time_2 = time.time()
        fps = int(1 / (end_time_2 - start_time))
        cv2.putText(input_frame, str(fps), (840, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow("Video {0}x{1}".format(input_frame.shape[1], input_frame.shape[0]), input_frame)


if __name__ == "__main__":

    coral_reef_before_photo = cv2.imread("/home/ibrahim/Masaüstü/coral_colony_0.png")
    coral_reef_before_photo = cv2.resize(coral_reef_before_photo, (600, 600))
    coral_reef_after_photo = cv2.imread("/home/ibrahim/Masaüstü/coral_colony_4.png")
    coral_reef_after_photo = cv2.resize(coral_reef_after_photo, (600, 600))

    print("Coral Version : ", Coral.version)
    # cv2.imshow("Image", coral_reef_before_photo)
    coral_reef_before = Coral()
    coral_reef_before.get_image(coral_reef_before_photo)

    coral_reef_before.apply_skeletonize()
    # cv2.imshow("Mask Before", coral_reef_before.mask_sum_image)
    # cv2.imshow("Skeleton Before", coral_reef_before.skeleton_image)

    print("Key Points Coral Reef Before : ", coral_reef_before.find_key_points())
    print("Error : ", coral_reef_before.error_msg)
    coral_reef_before.show_image()
    cv2.imshow("Points Before", coral_reef_before.copy_image)

    coral_reef_after = Coral()
    coral_reef_after.get_image(coral_reef_after_photo)

    coral_reef_after.apply_skeletonize()
    # cv2.imshow("Mask After", cv2.resize(coral_reef_after.mask_sum_image, (600, 600)))
    # cv2.imshow("Skeleton After", coral_reef_after.skeleton_image)
    print("Key Points Coral Reef After : ", coral_reef_after.find_key_points())
    print("Error : ", coral_reef_after.error_msg)
    coral_reef_after.show_image()
    cv2.imshow("Points After", coral_reef_after.copy_image)

    coral_reef_after.overlap(coral_reef_before.copy_image, coral_reef_before.key_points)
    cv2.imshow("Overlapped Image", coral_reef_after.overlapped_image)

    coral_reef_after.apply_skeletonize_2()
    coral_reef_after.find_key_points_end()

    coral_reef_after.overlap(coral_reef_after.warped_photo, coral_reef_after.points_warped)

    cv2.imshow("Overlapped Image 2", coral_reef_after.overlapped_image)

    coral_reef_after.find_difference(coral_reef_after.warped_photo, coral_reef_after.copy_image_2,
                                     coral_reef_after.copy_image_2)
    cv2.imshow("Difference", coral_reef_after.copy_image_2)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
