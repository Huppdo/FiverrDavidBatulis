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

questionList = {}

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
    msg = msg.replace(" ","")
    if str(num[1:]) in inProgress.keys():
        for question in inProgress[str(num[1:])].keys():
            if inProgress[str(num[1:])][question] != -1:
                continue
            else:
                if verifyAnswer(msg, num, question):
                    inProgress[str(num[1:])][question] = msg
                    if questionList[list(questionList.keys())[list(questionList.keys()).index(question)+1]]["question"] == "END":
                        sendReport(num)
                    else:
                        sendText(num, questionList[list(questionList.keys())[list(questionList.keys()).index(question)+1]]["question"])
                break
    elif "start" in str(msg).lower():
        inProgress[str(num[1:])] = {'Q1': -1,'Q2': -1,'Q3': -1,'Q4': -1,'Q5': -1,'Q6': -1,'Q7': -1,'Q8': -1,'Q9': -1,'Q10': -1,'Q11': -1,'Q12': -1,'Q13': -1,'Q14': -1,'Q15': -1,'Q16': -1,'Q17': -1,'Q18': -1,'Q19': -1,'Q20': -1,'Q21': -1,'Q22': -1,'Q23': -1,'Q24': -1}
        sendText(num, "Insert welcome message, reply STOP to stop")
        sendText(num, questionList["Q1"]["question"])

def removeNum(num):
    global blockedList
    blockedList.append(num)
    with open("blocked.json", "r") as read_file:
        blockedList = json.load(read_file)

def sendReport(num):
    print("This report is from: " + str(num))
    for question in inProgress[str(num[1:])].keys():
        if questionList[question]["question"] == "END":
            del inProgress[str(num[1:])]
            return
        else:
            print(str(questionList[question]["question"]) + ": " + inProgress[str(num[1:])][question])
    del inProgress[str(num[1:])]

def verifyAnswer(msg, num, question):
    if str(msg).replace(".","").isdigit():
        try:
            intMsg = float(msg)
        except:
            sendText(num, "There was an error processing your answer. Please try again only using digits and no whitespaces.")
            return False
        if intMsg >= questionList[question]["min"] and intMsg <= questionList[question]["max"]:
            return True
        else:
            sendText(num, "Your answer needs to be between " + str(questionList[question]["min"]) + " and " + str(questionList[question]["max"]))
    else:
        if "-" in str(msg):
            sendText(num, "Your answer needs to be between " + str(questionList[question]["min"]) + " and " + str(questionList[question]["max"]))
        else:
            sendText(num, "Please only send messages with numerical digits and no whitespace")


@app.route("/sms", methods=['POST'])
def receiveText():  # Code executed upon receiving text
    number = request.form['From']
    message_body = request.form['Body']
    print(str(message_body) + " received from: " + str(number))
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
        from_='+16143502814',
        to=str(number)
    )

def loadFiles(): #Loads Twilio account info off twilio.json
    global twilioAuth
    global twilioAccountID
    global blockedList
    global questionList
    with open("twilio.json", "r") as read_file:
        data = json.load(read_file)
    twilioAuth = str(data["twilioAuth"])
    twilioAccountID = str(data["twilioID"])
    with open("blocked.json", "r") as read_file:
        blockedList = json.load(read_file)
    with open("questions.json", "r") as read_file:
        questionList = json.load(read_file)

if __name__ == "__main__": #starts the whole program
    print("started")
    loadFiles()
    app.run(host='0.0.0.0', port=5001)