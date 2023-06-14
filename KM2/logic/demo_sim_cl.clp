_FILES_CLASSICLADDER
_FILE-ioconf.csv
#VER=1.0
_/FILE-ioconf.csv
_FILE-monostables.csv
1,10
1,20
_/FILE-monostables.csv
_FILE-sections.csv
#VER=1.0
#NAME000=Prog1
000,0,-1,1,2,0
_/FILE-sections.csv
_FILE-general.txt
PERIODIC_REFRESH=1
SIZE_NBR_RUNGS=12
SIZE_NBR_BITS=20
SIZE_NBR_WORDS=4
SIZE_NBR_TIMERS=20
SIZE_NBR_MONOSTABLES=2
SIZE_NBR_COUNTERS=10
SIZE_NBR_TIMERS_IEC=10
SIZE_NBR_PHYS_INPUTS=15
SIZE_NBR_PHYS_OUTPUTS=30
SIZE_NBR_ARITHM_EXPR=4
SIZE_NBR_SECTIONS=4
SIZE_NBR_SYMBOLS=161
_/FILE-general.txt
_FILE-com_params.txt
MODBUS_MASTER_SERIAL_PORT=
MODBUS_MASTER_SERIAL_SPEED=9600
MODBUS_MASTER_SERIAL_DATABITS=8
MODBUS_MASTER_SERIAL_STOPBITS=1
MODBUS_MASTER_SERIAL_PARITY=0
MODBUS_ELEMENT_OFFSET=0
MODBUS_MASTER_SERIAL_USE_RTS_TO_SEND=0
MODBUS_MASTER_TIME_INTER_FRAME=100
MODBUS_MASTER_TIME_OUT_RECEIPT=500
MODBUS_MASTER_TIME_AFTER_TRANSMIT=0
MODBUS_DEBUG_LEVEL=0
MODBUS_MAP_COIL_READ=0
MODBUS_MAP_COIL_WRITE=0
MODBUS_MAP_INPUT=0
MODBUS_MAP_HOLDING=0
MODBUS_MAP_REGISTER_READ=0
MODBUS_MAP_REGISTER_WRITE=0
_/FILE-com_params.txt
_FILE-rung_6.csv
#VER=2.0
#LABEL=
#COMMENT=
#PREVRUNG=3
#NEXTRUNG=2
0-0-50/6 , 0-0-50/9 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/2
1-0-0/1 , 1-0-50/8 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 52-0-0/3
0-0-60/3 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 53-1-0/1
1-0-0/3 , 2-0-50/8 , 9-0-0/0 , 9-0-0/0 , 9-0-50/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 52-0-0/4
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 53-1-0/3
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 53-1-0/1
_/FILE-rung_6.csv
_FILE-timers.csv
1,10
1,20
0,20
2,1
2,5
1,0
1,0
1,0
1,0
1,0
1,0
1,0
1,0
1,0
1,0
1,0
1,0
1,0
1,0
1,0
_/FILE-timers.csv
_FILE-rung_5.csv
#VER=2.0
#LABEL=
#COMMENT=
#PREVRUNG=1
#NEXTRUNG=4
1-0-50/6 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 50-0-0/2
1-0-50/7 , 0-1-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
1-0-50/4 , 0-1-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
1-0-0/4 , 9-0-0/0 , 1-0-50/6 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 50-0-60/9
0-0-0/0 , 0-0-0/0 , 1-1-50/7 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 50-0-60/12
0-0-0/0 , 0-0-0/0 , 1-1-50/4 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 50-0-60/13
_/FILE-rung_5.csv
_FILE-symbols.csv
#VER=1.0
%I0,GUI-E,
%I1,EXT-E,
%I2,E-RESET,
%I3,Lube_on,no signal connected
%I4,m_fault,
%I5,gui_reset,
%I6,a_fault,
%I7,b_fault,
%I8,flush_on,
%I9,m_is_on,
%Q0,EMC-E,
%Q1,toggle,
%Q2,Lube_low,
%Q3,abort,
%Q4,gask_stop,
%Q5,flushing,
%Q6,m_min_s,
%Q7,mix_a_off,
%Q8,rec_a_on,
%Q9,a_err,
%T0,timer,Time lube pump is on
%T1,Time-off,Time lube pump is off
%T2,Time-warn,Time before low lube warning
%B0,reset,reset off timer
%B1,fault_inn,
%B2,fault,
%B3,wait_flus,
%B4,error,
%B5,%B5,
%B6,%B6,
%B7,%B7,
%B8,%B8,
%B9,%B9,
%B10,%B10,
%B11,%B11,
%B12,%B12,
%B13,%B13,
%B14,%B14,
%B15,%B15,
%B16,%B16,
%B17,%B17,
%B18,%B18,
%B19,%B19,
%W0,%W0,
%W1,%W1,
%W2,%W2,
%W3,%W3,
%IW0,%IW0,
%IW1,%IW1,
%IW2,%IW2,
%IW3,%IW3,
%IW4,%IW4,
%IW5,%IW5,
%IW6,%IW6,
%IW7,%IW7,
%IW8,%IW8,
%IW9,%IW9,
%QW0,%QW0,
%QW1,%QW1,
%QW2,%QW2,
%QW3,%QW3,
%QW4,%QW4,
%QW5,%QW5,
%QW6,%QW6,
%QW7,%QW7,
%QW8,%QW8,
%QW9,%QW9,
%IF0,%IF0,
%IF1,%IF1,
%IF2,%IF2,
%IF3,%IF3,
%IF4,%IF4,
%IF5,%IF5,
%IF6,%IF6,
%IF7,%IF7,
%IF8,%IF8,
%IF9,%IF9,
%QF0,%QF0,
%QF1,%QF1,
%QF2,%QF2,
%QF3,%QF3,
%QF4,%QF4,
%QF5,%QF5,
%QF6,%QF6,
%QF7,%QF7,
%QF8,%QF8,
%QF9,%QF9,
%T3,%T3,Old Timer
%T4,%T4,Old Timer
%TM0,%TM0,New Timer
%TM1,%TM1,New Timer
%TM2,%TM2,New Timer
%TM3,%TM3,New Timer
%TM4,%TM4,New Timer
%TM5,%TM5,New Timer
%TM6,%TM6,New Timer
%TM7,%TM7,New Timer
%TM8,%TM8,New Timer
%TM9,%TM9,New Timer
%M0,%M0,One-shot
%M1,%M1,One-shot
%C0,%C0,Counter
%C1,%C1,Counter
%C2,%C2,Counter
%C3,%C3,Counter
%C4,%C4,Counter
%C5,%C5,Counter
%C6,%C6,Counter
%C7,%C7,Counter
%C8,%C8,Counter
%C9,%C9,Counter
%E0,%E0,Error Flag Bit
%E1,%E1,Error Flag Bit
%E2,%E2,Error Flag Bit
%E3,%E3,Error Flag Bit
%E4,%E4,Error Flag Bit
%E5,%E5,Error Flag Bit
%E6,%E6,Error Flag Bit
%E7,%E7,Error Flag Bit
%E8,%E8,Error Flag Bit
%E9,%E9,Error Flag Bit
%I10,%I10,
%I11,%I11,
%I12,%I12,
%I13,%I13,
%I14,%I14,
%Q10,rec_b_on,
%Q11,rec_b_off,
%Q12,b_err,
%Q13,m_err,
%Q14,%Q14,
%Q15,%Q15,
%Q16,%Q16,
%Q17,%Q17,
%Q18,%Q18,
%Q19,%Q19,
%Q20,%Q20,
%Q21,%Q21,
%Q22,%Q22,
%Q23,%Q23,
%Q24,%Q24,
%Q25,%Q25,
%Q26,%Q26,
%Q27,%Q27,
%Q28,%Q28,
%Q29,%Q29,
%T5,%T5,Old Timer
%T6,%T6,Old Timer
%T7,%T7,Old Timer
%T8,%T8,Old Timer
%T9,%T9,Old Timer
%T10,%T10,Old Timer
%T11,%T11,Old Timer
%T12,%T12,Old Timer
%T13,%T13,Old Timer
%T14,%T14,Old Timer
%T15,%T15,Old Timer
%T16,%T16,Old Timer
%T17,%T17,Old Timer
%T18,%T18,Old Timer
%T19,%T19,Old Timer
_/FILE-symbols.csv
_FILE-rung_4.csv
#VER=2.0
#LABEL=
#COMMENT=
#PREVRUNG=5
#NEXTRUNG=3
2-0-0/2 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 53-0-0/4
1-0-0/2 , 2-0-50/9 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 50-0-0/4
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
_/FILE-rung_4.csv
_FILE-rung_3.csv
#VER=2.0
#LABEL=
#COMMENT=pump_faults
#PREVRUNG=4
#NEXTRUNG=6
1-0-0/2 , 1-0-50/9 , 2-0-50/8 , 2-0-0/1 , 9-0-0/0 , 99-0-0/0 , 13-0-0/1 , 9-0-0/0 , 9-0-0/0 , 52-0-60/3
0-0-60/3 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 99-0-0/0 , 99-0-0/0 , 0-0-0/0 , 0-0-0/0 , 52-1-60/4
1-0-60/3 , 9-0-50/0 , 9-0-0/0 , 9-0-50/0 , 9-0-0/0 , 99-0-0/0 , 13-0-0/0 , 9-0-50/0 , 0-0-0/0 , 50-1-60/5
0-0-50/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 99-0-0/0 , 99-0-50/1 , 0-0-0/0 , 9-1-0/0 , 53-0-60/3
0-0-50/6 , 0-0-50/0 , 0-0-0/0 , 0-0-50/1 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 9-1-0/0 , 53-0-60/4
0-0-50/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 9-1-0/0 , 52-0-0/1
_/FILE-rung_3.csv
_FILE-rung_2.csv
#VER=2.0
#LABEL=
#COMMENT=Intermittent Lube
#PREVRUNG=6
#NEXTRUNG=-1
9-0-0/0 , 1-0-50/3 , 2-0-0/0 , 99-0-0/0 , 10-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 53-0-60/1
0-0-0/0 , 0-0-0/0 , 0-1-0/0 , 99-1-0/0 , 99-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 52-0-60/1
0-0-0/0 , 0-0-0/0 , 2-1-60/1 , 9-0-0/0 , 9-0-0/0 , 99-0-0/0 , 10-0-0/1 , 0-0-60/0 , 0-0-0/0 , 0-0-0/0
0-0-0/0 , 0-0-0/0 , 0-1-0/0 , 0-0-0/0 , 0-0-0/0 , 99-1-0/0 , 99-0-0/0 , 9-0-0/0 , 9-0-0/0 , 50-0-0/0
0-0-0/0 , 0-0-0/0 , 1-1-50/4 , 99-0-0/0 , 10-0-0/2 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-60/9
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 99-1-0/0 , 99-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 50-0-60/2
_/FILE-rung_2.csv
_FILE-sequential.csv
#VER=1.0
_/FILE-sequential.csv
_FILE-counters.csv
0
0
0
0
0
0
0
0
0
0
_/FILE-counters.csv
_FILE-modbusioconf.csv
#VER=1.0
_/FILE-modbusioconf.csv
_FILE-rung_0.csv
#VER=2.0
#LABEL=
#COMMENT=
#PREVRUNG=0
#NEXTRUNG=1
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
_/FILE-rung_0.csv
_FILE-rung_1.csv
#VER=2.0
#LABEL=Rung 1
#COMMENT=Stepper Estop Chain
#PREVRUNG=0
#NEXTRUNG=5
0-0-50/0 , 1-0-50/0 , 9-0-50/0 , 9-0-50/1 , 9-0-0/0 , 9-0-0/0 , 9-0-60/0 , 9-0-0/0 , 9-0-0/0 , 50-0-60/0
0-0-0/0 , 2-0-50/1 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-50/2 , 9-0-0/0 , 9-0-0/0 , 0-1-60/1
0-0-50/0 , 1-0-50/0 , 2-0-50/1 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/1 , 9-0-0/0 , 0-1-60/1
9-0-0/0 , 1-0-50/0 , 2-0-50/1 , 1-0-60/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 9-0-0/0 , 0-1-0/0
0-0-60/1 , 0-0-0/0 , 0-0-0/0 , 1-1-50/2 , 0-1-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-60/6
0-0-0/0 , 0-0-0/2 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0 , 0-0-0/0
_/FILE-rung_1.csv
_FILE-timers_iec.csv
2,1,0
1,1,0
2,5,1
2,5,1
2,5,1
2,5,1
2,5,1
2,5,1
1,0,0
1,0,0
_/FILE-timers_iec.csv
_FILE-arithmetic_expressions.csv
#VER=2.0
_/FILE-arithmetic_expressions.csv
_/FILES_CLASSICLADDER
