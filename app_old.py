# importing required modules
import time
import json
from gevent.pywsgi import WSGIServer
from flask import Flask, Response, render_template, stream_with_context
from gevent import monkey
import os
from time import sleep
monkey.patch_all()
TEMPLATE_DIR = os.path.abspath('../templates')
STATIC_DIR = os.path.abspath('../static')
# creating flask object
app = Flask(__name__)
counter = 0
SEND_DATA = True


# Main Data Structure
Data = {
    "light": {
        "status": "on", "mode": "on"
    },
    "fingerprint": {
        "status": "off", "mode": "None"
    }
}
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
    print(json.dumps(Data))
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
    print(Data)
    SEND_DATA = True





if __name__ == "__main__":
    http_server = WSGIServer(("localhost", 80), app)
    http_server.serve_forever()
