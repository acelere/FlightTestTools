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

        tk.Tk.wm_title(self, "SPECIAL IADS/iLevil Data Merge")
        
        
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, PageOne, PageTwo):

            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()
        
    


class StartPage(tk.Frame):


    
    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        label = tk.Label(self, text="Select EACH step below, in order", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button = ttk.Button(self, text="Select iLevil file",
                            command=self.getGraphtecFile)
        button.pack()
        self.graphtecExists = False

        button2 = ttk.Button(self, text="Select VN file",
                            command=self.getINSFile)
        button2.pack()
        self.INSExists = False

        button3 = ttk.Button(self, text="Detect Peaks",
                            command=self.detectPeaks)
        button3.pack()


        button5 = ttk.Button(self, text="Accept",
                            command=self.saveValues)
        button5.pack()

        self.saveOK = False


        self.figInit = False
        


    def updatePlot(self, gr_plt_data, vn_plt_data):

        if self.figInit == True:
            self.a.clear()
            self.b.clear()

        else:
            self.f = Figure(figsize=(8,5), dpi=100)
            self.a = self.f.add_subplot(211)
            self.a.set_ylabel('iLevil Z Accel')
            self.b = self.f.add_subplot(212)
            self.b.set_ylabel('Acceleration.Z')
            self.figInit = True
            self.canvas = FigureCanvasTkAgg(self.f, self)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

            self.toolbar = NavigationToolbar2Tk(self.canvas, self)
            self.toolbar.update()
            self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.a.plot(gr_plt_data.index.values, gr_plt_data['ACC_Z'].values, 'o-')
        self.b.plot(vn_plt_data.index.values, vn_plt_data['Acceleration.Z'].values, '.-')
        self.canvas.draw()    





    def getGraphtecFile(self):

        filename = tk.filedialog.askopenfilename(filetypes=[('CSV','*.csv')], title='Select GRAPHTEC file')

        print(filename)
        self.graphtec = pd.read_csv(filename, skiprows=lambda x: x in [0, 1, 2, 3, 4],
                                                          encoding='utf-8')


        self.wrong_dt_pre = self.graphtec['DATE']+' '+self.graphtec['UTC_TIME']
        
        self.wrong_dt = pd.to_datetime(self.wrong_dt_pre, format='%d-%m-%Y %H:%M:%S', errors='coerce')
        millis = self.graphtec['TIMER(ms)']
        millis_diff = millis.diff()

        self.wrong_dt += pd.to_timedelta(millis_diff, unit='ms', errors='coerce')
        self.graphtec['wrong_dt'] = self.wrong_dt
        
        #calculate the differential of the event signal
        # for peak detection
        self.graphtec['ACC_Z_diff'] = self.graphtec['ACC_Z'].diff()

        print('iLevil file loaded')
        print('initial timestamp: ',self.graphtec['wrong_dt'][0])
        print('final timestamp: ',self.graphtec['wrong_dt'].tail(1))
        print()
        print(self.graphtec.head())

        self.graphtecExists = True

    def getINSFile(self):

        filename = tk.filedialog.askopenfilename(filetypes=[('TXT','*.txt'), ('CSV','*.csv')], title='Select VECTORNAV file')

        na_vals = ['', '#NA', 'N/A', '-nan', 'nan', 'NAN', 'NaN', 'NULL', 'null', ' ']
        self.vn_raw = pd.read_table(filename, skiprows=[1], sep='\t', converters={0:str, 1:lambda x: float(x or 0)})
        #dropping excess columns first


        for column in self.vn_raw.columns.values:

            splitted = column.split(' (')
            
            self.vn_raw.rename({column:splitted[0]}, axis='columns', inplace=True)
        
        #print(self.vn_raw.columns.values)
            
        #cleanup the mess that comes from VectorNav
        self.vn_raw.drop('Dcm00', 1, inplace=True)
        self.vn_raw.drop('Dcm01', 1, inplace=True)
        self.vn_raw.drop('Dcm02', 1, inplace=True)
        self.vn_raw.drop('Dcm10', 1, inplace=True)
        self.vn_raw.drop('Dcm11', 1, inplace=True)
        self.vn_raw.drop('Dcm12', 1, inplace=True)
        self.vn_raw.drop('Dcm20', 1, inplace=True)
        self.vn_raw.drop('Dcm21', 1, inplace=True)
        self.vn_raw.drop('Dcm22', 1, inplace=True)
        self.vn_raw.drop('YawPitchRollUncertainty.X', 1, inplace=True)
        self.vn_raw.drop('YawPitchRollUncertainty.Y', 1, inplace=True)
        self.vn_raw.drop('YawPitchRollUncertainty.Z', 1, inplace=True)
        self.vn_raw.drop('UncompensatedAcceleration.X', 1, inplace=True)
        self.vn_raw.drop('UncompensatedAcceleration.Y', 1, inplace=True)
        self.vn_raw.drop('UncompensatedAcceleration.Z', 1, inplace=True)
        self.vn_raw.drop('UncompensatedMagnetic.X', 1, inplace=True)
        self.vn_raw.drop('UncompensatedMagnetic.Y', 1, inplace=True)
        self.vn_raw.drop('UncompensatedMagnetic.Z', 1, inplace=True)
        self.vn_raw.drop('UncompensatedAngularRate.X', 1, inplace=True)
        self.vn_raw.drop('UncompensatedAngularRate.Y', 1, inplace=True)
        self.vn_raw.drop('UncompensatedAngularRate.Z', 1, inplace=True)
        self.vn_raw.drop('EstimatedPositionEcef.X', 1, inplace=True)
        self.vn_raw.drop('EstimatedPositionEcef.Y', 1, inplace=True)
        self.vn_raw.drop('EstimatedPositionEcef.Z', 1, inplace=True)
        self.vn_raw.drop('EstimatedVelocityBody.X', 1, inplace=True)
        self.vn_raw.drop('EstimatedVelocityBody.Y', 1, inplace=True)
        self.vn_raw.drop('EstimatedVelocityBody.Z', 1, inplace=True)
        self.vn_raw.drop('EstimatedVelocityEcef.X', 1, inplace=True)
        self.vn_raw.drop('EstimatedVelocityEcef.Y', 1, inplace=True)
        self.vn_raw.drop('EstimatedVelocityEcef.Z', 1, inplace=True)
        self.vn_raw.drop('EstimatedPositionUncertainty', 1, inplace=True)
        self.vn_raw.drop('EstimatedVelocityUncertainty', 1, inplace=True)
        self.vn_raw.drop('GpsTow', 1, inplace=True)
        self.vn_raw.drop('GpsTowNs', 1, inplace=True)
        self.vn_raw.drop('GpsWeek', 1, inplace=True)
        self.vn_raw.drop('GpsPositionEcef.X', 1, inplace=True)
        self.vn_raw.drop('GpsPositionEcef.Y', 1, inplace=True)
        self.vn_raw.drop('GpsPosition.Z', 1, inplace=True)

        self.vn_raw.drop('GpsVelocityEcef.X', 1, inplace=True)
        self.vn_raw.drop('GpsVelocityEcef.Y', 1, inplace=True)
        self.vn_raw.drop('GpsVelocityEcef.Z', 1, inplace=True)
        self.vn_raw.drop('GpsTimeUncertainty', 1, inplace=True)
        self.vn_raw.drop('ImuStatus', 1, inplace=True)
        self.vn_raw.drop('VpeStatus', 1, inplace=True)
        self.vn_raw.drop('TimeSyncIn', 1, inplace=True)
        self.vn_raw.drop('SyncInCount', 1, inplace=True)
        self.vn_raw.drop('DeltaTime', 1, inplace=True)
        self.vn_raw.drop('DeltaTheta.X', 1, inplace=True)
        self.vn_raw.drop('DeltaTheta.Y', 1, inplace=True)
        self.vn_raw.drop('DeltaTheta.Z', 1, inplace=True)
        self.vn_raw.drop('DeltaVelocity.X', 1, inplace=True)
        self.vn_raw.drop('DeltaVelocity.Y', 1, inplace=True)
        self.vn_raw.drop('DeltaVelocity.Z', 1, inplace=True)
        self.vn_raw.drop('TimeGpsPps', 1, inplace=True)
        self.vn_raw.drop('TimeUtc', 1, inplace=True)

        self.vn_raw.drop('LinearAccelerationBody.X', 1, inplace=True)
        self.vn_raw.drop('LinearAccelerationBody.Y', 1, inplace=True)
        self.vn_raw.drop('LinearAccelerationBody.Z', 1, inplace=True)
        self.vn_raw.drop('LinearAccelerationNed.X', 1, inplace=True)
        self.vn_raw.drop('LinearAccelerationNed.Y', 1, inplace=True)
        self.vn_raw.drop('LinearAccelerationNed.Z', 1, inplace=True)
        self.vn_raw.drop('AccelerationEcef.X', 1, inplace=True)
        self.vn_raw.drop('AccelerationEcef.Y', 1, inplace=True)
        self.vn_raw.drop('AccelerationEcef.Z', 1, inplace=True)
        self.vn_raw.drop('LinearAccelerationEcef.X', 1, inplace=True)
        self.vn_raw.drop('LinearAccelerationEcef.Y', 1, inplace=True)
        self.vn_raw.drop('LinearAccelerationEcef.Z', 1, inplace=True)
        self.vn_raw.drop('MagneticNed.X', 1, inplace=True)
        self.vn_raw.drop('MagneticNed.Y', 1, inplace=True)
        self.vn_raw.drop('MagneticNed.Z', 1, inplace=True)
        self.vn_raw.drop('MagneticEcef.X', 1, inplace=True)
        self.vn_raw.drop('MagneticEcef.Y', 1, inplace=True)
        self.vn_raw.drop('MagneticEcef.Z', 1, inplace=True)
        self.vn_raw.drop('GpsPositionAccuracyEcef.X', 1, inplace=True)
        self.vn_raw.drop('GpsPositionAccuracyEcef.Y', 1, inplace=True)
        self.vn_raw.drop('GpsPositionAccuracyEcef.Z', 1, inplace=True)
        self.vn_raw.drop('EstimatedAttitudeUncertainty', 1, inplace=True)
        self.vn_raw.drop('Quaternion.X', 1, inplace=True)
        self.vn_raw.drop('Quaternion.Y', 1, inplace=True)
        self.vn_raw.drop('Quaternion.Z', 1, inplace=True)
        self.vn_raw.drop('Quaternion.W', 1, inplace=True)

        self.vn_raw.drop('EstimatedPositionLla.Latitude', 1, inplace=True)
        self.vn_raw.drop('EstimatedPositionLla.Longitude', 1, inplace=True)
        self.vn_raw.drop('EstimatedPositionLla.Altitude', 1, inplace=True)

        self.vn_raw.drop('GpsTimestampLocalTime', 1, inplace=True)
        self.vn_raw.drop('GpsPositionUncertainty.X', 1, inplace=True)
        self.vn_raw.drop('GpsPositionUncertainty.Y', 1, inplace=True)
        self.vn_raw.drop('GpsPositionUncertainty.Z', 1, inplace=True)
        self.vn_raw.drop('GpsVelocityUncertainty', 1, inplace=True)

        self.vn_raw.drop('SensorSaturation', 1, inplace=True)


        # since the dataset is duplicated (I do not know why), I am getting rid of duplicates by direct index
        self.vn_clean = self.vn_raw.iloc[:, [j for j, c in enumerate(self.vn_raw.columns) if j < 37]].copy()
        self.vn_clean.fillna(method='pad', inplace=True)

        #vectornav timestamp

        #vectornav timestamp
        self.vn_clean['time'] = pd.to_datetime(self.vn_clean['Timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        vn_dt = self.vn_clean['time'][1]-self.vn_clean['time'][0]
        #print('the vn delta t is ', vn_dt, type(vn_dt))

        #calculate the differential of the z accel signal
        # for peak detection
        self.vn_clean['Acceleration.Z_diff'] = self.vn_clean['Acceleration.Z'].diff()

        print('VectorNav file loaded')
        print('initial timestamp: ',self.vn_clean['time'][0])
        print('final timestamp: ',self.vn_clean['time'].tail(1))
        print()
        
        self.INSExists = True

    def search_peaks(self):
        '''this function will detect the peaks and return the timedelta
        '''
        peaks_not_detected = True
        while peaks_not_detected:
            print()
            print()
            print('input iLevil peak threshold')
            graphtec_mph = tksd.askfloat("Input", "Enter iLevil peak threshold", minvalue = 0.0001, maxvalue = 5.0)
            print()
            print()
            print('input VectorNav peak threshold')
            #get the threshold
            vn_mph = tksd.askfloat("Input", "Enter VectorNav peak threshold", minvalue = 0.0001, maxvalue = 50.0)
   

            peaks = detect_peaks(self.graphtec['ACC_Z_diff'].values, mph=graphtec_mph)          

            peaks2 = detect_peaks(self.vn_clean['Acceleration.Z_diff'].values, mph=vn_mph)
            if len(peaks)==0:
                print('iLevil peaks not detectd - choose a lower threshold')
            if len(peaks2)==0:
                print('VectorNav peaks not detectd - choose a lower threshold')
            if (len(peaks)>0) and (len(peaks2)>0):
                print('peaks found')
                peaks_not_detected = False
            
        print('iLevil initial timestamp: {}'.format(self.graphtec['wrong_dt'].iloc[0]))
        print('iLevil peak detected at: {}'.format(self.graphtec['wrong_dt'].iloc[peaks[0]]))
        print('VectorNav initial timestamp: {}'.format(self.vn_clean['time'].iloc[0]))
        print('VectorNav peak detected at: {}'.format(self.vn_clean['time'].iloc[peaks2[0]]))
        print()

        dt_window = 20 # plus or minus seconds around found peak
        
        delta_time = self.graphtec['wrong_dt'].iloc[peaks[0]]-self.vn_clean['time'].iloc[peaks2[0]]
        print()
        gr_plt_data = self.graphtec[(self.graphtec['wrong_dt'] > (self.graphtec['wrong_dt'].iloc[peaks[0]]-pd.Timedelta(seconds=dt_window))) &
              (self.graphtec['wrong_dt'] < (self.graphtec['wrong_dt'].iloc[peaks[0]]+pd.Timedelta(seconds=dt_window)))]

        vn_plt_data = self.vn_clean[(self.vn_clean['time'] > (self.vn_clean['time'].iloc[peaks2[0]]-pd.Timedelta(seconds=dt_window))) &
              (self.vn_clean['time'] < (self.vn_clean['time'].iloc[peaks2[0]]+pd.Timedelta(seconds=dt_window)))]

        return peaks, peaks2, gr_plt_data, vn_plt_data, delta_time



    def detectPeaks(self):
        #start timestamp manipulation

        if not self.graphtecExists:
            self.popupmsg('Select iLevil file first')
        elif not self.INSExists:
            self.popupmsg('Select INS file first')
        else:

            self.gr_peaks, self.vn_peaks, self.gr_data, self.vn_data, self.deltat = self.search_peaks()

            print('Delta is: {}'.format(self.deltat))

            print('finished peaks routine')
            
            self.saveOK = True
            self.updatePlot(self.gr_data, self.vn_data)

    def saveValues(self):

        if self.saveOK == False:
            self.popupmsg('Detect peaks first')
        else:
            
            #new_time = self.wrong_dt - (self.graphtec['wrong_dt'].iloc[self.gr_peaks[0]]-self.vn_clean['time'].iloc[self.vn_peaks[0]])
            new_time = self.wrong_dt - pd.Timedelta(hours=4, minutes=00, seconds=00, milliseconds=0)
            print(type((self.graphtec['wrong_dt'].iloc[self.gr_peaks[0]]-self.vn_clean['time'].iloc[self.vn_peaks[0]])))

            print('now I am here 01')

            self.graphtec['time'] = new_time

            
            #join values
            result = self.vn_clean.append(self.graphtec.iloc[0:,:]).sort_values(by=['time'])



            #droping stuff we dont need
            ##result = result.drop('Number', 1)
            #result = result.drop('Alarm1-10', 1)
            #result = result.drop('AlarmOut', 1)
            #result = result.drop('Date&Time', 1)
            #result = result.drop('Time', 1)

            #result = result.drop('ms', 1)

            #result = result.drop('Timestamp', 1)
            #result = result.drop('wrong_dt', 1)
            #result = result.drop('CH8_diff', 1)
            #result = result.drop('Acceleration.Z_diff', 1)
            
            #first, pad forward with last value
            result.fillna(method='pad', inplace=True)
            
            #second, fill backwards so that veusz can cope...
            result.fillna(0, inplace=True)

            #calculate total 2D velocity
            #result['tot_veloc'] = (result['EstimatedVelocityNed.X']**2+result['EstimatedVelocityNed.Y']**2)**0.5*1.94384

            #calculate diffs
            result['d_theta']=result['Attitude.YawPitchRoll.Pitch'] - result['PITCH']
            result['d_roll']=result['Attitude.YawPitchRoll.Roll'] - result['ROLL']
            result['d_yaw']=result['Attitude.YawPitchRoll.Yaw'] - result['YAW']
            result['d_altitude']=result['GpsPositionLla.Altitude'] - result['ALTGPS']
            result['d_q']=result['AngularRate.Y']/(2*np.pi) - result['RATE_P']
            result['d_p']=result['AngularRate.X']/(2*np.pi) - result['RATE_Q']
            result['d_r']=result['AngularRate.Z']/(2*np.pi) - result['RATE_R']

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
 

    

class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        
        label = tk.Label(self, text="Select the Graphtec file for upload", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = ttk.Button(self, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
        button1.pack()

        button2 = ttk.Button(self, text="Page Two",
                            command=lambda: controller.show_frame(PageTwo))
        button2.pack()



class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Page Two!!!", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button1 = ttk.Button(self, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
        button1.pack()

        button2 = ttk.Button(self, text="Page One",
                            command=lambda: controller.show_frame(PageOne))
        button2.pack()




        

app = FTISyncApp()
app.mainloop()
