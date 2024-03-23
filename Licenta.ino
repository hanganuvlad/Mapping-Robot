#define viteza_mica 50
#define viteza_micaB 70
#define viteza_mare 255
#define viteza_mareB 100

//motor MARE
int dirmotorA = 8;
int pwmmotorA = 9;

//motor mic
int dir1motorB = 10;
int dir2motorB = 11;
int analogpin = 2;
int sem = 2;

void slowdown(int viteza)
{
  if (sem == 2)
    analogWrite(pwmmotorA, 0);
  else
  {
    for (int i=viteza; i>=80; i--)
    {
      analogWrite(pwmmotorA, i);
      delay(10);
    }
    analogWrite(pwmmotorA, 0);
  }
}

void setup() 
{
  pinMode(dirmotorA, OUTPUT);
  pinMode(pwmmotorA, OUTPUT);
  
  pinMode(dir1motorB, OUTPUT);
  pinMode(dir2motorB, OUTPUT);
  pinMode(analogpin, OUTPUT);
  Serial.begin(9600);
}

void loop() 
{
  int i,viteza,val;
  boolean isValidInput;
  Serial.println( "-----------------------------" );
  Serial.println( "MENU:" );
  Serial.println( "1) Fast SPEED" );
  Serial.println( "2) Low SPEED" );
  Serial.println( "3) Soft stop (coast)" );
  Serial.println( "4) Left" );
  Serial.println( "5) Right" );
  Serial.println( "6) Hard stop (brake)" );
  Serial.println( "7) Forward" );
  Serial.println( "-----------------------------" );
  do
  {
    byte c;
    while( !Serial.available() );
    c = Serial.read();
    switch( c )
    {
      case '1': // 1) Fast SPEED
        Serial.println( "Fast SPEED..." );
        digitalWrite(dirmotorA, LOW);
        analogWrite(pwmmotorA, viteza_mare);
        sem = 1;
        isValidInput = true;
        break;      
         
      case '2': // 2) Low SPEED      
        Serial.println( "Low SPEED..." );
        digitalWrite(dirmotorA, LOW);
        analogWrite(pwmmotorA, viteza_mica);
        sem = 0;
        isValidInput = true;
        break;
         
      case '3': // 3) Soft stop
        Serial.println( "Soft stop" );
        digitalWrite(dirmotorA, LOW);
        if (sem == 1)
          viteza = viteza_mare;
        else
          viteza = viteza_mica;
          
        slowdown(viteza);

        digitalWrite(dir1motorB, LOW);
        digitalWrite(dir2motorB, LOW);
        isValidInput = true; sem = 2;
        break;      
 
      case '4': // 4) Left
        Serial.println( "Left" );
        digitalWrite(dirmotorA, LOW);
        if (sem == 1)
          analogWrite(pwmmotorA, viteza_mare);
        else
          analogWrite(pwmmotorA, viteza_mica);
        
        digitalWrite(dir1motorB, LOW);
        digitalWrite(dir2motorB, HIGH);
        analogWrite(dir1motorB, viteza_mareB);
        //digitalWrite(dir2motorB, LOW);

        delay(1000);
        val = analogRead(analogpin);
        Serial.println(val);
        isValidInput = true;
        break;      
      
      case '5': // 5) Right
        Serial.println( "Right" );
        digitalWrite(dirmotorA,LOW);
        if (sem == 1)
          analogWrite(pwmmotorA, viteza_mare);
        else
          analogWrite(pwmmotorA, viteza_mica);
        
        digitalWrite(dir1motorB, HIGH);
        digitalWrite(dir2motorB, LOW);
        analogWrite(dir2motorB, viteza_mareB);
        //digitalWrite(dir1motorB, LOW);
        delay(1000);
        
        isValidInput = true;
        val = analogRead(analogpin);
        Serial.println(val);
        break;
       
      case '6': // 6) Hard stop
        Serial.println( "Hard stop" );
        if (sem == 1)
          analogWrite(pwmmotorA, viteza_mare);
        else
          analogWrite(pwmmotorA, viteza_mica);
        analogWrite(pwmmotorA,0);
        
        digitalWrite(dir1motorB, LOW);
        digitalWrite(dir2motorB, LOW);
        isValidInput = true;
        break;      
      
      case '7': // 7) Forward
        
        Serial.println(sem);
        Serial.println( "Forward" );
        digitalWrite(dirmotorA, LOW);
        
        if (sem == 1)
          analogWrite(pwmmotorA, viteza_mare);
        else
          analogWrite(pwmmotorA, viteza_mica);
        
        val = analogRead(analogpin);
        if (val <= 450)
        {
          digitalWrite(dir1motorB, LOW);
          digitalWrite(dir2motorB, HIGH);
          while (val <= 400)
          {
            analogWrite(dir2motorB, 150);
            val = analogRead(analogpin);
            Serial.println(val);
          }
          digitalWrite(dir2motorB, LOW);
        }
        else
        {
          digitalWrite(dir1motorB, HIGH);
          digitalWrite(dir2motorB, LOW);
          while (val >= 600)
          {
            analogWrite(dir1motorB, 150);
            val = analogRead(analogpin);
            Serial.println(val);
          }
          digitalWrite(dir1motorB, LOW);
        }
        
        isValidInput = true;
        break;
      default:
        if (c > 7 || c < 1)
          Serial.println("Wrong character!");
        
        isValidInput = false;
        break;
    }
  } while( isValidInput == true );
}
