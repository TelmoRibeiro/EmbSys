#include <Servo.h>

#define Rate           9600
#define DoorDelay      500
#define SensorDistance 15

#define SensorInputPin  5 // SENSOR INPUT  PIN
#define SensorOutputPin 6 // SENSOR OUTPUT PIN
#define ServoOuputPin   9 // SERVO  OUTPUT PIN

Servo servo;

String doorStatus = "OPEN";  // current door status
String toSendFlag = "NULL";  // RASPI input

bool freshValue = false;

unsigned long lastTimestamp = 0;

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
  unsigned long msg_timestamp = millis(); // @ telmo - not quite timestamp

  delay(100);

  if (toSendFlag != "NULL") {
    String message = toSendFlag + "@" + "None" + "@" + String(msg_timestamp) + "@";
    Serial.println(message);
    toSendFlag = "NULL";
  }
  else if (currentDistance <= SensorDistance && freshValue && doorStatus == "OPEN") {
    String message = String("SENSOR_E") + "@" + "None" + "@" + String(msg_timestamp) + "@"; // @ telmo - do not ask about it, C++ is dumb...
    Serial.println(message);
    freshValue = false;
    lastTimestamp = msg_timestamp;
  }
  else if (currentDistance > SensorDistance && msg_timestamp >= lastTimestamp + 10000) {
    freshValue = true;
  }
  if (Serial.available()) {
    // @ telmo - CRISTINA code block begins //
    String message = Serial.readStringUntil('\n');
    int posA = message.indexOf('@');
    int posB = message.indexOf('@',posA + 1);
    int posC = message.indexOf('@',posB + 1);
    String flag = message.substring(0,posA);
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