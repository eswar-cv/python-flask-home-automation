import json
#!/usr/bin/env python3
import serial
from time import time
from threading import Thread
from multiprocessing import Process
from sys import platform
from gevent.pywsgi import WSGIServer
from flask import Flask, Response, render_template, stream_with_context
from gevent import monkey
import os
import RPi.GPIO as GPIO
from mpu6050 import mpu6050
sensor = mpu6050(0x68)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
from time import sleep
GPIO.setup(16, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
OPEN = 16
CLOSE = 18
GPIO.setmode(GPIO.BOARD)
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(37, GPIO.OUT)
    #exec("from picamera import PiCamera")
    #exec("camera = PiCamera()")
# monkey.patch_all()
TEMPLATE_DIR = os.path.abspath('../templates')
STATIC_DIR = os.path.abspath('../static')
# creating flask object
app = Flask(__name__)
counter = 0
SEND_DATA = True

def DoorControl(PORT, duration):
    GPIO.setmode(GPIO.BOARD)
    GPIO.output(PORT, GPIO.HIGH)
    sleep(duration)
    GPIO.setmode(GPIO.BOARD)
    GPIO.output(PORT, GPIO.LOW)

# Main Data Structure
Data = {
    "light": {
        "status": "on", "mode": "auto"
    },
    "fan": {
        "status": "on", "mode": "auto"
    },
    "fingerprint": {
        "last_event": None, "mode": "Checkikng for fingerprint"
    },
    "gasreading": 0,
    "temperature": {},
}

def gen():
    if platform != "win32":
        #start = time()
        #os.system("raspistill -o /home/pi/mainfiles/pic.jpg")
        return (b'--frame\r\n' 
            b'Content-Type: image/jpeg\r\n\r\n' + open('/home/pi/mainfiles/pic.jpg', 'rb').read() + b'\r\n') 
    else:
        ui.screenshot().save("pic.jpg")
        return (b'--frame\r\n' 
            b'Content-Type: image/jpeg\r\n\r\n' + open('pic.jpg', 'rb').read() + b'\r\n') 


@app.route('/video_feed')
def video_feed():
    print("Video feed route called")
    """Video streaming route. Put this in the src attribute of an img tag.""" 
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame') 

# sending main page to user
@app.route("/")
def render_index():
    global SEND_DATA
    SEND_DATA = True
    return render_template("index.html")


# Sending data to user on event trigger
# changing the value of SEND_DATA to True will make the code to send message to user
# SEND_DATA will be set to False after sending data to user
# the data is used to change the content of page
# Front-end changes wont occour unless there is a command from backend
# This will prevent conflits between the current stage of page and system


@app.route("/listen")
def listen():
    # def SendData():
    #     print("SendData() Called")
    #     global SEND_DATA
    #     while True:
    #         while not SEND_DATA:
    #             pass
    #         sleep(1)
    #         yield f"data: {json.dumps(Data)}\nevent: data\n\n"
    #         print(f"data sent: {json.dumps(Data)}")
    #         #SEND_DATA = False
    return Response(json.dumps(Data), mimetype='text/event-stream')

@app.route("/setmode/<main>/<sub>/<number>")
def showinfo(main, sub, number):
    print(f"{main} --> {sub} --> {number}")
    ProcessMode(main, sub, number)
    return Response(json.dumps(Data), mimetype='text/event-stream')

def DoorUnlock():
    DoorControl(OPEN, 4.5)
    sleep(5)
    DoorControl(CLOSE, 4.5)

def ProcessMode(main, sub, number = -1):
    global Data
    if main in ["light", "fan"]:
        Data[main]["mode"] = sub
        if sub in ["on", "off"]:
            Data[main]["status"] = sub
        if main == "light" and platform != "win32": 
            SerialWrite(f"roomlight {sub}")
    if main == "fingerprint":
        print("Processing fingerprint command")
        if int(number) in range(0, 101):
            print("Sending input to arduino")
            Data["fingerprint"]["last"] = f"{sub} id {number}"
            if platform != "win32":
                print((f"{main} {sub} _ _ {number}"))
                SerialWrite(f"{main} {sub} _ _ {number}")
    SEND_DATA = True

#!/usr/bin/env python3
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.reset_input_buffer()

def UpdateTemp():
    while True:
        try:
            GPIO.output(37, GPIO.LOW)
            readings = sensor.get_all_data()
            Data["temperature"] = int(readings[2])
        except:
            GPIO.output(37, GPIO.LOW)
            print("Failed to get data from sensor")
            Data["temperature"] = 30
        #Data["fan"] = {'status': 'off', 'mode': 'off'}
        #print(Data["fan"])
        if ((Data["temperature"] > 25 and Data["fan"]["mode"] == "auto") or Data["fan"]["mode"] == "on") and Data["fan"]["mode"] != "off":
            if Data["fan"]["mode"] != "off" and Data["fan"]["status"] != "off":
                GPIO.output(37, GPIO.LOW)
                GPIO.output(37, GPIO.HIGH)
                print("\nFan On\n")
                Data["fan"]["status"] = "on"
        else:
            GPIO.output(37, GPIO.LOW)
            print("\nFan On\n")
            Data["fan"]["status"] = "off"
        if Data["fan"]["mode"] == "off":
            print("\nFan Off\n")
            GPIO.output(37, GPIO.LOW)
            Data["fan"]["status"] = "off"
            
        print(f"Temperature: {Data['temperature']}")
        sleep(5)
Thread(target = UpdateTemp).start()

def DoorControl(PORT, duration):
    GPIO.output(PORT, GPIO.HIGH)
    sleep(duration)
    GPIO.output(PORT, GPIO.LOW)
    
def SerialRead():
    while True:
        #try:
            line = ser.readline().decode('utf-8').rstrip()
            if line != "" and line != "\n":
                if "reportchange" in line:
                    ProcessChange(line);
                else:
                    print(f"| {line}")
        #except KeyboardInterrupt:
        #    exit
        #except:
        #    print("\n\nError occoured while reading data form serial connection\n\n")
unlocking = False
def ProcessChange(line):
    global unlocking
    if "reportchange fingerprint detected" in line and unlocking == False:
        unlocking = True
        GPIO.setmode(GPIO.BOARD)
        DoorUnlock()
        unlocking = False
    else:
        line = line.split()
        if line[1] == "gassensor":
            print(f"Gassensor {line[2]}")
            gasreading = int(line[2])
            Data["gasreading"] = gasreading;
            
Process(target = SerialRead).start()
def CaptureFeed():
    while True:
        #os.system("raspistill -t 10000 -tl 1000 -o /home/pi/mainfiles/pic.jpg")
        os.system("raspistill -o /home/pi/mainfiles/pic.jpg")
        print("Stored image")
        sleep(2)
#Process(target = CaptureFeed).start()
def SerialWrite(string):
    ser.write((string + "\n").encode("utf-8"))


def SerialWriteUserInput():
    while True:
        ser.write((input("--> ") + "\n").encode("utf-8"))

if __name__ == "__main__":
    app.run(debug = True, port=8000, host='0.0.0.0', threaded = True)
# update now
