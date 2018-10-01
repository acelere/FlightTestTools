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



root = tk.Tk()
center_window(500, 400)
print('Select GRAPHTEC file')
filename = tk.filedialog.askopenfilename(filetypes=[('CSV','*.csv')], title='Select GRAPHTEC file')
print(filename)
graphtec = pd.read_csv(filename, skiprows=16)
filename = tk.filedialog.askopenfilename(filetypes=[('TXT','*.txt'), ('CSV','*.csv')], title='Select BGS file')
bgs = pd.read_table(filename, skiprows=[1],
                    converters={0:str, 1:str,2:float,3:float,4:float,5:float,6:float,7:float,8:float,9:float,10:float,11:float,
                                12:float,13:float,14:float,15:float,16:float,17:float,18:float,19:float,20:float,21:float,22:float})

print('BGS')

delta_h = tksd.askinteger("askinteger", "Enter DELTA_H", minvalue = -23, maxvalue = 23)
delta_m = tksd.askinteger("askinteger", "Enter DELTA_M", minvalue = -59, maxvalue = 59)
delta_s = tksd.askinteger("askinteger", "Enter DELTA_S", minvalue = -59, maxvalue = 59)


print(delta_h, delta_m, delta_s)


print('Graphtec hour manipulation')
print('Initial time at GRAPHTEC file:    ', graphtec.iloc[1,1])

wrong_dt = pd.to_datetime(graphtec.iloc[:,1], format='%Y-%m-%d %H:%M:%S', errors='coerce')

new_time = wrong_dt + (pd.to_timedelta(delta_h, unit='h') + pd.to_timedelta(delta_m, unit='m') + pd.to_timedelta(delta_s, unit='s'))
millis = graphtec.loc[:,'ms']
millis = millis[1:].apply(int) #needs to start from row#1 because row#0 is text
#print(millis.head())
new_time += pd.to_timedelta(millis, unit='ms', errors='coerce')

print('Corrected time for GRAPHTEC file: ', new_time.iloc[1])


#graphtec['NewTime'] = new_time
graphtec['veusz_time'] = new_time
#print(graphtec.loc[0:5,'NewTime'])

bgs['veusz_time'] = pd.to_datetime(bgs.iloc[:,1]+' '+bgs.iloc[:,0], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')

result = bgs.append(graphtec.iloc[1:,:]).sort_values('veusz_time')
#result['test_date_format'] = result['veusz_time'].apply(lambda x: dt.datetime.strftime(x, '%y/%m/%d %H:%M:%S.%f'))



##veusz_time = orig_t
##for i in range(1,len(orig_t)):
##    veusz_time[i] = orig_t[i][8:10]+'/'+orig_t[i][5:7]+'/'+orig_t[i][2:4]+' '+orig_t[i][11:]
##
##result['veusz_time'] = veusz_time


my_header_list = list(result)
result = result.drop(my_header_list[0], 1)
result = result.drop('Alarm1-10', 1)
result = result.drop('AlarmOut', 1)
result = result.drop('Date&Time', 1)
result = result.drop('GPS Date', 1)
result = result.drop('ms', 1)
#result = result.drop('NewTime', 1)
result.fillna(method='pad', inplace=True)
result = result.drop([0], 0)
result = result.drop([1], 0)
result['tot_veloc'] = (result['North Velocity']**2+result['East Velocity']**2)**0.5*1.94384

filename = tk.filedialog.asksaveasfilename(title='Select/Type OUTPUT file', defaultextension='.csv')
root.withdraw()

result.to_csv(filename)

#print(result.head())
