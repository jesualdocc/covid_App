#Adds higher lever package to path directory
import sys, os
dirname = os.path.dirname(__file__)
app_package_dir = os.path.join(dirname, '..')
sys.path.append(dirname)
sys.path.append(app_package_dir)

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask import Blueprint
from flask.helpers import make_response
from flask import request, jsonify
import jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from helper_functions import convert_user_tuple_to_dict
from config import Config
from db.sql_connector import SQLConnector
from jwt_auth import token_required

users = Blueprint('users', __name__)
sql = SQLConnector()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@users.route('/login', methods=['POST'])
@limiter.limit("3 per minute")
def login():
    global sql 
   
    if 'userName' in request.json and 'password' in request.json:
        
        user = sql.find_users(request.json['userName'])
       
        if user is None:
            return jsonify({'message': 'Username or Password is incorrect'}), 401

        if check_password_hash(user[5], request.json['password']):
         
            user_dict = convert_user_tuple_to_dict(user)
            # generates the JWT Token with an expiration time
            token_expiration = datetime.utcnow() + timedelta(minutes = 60)
            token = jwt.encode({'id': user[0], 'exp' : token_expiration
        }, Config.SECRET_KEY) 

            return make_response(jsonify({'token' : token.decode('UTF-8'), 'user':user_dict}), 201)
       
        else:
            return jsonify({'message': 'Username or Password is incorrect'}), 401

    return make_response(jsonify({'message':'Invalid paramentes'}), 400)

############################################################################
#Registers a new user
@users.route('/registration', methods=['POST'])
@limiter.limit("2 per minute")
def registration():
    global sql

    result = request.json
    try:
        password = result['password']
        result['password'] = generate_password_hash(password)
        
        sql.add_user(result)
        
        return jsonify({'message': 'Succesfull'}), 201
    except:
        return jsonify({'request':result}), 400

############################################################################
#Update user info
@users.route('/profileinfo', methods=['PUT'])
@token_required 
def profile_info():
    global sql

    result = request.json
    
    if 'changeType' in request.headers:
        if request.headers['changeType'] == 'profile':
        
            try:
                sql.update_user(result)

                return make_response(jsonify({'message': 'Succesfull'}), 201)
            except:
                
                return make_response(jsonify({'request':result}), 400)

        #Change password only
        if request.headers['changeType'] == 'password':
            password = result['password']
           
            result['password'] = generate_password_hash(password)

            try:
                
                sql.update_user(result)

                return make_response(jsonify({'message': 'Succesfull'}), 201)
            except:
                
                return make_response(jsonify({'request':result}), 400)
            
    return make_response(jsonify({'request':result}), 400)