import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import datetime as dt
style.use('ggplot')

import tkinter as tk
import tkinter.simpledialog as tksd
import tkinter.filedialog


def center_window(width=300, height=200):
    # get screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # calculate position x and y coordinates
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    root.geometry('%dx%d+%d+%d' % (width, height, x, y))

#read data
#use ITPS_all_data SGB preset
root = tk.Tk()
center_window(500, 400)
print('Select GRAPHTEC file')
filename = tk.filedialog.askopenfilename(filetypes=[('CSV','*.csv')], title='Select GRAPHTEC file')
#filename = 'C:/Users/PFDR-1/Documents/171127_A139/rec3.csv'
print(filename)
graphtec = pd.read_csv(filename, skiprows=lambda x: x in [0, 1, 2, 3, 4, 5,
                                                          6, 7, 8, 9, 10,
                                                          11, 12, 13, 14, 15,
                                                          16, 18], encoding='utf-8')
filename = tk.filedialog.askopenfilename(filetypes=[('TXT','*.txt'), ('CSV','*.csv')], title='Select SBG file')
#filename = 'C:/Users/PFDR-1/Documents/171127_A139/rec3.txt'
sbg = pd.read_table(filename, skiprows=[1],
                    converters={0:float, 1:str,2:str, 3:str,4:str,5:float,6:float,7:float,8:float,9:float,10:float,11:float,
                                12:float,13:float,14:float,15:float,16:float,17:float,18:float,19:float,20:float,21:float,22:float,
                                23:float,24:float,25:float,26:float,27:float,28:float, 29:float})


print('SBG')
#drop all bad columns
sbg.dropna(how='any')
print(sbg.shape)

#ask percentage of initial time to use to calculate average
init_percent_slice = tksd.askinteger("askinteger", "Enter percentage of initial data to use in average:", minvalue = 0, maxvalue = 100 )
#init_percent_slice = 0.01

print('SBG - Calculating first ', init_percent_slice*100, '% of data averages for pitch and roll')
print()

print('before')
print('Pitch: ',sbg['Pitch'][0:5], 'Roll', sbg['Roll'][0:5])

if init_percent_slice > 0:
	pitch_zero_average = (np.average(sbg['Pitch'][0:int(len(sbg['Pitch'])*init_percent_slice)]))
	roll_zero_average = (np.average(sbg['Roll'][0:int(len(sbg['Roll'])*init_percent_slice)]))
	sbg['Pitch'] = sbg['Pitch'] - pitch_zero_average
	sbg['Roll'] = sbg['Roll'] - roll_zero_average

print('after')
print('Pitch: ',sbg['Pitch'][0:5], 'Roll', sbg['Roll'][0:5])

print('S raw before slice',sbg['GPS Date'][0])
#correct STUPID stupid floating point in the date - new sbg software
sbg['GPS Date'] = (sbg['GPS Date'].str.split('.').str.get(0))

print('S raw after slice',sbg['GPS Date'][0])
#get the delta time
delta_h = tksd.askinteger("askinteger", "Enter DELTA_H", minvalue = -23, maxvalue = 23)
delta_m = tksd.askinteger("askinteger", "Enter DELTA_M", minvalue = -59, maxvalue = 59)
delta_s = tksd.askinteger("askinteger", "Enter DELTA_S", minvalue = -59, maxvalue = 59)
delta_ms = tksd.askinteger("askinteger", "Enter DELTA_Milli_S", minvalue = -999, maxvalue = 999)


print(delta_h, delta_m, delta_s, delta_ms)


print('Graphtec hour manipulation')

print()
wrong_dt = pd.to_datetime(graphtec['Date&Time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
print('Graphtec start time before anything',wrong_dt.head(1))
print('Graphtec end time', wrong_dt.tail(1))
new_time = wrong_dt + pd.to_timedelta(delta_ms, unit='ms')+ pd.to_timedelta(delta_s, unit='s')+ pd.to_timedelta(delta_m, unit='m')+ pd.to_timedelta(delta_h, unit='h')
#new_time = wrong_dt + (pd.to_timedelta(delta_h, unit='h') + pd.to_timedelta(delta_m, unit='m') + pd.to_timedelta(delta_s, unit='s')+
#                                                                                                                 pd.to_timedelta(delta_ms, unit='ms'))
millis = graphtec['ms']
print('Graphtec time after adding deltas',new_time.head(1))
new_time += pd.to_timedelta(millis, unit='ms', errors='coerce')
print('G time after millis',new_time.head(1))

graphtec['time'] = new_time

print('SBG raw time',sbg['GPS Date'][0], sbg['    GPS Time'][0])

sbg['time'] = pd.to_datetime(sbg['GPS Date']+' '+sbg['    GPS Time'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
print('SBG time after format',sbg['time'][0])
print('SBG end time after format',sbg['time'].tail(1))

#join values
result = sbg.append(graphtec.iloc[0:,:]).sort_values('time')

#old idea to get indexes...
#my_header_list = list(result)

#droping stuff we dont need
result = result.drop('Number', 1)
result = result.drop('Alarm1-10', 1)
result = result.drop('AlarmOut', 1)
result = result.drop('Date&Time', 1)
result = result.drop('GPS Date', 1)
result = result.drop('    GPS Time', 1)
result = result.drop('    UTC Time', 1)
result = result.drop('UTC Date', 1)
result = result.drop('ms', 1)
result = result.drop('Time Stamp', 1)
#first, pad forward with last value
result.fillna(method='pad', inplace=True)
#second, fill backwards so that veusz can cope...
result.fillna(0, inplace=True)

#calculate total 2D velocity
result['tot_veloc'] = (result['North Velocity']**2+result['East Velocity']**2)**0.5*1.94384


#save file
filename = tk.filedialog.asksaveasfilename(title='Select/Type OUTPUT file', defaultextension='.csv')
#filename = 'C:/Users/PFDR-1/Documents/171127_A139/rec3_out.csv'
root.withdraw()

result.to_csv(filename)
print('Done')

