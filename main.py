import cv2
import sss as f
from datetime import datetime
from handmade import SerialCom
import time

obj = SerialCom(9600)
img = cv2.VideoCapture(0)

start = datetime.now()
cont = 0
aux = 0

sem = 0

maxi = 20
mini = 10
tresh = 40

min_t = 30  # 30
max_t = 21  # 21

last_panta = 0.0
panta = None
while True:

    ret, frame = img.read()
    frame = f.image_resize(frame, 384, 208)

    original_image = frame.copy()
    centru_image = frame.copy()

    canny_laterala = f.canny(original_image, minTreshCanny=min_t, maxTreshCanny=max_t, blur_kernel=(11, 11))
    cv2.imshow("canny_laterala", canny_laterala)

    roi_laterala = f.roi(canny_laterala, raport=0.4, sjx=0, djx=200, ssx=0, dsx=200)
    cv2.imshow("roi_laterala", roi_laterala)

    lines_laterala = f.hough(roi_laterala, maxi=maxi, mini=mini, tresh=tresh)
    #print(lines_laterala,"\n")
    #print(len(lines_laterala))
    
    average_lines_laterala = f.averageLines_left(original_image, lines_laterala)
    panta = f.getPanta(average_lines_laterala)

    if panta is not None:
        #print(panta)
        last_panta = panta
    else:
        panta = last_panta
        print("ultima panta: ", round(abs(panta)))
    
    obj.drive(200)
    try:
        if f.stopLine(lines_laterala):
            print(">" * 20, "virez dreapta")
            obj.setAngle(105)
                
        else:
            if (f.metoda(lines_laterala) == False):   
                kp = 18
                panta = round(abs(panta), 3)
                target = 1.04
                error = target - panta
                P = kp * error
                print("Proportionalu: ",round(int(63+P)))
                print(panta)
                if round(int(63+P)) < 35:
                    obj.setAngle(35)
                if round(int(63+P)) > 85:
                    obj.setAngle(85)W
                if round(int(63+P)) >= 35 and round(int(63+P)) <= 85:
                    obj.setAngle(round(int(63+P)))
            else:
                f.metoda(lines_laterala)
            
    except:
        print("CRED CA NU VAD NIMIC")
        obj.setAngle(58)

    lines_final = f.drawLines_left(frame, average_lines_laterala)


    key = cv2.waitKey(1)
    if key == ord('q'):
        break

img.release()
cv2.destroyAllWindows()
