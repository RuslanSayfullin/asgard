# -*- coding: utf-8 -*-

from math import cos, sin, pi
import numpy as np
import datetime

START_STEP = 10
FINISH_STEP = 10
START_LENGTH = 19

class Cam():
    def __init__(self):
        self.seal_width = 0
        self.sealing_height = 0
        self.x_axis_offset = 0
        self.y_axis_offset = 0
        self.length = 0
        self.width = 0
        self.step_x = 0
        self.step_y = 0
        self.radius_1 = 0
        self.radius_2 = 0
        self.radius_3 = 0
        self.radius_4 = 0
        self.quantity_x = 0
        self.quantity_y = 0
        self.feed = 0
        self.speed = 0
        self.tool_number = 0
        self.tool_diam = 5
        self.file_name = "cam.ngc"
        self.file_path = "./"
        self.z_save = 50
        self.z_work = 5

    def set_parameter(self, seal_width, tool_diam,
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
                      circle_diameter):
        self.seal_width = seal_width
        self.tool_diam = tool_diam
        self.x_axis_offset = x_axis_offset
        self.y_axis_offset = y_axis_offset
        self.width = length
        self.length = width
        self.step_x = STEP_X
        self.step_y = STEP_Y
        self.radius_1 = radius_1
        self.radius_2 = radius_2
        self.radius_3 = radius_3
        self.radius_4 = radius_4
        self.quantity_x = quantity_x
        self.quantity_y = quantity_y
        self.feed = feed
        self.speed = speed
        self.tool_number = tool_number
        self.z_save = z_save
        self.z_work = z_work
        self.overlap_length = overlap_length
        self.start_length = start_length
        self.radius_circle = circle_diameter *0.5

    def draw_rectangle(self, x_pos, y_pos):
        gcode_rectangle = []
        gcode_rectangle.append("G1 Z[#<Zsave>] F{:1f}".format(2000))
        # левый нижний угол начало
        gcode_rectangle.append("(Подход к точки начала насения)")
        if self.radius_1 != 0:
            # point 1
            gcode_rectangle.append("G1 X{:5.3f}  Y[{:5.3f}+#<START_STEP>+#<START_LENGTH>]  F[#<FEED>]".format(
                x_pos,
                y_pos+self.radius_1
            ))
            gcode_rectangle.append("G1 Z[#<Zwork>] F{:1f}".format(2000))
            # point 2
            gcode_rectangle.append("G1 X{:5.3f}  Y[{:5.3f}+#<START_LENGTH>]  F[#<FEED>]".format(
                x_pos,
                y_pos+self.radius_1
            ))
            gcode_rectangle.append("M401 P1")
            # point 4           
            gcode_rectangle.append("G1 X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                x_pos,
                y_pos+self.radius_1
            ))
            # point 5            
            gcode_rectangle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
                        x_pos+self.radius_1,
                        y_pos,
                        self.radius_1
                    ))
        else:
            # point 1
            gcode_rectangle.append("G1 X{:5.3f}  Y[{:5.3f}+#<START_STEP>+#<START_LENGTH>]  F[#<FEED>]".format(
                x_pos,
                y_pos
            ))
            gcode_rectangle.append("G1 Z[#<Zwork>] F{:1f}".format(2000))
            # point 2
            gcode_rectangle.append("G1 X{:5.3f}  Y[{:5.3f}+#<START_LENGTH>]  F[#<FEED>]".format(
                x_pos,
                y_pos
            ))
            gcode_rectangle.append("M401 P1")
            # point 4
            gcode_rectangle.append("G1 X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                x_pos,
                y_pos,
            ))
        # правый нижний угол
        gcode_rectangle.append("(правый нижний угол)")
        if self.radius_2 != 0:
            gcode_rectangle.append("G1  X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                x_pos+self.length-self.radius_2,
                y_pos
            ))
            gcode_rectangle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
                x_pos+self.length,
                y_pos+self.radius_2,
                self.radius_2
            ))
        else:
            gcode_rectangle.append("G1  X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                x_pos+self.length,
                y_pos
            ))
        # правый вверхний угол
        gcode_rectangle.append("(правый вверхний угол)")
        if self.radius_3 != 0:
            gcode_rectangle.append("G1  X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                x_pos+self.length,
                y_pos+self.width-self.radius_3
            ))
            gcode_rectangle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f}F[#<FEED>]".format(
                x_pos+self.length-self.radius_3,
                y_pos+self.width,
                self.radius_3
            ))
        else:
            gcode_rectangle.append("G1  X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                x_pos+self.length,
                y_pos+self.width
            ))
        # левый вверхний угол
        gcode_rectangle.append("(левый вверхний угол)")
        if self.radius_4 != 0:
            gcode_rectangle.append("G1  X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                x_pos+self.radius_4,
                y_pos+self.width
            ))
            gcode_rectangle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
                x_pos,
                y_pos+self.width-self.radius_4,
                self.radius_3
            ))
        else:
            gcode_rectangle.append("G1  X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                x_pos,
                y_pos+self.width
            ))
        # левый нижний угол окончание
        gcode_rectangle.append("(левый нижний угол торможение)")
        if self.radius_1 != 0:
            y_3_pos = y_pos + self.radius_1 + self.start_length - self.overlap_length
            y_4_pos = y_pos + self.radius_1
            gcode_rectangle.append("(y_4_pos =  {} y_3_pos ={}) ".format(y_4_pos,y_3_pos ))

            if y_3_pos >= y_4_pos:
                # если точка окончания находится выше радиуса
                # point 3
                gcode_rectangle.append("G1 X{:5.3f}  Y[{:5.3f}+#<START_LENGTH>-#<OVERLAP_LENGTH>]  F[#<FEED>]".format(
                    x_pos,
                    y_3_pos
                ))
                gcode_rectangle.append("M401 P2")
                # point 4
                gcode_rectangle.append("G1 X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                    x_pos,
                    y_4_pos
                ))
                # point 5
                gcode_rectangle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
                    x_pos+self.radius_1,
                    y_pos,
                    self.radius_1
                ))
                # point 6
                gcode_rectangle.append("G1 X[{:5.3f}+#<FINISH_STEP>] Y{:5.3f} F[#<FEED>]".format(
                    x_pos+self.radius_1,
                    y_pos
                ))
            else:
                # если точка окончания находится радиуса
                # проверяем два условия расстояни 
                # разница между расстояними больше длины дуги 
                # или меньше радиуса 1
                delta_y43 = y_4_pos - y_3_pos
                perimeter = (2 * pi * self.radius_1) /4
                gcode_rectangle.append("(delta_y43 =  {} perimeter ={}) ".format(delta_y43,perimeter ))
                if perimeter <= delta_y43:
                    # длина дуги меньше разницы между точками значит
                    # после дуги нам нужно проехать еще дальше
                    # point 4
                    gcode_rectangle.append("G1 X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                        x_pos,
                        y_4_pos
                    ))
                    # point 5
                    gcode_rectangle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
                        x_pos+self.radius_1,
                        y_pos,
                        self.radius_1
                    ))
                    # point 3
                    temp = (delta_y43-perimeter)+self.radius_1
                    if temp < self.length/2:
                        x_3_pos = x_pos+ temp
                    else:
                        x_3_pos = x_pos+ (self.length/2)
                    gcode_rectangle.append("G1 X{:5.3f}  Y{:5.3f}  F[#<FEED>]".format(
                        x_3_pos,
                        y_pos
                    ))
                    gcode_rectangle.append("M401 P2")
                    # point 6
                    gcode_rectangle.append("G1 X[{:5.3f}+#<FINISH_STEP>] Y{:5.3f} F[#<FEED>]".format(
                        x_pos+(delta_y43-perimeter)+self.radius_1,
                        y_pos
                    ))
                else:
                    # длина дуги больше разницы между точками значит
                    # остановить подачу нужно нужно на радиусе
                    # point 4
                    gcode_rectangle.append("G1 X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                        x_pos,
                        y_4_pos
                    ))
                    # point 3
                    angle = (perimeter - delta_y43 )/self.radius_1
                    x_3_pos = x_pos+self.radius_1-self.radius_1*cos(angle)
                    y_3_pos = y_pos+self.radius_1-self.radius_1*sin(angle)
                    gcode_rectangle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
                        x_3_pos,
                        y_3_pos,
                        self.radius_1
                    ))
                    gcode_rectangle.append("M401 P2")
                    # point 5
                    gcode_rectangle.append("(point 5 {}) ".format(angle))
                    gcode_rectangle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
                        x_pos+self.radius_1,
                        y_pos,
                        self.radius_1
                    ))
                    # point 6
                    gcode_rectangle.append("G1 X[{:5.3f}+#<FINISH_STEP>] Y{:5.3f} F[#<FEED>]".format(
                        x_pos+self.radius_1,
                        y_pos
                    ))
        # если радиус равен нулю
        else:
            # point 3
            gcode_rectangle.append("G1 X{:5.3f}  Y[{:5.3f}+#<START_LENGTH>-#<OVERLAP_LENGTH>]  F[#<FEED>]".format(
                x_pos,
                y_pos
            ))            
            gcode_rectangle.append("M401 P2")
            # point 4,5
            gcode_rectangle.append("G1 X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
                x_pos,
                y_pos
            ))
            # point 6
            gcode_rectangle.append("G1 X[{:5.3f}+#<FINISH_STEP>] Y{:5.3f} F[#<FEED>]".format(
                x_pos+self.radius_1,
                y_pos
            ))
        gcode_rectangle.append("G1 Z[#<Zsave>] F{:1f}".format(2000))

        return "\n".join(gcode_rectangle)

    def create_rectangle(self, x_pos, y_pos):
        gcode_rectangle = []
        gcode_rectangle.append(
            """o<rectangle> CALL [{:5.3f}] [{:5.3f}] [{}] [{}] [{}] [{}] [{}] [{}] [{}] [{}] [{}] [{}] [{}] [{}] [{}] [{}]""".format(
            x_pos,
            y_pos,
            "#<width>",
            "#<length>",
            "#<R1>",
            "#<R2>",
            "#<R3>",
            "#<R4>",
            "#<Zsave>",
            "#<Zwork>",
            "#<FEED>",
            "#<FEED_Z>",
            "#<START_STEP>",
            "#<START_LENGTH>",
            "#<OVERLAP_LENGTH>",
            "#<FINISH_STEP>"
            ))
        return "\n".join(gcode_rectangle)

    def draw_cicle(self, x_pos, y_pos):
        gcode_cicle = []
        gcode_cicle.append("G1 Z[#<Zsave>] F{:1f}".format(2000))
        # начало разгона
        gcode_cicle.append("(начало разгона и первый сектор дуги)")
        # point 1
        gcode_cicle.append("G1 X{:5.3f} Y[{:5.3f}+#<START_STEP>] F[#<FEED>]".format(
            x_pos - self.radius_circle,
            y_pos
        ))
        gcode_cicle.append("G1 Z[#<Zwork>] F{:1f}".format(2000))
        # point 2
        gcode_cicle.append("G1 X{:5.3f} Y{:5.3f} F[#<FEED>]".format(
            x_pos - self.radius_circle,
            y_pos + 0
        ))
        # point 3

        perimeter = (2 * pi * self.radius_circle) /4
        if self.start_length <= perimeter:
            start_length_circle = self.start_length
        else:
            start_length_circle = perimeter*0.5
        temp = self._generation_for_g3(start_length_circle, self.radius_circle,0,x_pos,y_pos,"[#<FEED>]")
        gcode_cicle = gcode_cicle + temp
        gcode_cicle.append("M401 P1")
        # 1 ый сектор
        gcode_cicle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
                x_pos,
                y_pos - self.radius_circle,
                self.radius_circle
            ))
        # 2 ой сектор
        gcode_cicle.append("(2ой сектор дуги)")
        gcode_cicle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
            x_pos+self.radius_circle,
            y_pos+0,
            self.radius_circle
        ))
        # 3 ий сектор
        gcode_cicle.append("(3ой сектор дуги)")
        gcode_cicle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
            x_pos+0,
            y_pos+self.radius_circle,
            self.radius_circle
        ))
        # 4ий сектор
        gcode_cicle.append("(4ой сектор дуги)")
        gcode_cicle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
            x_pos - self.radius_circle,
            y_pos+0,
            self.radius_circle
        ))
        # торможение
        temp = self._generation_for_g3(start_length_circle + self.overlap_length , self.radius_circle,0,x_pos,y_pos,"[#<FEED>]")
        gcode_cicle = gcode_cicle + temp
        gcode_cicle.append("M401 P2")
        angle = (self.start_length + self.overlap_length +FINISH_STEP  )/self.radius_circle
        x_5_pos = x_pos-self.radius_circle*cos(angle) 
        y_5_pos = y_pos-self.radius_circle*sin(angle)
        gcode_cicle.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F[#<FEED>]".format(
            x_5_pos,
            y_5_pos,
            self.radius_circle
        ))
        gcode_cicle.append("G1 Z[#<Zsave>] F{:1f}".format(2000))

        return "\n".join(gcode_cicle)

    def _generation_for_g3(self, arc_length, arc_radius, starting_angle=0, x_center=0, y_center=0, feed=1000):
        def draw(sector,x_pos,y_pos,arc_radius,feed):
            out = []
            if sector ==1:
                out.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F{}".format(
                x_pos,
                y_pos-arc_radius,
                arc_radius,
                feed
                ))
            elif sector ==2:
                temp = draw(1,x_pos,y_pos,arc_radius,feed)
                out.extend(temp)
                out.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F{}".format(
                    x_pos+arc_radius,
                    y_pos,
                    arc_radius,
                    feed
                    ))
            elif sector ==3:
                temp = draw(2,x_pos,y_pos,arc_radius,feed)
                out.extend(temp)
                out.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F{}".format(
                    x_pos,
                    y_pos+arc_radius,
                    arc_radius,
                    feed
                    ))
            elif sector == 4:
                temp = draw(3,x_pos,y_pos,arc_radius,feed)
                out.extend(temp)
                out.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F{}".format(
                    x_pos-arc_radius,
                    y_pos,
                    arc_radius,
                    feed
                    ))
            else:
                out.append(draw(4,x_pos,y_pos,arc_radius,feed))
            return out
    
        gcode_g3 = []#
        angle = arc_length/arc_radius
        fuul_count, angle = divmod(angle , (2*pi))
        print(fuul_count, angle )
        if fuul_count >0:
            for i in range(int(fuul_count)):
                temp = draw(4,x_center,y_center,arc_radius,feed)
                gcode_g3 = gcode_g3+ temp
        if angle <= pi/2: #1 sector
            print("1 sector")
            gcode_g3.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F{}".format(
                x_center-arc_radius*cos(angle),
                y_center-arc_radius*sin(angle),
                arc_radius,
                feed
            ))
        elif angle > pi/2 and angle <= pi:  #2 sector
            print("2 sector")
            # нарисовать 1 сектора 2 уже по углу
            temp = draw(1,x_center,y_center,arc_radius,feed)
            gcode_g3 = gcode_g3 + temp

            gcode_g3.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F{}".format(
                x_center-arc_radius*cos(angle),
                y_center-arc_radius*sin(angle),
                arc_radius,
                feed
            ))
        elif angle > pi and angle <= pi*3/2:  #3 sector
            print("3 sector")
            # нарисовать 2 сектора 3 уже по углу
            temp = draw(2,x_center,y_center,arc_radius,feed)
            gcode_g3 = gcode_g3 + temp

            gcode_g3.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F{}".format(
                x_center-arc_radius*cos(angle),
                y_center-arc_radius*sin(angle),
                arc_radius,
                feed
            ))
        elif angle > pi*3/2 and angle <= pi*2:  #4 sector    
            print("4 sector")
            # нарисовать 3 сектора 4 уже по углу
            temp = draw(3,x_center,y_center,arc_radius,feed)
            gcode_g3 = gcode_g3 + temp

            gcode_g3.append("G3 X{:5.3f} Y{:5.3f} R{:5.3f} F{}".format(
                x_center-arc_radius*cos(angle),
                y_center-arc_radius*sin(angle),
                arc_radius,
                feed
            ))
        else: #заданная длина больше окружности
            print("заданная длина больше окружности")
            temp = draw(4,x_center,y_center,arc_radius,feed)
            gcode_g3 = gcode_g3+ temp
        return   gcode_g3

    def generator_gcode(self, type_cam):
        gcode = []
        now = datetime.datetime.now()

        gcode.append("(Использован скрипт автогенерации gcode системы управления ACNC)")
        gcode.append("(Программа {} сгенерирована  {})".format(self.file_name, now.strftime("%d-%m-%Y %H:%M")))
        #gcode.append("M61Q{:5.3f}".format(self.tool_number))

        gcode.append("#<Zwork> = {:5.3f}".format(self.z_work))
        gcode.append("#<Zsave> = {:5.3f}".format(self.z_save))
        gcode.append("#<FEED> = {:5.1f}".format(self.feed))

        if type_cam == 1:  # rect
            gcode.append("#<FEED_Z> = {:5.1f}".format(2000))
            gcode.append("#<START_STEP> = {:5.3f}".format(START_STEP))
            gcode.append("#<FINISH_STEP> = {:5.3f}".format(FINISH_STEP))
            gcode.append("#<START_LENGTH> = {:5.3f}".format(self.start_length))
            gcode.append("#<OVERLAP_LENGTH> = {:5.3f}".format(self.overlap_length))
            gcode.append("#<R1> = {:5.3f}".format(self.radius_1))
            gcode.append("#<R2> = {:5.3f}".format(self.radius_2))
            gcode.append("#<R3> = {:5.3f}".format(self.radius_3))
            gcode.append("#<R4> = {:5.3f}".format(self.radius_4))

            gcode.append("#<width>  = {:5.3f}".format(self.width))
            gcode.append("#<length> = {:5.3f}".format(self.length))


        if type_cam == 0:  # draw_cicle
            gcode.append("#<START_STEP> = {:5.3f}".format(START_STEP))

        gcode.append("M400J{:5.3f}K{:5.3f}F{:5.3f}S{:5.3f}".format(self.tool_diam, self.seal_width,
                                                 self.feed, self.speed ))
        gcode.append("G54 G17 G40 G49 G90 G92.1 G94 G64 P0.001")
        gcode.append("G1 Z[#<Zsave>] F{:1f}".format(2000))

        pos_x = []
        pos_x.append((self.x_axis_offset, self.y_axis_offset))
        if self.quantity_x != 0 and self.step_x != 0:
            for x_count in range(self.quantity_x-1):
                pos_x.append((pos_x[0][0] + self.step_x *
                              (x_count + 1), pos_x[0][1]+0))
        pos_xy = []
        pos_xy.append(pos_x)
        if self.quantity_y != 0 and self.step_y != 0:
            for y_count in range(self.quantity_y-1):
                temp = []
                for i in range(len(pos_x)):
                    temp.append(
                        (pos_xy[0][i][0] + 0, pos_xy[0][i][1]+self.step_y*(y_count+1)))
                pos_xy.append(temp)

        for i in range(len(pos_xy)):
            for j in range(len(pos_xy[i])):
                current_pos_x = pos_xy[i][j][0]
                current_pos_y = pos_xy[i][j][1]
                gcode.append("(Деталь #{:5.3f} {:5.3f})".format(i+1, j+1))
                if type_cam == 0:  # draw_cicle
                    temp = self.draw_cicle(current_pos_x, current_pos_y)
                if type_cam == 1:  # rect
                    temp = self.create_rectangle(current_pos_x, current_pos_y)
                gcode.append(temp)

        gcode.append("G53 G0 Z0 ")
        gcode.append("G53 G0 X0 Y0 ")

        gcode.append("M2")
        #GUI/test/gcode/test.ngc
        file = open('{}/{}'.format(self.file_path, self.file_name), 'w')
        file.write("\n".join(gcode))
        file.close()
        return "{}/{}".format(self.file_path, self.file_name)

if __name__ == '__main__':
    cam = Cam()
