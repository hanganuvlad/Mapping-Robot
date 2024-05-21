#include <Servo.h>

#define viteza_mica 103
#define viteza_micaB 150
#define viteza_mare 255
#define viteza_mareB 150

int servoPin = 5;
Servo Servo1; 

float c;

//motor MARE
int dirmotorA=2;
int pwmmotorA=3;

//Char control
char receivedMessage[7];
char *ptr = 0;
double steering = 0;
double m_speed = 0;
int test,val;

void slowdown(int viteza)
{
    for (int i=viteza; i>=80; i--)
    {
      analogWrite(pwmmotorA,i);
      delay(10);
    }
    analogWrite(pwmmotorA,0);
}

void setup() 
{
  pinMode(dirmotorA,OUTPUT);
  pinMode(pwmmotorA,OUTPUT);
  Servo1.attach(servoPin); 
  Servo1.write(63);
  
  pinMode(13,OUTPUT);
  Serial.begin(9600);
}

void loop() 
{ 
  if (Serial.available())
  {
    
    memset(receivedMessage, '\0', sizeof(receivedMessage));
    Serial.readBytesUntil('\r', receivedMessage, 5);
    
    ptr = &(receivedMessage[0]);
    if(*ptr == 'S')
    {
      ptr++;

      steering = 0;
      for(int i = strlen(ptr)-1; *ptr != '\0'; i--)
      {
        steering += (*ptr++ - '0') * pow(10,i);
      }
      steering = round(steering);
      Servo1.write(steering);
      delay(10); 
    }
    else if(*ptr == 'M')
    {
      ptr++;

      m_speed = 0;
      for(int i = strlen(ptr)-1; *ptr != '\0'; i--)
      {
        m_speed += (*ptr++ - '0') * pow(10,i);  
      }
      m_speed = round(m_speed);
      if(m_speed == 200)
      {
        digitalWrite(13,HIGH); 
        digitalWrite(dirmotorA,LOW);
        analogWrite(pwmmotorA,viteza_mica);
      }
      else
      {
        digitalWrite(13,LOW); 
        slowdown(viteza_mica);
      }
    } 
  }
  
}
