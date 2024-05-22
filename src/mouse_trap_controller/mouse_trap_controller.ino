#include <Servo.h>

#define Rate           9600 // should be == multim.py
#define DoorDelay      500  // @ telmo - why do we need this?
#define SensorDistance 15   // trigger distance to send SENSOR_E (cm)

#define SensorInputPin  5 // SENSOR INPUT  PIN
#define SensorOutputPin 6 // SENSOR OUTPUT PIN
#define ServoOuputPin   9 // SERVO  OUTPUT PIN


Servo servo;


String DoorStatus = "OPEN"; // current door status
bool   freshValue = true;   // new SENSOR_E?

unsigned long timestamp = 0; // msg timestamp
unsigned long messageID = 0; // msg ID


void setup() {
    // SETUP SENSOR //
    pinMode(SensorInputPin,INPUT);
    pinMode(SensorOutputPin,OUTPUT);
    
    // OPEN DOOR (at the start) //
    actuateServo("OPEN_R");

    // RASPPI //
    Serial.begin(Rate);
}

void loop() {
    digitalWrite(SensorOutputPin,LOW);   // @ telmo - LOW?
    delayMicroseconds(2);               // @ telmo - why this?
    digitalWrite(SensorOutputPin,HIGH); // @ telmo - HIGH?
    delayMicroseconds(10);              // @ telmo - why this?
    digitalWrite(SensorOutputPin,LOW);  // @ telmo - LOW?
    
    float currentDuration = pulseIn(SensorInputPin,HIGH);  // @ telmo - reading pulse?
    float currentDistance = currentDuration * 0.0343 / 2;  // @ telmo - calculating distance from travel time?
  
    delay(50); // @ telmo - what are we delaying here?
    
    // @ telmo - is there something new worth reporting to multim.py?
    if (currentDistance <= SensorDistance && freshValue) {
         timestamp = millis(); // @ telmo - not quite
         String message = String(messageID) + "@" + String(timestamp) + "@" + "SENSOR_E" + "@";
         Serial.println(message);
         messageID++;
         freshValue = false;
    }
    // @ telmo - if we had something inside... we don't anymore
    // @ telmo - if something is in it should be a new something
    else if (currentDistance > SensorDistance) {
      freshValue = true;
    }   
    // @ telmo - is there something new reported from multim.py?
    if (Serial.available()) {
      // @ telmo - CRISTINA code block begins //
      String message = Serial.readStringUntil('\n');
      int pos2 = message.indexOf('@');
      int pos3 = message.indexOf('@', pos2 + 1);
      int pos4 = message.indexOf('@', pos3 + 1);
      String flag = message.substring(pos3 + 1, pos4);
      // @ telmo - CRISTINA code block ends //
      if ((flag == "OPEN_R" && DoorStatus == "CLOSE") || (flag == "CLOSE_R" && DoorStatus == "OPEN")) {
        actuateServo(flag);
      }
    }
}

void actuateServo(String flag) {
  if (flag == "CLOSE_R") {
    servo.attach(ServoOuputPin);
    servo.write(0);
    delay(DoorDelay); // @ telmo - why do we need to delay?
    servo.detach();
    DoorStatus = "CLOSE";
  }
  else if (flag == "OPEN_R") {
    servo.attach(ServoOuputPin);
    servo.write(180);
    delay(DoorDelay); // @ telmo - why do we need to delay?
    servo.detach();
    DoorStatus = "OPEN";
  }
  else Serial.write("OOPS!");
}