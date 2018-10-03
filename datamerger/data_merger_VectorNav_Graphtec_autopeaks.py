# base code derived from: https://pythonprogramming.net/tkinter-depth-tutorial-making-actual-program/
# The code for changing pages was derived from: http://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
# License: http://creativecommons.org/licenses/by-sa/3.0/

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt

import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog as tksd
import tkinter.filedialog

import sys
sys.path.insert(1, r'./functions')  # add to pythonpath
from detect_peaks import detect_peaks

LARGE_FONT= ("Verdana", 12)


class FTISyncApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "Graphtec/INS Data Merge")
        
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        

        self.frames = {}

        frame = StartPage(container, self)
        self.frames[StartPage] = frame
        frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)
        


    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()
        


class StartPage(tk.Frame):
    ''' This class is the place holder for the main page interface
    '''
    
    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        label = tk.Label(self, text="Select EACH step below, in order", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button = ttk.Button(self, text="Select Graphtec file",
                            command=self.getGraphtecFile)
        button.pack()
        self.graphtecExists = False

        button2 = ttk.Button(self, text="Select INS file",
                            command=self.getINSFile)
        button2.pack()
        self.INSExists = False

        button3 = ttk.Button(self, text="Detect Peaks",
                            command=self.detectPeaks)
        button3.pack()


        button4 = ttk.Button(self, text="Accept",
                            command=self.saveValues)
        button4.pack()


        button5 = ttk.Button(self, text="Manual Time Delta",
                            command=self.manualDelta)
        button5.pack()

        self.saveOKPeaks = False
        self.saveOKManual = False
        self.figInit = False

        self.delta_h = 0
        self.delta_m = 0
        self.delta_s = 0
        self.delta_ms = 0
        


    def updatePlot(self, gr_plt_data, vn_plt_data):
        '''data in:
            gr_plt_data: pandas dataframe that contains the graphtec FILTERED data for the graph
            vn_plt_data: same thing for the vectornav
        '''

        if self.figInit == True:
            self.a.clear()
            self.b.clear()

        else:
            self.f = Figure(figsize=(8,5), dpi=100)
            self.a = self.f.add_subplot(211)
            self.a.set_ylabel('Graphtec Event')
            self.b = self.f.add_subplot(212)
            self.b.set_ylabel('VN Z Accel')
            self.figInit = True
            self.canvas = FigureCanvasTkAgg(self.f, self)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

            self.toolbar = NavigationToolbar2Tk(self.canvas, self)
            self.toolbar.update()
            self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.a.plot(gr_plt_data.index.values, gr_plt_data['CH8'].values, 'o-')
        self.b.plot(vn_plt_data.index.values, vn_plt_data['Acceleration.Z'].values, '.-')
        self.canvas.draw()    




    def getGraphtecFile(self):
        '''
        read the Graphtec csv file
        get rid of lines as listed in skiprows below
        '''

        filename = tk.filedialog.askopenfilename(filetypes=[('CSV','*.csv')], title='Select GRAPHTEC file')

        print(filename)
        self.graphtec = pd.read_csv(filename, skiprows=lambda x: x in [0, 1, 2, 3, 4, 5,
                                                          6, 7, 8, 9, 10,
                                                          11, 12, 13, 14, 15,
                                                          16, 18], encoding='utf-8')


        self.wrong_dt = pd.to_datetime(self.graphtec['Date&Time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        millis = self.graphtec['ms']

        self.wrong_dt += pd.to_timedelta(millis, unit='ms', errors='coerce')
        self.graphtec['wrong_dt'] = self.wrong_dt
        
        #calculate the differential of the event signal
        # for peak detection
        self.graphtec['CH8_diff'] = self.graphtec['CH8'].diff()

        print('Graphtec file loaded')

        self.graphtecExists = True

    def getINSFile(self):

        filename = tk.filedialog.askopenfilename(filetypes=[('TXT','*.txt'), ('CSV','*.csv')], title='Select VECTORNAV file')

        print('Reading INS file...')
        self.vn_raw = pd.read_table(filename, skiprows=[1], sep='\t', converters={0:str, 1:lambda x: float(x or 0)})
        #dropping excess columns first


        for column in self.vn_raw.columns.values:
            splitted = column.split(' (')

            self.vn_raw.rename({column:splitted[0]}, axis='columns', inplace=True)

        rows_to_remove = ['Dcm00', 
        'Dcm01', 
        'Dcm02', 
        'Dcm10', 
        'Dcm11', 
        'Dcm12', 
        'Dcm20', 
        'Dcm21', 
        'Dcm22', 
        'YawPitchRollUncertainty.X', 
        'YawPitchRollUncertainty.Y', 
        'YawPitchRollUncertainty.Z', 
        'UncompensatedAcceleration.X', 
        'UncompensatedAcceleration.Y', 
        'UncompensatedAcceleration.Z', 
        'UncompensatedMagnetic.X', 
        'UncompensatedMagnetic.Y', 
        'UncompensatedMagnetic.Z', 
        'UncompensatedAngularRate.X', 
        'UncompensatedAngularRate.Y', 
        'UncompensatedAngularRate.Z', 
        'EstimatedPositionEcef.X', 
        'EstimatedPositionEcef.Y', 
        'EstimatedPositionEcef.Z', 
        'EstimatedVelocityBody.X', 
        'EstimatedVelocityBody.Y', 
        'EstimatedVelocityBody.Z', 
        'EstimatedVelocityEcef.X', 
        'EstimatedVelocityEcef.Y', 
        'EstimatedVelocityEcef.Z', 
        'EstimatedPositionUncertainty', 
        'EstimatedVelocityUncertainty', 
        'GpsTow', 
        'GpsTowNs', 
        'GpsWeek', 
        'GpsPositionEcef.X', 
        'GpsPositionEcef.Y', 
        'GpsPosition.Z', 
        'GpsVelocityEcef.X', 
        'GpsVelocityEcef.Y', 
        'GpsVelocityEcef.Z', 
        'GpsTimeUncertainty', 
        'ImuStatus', 
        'VpeStatus', 
        'TimeSyncIn', 
        'SyncInCount', 
        'DeltaTime', 
        'DeltaTheta.X', 
        'DeltaTheta.Y', 
        'DeltaTheta.Z', 
        'DeltaVelocity.X', 
        'DeltaVelocity.Y', 
        'DeltaVelocity.Z', 
        'TimeGpsPps', 
        'TimeUtc', 
        'LinearAccelerationBody.X', 
        'LinearAccelerationBody.Y', 
        'LinearAccelerationBody.Z', 
        'LinearAccelerationNed.X', 
        'LinearAccelerationNed.Y', 
        'LinearAccelerationNed.Z', 
        'AccelerationEcef.X', 
        'AccelerationEcef.Y', 
        'AccelerationEcef.Z', 
        'LinearAccelerationEcef.X', 
        'LinearAccelerationEcef.Y', 
        'LinearAccelerationEcef.Z', 
        'MagneticNed.X', 
        'MagneticNed.Y', 
        'MagneticNed.Z', 
        'MagneticEcef.X', 
        'MagneticEcef.Y', 
        'MagneticEcef.Z', 
        'GpsPositionAccuracyEcef.X', 
        'GpsPositionAccuracyEcef.Y', 
        'GpsPositionAccuracyEcef.Z', 
        'EstimatedAttitudeUncertainty', 
        'Quaternion.X', 
        'Quaternion.Y', 
        'Quaternion.Z', 
        'Quaternion.W', 
        'EstimatedPositionLla.Latitude', 
        'EstimatedPositionLla.Longitude', 
        'EstimatedPositionLla.Altitude', 
        'GpsTimestampLocalTime', 
        'GpsPositionUncertainty.X', 
        'GpsPositionUncertainty.Y', 
        'GpsPositionUncertainty.Z', 
        'GpsVelocityUncertainty', 
        'SensorSaturation']

        for row in rows_to_remove:
            self.vn_raw.drop(row, 1, inplace=True)


        # since the dataset is duplicated (I do not know why), I am getting rid of duplicates by direct index
        self.vn_clean = self.vn_raw.iloc[:, [j for j, c in enumerate(self.vn_raw.columns) if j < 37]].copy()

        # padding the file to fill voids before merging
        self.vn_clean.fillna(method='pad', inplace=True)

        #vectornav timestamp
        self.vn_clean['time'] = pd.to_datetime(self.vn_clean['Timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

        #calculate the differential of the z accel signal
        # for peak detection
        self.vn_clean['Acceleration.Z_diff'] = self.vn_clean['Acceleration.Z'].diff()

        print('VectorNav file loaded')
        
        self.INSExists = True

    def search_peaks(self):
        '''this function will detect the peaks and return the timedelta
        '''
        peaks_not_detected = True
        user_cancelled = False

        while (peaks_not_detected and not user_cancelled):
            print()
            print()
            print('input GRAPHTEC peak threshold')
            graphtec_mph = tksd.askfloat("Input", "Enter GRAPHTEC peak threshold", minvalue = 0.0001, maxvalue = 5.0)
            if graphtec_mph:

                print()
                print()
                print('input VectorNav peak threshold')
                #get the threshold
                vn_mph = tksd.askfloat("Input", "Enter VectorNav peak threshold", minvalue = 0.0001, maxvalue = 50.0)
                if vn_mph:
                    peaks = detect_peaks(self.graphtec['CH8_diff'].values, mph=graphtec_mph)          

                    peaks2 = detect_peaks(self.vn_clean['Acceleration.Z_diff'].values, mph=vn_mph)
                    if len(peaks)==0:
                        print('Graphtec peaks not detectd - choose a lower threshold')
                    if len(peaks2)==0:
                        print('VectorNav peaks not detectd - choose a lower threshold')
                    if (len(peaks)>0) and (len(peaks2)>0):
                        print('peaks found')
                        peaks_not_detected = False
                else:
                    user_cancelled = True
            else:
                user_cancelled = True
        if user_cancelled == False:
            
            print('Graphtec initial timestamp: {}'.format(self.graphtec['wrong_dt'].iloc[0]))
            print('Graphtec peak detected at: {}'.format(self.graphtec['wrong_dt'].iloc[peaks[0]]))
            print('VectorNav initial timestamp: {}'.format(self.vn_clean['time'].iloc[0]))
            print('VectorNav peak detected at: {}'.format(self.vn_clean['time'].iloc[peaks2[0]]))
            print()

            dt_window = 2 # plus or minus seconds around found peak
            
            delta_time = self.graphtec['wrong_dt'].iloc[peaks[0]]-self.vn_clean['time'].iloc[peaks2[0]]
            print()
            gr_plt_data = self.graphtec[(self.graphtec['wrong_dt'] > (self.graphtec['wrong_dt'].iloc[peaks[0]]-pd.Timedelta(seconds=2))) &
                  (self.graphtec['wrong_dt'] < (self.graphtec['wrong_dt'].iloc[peaks[0]]+pd.Timedelta(seconds=2)))]

            vn_plt_data = self.vn_clean[(self.vn_clean['time'] > (self.vn_clean['time'].iloc[peaks2[0]]-pd.Timedelta(seconds=2))) &
                  (self.vn_clean['time'] < (self.vn_clean['time'].iloc[peaks2[0]]+pd.Timedelta(seconds=2)))]

            return peaks, peaks2, gr_plt_data, vn_plt_data, delta_time
        else:
            return [np.array(None), np.array(None), np.array(None), np.array(None), np.array(None)]



    def detectPeaks(self):
        #start timestamp manipulation

        if not self.graphtecExists:
            self.popupmsg('Select Graphtec file first')
        elif not self.INSExists:
            self.popupmsg('Select INS file first')
        else:

            self.gr_peaks, self.vn_peaks, self.gr_data, self.vn_data, self.deltat = self.search_peaks()
            if self.gr_peaks.all():

                print('Delta is: {}'.format(self.deltat))
                print('finished peaks routine')
                
                self.saveOKPeaks = True
                self.updatePlot(self.gr_data, self.vn_data)

    def manualDelta(self):
        if not self.graphtecExists:
            self.popupmsg('Select Graphtec file first')
        elif not self.INSExists:
            self.popupmsg('Select INS file first')
        else:
            self.delta_h = tksd.askinteger("askinteger", "Enter DELTA_H", minvalue = -23, maxvalue = 23)
            self.delta_m = tksd.askinteger("askinteger", "Enter DELTA_M", minvalue = -59, maxvalue = 59)
            self.delta_s = tksd.askinteger("askinteger", "Enter DELTA_S", minvalue = -59, maxvalue = 59)
            self.delta_ms = tksd.askinteger("askinteger", "Enter DELTA_MilliS", minvalue = -1000, maxvalue = 1000)


            print('Deltas: {} hours, {} minutes, {} seconds and {} milliseconds'. format(self.delta_h, self.delta_m, self.delta_s, self.delta_ms))
            self.saveOKManual = True


    def saveValues(self):

        print('Peaks', self.saveOKPeaks, ' Manual ', self.saveOKManual, ' or ', (self.saveOKPeaks == True or self.saveOKManual == True))
        if self.saveOKPeaks == True:
            print('Saving data using detected peaks for synchronism')
            new_time = self.wrong_dt - (self.graphtec['wrong_dt'].iloc[self.gr_peaks[0]]-self.vn_clean['time'].iloc[self.vn_peaks[0]])
        elif self.saveOKManual == True:
            new_time = self.wrong_dt + (pd.to_timedelta(self.delta_h, unit='h') + pd.to_timedelta(self.delta_m, unit='m') +
                                        pd.to_timedelta(self.delta_s, unit='s') + pd.to_timedelta(self.delta_ms, unit='ms'))
            print('Saving data using manual deltas for synchronism')
        else:
            self.popupmsg('Detect peak or enter deltas manually first')

        if ((self.saveOKPeaks == True) or (self.saveOKManual == True)):
            self.graphtec['time'] = new_time
        
            #join values
            result = self.vn_clean.append(self.graphtec.iloc[0:,:], sort=True).sort_values(by=['time'])

            #droping stuff we dont need
            ##result = result.drop('Number', 1)
            result = result.drop('Alarm1-10', 1)
            result = result.drop('AlarmOut', 1)
            result = result.drop('Date&Time', 1)

            result = result.drop('ms', 1)

            result = result.drop('Timestamp', 1)
            result = result.drop('wrong_dt', 1)
            #result = result.drop('CH8_diff', 1)
            #result = result.drop('Acceleration.Z_diff', 1)
            
            #first, pad forward with last value
            result.fillna(method='pad', inplace=True)
            
            #second, fill backwards so that veusz can cope...
            result.fillna(0, inplace=True)

            #calculate total 2D velocity
            result['tot_veloc'] = (result['EstimatedVelocityNed.X']**2+result['EstimatedVelocityNed.Y']**2)**0.5*1.94384

            #save file
            filename = tk.filedialog.asksaveasfilename(title='Select/Type OUTPUT file', defaultextension='.csv')

            result.to_csv(filename)
            print('Done')
        


    def popupmsg(self, msg):
        popup = tk.Tk()
        popup.wm_title("!")
        label = ttk.Label(popup, text=msg, font=("Helvetica", 10))
        label.pack(side="top", fill="x", pady=10)
        B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
        B1.pack()
        popup.mainloop()
 
        

app = FTISyncApp()
app.mainloop()
