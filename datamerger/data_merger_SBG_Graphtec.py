import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import datetime as dt
style.use('ggplot')

import tkinter as tk
import tkinter.simpledialog as tksd


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
print(filename)
graphtec = pd.read_csv(filename, skiprows=17)
filename = tk.filedialog.askopenfilename(filetypes=[('TXT','*.txt'), ('CSV','*.csv')], title='Select sbg file')
sbg = pd.read_table(filename, skiprows=[1],
                    converters={0:float, 1:str,2:str, 3:str,4:str,5:float,6:float,7:float,8:float,9:float,10:float,11:float,
                                12:float,13:float,14:float,15:float,16:float,17:float,18:float,19:float,20:float,21:float,22:float,
                                23:float,24:float,25:float,26:float,27:float,28:float, 29:float})


print('SBG')
#drop all bad columns
sbg.dropna(how='any')
print(sbg.shape)

#correct stupid floating point in the date - new sbg software
sbg['GPS Date'] = (sbg['GPS Date'].str.slice_replace(9,13,'')[:5])

#get the delta time
delta_h = tksd.askinteger("askinteger", "Enter DELTA_H", minvalue = -23, maxvalue = 23)
delta_m = tksd.askinteger("askinteger", "Enter DELTA_M", minvalue = -59, maxvalue = 59)
delta_s = tksd.askinteger("askinteger", "Enter DELTA_S", minvalue = -59, maxvalue = 59)


print(delta_h, delta_m, delta_s)


print('Graphtec hour manipulation')


wrong_dt = pd.to_datetime(graphtec['Time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

new_time = wrong_dt + (pd.to_timedelta(delta_h, unit='h') + pd.to_timedelta(delta_m, unit='m') + pd.to_timedelta(delta_s, unit='s'))
millis = graphtec['ms']

new_time += pd.to_timedelta(millis, unit='ms', errors='coerce')


graphtec['time'] = new_time


sbg['time'] = pd.to_datetime(sbg['GPS Date']+' '+sbg['    GPS Time'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')


#join values
result = sbg.append(graphtec.iloc[0:,:]).sort_values('time')

#old idea to get indexes...
#my_header_list = list(result)

#droping stuff we dont need
result = result.drop('NO.', 1)
result = result.drop('A1234567890', 1)
result = result.drop('A1234', 1)
result = result.drop('Time', 1)
result = result.drop('GPS Date', 1)
result = result.drop('    GPS Time', 1)
result = result.drop('    UTC Time', 1)
result = result.drop('UTC Date', 1)
result = result.drop('ms', 1)
result.fillna(method='pad', inplace=True)

#calculate total 2D velocity
result['tot_veloc'] = (result['North Velocity']**2+result['East Velocity']**2)**0.5*1.94384


#save file
filename = tk.filedialog.asksaveasfilename(title='Select/Type OUTPUT file', defaultextension='.csv')
root.withdraw()

result.to_csv(filename)
print('Done')

