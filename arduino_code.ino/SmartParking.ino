#include <Servo.h>
#include <TimeLib.h>  // Required for day() function

// Entry Gate
#define trigEntry 2
#define echoEntry 3
#define servoEntryPin 5
#define redLEDEntry 6
#define greenLEDEntry 7
#define buzzerEntry 8

// Exit Gate
#define trigExit 9
#define echoExit 10
#define servoExitPin 11
#define redLEDExit A0
#define greenLEDExit A1
#define buzzerExit A2

Servo servoEntry;
Servo servoExit;

// Parking counters
int currentCars = 0;
int totalEnteredToday = 0;
int totalExitedToday = 0;
const int maxCars = 4;

// For tracking day changes
unsigned long lastDayCheck = 0;
int lastDay = -1;

long readUltrasonic(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW); 
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH);
  return duration * 0.034 / 2;
}

void checkDayChange() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastDayCheck >= 60000) { // Check every minute
    lastDayCheck = currentMillis;
    
    // Get current day (requires TimeLib.h)
    int currentDay = day();
    
    // If day changed, reset daily counters
    if (lastDay != -1 && currentDay != lastDay) {
      totalEnteredToday = 0;
      totalExitedToday = 0;
      // Optional: Send reset notification
      Serial.println("DAY_CHANGE: Counters reset for new day");
    }
    
    lastDay = currentDay;
  }
}

void sendParkingData() {
  Serial.print("PARKING_DATA:");
  Serial.print("ENTERED="); Serial.print(totalEnteredToday); Serial.print(",");
  Serial.print("CURRENT="); Serial.print(currentCars); Serial.print(",");
  Serial.print("EXITED="); Serial.print(totalExitedToday); Serial.print(",");
  Serial.print("CAPACITY="); Serial.println(maxCars);
}

void setup() {
  Serial.begin(9600);

  // Set initial time (you'll need to set this to current time)
  // Format: setTime(hours, minutes, seconds, day, month, year);
  // Example: setTime(12, 0, 0, 25, 5, 2024); // 25th May 2024, 12:00:00
  // Set initial time (hr, min, sec, day, month, year)
  setTime(12, 0, 0, 25, 5, 2024); // Example: May 25, 2024 at 12:00:00
  // Entry gate setup
  pinMode(trigEntry, OUTPUT);
  pinMode(echoEntry, INPUT);
  pinMode(redLEDEntry, OUTPUT);
  pinMode(greenLEDEntry, OUTPUT);
  pinMode(buzzerEntry, OUTPUT);
  servoEntry.attach(servoEntryPin);

  // Exit gate setup
  pinMode(trigExit, OUTPUT);
  pinMode(echoExit, INPUT);
  pinMode(redLEDExit, OUTPUT);
  pinMode(greenLEDExit, OUTPUT);
  pinMode(buzzerExit, OUTPUT);
  servoExit.attach(servoExitPin);

  // Initialize gates to closed
  servoEntry.write(0);
  servoExit.write(0);
  
  // Initialize LEDs
  digitalWrite(redLEDEntry, HIGH);
  digitalWrite(redLEDExit, HIGH);
  digitalWrite(greenLEDEntry, LOW);
  digitalWrite(greenLEDExit, LOW);
}

void loop() {
  checkDayChange();
  
  // ---------- ENTRY GATE ----------
  long entryDistance = readUltrasonic(trigEntry, echoEntry);

  if (entryDistance < 15 && currentCars < maxCars) {
    digitalWrite(greenLEDEntry, HIGH);
    digitalWrite(redLEDEntry, LOW);
    digitalWrite(buzzerEntry, HIGH); 
    delay(100); 
    digitalWrite(buzzerEntry, LOW);

    servoEntry.write(90); // Open gate
    delay(500); // Allow car to move
  } 
  else if (entryDistance >= 15 && servoEntry.read() == 90) {
    servoEntry.write(0); // Close gate
    currentCars++;
    totalEnteredToday++;
    digitalWrite(greenLEDEntry, LOW);
    digitalWrite(redLEDEntry, HIGH);
    sendParkingData();
    delay(1000);
  } 
  else {
    digitalWrite(greenLEDEntry, LOW);
    digitalWrite(redLEDEntry, HIGH);
  }

  // ---------- EXIT GATE ----------
  long exitDistance = readUltrasonic(trigExit, echoExit);

  if (exitDistance < 15 && currentCars > 0) {
    digitalWrite(greenLEDExit, HIGH);
    digitalWrite(redLEDExit, LOW);
    digitalWrite(buzzerExit, HIGH); 
    delay(100); 
    digitalWrite(buzzerExit, LOW);

    servoExit.write(90); // Open gate
    delay(500); // Allow car to move
  } 
  else if (exitDistance >= 15 && servoExit.read() == 90) {
    servoExit.write(0); // Close gate
    currentCars--;
    totalExitedToday++;
    digitalWrite(greenLEDExit, LOW);
    digitalWrite(redLEDExit, HIGH);
    sendParkingData();
    delay(1000);
  } 
  else {
    digitalWrite(greenLEDExit, LOW);
    digitalWrite(redLEDExit, HIGH);
  }

  // Send data periodically (every 5 seconds)
  static unsigned long lastSendTime = 0;
  if (millis() - lastSendTime >= 5000) {
    lastSendTime = millis();
    sendParkingData();
  }

  delay(200);
}