#!/usr/bin/python
#-*- coding: utf-8 -*-

# Для использование  необходимо в INI файл в раздел HAL выставить строку
# HALCMD = loadusr python gasketing/gasketing.py
# https://studref.com/458046/tehnika/smeshivanie_zhidkostey_raznoy_plotnosti
# https://planetcalc.ru/1421/

import time
from math import pi, asin, sin
import sys


# Set up logging
#from qtvcp import logger
#LOG = logger.getLogger(__name__)
# Set the log level for this module
# LOG.setLevel(logger.INFO) # One of DEBUG, INFO, WARNING, ERROR, CRITICAL
#LOG.setLevel(logger.INFO)

import hal
import hal_glib  # needed to make our own hal pins
import linuxcnc  # to get our own error system

#from datetime import datetime


#_Version = 0.3
# Перепесанно все с нуля от соеденн от GTK остался только hal и linuxcnc
# Все параметры через hal пины, ни каких настроек из файла


#_Version = 0.2.0 от 28.07.2020
# Исправлено зацыкливание при условие когда привышенно число нанесений
# Исправлено не открвался клапан РС7 при ручной подачи компонентов А и Б
# Добавленно остановка подачи компонентов при нажатие на кнопку "стоп" программа
# Добавленна задержка 0.5 сек на отключение клапана РС2,
# отвечающий за подачу растворителя и воздуха в камеру смещения компонентов,
# для того чтобы не оставалось воздуха в системе


#_Version = 0.2.0 от 27.07.2020
# Новая версия добавленны поддержка датчиков давления с ПЛК
# Возврат в исходную точку программы при первой промывки
# Убранны внешние М-кода на на пермещенеи в точку сброса и промывки,
# теперь перемешение осуществяется из этого модуля с проверкой достижения заданной позиции
# координаты задаются через  hal пины смотри gmoccapy_postgui.hal



class Gasketing(object):
    """
    Модуль для управления установкой по нанесению двух компонентных смесей
    """

    def __init__(self):
        #self.log_file = log_file

        self.halcomp = hal.component("gasketing")
        self.command = linuxcnc.command()
        self.stat = linuxcnc.stat()
        self.error_channel = linuxcnc.error_channel()
        # initial poll, so all is up to date
        self.stat.poll()
        self.error_channel.poll()
        # Создание пинов
        self._make_hal_pins()
        self.halcomp["app.first"] = True
        self.halcomp["app.count"] = 0
        # Промывка
        self.flushing_flag = False
        self.flushing_pin = False
        self.flushing_start_time = time.time()
        # Нанесение
        self.app_flag = False
        self.app_start_time = time.time()
        self.app_stop_time = time.time()
        # Сброс компонетов
        self.reset_comp_flag = False
        self.reset_comp_start_time = time.time()
        #тестированеи компонента А
        self.test_a_flag = False
        self.test_a_time = time.time()
        #тестированеи компонента B
        self.test_b_flag = False
        self.test_b_time = time.time()
        #тестированеи смеси
        self.test_mixture_flag = False
        self.test_mixture_time = time.time()
        #рекуперациия компонента А
        self.recovery_a_flag = False
        self.recovery_a_time = time.time()
        #рекуперациия компонента B
        self.recovery_b_flag = False
        self.recovery_b_time = time.time()
        #Насышение компонента А
        self.saturation_a_flag = False
        self.saturation_a_time = time.time()
        #Насышение компонента B
        self.saturation_b_flag = False
        self.saturation_b_time = time.time()
        #перемешивание компонента А
        self.mixing_a_flag = False
        self.mixing_a_time = time.time()
        #перемешивание компонента B
        self.mixing_b_flag = False
        self.mixing_b_time = time.time()
        #
        #  компонента А
        self.feed_off_a_flag = False
        self.feed_off_a_speed = 0.0
        self.feed_off_a_time = time.time()
        #  компонента B
        self.feed_off_b_flag = False
        self.feed_off_b_speed = 0.0
        self.feed_off_b_time = time.time()

        
        self.initialized = True
        #LOG.debug("Инициализация закончена {}".format( self.initialized))


    def _make_hal_pins(self):
        #######################################################################
        # Параметры нанесения и работы
        # Параметры компонента А
        self.halcomp.newparam("a.pump.capacity", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("a.density", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("a.mass_fraction", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("a.max_pressure", hal.HAL_FLOAT, hal.HAL_RW)
        # Параметры компонента Б
        self.halcomp.newparam("b.pump.capacity", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("b.density", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("b.mass_fraction", hal.HAL_FLOAT, hal.HAL_RW)
        # Параметры  готовой смеси
        self.halcomp.newparam("mixture.density", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("mixture.expansion-ratio", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("mixture.expansion-ratio-a", hal.HAL_FLOAT, hal.HAL_RW)
        # Парамеры при рекуперации
        self.halcomp.newparam("a.recuperation.speed", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("b.recuperation.speed", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("b.max_pressure", hal.HAL_FLOAT, hal.HAL_RW)
        # Парамеры при промывки
        self.halcomp.newparam("flushing.time_air", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("flushing.time_solver", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("flushing.time_mixer_on", hal.HAL_FLOAT, hal.HAL_RW)
        self.halcomp.newparam("flushing.speed_mixer", hal.HAL_FLOAT, hal.HAL_RW)
        # Параметры нанесения и работы установки окончание
        #######################################################################

        #######################################################################
        # пин для установки Estop (внутренний LinuxCNC) Вкл.
        self.halcomp.newpin("estop.activate", hal.HAL_BIT, hal.HAL_IN)
        #вывод для отображения состояния Estop  Вкл. / Выкл
        self.halcomp.newpin("estop.is-activated", hal.HAL_BIT, hal.HAL_OUT)
        # Пины с режимом работы
        self.halcomp.newpin("mode", hal.HAL_U32, hal.HAL_IO)
        # Пины с режимом работы
        self.halcomp.newpin("error.code", hal.HAL_U32, hal.HAL_OUT)
        self.halcomp.newpin("error.is", hal.HAL_BIT, hal.HAL_OUT)

        # Пины с который контролирует что питание поданно
        self.halcomp.newpin("power.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("power.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("power.is-on", hal.HAL_BIT, hal.HAL_IN)


        #######################################################################
        # Пины для управления оборудованием
        #######################################################################
        # Управление  пневмоцилиндрами
        # клапан безопастности                          Р01
        # Общий клапан на промывку                      Р02
        # Воздух для промывки                           Р03
        # Подача растворителя                           Р04
        # Подача компонента А                           Р05
        # Подача компонента Б                           Р06
        # Открыть клапан на сбор компонентов            Р07
        # Насыщение компонета А кислородом              Р08
        # Насыщение компонета B кислородом              Р09
        # Нагнетанние давления для компонета А          Р10
        # Нагнетанние давления для компонета B          Р11
        # Открыть клапан P14 на рекуперация компонета А     Р12
        # Открыть клапан P15 на рекуперация компонета Б     Р13

        self.halcomp.newpin("P.01", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.02", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.03", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.04", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.05", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.06", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.07", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.08", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.09", hal.HAL_BIT, hal.HAL_OUT) ##
        self.halcomp.newpin("P.10", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.11", hal.HAL_BIT, hal.HAL_OUT) ###
        self.halcomp.newpin("P.12", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("P.13", hal.HAL_BIT, hal.HAL_OUT)
        #пин для управление клапанами в режими наладки
        self.halcomp.newpin("P-command", hal.HAL_S32, hal.HAL_IN)
        # Управление насосом компонета А
        self.halcomp.newpin("a.pump.motor-is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("a.pump.speed", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("a.pump.speed-max", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("a.pump.is-max-speed", hal.HAL_BIT, hal.HAL_OUT)

        self.halcomp.newpin("a.pump.speed-gr", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("a.pump.speed-ratio", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("a.pump.time", hal.HAL_FLOAT, hal.HAL_OUT)
        #Пины для принудительного включения в режими наладки
        self.halcomp.newpin("a.pump.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("a.pump.speed-target", hal.HAL_FLOAT, hal.HAL_IN)

        # Управление насосом компонета Б
        self.halcomp.newpin("b.pump.motor-is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("b.pump.speed", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("b.pump.speed-max", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("b.pump.is-max-speed", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("pump.time-sleep", hal.HAL_FLOAT, hal.HAL_IN)

        self.halcomp.newpin("b.pump.speed-gr", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("b.pump.speed-ratio", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("b.pump.time", hal.HAL_FLOAT, hal.HAL_OUT)
        #Пины для принудительного включения в режими наладки
        self.halcomp.newpin("b.pump.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("b.pump.speed-target", hal.HAL_FLOAT, hal.HAL_IN)

        # Управление мешалкой компонентов
        self.halcomp.newpin("a.mixing.motor-is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("b.mixing.motor-is-on", hal.HAL_BIT, hal.HAL_OUT)
        # Управление миксером
        self.halcomp.newpin("mixer.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("mixer.off", hal.HAL_BIT, hal.HAL_IN)

        self.halcomp.newpin("mixer.is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("mixer.speed-target", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("mixer.speed", hal.HAL_FLOAT, hal.HAL_OUT)
        # Пины для управления оборудованием окончание
        #######################################################################

        #######################################################################
        # Сигналы с датчиков
        # показания с датчиков давления компонентов до преобразования
        self.halcomp.newpin("a.pressure.in", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("b.pressure.in", hal.HAL_FLOAT, hal.HAL_IN)
        # коэффинт преобразования
        self.halcomp.newpin("a.pressure.gain", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("b.pressure.gain", hal.HAL_FLOAT, hal.HAL_IN)
        # показания с датчиков давления компонентов после преобразования
        self.halcomp.newpin("a.pressure.out", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("b.pressure.out", hal.HAL_FLOAT, hal.HAL_OUT)
        #Сигнал о том что превышенно максимальное давление
        self.halcomp.newpin("a.pressure.is-max", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("b.pressure.is-max", hal.HAL_BIT, hal.HAL_OUT)

        # показания с датчиков минимального состояния копонентов и растворителя
        self.halcomp.newpin("a.min", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("b.min", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("solvent.min", hal.HAL_BIT, hal.HAL_IN)
        # Сигналы с датчиков окончание
        #######################################################################

        #######################################################################
        # Пины отвечающие за рекуперации компонента А
        self.halcomp.newpin("a.recovery.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("a.recovery.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("a.recovery.is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("a.recovery.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("a.recovery.time", hal.HAL_FLOAT, hal.HAL_OUT)
        # Пины отвечающие за рекуперации компонента B
        self.halcomp.newpin("b.recovery.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("b.recovery.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("b.recovery.is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("b.recovery.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("b.recovery.time", hal.HAL_FLOAT, hal.HAL_OUT)
        # Команда отвечающие для насыщения компонента А
        self.halcomp.newpin("a.saturation.is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("a.saturation.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("a.saturation.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("a.saturation.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("a.saturation.time", hal.HAL_FLOAT, hal.HAL_OUT)
        # Пины отвечающие за насыщения компонента Б
        self.halcomp.newpin("b.saturation.is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("b.saturation.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("b.saturation.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("b.saturation.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("b.saturation.time", hal.HAL_FLOAT, hal.HAL_OUT)
        # Команда  для перемешивания компонентов A
        self.halcomp.newpin("a.mixing.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("a.mixing.is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("a.mixing.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("a.mixing.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("a.mixing.time", hal.HAL_FLOAT, hal.HAL_OUT)
        # Команда  для перемешивания компонентов B
        self.halcomp.newpin("b.mixing.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("b.mixing.is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("b.mixing.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("b.mixing.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("b.mixing.time", hal.HAL_FLOAT, hal.HAL_OUT)


        # Пины отвечающие за нанесение  height, width, component_mass
        self.halcomp.newpin("app.height", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("app.width", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("app.feed", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("app.feed_nom", hal.HAL_FLOAT, hal.HAL_IN)

        self.halcomp.newpin("app.speed", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("app.time", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("app.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("app.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("app.is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("app.first", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("app.count", hal.HAL_U32, hal.HAL_OUT)
        self.halcomp.newpin("app.max-count", hal.HAL_U32, hal.HAL_IN)
        self.halcomp.newpin("app.sleep-time", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("app.is-idle", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("app.is-paused", hal.HAL_BIT, hal.HAL_IN)
        # суммарная расход кажого из компонентов
        self.halcomp.newpin("app.set_mass", hal.HAL_FLOAT, hal.HAL_IN)
        # суммарная расход кажого из компонентов расчитавылся при скорости 

        self.halcomp.newpin("app.feed_of_mass", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("app.cal_of_mass", hal.HAL_BIT, hal.HAL_IN)

        # Пин задежки на включение сопла
        self.halcomp.newpin("app.time-sleep-p07", hal.HAL_FLOAT, hal.HAL_IN)

        # Пины при промывки
        self.halcomp.newpin("flushing.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("flushing.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("flushing.is-on", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("flushing.is-count", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("flushing.is-time", hal.HAL_BIT, hal.HAL_OUT)
        self.halcomp.newpin("flushing.time-last", hal.HAL_FLOAT, hal.HAL_OUT)

        self.halcomp.newpin("flushing.time", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("flushing.status", hal.HAL_S32, hal.HAL_OUT)
        # Пины отвечающие за сброс компонентов
        self.halcomp.newpin("reset-comp.speed-mixer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("reset-comp.speed-a", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("reset-comp.speed-b", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("reset-comp.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("reset-comp.time", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("reset-comp.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("reset-comp.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("reset-comp.is-on", hal.HAL_BIT, hal.HAL_OUT)
        # режим симуляции при нем не подается сигнал на моторы
        self.halcomp.newpin("sim.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("sim.is-on", hal.HAL_BIT, hal.HAL_OUT)

        #Пины для тестирования подача компонента А
        self.halcomp.newpin("test.a.mass", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("test.a.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("test.a.time", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("test.a.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("test.a.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("test.a.is-on", hal.HAL_BIT, hal.HAL_OUT)
        #Пины для тестирования подача компонента Б
        self.halcomp.newpin("test.b.mass", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("test.b.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("test.b.time", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("test.b.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("test.b.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("test.b.is-on", hal.HAL_BIT, hal.HAL_OUT)
        #Пины для тестирования подача компонента готовой смеси
        self.halcomp.newpin("test.mixture.mass", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("test.mixture.timer", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("test.mixture.speed", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("test.mixture.time", hal.HAL_FLOAT, hal.HAL_OUT)
        self.halcomp.newpin("test.mixture.on", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("test.mixture.off", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("test.mixture.is-on", hal.HAL_BIT, hal.HAL_OUT)
        # Команнды на начало работы окончание
        #######################################################################

        # Пин отображающей время цикла
        self.halcomp.newpin("time", hal.HAL_FLOAT, hal.HAL_OUT)
        
        # Пин с задержкой цикла чтобы не загружать проц
        self.halcomp.newpin("time-sleep", hal.HAL_FLOAT, hal.HAL_IN)
        self.halcomp.newpin("test-in", hal.HAL_BIT, hal.HAL_OUT)
        #hal_glib.GPin(pin).connect("value_changed", self.rest)
        self.halcomp.newpin("pump_fault", hal.HAL_BIT, hal.HAL_IN)
        self.halcomp.newpin("a_fault", hal.HAL_BIT, hal.HAL_IN)
        #LOG.info("Создание hal пинов завершено")

    ###################################################
    def update_pressure(self):
        """ обновление данных о давление """
        self.halcomp["a.pressure.out"] = (
            self.halcomp["a.pressure.in"] * self.halcomp["a.pressure.gain"])
        self.halcomp["b.pressure.out"] = (
            self.halcomp["b.pressure.in"] * self.halcomp["b.pressure.gain"])
        #Проверка того что не привысили давление компонента А
        if self.halcomp["a.pressure.out"] > self.halcomp["a.max_pressure"]:
            self.halcomp["a.pressure.is-max"] = True
        else:
            self.halcomp["a.pressure.is-max"] = False
        #Проверка того что не привысили давление компонента Б
        if self.halcomp["b.pressure.out"] > self.halcomp["b.max_pressure"]:
            self.halcomp["b.pressure.is-max"] = True
        else:
            self.halcomp["b.pressure.is-max"] = False
    
    def pump_fault(self):
        if self.halcomp["pump_fault"] == True:
			 # Отключаем флаги которые отвечают за начало процесса
             # и откючаем сам процесс
             # Промывка
            if self.feed_off_a_flag:
                self.feed_off_a_flag= self.feed_comp_a_off(False)
            if self.feed_off_b_flag:
                self.feed_off_b_flag= self.feed_comp_b_off(False)
            if self.flushing_flag:
                self.flushing_flag = self.flushing(False, self.flushing_start_time)
			# Нанесение
            if self.app_flag:
                self.app_flag = self.application(False, self.app_start_time)
            #тестированеи компонента А
            if self.test_a_flag:
                self.test_a_flag = self.feed_mass_a(False, self.test_a_time)
            #тестированеи компонента B
            if self.test_b_flag:
                self.test_b_flag = self.feed_mass_b(False, self.test_a_time)
            #тестированеи смеси
            if self.test_mixture_flag:
                self.test_mixture_flag = self.feed_mass_mixture(False, self.test_mixture_time)
            #рекуперациия компонента А
            if self.recovery_a_flag:
                self.recovery_a_flag = self.recovery_a(False, self.recovery_a_time)
            #рекуперациия компонента B
            if self.recovery_b_flag:
                self.recovery_b_flag = self.recovery_b(False, self.recovery_a_time)
            #Насышение компонента А
            if self.saturation_a_flag:
                self.saturation_a_flag = self.saturation_a(False, self.saturation_a_time)
            #Насышение компонента B
            if self.saturation_b_flag:
                self.saturation_b_flag = self.saturation_b(False, self.saturation_a_time)
            #перемешивание компонента А
            if self.mixing_a_flag:
                self.mixing_a_flag = self.mixing_a(False, self.mixing_a_time)
            #перемешивание компонента B
            if self.mixing_b_flag:
                self.mixing_b_flag = self.mixing_b(False, self.mixing_a_time)
            # Сброс компонетов
            if self.reset_comp_flag:
                self.reset_comp_flag = self.reset_components(False, self.reset_comp_start_time)

            # выключение подачи компонента
            self.halcomp["a.pump.motor-is-on"] = False
            self.halcomp["a.pump.speed"] = 0
            self.halcomp["b.pump.motor-is-on"] = False
            self.halcomp["b.pump.speed"] = 0
            # выключение врашения шпинделя/главного миксера
            self.halcomp["mixer.is-on"] = False
            self.halcomp["mixer.speed"] = 0
            # выключение статусных бит рекуперации и насышения
            self.halcomp["a.recovery.is-on"] = False
            self.halcomp["a.recovery.on"] = False
            self.halcomp["a.saturation.is-on"] = False
            self.halcomp["a.saturation.on"] = False
            self.halcomp["a.mixing.is-on"] = False
            self.halcomp["a.mixing.on"] = False
            self.halcomp["b.recovery.is-on"] = False
            self.halcomp["b.recovery.on"] = False
            self.halcomp["b.saturation.is-on"] = False
            self.halcomp["b.saturation.on"] = False
            self.halcomp["b.mixing.is-on"] = False
            self.halcomp["b.mixing.on"] = False
            # выключение всех клапанов
            self.clapan_power(False)
            # выключение режима нанесения  и промывки
            self.halcomp["app.on"] = False
            self.halcomp["app.is-on"] = False
            self.halcomp["flushing.on"] = False
            self.halcomp["flushing.is-on"] = False
            self.halcomp["reset-comp.on"] = False
            self.halcomp["reset-comp.is-on"] = False
            # выключение режима тестирования
            self.halcomp["test.a.on"] = False
            self.halcomp["test.a.is-on"] = False
            self.halcomp["test.b.on"] = False
            self.halcomp["test.b.is-on"] = False
            self.halcomp["test.mixture.on"] = False
            self.halcomp["test.mixture.is-on"] = False
            
            print('pum1111111111111')
            
    def estop_is_activated(self):
        """
        Дейстия при аварийной остановки
        """
        # Отключаем флаги которые отвечают за начало процесса
        # и откючаем сам процесс
        # Промывка
        if self.feed_off_a_flag:
            self.feed_off_a_flag= self.feed_comp_a_off(False)
        if self.feed_off_b_flag:
            self.feed_off_b_flag= self.feed_comp_b_off(False)
        if self.flushing_flag:
            self.flushing_flag = self.flushing(False, self.flushing_start_time)
        # Нанесение
        if self.app_flag:
            self.app_flag = self.application(False, self.app_start_time)
        #тестированеи компонента А
        if self.test_a_flag:
            self.test_a_flag = self.feed_mass_a(False, self.test_a_time)
        #тестированеи компонента B
        if self.test_b_flag:
            self.test_b_flag = self.feed_mass_b(False, self.test_a_time)
        #тестированеи смеси
        if self.test_mixture_flag:
            self.test_mixture_flag = self.feed_mass_mixture(False, self.test_mixture_time)
        #рекуперациия компонента А
        if self.recovery_a_flag:
            self.recovery_a_flag = self.recovery_a(False, self.recovery_a_time)
        #рекуперациия компонента B
        if self.recovery_b_flag:
            self.recovery_b_flag = self.recovery_b(False, self.recovery_a_time)
        #Насышение компонента А
        if self.saturation_a_flag:
            self.saturation_a_flag = self.saturation_a(False, self.saturation_a_time)
        #Насышение компонента B
        if self.saturation_b_flag:
            self.saturation_b_flag = self.saturation_b(False, self.saturation_a_time)
        #перемешивание компонента А
        if self.mixing_a_flag:
            self.mixing_a_flag = self.mixing_a(False, self.mixing_a_time)
        #перемешивание компонента B
        if self.mixing_b_flag:
            self.mixing_b_flag = self.mixing_b(False, self.mixing_a_time)
        # Сброс компонетов
        if self.reset_comp_flag:
            self.reset_comp_flag = self.reset_components(False, self.reset_comp_start_time)

        # выключение подачи компонента
        self.halcomp["a.pump.motor-is-on"] = False
        self.halcomp["a.pump.speed"] = 0
        self.halcomp["b.pump.motor-is-on"] = False
        self.halcomp["b.pump.speed"] = 0
        # выключение врашения шпинделя/главного миксера
        self.halcomp["mixer.is-on"] = False
        self.halcomp["mixer.speed"] = 0
        # выключение статусных бит рекуперации и насышения
        self.halcomp["a.recovery.is-on"] = False
        self.halcomp["a.recovery.on"] = False
        self.halcomp["a.saturation.is-on"] = False
        self.halcomp["a.saturation.on"] = False
        self.halcomp["a.mixing.is-on"] = False
        self.halcomp["a.mixing.on"] = False
        self.halcomp["b.recovery.is-on"] = False
        self.halcomp["b.recovery.on"] = False
        self.halcomp["b.saturation.is-on"] = False
        self.halcomp["b.saturation.on"] = False
        self.halcomp["b.mixing.is-on"] = False
        self.halcomp["b.mixing.on"] = False
        # выключение всех клапанов
        self.clapan_power(False)
        # выключение режима нанесения  и промывки
        self.halcomp["app.on"] = False
        self.halcomp["app.is-on"] = False
        self.halcomp["flushing.on"] = False
        self.halcomp["flushing.is-on"] = False
        self.halcomp["reset-comp.on"] = False
        self.halcomp["reset-comp.is-on"] = False
        # выключение режима тестирования
        self.halcomp["test.a.on"] = False
        self.halcomp["test.a.is-on"] = False
        self.halcomp["test.b.on"] = False
        self.halcomp["test.b.is-on"] = False
        self.halcomp["test.mixture.on"] = False
        self.halcomp["test.mixture.is-on"] = False

    def power_machine_off(self):
        """
        если питание выключенно то закрываем все клапана и
        пины которые отвечают за включение двигателей
        """
        # выключение подачи компонента
        self.halcomp["a.pump.motor-is-on"] = False
        self.halcomp["a.pump.speed"] = 0
        self.halcomp["b.pump.motor-is-on"] = False
        self.halcomp["b.pump.speed"] = 0
        # выключение врашения шпинделя/главного миксера
        self.halcomp["mixer.is-on"] = False
        self.halcomp["mixer.speed"] = 0
        # выключение статусных бит рекуперации и насышения
        self.halcomp["a.recovery.on"] = False
        self.halcomp["a.saturation.on"] = False
        self.halcomp["a.mixing.on"] = False
        self.halcomp["b.recovery.on"] = False
        self.halcomp["b.saturation.on"] = False
        self.halcomp["b.mixing.on"] = False
        # выключение всех клапанов
        self.clapan_power(False)
        #также выключаем все запросы на выполнение если они были активны
        # выключение режима нанесения  и промывки
        self.halcomp["app.on"] = False
        self.halcomp["flushing.on"] = False
        # выключение режима тестирования
        self.halcomp["test.a.on"] = False
        self.halcomp["test.b.on"] = False
        self.halcomp["test.mixture.on"] = False


    def clapan_power(self, status):
        """
        Выключает все клана
        """
        self.halcomp["P.01"] = status
        self.halcomp["P.02"] = status
        self.halcomp["P.03"] = status
        self.halcomp["P.04"] = status
        self.halcomp["P.05"] = status
        self.halcomp["P.06"] = status
        self.halcomp["P.07"] = status
        self.halcomp["P.08"] = status
        self.halcomp["P.09"] = status
        self.halcomp["P.10"] = status
        self.halcomp["P.11"] = status
        self.halcomp["P.12"] = status
        self.halcomp["P.13"] = status
    #@staticmethod
    def speed_calculation(self, method_calculation, set_feed=0):
        """
        Функция для расчета скорости насосов в зависимости от того из какого места вызвана
        единицы измерения
        плотности - грамм/см3
        масса - грамм
        объем - см3
        скорость обороты/мин после вычисления
        длина в см """
        try:
            # скорость перемешения преводим мм/мин в см/сек
            feed = set_feed / 600
            # Габаритные размеры слоя переводим в см
            height = self.halcomp["app.height"] /10
            width = self.halcomp["app.width"]  /10
            # парамеры готовой смеси
            ro = self.halcomp["mixture.density"]
            k = self.halcomp["mixture.expansion-ratio"]
            k2 = self.halcomp["mixture.expansion-ratio-a"]
            # суммарная расход кажого из компонентов гр/мин в гр/сек
            set_mass = self.halcomp["app.set_mass"]/60
            feed_of_mass = self.halcomp["app.feed_of_mass"] / 600

            cal_of_mass = self.halcomp["app.cal_of_mass"] 

            # парамеры компонента А
            ro_comp_a = self.halcomp["a.density"]
            q_pump_a = self.halcomp["a.pump.capacity"]
            w_a = self.halcomp["a.mass_fraction"]
            # парамеры компонента Б
            ro_comp_b = self.halcomp["b.density"]
            q_pump_b = self.halcomp["b.pump.capacity"]
            w_b = self.halcomp["b.mass_fraction"]
            # парамеры тестовой компонента А
            test_time_a = self.halcomp["test.a.timer"]
            test_mass_a = self.halcomp["test.a.mass"]
            # парамеры тестовой компонента Б
            test_time_b = self.halcomp["test.b.timer"]
            test_mass_b = self.halcomp["test.b.mass"]
            # коэффициенты скорости
            ratio_a = self.halcomp["a.pump.speed-ratio"]
            ratio_b = self.halcomp["b.pump.speed-ratio"]
            # максимальная скорости
            speed_max_a = self.halcomp["a.pump.speed-max"]
            speed_max_b = self.halcomp["b.pump.speed-max"]
        except AttributeError:
            print("There is no such attribute")
        if method_calculation == 1:
            # Расчет скорости вращения насоса когда нужно
            # подать необходимо подать заданное массу компонентов
            try:
                speed_b = test_mass_b /(ro_comp_b * q_pump_b * test_time_b)
            except ZeroDivisionError:
                speed_b = 0
                self.halcomp["error.code"] = 4
                self.halcomp["error.is"] = True
            try:
                speed_a = test_mass_a /(ro_comp_a * q_pump_a * test_time_a)
            except ZeroDivisionError:
                speed_a = 0
                self.halcomp["error.code"] = 5
                self.halcomp["error.is"] = True
        elif method_calculation == 2:
            # Расчет скорости вращения насоса когда нужно
            # подать необходимо подать компоненты во время нанесения
            if feed == 0:
                speed_b = 0
                speed_a = 0
                self.halcomp["error.code"] = 11
            else:
                try:
                    width = width * k
                    height = width *0.5
                    radius = height*0.5 + width*width/(8* height)
                    alfa = 2 * asin(width/(2*radius))
                    area = 0.5*radius*radius*(alfa - sin(alfa))
                    # Объем смеси  Vr(t) = area * feed  * t
                    Vr = area * feed
                    # Масса смеси mp(t) = Vp(t)*ro * k
                    # где k  коэфикнт расширения
                    mr = Vr * ro *k2
                    # масса каждого компонента  m_i(t) = mr(t) * w_i/(w_a + w_b)
                    m_a = mr * w_a/(w_a + w_b)
                    m_b = mr * w_b/(w_a + w_b)
                    #  Объем каждого компонента  V_i(t) = m_i(t) / ro_i
                    V_a = m_a / ro_comp_a
                    V_b = m_b / ro_comp_b
                    # скорость насоса компонента Б speed_b(t) = m_b(t)/(ro_comp_b * q_pump_b * t)
                    speed_b = m_b / (ro_comp_b * q_pump_b)
                    # скорость насоса компонента A speed_a(t) =
                    #  (V_a(t)/V_b(t) ) * (q_pump_b /q_pump_a) * speed_b(t)
                    speed_a = (V_a/V_b) * (q_pump_b /q_pump_a) * speed_b
                except ZeroDivisionError:
                    self.halcomp["error.code"] = 1
                    self.halcomp["error.is"] = True
                    speed_b = 0
                    speed_a = 0
                except AttributeError:
                    self.halcomp["error.code"] = 10
                    self.halcomp["error.is"] = True
                if cal_of_mass:
                    #Если заданно считать через массу
                    # масса = частному суммарному расходу компонентов гр/мин
                    # при котором соствлялась таблица умноженная на текушию скорость 
                    mr = (set_mass/feed_of_mass)*feed*k
                    # масса каждого компонента  m_i(t) = mr(t) * w_i/(w_a + w_b)
                    m_a = mr * w_a/(w_a + w_b)
                    m_b = mr * w_b/(w_a + w_b)
                    #  Объем каждого компонента  V_i(t) = m_i(t) / ro_i
                    V_a = m_a / ro_comp_a
                    V_b = m_b / ro_comp_b
                    # скорость насоса компонента Б speed_b(t) = m_b(t)/(ro_comp_b * q_pump_b * t)
                    speed_b = m_b / (ro_comp_b * q_pump_b)
                    # скорость насоса компонента A speed_a(t) =
                    #  (V_a(t)/V_b(t) ) * (q_pump_b /q_pump_a) * speed_b(t)
                    speed_a = (V_a/V_b) * (q_pump_b /q_pump_a) * speed_b

        elif method_calculation == 3:
            # Расчет скорости вращения насоса когда нужно
            # подать необходимо подать заданную массу компонтов
            try:
                # заданная масса компонентов
                mixture_mass = self.halcomp["test.mixture.mass"]
                # время подачи
                mixture_timer = self.halcomp["test.mixture.timer"]
                # масса каждого компонента  m_i = mr * w_i/(w_a + w_b)
                m_a = mixture_mass * w_a/(w_a + w_b)
                m_b = mixture_mass * w_b/(w_a + w_b)
                #  Объем каждого компонента  V_i = m_i / ro_i
                V_a = m_a / ro_comp_a
                V_b = m_b / ro_comp_b
                # скорость насоса компонента Б speed_b(t) = m_b/(ro_comp_b * q_pump_b * t)
                speed_b = m_b / (ro_comp_b * q_pump_b * mixture_timer)
                # скорость насоса компонента A speed_a(t) =
                # (V_a/V_b) * (q_pump_b /q_pump_a) * speed_b(t)
                speed_a = (V_a/V_b) * (q_pump_b /q_pump_a) * speed_b

            except ZeroDivisionError:
                self.halcomp["error.code"] = 2
                self.halcomp["error.is"] = True
                speed_b = 0
                speed_a = 0
        else:
            self.halcomp["error.code"] = 3
            self.halcomp["error.is"] = True
            speed_b = 0
            speed_a = 0

        speed_a = speed_a * ratio_a * 60
        speed_b = speed_b * ratio_b * 60

        if speed_a != 0 and speed_b != 0:
            k_speed = speed_a /speed_b
        else:
            k_speed = 1
        if speed_a > speed_max_a and speed_b < speed_max_b:
            self.halcomp["a.pump.is-max-speed"] = True
            self.halcomp["b.pump.is-max-speed"] = False
            speed_a = speed_max_a
            speed_b = speed_a * (1/k_speed)
        elif speed_a < speed_max_a and speed_b > speed_max_b:
            self.halcomp["a.pump.is-max-speed"] = False
            self.halcomp["b.pump.is-max-speed"] = True
            speed_b = speed_max_b
            speed_a = k_speed * speed_b
        elif speed_a > speed_max_a and speed_b > speed_max_b:
            self.halcomp["a.pump.is-max-speed"] = True
            self.halcomp["b.pump.is-max-speed"] = True
            ka = speed_a / speed_max_a
            kb = speed_b / speed_max_b
            if ka > kb:
                speed_a = speed_max_a
                speed_b = speed_a * (1/k_speed)
            else:
                speed_b = speed_max_b
                speed_a = k_speed * speed_b
        else:
            self.halcomp["a.pump.is-max-speed"] = False
            self.halcomp["b.pump.is-max-speed"] = False
            #speed_a = speed_a
            #speed_b = speed_b
        return speed_a, speed_b

    def mixer_on(self, status, speed=0):
        """включение миксера"""
        if status:
            self.halcomp["mixer.is-on"] = True
            self.halcomp["mixer.speed"] = speed
        else:
            self.halcomp["mixer.is-on"] = False
            self.halcomp["mixer.speed"] = 0

    def feed_comp_a(self, status, start_timer, speed):
        """включение подачи компонента A"""
        if status:
            self.halcomp["P.12"] = False
            if self.halcomp["sim.on"]:
                self.halcomp["a.pump.motor-is-on"] = False
                self.halcomp["sim.is-on"] = True
                self.halcomp["P.05"] = False
            else:
                self.halcomp["a.pump.motor-is-on"] = True
                self.halcomp["sim.is-on"] = False
                self.halcomp["P.05"] = True
            self.halcomp["a.pump.speed"] = speed
            self.feed_off_a_speed = speed
            # парамеры компонента А
            ro_comp_a = self.halcomp["a.density"]
            q_pump_a = self.halcomp["a.pump.capacity"]
            self.halcomp["a.pump.speed-gr"] = speed * ro_comp_a * q_pump_a
            current_time = time.time()-start_timer
            self.halcomp["a.pump.time"] = current_time
        else:
            self.halcomp["P.05"] = False
            #self.halcomp["P.12"] = False
            #self.halcomp["a.pump.motor-is-on"] = False
            self.feed_off_a_flag = True
            self.feed_off_a_time = time.time()
            self.halcomp["a.pump.speed"] = speed
            # парамеры компонента А
            ro_comp_a = self.halcomp["a.density"]
            q_pump_a = self.halcomp["a.pump.capacity"]
            self.halcomp["a.pump.speed-gr"] = speed * ro_comp_a * q_pump_a

    def feed_comp_a_off(self, status):
        """включение подачи компонента A"""
        ro_comp_a = self.halcomp["a.density"]
        q_pump_a = self.halcomp["a.pump.capacity"]
        start_timer = self.feed_off_a_time
        if status:
            current_time = time.time() - start_timer
            if current_time < self.halcomp["pump.time-sleep"]:
                speed = self.feed_off_a_speed
                self.halcomp["P.05"] = False
                self.halcomp["a.pump.motor-is-on"] = True
                self.halcomp["a.pump.speed"] = speed
                # парамеры компонента А
                self.halcomp["a.pump.speed-gr"] = speed * ro_comp_a * q_pump_a
                return True
            else:
                speed = 0
                self.halcomp["P.05"] = False
                self.halcomp["a.pump.motor-is-on"] = False
                self.halcomp["a.pump.speed"] = speed
                # парамеры компонента А
                self.halcomp["a.pump.speed-gr"] = speed * ro_comp_a * q_pump_a
                return False
        else:
            self.halcomp["P.05"] = False
            self.halcomp["a.pump.motor-is-on"] = False
            self.halcomp["a.pump.speed"] = 0
            return False

    def feed_comp_b(self, status, start_timer, speed):
        """включение подачи компонента B"""
        if status:
            
            self.halcomp["P.13"] = False
            if self.halcomp["sim.on"]:
                self.halcomp["b.pump.motor-is-on"] = False
                self.halcomp["sim.is-on"] = True
                self.halcomp["P.06"] = False
            else:
                self.halcomp["b.pump.motor-is-on"] = True
                self.halcomp["sim.is-on"] = False
                self.halcomp["P.06"] = True
            self.halcomp["b.pump.speed"] = speed
            self.feed_off_b_speed = speed

            ro_comp_b = self.halcomp["b.density"]
            q_pump_b = self.halcomp["b.pump.capacity"]
            self.halcomp["b.pump.speed-gr"] = speed * ro_comp_b * q_pump_b
            current_time = time.time()-start_timer
            self.halcomp["b.pump.time"] = current_time
        else:
            self.halcomp["P.06"] = False
            #self.halcomp["P.13"] = False
            #self.halcomp["b.pump.motor-is-on"] = False
            self.feed_off_b_flag = True
            self.feed_off_b_time = time.time()
            self.halcomp["b.pump.speed"] = speed
            ro_comp_b = self.halcomp["b.density"]
            q_pump_b = self.halcomp["b.pump.capacity"]
            self.halcomp["b.pump.speed-gr"] = speed * ro_comp_b * q_pump_b

    def feed_comp_b_off(self, status):
        """включение подачи компонента A"""
        ro_comp_b = self.halcomp["b.density"]
        q_pump_b = self.halcomp["b.pump.capacity"]
        start_timer = self.feed_off_b_time

        if status:
            current_time = time.time() - start_timer
            if current_time < self.halcomp["pump.time-sleep"]:
                speed = self.feed_off_b_speed
                self.halcomp["P.06"] = False
                self.halcomp["b.pump.motor-is-on"] = True
                self.halcomp["b.pump.speed"] = speed
                self.halcomp["b.pump.speed-gr"] = speed * ro_comp_b * q_pump_b
                return True
            else:
                speed = 0
                self.halcomp["P.06"] = False
                self.halcomp["b.pump.motor-is-on"] = False
                self.halcomp["b.pump.speed"] = speed
                self.halcomp["b.pump.speed-gr"] = speed * ro_comp_b * q_pump_b
                return False
        else:
            self.halcomp["P.06"] = False
            self.halcomp["b.pump.motor-is-on"] = False
            self.halcomp["b.pump.speed"] = 0
            return False



    def recovery_a(self, status, start_timer):
        """включение рекупеции компонента A"""
        def recovery_a_on(status, start_timer, speed):
            self.halcomp["a.pump.motor-is-on"] = status
            self.halcomp["a.pump.speed"] = speed
            ro_comp_a = self.halcomp["a.density"]
            q_pump_a = self.halcomp["a.pump.capacity"]
            self.halcomp["a.pump.speed-gr"] = speed * ro_comp_a * q_pump_a
            self.halcomp["a.pump.time"] = time.time()-start_timer
            #self.halcomp["P.05"] = status
            self.halcomp["P.12"] = status
            self.halcomp["a.recovery.is-on"] = status
            if status is False:
                self.halcomp["a.recovery.on"] = status
        if status:
            set_timer = self.halcomp["a.recovery.timer"]
            current_time = time.time() - start_timer
            self.halcomp["a.recovery.time"] = current_time
            if current_time < set_timer:
                speed = self.halcomp["a.recuperation.speed"]
                recovery_a_on(True, start_timer, speed)
                return True
            else:
                recovery_a_on(False, start_timer, 0)
                return False
        else:
            recovery_a_on(False, start_timer, 0)
            return False

    def recovery_b(self, status, start_timer):
        """включение рекупеции компонента B"""
        def recovery_b_on(status, start_timer, speed):
            self.halcomp["b.pump.motor-is-on"] = status
            self.halcomp["b.pump.speed"] = speed
            ro_comp_b = self.halcomp["b.density"]
            q_pump_b = self.halcomp["b.pump.capacity"]
            self.halcomp["b.pump.speed-gr"] = speed * ro_comp_b * q_pump_b
            self.halcomp["b.pump.time"] = time.time()-start_timer
            #self.halcomp["P.06"] = status
            self.halcomp["P.13"] = status
            self.halcomp["b.recovery.is-on"] = status
            if status is False:
                self.halcomp["b.recovery.on"] = status

        if status:
            set_timer = self.halcomp["b.recovery.timer"]
            current_time = time.time() - start_timer
            self.halcomp["b.recovery.time"] = current_time
            if current_time < set_timer:
                speed = self.halcomp["b.recuperation.speed"]
                recovery_b_on(True, start_timer, speed)
                return True
            else:
                recovery_b_on(False, start_timer, 0)
                return False
        else:
            recovery_b_on(False, start_timer, 0)
            return False

    def flushing(self, status, start_timer_flushing):
        """Функция для промывки смесительной камеры на вход состояние и время начала цикла """
        if status:
            time_solver = self.halcomp["flushing.time_solver"]
            time_air = self.halcomp["flushing.time_air"]
            time_mixer = self.halcomp["flushing.time_mixer_on"]
            mixer_speed = self.halcomp["flushing.speed_mixer"]
            current_time = time.time() - start_timer_flushing
            self.halcomp["flushing.time"] = current_time
            stage_1 = (current_time < time_solver and current_time > 0)
            stage_2 = (current_time < (time_solver + time_air)
                       and current_time > time_solver)
            stage_3 = (current_time < (2 * time_solver + time_air)
                       and current_time > (time_solver + time_air))
            stage_4 = (current_time < 2 * (time_solver + time_air)
                       and current_time > (2 * time_solver + time_air))
            stage_5 = (current_time < 2 * (time_solver + time_air) +
                       2 and current_time > 2 * (time_solver + time_air))
            stage_6 = (current_time > 2 * (time_solver + time_air) + 2)

            if current_time > time_mixer:
                self.mixer_on(True, mixer_speed)
            if stage_5:
                self.halcomp["P.02"] = True  # общий клапан
                self.halcomp["P.03"] = False  # воздух
                self.halcomp["P.04"] = False  # растворитель
                self.halcomp["P.07"] = True  # сброс
                self.halcomp["flushing.status"] = 2 if stage_2 else 4
                self.halcomp["flushing.is-on"] = True
                return True
            if stage_6:
                self.halcomp["P.02"] = False  # общий клапан
                self.halcomp["P.03"] = False  # воздух
                self.halcomp["P.04"] = False  # растворитель
                self.halcomp["P.07"] = True  # сброс
                self.mixer_on(False)
                self.halcomp["flushing.status"] = 6
                self.halcomp["flushing.is-on"] = False
                self.halcomp["flushing.on"] = False
                self.flushing_flag = False
                self.halcomp["app.count"] = 0
                self.halcomp["app.first"] = True
                return False
            if stage_1 or stage_3:
                self.halcomp["P.02"] = True  # общий клапан
                self.halcomp["P.03"] = False  # воздух
                self.halcomp["P.04"] = True  # растворитель
                self.halcomp["P.07"] = True  # сброс
                self.halcomp["flushing.status"] = 1 if stage_1 else 3
                self.halcomp["flushing.is-on"] = True
                return True
            if stage_2 or stage_4:
                self.halcomp["P.02"] = True  # общий клапан
                self.halcomp["P.03"] = True  # воздух
                self.halcomp["P.04"] = False  # растворитель
                self.halcomp["P.07"] = True  # сброс NO
                self.halcomp["flushing.status"] = 2 if stage_2 else 4
                self.halcomp["flushing.is-on"] = True
                return True
        else:
            self.halcomp["P.02"] = False  # общий клапан
            self.halcomp["P.03"] = False  # воздух
            self.halcomp["P.04"] = False  # растворитель
            self.halcomp["P.07"] = False  # сброс
            self.mixer_on(False)
            self.halcomp["flushing.status"] = 7
            self.halcomp["flushing.is-on"] = False
            self.halcomp["flushing.on"] = False
            self.halcomp["app.count"] = 0
            self.halcomp["app.first"] = True
            return False

    def application(self, status, start_timer_app):
        """Функция для включения нанесения"""
        if status:
            mixer_speed = self.halcomp["app.speed"]
            feed = self.halcomp["app.feed"]
            speed_a, speed_b = self.speed_calculation(method_calculation=2, set_feed=feed)
            self.feed_comp_a(True, start_timer_app, speed_a)
            self.feed_comp_b(True, start_timer_app, speed_b)
            self.mixer_on(True, mixer_speed)
            if self.halcomp["sim.on"]:
                self.halcomp["P.07"] = False  # сброс
            else:
                if time.time()-start_timer_app>self.halcomp["app.time-sleep-p07"]:
                    self.halcomp["P.07"] = True  # сброс
                else:
                    self.halcomp["P.07"] = False  # сброс
            current_time = time.time() - start_timer_app
            self.halcomp["app.time"] = current_time
            self.halcomp["app.is-on"] = True
            return True
        else:
            #Функция для выключения нанесения
            self.feed_comp_a(False, start_timer_app, 0)
            self.feed_comp_b(False, start_timer_app, 0)
            self.mixer_on(False, 0)
            self.halcomp["P.07"] = False  # сброс
            self.halcomp["app.is-on"] = False
            self.halcomp["app.on"] = False
            if self.halcomp["sim.on"] is False:
                self.halcomp["app.first"] = False
                self.halcomp["app.count"] = self.halcomp["app.count"] + 1          
                self.app_stop_time = time.time()
            return False

    def reset_components(self, status, start_timer):
        """Функция для сброса компонентов"""
        def reset_components_on(status, pump_speed_a, pump_speed_b, motor_speed_mixer, timer):
            self.feed_comp_a(status, timer, pump_speed_a)
            self.feed_comp_b(status, timer, pump_speed_b)
            self.mixer_on(status, motor_speed_mixer)
            self.halcomp["P.07"] = status  # сброс
            self.halcomp["reset-comp.is-on"] = True
        def reset_components_off(status, pump_speed_a, pump_speed_b, motor_speed_mixer, timer):
            self.feed_comp_a(status, timer, pump_speed_a)
            self.feed_comp_b(status, timer, pump_speed_b)
            self.mixer_on(status, motor_speed_mixer)
            self.halcomp["P.07"] = status  # сброс
            self.halcomp["reset-comp.is-on"] = status
            if status is False:
                self.halcomp["reset-comp.on"] = status
        if status:
            set_timer = self.halcomp["reset-comp.timer"]
            current_time = time.time() - start_timer
            self.halcomp["reset-comp.time"] = current_time
            stage_1 = current_time < set_timer  #on
            stage_2 = ((set_timer < current_time ) and  (current_time < set_timer + 0.5 ))#off
            stage_3 = ((set_timer + 0.5 < current_time) and (current_time < set_timer + 2.5)) #on
            stage_4 = current_time > set_timer + 2.5 #off

            if stage_1:
                mixer_speed = self.halcomp["reset-comp.speed-mixer"]
                feed = self.halcomp["app.feed_nom"]
                speed_a, speed_b = self.speed_calculation(method_calculation=2, set_feed=feed)
                if speed_a == 0 or speed_b == 0:
                    speed_a = self.halcomp["reset-comp.speed-a"]
                    speed_b = self.halcomp["reset-comp.speed-b"]
                reset_components_on(True, speed_a, speed_b, mixer_speed, start_timer)
                return True
            else:
                reset_components_off(False, 0, 0, 0, start_timer)
                return False
        else:
            reset_components_off(False, 0, 0, 0, start_timer)
            return False

    def feed_mass_a(self, status, start_timer):
        """Тестирование подачи компонента A за определенное время"""
        def mass_a_on(status, timer, pump_speed):
            #self.feed_comp_a(status, timer, pump_speed)
            self.halcomp["a.pump.motor-is-on"] = status
            self.halcomp["a.pump.speed"] = pump_speed
            self.halcomp["P.05"] = status
            ro_comp_a = self.halcomp["a.density"]
            q_pump_a = self.halcomp["a.pump.capacity"]
            self.halcomp["a.pump.speed-gr"] = pump_speed * ro_comp_a * q_pump_a
            current_time = time.time()-timer
            self.halcomp["a.pump.time"] = current_time
            self.halcomp["P.07"] = status  # сброс
            self.halcomp["test.a.is-on"] = status
            if status is False:
                self.halcomp["test.a.on"] = status
        if status:
            set_timer = self.halcomp["test.a.timer"]
            current_time = time.time() - start_timer
            self.halcomp["test.a.time"] = current_time
            if current_time < set_timer:
                speed_a, _ = self.speed_calculation(method_calculation=1, set_feed=0)
                mass_a_on(True, start_timer, speed_a)
                return True
            else:
                mass_a_on(False, start_timer, 0)
                return False
        else:
            mass_a_on(False, start_timer, 0)
            return False

    def feed_mass_b(self, status, start_timer):
        """ Тестирование подачи компонента B за определенное время"""
        def mass_b_on(status, timer, pump_speed):
            #self.feed_comp_b(status, timer, pump_speed)
            self.halcomp["b.pump.motor-is-on"] = status
            self.halcomp["P.06"] = status
            self.halcomp["b.pump.speed"] = pump_speed
            ro_comp_b = self.halcomp["b.density"]
            q_pump_b = self.halcomp["b.pump.capacity"]
            self.halcomp["b.pump.speed-gr"] = pump_speed * ro_comp_b * q_pump_b
            current_time = time.time()-timer
            self.halcomp["b.pump.time"] = current_time
            self.halcomp["P.07"] = status  # сброс
            self.halcomp["test.b.is-on"] = status
            if status is False:
                self.halcomp["test.b.on"] = status
        if status:
            set_timer = self.halcomp["test.b.timer"]
            current_time = time.time() - start_timer
            self.halcomp["test.b.time"] = current_time
            _, speed_b = self.speed_calculation(method_calculation=1, set_feed=0)
            if current_time < set_timer:
                mass_b_on(True, start_timer, speed_b)
                return True
            else:
                mass_b_on(False, start_timer, 0)
                return False
        else:
            mass_b_on(False, start_timer, 0)
            return False

    def feed_mass_mixture(self, status, start_timer):
        """Тестирование подачи готоовой смеси за определенное время"""
        def mixture_on(status, pump_speed_a, pump_speed_b, motor_speed_mixer, timer):
            #self.feed_comp_a(status, timer, pump_speed_a)
            #self.feed_comp_b(status, timer, pump_speed_b)
            current_time = time.time()-timer
            self.halcomp["P.05"] = status
            self.halcomp["P.06"] = status

            self.halcomp["a.pump.motor-is-on"] = status
            self.halcomp["a.pump.speed"] = pump_speed_a
            ro_comp_a = self.halcomp["a.density"]
            q_pump_a = self.halcomp["a.pump.capacity"]
            self.halcomp["a.pump.speed-gr"] = pump_speed_a * ro_comp_a * q_pump_a
            self.halcomp["a.pump.time"] = current_time

            self.halcomp["b.pump.motor-is-on"] = status
            self.halcomp["b.pump.speed"] = pump_speed_b
            ro_comp_b = self.halcomp["b.density"]
            q_pump_b = self.halcomp["b.pump.capacity"]
            self.halcomp["b.pump.speed-gr"] = pump_speed_b * ro_comp_b * q_pump_b
            self.halcomp["b.pump.time"] = current_time

            self.mixer_on(status, motor_speed_mixer)
            self.halcomp["P.07"] = status  # сброс
            self.halcomp["test.mixture.is-on"] = status
            if status is False:
                self.halcomp["test.mixture.on"] = status
        if status:
            set_timer = self.halcomp["test.mixture.timer"]
            current_time = time.time() - start_timer
            self.halcomp["test.mixture.time"] = current_time
            if current_time < set_timer:
                mixer_speed = self.halcomp["test.mixture.speed"]
                speed_a, speed_b = self.speed_calculation(method_calculation=3, set_feed=0)
                mixture_on(True, speed_a, speed_b, mixer_speed, start_timer)
                return True
            else:
                mixture_on(False, 0, 0, 0, start_timer)
                return False
        else:
            mixture_on(False, 0, 0, 0, start_timer)
            return False

    def saturation_a(self, status, start_timer):
        """включение насыщения компонента A"""
        def saturation_a_on(status):
            self.halcomp["P.08"] = status
            self.halcomp["P.10"] = status
            self.halcomp["a.saturation.is-on"] = status
            if status is False:
                self.halcomp["a.saturation.on"] = status
        if status:
            set_timer = self.halcomp["a.saturation.timer"]
            current_time = time.time() - start_timer
            self.halcomp["a.saturation.time"] = current_time
            if current_time < set_timer:
                saturation_a_on(True)
                return True
            else:
                saturation_a_on(False)
                return False
        else:
            saturation_a_on(False)
            return False

    def saturation_b(self, status, start_timer):
        """Включение насыщения компонента B"""
        def saturation_b_on(status):
            self.halcomp["P.09"] = status
            self.halcomp["P.11"] = status
            self.halcomp["b.saturation.is-on"] = status
            if status is False:
                self.halcomp["b.saturation.on"] = status
        if status:
            set_timer = self.halcomp["b.saturation.timer"]
            current_time = time.time() - start_timer
            self.halcomp["b.saturation.time"] = current_time
            if current_time < set_timer:
                saturation_b_on(True)
                return True
            else:
                saturation_b_on(False)
                return False
        else:
            saturation_b_on(False)
            return False

    def mixing_a(self, status, start_timer):
        """Включение перемешения компонента A"""
        def mixing_a_on(status):
            self.halcomp["a.mixing.is-on"] = status
            self.halcomp["a.mixing.motor-is-on"] = status
            if status is False:
                self.halcomp["a.mixing.on"] = status

        if status:
            set_timer = self.halcomp["a.mixing.timer"]
            current_time = time.time() - start_timer
            self.halcomp["a.mixing.time"] = current_time
            if current_time < set_timer:
                mixing_a_on(True)
                return True
            else:
                mixing_a_on(False)
                return False
        else:
            mixing_a_on(False)
            return False

    def mixing_b(self, status, start_timer):
        """Включение перемещивания компонента B"""
        def mixing_b_on(status):
            self.halcomp["b.mixing.is-on"] = status
            self.halcomp["b.mixing.motor-is-on"] = status
            if status is False:
                self.halcomp["b.mixing.on"] = status
        if status:
            set_timer = self.halcomp["b.mixing.timer"]
            current_time = time.time() - start_timer
            self.halcomp["b.mixing.time"] = current_time
            if current_time < set_timer:
                mixing_b_on(True)
                return True
            else:
                mixing_b_on(False)
                return False
        else:
            mixing_b_on(False)
            return False

    def flushing_loop(self):
        """
        часть бесконечного цикла которая
        проверяет разлешенно ли выполнять промывку
        """
        self.flushing_flag, self.flushing_start_time = self.check_flag(
            self.halcomp["flushing.on"],
            self.halcomp["flushing.is-on"],
            self.flushing_start_time,
            self.flushing_flag,
            self.flushing)
        if self.flushing_flag:
            self.flushing_flag = self.flushing(True, self.flushing_start_time)

    def normal_mode(self):
        """
        Нормальный режим работы при нем доступны
        промывка
        наненсение
        сброс компонетов
        рекуперация
        насыщение
        перемещивание компонента
        """
        # проверка условия что привысили максимлаьное значение
        if self.halcomp["app.count"] >= self.halcomp["app.max-count"]:
            self.halcomp["flushing.is-count"] = True
        else:
            self.halcomp["flushing.is-count"] = False
        if self.halcomp["app.first"] is False and self.halcomp["app.is-on"] is False:
            last_app_time = time.time() - self.app_stop_time
            self.halcomp["flushing.time-last"] = self.halcomp["app.sleep-time"] - last_app_time
            if last_app_time > self.halcomp["app.sleep-time"]:
                self.halcomp["flushing.is-time"] = True
            else:
                self.halcomp["flushing.is-time"] = False
        else:
            self.halcomp["flushing.time-last"] = 0
            self.halcomp["flushing.is-time"] = False
        if self.feed_off_a_flag:
            self.feed_off_a_flag= self.feed_comp_a_off(True)
        if self.feed_off_b_flag:
            self.feed_off_b_flag= self.feed_comp_b_off(True)
        #Промывка
        self.flushing_loop()
        #Нанесение
        self.app_flag, self.app_start_time = self.check_flag(
            self.halcomp["app.on"],
            self.halcomp["app.is-on"],
            self.app_start_time,
            self.app_flag,
            self.application)
        if self.app_flag:
            self.app_flag = self.application(True, self.app_start_time)
        if self.halcomp["app.is-idle"]:
            if self.app_flag:
                self.app_flag = self.application(False, self.app_start_time)
            if self.flushing_flag:
                self.flushing_flag = self.flushing(False, self.flushing_start_time)
            if self.reset_comp_flag:
                self.reset_comp_flag = self.reset_components(False, self.reset_comp_start_time)
        # Сброс компонетов
        self.reset_comp_flag, self.reset_comp_start_time = self.check_flag(
            self.halcomp["reset-comp.on"],
            self.halcomp["reset-comp.is-on"],
            self.reset_comp_start_time,
            self.reset_comp_flag,
            self.reset_components)
        if self.reset_comp_flag:
            self.reset_comp_flag = self.reset_components(True, self.reset_comp_start_time)
        #рекуперациия компонента А
        self.recovery_a_flag, self.recovery_a_time = self.check_flag(
            self.halcomp["a.recovery.on"],
            self.halcomp["a.recovery.is-on"],
            self.recovery_a_time,
            self.recovery_a_flag,
            self.recovery_a)
        if self.recovery_a_flag:
            self.recovery_a_flag = self.recovery_a(True, self.recovery_a_time)
        #рекуперациия компонента B
        self.recovery_b_flag, self.recovery_b_time = self.check_flag(
            self.halcomp["b.recovery.on"],
            self.halcomp["b.recovery.is-on"],
            self.recovery_b_time,
            self.recovery_b_flag,
            self.recovery_b)
        if self.recovery_b_flag:
            self.recovery_b_flag = self.recovery_b(True, self.recovery_b_time)
        #насыщение компонента А
        self.saturation_a_flag, self.saturation_a_time = self.check_flag(
            self.halcomp["a.saturation.on"],
            self.halcomp["a.saturation.is-on"],
            self.saturation_a_time,
            self.saturation_a_flag,
            self.saturation_a)
        if self.saturation_a_flag:
            self.saturation_a_flag = self.saturation_a(True, self.saturation_a_time)
        #насыщение компонента B
        self.saturation_b_flag, self.saturation_b_time = self.check_flag(
            self.halcomp["b.saturation.on"],
            self.halcomp["b.saturation.is-on"],
            self.saturation_b_time,
            self.saturation_b_flag,
            self.saturation_b)
        if self.saturation_b_flag:
            self.saturation_b_flag = self.saturation_b(True, self.saturation_b_time)
        #Перемешивание компонента А
        self.mixing_a_flag, self.mixing_a_time = self.check_flag(
            self.halcomp["a.mixing.on"],
            self.halcomp["a.mixing.is-on"],
            self.mixing_a_time,
            self.mixing_a_flag,
            self.mixing_a)
        if self.mixing_a_flag:
            self.mixing_a_flag = self.mixing_a(True, self.mixing_a_time)
        #Перемешивание компонента B
        self.mixing_b_flag, self.mixing_b_time = self.check_flag(
            self.halcomp["b.mixing.on"],
            self.halcomp["b.mixing.is-on"],
            self.mixing_b_time,
            self.mixing_b_flag,
            self.mixing_b)
        if self.mixing_b_flag:
            self.mixing_b_flag = self.mixing_b(True, self.mixing_b_time)

    def test_mode(self):
        """
        тестовый режим при нем доспупны
        тестовая подача компонента А
        тестовая подача компонента Б
        тестовая подача готовой массы
        промывка
        """
        #Промывка
        self.flushing_loop()
        #тестированеи компонента А
        self.test_a_flag, self.test_a_time = self.check_flag(
            self.halcomp["test.a.on"],
            self.halcomp["test.a.is-on"],
            self.test_a_time,
            self.test_a_flag,
            self.feed_mass_a)
        if self.test_a_flag:
            self.test_a_flag = self.feed_mass_a(True, self.test_a_time)
        #тестированеи компонента B
        self.test_b_flag, self.test_b_time = self.check_flag(
            self.halcomp["test.b.on"],
            self.halcomp["test.b.is-on"],
            self.test_b_time,
            self.test_b_flag,
            self.feed_mass_b)
        if self.test_b_flag:
            self.test_b_flag = self.feed_mass_b(True, self.test_b_time)
        #тестированеи смеси
        self.test_mixture_flag, self.test_mixture_time = self.check_flag(
            self.halcomp["test.mixture.on"],
            self.halcomp["test.mixture.is-on"],
            self.test_mixture_time,
            self.test_mixture_flag,
            self.feed_mass_mixture)
        if self.test_mixture_flag:
            self.test_mixture_flag = self.feed_mass_mixture(True, self.test_mixture_time)

    def clapan_loop(self):
        """
        Режим управления клапанами в зависимости смотрит номер командного пина
        и изменяет значение соотвествующего клапан
        если задан -1 клапан то закрывает все клапана
        если задан не существующий номер то меняет на значение пина на 0
        """
        if self.halcomp["P-command"] == 1:
            self.halcomp["P-command"] = 0
            self.halcomp["P.01"] = not self.halcomp["P.01"]
            return
        elif self.halcomp["P-command"] == 2:
            self.halcomp["P-command"] = 0
            self.halcomp["P.02"] = not self.halcomp["P.02"]
            return
        elif self.halcomp["P-command"] == 3:
            self.halcomp["P-command"] = 0
            self.halcomp["P.03"] = not self.halcomp["P.03"]
            return
        elif self.halcomp["P-command"] == 4:
            self.halcomp["P-command"] = 0
            self.halcomp["P.04"] = not self.halcomp["P.04"]
            return
        elif self.halcomp["P-command"] == 5:
            self.halcomp["P-command"] = 0
            self.halcomp["P.05"] = not self.halcomp["P.05"]
            return
        elif self.halcomp["P-command"] == 6:
            self.halcomp["P-command"] = 0
            self.halcomp["P.06"] = not self.halcomp["P.06"]
            return
        elif self.halcomp["P-command"] == 7:
            self.halcomp["P-command"] = 0
            self.halcomp["P.07"] = not self.halcomp["P.07"]
            return
        elif self.halcomp["P-command"] == 8:
            self.halcomp["P-command"] = 0
            self.halcomp["P.08"] = not self.halcomp["P.08"]
            return
        elif self.halcomp["P-command"] == 9:
            self.halcomp["P-command"] = 0
            self.halcomp["P.09"] = not self.halcomp["P.09"]
            return
        elif self.halcomp["P-command"] == 10:
            self.halcomp["P-command"] = 0
            self.halcomp["P.10"] = not self.halcomp["P.10"]
            return
        elif self.halcomp["P-command"] == 11:
            self.halcomp["P-command"] = 0
            self.halcomp["P.11"] = not self.halcomp["P.11"]
            return
        elif self.halcomp["P-command"] == 12:
            self.halcomp["P-command"] = 0
            self.halcomp["P.12"] = not self.halcomp["P.12"]
            return
        elif self.halcomp["P-command"] == 13:
            self.halcomp["P-command"] = 0
            self.halcomp["P.13"] = not self.halcomp["P.13"]
            return
        elif self.halcomp["P-command"] == -1:
            self.halcomp["P-command"] = 0
            self.clapan_power(False)
            return
        else:
            self.halcomp["P-command"] = 0
            return

    def setup_mode(self):
        """
        Режим наладки при нем доступны
        возможность открытия любого клапана
        """
        self.clapan_loop()
    
    def setup_mode2(self):
        """
        Режим наладки при нем доступны
        запус двигателя компонента с заданной скоростью
        """
        if self.halcomp["a.pump.on"]:
            pump_speed = self.halcomp["a.pump.speed-target"]
            timer = time.time()
            self.feed_comp_a(True, timer, pump_speed)
        else:
            self.feed_comp_a(False, 0, 0)

        if self.halcomp["b.pump.on"]:
            pump_speed = self.halcomp["b.pump.speed-target"]
            timer = time.time()
            self.feed_comp_b(True, timer, pump_speed)
        else:
            self.feed_comp_b(False, 0, 0)

        if self.halcomp["mixer.on"]:
            mixer_speed = self.halcomp["mixer.speed-target"]
            self.mixer_on(True, mixer_speed)
        else:
            self.mixer_on(False, 0)
    def check_flag(self, pin, status_pin, start_timer, flag, func):
        """
        Поднимаем флаг и записываем время старта
        взависимости от состояние процесса и
        управляющего пина.
        """
        if pin and status_pin is False:
            flag_on = True
            timer_on = time.time()
            func(True, timer_on)
            print("START", func)
        elif pin and status_pin:
            flag_on = flag
            timer_on = start_timer
        elif pin is False and status_pin is False:
            flag_on = flag
            timer_on = start_timer
        else:
            flag_on = False
            timer_on = start_timer
            func(False, start_timer)
            print("STOP", func)
        return flag_on, timer_on

    def loop(self):
        """
        Основой цикл программы вначале считываес состояие LCNC,
        если ошибок нет то идем дальше если есть то заверщаем программу.
        Дальше порверяем на наличеи ошибок и то что пин на ошибку не активирован
        """
        # получаем состояние linuxcnc, если pid linuxcnc убит
        # из внешней команды, мы также выйдем из программы
        while True:
            start_time = time.time()
            ###################
            self.pump_fault()
            ###################
            try:
				###################
                self.pump_fault()
                ###################3
                self.stat.poll()  # получаем текущие состояние linuxcnc
                if self.halcomp["estop.activate"] is False:
                    self.update_pressure()
                    if (self.halcomp["a.pressure.is-max"] is False and
                            self.halcomp["b.pressure.is-max"] is False):
                        self.halcomp["estop.is-activated"] = False
                        if self.halcomp["power.on"]:
                            self.halcomp["power.is-on"] = True
                            if self.halcomp["mode"] == 0:
                                self.normal_mode()
                                self.test_mode()
                            elif self.halcomp["mode"] == 4:
                                self.setup_mode()
                            elif self.halcomp["mode"] == 6:
                                self.setup_mode2()                                
                            else:
                                self.normal_mode()
                                self.test_mode()
                        else:
                            self.estop_is_activated()
                            self.halcomp["power.is-on"] = False
                    else:
                        self.estop_is_activated()
                        self.halcomp["estop.is-activated"] = True
                else:
                    self.estop_is_activated()
                    self.halcomp["power.is-on"] = False
                    self.halcomp["estop.is-activated"] = True
                t_sleep = self.halcomp["time-sleep"]
                time.sleep(t_sleep)
                self.halcomp["time"] = time.time()-start_time
            except KeyboardInterrupt:
                print("Gasketing: KeyboardInterrupt !!!")
                self.kill_output()
                raise
            except:
                print("error")
                print(sys.exc_info())
            # ошибки Linuxcnc

    def kill_output(self):
        """
        Действия при аварийном отключение
        """
        self.estop_is_activated()
        print(sys.exc_info())
        print("Gasketing: Kill !!!")
        return True


if __name__ == "__main__":
    import traceback

    try:
        app = Gasketing()  # получаем текущие состояние linuxcnc
        app.loop()
    except KeyboardInterrupt:
        sys.exit(0)
    else:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        formatted_lines = traceback.format_exc().splitlines()
        print()
        print("**** Gasketing debugging:", formatted_lines[0])
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        print(formatted_lines[-1])
