import time

import cv2
import numpy as np
from handmade import SerialCom
obj = SerialCom(9600)


def canny(original_image, minTreshCanny=100, maxTreshCanny=100, blur_kernel=(3, 3)):
    # Primeste imaginea și o transformă în filtru gray. 
    gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    
    # Blurează imaginea pentru continuitatea mai bună a liniilor
    blur_image = cv2.blur(gray_image, blur_kernel)

    # Trecerile bruste de la o culoare la alta determină un punct alb.
    canny_img = cv2.Canny(blur_image, minTreshCanny, maxTreshCanny)

    # Returnarea imaginii procesate
    return canny_img


def roi(original_image, raport=0.1, sjx=0, djx=0, ssx=20, dsx=20):
    # Parametrii adaptivi in functie de imaginea parametru
    st_j = (sjx, original_image.shape[0])
    st_s = (ssx, int(original_image.shape[0] - raport * original_image.shape[0]))
    dr_s = (original_image.shape[1] - dsx, int(original_image.shape[0] - raport * original_image.shape[0]))
    dr_j = (original_image.shape[1] - djx, original_image.shape[0])

    # Desenarea traseului pe mask
    mask = np.zeros_like(original_image)

    # Crearea formei regiunii de interes
    shape = np.array([[st_j, st_s, dr_s, dr_j]])

    # Desenarea pe mask (fundal negru de dim pozei originale) forma geometrica de culoare alba
    cv2.fillPoly(mask, shape, 255)

    # Returneaza regiunea de interes
    return cv2.bitwise_and(original_image, mask)


def hough(proc_img, maxi=80, mini=15, fi=2, tresh=30, teta=180):
    """
    proc_img -    imaginea dupa ce iese din canny + roi
    maxi     -    spatiul MAXIM (in px) intre 2 puncte, ca ele sa formeze o dreapta
    mini     -    distanta MINIMA (in px) intre 2 puncte, ca ele sa formeze o dreapta.
    tresh    -    cu cat puntea e mai mare, cu atat liniile sunt abstractizate mai mult.
    teta     -    tin de spatiul Hough. Ungiul dintre fi si dreapta ox
    fi       -    perpendiculara din origine pe dreapta
    return   -    returneaza un array multidimensional de forma [ [[x1,y1,x2,y2]]  [[x3,x4,y3,y4]]  ...  [[xn-1,yn-1,xn,yn]] ] fiecare element, contine punctele cu care se face o linie.
    """

    # Parametrii pot fi modificati in timp real
    lines = cv2.HoughLinesP(proc_img,
                            fi,
                            np.pi / teta,
                            tresh,
                            np.array([]),
                            minLineLength=mini,
                            maxLineGap=maxi)

    return lines


def makeCoordinates(image, line_parameters, side, lung_desen=3 / 5):
    """
    makeCoordinates( ) Se aplica selectiv pentru media liniilor de pe o stanga, respectiv dreapta.
    Deci aici tu creezi dreapta finala de care se va tine cont in directia robotului

    print (img.shape) => (342, 548, 3) => img.shape[0] = rows, img.shape[1] = columns, img.shape[2] = color channels,

    Ai link ca sa intelegi cum variaza parametrii
    https://www.desmos.com/calculator/4oztvm77ln

    :param crop: > 0 neaparat!  1 => scoti toate dreptele dintre prima bisect si ox
                                0.1 => scoti toate dreptele care se apropie de ox foarte mult

    :param lung_desen:          Cat de lunga sa fie desenata linia
    :param image:               Frame-ul original
    :param line_parameters:     Media liniilor de pe o singura parte
    :param side:                Imi trimit acest parametru, pentru ca altfel nu am cum sa stiu ce dreapta prelucrez

    :return:                    [x1, y1, x2, y2] Pur necesar pentru noi, ca sa vedem dreapta
    ########## DE SCOS PENTRU PERFORMANTA #########
    """

    # Daca e none, inseamna ca nu a vazut nicio linie
    if line_parameters is None:
        return None
    else:

        # Panta si intersectia cu Oy
        slope, intercept = line_parameters

        # image.shape[0] = rows  (din rezolutia imaginii)
        y1 = image.shape[0]

        # Stabilesti lungimea dintre puncte
        y2 = int(y1 * lung_desen)

        if side == 'left':

            # Panta dreptei descrescatoare x tinde la infinit => nu pot calcula
            if slope > -0.2:
                return None

        else:

            # Panta dreptei crescatoare x tinde la infinit => nu pot calcula
            if slope < 0.2:
                return None

        x1 = int((y1 - intercept) / slope)
        x2 = int((y2 - intercept) / slope)

        # returnez coordonatele ce definesc dreapta pe care o desenez pe ecran
        return np.array([x1, y1, x2, y2])


def stopLine(houghLines, thresh=0.1):
    try:
        isStopLine = False
        for line in houghLines:
        
            for x1, y1, x2, y2 in line:
                panta = (y2 - y1) / (x2 - x1)
                
                if abs(panta) < thresh:
                    return True
                    
        return isStopLine
        
    except Exception:
        pass


def averageLines(image, houghLines):
    """
    :param image:           imaginea este cea originala, de la imag.read()
    :param houghLines:      [ [[x1,y1,x2,y2]]  [[x3,x4,y3,y4]]  ...  [[xn-1,yn-1,xn,yn]] ]

    FUNCTIA polyfit((x1,x2),(y1,y2), grad_ecuatie). Returneaza panta dreptei formata de cele 2 puncte
    si intersectia cu axa Oy. De avut in vedere ca el ia ca origine coltul stanga sus al ecranului.
    X creste cu cat te uiti spre dreapta, Y creste cu cat te uiti in jos.

    :return:                np.array([left_line, right_line])
                        sau np.array([None, right line])
                        sau np.array([left_line, None])
                        sau np.array([None, None])
    """

    # Un acumulator pentru a face media liniilor inclinate spre DREAPTA
    left_fit = []

    # Un acumulator pentru a face media liniilor inclinate spre STANGA
    right_fit = []

    # Daca exista vreo linie detectata
    try:

        # Din [ [[]] [[]] [[]] ] --> [[]]  [[]]  [[]]. Ai scapat de o dimensiune => [[120 409 437 409]] ... [[a b c d]]
        for line in houghLines:

            # Ai pus efectiv mana pe valori.
            for x1, y1, x2, y2 in line:

                # Daca x1 = x2 => slope tinde la  infinit => nu pot aplica Polyfit
                if x1 == x2:
                    # Sar peste dreapta formata din punctele astea, si trec la urmatoarea pereche de 4 puncte
                    continue

                # Capetele unei singure linii
                parameters = np.polyfit((x1, x2), (y1, y2), 1)

                # Panta dreptei
                slope = parameters[0]

                # Intersectia dreptei cu Oy
                intercept = parameters[1]

                if slope < 0 and x2 < int(image.shape[1] / 2):

                    # Creez o lista cu toate functiile dreptelor de pe stanga
                    left_fit.append((slope, intercept))

                elif slope >= 0 and x2 > int(image.shape[1] / 2):

                    # Creez o lista cu toate functiile dreptelor de pe stanga
                    right_fit.append((slope, intercept))

        # Daca exista linii pe partea stanga
        if left_fit:

            # Face media tuturor pantelor si tuturor intersectiilor cu Oy
            left_fit_average = np.average(left_fit, axis=0)

        else:

            # Imi dau aceasta valoare SPECIAL ca sa stiu ca nu trebuie sa desenez pt ca nu am linie
            left_fit_average = None

        # Daca exista linii pe partea dreapta
        if right_fit:

            # Face media tuturor pantelor si tuturor intersectiilor cu Oy
            right_fit_average = np.average(right_fit, axis=0)

        else:

            # Imi dau aceasta valoare SPECIAL ca sa stiu ca nu trebuie sa desenez pt ca nu am linie
            right_fit_average = None

        # left_line [x1,y1,x2,y2], linia STANGA medie
        left_line = makeCoordinates(image, left_fit_average, 'left')

        # right_line [x1,y1,x2,y2], linia DREAPTA medie
        right_line = makeCoordinates(image, right_fit_average, 'right')

        # Nu vad linia stanga
        if left_line is None:

            # Vad doar linia dreapta
            return np.array([None, right_line])

        # Vad linia stanga
        else:

            # Nu vad linia dreapta
            if right_line is None:
                return np.array([left_line, None])

        # Le vad pe ambele
        return np.array([left_line, right_line])

    except Exception:

        # In cazul asta, nu ai linie detectata din hough
        return np.array([None, None])


def averageLines_left(image, houghLines):
    # Un acumulator pentru a face media liniilor inclinate spre DREAPTA
    left_fit = []

    # Daca exista vreo linie detectata
    try:

        # Din [ [[]] [[]] [[]] ] --> [[]]  [[]]  [[]]. Ai scapat de o dimensiune => [[120 409 437 409]] ... [[a b c d]]
        for line in houghLines:

            # Ai pus efectiv mana pe valori.
            for x1, y1, x2, y2 in line:

                # Daca x1 = x2 => slope tinde la  infinit => nu pot aplica Polyfit
                if x1 == x2:
                    # Sar peste dreapta formata din punctele astea, si trec la urmatoarea pereche de 4 puncte
                    continue

                # Capetele unei singure linii
                parameters = np.polyfit((x1, x2), (y1, y2), 1)

                # Panta dreptei
                slope = parameters[0]

                # Intersectia dreptei cu Oy
                intercept = parameters[1]

                if slope < 0 and x2 < int(image.shape[1] / 2):
                    # Creez o lista cu toate functiile dreptelor de pe stanga
                    left_fit.append((slope, intercept))

        # Daca exista linii pe partea stanga
        if left_fit:

            # Face media tuturor pantelor si tuturor intersectiilor cu Oy
            left_fit_average = np.average(left_fit, axis=0)

        else:

            # Imi dau aceasta valoare SPECIAL ca sa stiu ca nu trebuie sa desenez pt ca nu am linie
            left_fit_average = None

        # left_line [x1,y1,x2,y2], linia STANGA medie
        left_line = makeCoordinates(image, left_fit_average, 'left')

        if left_line is None:
            # Vad doar linia dreapta
            return np.array([None])

        return np.array([left_line])

    except Exception:
        # print(e)
        return np.array([None])

def getPanta(line):
    try:
        for x1, y1, x2, y2 in line:
            panta = (y2 - y1) / (x2 - x1)
            return panta
    except:
        return None


def drawLines_left(image, lines):
    """
    :param image:   Doar pentru a-si lua dimensiunile Linii, Coloane

    :param lines:       lines[0] contine coordonatele liniei de pe stanga
                        lines[1] contine coordonatele liniei de pe dreapta

                        np.array([left_line, right_line])   sau
                        np.array([None, right line])        sau
                        np.array([left_line, None])         sau
                        np.array([None, None])

    :return:        mask (o imagine cu 2 linii desenate pe ea)
    """

    # Copiez dimensiunile imaginii originale, (Width, Heigh) dar toti pixelii negri.
    mask = np.zeros_like(image)

    if veziBanda_stanga(lines) == [True]:
        try:
            for x1, y1, x2, y2 in lines:
                """aici am avut un try except overflowerror , in except printam toate coordonatele
                ar trebui sa nu mai am nicio eroare
                """

                # Desenarea efectiva pe mask
                cv2.line(mask, (x1, y1), (x2, y2), color=(0, 0, 255), thickness=5)
                panta = (y2 - y1) / (x2 - x1)
                #print(panta)
                # if (panta < 0):
                # print("stanga",panta)
                # ser.write("2\n".encode('utf-8'))
                # print ("val: ", val)
                # else:
                # print("dreapta",panta)

            # Returneaza o masca cu cele 2 linii, urmeaza sa le suprapui
            return mask
        except Exception:
            # print(e)
            pass
    else:

        # returnez efectiv nimic, doar pentru a nu imi arunca exceptie
        return mask


def drawLines(image, lines):
    """
    :param image:   Doar pentru a-si lua dimensiunile Linii, Coloane

    :param lines:       lines[0] contine coordonatele liniei de pe stanga
                        lines[1] contine coordonatele liniei de pe dreapta

                        np.array([left_line, right_line])   sau
                        np.array([None, right line])        sau
                        np.array([left_line, None])         sau
                        np.array([None, None])

    :return:        mask (o imagine cu 2 linii desenate pe ea)
    """

    # Copiez dimensiunile imaginii originale, (Width, Heigh) dar toti pixelii negri.
    mask = np.zeros_like(image)

    # Metoda {veziBanda} asta este implementata aici, mai la final
    # Returneaza [boolean, boolean]

    # val=2
    # ser = serial.Serial("/dev/ttyACM0", 9600)
    sem = 0
    # time.sleep(2)

    if veziBanda(lines) == [True, True]:

        for x1, y1, x2, y2 in lines:
            """aici am avut un try except overflowerror , in except printam toate coordonatele
            ar trebui sa nu mai am nicio eroare
            """

            # Desenarea efectiva pe mask
            cv2.line(mask, (x1, y1), (x2, y2), color=(0, 0, 255), thickness=5)
            panta = (y2 - y1) / (x2 - x1)
            #print(panta)
            # if (panta < 0):
            # print("stanga",panta)
            # ser.write("2\n".encode('utf-8'))
            # print ("val: ", val)
            # else:
            # print("dreapta",panta)

        # Returneaza o masca cu cele 2 linii, urmeaza sa le suprapui
        return mask

    elif veziBanda(lines) == [True, False]:
        # Iau doar coordonatele pt linia stanga
        x1, y1, x2, y2 = lines[0]
        """aici am avut un try except overflowerror , in except printam toate coordonatele
        ar trebui sa nu mai am nicio eroare
        """

        cv2.line(mask, (x1, y1), (x2, y2), color=(255, 0, 0), thickness=5)
        panta = (y2 - y1) / (x2 - x1)
        print("stanga", panta)
        if -1.0 >= panta >= -2:
            """merge fata """
            # print("merge merge merge merge")
            # ser.write("2\n".encode('utf-8'))
            # time.sleep(0.1)
        elif panta < -20:

            if sem == 0:
                # ser.write("3\n".encode('utf-8'))
                time.sleep(0)

                # ser.write("5\n".encode('utf-8'))

        # Returneaza o masca cu o singura linie (linia stanga)
        return mask

    elif veziBanda(lines) == [False, True]:

        # Iau doar coordonatele pt linia dreapta
        x1, y1, x2, y2 = lines[1]
        """aici am avut un try except overflowerror , in except printam toate coordonatele
        ar trebui sa nu mai am nicio eroare
        """

        cv2.line(mask, (x1, y1), (x2, y2), color=(0, 0, 255), thickness=5)
        panta = (y2 - y1) / (x2 - x1)
        print("dreapta", panta)

        # Returneaza o masca cu o singura linie (linia dreapta)
        return mask

    else:

        # returnez efectiv nimic, doar pentru a nu imi arunca exceptie
        return mask


def mapFunction(x, in_min, in_max, out_min, out_max):
    """
    Re-maps a number from one range to another. That is, a value of fromLow would get mapped to toLow,
    a value of fromHigh to toHigh,values in-between to values in-between, etc.

    Does not constrain values to within the range, because out-of-range values are sometimes intended and useful.
    The constrain() function may be used either before or after this function, if limits to the ranges are desired.

    Note that the "lower bounds" of either range may be larger or smaller than the "upper bounds" so the map()
    function may be used to reverse a range of numbers, for example

    y = mapFunction(x, 1, 50, 50, 1);

    The function also handles negative numbers well, so that this example

    y = mapFunction(x, 1, 50, 50, -100);

    is also valid and works well.

    :param x:           the number to map.
    :param in_min:      the lower bound of the value’s current range.
    :param in_max:      the upper bound of the value’s current range.
    :param out_min:     the lower bound of the value’s target range.
    :param out_max:     the upper bound of the value’s target range.
    :return:            The mapped value.
    """

    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def veziBanda(linie_stanga_dreapta):
    """
    :param linie_stanga_dreapta:    np.array([left_line, right_line])   sau
                                    np.array([None, right line])        sau
                                    np.array([left_line, None])         sau
                                    np.array([None, None])

    :return:        O lista [boolean, boolean] in functie de banda pe care o vede.

                    Ex: [True, True]   => vede ambele benzi
                        [False, False] => nu vede nicio banda
    """

    left, right = linie_stanga_dreapta

    if left is None:
        if right is None:
            return [False, False]
        else:
            return [False, True]
    else:
        if right is None:
            return [True, False]
        else:
            return [True, True]


def veziBanda_stanga(linie_stanga):
    """
    :param linie_stanga_dreapta:    np.array([left_line, right_line])   sau
                                    np.array([None, right line])        sau
                                    np.array([left_line, None])         sau
                                    np.array([None, None])

    :return:        O lista [boolean, boolean] in functie de banda pe care o vede.

                    Ex: [True, True]   => vede ambele benzi
                        [False, False] => nu vede nicio banda
    """

    left = linie_stanga

    if left is None:
        return [False]
    else:
        return [True]


def image_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)
    
    # return the resized image
    return resized

def computePidPeDistanta(ssx_banda, KP=0.1, ssx_limita=83):
    if ssx_banda >= ssx_limita:  # stanga sus x de la dreapta
        err = 60+((ssx_banda - ssx_limita) * KP)
        err = round(int(err))
        print("ERRRRRRRRRRRRR: ",err)
        if err < 35:
            obj.setAngle(35)
        if err > 85:
            obj.setAngle(85)
        if err >=35 and err <= 85:
            obj.setAngle(err)
        return True
    else:
        return False

def metoda(line):
    if len(line) == 1:
        for x1, y1, x2, y2 in line[0]:
            # Doar daca e cazul
            if computePidPeDistanta(x2, KP=0.1, ssx_limita=83):
                return True

    else:
        ssx_minim = 99999

        """2 iteratii"""
        for x1, y1, x2, y2 in line[0]:
            if x2 < ssx_minim:
                ssx_minim = x2

        # Doar daca e cazul
        if computePidPeDistanta(ssx_minim, KP=0.1, ssx_limita=83):
            return True
    return False
