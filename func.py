import datetime

import cv2
import numpy as np

# adresa senzor fata 0x14
# adresa lateral 0x54

a,b,c,d,e,f = (84, 0, 0, 255, 70,196)
q,w,e,r,t,y = (0, 0, 62, 248, 55, 255)

lower_blue = np.array([a, b, c])
upper_blue = np.array([d, e, f])

lower_red = np.array([q, w, e])
upper_red = np.array([r, t, y])

# Pt detectie semn
kernel = np.ones((3, 3), np.uint8)


##ATENTIE AM SCOS KERNEL 

def canny(original_image, minTreshCanny=50, maxTreshCanny=100):
    """
    0 - Functia primeste ca parametru imaginea, np array

    1 - Transforma imaginea in GrayScale
    
    2 - Blureaza imaginea pt continuitatea mai buna a liniilor

    3 - Diferenta de culoare brusca => alb
       Diferenta de culoare lenta => negru
       
    4 - Returneaza un nou np array cu imaginea procesata
    """
    gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)

    
    # Trecerile bruste de la o culoare la alta => punct alb.
    canny_img = cv2.Canny(gray_image, minTreshCanny, maxTreshCanny)

    # Imaginea procesata, pe care urmeaza sa aplici functiile
    return canny_img


def roi(original_image, dist=20, raport = 0.1, sjx = 0, djx =0, ssx = 20, dsx=20):
    """
    1 - Faci o imagine neagra de aceeasi dimensiune cu cea a imag originale

    2 - Alegi coordonatele formei tale geometrice (3 pct => triunghi, 4 pct => trapez)

    3 - Faci un array bidimensional de forma respectiva

    4 - Colorezi triunghiul alb

    5 - Suprapui pe original, mask. Tot ce se suprapune cu 0 dispare, tot ce se
        suprapune cu alb ramane neschimbat

    Returneaza imaginea ce surprinde doar Region Of Interest-ul tau
    """

    # Parametrii adaptivi in functie de imaginea parametru
    st_j=(sjx, original_image.shape[0])
    st_s=(ssx, int(original_image.shape[0] - (raport)*original_image.shape[0]))
    dr_s=(original_image.shape[1]-dsx, int(original_image.shape[0]- (raport)*original_image.shape[0]))
    dr_j=(original_image.shape[1] - djx , original_image.shape[0])
    
    # Pe mask urmeaza sa desenezi trapezul
    mask = np.zeros_like(original_image)

    # Creezi forma geometrica a triunghiului / trapez ( depinde ce vrei )
    shape = np.array([[st_j, st_s, dr_s, dr_j]])

    # Desenezi pe mask (fundal negru de dim pozei orig) forma ta geometrica de culoare alba
    cv2.fillPoly(mask, shape, 255)

    # Returneaza Region Of Interes
    return cv2.bitwise_and(original_image, mask)


def hough(proc_img, maxi=80, mini=15, fi=2, tresh=30, teta=180):
    """
    :param proc_img:    imaginea dupa ce iese din canny() + roi().
    :param maxi:        spatiul MAXIM (in px) intre 2 pct, ca ele sa formeze o dreapta.
    :param mini:        distanta MINIMA (in px) intre 2 pct, ca ele sa formeze o dreapta.
    :param tresh:       cu cat tresh e mai mare, cu atat e mai selectiv pentru linii.

    :param teta:        Tin de spatiul Hough. Ungiul dintre fi si ox
    :param fi:          Perpendiculara din origine pe dreapta mea

    :return:            Array multidimensional de forma [ [[x1,y1,x2,y2]]  [[x3,x4,y3,y4]]  ...  [[xn-1,yn-1,xn,yn]] ]
                        fiecare element, contine punctele cu care faci o linie.
                        len(lines) => nr de linii pe care le vede
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


def makeCoordinates(image, line_parameters, side, lung_desen=3 / 5, crop=0.1):
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
            if slope > -0.2 :
                return None
            
        else:

            # Panta dreptei crescatoare x tinde la infinit => nu pot calcula
            if slope < 0.2 :
                return None
            
        x1 = int((y1 - intercept) / slope)
        x2 = int((y2 - intercept) / slope)

        # returnez coordonatele ce definesc dreapta pe care o desenez pe ecran
        return np.array([x1, y1, x2, y2])


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

    except TypeError as e:

        # In cazul asta, nu ai linie detectata din hough
        return np.array([None, None])


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
    if veziBanda(lines) == [True, True]:

        for x1, y1, x2, y2 in lines:
            """aici am avut un try except overflowerror , in except printam toate coordonatele
            ar trebui sa nu mai am nicio eroare
            """

            # Desenarea efectiva pe mask
            cv2.line(mask, (x1, y1), (x2, y2), color=(255, 0, 0), thickness=5)

        # Returneaza o masca cu cele 2 linii, urmeaza sa le suprapui
        return mask

    elif veziBanda(lines) == [True, False]:   # Negative

        # Iau doar coordonatele pt linia stanga
        x1, y1, x2, y2 = lines[0]
        """aici am avut un try except overflowerror , in except printam toate coordonatele
        ar trebui sa nu mai am nicio eroare
        """

        cv2.line(mask, (x1, y1), (x2, y2), color=(255, 0, 0), thickness=5)
        slope = (y2-y1)/(x2-x1)
        print(slope)

        # Returneaza o masca cu o singura linie (linia stanga)
        return mask

    elif veziBanda(lines) == [False, True]:   # Pozitive

        # Iau doar coordonatele pt linia dreapta
        x1, y1, x2, y2 = lines[1]
        """aici am avut un try except overflowerror , in except printam toate coordonatele
        ar trebui sa nu mai am nicio eroare
        """

        cv2.line(mask, (x1, y1), (x2, y2), color=(255, 0, 0), thickness=5)
        slope = (y2-y1)/(x2-x1)
        print(slope)
        
        # Returneaza o masca cu o singura linie (linia dreapta)
        return mask

    else:

        # returnez efectiv nimic, doar pentru a nu imi arunca exceptie
        return mask


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



