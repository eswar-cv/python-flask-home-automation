import json
from sys import platform
from gevent.pywsgi import WSGIServer
from flask import Flask, Response, render_template, stream_with_context
from gevent import monkey
import os
if platform != "win32":
    exec("import serial")
    exec("from picamera import PiCamera")
    exec("camera = PiCamera()")
else:
    import pyautogui as ui
from time import time, sleep
from threading import Thread

from multiprocessing import Process
# monkey.patch_all()
TEMPLATE_DIR = os.path.abspath('../templates')
STATIC_DIR = os.path.abspath('../static')
# creating flask object
app = Flask(__name__)
counter = 0
SEND_DATA = True



# Main Data Structure
Data = {
    "light": {
        "status": "on", "mode": "auto"
    },
    "fan": {
        "status": "on", "mode": "auto"
    },
    "fingerprint": {
        "status": "off", "mode": "None"
    }
}

def gen():
    if platform != "win32":
        start = time()
        try:
            exec('camera.capture("/home/pi/mainfiles/pic.jpg", use_video_port= True)')
            print(f"image saved. time taken: {time() - start}")
        except:
            os.system("raspistill -o /home/pi/mainfiles/pic.jpg")
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

@app.route("/setmode/<main>/<sub>")
def showinfo(main, sub):
    print(f"{main} --> {sub}")
    ProcessMode(main, sub)
    return {}

def ProcessMode(main, sub):
    global Data
    if main in ["light", "fan"]:
        Data[main]["mode"] = sub
        if sub in ["on", "off"]:
            Data[main]["status"] = sub
        if main == "light" and platform != "win32": 
            SerialWrite(f"roomlight {sub}")
    SEND_DATA = True

#!/usr/bin/env python3
if platform == "win32":
    serial = "serial"
if platform != "win32":
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.reset_input_buffer()

    def SerialRead():
        while True:
            print("Waiting for serial input")
            line = ser.readline().decode('utf-8').rstrip()
            if line != "" and line != "\n":
                print(f"| {line}")
    Thread(target = SerialRead).start()

    def SerialWrite(string):
        ser.write((string + "\n").encode("utf-8"))


    def SerialWriteUserInput():
        while True:
            ser.write((input("--> ") + "\n").encode("utf-8"))

if __name__ == "__main__":
    app.run(port=80, host='0.0.0.0', threaded = True)

