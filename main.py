import requests
from twilio import twiml
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import random as rand
import threading
import json
import time
from flask import Flask, request
import smtplib, ssl

#pick whether app is in Demo mode
demoMode = False

#pick if email sends full question or just question Code
fullQuestion = False

#define Flask app
app = Flask(__name__)

#init blank variables
twilioAccountID = ""
twilioAuth = ""

blockedList = []

questionList = {}

inProgress = {}

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "instantalk.alerts@gmail.com"  # Enter your address
receiver_email = "dbatulis@icloud.com"  # Enter receiver address
gmail_password = ""

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

#Main function ran upon new text
def verifyProcess(msg, num):
    print()
    msg = msg.replace(" ","")
    #if number is in progress
    if str(num[1:]) in inProgress.keys():
        for question in inProgress[str(num[1:])].keys():
            #find first unanswered question
            if inProgress[str(num[1:])][question] != -1:
                continue
            #First unanswered
            else:
                #If the answer is formatted right
                if verifyAnswer(msg, num, question):
                    #Set question variable to answer
                    if question == "Q0":
                        inProgress[str(num[1:])][question] = str(msg)
                    else:
                        inProgress[str(num[1:])][question] = msg

                    #If the next question is END
                    if questionList[list(questionList.keys())[list(questionList.keys()).index(question)+1]]["question"] == "END":
                        sendText(num, "Thank you, you have finished all of your questions!")
                        sendReport(num)
                    #else send next question
                    else:
                        sendText(num, questionList[list(questionList.keys())[list(questionList.keys()).index(question)+1]]["question"])
                break
    #If number not in progress
    else:
        inProgress[str(num[1:])] = {'Q0': -1, 'Q1': -1,'Q2': -1,'Q3': -1,'Q4': -1,'Q5': -1,'Q6': -1,'Q7': -1,'Q8': -1,'Q9': -1,'Q10': -1,'Q11': -1,'Q12': -1,'Q13': -1,'Q14': -1,'Q15': -1,'Q16': -1,'Q17': -1,'Q18': -1,'Q19': -1,'Q20': -1,'Q21': -1,'Q22': -1,'Q23': -1,'Q24': -1}
        sendText(num, "You have been accepted into AboveBoard! Please answer all 20 questions by responding with numbers from 0-24 or 0-100 or characters when specified.")
        sendText(num, "Respond STOP at any time to opt out. Copyright Pro Fee LLC 2019")
        sendText(num, questionList["Q0"]["question"])

#if running custom Optout
def removeNum(num):
    global blockedList
    blockedList.append(num)
    with open("blocked.json", "r") as read_file:
        blockedList = json.load(read_file)

#Send email report
def sendReport(num):
    msgStr = """"""
    msgStr += "Subject: " + str(num) + "\n\n"
    msgStr += "This email was generated from - " + str(num) + "\n"
    for question in inProgress[str(num[1:])].keys():
        if questionList[question]["question"] == "END":
            del inProgress[str(num[1:])]
            break
        else:
            msgStr += pickIdentify(question) + ": raw answer = " + inProgress[str(num[1:])][question] + ",  weighted score = " + solveScore(question, inProgress[str(num[1:])][question])+ "\n"
    print(msgStr)
    #Open email server
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, gmail_password)
        server.sendmail(sender_email, receiver_email, msgStr)

def pickIdentify(question):
    if fullQuestion:
        return str(questionList[question]["question"])
    else:
        return str(questionList[question]["ID"])

def solveScore(question, answer):
    #Adjusted Score
    if question == "Q1" or question == "Q4" or question == "Q19":
        return str(float(answer)/24)
    #Organic Score 24hrs
    elif question == "Q2" or question == "Q3":
        return str((24-float(answer)) / 24)
    #Normal Score
    elif question == "Q5" or question == "Q8" or question == "Q9" or question == "Q11" or question == "Q14" or question == "Q16" or question == "Q0":
        return str(answer)
    #Organic Score 100%
    elif question == "Q6" or question == "Q7" or question == "Q10" or question == "Q12" or question == "Q13" or question == "Q15":
        return str(100 - float(answer))
    elif question == "Q17" or question == "Q18" or question == "Q20":
        return str(float(answer) / 30)
    elif question == "Q21" or question == "Q22":
        return str((30-float(answer)) / 30)
    elif question == "Q21":
        return str(100 - float(answer))
    else:
        return str("No scoring available")


#Verify answer formatting
def verifyAnswer(msg, num, question):
    print(question)
    if question == "Q0":
        if len(msg) <= 40:
            return True
        else:
            sendText(num, "Your message was too long, please only use 40 digits or less.")
            return False
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

#Code run by Twilio for text
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

#Base function for sending a text with a number and msg
def sendText(number, msg):  # Code to send outgoing text
    account_sid = twilioAccountID
    auth_token = twilioAuth
    client = Client(account_sid, auth_token)
    message = client.messages \
        .create(
        body=str(msg),
        from_='+16172998275',
        to=str(number)
    )

#Code to add number.
@app.route("/add")
def addNumber():  # Code executed upon receiving text
    num = request.args.get('num')
    if num is None:
        return '''<h1>Error.</h1>'''.format(num)
    if "+" not in str(num):
        num = "+" + str(num)
    inProgress[str(num[1:])] = {'Q0': '', 'Q1': -1, 'Q2': -1, 'Q3': -1, 'Q4': -1, 'Q5': -1, 'Q6': -1, 'Q7': -1,'Q8': -1, 'Q9': -1, 'Q10': -1, 'Q11': -1, 'Q12': -1, 'Q13': -1, 'Q14': -1, 'Q15': -1, 'Q16': -1, 'Q17': -1, 'Q18': -1, 'Q19': -1, 'Q20': -1, 'Q21': -1, 'Q22': -1, 'Q23': -1,'Q24': -1}
    sendText(num, "You have been accepted into AboveBoard! Please answer all 21 questions by responding with numbers from 0-24 or 0-100 or characters when specified.")
    sendText(num, "Respond STOP at any time to opt out. Copyright Pro Fee LLC 2019")
    sendText(num, questionList["Q0"]["question"])
    return '''<p>Success</p>'''.format(num)

def loadFiles(): #Loads Twilio account info off twilio.json, blocked users off blocked.json, questions off questions.json
    global twilioAuth
    global twilioAccountID
    global blockedList
    global questionList
    global gmail_password
    with open("twilio.json", "r") as read_file:
        data = json.load(read_file)
    twilioAuth = str(data["twilioAuth"])
    twilioAccountID = str(data["twilioID"])
    gmail_password = str(data["gmailPass"])
    with open("blocked.json", "r") as read_file:
        blockedList = json.load(read_file)
    if demoMode:
        with open("demo.json", "r") as read_file:
            questionList = json.load(read_file)
    else:
        with open("questions.json", "r") as read_file:
            questionList = json.load(read_file)

if __name__ == "__main__": #starts the whole program
    print("started")
    loadFiles()
    app.run(host='0.0.0.0', port=5001)