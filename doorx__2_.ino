// DoorX — Arduino Controller
// Servo Motor + Green/Red LED Access Control
// Upload this to Arduino UNO via Arduino IDE

#include <Servo.h>

Servo doorServo;

const int SERVO_PIN  = 9;
const int GREEN_LED  = 7;
const int RED_LED    = 6;

const int DOOR_OPEN_ANGLE   = 90;   // angle when door is OPEN
const int DOOR_CLOSED_ANGLE = 0;    // angle when door is CLOSED

void setup() {
  Serial.begin(9600);
  doorServo.attach(SERVO_PIN);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  // Boot state: door closed, red on
  doorServo.write(DOOR_CLOSED_ANGLE);
  digitalWrite(RED_LED, HIGH);
  digitalWrite(GREEN_LED, LOW);

  Serial.println("DOORX_READY");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "GRANT") {
      grantAccess();
    }
    else if (cmd == "DENY") {
      denyAccess();
    }
    else if (cmd == "RESET") {
      resetDoor();
    }
  }
}

void grantAccess() {
  // Green LED ON, Red OFF
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);

  // Open door (servo to 90 degrees)
  doorServo.write(DOOR_OPEN_ANGLE);
  Serial.println("DOOR_OPENED");

  // Keep open for 4 seconds
  delay(4000);

  // Auto close
  resetDoor();
}

void denyAccess() {
  // Red LED blink 3 times (alert)
  digitalWrite(GREEN_LED, LOW);
  for (int i = 0; i < 3; i++) {
    digitalWrite(RED_LED, HIGH);
    delay(200);
    digitalWrite(RED_LED, LOW);
    delay(200);
  }
  // Leave red on
  digitalWrite(RED_LED, HIGH);
  doorServo.write(DOOR_CLOSED_ANGLE);
  Serial.println("ACCESS_DENIED");
}

void resetDoor() {
  doorServo.write(DOOR_CLOSED_ANGLE);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);
  Serial.println("DOOR_CLOSED");
}
