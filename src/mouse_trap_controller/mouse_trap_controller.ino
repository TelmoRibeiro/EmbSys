#include <Servo.h>

#define Rate           9600 // should be == multim.py
#define DoorDelay      500
#define SensorDistance 15

#define SensorInputPin  5 // SENSOR INPUT  PIN
#define SensorOutputPin 6 // SENSOR OUTPUT PIN
#define ServoOuputPin   9 // SERVO  OUTPUT PIN

Servo servo;

String doorStatus = "OPEN";  // current door status
String toSendFlag = "NULL";  // RASPI input

bool freshValue = false;  // needed as this!

unsigned long lastTS = 0; //

unsigned long messageID = 1;  // msg ID

void setup() {
  // SETUP SENSOR
  pinMode(SensorInputPin,INPUT);
  pinMode(SensorOutputPin,OUTPUT);
  // OPEN DOOR (at the start)
  actuateServo("OPEN_R");
  // RASPPI
  Serial.begin(Rate);
}

void loop() {
  float currentDistance = getCurrentDistance();
  unsigned long messageTS = millis(); // @ telmo - not quite timestamp

  delay(100);

  if (toSendFlag != "NULL") {
    String message = String(messageID) + "@" + String(messageTS) + "@" + toSendFlag + "@";
    Serial.println(message);
    messageID++;
    toSendFlag = "NULL";
  }
  else if (currentDistance <= SensorDistance && freshValue && doorStatus == "OPEN") {
    String message = String(messageID) + "@" + String(messageTS) + "@" + "SENSOR_E" + "@";
    Serial.println(message);
    messageID++;
    freshValue = false;
    lastTS = messageTS;
  }
  else if (currentDistance > SensorDistance && messageTS >= lastTS + 10000) {
    freshValue = true;
  }
  if (Serial.available()) {
    // @ telmo - CRISTINA code block begins //
    String message = Serial.readStringUntil('\n');
    int pos2 = message.indexOf('@');
    int pos3 = message.indexOf('@', pos2 + 1);
    int pos4 = message.indexOf('@', pos3 + 1);
    String flag = message.substring(pos3 + 1, pos4);
    // @ telmo - CRISTINA code block ends //
    if (flag == "OPEN_R" && doorStatus == "CLOSE") {
      toSendFlag = "OPEN_E";
      actuateServo(flag);
    } else if (flag == "CLOSE_R" && doorStatus == "OPEN") {
      toSendFlag = "CLOSE_E";
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
    doorStatus = "CLOSE";
  }
  else if (flag == "OPEN_R") {
    servo.attach(ServoOuputPin);
    servo.write(180);
    delay(DoorDelay); // @ telmo - why do we need to delay?
    servo.detach();
    doorStatus = "OPEN";
  }
  else Serial.write("OOPS!");
}

float getCurrentDistance() {
  digitalWrite(SensorOutputPin,LOW);
  delayMicroseconds(2);
  digitalWrite(SensorOutputPin,HIGH);
  delayMicroseconds(10);
  digitalWrite(SensorOutputPin,LOW);
    
  float currentDuration = pulseIn(SensorInputPin,HIGH);
  return currentDuration * 0.0343 / 2;  
}