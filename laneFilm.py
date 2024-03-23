##############################
#        laneFilm.py         #
##############################


import cv2
import func as f
from datetime import datetime


img = cv2.VideoCapture(1)
#img = cv2.VideoCapture('test4.mp4') 

img.set(3, 384)
img.set(4, 208)

start = datetime.now()
cont = 0

while True:

    ret, frame = img.read()

    canny_img = f.canny(frame)


    lines = f.hough(canny_img, maxi=60, mini=10, tresh=50)
    average_lines = f.averageLines(frame, lines)
    booleanBenzi = f.veziBanda(average_lines)
    lines_final = f.drawLines(frame, average_lines)
    combo_image = cv2.addWeighted(frame, 0.8, lines_final, 1, 1)

    #cv2.imshow('fer', frame)
    cv2.imshow('fer2', combo_image)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break



    cont+=1

img.release()
cv2.destroyAllWindows()
