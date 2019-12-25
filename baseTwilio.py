import requests
from twilio import twiml
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import random as rand
import threading
import json
import time
from flask import Flask, request

app = Flask(__name__)

twilioAccountID = ""
twilioAuth = ""

blockedList = []

inProgress = {}
class myThread(threading.Thread):  # Thread created upon request
    def __init__(self, name, sendnum, msgbody):
        threading.Thread.__init__(self)
        self.name = name
        self.sendnum = sendnum
        self.msgbody = msgbody
    def run(self):
        print("Fetching request to " + self.sendnum)
        verifyProcess(self.msgbody, self.sendnum)
        print("Finished request to " + self.sendnum)

def verifyProcess(msg, num):
    global inProgress


@app.route("/sms", methods=['POST'])
def receiveText():  # Code executed upon receiving text
    number = request.form['From']
    message_body = request.form['Body']
    print(str(message_body) + "received from: " + str(number))
    print("------")
    resp = MessagingResponse()
    t = myThread(number, number, message_body)
    t.start()
    return (str(resp))

def sendText(number, msg):  # Code to send outgoing text
    account_sid = twilioAccountID
    auth_token = twilioAuth
    client = Client(account_sid, auth_token)
    message = client.messages \
        .create(
        body=str(msg),
        from_='+12053950843',
        to=str(number)
    )

def loadFiles(): #Loads Twilio account info off twilio.json
    global twilioAuth
    global twilioAccountID
    global blockedList
    with open("twilio.json", "r") as read_file:
        data = json.load(read_file)
    twilioAuth = str(data["twilioAuth"])
    twilioAccountID = str(data["twilioID"])
    with open("blocked.json", "r") as read_file:
        blockedList = json.load(read_file)

if __name__ == "__main__": #starts the whole program
    print("started")
    loadFiles()
    app.run(host='0.0.0.0', port=5001)