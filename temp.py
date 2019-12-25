import smtplib
import ssl
import requests
from twilio import twiml
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import random as rand
import threading
import json
import time
from flask import Flask, request, make_response, url_for, redirect, render_template
from base64 import b64encode, b64decode

app = Flask(__name__)

email = ""

twilioAccountID = ""
twilioAuth = ""

editPW = "89u234knlaju1jwj"

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "instantalk.alerts@gmail.com"  # Enter your address
receiver_email = "dbatulis@icloud.com"  # Enter receiver address
gmail_password = ""

'''
- Reorder questions
- Display past users
'''

#"q1":{"question": "Is a hamburger a hotdog?", "type": "MC", "ans":{"A":"1","B":"2","C":"3","D":"4"}
#"q2":{"question": "Is a hamburger a hotdog?", "type": "SA"}

questionsList = {}

inProgress = {}

class myThread(threading.Thread):  # Thread created upon request
    def __init__(self, name, sendnum, msgbody):
        threading.Thread.__init__(self)
        self.name = name
        self.sendnum = sendnum
        self.msgbody = msgbody
    def run(self):
        print("Fetching request to " + self.sendnum)
        if self.msgbody == "forceEnroll_postAuthKey_15692":
            sendText(self.sendnum, "You have been enrolled in XYZ")
        verifyProcess(self.msgbody, self.sendnum)
        print("Finished request to " + self.sendnum)

def verifyProcess(msg, num):
    global inProgress
    if num[1:] in inProgress.keys():
        nextKey = False
        for key in inProgress[num[1:]].keys():
            if nextKey:
                sendText(num, createQuestion(key))
                break
            if inProgress[num[1:]][key] == "noAns":
                if key == "q1" or key == "q8":
                    if key == "q1" and msg.lower() == "d":
                        sendText(num, "Call 911 immediately. This survey is now over")
                        del inProgress[num[1:]]
                        return
                    if key == "q8" and msg.lower() == "b":
                        sendText(num, "If patient is unsafe or unstable or not improving 911 should be called")
                if verifyAns(key, msg, num):
                    inProgress[num[1:]][key] = msg
                    nextKey = True
                    continue
                else:
                    sendText(num, createQuestion(key))
                    break
        else:
            sendText(num, "Please donate $10000 $1000, $100, $10, or $1 to support our healing mission: (website pending)")
            msgStr = """"""
            msgStr += "Subject: " + str(num) + "\n\n"
            msgStr += "This email was generated from - " + str(num) + "\n"
            for question in inProgress[str(num[1:])].keys():
                if questionsList[question]["question"] == "END":
                    del inProgress[str(num[1:])]
                    break
                else:
                    msgStr += questionsList[question]["question"] + ": answer = " + inProgress[str(num[1:])][question]
            print(msgStr)
            #Open email server
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender_email, gmail_password)
                server.sendmail(sender_email, receiver_email, msgStr)
    else:
        inProgress[num[1:]] = {}
        for key in questionsList.keys():
            inProgress[num[1:]][key] = "noAns"
        sendText(num, "Welcome! Please respond with STOP or QUIT to opt out of sms messages.")
        sendText(num, createQuestion("q1"))

@app.route("/")
def welcomeLanding():
    resp = make_response(redirect(url_for('login')))
    return resp

@app.route("/editQuestions")
def makeEditQuestions():
    global questionsList
    ID = request.cookies.get('userID')
    if b64decode(ID).decode("utf-8") != editPW:
        resp = make_response(redirect(url_for('login')))
        return resp
    htmlStr = ""
    for i in questionsList.keys():
        htmlStr += '<a style="display: block" href="/editQuestions/singleQuestion/?questID=' + str(i) + '">' + str(i) + '</a> <br/>'
    return make_response(render_template('editQuestionDisplay.html', questionLinks=htmlStr))

@app.route("/editQuestions/singleQuestion/",methods=['get', 'post'])
def singleQuestion():
    global questionsList
    questID = request.args.get("questID")
    ID = request.cookies.get('userID')
    if b64decode(ID).decode("utf-8") != editPW:
        resp = make_response(redirect(url_for('login')))
        return resp
    if request.method == 'POST':
        if request.args.get("refer") == "new":
            questionsList[request.form.get("questID")] = {"question":"","type":request.form.get("type"),"ans":{}}
        try:
            if request.form.get("remove") == 'on':
                delete = True
            else:
                delete = False
        except Exception:
            delete = False
        questID = request.form.get("questID")
        if delete:
            del questionsList[questID]
            if not fixListDict():
                resp = make_response(redirect(url_for('makeEditQuestions')))
                return resp
            with open("questions.json", "w") as write_file:
                json.dump(questionsList, write_file)
            resp = make_response(redirect(url_for('makeEditQuestions')))
            return resp
        if request.form.get("type") == "MC":
            questionsList[questID]["question"] = request.form.get("question")
            questionsList[questID]["ans"]["A"] = request.form.get("AnsA")
            questionsList[questID]["ans"]["B"] = request.form.get("AnsB")
            questionsList[questID]["ans"]["C"] = request.form.get("AnsC")
            questionsList[questID]["ans"]["D"] = request.form.get("AnsD")
            with open("questions.json", "w") as write_file:
                json.dump(questionsList, write_file)
            resp = make_response(redirect(url_for('makeEditQuestions')))
            return resp
        elif request.form.get("type") == "SA":
            questionsList[questID]["question"] = request.form.get("question")
            with open("questions.json", "w") as write_file:
                json.dump(questionsList, write_file)
            resp = make_response(redirect(url_for('makeEditQuestions')))
            return resp
    if request.args.get("refer") == "new":
        questID = "q" + str(len(questionsList)+1)
        if request.args.get("qType") == "MC":
            return make_response(
                render_template('editMCQuestion.html', questID=questID, typeID="MC",
                                question="",
                                AnsA="", AnsB="",
                                AnsC="", AnsD=""))
        elif request.args.get("qType") == "SA":
            return make_response(
                render_template('editSAQuestion.html', questID=questID, typeID="SA",
                                question=""))
    if questionsList[questID]["type"] == "MC":
        return make_response(render_template('editMCQuestion.html', questID=questID, typeID=questionsList[questID]["type"], question=questionsList[questID]["question"],
                                             AnsA=questionsList[questID]["ans"]["A"],AnsB=questionsList[questID]["ans"]["B"],AnsC=questionsList[questID]["ans"]["C"],AnsD=questionsList[questID]["ans"]["D"]))
    elif questionsList[questID]["type"] == "SA":
        return make_response(render_template('editSAQuestion.html', questID=questID, typeID=questionsList[questID]["type"], question=questionsList[questID]["question"]))

@app.route("/freeSend", methods=['get', 'post'])
def freeSend():
    ID = request.cookies.get('userID')
    if b64decode(ID).decode("utf-8") != editPW:
        resp = make_response(redirect(url_for('login')))
        return resp
    if request.method == 'POST':
        num = request.form.get("number")
        msg = request.form.get("msg")
        print(num)
        print(msg)
        if "+" not in num or len(num) != 12 or len(num) == 0 or len(msg) > 150 or len(msg) == 0:
            return make_response(render_template('freesend.html'))
        sendText(num, msg)
        return make_response(render_template('freesend.html'))
    else:
        return make_response(render_template('freesend.html'))

@app.route("/forceAdd", methods=['get', 'post'])
def forceAdd():
    ID = request.cookies.get('userID')
    if b64decode(ID).decode("utf-8") != editPW:
        resp = make_response(redirect(url_for('login')))
        return resp
    if request.method == 'POST':
        phoneNum = request.form.get("number")
        t = myThread(phoneNum, phoneNum, "forceEnroll_postAuthKey_15692")
        t.start()
        return make_response(render_template('forceadd.html'))
    else:
        return make_response(render_template('forceadd.html'))

@app.route("/viewProgress", methods=['get', 'post'])
def showUsers():
    ID = request.cookies.get('userID')
    phoneNum = request.args.get("phoneNum")
    if b64decode(ID).decode("utf-8") != editPW:
        resp = make_response(redirect(url_for('login')))
        return resp
    if request.method == 'POST':
        num = request.form.get("number")
        msg = request.form.get("msg")
        inProgress[num[1:]]["Response"] = msg
        print(num)
        print(msg)
        if "+" not in num or len(num) != 12 or len(num) == 0 or len(msg) > 150 or len(msg) == 0:
            return make_response(render_template('viewusers.html'))
        sendText(num, msg)
        with open("finished.json", "r") as read_file:
            data = json.load(read_file)
        data[num[1:]] = inProgress[num[1:]]
        with open("finished.json", "w") as write_file:
            json.dump(data, write_file)
        del inProgress[num[1:]]
        resp = make_response(redirect(url_for('questionMain')))
        return resp
    if phoneNum is None or phoneNum not in inProgress.keys():
        htmlStr = ""
        for i in inProgress.keys():
            htmlStr += '<a style="display: block" href="/viewProgress?phoneNum=' + str(i) + '">' + str(i) + '</a> <br/>'
        return render_template("viewusers.html", userList=htmlStr)
    elif phoneNum in inProgress.keys():
        blankStr = ""
        finished = 1
        for key in inProgress[phoneNum].keys():
            if inProgress[phoneNum][key] == "noAns":
                finished = 0
            blankStr += str(key) + ") " + str(questionsList[key]["question"]) + " - " + str(inProgress[phoneNum][key]) + "<br/>"
        return render_template("viewoneuser.html", userList=blankStr, showForm=finished, phoneNum=str("+"+phoneNum))

@app.route("/viewQuestions")
def viewAllQuestions():
    ID = request.cookies.get('userID')
    if b64decode(ID).decode("utf-8") != editPW:
        resp = make_response(redirect(url_for('login')))
        return resp
    ansStr = "\n"
    for question in questionsList.keys():
        print(question)
        ansStr += question + ") " + questionsList[question]["question"] + ", type = " + questionsList[question]["type"] + "<br/>"
    print(ansStr)
    return render_template("viewall.html", questionsList=ansStr)

@app.route("/login", methods=['get', 'post'])
def login():
    ID = request.cookies.get('userID')
    newID = request.form.get("userID")
    if ID != None and b64decode(ID).decode("utf-8") == editPW :
        resp = make_response(redirect(url_for('questionMain')))
        return resp
    elif newID == editPW:
        resp = make_response(redirect(url_for('questionMain')))
        resp.set_cookie('userID', b64encode(newID.encode("utf-8")))
        return resp
    else:
        return make_response(render_template('login.html'))

@app.route("/questions")
def questionMain():
    ID = request.cookies.get('userID')
    if b64decode(ID).decode("utf-8") != editPW:
        resp = make_response(redirect(url_for('login')))
        return resp
    else:
        return make_response(render_template('questions.html'))

@app.route("/viewUserInfo")
def userInfo():
    ID = request.cookies.get('userID')
    if b64decode(ID).decode("utf-8") != editPW:
        resp = make_response(redirect(url_for('login')))
        return resp
    elif b64decode(ID).decode("utf-8") == editPW:
        return make_response(render_template('userinfo.html', currentPW = ID))

@app.route("/changePW", methods=['get', 'post'])
def password():
    newPW = request.form.get("newPW")
    oldPW = request.form.get("oldPW")
    ID = request.cookies.get('userID')
    if b64decode(ID).decode("utf-8") != editPW:
        resp = make_response(redirect(url_for('login')))
        return resp
    if newPW is not None and oldPW is not None:
        if oldPW == editPW:
            if newPW is not "":
                with open("twilio.json", "r") as read_file:
                    data = json.load(read_file)
                if oldPW == editPW:
                    data['editPW'] = str(newPW)
                with open("twilio.json", "w") as write_file:
                    json.dump(data, write_file)
                loadFiles()
                resp = make_response(redirect(url_for('userInfo')))
                resp.set_cookie('userID', newPW)
                return resp
            else:
                return make_response(render_template('changepw.html', errorMsg="New password must not be blank"))
        else:
            return make_response(render_template('changepw.html', errorMsg="Old password field does not match any current passwords"))
    else:
        return make_response(render_template('changepw.html', errorMsg=" "))

@app.route("/logout")
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('userID', "")
    return resp

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

def createQuestion(key):
    question = questionsList[key]
    if question["type"] == "MC":
        questionTxt = question["question"] + "\n"
        if question["ans"]["A"] != "-" and question["ans"]["A"] != "":
            questionTxt += "A) " + question["ans"]["A"] + "\n"
        if question["ans"]["B"] != "-" and question["ans"]["B"] != "":
            questionTxt += "B) " + question["ans"]["B"] + "\n"
        if question["ans"]["C"] != "-" and question["ans"]["C"] != "":
            questionTxt += "C) " + question["ans"]["C"] + "\n"
        if question["ans"]["D"] != "-" and question["ans"]["D"] != "":
            questionTxt += "D) " + question["ans"]["D"] + "\n"
        return questionTxt
    elif question["type"] == "SA":
        questionTxt = question["question"]
        return questionTxt

def verifyAns(key,msg,num):
    if questionsList[key]["type"] == "SA":
        if len(msg) < 150:
            return True
        else:
            return False
    elif questionsList[key]["type"] == "MC":
        msg = str(msg).lower()
        if msg != "a" and msg != "b" and msg != "c" and msg != "d":
            return False
        else:
            if msg == "a" and questionsList[key]["ans"]["A"] != "-" and questionsList[key]["ans"]["A"] != "":
                return True
            elif msg == "b" and questionsList[key]["ans"]["B"] != "-" and questionsList[key]["ans"]["B"] != "":
                return True
            elif msg == "c" and questionsList[key]["ans"]["C"] != "-" and questionsList[key]["ans"]["C"] != "":
                return True
            elif msg == "d" and questionsList[key]["ans"]["D"] != "-" and questionsList[key]["ans"]["D"] != "":
                return True
            else:
                return False
    else:
        return False

def fixListDict():
    global questionsList
    dictKeys = list(questionsList.keys())
    newQuestionDict = {}
    counter = 1
    for i in dictKeys:
        newQuestionDict["q"+str(counter)] = questionsList[i]
        counter += 1
    questionsList = newQuestionDict
    userList = list(inProgress.keys())
    for user in userList:
        indepUser = list(inProgress[user].keys())
        newUserDict = {}
        counter = 1
        for i in indepUser:
            if i not in dictKeys:
                del inProgress[user][i]
        indepUser = list(inProgress[user].keys())
        print(indepUser)
        for i in indepUser:
            newUserDict["q" + str(counter)] = inProgress[user][i]
            counter += 1
        inProgress[user] = newUserDict
    else:
        return True

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
    global editPW
    global questionsList
    with open("twilio.json", "r") as read_file:
        data = json.load(read_file)
    twilioAuth = str(data["twilioAuth"])
    twilioAccountID = str(data["twilioID"])
    editPW = str(data["editPW"])
    gmail_password = str(data["gmailPass"])
    with open("questions.json", "r") as read_file:
        data = json.load(read_file)
    questionsList = data
    print(questionsList)

if __name__ == "__main__": #starts the whole program
    print("started")
    loadFiles()
    app.run(host='0.0.0.0', port=80)