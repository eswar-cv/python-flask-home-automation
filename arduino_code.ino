// Including required libraries
#include <Adafruit_Fingerprint.h>
// BASIC DECLARATIONS ///////////////////////////////////////////////////////////////////////////////////////////////////////////
#if (defined(__AVR__) || defined(ESP8266)) && !defined(__AVR_ATmega2560__)
SoftwareSerial mySerial(2, 3);
#else
#define mySerial Serial1
#endif
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);
// BAISC DECLARATIONS ENDS HERE /////////////////////////////////////////////////////////////////////////////////////////////////////
// GLOBAL VARIABLES AND OTHER STUFF ///////////////////////////////////////////////////////////////////////////////////////////////////

bool checkfingerprint = 1;
bool checkroomlight = 1;
bool roomlighton = 0;
int roomlight = 13;
int gassensor = A0;
String fingerprintstatus = "checking";


// CODE TO CONTROL THE OPERATIONS RELATED TO FINGERPRINTS
uint8_t getFingerprintID() {
  Serial.println("checking for fingerprint");
  uint8_t p = finger.getImage();
  switch (p) {
    case FINGERPRINT_OK:
      Serial.println("Image taken");
      break;
    case FINGERPRINT_NOFINGER:
      return p;
    case FINGERPRINT_PACKETRECIEVEERR:
      Serial.println("Communication error");
      return p;
    case FINGERPRINT_IMAGEFAIL:
      Serial.println("Imaging error");
      return p;
    default:
      Serial.println("Unknown error");
      return p;
  }
  // OK success!
  p = finger.image2Tz();
  switch (p) {
    case FINGERPRINT_OK:
      Serial.println("Image converted");
      break;
    case FINGERPRINT_IMAGEMESS:
      Serial.println("Image too messy");
      return p;
    case FINGERPRINT_PACKETRECIEVEERR:
      Serial.println("Communication error");
      return p;
    case FINGERPRINT_FEATUREFAIL:
      Serial.println("Could not find fingerprint features");
      return p;
    case FINGERPRINT_INVALIDIMAGE:
      Serial.println("Could not find fingerprint features");
      return p;
    default:
      Serial.println("Unknown error");
      return p;
  }
  // OK converted!
  p = finger.fingerSearch();
  if (p == FINGERPRINT_OK) {
    Serial.println("Found a print match!");
  } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
    Serial.println("Communication error");
    return p;
  } else if (p == FINGERPRINT_NOTFOUND) {
    Serial.println("Did not find a match");
    return p;
  } else {
    Serial.println("Unknown error");
    return p;
  }
  // found a match!
  Serial.print("reportchange fingerprint detected "); Serial.println(finger.fingerID);
  return finger.fingerID;
}
// returns -1 if failed, otherwise returns ID #
int getFingerprintIDez() {
  uint8_t p = finger.getImage();
  if (p != FINGERPRINT_OK)  return -1;
  p = finger.image2Tz();
  if (p != FINGERPRINT_OK)  return -1;
  p = finger.fingerFastSearch();
  if (p != FINGERPRINT_OK)  return -1;
  // found a match!
  Serial.print("fingerprint found "); Serial.println(finger.fingerID);
  return finger.fingerID;
}
// CODE TO ENROLL FINGERPRINT/////////////////////////////////////////////////////////////////////
uint8_t getFingerprintEnroll(uint8_t id) {
  int p = -1;
  Serial.print("Waiting for valid finger to enroll as #"); Serial.println(id);
  delay(200);
  while (p != FINGERPRINT_OK) {
    delay(200);
    p = finger.getImage();
    delay(200);
    switch (p) {
    case FINGERPRINT_OK:
      Serial.println("Image taken");
      break;
    default:
      Serial.println("Unknown error");
      break;
    }
  }
  // OK success!
  p = finger.image2Tz(1);
  switch (p) {
    case FINGERPRINT_OK:
      Serial.println("Image converted");
      break;
      default:
      return p;
  }
  Serial.println("Remove finger");
  delay(2000);
  p = 0;
  while (p != FINGERPRINT_NOFINGER) {
    p = finger.getImage();
  }
  Serial.print("ID "); Serial.println(id);
  p = -1;
  Serial.println("Place same finger again");
  while (p != FINGERPRINT_OK) {
    delay(200);
    p = finger.getImage();
    delay(200);
    switch (p) {
    case FINGERPRINT_OK:
      Serial.println("Image taken");
      break;
    default:
      break;
    }
  }
  p = finger.image2Tz(2);
  switch (p) {
    case FINGERPRINT_OK:
      Serial.println("Image converted");
      break;
    default:
      return p;
  }
  Serial.print("Creating model for #");  Serial.println(id);
  p = finger.createModel();
  if (p == FINGERPRINT_OK) {
    Serial.println("Prints matched!");
  } 
  else{
    return p;
  } 
  Serial.print("ID "); Serial.println(id);
  p = finger.storeModel(id);
  if (p == FINGERPRINT_OK) {
    Serial.println("Stored!");
  } 
  else{
    return p;  
  }
  return true;
}
// CODE TO ENROLL FINGERPRINT ENDS HERE//////////////////////////////////////////////////////////////
// CODE TO DELETE FINGERPRINT STARTS HERE////////////////////////////////////////////////////////
uint8_t deleteFingerprint(uint8_t id) {
  uint8_t p = -1;
  p = finger.deleteModel(id);
  if (p == FINGERPRINT_OK) {
    Serial.println("Deleted!");
  } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
    Serial.println("Communication error");
  } else if (p == FINGERPRINT_BADLOCATION) {
    Serial.println("Could not delete in that location");
  } else if (p == FINGERPRINT_FLASHERR) {
    Serial.println("Error writing to flash");
  }
  return p;
}
// CODE TO DELETE FINGERPRINT ENDS HERE////////////////////////////////////////////////////////////////////
// COODES RELATED TO FINGERPRINT ENDS HERE ////////////////////////////////////////////////////////////////////
int ledpin = 12;
char DIVIDE_CHAR = ' ';
// MAIN SETUP OF THE CODE//////////////////////////////////////////////////////////////////////////////////////////////////
void setup(){
  pinMode(ledpin, OUTPUT);
  pinMode(roomlight, OUTPUT);
  pinMode(gassensor, INPUT);
  Serial.begin(9600);
  // wait till serial connection is established
  while (!Serial);  // For Yun/Leo/Micro/Zero/...
  delay(100);
  if (checkfingerprint){
  finger.begin(57600);
  delay(5);
  if (finger.verifyPassword()) {
    Serial.println("Fingerprint Sensor Detected");
  } else {
    Serial.println("Fingerprint Sensor Not Detected");
    // make the code idle and stop all actions to ensure that no issues are caused
    while (1) { delay(1); }
  }
  Serial.println(F("Reading sensor parameters"));
  finger.getParameters();
  Serial.print(F("Status: 0x")); Serial.println(finger.status_reg, HEX);
  Serial.print(F("Sys ID: 0x")); Serial.println(finger.system_id, HEX);
  Serial.print(F("Capacity: ")); Serial.println(finger.capacity);
  Serial.print(F("Security level: ")); Serial.println(finger.security_level);
  Serial.print(F("Device address: ")); Serial.println(finger.device_addr, HEX);
  Serial.print(F("Packet len: ")); Serial.println(finger.packet_len);
  Serial.print(F("Baud rate: ")); Serial.println(finger.baud_rate);
  finger.getTemplateCount();
  if (finger.templateCount == 0) {
    Serial.print("Sensor doesn't contain any fingerprint data. Please run the 'enroll' example.");
  }
  else {
    Serial.println("Waiting for valid finger...");
    Serial.print("Sensor contains "); Serial.print(finger.templateCount); Serial.println(" templates");
  }
  }
}
// MAIN SETUP ENDS HERE//////////////////////////////////////////////////////////////////////////////////////////////////
// FUNCTION TO FETCH INSTRUCTIONS FROM THE STRING
typedef struct Instructions{
  String main;
  String sub;
  String str1;
  String str2;
  int int1;
  int int2;
} Instructions;
struct Instructions FetchInstructions(String serialstring){
    int index = 0;
    String temp = "";
    Instructions data;
    int len = serialstring.length();
    // getting main command////////////////////////////////////////
    while (serialstring[index] != DIVIDE_CHAR && index < len){
      temp += serialstring[index];
      index += 1;
    }
    data.main = temp;
    temp = "";
    index += 1;
    // getting sub command/////////////////////////////////////////
    while (serialstring[index] != DIVIDE_CHAR && index < len){
      temp += serialstring[index];
      index += 1;
    }
    data.sub = temp;
    temp = "";
    index += 1;
    // getting first string////////////////////////////////////////
    while (serialstring[index] != DIVIDE_CHAR && index < len){
      temp += serialstring[index];
      index += 1;
    }
    data.str1 = temp;
    temp = "";
    index += 1;
    // getting second string//////////////////////////////////////
    while (serialstring[index] != DIVIDE_CHAR && index < len){
      temp += serialstring[index];
      index += 1;
    }
    data.str2 = temp;
    temp = "";
    index += 1;
    // getting first int///////////////////////////////////////////
    while (serialstring[index] != DIVIDE_CHAR && index < len){
      temp += serialstring[index];
      index += 1;
    }
    data.int1 = temp.toInt();
    temp = "";
    index += 1;
    // getting second int//////////////////////////////////////////
    while (serialstring[index] != DIVIDE_CHAR && index < len){
      temp += serialstring[index];
      index += 1;
    }
    data.int2 = temp.toInt();
    temp = "";
    index += 1;    
    return data;
}
// FUNCTION TO EXTRACT USER INSTRUCTIONS ENDS HERE
// FUNCTION TO CHECK FOR USER INSTRUCTIONS STARTS HERE
void CheckForInstructions(){
  if (Serial.available()){
    String serialstring = Serial.readStringUntil('\n');
    Serial.println(serialstring);
     if (serialstring.length() > 0){
      Instructions instructions = FetchInstructions(serialstring);
      ProcessInstruction(instructions);
      //Serial.println(instructions.main);
      //Serial.println(instructions.sub);
      //Serial.println(instructions.str1);
      //Serial.println(instructions.str2);
      //Serial.println(instructions.int1);
      //Serial.println(instructions.int2);
    }
  }
}
void ProcessInstruction(Instructions data){
  if (data.main == "fingerprint") ManageFingerprints(data);
  else if (data.main == "roomlight") ManageRoomlight(data);
}
int ManageFingerprints(Instructions data){
  if (checkfingerprint == 0) return 0;
  // if user requests to add a fingerprint
  if (data.sub == "add"){
    // getting the id of the fingerprint which should be added
    uint8_t fingerprint_id = data.int1;
    // enrolling the fingerprint by asking the user to place their finger
    getFingerprintEnroll(fingerprint_id);
    
  }
  // if user requests to delete a specific fingerprint
  else if (data.sub == "delete"){
    int fingerprint_id = data.int1;
    deleteFingerprint(fingerprint_id);
    
  }
  // if user requests to delete all fingerprints
  else if (data.sub == "empty"){
    finger.emptyDatabase();
  }
}
int ManageRoomlight(Instructions data){
  if (data.sub == "on"){
    checkroomlight = 1;
    roomlighton = 1;
  }
  else if (data.sub == "off"){
    roomlighton = 0;
    CheckLight();
    roomlighton = 0;
    digitalWrite(roomlight, LOW);
    checkroomlight = 0;
  }
  else if (data.sub == "auto"){
    checkroomlight = 1;
    roomlighton = 0;
  }
}
int gassensor_send(){
  int reading = analogRead(gassensor);
  Serial.print("reportchange gassensor "); Serial.println(reading);
}
int CheckLight(){
  int reading = analogRead(A0);
  if ((checkroomlight && reading < 75) || roomlighton){
    digitalWrite(roomlight, HIGH);
    Serial.println("reportchange roomlight on");
  }
  
  else {
    digitalWrite(roomlight, LOW); 
    Serial.println("reportchange roomlight off");
  }
}
// MAIN LOOP CODE STARTS HERE
void loop(){
  delay(500);
  CheckForInstructions();
  if (checkroomlight) CheckLight();
  if (checkfingerprint) getFingerprintID();
  gassensor_send();
}