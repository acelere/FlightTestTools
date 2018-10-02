#python dynamic_color_tracking

import cv2
import argparse
import numpy as np
import pandas as pd
import time


def trackbar_callback(value):
    pass

def setup_trackbars(range_filter):
    cv2.namedWindow("Trackbars", 0)

    for i in ["MIN", "MAX"]:
        v = 0 if i == "MIN" else 255
        for j in range_filter:
            cv2.createTrackbar("%s_%s" % (j, i), "Trackbars", v, 255, trackbar_callback) #try with trackbar_callback

def get_trackbar_values(range_filter):
    values = []

    for i in ["MIN", "MAX"]:
        for j in range_filter:
            v = cv2.getTrackbarPos("%s_%s" % (j, i), "Trackbars")
            values.append(v)
    return values

def detect_object(mask):
    
    cnts = cv2.findContours(mask.copy(), cv2. RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    center = None
    radius = 0

    #calculate only if something was found
    if len(cnts) >0:
        c = max(cnts, key=cv2.contourArea)
        ((x,y), r) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        radius = int(r)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
    return center, radius

def calculate_percentages(center, upper_bound, lower_bound):
    size_x = (lower_bound[0] - upper_bound[0])
    size_y = (lower_bound[1] - upper_bound[1])
    x_perc = 0
    y_perc = 0
    if (size_x != 0 and size_y !=0):
            x_perc = int((((center[0] - upper_bound[0]) / size_x) - 0.5) * 2 * 100)
            y_perc = int((((center[1] - upper_bound[1]) / size_y) - 0.5) * 2 * 100)
    return x_perc, y_perc         
    


def draw_circle(image, center, radius, upper_bound, lower_bound, cal_status):
    #draw only if radius > 5
    if radius > 5:
        cv2.circle(image, center, radius, (0, 255, 255), 2)
        cv2.putText(image,"centroid", (center[0]+10,center[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4,(0, 0, 255),1)
        if (cal_status):
            x_perc, y_perc = calculate_percentages(center, upper_bound, lower_bound)
            cv2.putText(image,"("+str(x_perc)+","+str(y_perc)+")",
                    (center[0]+10,center[1]+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4,(0, 0, 255),1)
        else:
            cv2.putText(image,"("+str(center[0])+","+str(center[1])+")",
                    (center[0]+10,center[1]+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4,(0, 0, 255),1)

def draw_bounds(image, upper_bound, lower_bound, cal_status, rec_status):
    #lower_bound = (upper_bound[0] + width, upper_bound[1] + height)
    #print(upper_bound, type(upper_bound))
    cv2.rectangle(image, upper_bound, lower_bound, (0, 255, 255), 2)
    if  cal_status:
        cv2.putText(image,"calibrated", upper_bound,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4,(0, 0, 255),1)
    if  rec_status:
        cv2.putText(image,"RECORDING", lower_bound,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4,(0, 0, 255),1)    

def main():
    camera = cv2.VideoCapture(0)
    
    frame_w = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    frame_h = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    upper_limit_x = int(frame_w) #upper relative to screen - upper left corner
    upper_limit_y = int(frame_h)
    lower_limit_x = 0
    lower_limit_y = 0

    range_filter = 'HSV' #or RGB
    setup_trackbars(range_filter)
    cal_status = False
    calibrating = False
    recording = False

    df = pd.DataFrame({'Time':[time.asctime(time.localtime())], 'X_percent':[0], 'Y_percent':[0]})

    try:
        while True:
            _, image = camera.read()
            if range_filter == 'RGB':
                frame_to_thresh = image.copy()
            else:
                frame_to_thresh = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            key = cv2.waitKey(5) & 0xFF

            if (key == ord('q') or key == ord('Q') or key == 27): #exit
                break
            elif (key == ord('c') or key == ord('C')): #calibrate
                calibrating = not calibrating
            elif (key == ord('r') or key == ord('R')): #rest
                cal_status = False
                calibrating = False
                recording = False
                upper_limit_x = int(frame_w) #upper relative to screen - upper left corner
                upper_limit_y = int(frame_h)
                lower_limit_x = 0
                lower_limit_y = 0
            elif (key == ord('s') or key == ord('S')): #start/stop rec
                recording = not recording

            v1_min, v2_min, v3_min, v1_max, v2_max, v3_max = get_trackbar_values(range_filter)

            thresh = cv2.inRange(frame_to_thresh, (v1_min, v2_min, v3_min), (v1_max, v2_max, v3_max))
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel) #filter out white noise
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) #also to remove noise
            # find contours in the mask and initialize the current
            # (x, y) center of the ball
            # http://docs.opencv.org/2.4/modules/imgproc/doc/structural_analysis_and_shape_descriptors.html

            center, radius = detect_object(mask)
            time_stamp = time.localtime()
            if calibrating:
                if type(center) != 'NoneType': #had to add this becuause sometimes the object comes empty
                    if center[0] < upper_limit_x:
                        print(center[0])
                        upper_limit_x = int(center[0])
                    if center[1] < upper_limit_y:
                        upper_limit_y = int(center[1])
                    if center[0] > lower_limit_x:
                        lower_limit_x = int(center[0])
                    if center[1] > lower_limit_y:
                        lower_limit_y = int(center[1])
                    cal_status = True
                    #IMPLEMENT CENTER POINT

                    
            if (recording and cal_status):
                x_perc, y_perc = calculate_percentages(center, (upper_limit_x, upper_limit_y),
                                (lower_limit_x, lower_limit_y))
                print("x= ",x_perc, " y= ",y_perc)
                df = df.append({'Time':time.asctime(time_stamp), 'X_percent':x_perc, 'Y_percent':y_perc}, ignore_index=True)
                print(df.tail())


                
            draw_circle(image, center, radius, (upper_limit_x, upper_limit_y),
                                (lower_limit_x, lower_limit_y), (cal_status and not calibrating))
            draw_bounds(image, (upper_limit_x, upper_limit_y),
                                (lower_limit_x, lower_limit_y), (cal_status and not calibrating), recording)
            

            cv2.imshow("Image", image)
            cv2.imshow("Mask", mask)
    except Exception as e:
        print(str(e))
    camera.release()
    cv2.destroyAllWindows()
    print(df.head())
    df.to_csv('newcsv.csv')

if __name__ == '__main__':
    main()
    print("done")

