import serial

class SerialCom:
    def __init__(self, baudrate):

        """
        Init method tries to set a serial communication between NUCLEO and MASTER, where master can be Win or Linux.
        If it fails, the " THERE IS NO SERIAL COMMUNICATION " message will be outputted

        If the baudrate inputted by the user is not found in the accepted baudrates list, the baudrate will be setted
        BY DEFAULT on 19200

        :param baudrate: baudrate
        """
        if baudrate not in serial.Serial.BAUDRATES:
            self.message(True, "Baudrate must be one of " + str(serial.Serial.BAUDRATES))
            self.baudrate = 9600
        else:
            self.message(False, "Baudrate set to " + str(baudrate))
            self.baudrate = baudrate

        try:
            self.ser = serial.Serial("COM3", baudrate, timeout=1)
            self.message(False, "ARDUINO is connected to PC via COM3 port")

        except Exception as e:
            self.message(True, "ARDUINO could not connect to COM3 port\n" + str(e))
            try:
                self.ser = serial.Serial('/dev/ttyACM0', baudrate, timeout=1)
                self.message(False, "ARDUINO is connected to LINUX via ttyACM0 port")

            except Exception as f:
                self.message(True, "ARDUINO could not connect to /dev/ttyACM0\n" + str(f))
                try:
                    self.ser = serial.Serial('/dev/ttyACM1', baudrate, timeout=1)
                    self.message(False, "ARDUINO is connected to LINUX via ttyACM1 port")

                except Exception as g:
                    self.message(True, "THERE IS NO SERIAL COMMUNICATION\n" + str(g))

    def __del__(self):
        """
        The destructor. It just closes the serial communication, allowing for the next time another communication
        to be started on the same port.

        There is a problem running this on pycharm in console because if you have a simple program,
        the garbage collector will automatically delete your object as soon as you will crate it.

        A success or warning message will be shown.
        :return:
        """
        try:
            self.ser.close()
            self.message(False, "Serial connection closed")

        except Exception as e:
            self.message(True, "din Destructor " + str(e))

    def pwmValidation(self, pwm):
        if pwm < -255:
            self.message(True, "pwm must be in interval [-255, 255]. Default set to -255")
            return -255
        if pwm > 255:
            self.message(True, "pwm dmust be in interval [-255, 255]. Default set to 255")
            return 255
        return pwm

    def drive(self, pwm):
        """
        The function receives the wanted speed and translate it in the serial communication language chosen by you

        1. Validation of the pwm value. ONLY ALLOWED [0, 255]
        2. Create the serial message in the formatted type : LSD\r to LSDDD\r - L-letter, S-sign, D-digit
        3. Validate the length of the message from the above point(2)
        4. Send the message to ARDUINO

        :param pwm: an integer value
        :return: a string like "M200\r"
        """
        pwm = self.pwmValidation(pwm)
        mesaj_serial_brut = self.createMessageForSerial("motor", pwm)
        mesaj_serial_valid = self.lengthValidation("motor", mesaj_serial_brut)
        self.ser.write(mesaj_serial_valid.encode('utf-8'))

    def angleValidation(self, angle):
        if angle < 21:
            return 21
        if angle > 780:
            return 780
        return angle

    def setAngle(self, angle):
        angle = self.angleValidation(angle)
        mesaj_serial_brut = self.createMessageForSerial("servo", angle)
        mesaj_serial_valid = self.lengthValidation("servo", mesaj_serial_brut)
        self.ser.write(mesaj_serial_valid.encode('utf-8'))
        self.angle = angle

    def lengthValidation(self, forWhat, mesaj):
        if len(mesaj) > 6:
            self.message(True, "Maximum 6 characters of type:\nM+9999\\r\nS1024\\r")
            if forWhat.lower() == "servo":
                return "S0"
            elif forWhat.lower() == "motor":
                return "M0"
        else:
            return mesaj

    # noinspection PyMethodMayBeStatic
    def createMessageForSerial(self, forWhat, value):
        # SERVO
        if forWhat.lower() == "servo":
            return "S" + str(value) + "\r"
        # MOTOR
        elif forWhat.lower() == "motor":
            # Motor cu PID
            return "M" + str(value) + "\r"

    @staticmethod
    def message(isError, message):
        print("*" * 120)
        print(">>>WARNING<<< - " + message if isError else ">>>SUCCESS<<< - " + message)
        print("*" * 120, end="\n\n")


obj = SerialCom(9600)
