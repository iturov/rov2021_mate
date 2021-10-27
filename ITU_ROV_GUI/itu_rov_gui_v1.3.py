"""
2021 Mate Rov yarışması için hazırlanan ITU ROV GUI
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from master.arducam.arducam import Video  # Front and bottom camera client with gstreamer

# Mate Coral Colony mission => Ibrahim Kose, Alperen Kiyak, Ali Esad Ugur
from missions.coral_colony.coral_colony_v1 import Coral
# Mate Subway Car mission => Hasan Fatih Durkaya, Hidayet Ersin Dursun, Faik Eren Altun
from missions.photomosaic.Subway_car import Subway_car
# Mate Flying Transect Line and Mapping mission => Atacan Yavuz, Aybala Dilara Hellagün, Emre Anıl Oğuz
from missions.mapping.mapping_photo import Mapping
from missions.autonomous_flying.flying_transect_line import RovDrive, LineDetect

import cv2
import numpy as np
import time
import socket
import pygame
import configparser


class MainWindow(QMainWindow):
    """
    Arayüz yapısını oluşturan MainWindow fonksiyonlarının bulunduğu sınıftır.
    """
    def __init__(self):
        super().__init__()
        # self.setupUi()
        self.system = True
        self.camera_var = 0
        self.video_record = False
        self.recorder = None

        self.microrov_key = [ord("W"), ord("A"), ord("S"), ord("D"), ord("Q"), ord("E")]
        self.masterRov_key = [ord("J"), ord("K")]
        self.microKeys = list()
        self.rovKeys = list()

        self.message = ""
        self.warnings_list = []

        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        ####################################################   CORAL COLONY

        self.coralMission = False

        self.coral_colony_before_photo = cv2.imread("missions/coral_colony/Photos/coral_colony_0.png")
        self.coral_colony_before_photo = cv2.resize(self.coral_colony_before_photo, (600, 600))

        self.coral_colony_before = Coral()

        self.coral_colony_before.get_image(self.coral_colony_before_photo)
        self.coral_colony_before.apply_skeletonize()

        self.coral_colony_before.find_key_points()
        self.coral_colony_before.show_image()

        ####################################################   MAPPING AND AUTONOMOUS FLYING

        self.line_detect = LineDetect()
        self.autonomousMission = False

        self.mapping = Mapping()

        self.mapping.coral1 = cv2.imread("missions/mapping/icons/Coral1.png")
        self.mapping.coral1_map = cv2.imread("missions/mapping/icons/Coral1_map.png")

        self.mapping.coral2 = cv2.imread("missions/mapping/icons/Coral2.png")
        self.mapping.coral2_map = cv2.imread("missions/mapping/icons/Coral2_map.png")

        self.mapping.dot = cv2.imread("missions/mapping/icons/dot.png")
        self.mapping.dot_map = cv2.imread("missions/mapping/icons/dot_map.png")

        self.mapping.red_star = cv2.imread("missions/mapping/icons/RedStar.png")
        self.mapping.red_star_map = cv2.imread("missions/mapping/icons/RedStar_map.png")

        self.mapping.yellow_square = cv2.imread("missions/mapping/icons/yellowSquare.png")
        self.mapping.yellow_square_map = cv2.imread("missions/mapping/icons/yellowSquare_map.png")

        self.mapping.empty = cv2.imread("missions/mapping/icons/Empty.png")

        self.map = np.zeros((900, 450, 3), dtype=np.uint8)
        self.map[:] = [255, 255, 255]

        ####################################################   SUBWAY CAR

        self.subway_car = Subway_car()
        self.surface_num = 1
        self.photomosaicMission = False

    def setupUi(self):
        """
        Tüm layout, group ve butonların ayarlandığı yerdir.
        """
        print("Welcome to ITU ROV GUI 2021")

        self.setWindowIcon(QtGui.QIcon("icons/favicon.ico"))
        # self.setWindowModality(QtCore.Qt.WindowModal)
        self.resize(1400, 940)
        self.main_gl = QtWidgets.QWidget()
        self.main_gl.setObjectName("main_gl")
        self.gridLayout = QtWidgets.QGridLayout(self.main_gl)
        self.gridLayout.setObjectName("gridLayout")
        self.rightside_gl = QtWidgets.QGridLayout()
        self.rightside_gl.setObjectName("rightside_gl")
        self.main_tw = QtWidgets.QTabWidget(self.main_gl)
        self.main_tw.setObjectName("main_tw")
        self.TASKS = QtWidgets.QWidget()
        self.TASKS.setObjectName("TASKS")

        self.buton_minimum_height = 32

        self.task_gridLayout = QtWidgets.QGridLayout(self.TASKS)
        self.task_gridLayout.setSpacing(10)
        self.task_gridLayout.setObjectName("task_gridLayout")
        self.autonomous_gb = QtWidgets.QGroupBox(self.TASKS)
        self.autonomous_gb.setObjectName("autonomous_gb")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.autonomous_gb)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.autonomous_gb.setStyleSheet(
            "QGroupBox#autonomous_gb:title "
            "{subcontrol-origin: margin; subcontrol-position: top center; "
            "padding-left: 10px; padding-right: 10px;}"
            "QGroupBox#autonomous_gb "
            "{border :2px solid rgb(70,70,70); margin-top: 20px; border-radius: 10px;} ")

        self.stop_autonomous_pb = QtWidgets.QPushButton(self.autonomous_gb)
        self.stop_autonomous_pb.setObjectName("stop_autonomous_pb")
        self.gridLayout_3.addWidget(self.stop_autonomous_pb, 2, 1, 1, 1)
        self.stop_autonomous_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.mapping_cb = QtWidgets.QCheckBox(self.autonomous_gb)
        self.mapping_cb.setObjectName("mapping_cb")
        self.gridLayout_3.addWidget(self.mapping_cb, 2, 2, 1, 1)

        self.fly_auto_hl = QtWidgets.QHBoxLayout()
        self.fly_auto_hl.setObjectName("fly_auto_hl")
        self.start_autonomous_pb = QtWidgets.QPushButton(self.autonomous_gb)

        self.start_autonomous_pb.setObjectName("start_autonomous_pb")
        self.fly_auto_hl.addWidget(self.start_autonomous_pb)
        self.start_autonomous_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.createmap_pb = QtWidgets.QPushButton(self.autonomous_gb)
        self.createmap_pb.setObjectName("createmap_pb")
        self.fly_auto_hl.addWidget(self.createmap_pb)
        self.createmap_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.gridLayout_3.addLayout(self.fly_auto_hl, 1, 1, 1, 2)

        self.test_autonomous_pb = QtWidgets.QPushButton(self.autonomous_gb)
        self.test_autonomous_pb.setObjectName("test_autonomous_pb")
        self.gridLayout_3.addWidget(self.test_autonomous_pb, 0, 1, 1, 2)
        self.test_autonomous_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.task_gridLayout.addWidget(self.autonomous_gb, 0, 0, 1, 4)
        self.coralReef_gb = QtWidgets.QGroupBox(self.TASKS)
        self.coralReef_gb.setObjectName("mapping_gb")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.coralReef_gb)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.coralReef_gb.setStyleSheet(
            "QGroupBox#mapping_gb:title "
            "{subcontrol-origin: margin; subcontrol-position: top center; "
            "padding-left: 10px; padding-right: 10px;}"
            "QGroupBox#mapping_gb "
            "{border :2px solid rgb(70,70,70); margin-top: 20px; border-radius: 10px;} ")

        self.stop_mapping_pb = QtWidgets.QPushButton(self.coralReef_gb)
        self.stop_mapping_pb.setObjectName("stop_mapping_pb")
        self.gridLayout_4.addWidget(self.stop_mapping_pb, 3, 0, 1, 1)
        self.stop_mapping_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.coral_photo_pb = QtWidgets.QPushButton(self.coralReef_gb)
        self.coral_photo_pb.setObjectName("coral_photo_pb")
        self.gridLayout_4.addWidget(self.coral_photo_pb, 1, 0, 1, 2)
        self.coral_photo_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.start_mapping_pb = QtWidgets.QPushButton(self.coralReef_gb)
        self.start_mapping_pb.setObjectName("start_mapping_pb")
        self.gridLayout_4.addWidget(self.start_mapping_pb, 2, 0, 1, 1)
        self.start_mapping_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.start2_mapping_pb = QtWidgets.QPushButton(self.coralReef_gb)
        self.start2_mapping_pb.setObjectName("start2_mapping_pb")
        self.gridLayout_4.addWidget(self.start2_mapping_pb, 2, 1, 1, 1)
        self.start2_mapping_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.test_mapping_pb = QtWidgets.QPushButton(self.coralReef_gb)
        self.test_mapping_pb.setObjectName("test_mapping_pb")
        self.gridLayout_4.addWidget(self.test_mapping_pb, 3, 1, 1, 1)
        self.test_mapping_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.task_gridLayout.addWidget(self.coralReef_gb, 1, 0, 1, 4)

        self.subwaycar_gb = QtWidgets.QGroupBox(self.TASKS)
        self.subwaycar_gb.setObjectName("subwaycar_gb")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.subwaycar_gb)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.subwaycar_gb.setStyleSheet(
            "QGroupBox#subwaycar_gb:title "
            "{subcontrol-origin: margin; subcontrol-position: top center; "
            "padding-left: 10px; padding-right: 10px;}"
            "QGroupBox#subwaycar_gb "
            "{border :2px solid rgb(70,70,70); margin-top: 20px; border-radius: 10px;} ")

        self.tpicos_pb = QtWidgets.QPushButton(self.subwaycar_gb)
        self.tpicos_pb.setObjectName("tpicos_pb")
        self.gridLayout_6.addWidget(self.tpicos_pb, 1, 0, 1, 2)
        self.tpicos_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.createphotom_pb = QtWidgets.QPushButton(self.subwaycar_gb)
        self.createphotom_pb.setObjectName("createphotom_pb")
        self.gridLayout_6.addWidget(self.createphotom_pb, 2, 0, 1, 1)
        self.createphotom_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.start_photomastic_pb_2 = QtWidgets.QPushButton(self.subwaycar_gb)
        self.start_photomastic_pb_2.setObjectName("start_photomastic_pb_2")
        self.gridLayout_6.addWidget(self.start_photomastic_pb_2, 2, 1, 1, 1)
        self.start_photomastic_pb_2.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.start_photomastic_pb = QtWidgets.QPushButton(self.subwaycar_gb)
        self.start_photomastic_pb.setObjectName("start_photomastic_pb")
        self.gridLayout_6.addWidget(self.start_photomastic_pb, 0, 0, 1, 1)
        self.start_photomastic_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.stop_photomastic_pb = QtWidgets.QPushButton(self.subwaycar_gb)
        self.stop_photomastic_pb.setObjectName("stop_photomastic_pb")
        self.gridLayout_6.addWidget(self.stop_photomastic_pb, 0, 1, 1, 1)
        self.stop_photomastic_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.task_gridLayout.addWidget(self.subwaycar_gb, 2, 0, 1, 4)
        self.mussel_gb = QtWidgets.QGroupBox(self.TASKS)
        self.mussel_gb.setObjectName("mussel_gb")
        self.mussel_gb.setStyleSheet(
            "QGroupBox#mussel_gb:title "
            "{subcontrol-origin: margin; subcontrol-position: top center; "
            "padding-left: 10px; padding-right: 10px;}"
            "QGroupBox#mussel_gb "
            "{border :2px solid rgb(70,70,70); margin-top: 20px; border-radius: 10px;} ")
        self.gridLayout_mussel = QtWidgets.QGridLayout(self.mussel_gb)
        self.gridLayout_mussel.setObjectName("gridLayout_mussel")

        self.counted_mussel_sb = QtWidgets.QSpinBox(self.mussel_gb)
        self.counted_mussel_lb = QtWidgets.QLabel(self.mussel_gb)

        self.length_mussel_sb = QtWidgets.QSpinBox(self.mussel_gb)
        self.length_mussel_lb = QtWidgets.QLabel(self.mussel_gb)

        self.width_mussel_sb = QtWidgets.QSpinBox(self.mussel_gb)
        self.width_mussel_lb = QtWidgets.QLabel(self.mussel_gb)

        self.litreperhour_mussel_sb= QtWidgets.QDoubleSpinBox(self.mussel_gb)
        self.litreperhour_mussel_lb = QtWidgets.QLabel(self.mussel_gb)

        self.calculate_pb = QtWidgets.QPushButton(self.mussel_gb)
        self.calculation_lb = QtWidgets.QLabel(self.mussel_gb)

        self.gridLayout_mussel.addWidget(self.counted_mussel_sb, 0, 1, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.gridLayout_mussel.addWidget(self.counted_mussel_lb, 0, 0, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.gridLayout_mussel.addWidget(self.length_mussel_sb, 0, 3, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.gridLayout_mussel.addWidget(self.length_mussel_lb, 0, 2, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.gridLayout_mussel.addWidget(self.width_mussel_sb, 1, 1, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.gridLayout_mussel.addWidget(self.width_mussel_lb, 1, 0, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.gridLayout_mussel.addWidget(self.litreperhour_mussel_sb, 1, 3, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.gridLayout_mussel.addWidget(self.litreperhour_mussel_lb, 1, 2, 1, 1, alignment=QtCore.Qt.AlignCenter)

        self.gridLayout_mussel.addWidget(self.calculate_pb, 2, 0, 1, 2)
        self.gridLayout_mussel.addWidget(self.calculation_lb, 2, 2, 1, 2, alignment=QtCore.Qt.AlignCenter)

        self.task_gridLayout.addWidget(self.mussel_gb, 3, 1, 2, 3)

        self.videorecord_pb = QtWidgets.QPushButton(self.TASKS)
        self.videorecord_pb.setObjectName("videorecord_pb")
        self.task_gridLayout.addWidget(self.videorecord_pb, 3, 0, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.videorecord_pb.setEnabled(False)
        self.videorecord_pb.setFixedSize(60, 60)
        self.videorecord_pb.setStyleSheet(
            "QPushButton#videorecord_pb {border-image: url(icons/take_video.png);} "
            "QPushButton#videorecord_pb:hover {border-image: url(icons/take_video_3.png); border-radius : 35;} "
            "QPushButton#videorecord_pb:pressed {border-image: url(icons/take_pressed.png); border-radius : 35;}")

        self.takephoto_pb = QtWidgets.QPushButton(self.TASKS)
        self.takephoto_pb.setObjectName("takephoto_pb")
        self.task_gridLayout.addWidget(self.takephoto_pb, 4, 0, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.takephoto_pb.setEnabled(False)
        self.takephoto_pb.setFixedSize(60, 60)
        self.takephoto_pb.setStyleSheet(
            "QPushButton#takephoto_pb {border-image: url(icons/take_photo.png);border-radius : 35;} "
            "QPushButton#takephoto_pb:hover {border-image: url(icons/take_photo_3.png); border-radius : 35;} "
            "QPushButton#takephoto_pb:pressed {border-image: url(icons/take_pressed.png); border-radius : 35;}")

        self.INFO = QtWidgets.QWidget()
        self.INFO.setObjectName("INFO")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.INFO)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.info_label = QtWidgets.QLabel(self.INFO)
        self.info_label.setMaximumWidth(250)
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setText("ITU ROV Team is a team of undergraduate students that are developing a "
                                "Remotely Operated Vehicle(ROV) to attend the MATE ROV Competition in Tenessee in 2021."
                                "All the software and hardware will be open source.")
        self.info_label.setObjectName("info_label")
        self.gridLayout_5.addWidget(self.info_label, 0, 0, 1, 1)

        self.rightside_gl.addWidget(self.main_tw, 0, 0, 1, 1)
        self.counter_gb = QtWidgets.QGroupBox(self.main_gl)
        self.counter_gb.setObjectName("counter_gb")
        self.gridLayout_counter = QtWidgets.QGridLayout(self.counter_gb)
        self.gridLayout_counter.setObjectName("gridLayout_counter")
        self.counter_gb.setStyleSheet("QGroupBox#counter_gb {border :1px solid grey;}")

        self.counterstart_pb = QtWidgets.QPushButton(self.main_gl)
        self.counterstart_pb.setObjectName("counterstart_pb")
        self.counterstart_pb.setIcon(QIcon("icons/icon-start.png"))
        self.counterstart_pb.setIconSize(QSize(17, 17))
        self.gridLayout_counter.addWidget(self.counterstart_pb, 0, 0, 1, 1)
        self.counterstart_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.counterstop_pb = QtWidgets.QPushButton(self.main_gl)
        self.counterstop_pb.setEnabled(False)
        self.counterstop_pb.setObjectName("counterstop_pb")
        self.counterstop_pb.setIcon(QIcon("icons/icon-pause.png"))
        self.counterstop_pb.setIconSize(QSize(17, 17))
        self.gridLayout_counter.addWidget(self.counterstop_pb, 0, 1, 1, 1)
        self.counterstop_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))

        self.rightside_gl.addWidget(self.counter_gb, 2, 0, 1, 1)
        self.counter_lcd = QtWidgets.QLCDNumber(self.main_gl)
        self.counter_lcd.display("00:00")
        self.counter_lcd.setObjectName("counter_lcd")
        self.counter_lcd.setMaximumHeight(80)
        self.gridLayout_counter.addWidget(self.counter_lcd, 1, 0, 1, 2)
        self.ROV_LOGO_lb = QtWidgets.QLabel(self.main_gl)
        self.ROV_LOGO_lb.setText("")
        self.ROV_LOGO_lb.setPixmap(QtGui.QPixmap("pp3.png"))
        self.ROV_LOGO_lb.setScaledContents(False)
        self.ROV_LOGO_lb.setAlignment(QtCore.Qt.AlignCenter)
        self.ROV_LOGO_lb.setWordWrap(False)
        self.ROV_LOGO_lb.setObjectName("ROV_LOGO_lb")
        self.rightside_gl.addWidget(self.ROV_LOGO_lb, 3, 0, 1, 1)
        self.status_gl = QtWidgets.QGridLayout()
        self.status_gl.setObjectName("status_gl")
        self.microrov_st_lb = QtWidgets.QLabel(self.main_gl)
        self.microrov_st_lb.setObjectName("microrov_st_lb")
        self.status_gl.addWidget(self.microrov_st_lb, 2, 2, 1, 1, alignment=Qt.AlignCenter)
        self.microrov_lb = QtWidgets.QLabel(self.main_gl)
        self.microrov_lb.setObjectName("microrov_lb")
        self.status_gl.addWidget(self.microrov_lb, 2, 0, 1, 1)
        self.vehicle_lb = QtWidgets.QLabel(self.main_gl)
        self.vehicle_lb.setObjectName("vehicle_lb")
        self.status_gl.addWidget(self.vehicle_lb, 0, 0, 1, 1)
        self.vehicle_st_lb = QtWidgets.QLabel(self.main_gl)
        self.vehicle_st_lb.setObjectName("vehicle_st_lb")
        self.status_gl.addWidget(self.vehicle_st_lb, 0, 2, 1, 1, alignment=Qt.AlignCenter)
        self.h1_hl = QtWidgets.QFrame(self.main_gl)
        self.h1_hl.setFrameShape(QtWidgets.QFrame.HLine)
        self.h1_hl.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.h1_hl.setObjectName("h1_hl")
        self.status_gl.addWidget(self.h1_hl, 1, 0, 1, 3)
        self.vehicle_vl = QtWidgets.QFrame(self.main_gl)
        self.vehicle_vl.setFrameShape(QtWidgets.QFrame.VLine)
        self.vehicle_vl.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.vehicle_vl.setObjectName("vehicle_vl")
        self.status_gl.addWidget(self.vehicle_vl, 0, 1, 1, 1)
        self.microrov_vl = QtWidgets.QFrame(self.main_gl)
        self.microrov_vl.setFrameShape(QtWidgets.QFrame.VLine)
        self.microrov_vl.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.microrov_vl.setObjectName("microrov_vl")
        self.status_gl.addWidget(self.microrov_vl, 2, 1, 1, 1)
        self.rightside_gl.addLayout(self.status_gl, 4, 0, 1, 1)
        self.rightside_gl.setRowStretch(2, 70)
        self.gridLayout.addLayout(self.rightside_gl, 0, 1, 1, 1)
        self.leftside_gl = QtWidgets.QGridLayout()
        self.leftside_gl.setObjectName("leftside_gl")
        self.camera_gb = QtWidgets.QGroupBox(self.main_gl)
        self.camera_gb.setObjectName("camera_gb")
        self.camera_gb.setStyleSheet(
            "QGroupBox#camera_gb:title "
            "{subcontrol-origin: margin; subcontrol-position: top center; "
            "background-color: grey; padding: 6px 50px 4px 50px;"
            "border-top-left-radius: 10px; border-top-right-radius: 10px;}"
            "QGroupBox#camera_gb "
            "{border :2px solid grey; margin-top: 26px; border-radius: 15px;} ")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.camera_gb)
        self.verticalLayout.setObjectName("verticalLayout")
        self.cam_label = QtWidgets.QLabel(self.camera_gb)
        self.cam_label.setText("")
        self.cam_label.setObjectName("cam_label")
        self.cam_label.setPixmap(QtGui.QPixmap("icons/icon-no-video.png"))
        self.cam_label.setAlignment(QtCore.Qt.AlignCenter)
        self.cam_label.resize(1280, 740)
        self.verticalLayout.addWidget(self.cam_label)
        self.verticalLayout.setStretch(0, 90)
        self.leftside_gl.addWidget(self.camera_gb, 0, 0, 1, 2)
        self.warnings_vl = QtWidgets.QVBoxLayout()
        self.warnings_vl.setObjectName("warnings_vl")
        self.warnings_lb = QtWidgets.QLabel(self.main_gl)
        self.warnings_lb.setObjectName("warnings_lb")
        self.warnings_vl.addWidget(self.warnings_lb)
        ###############

        self.warnings_st_lb = QtWidgets.QLabel(self.main_gl)
        self.warnings_st_lb.setText("\n " * 100 + " " * 180)
        self.warnings_st_lb.setAlignment(Qt.AlignLeading | Qt.AlignLeft)
        self.warnings_st_lb.setObjectName("warnings_st_lb")
        self.warnings_st_lb.setWordWrap(True)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidget(self.warnings_st_lb)
        self.warnings_vl.addWidget(self.scroll_area)
        ################

        self.warnings_vl.setStretch(0, 20)
        self.warnings_vl.setStretch(1, 80)
        self.leftside_gl.addLayout(self.warnings_vl, 1, 0, 1, 1)
        self.leftside_gl.setRowStretch(0, 80)
        self.leftside_gl.setRowStretch(1, 20)
        ################################################################## CAMERA

        self.vehicle_cam_gl = QtWidgets.QGridLayout()
        self.vehicle_cam_gl.setObjectName("vehicle_cam_gl")

        self.vehicle_im_vl = QtWidgets.QVBoxLayout()
        self.vehicle_im_vl.setObjectName("vehicle_im_vl")

        self.vehicle_im_lb = QtWidgets.QLabel(self.main_gl)
        self.vehicle_im_lb.setObjectName("vehicle_im_lb")
        self.vehicle_im_vl.addWidget(self.vehicle_im_lb)
        self.vehicle_im_lb.setFixedSize(250, 130)
        self.vehicle_im_lb.setPixmap(QtGui.QPixmap("icons/vehicle.png"))
        self.vehicle_im_lb.setScaledContents(True)
        self.vehicle_cam_gl.addLayout(self.vehicle_im_vl, 0, 1, 1, 1)
        self.leftside_gl.addLayout(self.vehicle_cam_gl, 1, 1, 1, 1)
        self.vehicle_im_lb.setAlignment(QtCore.Qt.AlignCenter)

        self.frontcam_pb = QtWidgets.QPushButton(self.main_gl)
        self.frontcam_pb.setObjectName("frontcam_pb")
        self.vehicle_cam_gl.addWidget(self.frontcam_pb, 0, 2, 1, 1)
        self.frontcam_pb.setFixedSize(40, 40)
        self.frontcam_pb.setIcon(QIcon("icons/front_cam.png"))
        self.frontcam_pb.setIconSize(QSize(30, 30))

        self.bottomcam_pb = QtWidgets.QPushButton(self.main_gl)
        self.bottomcam_pb.setObjectName("bottomcam_pb")
        self.vehicle_cam_gl.addWidget(self.bottomcam_pb, 1, 1, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.bottomcam_pb.setFixedSize(40, 40)
        self.bottomcam_pb.setIcon(QIcon("icons/bottom_cam.png"))
        self.bottomcam_pb.setIconSize(QSize(30, 30))

        self.microrovcam_pb = QtWidgets.QPushButton(self.main_gl)
        self.microrovcam_pb.setObjectName("microrovcam_pb")
        self.vehicle_cam_gl.addWidget(self.microrovcam_pb, 0, 0, 1, 1)
        self.microrovcam_pb.setFixedSize(40, 40)
        self.microrovcam_pb.setIcon(QIcon("icons/microrov_cam.png"))
        self.microrovcam_pb.setIconSize(QSize(30, 30))

        self.closecam_pb = QtWidgets.QPushButton(self.main_gl)
        self.closecam_pb.setObjectName("closecam_pb")
        self.vehicle_cam_gl.addWidget(self.closecam_pb, 1, 2, 1, 1)
        self.closecam_pb.setFixedSize(40, 40)
        self.closecam_pb.setIcon(QIcon("icons/icon-camera.png"))
        self.closecam_pb.setIconSize(QSize(30, 30))

        ################################################################## SETTİNGS

        self.SETT = QtWidgets.QWidget()
        self.SETT.setObjectName("SETT")
        self.sett_gridLayout = QtWidgets.QGridLayout(self.SETT)
        self.sett_gridLayout.setObjectName("sett_gridLayout")
        self.sett_gridLayout.setSpacing(10)

        self.mappingSett_gb = QtWidgets.QGroupBox(self.SETT)
        self.mappingSett_gb.setObjectName("mappingSett_gb")
        self.mappingSett_gb.setStyleSheet(
            "QGroupBox#mappingSett_gb:title "
            "{subcontrol-origin: margin; subcontrol-position: top center; padding-left: 10px; padding-right: 10px;}"
            "QGroupBox#mappingSett_gb "
            "{border :2px solid rgb(70,70,70); margin-top: 20px; border-radius: 10px;} ")

        self.mapping_sett_gl = QtWidgets.QGridLayout(self.mappingSett_gb)
        self.mapping_sett_gl.setObjectName("mapping_sett_gl")
        self.mapping_sett_gl.setSpacing(10)

        self.mapping_sett_pb1 = QPushButton(self.mappingSett_gb)
        self.mapping_sett_pb1.setText("Buton 1")
        self.mapping_sett_pb1.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))
        self.mapping_sett_gl.addWidget(self.mapping_sett_pb1, 0, 0, 1, 1)

        self.mapping_sett_pb2 = QPushButton(self.mappingSett_gb)
        self.mapping_sett_pb2.setText("Buton 2")
        self.mapping_sett_pb2.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))
        self.mapping_sett_gl.addWidget(self.mapping_sett_pb2, 0, 1, 1, 1)

        self.sett_gridLayout.addWidget(self.mappingSett_gb, 0, 0, 1, 1)

        self.coralSett_gb = QtWidgets.QGroupBox(self.SETT)
        self.coralSett_gb.setObjectName("coralSett_gb")
        self.coralSett_gl = QtWidgets.QGridLayout(self.coralSett_gb)
        self.coralSett_gl.setObjectName("coralSett_gl")
        self.coralSett_gb.setStyleSheet(
            "QGroupBox#coralSett_gb:title "
            "{subcontrol-origin: margin; subcontrol-position: top center; "
            "padding-left: 10px; padding-right: 10px;}"
            "QGroupBox#coralSett_gb "
            "{border :2px solid rgb(70,70,70); margin-top: 20px; border-radius: 10px;} ")

        self.coralSett_pb1 = QPushButton(self.coralSett_gb)
        self.coralSett_pb1.setText("Buton 1")
        self.coralSett_pb1.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))
        self.coralSett_gl.addWidget(self.coralSett_pb1, 0, 0, 1, 1)

        self.coralSett_pb2 = QPushButton(self.coralSett_gb)
        self.coralSett_pb2.setText("Buton 2")
        self.coralSett_pb2.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))
        self.coralSett_gl.addWidget(self.coralSett_pb2, 0, 1, 1, 1)

        self.sett_gridLayout.addWidget(self.coralSett_gb, 1, 0, 1, 1)

        self.subwaySett_gb = QtWidgets.QGroupBox(self.SETT)
        self.subwaySett_gb.setObjectName("subwaySett_gb")
        self.subwaySett_gl = QtWidgets.QGridLayout(self.subwaySett_gb)
        self.subwaySett_gl.setObjectName("subwaySett_gl")
        self.subwaySett_gb.setStyleSheet(
            "QGroupBox#subwaySett_gb:title "
            "{subcontrol-origin: margin; subcontrol-position: top center; "
            "padding-left: 10px; padding-right: 10px;}"
            "QGroupBox#subwaySett_gb "
            "{border :2px solid rgb(70,70,70); margin-top: 20px; border-radius: 10px;} ")

        self.subwaySett_pb1 = QPushButton(self.subwaySett_gb)
        self.subwaySett_pb1.setText("Buton 1")
        self.subwaySett_pb1.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))
        self.subwaySett_gl.addWidget(self.subwaySett_pb1, 0, 0, 1, 1)

        self.subwaySett_pb2 = QPushButton(self.subwaySett_gb)
        self.subwaySett_pb2.setText("Buton 2")
        self.subwaySett_pb2.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))
        self.subwaySett_gl.addWidget(self.subwaySett_pb2, 0, 1, 1, 1)

        self.sett_gridLayout.addWidget(self.subwaySett_gb, 2, 0, 1, 1)

        ################################################################## CONFİGURATİONS

        self.CONF = QtWidgets.QWidget()
        self.CONF.setObjectName("CONF")
        self.conf_gridLayout = QtWidgets.QGridLayout(self.CONF)
        self.conf_gridLayout.setSpacing(10)
        self.conf_gridLayout.setObjectName("conf_gridLayout")

        self.joyConf_gb = QtWidgets.QGroupBox(self.CONF)
        self.joyConf_gb.setObjectName("joyConf_gb")
        self.gridLayout_joy = QtWidgets.QGridLayout(self.joyConf_gb)
        self.gridLayout_joy.setObjectName("gridLayout_joy")
        # self.joyConf_gb.setFixedHeight(500)
        self.joyConf_gb.setStyleSheet(
            "QGroupBox#joyConf_gb:title "
            "{subcontrol-origin: margin; subcontrol-position: top center; "
            "padding-left: 10px; padding-right: 10px;}"
            "QGroupBox#joyConf_gb "
            "{border :2px solid rgb(70,70,70); margin-top: 20px; border-radius: 10px;} ")

        self.combo_list = ["", "Forward", "Backward", "Left", "Right", "Op Grip MR", "Cl Grip MR",
                           "Light On", "Light Off", "MicroR FB", "MicroR LR",
                           "Op Grip R", "Cl Grip R", "CW Grip R", "CCW Grip R"]

        self.joy_0_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_0_lb.setMaximumHeight(32)
        self.joy_0_lb.setText("<font color=\"black\">0 <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_0_lb, 0, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_0 = QComboBox(self.joyConf_gb)
        self.combo_joy_0.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_0, 0, 1, 1, 2)

        self.joy_1_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_1_lb.setMaximumHeight(32)
        self.joy_1_lb.setText("<font color=\"black\">1  <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_1_lb, 1, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_1 = QComboBox(self.joyConf_gb)
        self.combo_joy_1.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_1, 1, 1, 1, 2)

        self.joy_2_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_2_lb.setMaximumHeight(32)
        self.joy_2_lb.setText("<font color=\"black\">2  <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_2_lb, 2, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_2 = QComboBox(self.joyConf_gb)
        self.combo_joy_2.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_2, 2, 1, 1, 2)

        self.joy_3_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_3_lb.setMaximumHeight(32)
        self.joy_3_lb.setText("<font color=\"black\">3  <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_3_lb, 3, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_3 = QComboBox(self.joyConf_gb)
        self.combo_joy_3.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_3, 3, 1, 1, 2)

        self.joy_4_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_4_lb.setMaximumHeight(32)
        self.joy_4_lb.setText("<font color=\"black\">4  <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_4_lb, 4, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_4 = QComboBox(self.joyConf_gb)
        self.combo_joy_4.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_4, 4, 1, 1, 2)

        self.joy_5_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_5_lb.setMaximumHeight(32)
        self.joy_5_lb.setText("<font color=\"black\">5  <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_5_lb, 5, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_5 = QComboBox(self.joyConf_gb)
        self.combo_joy_5.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_5, 5, 1, 1, 2)

        self.joy_6_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_6_lb.setMaximumHeight(32)
        self.joy_6_lb.setText("<font color=\"black\">6  <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_6_lb, 6, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_6 = QComboBox(self.joyConf_gb)
        self.combo_joy_6.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_6, 6, 1, 1, 2)

        self.joy_7_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_7_lb.setMaximumHeight(32)
        self.joy_7_lb.setText("<font color=\"black\">7  <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_7_lb, 7, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_7 = QComboBox(self.joyConf_gb)
        self.combo_joy_7.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_7, 7, 1, 1, 2)

        self.joy_8_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_8_lb.setMaximumHeight(32)
        self.joy_8_lb.setText("<font color=\"black\">8  <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_8_lb, 8, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_8 = QComboBox(self.joyConf_gb)
        self.combo_joy_8.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_8, 8, 1, 1, 2)

        self.joy_9_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_9_lb.setMaximumHeight(32)
        self.joy_9_lb.setText("<font color=\"black\">9  <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_9_lb, 0, 3, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_9 = QComboBox(self.joyConf_gb)
        self.combo_joy_9.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_9, 0, 4, 1, 2)

        self.joy_10_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_10_lb.setMaximumHeight(32)
        self.joy_10_lb.setText("<font color=\"black\">10 <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_10_lb, 1, 3, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_10 = QComboBox(self.joyConf_gb)
        self.combo_joy_10.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_10, 1, 4, 1, 2)

        self.joy_11_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_11_lb.setMaximumHeight(32)
        self.joy_11_lb.setText("<font color=\"black\">11 <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_11_lb, 2, 3, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_11 = QComboBox(self.joyConf_gb)
        self.combo_joy_11.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_11, 2, 4, 1, 2)

        self.joy_12_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_12_lb.setMaximumHeight(32)
        self.joy_12_lb.setText("<font color=\"black\">12 <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_12_lb, 3, 3, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_12 = QComboBox(self.joyConf_gb)
        self.combo_joy_12.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_12, 3, 4, 1, 2)

        self.joy_13_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_13_lb.setMaximumHeight(32)
        self.joy_13_lb.setText("<font color=\"black\">13 <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_13_lb, 4, 3, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_13 = QComboBox(self.joyConf_gb)
        self.combo_joy_13.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_13, 4, 4, 1, 2)

        self.joy_14_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_14_lb.setMaximumHeight(32)
        self.joy_14_lb.setText("<font color=\"black\">14 <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_14_lb, 5, 3, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_14 = QComboBox(self.joyConf_gb)
        self.combo_joy_14.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_14, 5, 4, 1, 2)

        self.joy_15_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_15_lb.setMaximumHeight(32)
        self.joy_15_lb.setText("<font color=\"black\">15 <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_15_lb, 6, 3, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_15 = QComboBox(self.joyConf_gb)
        self.combo_joy_15.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_15, 6, 4, 1, 2)

        self.joy_16_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_16_lb.setMaximumHeight(32)
        self.joy_16_lb.setText("<font color=\"black\">16 <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_16_lb, 7, 3, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_16 = QComboBox(self.joyConf_gb)
        self.combo_joy_16.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_16, 7, 4, 1, 2)

        self.joy_17_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_17_lb.setMaximumHeight(32)
        self.joy_17_lb.setText("<font color=\"black\">17 <font color=\"white\">: <font color=\"red\">▯")
        self.gridLayout_joy.addWidget(self.joy_17_lb, 8, 3, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_17 = QComboBox(self.joyConf_gb)
        self.combo_joy_17.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_17, 8, 4, 1, 2)

        self.joy_a0_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_a0_lb.setMaximumHeight(32)
        self.joy_a0_lb.setText("<font color=\"black\">A0 <font color=\"white\">:")
        self.gridLayout_joy.addWidget(self.joy_a0_lb, 9, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_a0 = QComboBox(self.joyConf_gb)
        self.combo_joy_a0.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_a0, 9, 1, 1, 2)

        self.joy_sld0 = QSlider(Qt.Horizontal, self.joyConf_gb)
        self.joy_sld0.setRange(-100, 100)
        self.joy_sld0.setEnabled(False)
        self.gridLayout_joy.addWidget(self.joy_sld0, 9, 3, 1, 3)

        self.joy_a1_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_a1_lb.setMaximumHeight(32)
        self.joy_a1_lb.setText("<font color=\"black\">A1 <font color=\"white\">:")
        self.gridLayout_joy.addWidget(self.joy_a1_lb, 10, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_a1 = QComboBox(self.joyConf_gb)
        self.combo_joy_a1.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_a1, 10, 1, 1, 2)

        self.joy_sld1 = QSlider(Qt.Horizontal, self.joyConf_gb)
        self.joy_sld1.setRange(-100, 100)
        self.joy_sld1.setEnabled(False)
        self.gridLayout_joy.addWidget(self.joy_sld1, 10, 3, 1, 3)

        self.joy_a2_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_a2_lb.setMaximumHeight(32)
        self.joy_a2_lb.setText("<font color=\"black\">A2 <font color=\"white\">:")
        self.gridLayout_joy.addWidget(self.joy_a2_lb, 11, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_a2 = QComboBox(self.joyConf_gb)
        self.combo_joy_a2.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_a2, 11, 1, 1, 2)

        self.joy_sld2 = QSlider(Qt.Horizontal, self.joyConf_gb)
        self.joy_sld2.setRange(-100, 100)
        self.joy_sld2.setEnabled(False)
        self.gridLayout_joy.addWidget(self.joy_sld2, 11, 3, 1, 3)

        self.joy_a3_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_a3_lb.setMaximumHeight(32)
        self.joy_a3_lb.setText("<font color=\"black\">A3 <font color=\"white\">:")
        self.gridLayout_joy.addWidget(self.joy_a3_lb, 12, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_a3 = QComboBox(self.joyConf_gb)
        self.combo_joy_a3.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_a3, 12, 1, 1, 2)

        self.joy_sld3 = QSlider(Qt.Horizontal, self.joyConf_gb)
        self.joy_sld3.setRange(-100, 100)
        self.joy_sld3.setEnabled(False)
        self.gridLayout_joy.addWidget(self.joy_sld3, 12, 3, 1, 3)

        self.joy_a4_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_a4_lb.setMaximumHeight(32)
        self.joy_a4_lb.setText("<font color=\"black\">A4 <font color=\"white\">:")
        self.gridLayout_joy.addWidget(self.joy_a4_lb, 13, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_a4 = QComboBox(self.joyConf_gb)
        self.combo_joy_a4.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_a4, 13, 1, 1, 2)

        self.joy_sld4 = QSlider(Qt.Horizontal, self.joyConf_gb)
        self.joy_sld4.setRange(-100, 100)
        self.joy_sld4.setEnabled(False)
        self.gridLayout_joy.addWidget(self.joy_sld4, 13, 3, 1, 3)

        self.joy_a5_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_a5_lb.setMaximumHeight(32)
        self.joy_a5_lb.setText("<font color=\"black\">A5 <font color=\"white\">:")
        self.gridLayout_joy.addWidget(self.joy_a5_lb, 14, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_a5 = QComboBox(self.joyConf_gb)
        self.combo_joy_a5.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_a5, 14, 1, 1, 2)

        self.joy_sld5 = QSlider(Qt.Horizontal, self.joyConf_gb)
        self.joy_sld5.setRange(-100, 100)
        self.joy_sld5.setEnabled(False)
        self.gridLayout_joy.addWidget(self.joy_sld5, 14, 3, 1, 3)

        self.joy_a6_lb = QtWidgets.QLabel(self.joyConf_gb)
        self.joy_a6_lb.setMaximumHeight(32)
        self.joy_a6_lb.setText("<font color=\"black\">A6 <font color=\"white\">:")
        self.gridLayout_joy.addWidget(self.joy_a6_lb, 15, 0, 1, 1, alignment=Qt.AlignRight)

        self.combo_joy_a6 = QComboBox(self.joyConf_gb)
        self.combo_joy_a6.addItems(self.combo_list)
        self.gridLayout_joy.addWidget(self.combo_joy_a6, 15, 1, 1, 2)

        self.joy_sld6 = QSlider(Qt.Horizontal, self.joyConf_gb)
        self.joy_sld6.setRange(-100, 100)
        self.joy_sld6.setEnabled(False)
        self.gridLayout_joy.addWidget(self.joy_sld6, 15, 3, 1, 3)

        self.conf_gridLayout.addWidget(self.joyConf_gb, 0, 0, 1, 2)

        self.joy_refresh_pb = QPushButton(self.CONF)
        self.joy_refresh_pb.setText("Refresh")
        self.joy_refresh_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))
        self.conf_gridLayout.addWidget(self.joy_refresh_pb, 2, 0, 1, 1)

        self.save_pb = QPushButton(self.CONF)
        self.save_pb.setText("Save Changes")
        self.save_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))
        self.conf_gridLayout.addWidget(self.save_pb, 1, 0, 1, 1)

        self.default_pb = QPushButton(self.CONF)
        self.default_pb.setText("Default Settings")
        self.default_pb.setMinimumSize(QtCore.QSize(0, self.buton_minimum_height))
        self.conf_gridLayout.addWidget(self.default_pb, 1, 1, 1, 1)

        ##################################################################

        self.main_tw.addTab(self.TASKS, "")
        self.main_tw.addTab(self.SETT, "")
        self.main_tw.addTab(self.CONF, "")
        self.main_tw.addTab(self.INFO, "")

        self.gridLayout.addLayout(self.leftside_gl, 0, 0, 1, 1)
        self.gridLayout.setColumnStretch(0, 80)
        self.setCentralWidget(self.main_gl)
        self.retranslateUi()

        self.main_tw.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.set_joy_config()

        self.joy_refr = False
        self.joy = Joy()

        if not self.joy.connected:
            self.warnings_list.append("Joystick not connected!")
        self.joy.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(lambda: self.timer_func())
        self.timer.start(100)

        self.second = 0
        self.minute = 0
        self.start = False
        self.stop = True
        self.timer2 = QtCore.QTimer()
        self.timer2.timeout.connect(lambda: self.counter_func())

        self.th = CameraShowThread()
        self.th.changePixmap.connect(self.setImage)
        self.th.start()
        self.frame = []

        self.mainThread = MainThread(self)
        self.mainThread.start()
        time.sleep(0.1)
        self.mikroThread = MikroThread(self)
        self.mikroThread.start()

        self.counterstart_pb.clicked.connect(self.f_counterstart_pb)
        self.counterstop_pb.clicked.connect(self.f_counterstop_pb)
        self.bottomcam_pb.clicked.connect(self.f_bottomcam_pb)
        self.frontcam_pb.clicked.connect(self.f_frontcam_pb)
        self.closecam_pb.clicked.connect(self.f_closecam_pb)
        self.takephoto_pb.clicked.connect(self.f_takephoto_pb)
        self.videorecord_pb.clicked.connect(self.f_takevideo)
        self.microrovcam_pb.clicked.connect(self.f_microrovcam_pb)
        self.start_autonomous_pb.clicked.connect(self.f_start_autonomous_pb)
        self.test_autonomous_pb.clicked.connect(self.f_test_autonomous_pb)
        self.stop_autonomous_pb.clicked.connect(self.f_stop_autonomous_pb)
        self.createmap_pb.clicked.connect(self.f_createmap_pb)
        self.coral_photo_pb.clicked.connect(self.f_coral_photo_pb)
        self.start_mapping_pb.clicked.connect(self.f_start_coral_colony_pb)
        self.start2_mapping_pb.clicked.connect(self.f_start2_mapping_pb)
        self.test_mapping_pb.clicked.connect(self.f_test_mapping_pb)
        self.stop_mapping_pb.clicked.connect(self.f_stop_coral_colony_pb)
        self.createphotom_pb.clicked.connect(self.f_createphotom_pb)
        self.start_photomastic_pb.clicked.connect(self.f_start_photomastic_pb)
        self.start_photomastic_pb_2.clicked.connect(self.f_start_photomastic_pb_2)
        self.tpicos_pb.clicked.connect(self.f_tpicos_pb)
        self.stop_photomastic_pb.clicked.connect(self.f_stop_photomastic_pb)
        self.joy_refresh_pb.clicked.connect(self.f_joy_refresh_pb)
        self.default_pb.clicked.connect(self.set_joy_config)
        self.save_pb.clicked.connect(self.f_save_pb)
        self.calculate_pb.clicked.connect(self.f_calculate)

    def setImage(self, image, rgbImage):
        """
        CameraShowThread'in sürekli çağırdığı bir fonksiyondur. Ana raçtan aldığı görüntüyü self.cam_label'a yansıtmak
        için self.showImage fonksiyonuna gönderir.
        Args:
            image: QtGui.QImage (1280x720)
            rgbImage: object (1280x720)
        """
        self.rgbImage = rgbImage
        self.takephoto_pb.setEnabled(True)
        self.videorecord_pb.setEnabled(True)
        self.showImage(image)

    def showImage(self, image):
        """
        Gelen görüntüyü self.cam_label'a yansıtır.
        Args:
            image: QtGui.QImage formatında olmalıdır.
        """
        self.frame = QtGui.QPixmap.fromImage(image)
        self.cam_label.setPixmap(self.frame)

    def f_calculate(self):
        """
        self.calculate_pb(TASKS/Mussel Bed Calculation/Calculate Butonu) basıldığında spinBox'lardaki sayılarla yaptığı
        hesabı self.calculation_lb labelına yazdırır.
        """
        count = self.counted_mussel_sb.value()
        l = self.length_mussel_sb.value()
        w = self.width_mussel_sb.value()
        rate = self.litreperhour_mussel_sb.value()
        calculation = count * (l * w / 0.25) * rate
        calculation = np.round(calculation, decimals=2)
        self.calculation_lb.setText("  " + str(calculation) + "  ")
        self.calculation_lb.setStyleSheet("background-color: dark-grey; font-size: 14pt")

    def f_counterstop_pb(self):
        """
        Sayacı durdurma butonunun basıldığında çalışan fonksiyondur. Sayaç durdurulmuş ise resetler, başlatılmış ise
        durdurur.
        """
        if self.stop == True:
            self.timer2.stop()
            self.counterstop_pb.setText("  RESET  ")
            self.counterstart_pb.setText("  CONTINUE  ")
            self.counterstop_pb.setIcon(QIcon("icons/icon-stop.png"))
            self.counterstop_pb.setIconSize(QSize(17, 17))
            self.counterstart_pb.setEnabled(True)
            self.stop = False
        else:
            self.second = 0
            self.minute = 0
            self.counter_lcd.display("00:00")
            self.counterstop_pb.setText("  STOP  ")
            self.counterstart_pb.setText("  START  ")
            self.counterstop_pb.setIcon(QIcon("icons/icon-pause.png"))
            self.counterstop_pb.setIconSize(QSize(17, 17))
            self.counterstop_pb.setEnabled(False)
            self.stop = True
            self.start = False

    def f_counterstart_pb(self):
        """
        Sayacı başlatma butonunun basıldığında çalışan fonksiyondur. Sayaç durdurulmuş ise devam ettirir, resetlenmiş
        ise başlatır.
        """
        if self.start == False:
            self.counterstop_pb.setEnabled(True)
            self.start = True
            self.timer2.start(1000)
            self.counterstart_pb.setEnabled(False)
        else:
            self.timer2.start(1000)
            self.start = True
            self.counterstop_pb.setText("  STOP  ")
            self.counterstart_pb.setText("  START  ")
            self.counterstop_pb.setIcon(QIcon("icons/icon-pause.png"))
            self.counterstop_pb.setIconSize(QSize(17, 17))
            self.counterstart_pb.setEnabled(False)
            self.stop = True

    def f_frontcam_pb(self):
        """
        Ön kamera butonu basıldığında çalışan fonksiyondur.
        """
        self.camera_var = 1
        self.frontcam_pb.setIcon(QIcon("icons/front_cam2.png"))
        self.frontcam_pb.setIconSize(QSize(30, 30))
        self.bottomcam_pb.setIcon(QIcon("icons/bottom_cam.png"))
        self.bottomcam_pb.setIconSize(QSize(30, 30))
        self.microrovcam_pb.setIcon(QIcon("icons/microrov_cam.png"))
        self.microrovcam_pb.setIconSize(QSize(30, 30))

    def f_bottomcam_pb(self):
        """
        Alt kamera butonu basıldığında çalışan fonksiyondur.
        """
        self.camera_var = 2
        self.frontcam_pb.setIcon(QIcon("icons/front_cam.png"))
        self.frontcam_pb.setIconSize(QSize(30, 30))
        self.bottomcam_pb.setIcon(QIcon("icons/bottom_cam2.png"))
        self.bottomcam_pb.setIconSize(QSize(30, 30))
        self.microrovcam_pb.setIcon(QIcon("icons/microrov_cam.png"))
        self.microrovcam_pb.setIconSize(QSize(30, 30))

    def f_microrovcam_pb(self):
        """
        Micro Rov kamera butonu basıldığında çalışan fonksiyondur.
        """
        self.camera_var = 3
        self.frontcam_pb.setIcon(QIcon("icons/front_cam.png"))
        self.frontcam_pb.setIconSize(QSize(30, 30))
        self.bottomcam_pb.setIcon(QIcon("icons/bottom_cam.png"))
        self.bottomcam_pb.setIconSize(QSize(30, 30))
        self.microrovcam_pb.setIcon(QIcon("icons/microrov_cam2.png"))
        self.microrovcam_pb.setIconSize(QSize(30, 30))

    def f_takephoto_pb(self):
        """
        Fotoğraf çekme butonu basıldığında çalışan fonksiyondur.
        """
        time = QDateTime.currentDateTime()
        timeDisplay = time.toString('yyyy-MM-dd_hh.mm.ss')
        # print(timeDisplay)
        if not self.frame == []:
            if self.camera_var == 1:
                cam = "front_"
            elif self.camera_var == 2:
                cam = "bottom_"
            elif self.camera_var == 3:
                cam = "micro_"
            else:
                cam = "unknown_"
            self.warnings_list.append("Photo was taken.")
            photo = cv2.cvtColor(self.rgbImage, cv2.COLOR_RGB2BGR)
            cv2.imwrite("Photos/{}{}.jpg".format(cam, timeDisplay), photo)
        else:
            self.warnings_list.append("Kameradan görüntü gelmediği için foto çekilemedi.")

    def f_takevideo(self):
        """
        Video çekme butonu basıldında çalışan fonksiyondur.
        """
        time = QDateTime.currentDateTime()
        timeDisplay = time.toString('yyyy-MM-dd_hh.mm.ss')
        if not self.frame == []:
            if self.video_record == False:
                self.videorecord_pb.setStyleSheet(
                    "QPushButton#videorecord_pb {border-image: url(icons/take_video_2.png); border-radius : 35;} "
                    "QPushButton#videorecord_pb:hover {border-image: url(icons/take_video_4.png); border-radius : 35;} "
                    "QPushButton#videorecord_pb:pressed {border-image: url(icons/take_pressed.png); border-radius : 35;}")
                if self.camera_var == 1:
                    cam = "front_"
                elif self.camera_var == 2:
                    cam = "bottom_"
                elif self.camera_var == 3:
                    cam = "micro_"
                else:
                    cam = "unknown_"
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                self.recorder = cv2.VideoWriter("Videos/{}{}.avi".format(cam, timeDisplay), fourcc, 60, (1280, 720))
                self.video_record = True
                self.warnings_list.append("Video started to be record.")
            else:
                self.warnings_list.append("Video was recorded.")
                self.videorecord_pb.setStyleSheet(
                    "QPushButton#videorecord_pb {border-image: url(icons/take_video.png); border-radius : 35;} "
                    "QPushButton#videorecord_pb:hover {border-image: url(icons/take_video_3.png); border-radius : 35;} "
                    "QPushButton#videorecord_pb:pressed {border-image: url(icons/take_pressed.png); border-radius : 35;}")
                self.video_record = False
        else:
            self.warnings_list.append("Kameradan görüntü gelmediği için video çekilemedi.")

    def f_closecam_pb(self):
        """
        Kamera kapama butonu basıldığında çalışan fonksiyondur.
        """
        self.frame = []
        self.camera_var = 0
        self.cam_label.clear()
        self.cam_label.setPixmap(QtGui.QPixmap("icons/icon-no-video.png"))
        self.cam_label.setAlignment(QtCore.Qt.AlignCenter)
        self.takephoto_pb.setEnabled(False)
        self.videorecord_pb.setEnabled(False)
        self.frontcam_pb.setIcon(QIcon("icons/front_cam.png"))
        self.frontcam_pb.setIconSize(QSize(30, 30))
        self.bottomcam_pb.setIcon(QIcon("icons/bottom_cam.png"))
        self.bottomcam_pb.setIconSize(QSize(30, 30))
        self.microrovcam_pb.setIcon(QIcon("icons/microrov_cam.png"))
        self.microrovcam_pb.setIconSize(QSize(30, 30))

    def f_test_autonomous_pb(self):
        pass

    def f_start_autonomous_pb(self):
        self.autonomousMission = True
        # self.line_detect.rov_drive = RovDrive()
        self.line_detect.rov_drive.connect_joystick()
        time.sleep(1)
        self.line_detect.rov_drive.arm_rov()
        self.warnings_list.append("Autonomous flying started.")

    def f_stop_autonomous_pb(self):
        self.autonomousMission = False
        self.line_detect.rov_drive.disarm_rov()
        time.sleep(0.1)
        self.line_detect.rov_drive.disconnect_joystick()
        self.warnings_list.append("Autonomous flying ended.")

    def f_start_coral_colony_pb(self):
        self.coralMission = True
        self.warnings_list.append("Coral Colony Mission started.")

    def f_stop_coral_colony_pb(self):
        self.coralMission = False
        self.warnings_list.append("Coral Colony Mission ended.")

    def mission_coral_colony(self, frame):
        """
        Coral Colony Mission
        Args:
            frame: Ön Kamera

        Returns:
            self.frame: İşlenmiş görüntü
        """
        coral_reef_after = Coral()
        start = time.time()

        frame = cv2.resize(frame, (960, 540))
        coral_reef_after.get_image(frame)

        if not coral_reef_after.get_roi():
            self.frame = coral_reef_after.show_frame(start)
            return self.frame

        coral_reef_after.apply_skeletonize()
        # cv2.imshow("Skel Video", coral_reef_after.skeleton_image)

        if not coral_reef_after.find_key_points():
            self.frame = coral_reef_after.show_frame(start)
            return self.frame

        coral_reef_after.overlap(self.coral_colony_before.roi_image, self.coral_colony_before.key_points)

        coral_reef_after.apply_skeletonize_2()
        coral_reef_after.find_key_points_end()
        coral_reef_after.overlap(coral_reef_after.warped_photo, coral_reef_after.points_warped)

        # cv2.imshow("Overlapped Image", coral_reef_after.overlapped_image)

        coral_reef_after.find_difference(coral_reef_after.warped_photo, coral_reef_after.roi_image,
                                         coral_reef_after.roi_image)

        self.frame = coral_reef_after.show_frame(start)
        return self.frame

    def mission_coral_colony_photo(self):
        """
        Coral Colony Mission fotoğraf üzerinde
        """
        self.coral_colony_after_photo = cv2.imread("missions/coral_colony/Photos/Coral Colony F.png")
        self.coral_colony_after_photo = cv2.resize(self.coral_colony_after_photo, (600, 600))

        self.coral_colony_after = Coral()
        self.coral_colony_after.get_image(self.coral_colony_after_photo)

        self.coral_colony_after.apply_skeletonize()
        self.coral_colony_after.find_key_points()
        self.coral_colony_after.show_image()

        self.coral_colony_after.overlap(self.coral_colony_before.copy_image, self.coral_colony_before.key_points)

        self.coral_colony_after.apply_skeletonize_2()
        self.coral_colony_after.find_key_points_end()

        self.coral_colony_after.overlap(self.coral_colony_after.warped_photo, self.coral_colony_after.points_warped)

        self.coral_colony_after.find_difference(self.coral_colony_after.warped_photo, self.coral_colony_after.copy_image_2,
                                                self.coral_colony_after.copy_image_2)
        self.coral_colony_diff = self.coral_colony_after.copy_image_2

    def mission_subway_car(self):
        """
        Subway Car Mission sırayla çekilmiş fotoğraflar üzerinde
        """
        frame = cv2.imread("missions/photomosaic/Photos/J1.png")  # yan_mavi.jpg
        self.subway_car.get_photo(frame)
        # subway_car.thresh_operation()
        self.subway_car.hsv_operation()
        self.subway_car.find_contour()
        self.subway_car.crop_minAreaRect()
        self.subway_car.crop_face()
        # subway_car.get_kmeans_top()
        self.subway_car.get_kmeans_side()

        frame = cv2.imread("missions/photomosaic/Photos/J2.png")  # yan_pembe.jpg
        self.subway_car.get_photo(frame)
        # subway_car.thresh_operation()
        self.subway_car.hsv_operation()
        self.subway_car.find_contour()
        self.subway_car.crop_minAreaRect()
        self.subway_car.crop_face()
        # subway_car.get_kmeans_top()
        self.subway_car.get_kmeans_side()

        frame = cv2.imread("missions/photomosaic/Photos/J4.png")  # yan_sari.jpg
        self.subway_car.get_photo(frame)
        # subway_car.thresh_operation()
        self.subway_car.hsv_operation()
        self.subway_car.find_contour()
        self.subway_car.crop_minAreaRect()
        self.subway_car.crop_face()
        # subway_car.get_kmeans_top()
        self.subway_car.get_kmeans_side()

        frame = cv2.imread("missions/photomosaic/Photos/J5.png")  # yan_kirmizi.jpg
        self.subway_car.get_photo(frame)
        # subway_car.thresh_operation()
        self.subway_car.hsv_operation()
        self.subway_car.find_contour()
        self.subway_car.crop_minAreaRect()
        self.subway_car.crop_face()
        # subway_car.get_kmeans_top()
        self.subway_car.get_kmeans_side()

        frame = cv2.imread("missions/photomosaic/Photos/J3.png")  # kmeans2.jpg
        self.subway_car.get_photo(frame)
        # subway_car.thresh_operation()
        self.subway_car.hsv_operation()
        self.subway_car.find_contour()
        self.subway_car.crop_minAreaRect()
        self.subway_car.crop_face()
        self.subway_car.get_kmeans_top()
        # subway_car.get_kmeans_side()

        # subway_car.control()
        self.subway_car.correct_photo()

        self.subway_car.add_white_to_photos()
        self.subway_car.concate_photos()

        result = self.subway_car.test()

        return result

    def mission_mapping_photo(self):
        self.coral_reef_img = cv2.imread("missions/mapping/Photos/Coral Reef 6.jpg")
        self.coral_reef_img = cv2.resize(self.coral_reef_img, (1600, 642))
        self.mapping.operation(self.coral_reef_img)
        self.mapping.intersection_detect()
        self.mapping.draw_map()

    def mission_autonomous_flying(self, frame):
        """
        Harita üzerinden otonom geçiş fonksiyonudur.
        Args:
            frame: Alt Kamera görüntüsü

        Returns:
            self.line_detect.canvas: İşlenmiş görüntü
        """
        frame = cv2.resize(frame, (640, 480))
        self.line_detect.operation(frame)
        self.line_detect.line_detect()
        self.line_detect.contour_operation()
        # self.line_detect.mapping()
        self.line_detect.drive_rotation()
        # self.line_detect.drive_altitude()
        self.line_detect.drive_yaw()
        self.line_detect.drive()

        return self.line_detect.canvas

    def f_coral_photo_pb(self):
        """
        Coral Colony Photo butonu basıldığında çalışan fonksiyondur. Ayrı bir pencerede eski coral colony fotoğrafını
        gösterir.
        """
        self.mission_coral_colony_photo()
        self.coral_window = QtWidgets.QWidget()
        ui = UiCoralPhotoWindow()
        ui.setupUi(self.coral_window)
        self.coral_window.show()

    def f_test_mapping_pb(self):
        pass

    def f_start2_mapping_pb(self):
        pass

    def f_createmap_pb(self):
        """
        Mapping Mission fotoğraf üzerinde
        """
        self.mission_mapping_photo()
        self.mapping_window = QtWidgets.QWidget()
        ui = UiMapping()
        ui.setupUi(self.mapping_window)
        self.mapping_window.show()

    def f_start_photomastic_pb(self):
        self.photomosaicMission = True
        self.warnings_list.append("Photomosaic Mission started.")

    def f_stop_photomastic_pb(self):
        self.photomosaicMission = False
        self.warnings_list.append("Photomosaic Mission ended.")

    def mission_photomosaic_with_rects(self, frame):
        """
        Subway Car görevi için test fonksiyonu
        Args:
            frame: Ön veya alt kamera görüntüsü

        Returns:
            output_frame: İşlenmiş görüntü
        """
        if self.camera_var == 1:
            output_frame = self.subway_car.draw_hsv(frame)

        elif self.camera_var == 2:
            output_frame = self.subway_car.draw_thresh(frame)

        return output_frame

    def f_start_photomastic_pb_2(self):
        pass

    def f_tpicos_pb(self):
        """
        Subway Car görevi fotoğraf çekme fonksiyonu
        """
        if not self.frame == []:
            photo = cv2.cvtColor(self.rgbImage, cv2.COLOR_RGB2BGR)
            cv2.imwrite("missions/photomosaic/Photos/surface_{}.jpg".format(self.surface_num), photo)
            self.warnings_list.append("Surface {} was taken.".format(self.surface_num))
            self.surface_num += 1
            if self.surface_num == 6:
                self.surface_num = 2
        else:
            self.warnings_list.append("Kameradan görüntü gelmediği için foto çekilemedi.")

    def f_createphotom_pb(self):
        """
        Subway Car görevinin sonucunu ayrı bir ekranda gösterir.
        """
        self.result = self.mission_subway_car()
        self.photomastic = QtWidgets.QWidget()
        ui = UiPhotomastic()
        ui.setupUi(self.photomastic, self.result)
        self.photomastic.show()

    def set_joy_config(self):
        """
        CONF tabında joystick eksen ve butonlarının ayarlarını config.ini dosyasından çekip arayüzde ayarlayan
        fonksiyondur.
        """
        text = self.config["joystick_config_default"]["B0"]
        if text == "BUSY":
            self.combo_joy_0.setEnabled(False)
            self.combo_joy_0.addItem(text)
            self.combo_joy_0.setCurrentText(text)
        else:
            self.combo_joy_0.setCurrentText(text)

        text = self.config["joystick_config_default"]["B1"]
        if text == "BUSY":
            self.combo_joy_1.setEnabled(False)
            self.combo_joy_1.addItem(text)
            self.combo_joy_1.setCurrentText(text)
        else:
            self.combo_joy_1.setCurrentText(text)

        text = self.config["joystick_config_default"]["B2"]
        if text == "BUSY":
            self.combo_joy_2.setEnabled(False)
            self.combo_joy_2.addItem(text)
            self.combo_joy_2.setCurrentText(text)
        else:
            self.combo_joy_2.setCurrentText(text)

        text = self.config["joystick_config_default"]["B3"]
        if text == "BUSY":
            self.combo_joy_3.setEnabled(False)
            self.combo_joy_3.addItem(text)
            self.combo_joy_3.setCurrentText(text)
        else:
            self.combo_joy_3.setCurrentText(text)

        text = self.config["joystick_config_default"]["B4"]
        if text == "BUSY":
            self.combo_joy_4.setEnabled(False)
            self.combo_joy_4.addItem(text)
            self.combo_joy_4.setCurrentText(text)
        else:
            self.combo_joy_4.setCurrentText(text)

        text = self.config["joystick_config_default"]["B5"]
        if text == "BUSY":
            self.combo_joy_5.setEnabled(False)
            self.combo_joy_5.addItem(text)
            self.combo_joy_5.setCurrentText(text)
        else:
            self.combo_joy_5.setCurrentText(text)

        text = self.config["joystick_config_default"]["B6"]
        if text == "BUSY":
            self.combo_joy_6.setEnabled(False)
            self.combo_joy_6.addItem(text)
            self.combo_joy_6.setCurrentText(text)
        else:
            self.combo_joy_6.setCurrentText(text)

        text = self.config["joystick_config_default"]["B7"]
        if text == "BUSY":
            self.combo_joy_7.setEnabled(False)
            self.combo_joy_7.addItem(text)
            self.combo_joy_7.setCurrentText(text)
        else:
            self.combo_joy_7.setCurrentText(text)

        text = self.config["joystick_config_default"]["B8"]
        if text == "BUSY":
            self.combo_joy_8.setEnabled(False)
            self.combo_joy_8.addItem(text)
            self.combo_joy_8.setCurrentText(text)
        else:
            self.combo_joy_8.setCurrentText(text)

        text = self.config["joystick_config_default"]["B9"]
        if text == "BUSY":
            self.combo_joy_9.setEnabled(False)
            self.combo_joy_9.addItem(text)
            self.combo_joy_9.setCurrentText(text)
        else:
            self.combo_joy_9.setCurrentText(text)

        text = self.config["joystick_config_default"]["B10"]
        if text == "BUSY":
            self.combo_joy_10.setEnabled(False)
            self.combo_joy_10.addItem(text)
            self.combo_joy_10.setCurrentText(text)
        else:
            self.combo_joy_10.setCurrentText(text)

        text = self.config["joystick_config_default"]["B11"]
        if text == "BUSY":
            self.combo_joy_11.setEnabled(False)
            self.combo_joy_11.addItem(text)
            self.combo_joy_11.setCurrentText(text)
        else:
            self.combo_joy_11.setCurrentText(text)

        text = self.config["joystick_config_default"]["B12"]
        if text == "BUSY":
            self.combo_joy_12.setEnabled(False)
            self.combo_joy_12.addItem(text)
            self.combo_joy_12.setCurrentText(text)
        else:
            self.combo_joy_12.setCurrentText(text)

        text = self.config["joystick_config_default"]["B13"]
        if text == "BUSY":
            self.combo_joy_13.setEnabled(False)
            self.combo_joy_13.addItem(text)
            self.combo_joy_13.setCurrentText(text)
        else:
            self.combo_joy_13.setCurrentText(text)

        text = self.config["joystick_config_default"]["B14"]
        if text == "BUSY":
            self.combo_joy_14.setEnabled(False)
            self.combo_joy_14.addItem(text)
            self.combo_joy_14.setCurrentText(text)
        else:
            self.combo_joy_14.setCurrentText(text)

        text = self.config["joystick_config_default"]["B15"]
        if text == "BUSY":
            self.combo_joy_15.setEnabled(False)
            self.combo_joy_15.addItem(text)
            self.combo_joy_15.setCurrentText(text)
        else:
            self.combo_joy_15.setCurrentText(text)

        text = self.config["joystick_config_default"]["B16"]
        if text == "BUSY":
            self.combo_joy_16.setEnabled(False)
            self.combo_joy_16.addItem(text)
            self.combo_joy_16.setCurrentText(text)
        else:
            self.combo_joy_16.setCurrentText(text)

        text = self.config["joystick_config_default"]["B17"]
        if text == "BUSY":
            self.combo_joy_17.setEnabled(False)
            self.combo_joy_17.addItem(text)
            self.combo_joy_17.setCurrentText(text)
        else:
            self.combo_joy_17.setCurrentText(text)

        text = self.config["joystick_config_default"]["A0"]
        if text == "BUSY":
            self.combo_joy_a0.setEnabled(False)
            self.combo_joy_a0.addItem(text)
            self.combo_joy_a0.setCurrentText(text)
        else:
            self.combo_joy_a0.setCurrentText(text)

        text = self.config["joystick_config_default"]["A1"]
        if text == "BUSY":
            self.combo_joy_a1.setEnabled(False)
            self.combo_joy_a1.addItem(text)
            self.combo_joy_a1.setCurrentText(text)
        else:
            self.combo_joy_a1.setCurrentText(text)

        text = self.config["joystick_config_default"]["A2"]
        if text == "BUSY":
            self.combo_joy_a2.setEnabled(False)
            self.combo_joy_a2.addItem(text)
            self.combo_joy_a2.setCurrentText(text)
        else:
            self.combo_joy_a2.setCurrentText(text)

        text = self.config["joystick_config_default"]["A3"]
        if text == "BUSY":
            self.combo_joy_a3.setEnabled(False)
            self.combo_joy_a3.addItem(text)
            self.combo_joy_a3.setCurrentText(text)
        else:
            self.combo_joy_a3.setCurrentText(text)

        text = self.config["joystick_config_default"]["A4"]
        if text == "BUSY":
            self.combo_joy_a4.setEnabled(False)
            self.combo_joy_a4.addItem(text)
            self.combo_joy_a4.setCurrentText(text)
        else:
            self.combo_joy_a4.setCurrentText(text)

        text = self.config["joystick_config_default"]["A5"]
        if text == "BUSY":
            self.combo_joy_a5.setEnabled(False)
            self.combo_joy_a5.addItem(text)
            self.combo_joy_a5.setCurrentText(text)
        else:
            self.combo_joy_a5.setCurrentText(text)

        text = self.config["joystick_config_default"]["A6"]
        if text == "BUSY":
            self.combo_joy_a6.setEnabled(False)
            self.combo_joy_a6.addItem(text)
            self.combo_joy_a6.setCurrentText(text)
        else:
            self.combo_joy_a6.setCurrentText(text)

    def f_save_pb(self):
        """
        CONF tabında yaptığımız joystick değişikliklerini config.ini dosyasına kaydeden fonksiyondur.
        """
        self.config["joystick_config_default"]["B0"] = self.combo_joy_0.currentText()
        self.config["joystick_config_default"]["B1"] = self.combo_joy_1.currentText()
        self.config["joystick_config_default"]["B2"] = self.combo_joy_2.currentText()
        self.config["joystick_config_default"]["B3"] = self.combo_joy_3.currentText()
        self.config["joystick_config_default"]["B4"] = self.combo_joy_4.currentText()
        self.config["joystick_config_default"]["B5"] = self.combo_joy_5.currentText()
        self.config["joystick_config_default"]["B6"] = self.combo_joy_6.currentText()
        self.config["joystick_config_default"]["B7"] = self.combo_joy_7.currentText()
        self.config["joystick_config_default"]["B8"] = self.combo_joy_8.currentText()
        self.config["joystick_config_default"]["B9"] = self.combo_joy_9.currentText()
        self.config["joystick_config_default"]["B10"] = self.combo_joy_10.currentText()
        self.config["joystick_config_default"]["B11"] = self.combo_joy_11.currentText()
        self.config["joystick_config_default"]["B12"] = self.combo_joy_12.currentText()
        self.config["joystick_config_default"]["B13"] = self.combo_joy_13.currentText()
        self.config["joystick_config_default"]["B14"] = self.combo_joy_14.currentText()
        self.config["joystick_config_default"]["B15"] = self.combo_joy_15.currentText()
        self.config["joystick_config_default"]["B16"] = self.combo_joy_16.currentText()
        self.config["joystick_config_default"]["B17"] = self.combo_joy_17.currentText()
        self.config["joystick_config_default"]["A0"] = self.combo_joy_a0.currentText()
        self.config["joystick_config_default"]["A1"] = self.combo_joy_a1.currentText()
        self.config["joystick_config_default"]["A2"] = self.combo_joy_a2.currentText()
        self.config["joystick_config_default"]["A3"] = self.combo_joy_a3.currentText()
        self.config["joystick_config_default"]["A4"] = self.combo_joy_a4.currentText()
        self.config["joystick_config_default"]["A5"] = self.combo_joy_a5.currentText()
        self.config["joystick_config_default"]["A6"] = self.combo_joy_a6.currentText()

        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

        self.warnings_list.append("The changes have been saved.")

    def f_joy_refresh_pb(self):
        """
        Joystick bağlantısını kontrol eden buton fonksiyonudur.
        """
        self.joy_refr = True

    def counter_func(self):
        """
        Sayaç başlatıldığında çağırılan fonksiyondur.
        """
        self.second = int(self.second)
        self.minute = int(self.minute)
        self.second += 1
        if self.second == 60:
            self.second = 0
            self.minute += 1
        if (self.second / 10) < 1:
            self.second = "0" + str(self.second)
        if (self.minute / 10) < 1:
            self.minute = "0" + str(self.minute)
        self.counter_lcd.display("{0}:{1}".format(self.minute, self.second))

    def timer_func(self):
        """
        self.SetupUi de her 100ms'de bir çalışan timer fonksiyonudur. Rov ve MicroRov bağlantıların kontrol ederve
        Warning'leri yazdırır.
        """
        # print("Calisiyor")
        if self.mainThread.s.connection:
            self.vehicle_st_lb.setText("   Connected   ")
            self.vehicle_st_lb.setStyleSheet("color : green; background-color: white")
        else:
            self.vehicle_st_lb.setText("   No Connection   ")
            self.vehicle_st_lb.setStyleSheet("color : red; background-color: white")

        if self.mikroThread.s.connection:
            self.microrov_st_lb.setText("   Connected   ")
            self.microrov_st_lb.setStyleSheet("color : green; background-color: white")
        else:
            self.microrov_st_lb.setText("   No Connection   ")
            self.microrov_st_lb.setStyleSheet("color : red; background-color: white")

        if not self.warnings_list:
            return

        self.message = "     "
        self.mes_num = len(self.warnings_list)
        for i in self.warnings_list[::-1]:
            self.message = self.message + str(self.mes_num) + "  -   " + str(i) + "\n     "
            self.mes_num -= 1

        self.warnings_st_lb.setText(self.message)

    def retranslateUi(self):
        """
        Başlık ve buton isimlerinin ayarlandığı fonksiyondur.
        """
        self.setWindowTitle("ITUROV GUI 2021")
        self.autonomous_gb.setTitle("Autonomous and Mapping")
        self.stop_autonomous_pb.setText("Stop")
        self.mapping_cb.setText("Mapping")
        self.start_autonomous_pb.setText("Start")
        self.test_autonomous_pb.setText("Test")
        self.coralReef_gb.setTitle("Coral Colony")
        self.stop_mapping_pb.setText("Stop")
        self.createmap_pb.setText("Create Map")
        self.coral_photo_pb.setText("Coral Colony Photo")
        self.start_mapping_pb.setText("Start ")
        self.start2_mapping_pb.setText("Start 2")
        self.test_mapping_pb.setText("Test")
        self.subwaycar_gb.setTitle("Subway Car")
        self.tpicos_pb.setText("Take Pic of Surface")
        self.createphotom_pb.setText("Photomosaic")
        self.start_photomastic_pb_2.setText("Test")
        self.start_photomastic_pb.setText("Start")
        self.stop_photomastic_pb.setText("Stop")
        self.mussel_gb.setTitle("Mussel Bed Calculation")
        self.counted_mussel_lb.setText("Count :")
        self.length_mussel_lb.setText("Length :")
        self.width_mussel_lb.setText("Width :")
        self.litreperhour_mussel_lb.setText("L/hr :")
        self.calculate_pb.setText("Calculate")
        self.main_tw.setTabText(self.main_tw.indexOf(self.TASKS), "TASKS")
        self.main_tw.setTabText(self.main_tw.indexOf(self.SETT), "SETT")
        self.mappingSett_gb.setTitle("Autonomous and Mapping Settings")
        self.coralSett_gb.setTitle("Coral Colony Settings")
        self.subwaySett_gb.setTitle("Subway Car Settings")
        self.main_tw.setTabText(self.main_tw.indexOf(self.CONF), "CONF")
        self.joyConf_gb.setTitle("Configurations")
        self.main_tw.setTabText(self.main_tw.indexOf(self.INFO), "INFO")
        self.counterstart_pb.setText("  START  ")
        self.counterstop_pb.setText("  STOP  ")
        self.microrov_st_lb.setText(" No Connection ")
        self.microrov_st_lb.setStyleSheet("color : red; background-color: white")
        self.microrov_lb.setText("    MicroROV:")
        self.vehicle_lb.setText("    Vehicle:")
        self.vehicle_st_lb.setText(" -")
        self.vehicle_st_lb.setStyleSheet("color : red; background-color: white")
        self.camera_gb.setTitle("CAMERA")
        # self.camera_gb.setAlignment(Qt.AlignCenter)
        self.warnings_lb.setText("WARNINGS")

    def closeEvent(self, event):
        """
        Arayüz kapanırken çalışan fonksiyondur. Kullanıcıya kapatmakta emin dlup olmadığı sorulur. Arayüz kapanmadan
        önce çalışan tüm thread'leri kapatır.
        """
        reply = QMessageBox.question(self, "Window Close", "Are you sure you want to close the window?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            self.timer.stop()
            self.timer2.stop()
            self.system = False
            print("System Shuts Down")
            self.mainThread.terminate()
            self.mikroThread.terminate()
            self.camera_var = 0
            time.sleep(1)
            self.mainThread.wait()
            self.mikroThread.wait()

        else:
            event.ignore()


class UiPhotomastic(QWidget):
    def setupUi(self, photomastic, result):
        self.result = result
        # super().__init__()
        photomastic.setObjectName("Photomastic")
        photomastic.resize((2 * itu_rov_gui.subway_car.w1) + (2 * itu_rov_gui.subway_car.h1), itu_rov_gui.subway_car.w1)
        self.verticalLayout = QtWidgets.QVBoxLayout(photomastic)
        self.verticalLayout.setObjectName("verticalLayout")
        self.photomastic_lb = QtWidgets.QLabel(photomastic)
        self.result = cv2.cvtColor(self.result, cv2.COLOR_BGR2RGB)
        self.result = QtGui.QImage(self.result.data, self.result.shape[1], self.result.shape[0],
                                   self.result.shape[1] * self.result.shape[2], QtGui.QImage.Format_RGB888)
        self.photomastic_lb.setPixmap(QtGui.QPixmap(self.result))
        self.photomastic_lb.setObjectName("photomastic_lb")
        self.verticalLayout.addWidget(self.photomastic_lb)
        self.photomastic_lb.setPixmap(QtGui.QPixmap(self.result))
        self.retranslateUi(photomastic)
        QtCore.QMetaObject.connectSlotsByName(photomastic)

    def retranslateUi(self, photomastic):
        _translate = QtCore.QCoreApplication.translate
        photomastic.setWindowTitle(_translate("photomastic", "PHOTOMOSAIC"))


class UiMapping(QWidget):
    def setupUi(self, mapping_window):
        mapping_window.setObjectName("mapping_window")
        mapping_window.resize(1400, 950)

        self.gridLayout = QtWidgets.QGridLayout(mapping_window)
        self.gridLayout.setObjectName("gridLayout")

        self.coral_reef_lb = QtWidgets.QLabel(mapping_window)
        self.coral_reef_img = itu_rov_gui.coral_reef_img
        self.coral_reef_img = cv2.cvtColor(self.coral_reef_img, cv2.COLOR_BGR2RGB)
        self.coral_reef_img = cv2.rotate(self.coral_reef_img, rotateCode=cv2.ROTATE_90_COUNTERCLOCKWISE)
        self.coral_reef_img = cv2.resize(self.coral_reef_img, (450, 900))
        self.coral_reef_img = QtGui.QImage(self.coral_reef_img.data, self.coral_reef_img.shape[1],
                                           self.coral_reef_img.shape[0], self.coral_reef_img.shape[1] *
                                           self.coral_reef_img.shape[2], QtGui.QImage.Format_RGB888)
        self.coral_reef_lb.setPixmap(QtGui.QPixmap(self.coral_reef_img))
        self.gridLayout.addWidget(self.coral_reef_lb, 0, 0, 1, 1, alignment=Qt.AlignCenter)
        ###########
        self.coral_reef_map1_lb = QtWidgets.QLabel(mapping_window)
        self.mapping_img1 = itu_rov_gui.mapping.mapping_screen
        self.mapping_img1 = cv2.cvtColor(self.mapping_img1, cv2.COLOR_BGR2RGB)
        self.mapping_img1 = cv2.rotate(self.mapping_img1, rotateCode=cv2.ROTATE_90_COUNTERCLOCKWISE)
        # self.mapping_img1 = cv2.resize(self.mapping_img1, (450, 900))
        self.mapping_img1 = QtGui.QImage(self.mapping_img1.data, self.mapping_img1.shape[1],
                                           self.mapping_img1.shape[0], self.mapping_img1.shape[1] *
                                           self.mapping_img1.shape[2], QtGui.QImage.Format_RGB888)
        self.coral_reef_map1_lb.setPixmap(QtGui.QPixmap(self.mapping_img1))
        self.gridLayout.addWidget(self.coral_reef_map1_lb, 0, 1, 1, 1, alignment=Qt.AlignCenter)
        #############
        self.coral_reef_map2_lb = QtWidgets.QLabel(mapping_window)
        self.mapping_img2 = itu_rov_gui.mapping.mapping_screen_map
        self.mapping_img2 = cv2.cvtColor(self. mapping_img2, cv2.COLOR_BGR2RGB)
        self.mapping_img2 = cv2.rotate(self.mapping_img2, rotateCode=cv2.ROTATE_90_COUNTERCLOCKWISE)
        # self.mapping_img2 = cv2.resize(self.mapping_img2, (450, 900))
        self.mapping_img2 = QtGui.QImage(self.mapping_img2.data, self.mapping_img2.shape[1],
                                         self.mapping_img2.shape[0], self.mapping_img2.shape[1] *
                                         self.mapping_img2.shape[2], QtGui.QImage.Format_RGB888)
        self.coral_reef_map2_lb.setPixmap(QtGui.QPixmap(self.mapping_img2))
        self.gridLayout.addWidget(self.coral_reef_map2_lb, 0, 2, 1, 1, alignment=Qt.AlignCenter)
        ##############
        self.pool_side_lb = QtWidgets.QLabel(mapping_window)
        self.pool_side_lb.setText("  -  Side of pool  -  ")
        self.pool_side_lb.setStyleSheet("color : rgb(0, 0, 0); font-size: 20pt; background-color: white")
        self.gridLayout.addWidget(self.pool_side_lb, 1, 0, 1, 3, alignment=Qt.AlignCenter)

        self.retranslateUi(mapping_window)
        QtCore.QMetaObject.connectSlotsByName(mapping_window)

    def retranslateUi(self, mapping_window):
        _translate = QtCore.QCoreApplication.translate
        mapping_window.setWindowTitle(_translate("mapping_window", "MAPPING PHOTO MISSION"))


class UiCoralPhotoWindow(QWidget):
    def setupUi(self, coral_window):
        coral_window.setObjectName("coral_window")
        coral_window.resize(1300, 800)

        self.gridLayout = QtWidgets.QGridLayout(coral_window)

        self.coral_before_name_lb = QtWidgets.QLabel(coral_window)
        self.coral_before_name_lb.setText("- Before Photo -")
        self.coral_before_name_lb.setStyleSheet("font-size: 20pt")
        self.gridLayout.addWidget(self.coral_before_name_lb, 0, 0, 1, 2, alignment=Qt.AlignCenter)

        self.coral_before_lb = QtWidgets.QLabel(coral_window)
        photo_before = itu_rov_gui.coral_colony_before_photo
        photo_before = cv2.cvtColor(photo_before, cv2.COLOR_BGR2RGB)
        photo_before = cv2.resize(photo_before, (600, 600))
        photo_before = QtGui.QImage(photo_before.data, photo_before.shape[1], photo_before.shape[0],
                                    photo_before.shape[1] * photo_before.shape[2], QtGui.QImage.Format_RGB888)
        self.coral_before_lb.setPixmap(QtGui.QPixmap(photo_before))
        self.gridLayout.addWidget(self.coral_before_lb, 1, 0, 1, 2, alignment=Qt.AlignCenter)
        ##########
        self.coral_after_name_lb = QtWidgets.QLabel(coral_window)
        self.coral_after_name_lb.setText("- Current Photo -")
        self.coral_after_name_lb.setStyleSheet("font-size: 20pt")
        self.gridLayout.addWidget(self.coral_after_name_lb, 0, 2, 1, 2, alignment=Qt.AlignCenter)

        self.coral_after_lb = QtWidgets.QLabel(coral_window)
        photo_after = itu_rov_gui.coral_colony_diff
        photo_after = cv2.cvtColor(photo_after, cv2.COLOR_BGR2RGB)
        photo_after = cv2.resize(photo_after, (600, 600))
        photo_after = QtGui.QImage(photo_after.data, photo_after.shape[1], photo_after.shape[0],
                                   photo_after.shape[1] * photo_after.shape[2], QtGui.QImage.Format_RGB888)
        self.coral_after_lb.setPixmap(QtGui.QPixmap(photo_after))
        self.gridLayout.addWidget(self.coral_after_lb, 1, 2, 1, 2, alignment=Qt.AlignCenter)
        ##########
        self.area_growth_lb = QtWidgets.QLabel(coral_window)
        self.area_growth_lb.setText(" Growth ")
        self.area_growth_lb.setStyleSheet("color : rgb(0, 255, 0); background-color: white; "
                                          "font-size: 20pt; font-weight: bold")
        self.gridLayout.addWidget(self.area_growth_lb, 2, 0, 1, 1, alignment=Qt.AlignCenter)

        self.area_death_lb = QtWidgets.QLabel(coral_window)
        self.area_death_lb.setText(" Death ")
        self.area_death_lb.setStyleSheet("color : rgb(255, 255, 0); background-color: white; "
                                         "font-size: 20pt; font-weight: bold")
        self.gridLayout.addWidget(self.area_death_lb, 2, 1, 1, 1, alignment=Qt.AlignCenter)

        self.area_bleach_lb = QtWidgets.QLabel(coral_window)
        self.area_bleach_lb.setText(" Bleaching ")
        self.area_bleach_lb.setStyleSheet("color : rgb(255, 0, 0); background-color: white; "
                                          "font-size: 20pt; font-weight: bold")
        self.gridLayout.addWidget(self.area_bleach_lb, 2, 2, 1, 1, alignment=Qt.AlignCenter)

        self.area_recov_lb = QtWidgets.QLabel(coral_window)
        self.area_recov_lb.setText(" Recovered ")
        self.area_recov_lb.setStyleSheet("color : rgb(0, 0, 255); background-color: white; "
                                         "font-size: 20pt; font-weight: bold")
        self.gridLayout.addWidget(self.area_recov_lb, 2, 3, 1, 1, alignment=Qt.AlignCenter)

        self.retranslateUi(coral_window)
        QtCore.QMetaObject.connectSlotsByName(coral_window)

    def retranslateUi(self, coral_window):
        _translate = QtCore.QCoreApplication.translate
        coral_window.setWindowTitle(_translate("coral_window", "CORAL COLONY PHOTO MISSION"))


class CameraShowThread(QThread, MainWindow):
    """
    - Thread -
    Arayüzde seçilen kamerayı araçtan alarak arayüze göndermekle görevli thread'dir.
    """
    changePixmap = QtCore.pyqtSignal(QtGui.QImage, object)

    def __init__(self):
        super(CameraShowThread, self).__init__()

    def run(self):

        video1 = Video(port=2000, selection=0)
        video2 = Video(port=5800, selection=1)
        video3 = Video(port=5000, selection=2)

        frame = []
        while True:
            if not itu_rov_gui.system:
                break

            if itu_rov_gui.camera_var == 0:
                time.sleep(0.5)
                continue

            if itu_rov_gui.camera_var == 1:
                if not video1.frame_available():
                    continue
                frame = video1.frame()
            elif itu_rov_gui.camera_var == 2:
                if not video2.frame_available():
                    continue
                frame = video2.frame()
                #frame = cv2.flip(frame, -1)
            elif itu_rov_gui.camera_var == 3:
                if not video3.frame_available():
                    continue
                frame = video3.frame()

            if itu_rov_gui.coralMission:
                frame = itu_rov_gui.mission_coral_colony(frame)
            elif itu_rov_gui.photomosaicMission:
                frame = itu_rov_gui.mission_photomosaic_with_rects(frame)
            elif itu_rov_gui.autonomousMission:
                frame = itu_rov_gui.mission_autonomous_flying(frame)
                frame = frame[100:540, 50:430]

            if itu_rov_gui.video_record:
                itu_rov_gui.recorder.write(frame)

            self.rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.rgbImage = cv2.resize(self.rgbImage, (1280, 720), interpolation=cv2.INTER_LINEAR)
            self.frame_qt = QtGui.QImage(self.rgbImage.data, self.rgbImage.shape[1], self.rgbImage.shape[0],
                                         self.rgbImage.shape[1] * self.rgbImage.shape[2], QtGui.QImage.Format_RGB888)
            self.changePixmap.emit(self.frame_qt, self.rgbImage)


class MainThread(QtCore.QThread):
    """
    - Thread -
    Ana Rov ile olan bağlantıyı kuran thread'dir. Joystick'de basılan butonlara göre gripper ve ışığı kontrol eder.
    """
    def run(self):

        self.s = Server(port=5566)
        self.s.bind_Server()
        self.s.setupConnection()
        self.s.axis_list = []
        time.sleep(1)

        while True:
            time.sleep(0.01)
            if not itu_rov_gui.system:
                break

            if self.s.connection:
                gripper_comm = ""
                if itu_rov_gui.joy.connected:
                    # 38 ac, 36 saat tersi, 40 kapat, 32 saat yonu
                    try:
                        if itu_rov_gui.joy.gripper_open:
                            gripper_comm = gripper_comm + "1"
                        else:
                            gripper_comm = gripper_comm + "0"

                        if itu_rov_gui.joy.gripper_close:
                            gripper_comm = gripper_comm + "2"
                        else:
                            gripper_comm = gripper_comm + "0"

                        if itu_rov_gui.joy.gripper_clockwise:
                            gripper_comm = gripper_comm + "3"
                        else:
                            gripper_comm = gripper_comm + "0"

                        if itu_rov_gui.joy.gripper_ctr_clockwise:
                            gripper_comm = gripper_comm + "4"
                        else:
                            gripper_comm = gripper_comm + "0"

                        if itu_rov_gui.joy.light_on:
                            gripper_comm = gripper_comm + "5"
                        else:
                            gripper_comm = gripper_comm + "0"

                        data = gripper_comm.encode('utf-8')
                        try:
                            # print("Sending trying")
                            self.s.conn.send(data)
                            # print("Sending Completed")

                        except BrokenPipeError as msg:
                            print("ROV ile baglanti koptu!")
                            msg = "Data Transfer2 BrokenPipe Exception:" + str(msg)
                            self.s.connection = False
                            self.s.bind_Server()
                            self.s.setupConnection()

                        except Exception as msg:
                            # print("data transfer exception : ", msg)
                            msg = "Data Transfer2 Exception: [FATAL]" + str(msg)
                            self.s.connection = False
                            self.s.bind_Server()
                            self.s.setupConnection()
                            print(msg)
                    except Exception as e:
                        print(str(e))
                        pass
                else:
                    # Joystick yok.
                    pass
            else:
                self.s.bind_Server()
                self.s.setupConnection()
                time.sleep(1)
                print("aaa")
            # if not self.gripper_cb.isChecked():
            #     ui.joy.pressed_buttons = []

            # Status Check Start ----------------------------------------------


class MikroThread(QtCore.QThread):
    """
    - Thread -
    Micro Rov ile olan bağlantıyı kuran thread'dir. Joystick'de basılan butonlara göre tekerlekler ve gripperı kontrol
    eder.
    """
    def run(self):

        self.s = Server(port=5560)
        self.s.bind_Server()
        self.s.setupConnection()
        itu_rov_gui.microKeys = []
        time.sleep(1)

        while True:
            time.sleep(0.01)
            if not itu_rov_gui.system:
                break

            if self.s.connection:
                gripper_comm = ""
                if itu_rov_gui.joy.connected:
                    joy_axis_list = itu_rov_gui.joy.axis_list
                    # 38 ac, 36 saat tersi, 40 kapat, 32 saat yonu
                    try:
                        if itu_rov_gui.joy.gripper_open:
                            gripper_comm = gripper_comm + "a"
                        else:
                            gripper_comm = gripper_comm + "b"
                        if itu_rov_gui.joy.gripper_close:
                            gripper_comm = gripper_comm + "c"
                        else:
                            gripper_comm = gripper_comm + "d"
                        if itu_rov_gui.joy.gripper_clockwise:
                            gripper_comm = gripper_comm + "e"
                        else:
                            gripper_comm = gripper_comm + "f"
                        if itu_rov_gui.joy.gripper_ctr_clockwise:
                            gripper_comm = gripper_comm + "g"
                        else:
                            gripper_comm = gripper_comm + "h"
                        data = gripper_comm.encode('utf-8')
                        try:
                            # print("Sending trying")
                            self.s.conn.send(data)
                            # print("Sending Completed")

                        except BrokenPipeError as msg:
                            print("Micro Rov ile baglanti koptu!")
                            msg = "Data Transfer2 BrokenPipe Exception:" + str(msg)
                            self.s.connection = False
                            self.s.bind_Server()
                            self.s.setupConnection()

                        except Exception as msg:
                            # print("data transfer exception : ", msg)
                            msg = "Data Transfer2 Exception: [FATAL]" + str(msg)
                    except Exception as e:
                        print(str(e))
                        pass
                else:
                    # Joystick yok.
                    pass


class Server:
    """
    MainThread ve MikroThread'de kullanılan soket bağlantısını kolaylaştıran class'tır.
    """
    def __init__(self, port):
        self.host = "192.168.2.1"
        self.port = port
        self.buffer_size = 1024
        self.axis_list = []
        self.timer = time.time()
        self.new_conn = False
        self.connection = False

    def bind_Server(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # print("Socket created")
        try:
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.host, self.port))
            print("Socket bind complete")
        except socket.error as msg:
            msg = "Bind Server error : " + str(msg)
            print(msg)
        except Exception as msg:
            msg = "Bind Server Execption : " + str(msg)
            print(msg)

        return self.s

    def setupConnection(self):
        self.s.listen(2)     # self.s.listen(1) degistirildi.
        self.connection = False
        self.conn, self.address = self.s.accept()
        self.conn.settimeout(0.5)
        time.sleep(0.5)
        self.axis_list = []
        self.timer = time.time()
        print("Connected to: " + self.address[0] + ":" + str(self.address[1]))
        self.connection = True


class Joy(QtCore.QThread):
    """
    - Thread -
    Bilgisayara bağlı kontrolcüyü tespit etmek ve değişen buton ve eksen bilgilerini almakla görevli thread'dir.
    """
    def __init__(self):
        super(Joy, self).__init__()
        self.joy_conn = False
        self.joy_conn = True
        self.axis_list = []
        self.gripper_open = False
        self.gripper_close = False
        self.gripper_clockwise = False
        self.gripper_ctr_clockwise = False
        self.light_on = False
        self.events = []
        self.pressed_buttons = []
        self.lastTime = 0
        self.lastActive = 0
        self.pygame = pygame
        self.pygame.init()
        self.clock = pygame.time.Clock()
        self.pygame.joystick.init()
        if self.pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.axes = self.joystick.get_numaxes()
            self.buttons = self.joystick.get_numbuttons()
            self.connected = True
        else:
            self.connected = False

    def reconnect(self):
        self.pygame.joystick.quit()
        self.pygame.joystick.init()
        if self.pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.axes = self.joystick.get_numaxes()
            self.buttons = self.joystick.get_numbuttons()
            self.connected = True
            itu_rov_gui.warnings_list.append("Joystick connected.")
        else:
            self.connected = False
            itu_rov_gui.warnings_list.append("Joystick does not appear to be connected!")

    def run(self):
        while True:
            if not itu_rov_gui.system:
                break

            if itu_rov_gui.joy_refr:
                self.pressed_buttons = []
                itu_rov_gui.joy_sld0.setValue(0)
                itu_rov_gui.joy_sld1.setValue(0)
                itu_rov_gui.joy_sld2.setValue(0)
                itu_rov_gui.joy_sld3.setValue(0)
                itu_rov_gui.joy_sld4.setValue(0)
                itu_rov_gui.joy_sld5.setValue(0)
                itu_rov_gui.joy_sld6.setValue(0)
                self.show_buttons()
                self.reconnect()
                itu_rov_gui.joy_refr = False

            if self.connected:
                try:
                    self.events = self.pygame.event.get()
                    self.which_button()
                    self.which_axes()
                except pygame.error as msg:
                    pass
            self.clock.tick(30)

    def which_button(self):
        self.pressed_buttons = []
        # print("Buttons : " + str(self.buttons))

        for i in range(self.buttons):
            if self.joystick.get_button(i) == 1:
                self.pressed_buttons.append(i)
        self.show_buttons()

        for event in self.events:
            if event.type == pygame.JOYBUTTONDOWN:
                self.lastActive = time.time()
                # print("Button Pressed")

                if self.joystick.get_button(10):
                    self.gripper_open = True
                elif self.joystick.get_button(8):
                    self.gripper_close = True

                if self.joystick.get_button(4):
                    self.gripper_clockwise = True
                elif self.joystick.get_button(9):
                    self.gripper_ctr_clockwise = True

                if self.joystick.get_button(17):
                    self.light_on = True
                else:
                    self.light_on = False

            elif event.type == pygame.JOYBUTTONUP:
                self.gripper_open = False
                self.gripper_close = False
                self.gripper_clockwise = False
                self.gripper_ctr_clockwise = False


    def show_buttons(self):
        if 0 in self.pressed_buttons:
            itu_rov_gui.joy_0_lb.setText("<font color=\"black\">0 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_0_lb.setText("<font color=\"black\">0 <font color=\"white\">: <font color=\"red\">▯")
        if 1 in self.pressed_buttons:
            itu_rov_gui.joy_1_lb.setText("<font color=\"black\">1 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_1_lb.setText("<font color=\"black\">1 <font color=\"white\">: <font color=\"red\">▯")
        if 2 in self.pressed_buttons:
            itu_rov_gui.joy_2_lb.setText("<font color=\"black\">2 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_2_lb.setText("<font color=\"black\">2 <font color=\"white\">: <font color=\"red\">▯")
        if 3 in self.pressed_buttons:
            itu_rov_gui.joy_3_lb.setText("<font color=\"black\">3 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_3_lb.setText("<font color=\"black\">3 <font color=\"white\">: <font color=\"red\">▯")
        if 4 in self.pressed_buttons:
            itu_rov_gui.joy_4_lb.setText("<font color=\"black\">4 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_4_lb.setText("<font color=\"black\">4 <font color=\"white\">: <font color=\"red\">▯")
        if 5 in self.pressed_buttons:
            itu_rov_gui.joy_5_lb.setText("<font color=\"black\">5 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_5_lb.setText("<font color=\"black\">5 <font color=\"white\">: <font color=\"red\">▯")
        if 6 in self.pressed_buttons:
            itu_rov_gui.joy_6_lb.setText("<font color=\"black\">6 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_6_lb.setText("<font color=\"black\">6 <font color=\"white\">: <font color=\"red\">▯")
        if 7 in self.pressed_buttons:
            itu_rov_gui.joy_7_lb.setText("<font color=\"black\">7 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_7_lb.setText("<font color=\"black\">7 <font color=\"white\">: <font color=\"red\">▯")
        if 8 in self.pressed_buttons:
            itu_rov_gui.joy_8_lb.setText("<font color=\"black\">8 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_8_lb.setText("<font color=\"black\">8 <font color=\"white\">: <font color=\"red\">▯")
        if 9 in self.pressed_buttons:
            itu_rov_gui.joy_9_lb.setText("<font color=\"black\">9 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_9_lb.setText("<font color=\"black\">9 <font color=\"white\">: <font color=\"red\">▯")
        if 10 in self.pressed_buttons:
            itu_rov_gui.joy_10_lb.setText("<font color=\"black\">10 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_10_lb.setText("<font color=\"black\">10 <font color=\"white\">: <font color=\"red\">▯")
        if 11 in self.pressed_buttons:
            itu_rov_gui.joy_11_lb.setText("<font color=\"black\">11 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_11_lb.setText("<font color=\"black\">11 <font color=\"white\">: <font color=\"red\">▯")
        if 12 in self.pressed_buttons:
            itu_rov_gui.joy_12_lb.setText("<font color=\"black\">12 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_12_lb.setText("<font color=\"black\">12 <font color=\"white\">: <font color=\"red\">▯")
        if 13 in self.pressed_buttons:
            itu_rov_gui.joy_13_lb.setText("<font color=\"black\">13 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_13_lb.setText("<font color=\"black\">13 <font color=\"white\">: <font color=\"red\">▯")
        if 14 in self.pressed_buttons:
            itu_rov_gui.joy_14_lb.setText("<font color=\"black\">14 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_14_lb.setText("<font color=\"black\">14 <font color=\"white\">: <font color=\"red\">▯")
        if 15 in self.pressed_buttons:
            itu_rov_gui.joy_15_lb.setText("<font color=\"black\">15 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_15_lb.setText("<font color=\"black\">15 <font color=\"white\">: <font color=\"red\">▯")
        if 16 in self.pressed_buttons:
            itu_rov_gui.joy_16_lb.setText("<font color=\"black\">16 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_16_lb.setText("<font color=\"black\">16 <font color=\"white\">: <font color=\"red\">▯")
        if 17 in self.pressed_buttons:
            itu_rov_gui.joy_17_lb.setText("<font color=\"black\">17 <font color=\"white\">: <font color=\"red\">▮")
        else:
            itu_rov_gui.joy_17_lb.setText("<font color=\"black\">17 <font color=\"white\">: <font color=\"red\">▯")

    def which_axes(self):
        self.axes = self.joystick.get_numaxes()
        # msg = ""
        for i in range(self.axes):
            self.axis = self.joystick.get_axis(i)
            if i == 0:
                itu_rov_gui.joy_sld0.setValue(int(self.axis * 100))
            if i == 1:
                itu_rov_gui.joy_sld1.setValue(int(self.axis * 100))
            if i == 2:
                itu_rov_gui.joy_sld2.setValue(int(self.axis * 100))
            if i == 3:
                itu_rov_gui.joy_sld3.setValue(int(self.axis * 100))
            if i == 4:
                itu_rov_gui.joy_sld4.setValue(int(self.axis * 100))
            if i == 5:
                itu_rov_gui.joy_sld5.setValue(int(self.axis * 100))
            if i == 6:
                itu_rov_gui.joy_sld6.setValue(int(self.axis * 100))
            if self.axis:
                self.lastActive = time.time()
                # msg = msg + "**"
            # print(self.axis)
            # msg = msg + "Axis {} value: {:>6.3f}    ". format(i, self.axis)
        # print(msg)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(70, 70, 70))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(40, 40, 40))
    palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.gray)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(90, 90, 90))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    itu_rov_gui = MainWindow()
    itu_rov_gui.setupUi()
    itu_rov_gui.show()

    sys.exit(app.exec_())
