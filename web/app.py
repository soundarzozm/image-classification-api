from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import requests
import subprocess
import json

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.ImageRecognition
users = db["Users"]

def UserExists(username):
    if users.find({"username": username}).count() == 0:
        return False
    return True

def VerifyPassword(username, password):
    if not UserExists(username):
        return CreateJson(301, "username not found"), True

    hashed_pw = users.find({
        "username": username
    })[0]["password"]

    if bcrypt.checkpw(password.encode("utf8"), hashed_pw) != True:
        return CreateJson(302, "wrong password"), True
    else:
        return {}, False    

def CountTokens(username):
    num_tokens = users.find({
        "username": username
    })[0]["tokens"]

    return num_tokens

def CreateJson(status, msg):
    retJson = {
        "status": status,
        "msg": msg
    }
    return jsonify(retJson)

class Register(Resource):
    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExists(username):
            return CreateJson(301, "username already exists")

        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        users.insert({
            "username": username,
            "password": hashed_pw,
            "tokens": 10
        })

        return CreateJson(200, "success")

class Classify(Resource):
    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        url = postedData["url"]

        retJson, error = VerifyPassword(username, password)

        if error:
            return retJson

        num_tokens = users.find({
            "username": username
        })[0]["tokens"]

        if num_tokens <= 0:
            return CreateJson(303, "not enough tokens")

        r = requests.get(url)

        with open("temp.jpg", "wb") as f:
            f.write(r.content)
            proc = subprocess.Popen("python3 classify_image.py --model_dir=. --image_file=./temp.jpg", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            proc.communicate()[0]
            proc.wait()
            with open("text.txt") as g:
                retJson = json.load(g)

        users.update({
            "username": username
        }, {
            "$set": {
                "tokens": num_tokens - 1
            }
        })

        return retJson

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        adminPw = postedData["adminPw"]
        refillAmt = postedData["refill"]

        if UserExists(username) == False:
            return CreateJson(301, "username not found")

        correct_pw = "abc123"

        if adminPw != correct_pw:  
            return CreateJson(304, "invalid admin password")

        num_tokens = CountTokens(username)

        users.update({
            "username": username
        },{
            "$set":{
                "tokens": num_tokens + refillAmt
            }
        })

        return CreateJson(200, "success")

api.add_resource(Register, "/register")
api.add_resource(Classify, "/classify")
api.add_resource(Refill, "/refill")

if __name__ == "__main__":
    app.run(host="0.0.0.0")