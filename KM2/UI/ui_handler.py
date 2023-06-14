# -*- coding: utf-8 -*-
############################
# **** IMPORT SECTION **** #
############################
import sys
import os
import shutil

import linuxcnc
import hal
import time
import datetime
import sqlite3
#from lib import gcode_cam
from gcode_cam import Cam


from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor, QPixmap

from qtvcp.widgets.gcode_editor import GcodeEditor as GCODE
from qtvcp.widgets.mdi_line import MDILine as MDI_WIDGET
from qtvcp.widgets.tool_offsetview import ToolOffsetView as TOOL_TABLE
from qtvcp.widgets.origin_offsetview import OriginOffsetView as OFFSET_VIEW
from qtvcp.widgets.stylesheeteditor import StyleSheetEditor as SSE
from qtvcp.widgets.file_manager import FileManager as FM
from qtvcp.lib.keybindings import Keylookup
from qtvcp.lib.gcodes import GCodes
from qtvcp.lib.toolbar_actions import ToolBarActions
from qtvcp.core import Status, Action, Info
from qtvcp import logger
from shutil import copyfile

# Set up logging
from qtvcp import logger
LOG = logger.getLogger(__name__)

# Set the log level for this module
# LOG.setLevel(logger.INFO) # One of DEBUG, INFO, WARNING, ERROR, CRITICAL

###########################################
# **** instantiate libraries section **** #
###########################################
KEYBIND = Keylookup()
STATUS = Status()
INFO = Info()
ACTION = Action()
TOOLBAR = ToolBarActions()
STYLEEDITOR = SSE()

# constants for tab pages
TAB_MAIN = 0
TAB_FILE = 1
TAB_TOOL = 2
TAB_OFFSETS = 3
TAB_CAM = 4
TAB_SETTINGS = 5
TAB_STATUS = 6

SECOND_TO_HOURS = 3600


CSS_DEFAUT = """
    QPushButton:disabled {
      background-color: #32414B;
      border: 1px solid #32414B;
      color: #787878;
      border-radius: 4px;
      padding: 3px;
    }
    QPushButton:checked {
      background-color: #32414B;
      border: 1px solid #32414B;
      border-radius: 4px;
      padding: 3px;
      outline: none;
    }
    QPushButton:checked:disabled {
      background-color: #19232D;
      border: 1px solid #32414B;
      color: #787878;
      border-radius: 4px;
      padding: 3px;
      outline: none;
    }
    QPushButton:checked:selected {
      background: #1464A0;
      color: #32414B;
    }
    QPushButton::menu-indicator {
      subcontrol-origin: padding;
      subcontrol-position: bottom right;
      bottom: 4px;
    }
    QPushButton:pressed {
      background-color: #19232D;
      border: 1px solid #19232D;
    }
    QPushButton:pressed:hover {
      border: 1px solid #148CD2;
    }
    QPushButton:selected {
      background: #1464A0;
      color: #32414B;
    }
    QPushButton:focus {
      border: 1px solid #1464A0;
    }
    """
###################################
# **** HANDLER CLASS SECTION **** #
###################################


class HandlerClass:
    ########################
    # **** INITIALIZE **** #
    ########################
    # widgets allows access to  widgets from the qtvcp files
    # at this point the widgets and hal pins are not instantiated
    def __init__(self, halcomp, widgets, paths):
        self.h = halcomp
        self.w = widgets
        self.PATHS = paths
        self.gcodes = GCodes()

        self.conn = sqlite3.connect('/home/cnc/KM2/UI/my_db.db')
        self.cur = self.conn.cursor()
        
        
        self.stat = linuxcnc.stat()
        self.cmnd = linuxcnc.command()
        self.error = linuxcnc.error_channel()

        self.gcode_cam = Cam()
        self.is_initialized = False
        self.init_time = time.time()
        
        

        KEYBIND.add_call('Key_F12', 'on_keycall_F12')
        KEYBIND.add_call('Key_Pause', 'on_keycall_pause')

        self.last_loaded_program = ""
        self.delete_file = None

        self.home_all = False
        self.reload_tool = 0
        self.first_turnon = True
        self.first_click_flushing = False

        self.slow_jog_factor = 10

        self.max_linear_velocity = INFO.MAX_LINEAR_JOG_VEL
        self.system_list = ["G54", "G55", "G56", "G57",
                            "G58", "G59", "G59.1", "G59.2", "G59.3"]
        self.axis_x_list = ["dSbox_pos1_x", "dSbox_pos2_x",
                            "offset_newvalue_x", "dSbox_flushing_x", "dSbox_reset_x"]
        self.axis_y_list = ["dSbox_pos1_y", "dSbox_pos2_y",
                            "offset_newvalue_y", "dSbox_flushing_y", "dSbox_reset_y"]
        self.axis_z_list = ["dSbox_pos1_z", "dSbox_pos2_z",
                            "offset_newvalue_z", "dSbox_flushing_z", "dSbox_reset_z"]
        self.offset_button = ["offset_g54", "offset_g55", "offset_g56", "offset_g57",
                              "offset_g58", "offset_g59", "offset_g591", "offset_g592",
                              "offset_g593"]
        self.offset_set_button = ["offset_x2", "offset_y2", "offset_z2",
                                  "offset_set_x", "offset_set_y", "offset_set_z"]
        self.cam_elemen = ["dsb_radius_1", "dsb_radius_2", "dsb_radius_3", "dsb_radius_4",
                           "lbl_radius_1", "lbl_radius_2", "lbl_radius_3", "lbl_radius_4",
                           "dsb_length", "label_65", "dsb_width", "label_75"]
        self.is_homed_list = ["step_cunt", "step_50",
                              "step_10", "step_5", "step_1", "step_05","jog_rate"]
        self.onoff_list = ["cycle_buttons", "extended_buttons",
                           "settings_buttons", "components_buttons"]
        self.progressbar_pressure_a = [
            "progressBar_a_comp", "progressBar_a_comp_2"]
        self.progressbar_pressure_b = [
            "progressBar_b_comp", "progressBar_b_comp_2"]
        self.is_saturation_a = ["btn_reset_components",
                                "btn_test_comp_a", "btn_test_comp_b", "btn_test_mix",
                                "cycle_buttons"]
        self.is_mixing_a = ["btn_reset_components",
                            "btn_test_comp_a", "btn_test_comp_b", "btn_test_mix",
                            "cycle_buttons"]
        self.is_recuperation_a = ["btn_reset_components",
                                  "btn_test_comp_a", "btn_test_comp_b", "btn_test_mix",
                                  "cycle_buttons"]
        self.is_saturation_b = ["btn_reset_components",
                                "btn_test_comp_a", "btn_test_comp_b", "btn_test_mix",
                                "cycle_buttons"]
        self.is_mixing_b = ["btn_reset_components",
                            "btn_test_comp_a", "btn_test_comp_b", "btn_test_mix",
                            "cycle_buttons"]
        self.is_recuperation_b = ["btn_reset_components",
                                  "btn_test_comp_a", "btn_test_comp_b", "btn_test_mix",
                                  "cycle_buttons"]
        self.is_flushing = ["btn_reset_components", "btn_to_pos1", "btn_to_pos2",
                            "btn_test_comp_a", "btn_test_comp_b", "btn_test_mix",
                            "cycle_buttons", "mdiline"]
        self.is_reset_components = ["btn_saturation_a", "btn_mixing_a", "btn_recuperation_a",
                                    "btn_saturation_b", "btn_mixing_b", "btn_recuperation_b",
                                    "btn_washed", "btn_to_pos1", "btn_to_pos2",
                                    "btn_test_comp_a", "btn_test_comp_b", "btn_test_mix"]
        self.is_app = ["btn_saturation_a", "btn_mixing_a", "btn_recuperation_a",
                       "btn_saturation_b", "btn_mixing_b", "btn_recuperation_b",
                       "btn_washed", "btn_reset_components", "btn_to_pos1", "btn_to_pos2",
                       "btn_test_comp_a", "btn_test_comp_b", "btn_test_mix"]
        self.is_test_a = ["btn_saturation_a", "btn_mixing_a", "btn_recuperation_a",
                          "btn_saturation_b", "btn_mixing_b", "btn_recuperation_b",
                          "btn_washed", "btn_reset_components", "btn_to_pos1", "btn_to_pos2",
                          "btn_test_comp_b", "btn_test_mix",
                          "cycle_buttons"]
        self.is_test_b = ["btn_saturation_a", "btn_mixing_a", "btn_recuperation_a",
                          "btn_saturation_b", "btn_mixing_b", "btn_recuperation_b",
                          "btn_washed", "btn_reset_components", "btn_to_pos1", "btn_to_pos2",
                          "btn_test_comp_a", "btn_test_mix",
                          "cycle_buttons"]
        self.is_test_mix = ["btn_saturation_a", "btn_mixing_a", "btn_recuperation_a",
                            "btn_saturation_b", "btn_mixing_b", "btn_recuperation_b",
                            "btn_washed", "btn_reset_components", "btn_to_pos1", "btn_to_pos2",
                            "btn_test_comp_a", "btn_test_comp_b",
                            "cycle_buttons"]
        self.setup_btn = [
            "actionbutton_calibration", "actionbutton_lcnc_status", "actionbutton_halscope",
            "actionbutton_halshow", "actionbutton_halmeter" ]
        self.pos_flushing = [
            "dSbox_flushing_x", "dSbox_flushing_y", "dSbox_flushing_z",
            "dSbox_reset_x", "dSbox_reset_y" , "dSbox_reset_z",
            "label_58" , "label_59" ]
        STATUS.connect('general', self.dialog_return)

        STATUS.connect("state-estop",lambda w: self.state_estop(False))
        STATUS.connect("state-estop-reset",lambda w: self.state_estop(True))
        
        STATUS.connect('state-on', lambda w: self.enable_onoff(True))
        STATUS.connect('state-off', lambda w: self.enable_onoff(False))

        STATUS.connect('user-system-changed', self.user_system_changed)
        STATUS.connect('periodic', lambda w: self.update_runtimer())
        STATUS.connect('gcode-line-selected', lambda w, line: self.set_start_line(line))
        STATUS.connect('interp-idle', lambda w: self.set_start_line(0))
        STATUS.connect('file-loaded', self.file_loaded)
        STATUS.connect('homed', self.homed)
        STATUS.connect('all-homed', self.all_homed)
        STATUS.connect('not-all-homed', self.not_all_homed)

        # Доупстимые расширения файлов
        self.ext = (".ngc", ".txt", ".tap", ".py")

        #method_list = [func for func in dir(self.w.PREFS_) if callable(getattr(self.w.PREFS_, func))]

    ##########################################
    # Special Functions called from QTSCREEN
    ##########################################

    # at this point:
    # the widgets are instantiated.
    # the HAL pins are built but HAL is not set ready

    def class_patch__(self):
        self.old_fman = FM.load
        FM.load = self.load_code
        self.old_save = GCODE.saveCall
        GCODE.saveCall = self.editor_save
        GCODE.exitCall = self.editor_exit

    def initialized__(self):
        self.init_pins()
        self.init_widgets()
        self.init_preferences()

        self.w.stackedWidget_log.setCurrentIndex(0)
        # Иницилизация файлового менеджерена настройка путей по умолчанию
        self.w.filemanager_usb.button.setText('USB')        
        self.w.filemanager_usb.button2.hide()
        self.w.filemanager_usb.default_path = (os.path.join('/media/cnc'))
        self.w.filemanager_usb.user_path = (os.path.join('/media/cnc'))
        self.w.filemanager_usb.list.setAlternatingRowColors(False)
        self.w.filemanager_usb.onMediaClicked()

        self.w.filemanager.button.hide()
        self.w.filemanager.button2.setText('GCODE')
        self.w.filemanager.default_path = (os.path.join('./gcode'))
        self.w.filemanager.user_path = (os.path.join('./gcode'))
        self.w.filemanager.list.setAlternatingRowColors(False)
        self.w.filemanager.onUserClicked()


        self.chk_run_from_line_checked(self.w.chk_run_from_line.isChecked())
        # Убераем ползунок скорсоти насосов
        self.w["widget_pump_ovr"].hide()
        # Убираем скорость шпинделя
        self.w["widget_spindle_ovr_3"].hide()
        # убираем данные о подачи готовой смеси
        self.w["feed_comp_mix"].hide()
        self.w["label_56"].hide()
        self.w["btn_reset_components"].hide()
        self.w.sb_tool_number.hide()
        self.w.label_120.hide()
        self.w.tool_diam_mm.hide()
        self.w.label_121.hide()
        self.w.cycle_step.hide()
        self.w.cycle_pause.hide()
        self.w.cycle_m1_stop.hide()
        #Время последнего включения насоса A and B
        self.start_time_pump_a = time.time()
        self.start_time_pump_b = time.time()


        self.widget_management_show(self.setup_btn, False)
        self.widget_management_show(self.pos_flushing, False)

        self.is_initialized = True
        self.init_time = time.time()
        ######

    def init_pins(self):
        pin = self.h.newpin("pressure-a", hal.HAL_FLOAT, hal.HAL_IN)
        pin.value_changed.connect(self.pressure_changed)
        pin = self.h.newpin("pressure-b", hal.HAL_FLOAT, hal.HAL_IN)
        pin.value_changed.connect(self.pressure_changed)
        pin = self.h.newpin("mixer-tor", hal.HAL_FLOAT, hal.HAL_IN)
        pin.value_changed.connect(self.mixer_changed)
        pin = self.h.newpin("go_to_pos1", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_go_to_pos1)
        pin = self.h.newpin("remote-start", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_start)
        pin = self.h.newpin("mode", hal.HAL_U32, hal.HAL_IN)
        #pin.value_changed.connect(self.pin_mode)

        self.h.newpin("homme-all", hal.HAL_BIT, hal.HAL_OUT)

        #пины для контроя необходимости промывуи
        self.h.newpin("flushing.is-count", hal.HAL_BIT, hal.HAL_IN)
        self.h.newpin("flushing.is-time", hal.HAL_BIT, hal.HAL_IN)
        self.h.newpin("flushing.time-last", hal.HAL_FLOAT, hal.HAL_IN)
        self.h.newpin("app.count", hal.HAL_U32, hal.HAL_IN)
        #пины c координатами промывки и сброса
        self.h.newpin("pos.flushing-x", hal.HAL_FLOAT, hal.HAL_OUT)
        self.h.newpin("pos.flushing-y", hal.HAL_FLOAT, hal.HAL_OUT)
        self.h.newpin("pos.flushing-z", hal.HAL_FLOAT, hal.HAL_OUT)

        self.h.newpin("pos.reset-x", hal.HAL_FLOAT, hal.HAL_OUT)
        self.h.newpin("pos.reset-y", hal.HAL_FLOAT, hal.HAL_OUT)
        self.h.newpin("pos.reset-z", hal.HAL_FLOAT, hal.HAL_OUT)     

        pin = self.h.newpin("test.a-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_test_component_a)
        pin = self.h.newpin("test.b-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_test_component_b)
        pin = self.h.newpin("test.mix-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_test_component_mix)

        pin = self.h.newpin("a.saturation-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_saturation_a)
        pin = self.h.newpin("b.saturation-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_saturation_b)
        pin = self.h.newpin("a.mixing-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_mixing_a)
        pin = self.h.newpin("b.mixing-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_mixing_b)
        pin = self.h.newpin("a.recovery-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_recovery_a)
        pin = self.h.newpin("b.recovery-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_recovery_b)
        pin = self.h.newpin("reset_components-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_reset_components)
        pin = self.h.newpin("flushing-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_flushing)
        pin = self.h.newpin("app-status", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_app)
       

        pin = self.h.newpin("min-a", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_min_a)
        pin = self.h.newpin("min-b", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_min_b)
        pin = self.h.newpin("min-solvent", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_min_solvent)
        pin = self.h.newpin("a.pressure.is-max", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_pressure_a)
        pin = self.h.newpin("b.pressure.is-max", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_pressure_b)

        pin = self.h.newpin("rele_motor", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_rele_motor)
        pin = self.h.newpin("servo_error", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_servo_error)
        pin = self.h.newpin("rele_air", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_rele_air)
        pin = self.h.newpin("rele_faz", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_rele_faz)
        #Время последнего включения насоса A and B
        pin = self.h.newpin("a.pump.motor-is-on", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_motor_on_a)
        pin = self.h.newpin("b.pump.motor-is-on", hal.HAL_BIT, hal.HAL_IN)
        pin.value_changed.connect(self.pin_motor_on_b)
        pin = self.h.newpin("a.recovery.timer-sleep-hour", hal.HAL_FLOAT, hal.HAL_IN)
        pin = self.h.newpin("b.recovery.timer-sleep-hour", hal.HAL_FLOAT, hal.HAL_IN)
        pin = self.h.newpin("a.recovery.timer-minutes", hal.HAL_FLOAT, hal.HAL_IN)
        pin = self.h.newpin("b.recovery.timer-minutes", hal.HAL_FLOAT, hal.HAL_IN)
        pin = self.h.newpin("a.recovery.timer-out-hour", hal.HAL_FLOAT, hal.HAL_OUT)
        pin = self.h.newpin("b.recovery.timer-out-hour", hal.HAL_FLOAT, hal.HAL_OUT)

    def init_widgets(self):
        self.w.slider_jog_linear.setMaximum(self.max_linear_velocity/6)
        self.w.slider_jog_linear.setValue(INFO.DEFAULT_LINEAR_JOG_VEL)
        self.w.slider_maxv_ovr.setMaximum(self.max_linear_velocity)
        self.w.slider_maxv_ovr.setValue(self.max_linear_velocity)
        self.w.slider_feed_ovr.setMaximum(INFO.MAX_FEED_OVERRIDE)
        self.w.slider_feed_ovr.setValue(100)
        self.w.slider_rapid_ovr.setMaximum(100)
        self.w.slider_rapid_ovr.setValue(100)
        self.w.slider_spindle_ovr.setMinimum(INFO.MIN_SPINDLE_OVERRIDE)
        self.w.slider_spindle_ovr.setMaximum(INFO.MAX_SPINDLE_OVERRIDE)
        self.w.slider_spindle_ovr.setValue(100)
        self.w.lbl_maxv_percent.setText("100 %")
        self.w.lbl_max_rapid.setText(str(self.max_linear_velocity))
        self.w.cmb_gcode_history.addItem("Файл не загружен")
        self.w.cmb_gcode_history.wheelEvent = lambda event: None
        #self.w.jogincrements_linear.wheelEvent = lambda event: None
        self.w.gcode_editor.hide()
        # clickable frames
        self.w.frame_cycle_start.mousePressEvent = self.btn_start_clicked
        self.w.MainTab.setCurrentIndex(TAB_MAIN)
        # запоминам вкладки
        self.save_tab_tool = self.w.MainTab.widget( TAB_TOOL )  # save it for later
        self.save_tab_offsets = self.w.MainTab.widget( TAB_OFFSETS )  # save it for later
        # Этой командой их можно будет востановить
        # self.w.MainTab.insertTab( TAB_TOOL, self.save_tab, 'Tab2 is here again' ) # restore
        # Удаляем вкладки не забываем что смщается индекс
        self.w.MainTab.removeTab(TAB_TOOL)
        self.w.MainTab.removeTab(TAB_OFFSETS-1)
        #self.w.MainTab.setTabEnabled(TAB_TOOL, False)
        #self.w.MainTab.setTabEnabled(TAB_OFFSETS, False)
        self.w.cam_menu.setCurrentIndex(1)

         # Установка максимального и минимального значения позиции
        self.stat.poll()
        for x, y, z in zip(self.axis_x_list, self.axis_y_list, self.axis_z_list):
            self.w[x].setMaximum(self.stat.axis[0]["max_position_limit"])
            self.w[y].setMaximum(self.stat.axis[1]["max_position_limit"])
            self.w[z].setMaximum(self.stat.axis[2]["max_position_limit"])

            self.w[x].setMinimum(self.stat.axis[0]["min_position_limit"])
            self.w[y].setMinimum(self.stat.axis[1]["min_position_limit"])
            self.w[z].setMinimum(self.stat.axis[2]["min_position_limit"])
        for a, b in zip(self.progressbar_pressure_a, self.progressbar_pressure_b):
            self.w[a].setMaximum(20) #2.0 bar
            self.w[b].setMaximum(20)
        self.w["progressBar_mixer"].setMaximum(100) #100%
        # Виджет управления моторами
        self.w.btn_feed_joint.hide()
        self.w.gcode_viewer.editor.setUtf8(True)
        self.w.gcode_editor.editor.setUtf8(True)
        #ищем панель инструментов в тоолбаре редактора кода  и скрываем 
        toolbar_list = self.w.gcode_editor.topMenu.findChildren(QtWidgets.QToolBar)
        toolBar = toolbar_list[0]
        #скрываем кнопки новый документ и октрыть
        toolBar.actions()[0].setVisible(False)
        toolBar.actions()[1].setVisible(False)
        self.w.btn_lighting.setVisible(False)

    def init_preferences(self):
        if not self.w.PREFS_:
            self.add_status(
                "КРИТИЧЕСКИЙ - файл настроек не найден, берутся значения по умолчанию")
            return
        #self.last_loaded_program = self.w.PREFS_.getpref('last_loaded_directory', None, str, 'BOOK_KEEPING')
        self.last_loaded_program = self.cur.execute("SELECT last_loaded_directory FROM BOOK_KEEPING").fetchall()[0][0]
        #self.last_loaded_program = self.w.PREFS_.getpref('last_loaded_file', None, str, 'BOOK_KEEPING')
        self.last_loaded_program = self.cur.execute("SELECT last_loaded_file FROM BOOK_KEEPING").fetchall()[0][0]
        #self.reload_tool = self.w.PREFS_.getpref('Tool to load', 0, int, 'CUSTOM_FORM_ENTRIES')
        self.reload_tool = self.cur.execute("SELECT Tool_to_load FROM CUSTOM_FORM_ENTRIES").fetchall()[0][0]
        ##self.w.DSBox_viscosity_a.setValue(self.w.PREFS_.getpref("viscosity_a", 5000.0, float, "Component_Properties"))
        ##self.w.DSBox_viscosity_b.setValue(self.w.PREFS_.getpref("viscosity_b", 10.0, float, "Component_Properties"))
        #self.w.DSBox_density_a.setValue(self.w.PREFS_.getpref("density_a", 1, float, "Component_Properties"))
        self.w.DSBox_density_a.setValue(self.cur.execute("SELECT density_a FROM Component_Properties").fetchall()[0][0])
        #self.w.DSBox_density_b.setValue(self.w.PREFS_.getpref("density_b", 1, float, "Component_Properties"))
        self.w.DSBox_density_b.setValue(self.cur.execute("SELECT density_b FROM Component_Properties").fetchall()[0][0])
        #self.w.SBox_mass_fraction_a.setValue(self.w.PREFS_.getpref("mass_fraction_a", 100, int, "Component_Properties"))
        self.w.SBox_mass_fraction_a.setValue(self.cur.execute("SELECT mass_fraction_a FROM Component_Properties").fetchall()[0][0])
        #self.w.SBox_mass_fraction_b.setValue(self.w.PREFS_.getpref("mass_fraction_b", 100, int, "Component_Properties"))
        self.w.SBox_mass_fraction_b.setValue(self.cur.execute("SELECT mass_fraction_b FROM Component_Properties").fetchall()[0][0])
        #self.w.DSBox_mixture_density.setValue(self.w.PREFS_.getpref("mixture_density", 0.25, float, "Component_Properties"))
        self.w.DSBox_mixture_density.setValue(self.cur.execute("SELECT mixture_density FROM Component_Properties").fetchall()[0][0])
        #self.w.DSBox_k.setValue(self.w.PREFS_.getpref("k", 5, float, "Component_Properties"))
        self.w.DSBox_k.setValue(self.cur.execute("SELECT k FROM Component_Properties").fetchall()[0][0])

        ##self.w.DSBox_pump_efficiency_a.setValue(self.w.PREFS_.getpref("pump_efficiency_a", 2.5, float, "Installation_Parameters"))
        ##self.w.DSBox_pump_efficiency_b.setValue(self.w.PREFS_.getpref("pump_efficiency_b", 2.5, float, "Installation_Parameters"))
        #self.w.SBox_saturation_time_a.setValue(self.w.PREFS_.getpref("saturation_time_a", 100, int, "Installation_Parameters"))
        self.w.SBox_saturation_time_a.setValue(self.cur.execute("SELECT saturation_time_a FROM Installation_Parameters").fetchall()[0][0])
        #self.w.SBox_saturation_time_b.setValue(self.w.PREFS_.getpref("saturation_time_b", 0, int, "Installation_Parameters"))
        self.w.SBox_saturation_time_b.setValue(self.cur.execute("SELECT saturation_time_b FROM Installation_Parameters").fetchall()[0][0])
        #self.w.SBox_stirrin_time_a.setValue(self.w.PREFS_.getpref("stirrin_time_a", 100, int, "Installation_Parameters"))
        self.w.SBox_stirrin_time_a.setValue(self.cur.execute("SELECT stirrin_time_a FROM Installation_Parameters").fetchall()[0][0])
        #self.w.SBox_stirrin_time_b.setValue(self.w.PREFS_.getpref("stirrin_time_b", 0, int, "Installation_Parameters"))
        self.w.SBox_stirrin_time_b.setValue(self.cur.execute("SELECT stirrin_time_b FROM Installation_Parameters").fetchall()[0][0])
        #self.w.SBox_recuperation_time_a.setValue(self.w.PREFS_.getpref("recuperation_time_a", 0, int, "Installation_Parameters"))
        self.w.SBox_recuperation_time_a.setValue(self.cur.execute("SELECT recuperation_time_a FROM Installation_Parameters").fetchall()[0][0])
        #self.w.SBox_recuperation_time_b.setValue(self.w.PREFS_.getpref("recuperation_time_b", 0, int, "Installation_Parameters"))
        self.w.SBox_recuperation_time_b.setValue(self.cur.execute("SELECT recuperation_time_b FROM Installation_Parameters").fetchall()[0][0])
        #self.w.SBox_waiting_time.setValue(self.w.PREFS_.getpref("waiting_time", 5, int, "Installation_Parameters"))
        self.w.SBox_waiting_time.setValue(self.cur.execute("SELECT waiting_time FROM Installation_Parameters").fetchall()[0][0])
        #self.w.SBox_reset_fill_time.setValue(self.w.PREFS_.getpref("reset_fill_time", 5, int, "Installation_Parameters"))
        self.w.SBox_reset_fill_time.setValue(self.cur.execute("SELECT reset_fill_time FROM Installation_Parameters").fetchall()[0][0])
        #self.w.SBox_apply_before_rinsing.setValue(self.w.PREFS_.getpref("apply_before_rinsing", 10, int, "Installation_Parameters"))
        self.w.SBox_apply_before_rinsing.setValue(self.cur.execute("SELECT apply_before_rinsing FROM Installation_Parameters").fetchall()[0][0])
        #self.w.chk_run_from_line.setChecked(self.w.PREFS_.getpref('Run from line', False, bool, 'CUSTOM_FORM_ENTRIES'))
        self.w.chk_run_from_line.setChecked(self.cur.execute("SELECT Run_from_line FROM CUSTOM_FORM_ENTRIES").fetchall()[0][0])

        #self.w.dsb_seal_width.setValue(self.w.PREFS_.getpref("dsb_seal_width", 10, float, "CAM"))
        self.w.dsb_seal_width.setValue(self.cur.execute("SELECT dsb_seal_width FROM CAM").fetchall()[0][0])
        ##self.w.dsb_sealing_height.setValue(self.w.PREFS_.getpref("w.dsb_sealing_height", 10, float, "CAM"))
        #self.w.dsb_diam_mm.setValue(self.w.PREFS_.getpref("dsb_diam_mm", 4, float, "CAM"))
        self.w.dsb_diam_mm.setValue(self.cur.execute("SELECT dsb_diam_mm FROM CAM").fetchall()[0][0])
        #self.w.dsb_work.setValue(self.w.PREFS_.getpref("dsb_work", 10, float, "CAM"))
        self.w.dsb_work.setValue(self.cur.execute("SELECT dsb_work FROM CAM").fetchall()[0][0])
        #self.w.dsb_save.setValue(self.w.PREFS_.getpref("dsb_save", 10, float, "CAM"))
        self.w.dsb_save.setValue(self.cur.execute("SELECT dsb_save FROM CAM").fetchall()[0][0])
        #self.w.dsb_overlap.setValue(self.w.PREFS_.getpref("dsb_overlap", 10, float, "CAM"))
        self.w.dsb_overlap.setValue(self.cur.execute("SELECT dsb_overlap FROM CAM").fetchall()[0][0])
        #self.w.dsb_start_length.setValue(self.w.PREFS_.getpref("dsb_start_length", 19, float, "CAM"))
        self.w.dsb_start_length.setValue(self.cur.execute("SELECT dsb_start_length FROM CAM").fetchall()[0][0])

        #self.w.dsb_x_axis_offset.setValue(self.w.PREFS_.getpref("dsb_x_axis_offset", 10, float, "CAM"))
        self.w.dsb_x_axis_offset.setValue(self.cur.execute("SELECT dsb_x_axis_offset FROM CAM").fetchall()[0][0])
        #self.w.dsb_y_axis_offset.setValue(self.w.PREFS_.getpref("dsb_y_axis_offset", 10, float, "CAM"))
        self.w.dsb_y_axis_offset.setValue(self.cur.execute("SELECT dsb_y_axis_offset FROM CAM").fetchall()[0][0])
        #self.w.dsb_length.setValue(self.w.PREFS_.getpref("dsb_length", 100, float, "CAM"))
        self.w.dsb_length.setValue(self.cur.execute("SELECT dsb_length FROM CAM").fetchall()[0][0])
        #self.w.dsb_width.setValue(self.w.PREFS_.getpref("dsb_width", 100, float, "CAM"))
        self.w.dsb_width.setValue(self.cur.execute("SELECT dsb_width FROM CAM").fetchall()[0][0])
        #self.w.dsb_circle_diam.setValue(self.w.PREFS_.getpref("dsb_circle_diam", 100, float, "CAM"))
        self.w.dsb_circle_diam.setValue(self.cur.execute("SELECT dsb_circle_diam FROM CAM").fetchall()[0][0])

        #self.w.dsb_step_x.setValue(self.w.PREFS_.getpref("dsb_step_x", 0, float, "CAM"))
        self.w.dsb_step_x.setValue(self.cur.execute("SELECT dsb_step_x FROM CAM").fetchall()[0][0])
        #self.w.dsb_step_y.setValue(self.w.PREFS_.getpref("dsb_step_y", 0, float, "CAM"))
        self.w.dsb_step_y.setValue(self.cur.execute("SELECT dsb_step_y FROM CAM").fetchall()[0][0])
        #self.w.dsb_radius_1.setValue(self.w.PREFS_.getpref("dsb_radius_1", 10, float, "CAM"))
        self.w.dsb_radius_1.setValue(self.cur.execute("SELECT dsb_radius_1 FROM CAM").fetchall()[0][0])
        #self.w.dsb_radius_2.setValue(self.w.PREFS_.getpref("dsb_radius_2", 10, float, "CAM"))
        self.w.dsb_radius_2.setValue(self.cur.execute("SELECT dsb_radius_2 FROM CAM").fetchall()[0][0])
        #self.w.dsb_radius_3.setValue(self.w.PREFS_.getpref("dsb_radius_3", 10, float, "CAM"))
        self.w.dsb_radius_3.setValue(self.cur.execute("SELECT dsb_radius_3 FROM CAM").fetchall()[0][0])
        #self.w.dsb_radius_4.setValue(self.w.PREFS_.getpref("dsb_radius_4", 10, float, "CAM"))
        self.w.dsb_radius_4.setValue(self.cur.execute("SELECT dsb_radius_4 FROM CAM").fetchall()[0][0])
        #self.w.sb_quantity_x.setValue(self.w.PREFS_.getpref("sb_quantity_x", 1, int, "CAM"))
        self.w.sb_quantity_x.setValue(self.cur.execute("SELECT sb_quantity_x FROM CAM").fetchall()[0][0])
        #self.w.sb_quantity_y.setValue(self.w.PREFS_.getpref("sb_quantity_y", 1, int, "CAM"))
        self.w.sb_quantity_y.setValue(self.cur.execute("SELECT sb_quantity_y FROM CAM").fetchall()[0][0])
        #self.w.sb_feed.setValue(self.w.PREFS_.getpref("sb_feed", 5000, int, "CAM"))
        self.w.sb_feed.setValue(self.cur.execute("SELECT sb_feed FROM CAM").fetchall()[0][0])
        #self.w.sb_speed.setValue(self.w.PREFS_.getpref("sb_speed", 1500, int, "CAM"))
        self.w.sb_speed.setValue(self.cur.execute("SELECT sb_speed FROM CAM").fetchall()[0][0])

        #self.w.test_mass_a.setValue(self.w.PREFS_.getpref("test_mass_a", 5.0, float, "last_test"))
        self.w.test_mass_a.setValue(self.cur.execute("SELECT test_mass_a FROM last_test").fetchall()[0][0])
        #self.w.test_mass_b.setValue(self.w.PREFS_.getpref("test_mass_b", 5.0, float, "last_test"))
        self.w.test_mass_b.setValue(self.cur.execute("SELECT test_mass_b FROM last_test").fetchall()[0][0])
        #self.w.test_mass_mix.setValue(self.w.PREFS_.getpref("test_mass_mix", 5.0, float, "last_test"))
        self.w.test_mass_mix.setValue(self.cur.execute("SELECT test_mass_mix FROM last_test").fetchall()[0][0])

        #self.w.DSBox_speed_a.setValue(self.w.PREFS_.getpref("speed_a", 1.0, float, "Installation_Parameters"))
        self.w.DSBox_speed_a.setValue(self.cur.execute("SELECT speed_a FROM Installation_Parameters").fetchall()[0][0])
        #self.w.DSBox_speed_b.setValue(self.w.PREFS_.getpref("speed_b", 1.0, float, "Installation_Parameters"))
        self.w.DSBox_speed_b.setValue(self.cur.execute("SELECT speed_b FROM Installation_Parameters").fetchall()[0][0])


        #self.w.dSbox_pos1_x.setValue(self.w.PREFS_.getpref("x", 10, float, "SAVE_POS1"))
        self.w.dSbox_pos1_x.setValue(self.cur.execute("SELECT x FROM SAVE_POS1").fetchall()[0][0])
        #self.w.dSbox_pos1_y.setValue(self.w.PREFS_.getpref("y", 10, float, "SAVE_POS1"))
        self.w.dSbox_pos1_y.setValue(self.cur.execute("SELECT y FROM SAVE_POS1").fetchall()[0][0])
        #self.w.dSbox_pos1_z.setValue(self.w.PREFS_.getpref("z", 10, float, "SAVE_POS1"))
        self.w.dSbox_pos1_z.setValue(self.cur.execute("SELECT z FROM SAVE_POS1").fetchall()[0][0])

        #self.w.dSbox_pos2_x.setValue(self.w.PREFS_.getpref("x", 10, float, "SAVE_POS2"))
        self.w.dSbox_pos2_x.setValue(self.cur.execute("SELECT x FROM SAVE_POS2").fetchall()[0][0])
        #self.w.dSbox_pos2_y.setValue(self.w.PREFS_.getpref("y", 10, float, "SAVE_POS2"))
        self.w.dSbox_pos2_y.setValue(self.cur.execute("SELECT y FROM SAVE_POS2").fetchall()[0][0])
        #self.w.dSbox_pos2_z.setValue(self.w.PREFS_.getpref("z", 10, float, "SAVE_POS2"))
        self.w.dSbox_pos2_z.setValue(self.cur.execute("SELECT z FROM SAVE_POS2").fetchall()[0][0])

        #if not self.w.PREFS_.getpref('saturation_a', False, bool, 'BUTTON_STATUS'):
        if self.cur.execute("SELECT saturation_a FROM BUTTON_STATUS").fetchall()[0][0] == '0':
            self.w.btn_saturation_a.hide()
        #if not self.w.PREFS_.getpref('mixing_a', False, bool, 'BUTTON_STATUS'):
        if self.cur.execute("SELECT mixing_a FROM BUTTON_STATUS").fetchall()[0][0] == '0':
            self.w.btn_mixing_a.hide()
        #if not self.w.PREFS_.getpref('recuperation_a', False, bool, 'BUTTON_STATUS'):
        if self.cur.execute("SELECT recuperation_a FROM BUTTON_STATUS").fetchall()[0][0] == '0':
            self.w.btn_recuperation_a.hide()
        #if not self.w.PREFS_.getpref('saturation_b', False, bool, 'BUTTON_STATUS'):
        #print(self.cur.execute("SELECT saturation_b FROM BUTTON_STATUS").fetchall()[0][0],'aaaaaaaaaaaaaaaaaaaaaaaaaaa')
        if self.cur.execute("SELECT saturation_b FROM BUTTON_STATUS").fetchall()[0][0] == '0':
            self.w.btn_saturation_b.hide()
        #if not self.w.PREFS_.getpref('mixing_b', False, bool, 'BUTTON_STATUS'):
        if self.cur.execute("SELECT mixing_b FROM BUTTON_STATUS").fetchall()[0][0] == '0':
            self.w.btn_mixing_b.hide()
        #if not self.w.PREFS_.getpref('recuperation_b', False, bool, 'BUTTON_STATUS'):
        if self.cur.execute("SELECT recuperation_b FROM BUTTON_STATUS").fetchall()[0][0] == '0':
            self.w.btn_recuperation_b.hide()
        self.set_hal_pin()
        self.set_pos_pin()

    def set_hal_pin(self):
        #density_a = self.w.PREFS_.getpref("density_a", 1, float, "Component_Properties")
        density_a = self.cur.execute("SELECT density_a FROM Component_Properties").fetchall()[0][0]
        #density_b = self.w.PREFS_.getpref("density_b", 1, float, "Component_Properties")
        density_b = self.cur.execute("SELECT density_b FROM Component_Properties").fetchall()[0][0]
        #mass_fraction_a = self.w.PREFS_.getpref("mass_fraction_a", 100, int, "Component_Properties")
        mass_fraction_a = self.cur.execute("SELECT mass_fraction_a FROM Component_Properties").fetchall()[0][0]
        #mass_fraction_b = self.w.PREFS_.getpref("mass_fraction_b", 100, int, "Component_Properties")
        mass_fraction_b = self.cur.execute("SELECT mass_fraction_b FROM Component_Properties").fetchall()[0][0]
        #k = self.w.PREFS_.getpref("k", 5, float, "Component_Properties")
        k = self.cur.execute("SELECT k FROM Component_Properties").fetchall()[0][0]
        #mixture_density = self.w.PREFS_.getpref("mixture_density", 0.25, float, "Component_Properties")
        mixture_density = self.cur.execute("SELECT mixture_density FROM Component_Properties").fetchall()[0][0]
        #saturation_time_a = self.w.PREFS_.getpref("saturation_time_a", 100, int, "Installation_Parameters")
        saturation_time_a = self.cur.execute("SELECT saturation_time_a FROM Installation_Parameters").fetchall()[0][0]
        #saturation_time_b = self.w.PREFS_.getpref("saturation_time_b", 0, int, "Installation_Parameters")
        saturation_time_b = self.cur.execute("SELECT saturation_time_b FROM Installation_Parameters").fetchall()[0][0]
        #mixing_time_a = self.w.PREFS_.getpref("stirrin_time_a", 100, int, "Installation_Parameters")
        mixing_time_a = self.cur.execute("SELECT stirrin_time_a FROM Installation_Parameters").fetchall()[0][0]
        #mixing_time_b = self.w.PREFS_.getpref("stirrin_time_b", 0, int, "Installation_Parameters")
        mixing_time_b = self.cur.execute("SELECT stirrin_time_b FROM Installation_Parameters").fetchall()[0][0]
        #recuperation_time_a = self.w.PREFS_.getpref("recuperation_time_a", 0, int, "Installation_Parameters")
        recuperation_time_a = self.cur.execute("SELECT recuperation_time_a FROM Installation_Parameters").fetchall()[0][0]
        #recuperation_time_b = self.w.PREFS_.getpref("recuperation_time_b", 0, int, "Installation_Parameters")
        recuperation_time_b = self.cur.execute("SELECT recuperation_time_b FROM Installation_Parameters").fetchall()[0][0]
        #waiting_time = self.w.PREFS_.getpref("waiting_time", 5, int, "Installation_Parameters")
        waiting_time = self.cur.execute("SELECT waiting_time FROM Installation_Parameters").fetchall()[0][0]
        #reset_fill_time = self.w.PREFS_.getpref("reset_fill_time", 5, int, "Installation_Parameters")
        reset_fill_time = self.cur.execute("SELECT reset_fill_time FROM Installation_Parameters").fetchall()[0][0]
        #apply_before_rinsing = self.w.PREFS_.getpref("apply_before_rinsing", 10, int, "Installation_Parameters")
        apply_before_rinsing = self.cur.execute("SELECT apply_before_rinsing FROM Installation_Parameters").fetchall()[0][0]
        print(apply_before_rinsing)
        #speed_a = self.w.PREFS_.getpref("speed_a", 1.0, float, "Installation_Parameters")
        speed_a = self.cur.execute("SELECT speed_a FROM Installation_Parameters").fetchall()[0][0]
        #speed_b = self.w.PREFS_.getpref("speed_b", 1.0, float, "Installation_Parameters")
        speed_b = self.cur.execute("SELECT speed_b FROM Installation_Parameters").fetchall()[0][0]

        #hal.set_p("gasketing.app.max-count", "{}".format(apply_before_rinsing))
        
        hal.set_p("gasketing.a.density", "{}".format(density_a))
        hal.set_p("gasketing.b.density", "{}".format(density_b))
        hal.set_p("gasketing.a.mass_fraction", "{}".format(mass_fraction_a))
        hal.set_p("gasketing.b.mass_fraction", "{}".format(mass_fraction_b))
        hal.set_p("gasketing.mixture.density", "{}".format(mixture_density))
        hal.set_p("gasketing.a.saturation.timer", "{}".format(saturation_time_a))
        hal.set_p("gasketing.b.saturation.timer", "{}".format(saturation_time_b))
        hal.set_p("gasketing.a.mixing.timer", "{}".format(mixing_time_a))
        hal.set_p("gasketing.b.mixing.timer", "{}".format(mixing_time_b))
        hal.set_p("gasketing.a.recovery.timer", "{}".format(recuperation_time_a))
        hal.set_p("gasketing.b.recovery.timer", "{}".format(recuperation_time_b))

        hal.set_p("gasketing.app.sleep-time", "{}".format(waiting_time))
        hal.set_p("gasketing.reset-comp.timer", "{}".format(reset_fill_time))
        hal.set_p("gasketing.app.max-count", "{}".format(int(apply_before_rinsing)))
        print(apply_before_rinsing)
        x = hal.get_value("gasketing.app.max-count")
        print(x)
        hal.set_p("gasketing.mixture.expansion-ratio", "{}".format(k))
        hal.set_p("gasketing.a.pump.speed-ratio", "{}".format(speed_a))
        hal.set_p("gasketing.b.pump.speed-ratio", "{}".format(speed_b))

    def set_pos_pin(self):
        #x = self.w.PREFS_.getpref("x", -2, float, "flushing")
        x = self.cur.execute("SELECT x FROM flushing").fetchall()[0][0]
        #y = self.w.PREFS_.getpref("y", 456, float, "flushing")
        y = self.cur.execute("SELECT y FROM flushing").fetchall()[0][0]
        #z = self.w.PREFS_.getpref("z", -130, float, "flushing")
        z = self.cur.execute("SELECT z FROM flushing").fetchall()[0][0]
        self.h["pos.flushing-x"] = x
        self.h["pos.flushing-y"] = y
        self.h["pos.flushing-z"] = z
        self.w.dSbox_flushing_x.setValue(x)
        self.w.dSbox_flushing_y.setValue(y)
        self.w.dSbox_flushing_z.setValue(z)
        
        #x = self.w.PREFS_.getpref("x", -2, float, "reset")
        x = self.cur.execute("SELECT x FROM reset").fetchall()[0][0]
        #y = self.w.PREFS_.getpref("y", 113, float, "reset")
        y = self.cur.execute("SELECT y FROM reset").fetchall()[0][0]
        #z = self.w.PREFS_.getpref("z", -130, float, "reset")
        z = self.cur.execute("SELECT z FROM reset").fetchall()[0][0]
        self.h["pos.reset-x"] = x
        self.h["pos.reset-y"] = y
        self.h["pos.reset-z"] = z
        self.w.dSbox_reset_x.setValue(x)
        self.w.dSbox_reset_y.setValue(y)
        self.w.dSbox_reset_z.setValue(z)

    
    
        

    def closing_func(self):
        print("0")
       
        self.cur.execute("UPDATE CAM set dsb_seal_width = {}".format(self.w.dsb_seal_width.value()))
        self.cur.execute("UPDATE CAM set dsb_x_axis_offset = {}".format(self.w.dsb_x_axis_offset.value()))
        #self.w.PREFS_.putpref('last_loaded_directory', os.path.dirname(self.last_loaded_program), str, 'BOOK_KEEPING')
        self.cur.execute("UPDATE BOOK_KEEPING set last_loaded_directory = '{}'".format(os.path.dirname(self.last_loaded_program)))
        self.conn.commit()
        print("1")
        
        #self.w.PREFS_.putpref('last_loaded_file', self.last_loaded_program, str, 'BOOK_KEEPING')
        self.cur.execute("UPDATE BOOK_KEEPING set last_loaded_file = '{}'".format(self.last_loaded_program))
        #self.w.PREFS_.putpref('Tool to load', STATUS.get_current_tool(), int, 'CUSTOM_FORM_ENTRIES')
        self.cur.execute("UPDATE CUSTOM_FORM_ENTRIES set Tool_to_load = {}".format(STATUS.get_current_tool()))
        #self.w.PREFS_.putpref('Run from line', self.w.chk_run_from_line.isChecked(bool,STATUS.get_current_tool))
        #self.cur.execute("UPDATE STATUS.get_current_tool set Run_from_line = {}".format(self.w.chk_run_from_line))
        #self.w.PREFS_.putpref("dsb_seal_width", self.w.dsb_seal_width.value(), float, "CAM")
        #print('qqqqqqqqqqqqqqqqqqq'self.w.dsb_seal_width)
        self.cur.execute("UPDATE CAM set dsb_seal_width = {}".format(self.w.dsb_seal_width.value()))
        #self.w.PREFS_.putpref("dsb_sealing_height", self.w.dsb_sealing_height.value(), float, "CAM")
        #self.cur.execute("UPDATE CAM set dsb_sealing_height = {}".format(self.w.dsb_sealing_height.value()))
        #self.w.PREFS_.putpref("dsb_save", self.w.dsb_save.value(), float, "CAM")
        
        print("1")
        self.cur.execute("UPDATE CAM set dsb_save = {}".format(self.w.dsb_save.value()))
        #self.w.PREFS_.putpref("dsb_work", self.w.dsb_work.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_work = {}".format(self.w.dsb_work.value()))
        #self.w.PREFS_.putpref("dsb_overlap", self.w.dsb_overlap.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_overlap = {}".format(self.w.dsb_overlap.value()))
        #self.w.PREFS_.putpref("dsb_start_length", self.w.dsb_start_length.value(), float, "CAM")
        self.cur.execute("UPDATE CAM  set dsb_start_length = {}".format(self.w.dsb_start_length.value()))
        #self.w.PREFS_.putpref("dsb_diam_mm", self.w.dsb_diam_mm.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_diam_mm  = {}".format(self.w.dsb_diam_mm.value()))
        #self.w.PREFS_.putpref("dsb_x_axis_offset", self.w.dsb_x_axis_offset.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_x_axis_offset = {}".format(self.w.dsb_x_axis_offset.value()))
        #self.w.PREFS_.putpref("dsb_y_axis_offset", self.w.dsb_y_axis_offset.value(), float, "CAM")
        self.cur.execute("UPDATE CAM  set dsb_y_axis_offset = {}".format(self.w.dsb_y_axis_offset.value()))
        #self.w.PREFS_.putpref("dsb_length", self.w.dsb_length.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_length = {}".format(self.w.dsb_length.value()))
        #self.w.PREFS_.putpref("dsb_circle_diam", self.w.dsb_circle_diam.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_circle_diam = {}".format(self.w.dsb_circle_diam.value()))
        #self.w.PREFS_.putpref("dsb_width", self.w.dsb_width.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_width = {}".format(self.w.dsb_width.value()))
        #self.w.PREFS_.putpref("dsb_step_x", self.w.dsb_step_x.valueself.w.dsb_width.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_step_x  = {}".format(self.w.dsb_step_x.value()))
        #self.w.PREFS_.putpref("dsb_step_y", self.w.dsb_step_y.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_step_y  = {}".format(self.w.dsb_step_y.value()))
        #self.w.PREFS_.putpref("dsb_radius_1", self.w.dsb_radius_1.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_radius_1 = {}".format(self.w.dsb_radius_1.value()))
        #self.w.PREFS_.putpref("dsb_radius_2", self.w.dsb_radius_1.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_radius_2  = {}".format(self.w.dsb_radius_2.value()))
        #self.w.PREFS_.putpref("dsb_radius_3", self.w.dsb_radius_3.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_radius_3  = {}".format( self.w.dsb_radius_3.value()))
        #self.w.PREFS_.putpref("dsb_radius_4", self.w.dsb_radius_4.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_radius_4 = {}".format(self.w.dsb_radius_4.value()))
        #self.w.PREFS_.putpref("sb_quantity_x", self.w.sb_quantity_x.value(), int, "CAM")
        self.cur.execute("UPDATE CAM set sb_quantity_x  = {}".format(self.w.sb_quantity_x.value()))
        #self.w.PREFS_.putpref("sb_quantity_y", self.w.sb_quantity_y.value(), int, "CAM")
        self.cur.execute("UPDATE CAM set sb_quantity_y  = {}".format(self.w.sb_quantity_y.value()))
        #self.w.PREFS_.putpref("sb_feed", self.w.sb_feed.value(), int, "CAM")
        self.cur.execute("UPDATE CAM set sb_feed  = {}".format(self.w.sb_feed.value()))
        #self.w.PREFS_.putpref("sb_speed", self.w.sb_speed.value(), int, "CAM")
        self.cur.execute("UPDATE CAM set sb_speed = {}".format(self.w.sb_speed.value()))
        self.conn.commit()
    
    
    
    def closing_cleanup__(self):
        self.closing_func()
    
    def processed_key_event__(self, receiver, event, is_pressed, key, code, shift, cntrl):
        # when typing in MDI, we don't want keybinding to call functions
        # so we catch and process the events directly.
        # We do want ESC, F1 and F2 to call keybinding functions though
        if code not in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_F1, QtCore.Qt.Key_F2,
                        QtCore.Qt.Key_F3, QtCore.Qt.Key_F5, QtCore.Qt.Key_F5):
            # search for the top widget of whatever widget received the event
            # then check if it's one we want the keypress events to go to
            flag = False
            receiver2 = receiver
            while receiver2 is not None and not flag:
                if isinstance(receiver2, QtWidgets.QDialog):
                    flag = True
                    break
                if isinstance(receiver2, QtWidgets.QLineEdit):
                    flag = True
                    break
                if isinstance(receiver2, QtWidgets.QDoubleSpinBox):
                    flag = True
                    break
                if isinstance(receiver2, QtWidgets.QSpinBox):
                    flag = True
                    break
                if isinstance(receiver2, MDI_WIDGET):
                    flag = True
                    break
                if isinstance(receiver2, GCODE):
                    flag = True
                    break
                if isinstance(receiver2, TOOL_TABLE):
                    flag = True
                    break
                if isinstance(receiver2, OFFSET_VIEW):
                    flag = True
                    break
                receiver2 = receiver2.parent()
            if flag:
                if isinstance(receiver2, GCODE):
                    # if in manual do our keybindings - otherwise
                    # send events to gcode widget
                    if STATUS.is_man_mode() == False:
                        if is_pressed:
                            receiver.keyPressEvent(event)
                            event.accept()
                        return True
                elif is_pressed:
                    receiver.keyPressEvent(event)
                    event.accept()
                    return True
                else:
                    event.accept()
                    return True
        if event.isAutoRepeat():
            return True
        try:
            KEYBIND.call(self, event, is_pressed, shift, cntrl)
            event.accept()
            return True
        except NameError as e:
            if is_pressed:
                LOG.debug('Exception in KEYBINDING: {}'.format(e))
                self.add_status('Exception in KEYBINDING: {}'.format(e))
        except Exception as e:
            if is_pressed:
                LOG.debug('Exception in KEYBINDING:', exc_info=e)
                print('Error in, or no function for: %s in handler file for-%s' %
                      (KEYBIND.convert(event), key))
        event.accept()
        return True
    ########################
    # callbacks from STATUS #
    ########################
    def user_system_changed(self, obj, data):
        print('CCCCCCHHHHHHHHHHAAAAAAAAAANNNNNN', data)
        sys_ch = self.system_list[int(data) - 1]
        self.w.offset_table.selectRow(int(data) + 3)
        self.w.actionbutton_rel.setText(sys_ch)
        self.user_system = int(data)
            
    def update_runtimer(self):
        """ Переодические процессы"""
        if self.is_initialized:
            if time.time() - self.init_time < 2:
                self.h["reset"] = True
            else:
                self.h["reset"] = False
                self.is_initialized = False
        # проверка необходимости промвки
        if STATUS.is_on_and_idle() and STATUS.is_all_homed():
            if self.h["flushing.is-count"]:
                ACTION.CALL_MDI("M403 ")
                self.add_status("промывка по причине привышения количества деталей")
            if self.h["flushing.is-time"]:
                ACTION.CALL_MDI("M403 ")
                self.add_status("промывка по причине привышения времени простоя")
        #apply_before_rinsing = self.w.PREFS_.getpref("apply_before_rinsing", 10, int, "Installation_Parameters")
        apply_before_rinsing = self.cur.execute("SELECT apply_before_rinsing FROM Installation_Parameters").fetchall()[0][0]
        #apply_before_rinsing = apply_before_rinsing
        app_l = apply_before_rinsing - self.h["app.count"]
        text_html = """
            <html><head/><body>
            <p align="justify"><span style=" font-size:14pt;">Осталось нанести до промывки {} из {}</span></p>
            <p align="justify"><span style=" font-size:14pt;">До промывки {:3.4f} сек</span></p>
            </body></html>
            """.format(app_l, apply_before_rinsing, self.h["flushing.time-last"])
        self.w.rp_gasting.setText(text_html)

        # проверка необходимости рециркуляции Компонента Б
        if STATUS.is_on_and_idle():
            self.h["b.recovery.timer-out-hour"] = (time.time()-self.start_time_pump_b)/SECOND_TO_HOURS
            if self.h["b.recovery.timer-out-hour"] > self.h["b.recovery.timer-sleep-hour"]:
                recuperation_time_b = self.h["b.recovery.timer-minutes"]*60
                hal.set_p("gasketing.b.recovery.timer", "{}".format(recuperation_time_b))
                hal.set_p("gasketing.b.recovery.on", "1")
        if self.w.chk_run_from_line.isChecked():
            self.w.lbl_start_line.setEnabled(True)
            
        else:
            self.w.lbl_start_line.setEnabled(False)
            self.w.lbl_start_line.setText("1")
        #if STATUS.is_auto_running():
        #    self.widget_management_enable(self.is_app, False)
        #Установка панели меню
        if self.w.cam_menu.currentIndex() == 0:
            # круг 
            self.widget_management_show(self.cam_elemen, False)
            self.widget_management_show(["dsb_circle_diam", "label_61"], True)

        if self.w.cam_menu.currentIndex() == 1:
            # прямоугольник 
            self.widget_management_show(self.cam_elemen, True)
            self.widget_management_show(["dsb_circle_diam", "label_61"], False)

        if self.h["cycle_simulation"]:
            self.w.cycle_simulation.setStyleSheet(self.set_color_btn(True))
        else:
            self.w.cycle_simulation.setStyleSheet(self.set_color_btn(False))
        if self.h["btn_lighting"]:
            self.w.btn_lighting.setStyleSheet(self.set_color_btn(True))
        else:
            self.w.btn_lighting.setStyleSheet(self.set_color_btn(False))
        #Проверка не нужно-ли показать скрытые параметры
        self.set_mode()


    def file_loaded(self, obj, filename):
        if filename is not None:
            self.add_status("Загруженный файл {}".format(filename))
            self.w.progressBar.setValue(0)
            self.last_loaded_program = filename
        else:
            self.add_status("Имя файла недействительно")
    def percent_loaded_changed(self, fraction):
        if fraction < 0:
            self.w.progressBar.setValue(0)
            self.w.progressBar.setFormat('Прогресс')
        else:
            self.w.progressBar.setValue(fraction)
            self.w.progressBar.setFormat('Выполненно: {}%'.format(fraction))
    def percent_completed_changed(self, fraction):
        self.w.progressBar.setValue(fraction)
        if fraction < 0:
            self.w.progressBar.setValue(0)
            self.w.progressBar.setFormat('Progress')
        else:
            self.w.progressBar.setFormat('Completed: {}%'.format(fraction))
    def homed(self, obj, joint):
        i = int(joint)
        axis = INFO.GET_NAME_FROM_JOINT.get(i).lower()
        try:
            self.w["dro_axis_{}".format(axis)].setProperty('homed', True)
            self.w["dro_axis_{}".format(axis)].setStyle(self.w["dro_axis_{}".format(axis)].style())
        except:
            pass
    def all_homed(self, obj):
        self.home_all = True
        self.h['homme-all'] = True
        self.set_mode()
        self.w.btn_feed_axis.setEnabled(True)
        for widget in self.onoff_list:
            self.w[widget].setEnabled(True)
        #скрываем кнопки шагом и скоростью перемещения
        for widget in self.is_homed_list:
            self.w[widget].setEnabled(True)
        if self.first_turnon is True:
            self.first_turnon = False
            command = "M61 Q{}".format(self.reload_tool)
            ACTION.CALL_MDI(command)
            if self.last_loaded_program is not None:
                if os.path.isfile(self.last_loaded_program):
                    self.w.cmb_gcode_history.addItem(self.last_loaded_program)
                    self.w.cmb_gcode_history.setCurrentIndex(self.w.cmb_gcode_history.count() - 1)
                    ACTION.OPEN_PROGRAM(self.last_loaded_program)
                    #self.w.manual_mode_button.setChecked(True)
    
        if self.user_system == 0:
            ACTION.SET_USER_SYSTEM('55')
            ACTION.SET_USER_SYSTEM('54')
            print("ZAMENA")
    def not_all_homed(self, obj, list):
        self.home_all = False
        self.h['homme-all'] = False
        self.set_mode()
        self.w.btn_feed_axis.setEnabled(False)
        for widget in self.is_homed_list:
            self.w[widget].setEnabled(False)
        for widget in self.onoff_list:
            self.w[widget].setEnabled(False)
        for i in INFO.AVAILABLE_JOINTS:
            if str(i) in list:
                axis = INFO.GET_NAME_FROM_JOINT.get(i).lower()
                try:
                    self.w["dro_axis_{}".format(axis)].setProperty('homed', False)
                    self.w["dro_axis_{}".format(axis)].setStyle(self.w["dro_axis_{}".format(axis)].style())
                except:
                    pass
    def enable_onoff(self, state):
        self.w.power.setStyleSheet(self.set_color_estop(state))
        if state:
            self.add_status("Машина включение")
        else:
            self.add_status("Машина выключение")
            #скрываем кнопки шагом и скоростью перемещения
            for widget in self.is_homed_list:
                self.w[widget].setEnabled(False)

        if self.home_all:
            for widget in self.onoff_list:
                self.w[widget].setEnabled(state)
            for widget in self.is_homed_list:
                self.w[widget].setEnabled(state)                
        self.set_mode()
    def state_estop(self, state):
        self.w.e_stop.setStyleSheet(self.set_color_estop(state))
        if state:
            self.add_status("ESTOP RESET")
            self.w.e_stop.setText("ESTOP RESET")
        else:
            self.add_status("ESTOP SET")
            self.w.e_stop.setText("ESTOP SET")

    #######################
    # callbacks from form #
    #######################
    #calback hal
    def pressure_changed(self, data):
        # this calculation assumes the voltage is line to neutral
        # and that the synchronous motor spindle has a power factor of 0.9
        for a, b in zip(self.progressbar_pressure_a, self.progressbar_pressure_b):
            self.w[a].setValue(self.h['pressure-a']*1)
            self.w[b].setValue(self.h['pressure-b']*1)
            self.w[a].setFormat('{:.2f} бар'.format(self.h['pressure-a']*1))
            self.w[b].setFormat('{:.2f} бар'.format(self.h['pressure-b']*1))
    def mixer_changed(self, data):
        # this calculation assumes the voltage is line to neutral
        # and that the synchronous motor spindle has a power factor of 0.9
        self.w.progressBar_mixer.setValue(self.h['mixer-tor']*1)
        self.w.progressBar_mixer.setFormat('{:.2f} %'.format(self.h['mixer-tor']*1))
    def pin_test_component_a(self, pin):
         # кнопка подачи компонента  A
        if pin:
            # если процесс тестирования комп. А. то отключаем все остальные кнопки
            self.widget_management_enable(self.is_test_a, False)
            self.add_status("Начат процесс тестирования компонента А")
        else:
            # если процесс тестирования  комп. А. завершен,
            # то включаем все остальные кнопки
            self.widget_management_enable(self.is_test_a, True)
            self.add_status("Процесс тестирования компонента А завершен")

    def pin_test_component_b(self, pin):
         # кнопка подачи компонента  A
        if pin:
            # если процесс тестирования комп. Б. то отключаем все остальные кнопки
            self.widget_management_enable(self.is_test_b, False)
            self.add_status("Начат процесс тестирования компонента Б")
        else:
            # если процесс тестирования  комп. Б. завершен,
            # то включаем все остальные кнопки
            self.widget_management_enable(self.is_test_b, True)
            self.add_status("Процесс тестирования компонента Б завершен")

    def pin_test_component_mix(self, pin):
         # кнопка подачи компонента  A
        if pin:
            # если процесс тестирования смеси то отключаем все остальные кнопки
            self.widget_management_enable(self.is_test_mix, False)
            self.add_status("Начат процесс тестирования готовой смеси")
        else:
            # если процесс тестирования  смеси завершен,
            # то включаем все остальные кнопки
            self.widget_management_enable(self.is_test_mix, True)
            self.add_status("Процесс  тестирования готовой смеси завершен")

    def pin_saturation_a(self, status):
        # кнопка насащеия компонента А
        self.w.btn_saturation_a.setStyleSheet(self.set_color_btn(status))
        if status:
            # если процесс насыщения идет то меняем статутс кнопки
            self.widget_management_enable(self.is_saturation_a, False)
            self.add_status("Начат процесс насыщения компонента А")
        else:
            self.widget_management_enable(self.is_saturation_a, True)
            self.add_status("Процесс  насыщения компонента А завершен")

    def pin_mixing_a(self, status):
        # кнопка перемешивания компонента А
        self.w.btn_mixing_a.setStyleSheet(self.set_color_btn(status))
        if status:
            self.widget_management_enable(self.is_mixing_a, False)
            self.add_status("Начат процесс перемешивания компонента А")
        elif status is False and self.h['a.saturation-status']:
            self.add_status("Процесс  перемешивания  компонента А завершен")
        else:
            self.widget_management_enable(self.is_mixing_a, True)
            self.add_status("Процесс  перемешивания  компонента А завершен" )

    def pin_recovery_a(self, status):
        # кнопка рециркуляции компонента А
        self.w.btn_recuperation_a.setStyleSheet(self.set_color_btn(status))
        if status:
            self.widget_management_enable(self.is_recuperation_a, False)
            self.add_status("Начат процесс рециркуляции компонента А")
        else:
            self.widget_management_enable(self.is_recuperation_a, True)
            self.add_status("Процесс  рециркуляции компонента А завершен")

    def pin_saturation_b(self, status):
        # кнопка насыщения компонента B
        self.w.btn_saturation_b.setStyleSheet(self.set_color_btn(status))
        if status:
            self.add_status("Начат процесс насыщения компонента Б")
            self.widget_management_enable(self.is_saturation_b, False)
        else:
            self.widget_management_enable(self.is_saturation_b, True)
            self.add_status("Процесс  насыщения компонента Б завершен")


    def pin_mixing_b(self, status):
        # кнопка перемешивания компонента B
        self.w.btn_mixing_b.setStyleSheet(self.set_color_btn(status))
        if status:
            self.widget_management_enable(self.is_mixing_b, False)
            self.add_status("Начат процесс перемешивания компонента Б")
        else:
            self.widget_management_enable(self.is_mixing_b, True)
            self.add_status("Процесс  перемешивания  компонента Б завершен" )

    def pin_recovery_b(self, status):
        # кнопка рециркуляции компонента B
        self.w.btn_recuperation_b.setStyleSheet(self.set_color_btn(status))
        if status:
            self.widget_management_enable(self.is_recuperation_b, False)
            self.add_status("Начат процесс рециркуляции компонента Б")
        else:
            self.widget_management_enable(self.is_recuperation_b, True)
            self.add_status("Процесс  рециркуляции компонента Б завершен")

    def pin_flushing(self, status):
        # кнопка промывки
        self.w.btn_washed.setStyleSheet(self.set_color_btn(status))
        if status:
            self.widget_management_enable(self.is_flushing, False)
            self.add_status("Начало цикла промывки")
        else:
            self.widget_management_enable(self.is_flushing, True)
            self.add_status("Промывка завершена")

    def pin_reset_components(self, status):
        # кнопка сброса
        self.w.btn_reset_components.setStyleSheet(self.set_color_btn(status))
        if status:
            self.widget_management_enable(self.is_reset_components, False)
            self.add_status("Начало цикла сброса компонентов")
        else:
            self.widget_management_enable(self.is_reset_components, True)
            self.add_status("Сброс компонентов завершен")

    def pin_app(self, status):
        # кнопка нанесения
        if status:
            self.widget_management_enable(self.is_app, False)
            self.add_status("Начало цикла нанесения")
        else:
            self.widget_management_enable(self.is_app, True)
            self.add_status("Окончание цикла нанесения")

    def pin_min_a(self, status):
        # кнопка нанесения
        if status:
            self.add_status("В баке осталось минимальное кол-во компонента А")
            info = '<b>В баке осталось минимальное кол-во компонента А <\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_MIN_A', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)

    def pin_min_b(self, status):
        # кнопка нанесения
        if status:
            self.add_status("В баке осталось минимальное кол-во компонента Б")
            info = '<b>В баке осталось минимальное кол-во компонента Б <\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_MIN_B', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)
    def pin_min_solvent(self, status):
        # кнопка нанесения
        if status:
            self.add_status("В баке осталось минимальное кол-во растворителя")
            info = '<b>В баке осталось минимальное кол-во растворителя <\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_MIN_SOLVENT', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)
    def pin_pressure_a(self, data):
        # кнопка нанесения
        if self.h['a.pressure.is-max']:
            self.add_status("Было превышено давление компонента А. Подача компонетов завершена")
            info = '<b>Было превышено давление компонента А. Подача компонетов завершена<\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_pressure_A', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)
    def pin_pressure_b(self, data):
        # кнопка нанесения
        if self.h['b.pressure.is-max']:
            self.add_status("Было превышено давление компонента Б. Подача компонетов завершена")
            info = '<b>Было превышено давление компонента Б. Подача компонетов завершена <\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_pressure_B', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)
    def pin_rele_motor(self, data):
        # кнопка нанесения
        if self.h['rele_motor']:
            self.add_status("Сработала защита двигателя миксера компонента")
            info = '<b>Сработала защита двигателя миксера компонента А. <\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_rele_motor', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)
    def pin_servo_error(self, data):
        # кнопка нанесения
        if self.h['servo_error']:
            self.add_status("На одном из сервоприводов возникла ошибка")
            info = '<b>На одном из сервоприводов возникла ошибка. Подробности на вкладке STATUS. <\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_servo_error', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)
    def pin_rele_air(self, data):
        # кнопка нанесения
        if self.h['rele_air']:
            self.add_status("Отсуствует Воздух в системе")
            info = '<b>Отсуствует Воздух в системе. <\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_rele_air', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)
    def pin_rele_faz(self, data):
        # кнопка нанесения
        if self.h['rele_faz']:
            self.add_status("Проверьте питание. Сработало реле контроля фаз")
            info = '<b> Проверьте питание. Сработало реле контроля фаз <\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_rele_faz', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)
    def pin_start(self, status):
        """Пин для запуска программы"""
        if status:
            self.start_program()

    def pin_go_to_pos1(self, state):
        if state and STATUS.is_on_and_idle() and STATUS.is_all_homed():
            self.go_to_pos1()

    def pin_motor_on_a(self, status):
        """Сохраняем последние время включение насоса копмпонента А"""
        if status:
            return
        else:
            self.start_time_pump_a = time.time()
            return

    def pin_motor_on_b(self, status):
        """Сохраняем последние время включение насоса копмпонента Б"""

        if status:
            return
        else:
            self.start_time_pump_b = time.time()
            return

    # TAB MAIN
    def cmb_gcode_history_clicked(self):
        if self.w.cmb_gcode_history.currentIndex() == 0:
            return
        filename = self.w.cmb_gcode_history.currentText().encode('utf-8')
        if filename == self.last_loaded_program:
            self.add_status("Выбранная программа уже загружена")
        else:
            ACTION.OPEN_PROGRAM(filename)
    # TAB FILE
    def btn_load_file_clicked(self):
        fname = self.w.filemanager.getCurrentSelected()
        if fname[1] is True:
            self.load_code(fname[0])
    def btn_copy_file_clicked(self):
        if self.w.sender() == self.w.btn_copy_right:
            source = self.w.filemanager_usb.getCurrentSelected()
            target = self.w.filemanager.getCurrentSelected()
        elif self.w.sender() == self.w.btn_copy_left:
            source = self.w.filemanager.getCurrentSelected()
            target = self.w.filemanager_usb.getCurrentSelected()
        else:
            return
        if source[1] is False:
            self.add_status("Указанный источник не является файлом")
            return
        if target[1] is True:
            destination = os.path.join(os.path.dirname(
                target[0]), os.path.basename(source[0]))
        else:
            destination = os.path.join(target[0], os.path.basename(source[0]))
        try:
            copyfile(source[0], destination)
            self.add_status("Скопированный файл из {} b {}".format(
                source[0], destination))
        except Exception as e:
            self.add_status("Невозможно скопировать файл. %s" % e)
    def btn_delete_clicked(self):
        if not STATUS.is_on_and_idle():
            return
        fname = self.w.filemanager.getCurrentSelected()
        full_filename = fname[0]
        self.delete_file = full_filename
        if os.path.isdir(self.delete_file):
            delete_type = "папку"
        else:
            delete_type = "файл"
        delete_name = os.path.basename(self.delete_file)
        info = '<b> Вы Действительно хотите удлаить {} {} <\b>'.format(delete_type, delete_name)
        mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_delete_file', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'YESNO'}
        ACTION.CALL_DIALOG(mess)

    def btn_gcode_edit_clicked(self, state):
        if not STATUS.is_on_and_idle():
            return
        fname = self.w.filemanager.getCurrentSelected()
        if fname[1] is True:
            full_filename = fname[0]
        else:
            full_filename=self.w.gcode_editor.editor._last_filename
        file_name = os.path.basename(full_filename)
        if state:
            self.w.filemanager.hide()
            self.w.filemanager_usb.hide()
            self.w.widget_file_copy.hide()
            self.w.gcode_editor.show()
            self.w.gcode_editor.editMode()
            toolBar = self.w.gcode_editor.topMenu.findChildren(QtWidgets.QToolBar)[0]
            Label = toolBar.findChildren(QtWidgets.QLabel)[0]
            text_label = '<html><head/><body><p><span style=" font-size:20pt; font-weight:600;">{}</span></p></body></html>'.format(file_name)
            Label.setText(text_label)
        else:
            self.w.filemanager.show()
            self.w.filemanager_usb.show()
            self.w.widget_file_copy.show()
            self.w.gcode_editor.hide()
            self.w.gcode_editor.readOnlyMode()
 
    # TAB TOOL
    def btn_m61_clicked(self):
        checked = self.w.tooloffsetview.get_checked_list()
        if len(checked) > 1:
            self.add_status("Выберите только 1 инструмент для загрузки")
        elif checked:
            self.add_status("Загруженный инструмент {}".format(checked[0]))
            ACTION.CALL_MDI("M61 Q{}".format(checked[0]))
        else:
            self.add_status("Инструмент не выбран")

    # TAB OFFSETS
    def offset_g5x_clicked(self):
        for i in self.offset_button:
            if self.w[i].isChecked():
                if self.w[i].text() == "G54":
                    ACTION.SET_USER_SYSTEM('54')
                elif self.w[i].text() == "G55":
                    ACTION.SET_USER_SYSTEM('55')
                else:
                    ACTION.SET_USER_SYSTEM(self.w[i].text())
                self.add_status('Активированна система координат ' + self.w[i].text())
    def _a_from_j(self, axis):
        if STATUS.is_joint_mode():
            return None, None
        if axis == '':
            axis = STATUS.get_selected_axis()
        j = "XYZABCUVW"
        try:
            jnum = j.find(axis)
        except:
            return None, None
        p, r, d = STATUS.get_position()
        if not INFO.MACHINE_IS_METRIC:
            r = INFO.convert_units_9(r)
        return axis, r[jnum]
    def offset_set_x_clicked(self):
        axis, now = self._a_from_j("X")
        num = self.w.offset_newvalue_x.value()
        ACTION.SET_AXIS_ORIGIN(axis, num)
        self.add_status("Cмещение по оси X {}".format(num))
    def offset_set_y_clicked(self):
        axis, now = self._a_from_j("Y")
        num = self.w.offset_newvalue_y.value()
        ACTION.SET_AXIS_ORIGIN(axis, num)
        self.add_status("Cмещение по оси Y {}".format(num))
    def offset_set_z_clicked(self):
        axis, linucncnow = self._a_from_j("Z")
        num = self.w.offset_newvalue_z.value()
        ACTION.SET_AXIS_ORIGIN(axis, num)
        self.add_status("Cмещение по оси Z {}".format(num))
    def offset_x2_clicked(self):
        axis, now = self._a_from_j("X")
        x = now/2.0
        ACTION.SET_AXIS_ORIGIN(axis, x)
        self.add_status("Cмещение по оси X {}".format(x))
    def offset_y2_clicked(self):
        axis, now = self._a_from_j("Y")
        x = now/2.0
        ACTION.SET_AXIS_ORIGIN(axis, x)
        self.add_status("Cмещение по оси Y {}".format(x))
    def offset_z2_clicked(self):
        axis, now = self._a_from_j("Z")
        x = now/2.0
        ACTION.SET_AXIS_ORIGIN(axis, x)
        self.add_status("Cмещение по оси Z {}".format(x))

    # TAB CAM
    def btn_cam_create_square_clicked(self):
        seal_width = self.w.dsb_seal_width.value()
        tool_diam = self.w.dsb_diam_mm.value()
        x_axis_offset = self.w.dsb_x_axis_offset.value()
        y_axis_offset = self.w.dsb_y_axis_offset.value()
        width = self.w.dsb_length.value()
        length = self.w.dsb_width.value()
        circle_diameter = self.w.dsb_circle_diam.value()
        STEP_X = self.w.dsb_step_x.value()
        STEP_Y = self.w.dsb_step_y.value()
        radius_1 = self.w.dsb_radius_1.value()
        radius_2 = self.w.dsb_radius_2.value()
        radius_3 = self.w.dsb_radius_3.value()
        radius_4 = self.w.dsb_radius_4.value()
        quantity_x = self.w.sb_quantity_x.value()
        quantity_y = self.w.sb_quantity_y.value()
        z_save = self.w.dsb_save.value()
        z_work = self.w.dsb_work.value()
        overlap_length = self.w.dsb_overlap.value()
        start_length = self.w.dsb_start_length.value()

        feed = self.w.sb_feed.value()
        speed = self.w.sb_speed.value()
        tool_number = self.w.sb_tool_number.value()
        file_name = self.w.le_file_name.text().encode('utf-8')+".ngc"

        self.gcode_cam.set_parameter(seal_width, tool_diam,
                                     x_axis_offset, y_axis_offset,
                                     width, length,
                                     STEP_X, STEP_Y,
                                     radius_1, radius_2,
                                     radius_3, radius_4,
                                     quantity_x, quantity_y,
                                     feed, speed,
                                     tool_number,
                                     z_save, z_work, 
                                     overlap_length, start_length,
                                     circle_diameter)

        self.gcode_cam.file_name = file_name
        self.gcode_cam.file_path = "./gcode"
        #self.gcode_cam.generator_gcode(1.2)
        type_cam = self.w.cam_menu.currentIndex()
        full_name = self.gcode_cam.generator_gcode(type_cam)
        full_name = os.path.abspath(full_name)

        self.add_status("Генерация кода завершена файл сохранен в {}".format(full_name))
        
        
        print("0")
       
        self.cur.execute("UPDATE CAM set dsb_seal_width = {}".format(self.w.dsb_seal_width.value()))
        self.cur.execute("UPDATE CAM set dsb_x_axis_offset = {}".format(self.w.dsb_x_axis_offset.value()))
        #self.w.PREFS_.putpref('last_loaded_directory', os.path.dirname(self.last_loaded_program), str, 'BOOK_KEEPING')
        self.cur.execute("UPDATE BOOK_KEEPING set last_loaded_directory = '{}'".format(os.path.dirname(self.last_loaded_program)))
        self.conn.commit()
        print("1")
        
        #self.w.PREFS_.putpref('last_loaded_file', self.last_loaded_program, str, 'BOOK_KEEPING')
        self.cur.execute("UPDATE BOOK_KEEPING set last_loaded_file = '{}'".format(self.last_loaded_program))
        #self.w.PREFS_.putpref('Tool to load', STATUS.get_current_tool(), int, 'CUSTOM_FORM_ENTRIES')
        self.cur.execute("UPDATE CUSTOM_FORM_ENTRIES set Tool_to_load = {}".format(STATUS.get_current_tool()))
        #self.w.PREFS_.putpref('Run from line', self.w.chk_run_from_line.isChecked(bool,STATUS.get_current_tool))
        #self.cur.execute("UPDATE STATUS.get_current_tool set Run_from_line = {}".format(self.w.chk_run_from_line))
        #self.w.PREFS_.putpref("dsb_seal_width", self.w.dsb_seal_width.value(), float, "CAM")
        #print('qqqqqqqqqqqqqqqqqqq'self.w.dsb_seal_width)
        self.cur.execute("UPDATE CAM set dsb_seal_width = {}".format(self.w.dsb_seal_width.value()))
        #self.w.PREFS_.putpref("dsb_sealing_height", self.w.dsb_sealing_height.value(), float, "CAM")
        #self.cur.execute("UPDATE CAM set dsb_sealing_height = {}".format(self.w.dsb_sealing_height.value()))
        #self.w.PREFS_.putpref("dsb_save", self.w.dsb_save.value(), float, "CAM")
        
        print("1")
        self.cur.execute("UPDATE CAM set dsb_save = {}".format(self.w.dsb_save.value()))
        #self.w.PREFS_.putpref("dsb_work", self.w.dsb_work.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_work = {}".format(self.w.dsb_work.value()))
        #self.w.PREFS_.putpref("dsb_overlap", self.w.dsb_overlap.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_overlap = {}".format(self.w.dsb_overlap.value()))
        #self.w.PREFS_.putpref("dsb_start_length", self.w.dsb_start_length.value(), float, "CAM")
        self.cur.execute("UPDATE CAM  set dsb_start_length = {}".format(self.w.dsb_start_length.value()))
        #self.w.PREFS_.putpref("dsb_diam_mm", self.w.dsb_diam_mm.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_diam_mm  = {}".format(self.w.dsb_diam_mm.value()))
        #self.w.PREFS_.putpref("dsb_x_axis_offset", self.w.dsb_x_axis_offset.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_x_axis_offset = {}".format(self.w.dsb_x_axis_offset.value()))
        #self.w.PREFS_.putpref("dsb_y_axis_offset", self.w.dsb_y_axis_offset.value(), float, "CAM")
        self.cur.execute("UPDATE CAM  set dsb_y_axis_offset = {}".format(self.w.dsb_y_axis_offset.value()))
        #self.w.PREFS_.putpref("dsb_length", self.w.dsb_length.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_length = {}".format(self.w.dsb_length.value()))
        #self.w.PREFS_.putpref("dsb_circle_diam", self.w.dsb_circle_diam.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_circle_diam = {}".format(self.w.dsb_circle_diam.value()))
        #self.w.PREFS_.putpref("dsb_width", self.w.dsb_width.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_width = {}".format(self.w.dsb_width.value()))
        #self.w.PREFS_.putpref("dsb_step_x", self.w.dsb_step_x.valueself.w.dsb_width.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_step_x  = {}".format(self.w.dsb_step_x.value()))
        #self.w.PREFS_.putpref("dsb_step_y", self.w.dsb_step_y.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_step_y  = {}".format(self.w.dsb_step_y.value()))
        #self.w.PREFS_.putpref("dsb_radius_1", self.w.dsb_radius_1.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_radius_1 = {}".format(self.w.dsb_radius_1.value()))
        #self.w.PREFS_.putpref("dsb_radius_2", self.w.dsb_radius_1.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_radius_2  = {}".format(self.w.dsb_radius_2.value()))
        #self.w.PREFS_.putpref("dsb_radius_3", self.w.dsb_radius_3.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_radius_3  = {}".format( self.w.dsb_radius_3.value()))
        #self.w.PREFS_.putpref("dsb_radius_4", self.w.dsb_radius_4.value(), float, "CAM")
        self.cur.execute("UPDATE CAM set dsb_radius_4 = {}".format(self.w.dsb_radius_4.value()))
        #self.w.PREFS_.putpref("sb_quantity_x", self.w.sb_quantity_x.value(), int, "CAM")
        self.cur.execute("UPDATE CAM set sb_quantity_x  = {}".format(self.w.sb_quantity_x.value()))
        #self.w.PREFS_.putpref("sb_quantity_y", self.w.sb_quantity_y.value(), int, "CAM")
        self.cur.execute("UPDATE CAM set sb_quantity_y  = {}".format(self.w.sb_quantity_y.value()))
        #self.w.PREFS_.putpref("sb_feed", self.w.sb_feed.value(), int, "CAM")
        self.cur.execute("UPDATE CAM set sb_feed  = {}".format(self.w.sb_feed.value()))
        #self.w.PREFS_.putpref("sb_speed", self.w.sb_speed.value(), int, "CAM")
        self.cur.execute("UPDATE CAM set sb_speed = {}".format(self.w.sb_speed.value()))
        self.conn.commit()
        
        
        
        
        #ACTION.OPEN_PROGRAM(full_name)
        self.cmnd.program_open(full_name)
        old = STATUS.stat.file
        #if old == full_name:
        STATUS.emit('file-loaded', full_name)
        self.w.cmb_gcode_history.addItem(full_name)
        self.w.cmb_gcode_history.setCurrentIndex(self.w.cmb_gcode_history.count() - 1)
        self.add_status("Открываем файл {}".format(file_name))
        self.w.MainTab.setCurrentIndex(TAB_MAIN)
    # TAB SETING
    def btn_setting_save_clicked(self):
        #self.w.PREFS_.putpref('last_loaded_directory', os.path.dirname(
        #    self.last_loaded_program), str, 'BOOK_KEEPING')
        self.cur.execute("UPDATE BOOK_KEEPING set last_loaded_directory = '{}'".format(os.path.dirname(self.last_loaded_program)))
        
        #self.w.PREFS_.putpref('last_loaded_file',
        #                      self.last_loaded_program, str, 'BOOK_KEEPING')
        self.cur.execute("UPDATE BOOK_KEEPING set last_loaded_file = '{}'".format(self.last_loaded_program))
        #self.w.PREFS_.putpref("viscosity_a", self.w.DSBox_viscosity_a.value(), float, "Component_Properties")
        ##self.w.PREFS_.putpref("viscosity_b", self.w.DSBox_viscosity_b.value(), float, "Component_Properties")
        ##self.w.PREFS_.putpref("density_a", self.w.DSBox_density_a.value(), float, "Component_Properties")
        self.cur.execute("UPDATE Component_Properties set density_a = {}".format(self.w.DSBox_density_a.value()))
        #self.w.PREFS_.putpref("density_b", self.w.DSBox_density_b.value(), float, "Component_Properties")
        self.cur.execute("UPDATE Component_Properties set density_b = {}".format(self.w.DSBox_density_b.value()))
        #self.w.PREFS_.putpref("mass_fraction_a", self.w.SBox_mass_fraction_a.value(), int, "Component_Properties")
        self.cur.execute("UPDATE Component_Properties set mass_fraction_a = {}".format(self.w.SBox_mass_fraction_a.value()))
        #self.w.PREFS_.putpref("mass_fraction_b", self.w.SBox_mass_fraction_b.value(), int, "Component_Properties")
        self.cur.execute("UPDATE Component_Properties set mass_fraction_b = {}".format(self.w.SBox_mass_fraction_b.value()))
        #self.w.PREFS_.putpref("mixture_density", self.w.DSBox_mixture_density.value(), float, "Component_Properties")
        self.cur.execute("UPDATE Component_Properties set mixture_density = {}".format(self.w.DSBox_mixture_density.value()))
        #self.w.PREFS_.putpref("k", self.w.DSBox_k.value(), float, "Component_Properties")
        self.cur.execute("UPDATE Component_Properties set k = {}".format(self.w.DSBox_k.value()))
        ##self.w.PREFS_.putpref("pump_efficiency_a", self.w.DSBox_pump_efficiency_a.value(), float, "Installation_Parameters")
        ##self.w.PREFS_.putpref("pump_efficiency_b", self.w.DSBox_pump_efficiency_b.value(), float, "Installation_Parameters")
        #self.w.PREFS_.putpref("saturation_time_a", self.w.SBox_saturation_time_a.value(), int, "Installation_Parameters")
        self.cur.execute("UPDATE Installation_Parameters set saturation_time_a = {}".format(self.w.SBox_saturation_time_a.value()))
        #self.w.PREFS_.putpref("saturation_time_b", self.w.SBox_saturation_time_b.value(), int, "Installation_Parameters")
        self.cur.execute("UPDATE Installation_Parameters set saturation_time_b = {}".format(self.w.SBox_saturation_time_b.value()))
        #self.w.PREFS_.putpref("stirrin_time_a", self.w.SBox_stirrin_time_a.value(), int, "Installation_Parameters")
        self.cur.execute("UPDATE Installation_Parameters set stirrin_time_a = {}".format(self.w.SBox_stirrin_time_a.value()))
        #self.w.PREFS_.putpref("stirrin_time_b", self.w.SBox_stirrin_time_b.value(), int, "Installation_Parameters")
        self.cur.execute("UPDATE Installation_Parameters set stirrin_time_b = {}".format(self.w.SBox_stirrin_time_b.value()))
        #self.w.PREFS_.putpref("recuperation_time_a", self.w.SBox_recuperation_time_a.value(), int, "Installation_Parameters")
        self.cur.execute("UPDATE Installation_Parameters set recuperation_time_a = {}".format(self.w.SBox_recuperation_time_a.value()))
        #self.w.PREFS_.putpref("recuperation_time_b", self.w.SBox_recuperation_time_b.value(), int, "Installation_Parameters")
        self.cur.execute("UPDATE Installation_Parameters set recuperation_time_b = {}".format(self.w.SBox_recuperation_time_b.value()))
        #self.w.PREFS_.putpref("waiting_time", self.w.SBox_waiting_time.value(), int, "Installation_Parameters")
        self.cur.execute("UPDATE Installation_Parameters set waiting_time = {}".format(self.w.SBox_waiting_time.value()))
        #self.w.PREFS_.putpref("reset_fill_time", self.w.SBox_reset_fill_time.value(), int, "Installation_Parameters")
        self.cur.execute("UPDATE Installation_Parameters set reset_fill_time = {}".format(self.w.SBox_reset_fill_time.value()))
        #self.w.PREFS_.putpref("apply_before_rinsing", self.w.SBox_apply_before_rinsing.value(), int, "Installation_Parameters")
        self.cur.execute("UPDATE Installation_Parameters set apply_before_rinsing = {}".format(self.w.SBox_apply_before_rinsing.value()))
        self.conn.commit()
        self.set_hal_pin()
        self.add_status("Обновление пинов ")
    def btn_save_pos_cliked(self):
        #self.w.PREFS_.putpref("x", self.w.dSbox_pos1_x.value(), float, "SAVE_POS1")
        self.cur.execute("UPDATE SAVE_POS1 set x = {}".format(self.w.dSbox_pos1_x.value()))
        #self.w.PREFS_.putpref("y", self.w.dSbox_pos1_y.value(), float, "SAVE_POS1")
        self.cur.execute("UPDATE SAVE_POS1 set y = {}".format(self.w.dSbox_pos1_y.value()))
        #self.w.PREFS_.putpref("z", self.w.dSbox_pos1_z.value(), float, "SAVE_POS1")
        self.cur.execute("UPDATE SAVE_POS1 set z = {}".format(self.w.dSbox_pos1_z.value()))
        #self.w.PREFS_.putpref("x", self.w.dSbox_pos2_x.value(), float, "SAVE_POS2")
        self.cur.execute("UPDATE SAVE_POS2 set x = {}".format(self.w.dSbox_pos2_x.value()))
        #self.w.PREFS_.putpref("y", self.w.dSbox_pos2_y.value(), float, "SAVE_POS2")
        self.cur.execute("UPDATE SAVE_POS2 set y = {}".format(self.w.dSbox_pos2_y.value()))
        #self.w.PREFS_.putpref("z", self.w.dSbox_pos2_z.value(), float, "SAVE_POS2")
        self.cur.execute("UPDATE SAVE_POS2 set z = {}".format(self.w.dSbox_pos2_z.value()))
        #точки промывки ", "
        #self.w.PREFS_.putpref("x", self.w.dSbox_flushing_x.value(), float, "flushing")
        self.cur.execute("UPDATE flushing set x = {}".format(self.w.dSbox_flushing_x.value()))
        #self.w.PREFS_.putpref("y", self.w.dSbox_flushing_y.value(), float, "flushing")
        self.cur.execute("UPDATE flushing set y = {}".format(self.w.dSbox_flushing_y.value()))
        #self.w.PREFS_.putpref("z", self.w.dSbox_flushing_z.value(), float, "flushing")
        self.cur.execute("UPDATE flushing set z = {}".format(self.w.dSbox_flushing_z.value()))
        #точки сброса 
        #self.w.PREFS_.putpref("x", self.w.dSbox_reset_x.value(), float, "reset")
        self.cur.execute("UPDATE reset set x = {}".format(self.w.dSbox_reset_x.value()))
        #self.w.PREFS_.putpref("y", self.w.dSbox_reset_y.value(), float, "reset")
        self.cur.execute("UPDATE reset set y = {}".format(self.w.dSbox_reset_y.value()))
        #self.w.PREFS_.putpref("z", self.w.dSbox_reset_z.value(), float, "reset")
        self.cur.execute("UPDATE reset set z = {}".format(self.w.dSbox_reset_z.value()))
        self.conn.commit()
        self.set_pos_pin()
        self.add_status("Сохранение позиций завершено ")
        

    # TAB STATUS
    def btn_clear_status_clicked(self):
        STATUS.emit('update-machine-log', None, 'DELETE')
    def btn_save_status_clicked(self):
        if self.w.stackedWidget_log.currentIndex() == 0:
            text = self.w.machinelog.toPlainText()
            tmp = 'log/machine_log_'
        if self.w.stackedWidget_log.currentIndex() == 1:
            text = self.w.integrator_log.toPlainText()
            tmp = 'log/integrator_log_'
        now = datetime.datetime.now()
        filename = now.strftime("%d_%m_%Y__%H_%M")
        #filename = self.w.lbl_clock.text().encode('utf-8')
        filename = tmp + filename.replace(' ', '_') + '.txt'
        self.add_status("Сохранение логов в файл  {}".format(filename))
        with open(filename, 'w') as f:
            f.write(text)
    # PANEL
    def start_program(self):
        if (self.h['a.recovery-status'] or self.h['b.recovery-status'] or
            self.h['a.mixing-status'] or self.h['b.mixing-status'] or
            self.h['a.saturation-status'] or self.h['b.saturation-status'] or
            self.h['flushing-status'] ):
            info = '<b> Идет одна или несколько из технологических операций. Дождись их завершения для запуска  программы<\b>'
            mess = {'NAME':'MESSAGE', 'ICON':'WARNING', 'ID':'_pin_start', 'MESSAGE':'Внимание !', 'MORE':info, 'TYPE':'OK'}
            ACTION.CALL_DIALOG(mess)
            return
        ACTION.SET_AUTO_MODE()
        if not STATUS.is_auto_mode():
            self.add_status(
                "Должен быть в АВТОМАТИЧЕСКОМ режиме для запуска программы")
            return
        if STATUS.is_auto_running():
            self.add_status("программа уже работает")
            return            
        start_line = int(self.w.lbl_start_line.text().encode('utf-8'))
        self.add_status("Запущенная программа со строки {}".format(start_line))
        self.run_time = 0
        if self.w.chk_run_from_line.isChecked():
            ACTION.RUN(start_line)
        else:
            ACTION.RUN()

    def btn_start_clicked(self, obj):
        if self.w.MainTab.currentIndex() != 0:
            return
        self.start_program()

    def btn_reload_file_clicked(self):
        if self.last_loaded_program:
            self.w.progressBar.setValue(0)
            self.add_status("Загруженный файл программы {}".format(self.last_loaded_program))
            ACTION.OPEN_PROGRAM(self.last_loaded_program)
    # Слайдеры скрорости
    def slider_maxv_changed(self, value):
        maxpc = (float(value) / self.max_linear_velocity) * 100
        self.w.lbl_maxv_percent.setText("{:3.0f} %".format(maxpc))

    def slider_rapid_changed(self, value):
        rapid = (float(value) / 10) * self.max_linear_velocity 
        self.w.lbl_max_rapid.setText("{:5.0f}".format(rapid))

    def btn_maxv_100_clicked(self):
        self.w.slider_maxv_ovr.setValue(self.max_linear_velocity)

    def btn_maxv_50_clicked(self):
        self.w.slider_maxv_ovr.setValue(self.max_linear_velocity / 2)

    def btn_pump_100_clicked(self):
        self.w.slider_pump_ovr.setValue(100)

    def btn_pump_50_clicked(self):
        self.w.slider_pump_ovr.setValue(100 / 2)
    ## Кнопки управления компонентом А
    def a_saturation(self):
        if self.h['a.saturation-status']:
            # если процесс насыщения идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M105 P0")
            if self.h['a.mixing-status']:
                ACTION.CALL_MDI_WAIT("M107 P0")
        else:
            #saturation_time_a = self.w.PREFS_.getpref("saturation_time_a", 100, int, "Installation_Parameters")
            saturation_time_a = self.cur.execute("SELECT saturation_time_a FROM Installation_Parameters").fetchall()[0][0]
            ACTION.CALL_MDI_WAIT("M105 P1 Q{}".format(saturation_time_a))
            ACTION.CALL_MDI_WAIT("M107 P1 Q{}".format(saturation_time_a+5))
    def a_mixing(self):
        if self.h['a.mixing-status']:
            # если процесс перемешивания идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M107 P0")
        else:
            #mixing_time_a = self.w.PREFS_.getpref("stirrin_time_a", 100, int, "Installation_Parameters")
            mixing_time_a = self.cur.execute("SELECT stirrin_time_a FROM Installation_Parameters").fetchall()[0][0]
            ACTION.CALL_MDI_WAIT("M107 P1 Q{}".format(mixing_time_a))
     # кнопка рециркуляции компонента А
    def a_recuperation(self):
        if self.h['a.recovery-status']:
            # если процесс рециркуляции идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M103 P0")
        else:
            #recuperation_time_a = self.w.PREFS_.getpref("recuperation_time_a", 0, int, "Installation_Parameters")
            recuperation_time_a = self.cur.execute("SELECT recuperation_time_a FROM Installation_Parameters").fetchall()[0][0]
            ACTION.CALL_MDI_WAIT("M103 P1 Q{}".format(recuperation_time_a))
    ## Кнопки управления компонентом B
    def b_saturation(self):
        if self.h['b.saturation-status']:
            # если процесс насыщения идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M106 P0")
            ACTION.CALL_MDI_WAIT("M108 P0")
        else:
            #saturation_time_b = self.w.PREFS_.getpref("saturation_time_b", 100, int, "Installation_Parameters")
            saturation_time_b = self.cur.execute("SELECT saturation_time_b FROM Installation_Parameters").fetchall()[0][0]
            ACTION.CALL_MDI_WAIT("M106 P1 Q{}".format(saturation_time_b))
            ACTION.CALL_MDI_WAIT("M108 P1 Q{}".format(saturation_time_b+5))
    def b_mixing(self):
        if self.h['b.mixing-status']:
            # если процесс перемешивания идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M108 P0")
        else:
            #mixing_time_b = self.w.PREFS_.getpref("stirrin_time_b", 100, int, "Installation_Parameters")
            mixing_time_b = self.cur.execute("SELECT stirrin_time_b FROM Installation_Parameters").fetchall()[0][0]
            ACTION.CALL_MDI_WAIT("M108 P1 Q{}".format(mixing_time_b))
     # кнопка рециркуляции компонента B
    def b_recuperation(self):
        if self.h['b.recovery-status']:
            # если процесс рециркуляции идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M104 P0")
        else:
            #recuperation_time_a = self.w.PREFS_.getpref("recuperation_time_a", 0, int, "Installation_Parameters")
            recuperation_time_a = self.cur.execute("SELECT recuperation_time_a FROM Installation_Parameters").fetchall()[0][0]
            ACTION.CALL_MDI_WAIT("M104 P1 Q{}".format(recuperation_time_a))
    # кнопка промывки
    def flushing(self):
        if self.h['flushing-status']:
            # если процесс насыщения идет то выключаем его
            #ACTION.CALL_MDI_WAIT("M101 P0")
            ACTION.CALL_MDI("M101 P0")
            ACTION.CALL_MDI("G53 G0 Z0 ")
            self.first_click_flushing = False
            self.widget_management_enable(self.is_flushing, True)
            self.w.btn_washed.setStyleSheet(self.set_color_btn(False))
        else:
            if STATUS.stat.interp_state == linuxcnc.INTERP_READING:
                ACTION.CALL_MDI("M101 P0")
                ACTION.CALL_MDI("G53 G0 Z0 ")
                self.first_click_flushing = False
                self.widget_management_enable(self.is_flushing, True)
                self.w.btn_washed.setStyleSheet(self.set_color_btn(False))
            else:
                ACTION.CALL_MDI("M403")
                self.first_click_flushing = True
                self.widget_management_enable(self.is_flushing, False)
                self.w.btn_washed.setStyleSheet(self.set_color_btn(True))
    # кнопка сброса
    def reset_components(self):
        if self.h['reset_components-status']:
            # если процесс насыщения идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M102 P0")
        else:
            ACTION.CALL_MDI("M403 Q5000")
    # кнопка позиции 1
    def go_to_pos1(self):
        #X = self.w.PREFS_.getpref("x", 10, float, "SAVE_POS1")
        X = self.cur.execute("SELECT x FROM SAVE_POS1").fetchall()[0][0]
        #Y = self.w.PREFS_.getpref("y", 10, float, "SAVE_POS1")
        Y = self.cur.execute("SELECT Y FROM SAVE_POS1").fetchall()[0][0]
        #Z = self.w.PREFS_.getpref("z", 10, float, "SAVE_POS1")
        Z = self.cur.execute("SELECT Z FROM SAVE_POS1").fetchall()[0][0]
        ACTION.CALL_MDI("G90")
        command = "G53 G1 Z{} F2000".format(Z)
        ACTION.CALL_MDI_WAIT(command, 8)
        command = "G53 G1 X{} Y{} F10000".format(X, Y)
        ACTION.CALL_MDI_WAIT(command, 20)      
    # кнопка позиции 2
    def go_to_pos2(self):
        #X = self.w.PREFS_.getpref("x", 10, float, "SAVE_POS2")
        X = self.cur.execute("SELECT X FROM SAVE_POS2").fetchall()[0][0]
        #Y = self.w.PREFS_.getpref("y", 10, float, "SAVE_POS2")
        Y = self.cur.execute("SELECT Y FROM SAVE_POS2").fetchall()[0][0]
        #Z = self.w.PREFS_.getpref("z", 10, float, "SAVE_POS2")
        Z = self.cur.execute("SELECT Z FROM SAVE_POS2").fetchall()[0][0]
        ACTION.CALL_MDI("G90")
        command = "G53 G1 Z{} F2000".format(Z)
        ACTION.CALL_MDI_WAIT(command, 8)
        command = "G53 G1 X{} Y{} F10000".format(X, Y)
        ACTION.CALL_MDI_WAIT(command, 20)
    # кнопка подачи компонента
    def test_a(self):
        if self.h["test.a-status"]:
            # если процесс тестирования подача комп. А идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M109 P0")
        else:
            ACTION.CALL_MDI_WAIT("M114 P0") #Выключаем режим симуляции
            ACTION.CALL_MDI_WAIT("M111 P0") #На всякий случай подачу готовой смеси
            ACTION.CALL_MDI_WAIT("M110 P0") #На всякий случай подачу компонента Б
            Q = self.w.test_mass_a.value()
            ACTION.CALL_MDI_WAIT("M109 P1 Q{}".format(Q))
    def test_b(self):
        if self.h["test.b-status"]:
            # если процесс тестирования подача комп. Б идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M110 P0")
        else:
            ACTION.CALL_MDI_WAIT("M114 P0") #Выключаем режим симуляции
            ACTION.CALL_MDI_WAIT("M111 P0") #На всякий случай подачу готовой смеси
            ACTION.CALL_MDI_WAIT("M109 P0") #На всякий случай подачу компонента А
            Q = self.w.test_mass_b.value()
            ACTION.CALL_MDI_WAIT("M110 P1  Q{}".format(Q))
            print(Q)
    def test_mix(self):
        if self.h["test.mix-status"]:
            # если процесс тестирования идет то выключаем его
            ACTION.ABORT()
            ACTION.CALL_MDI_WAIT("M111 P0")
        else:
            ACTION.CALL_MDI_WAIT("M114 P0") #Выключаем режим симуляции
            ACTION.CALL_MDI_WAIT("M109 P0") #На всякий случай подачу компонента А
            ACTION.CALL_MDI_WAIT("M110 P0") #На всякий случай подачу компонента Б
            Q = self.w.test_mass_mix.value()
            ACTION.CALL_MDI_WAIT("M111 P1  Q{}".format(Q))
    # Кнопка ускорения
    def slow_button_clicked(self, state):
        slider = self.w.sender().property('slider')
        current = self.w[slider].value()
        max = self.w[slider].maximum()
        if state:
            self.w.sender().setText("МЕДЛЕННО")
            self.w[slider].setMaximum(max / self.slow_jog_factor)
            self.w[slider].setValue(current / self.slow_jog_factor)
            self.w[slider].setPageStep(10)
        else:
            self.w.sender().setText("БЫСТРО")
            self.w[slider].setMaximum(max * self.slow_jog_factor)
            self.w[slider].setValue(current * self.slow_jog_factor)
            self.w[slider].setPageStep(100)

    #####################
    # general functions #
    #####################
    def widget_management_enable(self, list, fast):
        for i in list:
            self.w[i].setEnabled(fast)
    def widget_management_show(self, list, fast):
        for i in list:
            if fast:
                self.w[i].show()
            else:
                self.w[i].hide()
    def set_start_line(self, line):
        if line == 0:
            self.w.lbl_start_line.setText('1')
        elif self.w.chk_run_from_line.isChecked():
            self.w.lbl_start_line.setText(str(line))
        else:
            self.w.lbl_start_line.setText('1')
    def editor_save(self):
        fname = self.w.filemanager.getCurrentSelected()
        if fname[1] is True:
            full_filename = fname[0]
        else:
            full_filename=self.w.gcode_editor.editor._last_filename
        #full_filename = os.path.abspath(full_filename)

        name, ext = os.path.splitext(full_filename)
        if '.ngc' != ext.lower():
            npath = name + '.ngc'
        else:
            npath = name + ext           

        gcode_text = self.w.gcode_editor.editor.text()
        #ACTION.SAVE_PROGRAM(gcode_text, full_filename)
        try:
            outfile = open(npath, 'w')
            outfile.write(gcode_text)
            STATUS.emit('update-machine-log', 'Saved: ' + npath, 'TIME')
        except Exception as e:
            print(e)
            STATUS.emit('error', linuxcnc.OPERATOR_ERROR, e)
        finally:
            try:
                outfile.close()
            except:
                pass

        self.w.gcode_editor.editor.setModified(False)
        self.w.btn_gcode_edit.setChecked(False)
        self.btn_gcode_edit_clicked(False)
        self.load_code(full_filename)
    def editor_exit(self):
        self.w.gcode_editor.exit
        self.w.btn_gcode_edit.setChecked(False)
        self.btn_gcode_edit_clicked(False)
    def load_code(self, fname):
        if fname is None:
            return
        if any([fname.lower().endswith(i) for i in self.ext]):
            self.w.cmb_gcode_history.addItem(fname)
            self.w.cmb_gcode_history.setCurrentIndex(
                self.w.cmb_gcode_history.count() - 1)
            ACTION.OPEN_PROGRAM(fname)
            self.add_status("Загруженный файл программы : {}".format(fname))
            self.w.MainTab.setCurrentIndex(TAB_MAIN)
        else:
            self.add_status("Неизвестное или недействительное имя файла")
    def chk_run_from_line_checked(self, state):
        if not state:
            self.w.lbl_start_line.setText('1')
    def add_status(self, message):
        self._m = message
        print(message)
        self.w.statusbar.showMessage(self._m, 5000)
        STATUS.emit('update-machine-log', self._m, 'TIME')
    def set_color_estop(self,status):
        if status:
            css = """
                QPushButton {
                    background-color: #32414B;
                    border: 1px solid #32414B;
                    color: #00F000;
                    border-radius: 4px;
                    padding: 3px;
                    outline: none;
                    min-width: 80px;
                }
                QPushButton:hover {
                      border: 1px solid #148CD2;
                      color: #00F000;
                }
                """
        else:
            css = """
                QPushButton {
                    background-color: #505F69;
                    border: 1px solid #32414B;
                    color: #FF0000;
                    border-radius: 4px;
                    padding: 3px;
                    outline: none;
                    min-width: 80px;
                }
                QPushButton:hover {
                      border: 1px solid #148CD2;
                      color: #FF0000;
                }
                """
        return css+CSS_DEFAUT 
    def set_color_btn(self,status):
        if status:
            css = """
                QPushButton {
                    background-color: #32414B;
                    border: 1px solid #32414B;
                    color: #00F0F0;
                    border-radius: 4px;
                    padding: 3px;
                    outline: none;
                    min-width: 80px;
                }
                QPushButton:hover {
                    border: 1px solid #148CD2;
                    color: #00F0F0;
                }
                """
        else:
            css = """
                QPushButton {
                    background-color: #505F69;
                    border: 1px solid #32414B;
                    color: #F0F0F0;
                    border-radius: 4px;
                    padding: 3px;
                    outline: none;
                    min-width: 80px;
                }
                QPushButton:hover {
                    border: 1px solid #148CD2;
                    color: #F0F0F0;
                }
                """
        return css+CSS_DEFAUT

    def dialog_return(self, w, message):
        rtn = message.get('RETURN')
        name = message.get('NAME')
        id_delete_file = bool(message.get('ID') == '_delete_file')
        if id_delete_file and name == 'MESSAGE' and rtn is True:
            if os.path.isdir(self.delete_file):
                # папку
                delete_type = "Удалена папка"
                shutil.rmtree(self.delete_file, ignore_errors=True)
            else:
                # файл
                delete_type = "Удален файл"
                os.remove(self.delete_file) 
            self.add_status("{} {}".format(delete_type,self.delete_file))

    def set_mode(self):
        if self.h['mode'] == 6:
            self.widget_management_show(self.setup_btn, True)
            self.widget_management_show(self.pos_flushing, True)

            if  STATUS.is_all_homed():
                self.w.btn_feed_joint.hide()
                self.w.btn_feed_axis.show()
                for widget in self.is_homed_list:
                    self.w[widget].setEnabled(True)
            else:
                self.w.btn_feed_joint.show()
                self.w.btn_feed_axis.hide()     
        else:
            self.widget_management_show(self.setup_btn, False)
            self.widget_management_show(self.pos_flushing, False)

            self.w.btn_feed_joint.hide()
            self.w.btn_feed_axis.show()
    # keyboard jogging from key binding calls
    # double the rate if fast is true
    # Кнопки управленя
    def kb_jog(self, state, joint, direction, fast=False, linear=True):
        if not STATUS.is_man_mode() or not STATUS.machine_is_on():
            self.add_status('Machine must be ON and in Manual mode to jog')
            return
        if linear:
            distance = STATUS.get_jog_increment()
            rate = STATUS.get_jograte()/60
        else:
            distance = STATUS.get_jog_increment_angular()
            rate = STATUS.get_jograte_angular()/60
        if state:
            if fast:
                rate = rate * 2
            ACTION.JOG(joint, direction, rate, distance)
        else:
            ACTION.JOG(joint, 0, 0, 0)

    #####################
    # KEY BINDING CALLS #
    #####################

    # Machine control
    def on_keycall_ESTOP(self, event, state, shift, cntrl):
        if state:
            ACTION.SET_ESTOP_STATE(STATUS.estop_is_clear())

    def on_keycall_POWER(self, event, state, shift, cntrl):
        if state:
            ACTION.SET_MACHINE_STATE(not STATUS.machine_is_on())

    def on_keycall_HOME(self, event, state, shift, cntrl):
        if state:
            if STATUS.is_all_homed():
                ACTION.SET_MACHINE_UNHOMED(-1)
            else:
                ACTION.SET_MACHINE_HOMING(-1)

    def on_keycall_ABORT(self, event, state, shift, cntrl):
        if state:
            if STATUS.stat.interp_state == linuxcnc.INTERP_IDLE:
                self.w.close()
            else:
                self.cmnd.abort()

    def on_keycall_F12(self, event, state, shift, cntrl):
        if state:
            STYLEEDITOR.load_dialog()

    #Linear Jogging
    def on_keycall_XPOS(self, event, state, shift, cntrl):
        self.kb_jog(state, 0, 1, shift)
    def on_keycall_XNEG(self, event, state, shift, cntrl):
        self.kb_jog(state, 0, -1, shift)
    def on_keycall_YPOS(self, event, state, shift, cntrl):
        self.kb_jog(state, 1, 1, shift)
    def on_keycall_YNEG(self, event, state, shift, cntrl):
        self.kb_jog(state, 1, -1, shift)
    def on_keycall_ZPOS(self, event, state, shift, cntrl):
        self.kb_jog(state, 2, 1, shift)
    def on_keycall_ZNEG(self, event, state, shift, cntrl):
        self.kb_jog(state, 2, -1, shift)

    # def on_keycall_APOS(self, event, state, shift, cntrl):
    #    pass
    #    #self.kb_jog(state, 3, 1, shift, False)
    # def on_keycall_ANEG(self, event, state, shift, cntrl):
    #    pass
        #self.kb_jog(state, 3, -1, shift, linear=False)

    ###########################
    # **** closing event **** #
    ###########################

    ##############################
    # required class boiler code #
    ##############################

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        return setattr(self, item, value)

    def actOnOptionalStop(self, widget, state):
        if state:
            ACTION.SET_OPTIONAL_STOP_ON()
        else:
            ACTION.SET_OPTIONAL_STOP_OFF()

################################
# required handler boiler code #
################################


def get_handlers(halcomp, widgets, paths):
    return [HandlerClass(halcomp, widgets, paths)]
