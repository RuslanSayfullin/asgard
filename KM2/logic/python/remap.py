#!/usr/bin/python
#-*- coding: utf-8 -*-

from stdglue import cycle_prolog, cycle_epilog, init_stdglue

from interpreter import *
from emccanon import MESSAGE
import hal
from math import sin, cos, atan, atan2, sqrt, pi, acos,tan

import os
import time
import csv


def set_param(self, **words):
    if not self.task:
        return INTERP_OK
    H = 5.1
    K = 10.0
    F = 5000.0
    S = 2000.0
    # h/J диаметр сопла
    # K ширина 


    for key in words:
        if key == 'j':
            H = float(words[key])
        if key == 'k':
            K = float(words[key])
        if key == 'f':
            F = float(words[key])
        if key == 's':
            S = float(words[key])

    cal_of_mass = hal.get_value("gasketing.app.cal_of_mass")
    if cal_of_mass:
        k_h = hal.get_value("gasketing.mixture.expansion-ratio")
        width = K
        # создаем пустой список
        consumption = {}
        # открываем файл с данными по расходу
        with open('tabl.csv') as File:  
            reader = csv.reader(File)
            for row in reader:
                key, value = row
                key = float(key)
                value =float(value)
                consumption[key] = value
        width_list = sorted(consumption.keys())
        print(width_list)
        print(consumption)

        if consumption.get(width) is None:
            width_left_index = None
            for i in range(len(width_list)):
                if width_list[i] < width:
                    width_left_index = i
            if width_left_index is None:
                width_right_index = 0
                width_right = width_list[width_right_index]
                consumption_right = consumption.get(width_right)
                width_consumption = (width * consumption_right)/width_right
                print("1.Width value is less than specified in the table, calculated", width_consumption)
            else:
                print((width_left_index+1)>len(width_list), width_left_index+1,len(width_list))
                if (width_left_index+1)>=len(width_list):
                    width_left = width_list[width_left_index]
                    consumption_left = consumption.get(width_left)
                    width_consumption = (width * consumption_left)/width_left
                    print("2.Width value is greater than specified in the table, calculated", width_consumption)
                else:
                    width_left = width_list[width_left_index]
                    consumption_left = consumption.get(width_left)
                    width_right_index = width_left_index+1
                    width_right = width_list[width_right_index]
                    consumption_right = consumption.get(width_right)
                    factor = atan2(consumption_right-consumption_left,width_right-width_left)
                    width_consumption = (width-width_left)*tan(factor)+consumption_left
                    print("3.The width value is in the range between the known data types, calculated",factor,factor*(180/pi),width_consumption)
        else:
            width_consumption = consumption.get(width)
            print("4.The width value is in the table and it is equal to ",width_consumption)

        hal.set_p("gasketing.app.set_mass","{}".format(width_consumption))
    else:
        k_h = -9.072706345*(10**(-6))*(K**4)+0.00092005177*(K**3)-0.03046835339*(K**2)+0.35496043816*K+0.39428520839
        k_h = k_h*(0.008317016621351*(K*K)-0.221606200469182*K+2.14809887837498)
        #k_h = 1   
        hal.set_p("gasketing.app.height","{}".format(K*0.5*k_h)) 
        hal.set_p("gasketing.app.width","{}".format(K*k_h)  ) 
        #k_d =(0.135*H+2.925)*0.43*(-0.0469*K+1.526)
        k_d = 1
        hal.set_p("gasketing.mixture.expansion-ratio-a","{}".format(k_d))

    hal.set_p("gasketing.app.feed_nom","{}".format(F)  ) 
    hal.set_p("gasketing.app.speed","{}".format(S)  )
    hal.set_p("gasketing.reset-comp.speed-mixer","{}".format(S)  )
    hal.set_p("gasketing.app.feed","{}".format(F)  )

    is_fist = hal.get_value("gasketing.app.first")
    is_sim = hal.get_value("gasketing.sim.on")
    reset_comp_timer=hal.get_value("gasketing.reset-comp.timer")#+5.5
    if is_fist and is_sim is False:
        self.execute("G64 P0.001")
        self.execute("#<FEED_NOM>={}".format(F))
        self.execute("#<FEED> = 10000")
        self.execute("#<FEED_Z> = 2500")
        self.execute("#<X_pos>= #<_hal[ui.pos.reset-x]> ")
        self.execute("#<Y_pos>= #<_hal[ui.pos.reset-y]> ")
        self.execute("#<Z_pos>= #<_hal[ui.pos.reset-z]> ")
        self.execute("#<SLEEP> = {}".format(reset_comp_timer))
        self.execute("G53 G1 Z0 F[#<FEED_Z>]")
        self.execute("G53 G1 X[#<X_pos>] Y[#<Y_pos>] F[#<FEED>]")
        self.execute("G53 G1 Z[#<Z_pos>] F[#<FEED_Z> ]")
        self.execute("M102 P1 Q[#<FEED_NOM>]")
        self.execute("G4 P[#<SLEEP>]")
        self.execute("G53 G1 Z-20 F2500")
    return INTERP_OK

def app_on(self, **words):
    if not self.task:
        return INTERP_OK
    P = 0
    for key in words:
        if key == 'p':
            P = float(words[key])
    if P == 1:
        self.execute("M62 P0          \n" )
    elif P == 2:
        self.execute("M63 P0          \n" )
    elif P == 3:
        self.execute("M64 P0          \n" )
    elif P == 4:
        self.execute("M65 P0          \n" )                
    else:
        # если не извесная число после Р то сразу выключаем нанесение
        self.execute("M65 P0          \n" )
    #M62 P- - включить цифровой выход синхронизированный с движением. Слово P определяет номер цифрового выхода.
    #M63 P- - выключить цифровой выход синхронизированный с движением. Слово P определяет номер цифрового выхода.
    #M64 P- - немедленно включить цифровой выход. Слово P определяет номер цифрового выхода.
    #M65 P- - немедленно выключить цифровой выход. Слово P определяет номер цифрового выхода.
    return INTERP_OK

