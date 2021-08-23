from flask import Flask,redirect,request as req,url_for,redirect,jsonify,session
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user
import sqlite3
from datetime import datetime

app = Flask(__name__)
login_manager=LoginManager()
login_manager.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///spt_signals.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.secret_key="b'bV/\x1d\xc1\xf9\x96i\x15\xaa\xe9\x85A\xb0+Y\x11&\x111cz?+'"

database=SQLAlchemy(app)
ma=Marshmallow(app)


class Users(UserMixin, database.Model):
    __tablename__='perfect_trade_users'
    id=database.Column('id',database.Integer,primary_key=True)
    Fullname=database.Column(database.String(100))
    Email=database.Column(database.String(100))
    Password=database.Column(database.String(100))
    Customer_ID=database.Column(database.String(100))
    Date_Registered=database.Column(database.DateTime,nullable=False,default=datetime.now())

    def __init__(self,new_user):
        self.Fullname=new_user['fullname']
        self.Customer_ID=new_user['cus_id']
        self.Email=new_user['email']
        self.Password=new_user['password']

class userSchema(ma.Schema):
    class Meta:
            fields = ('id', 'Fullname','Email','Password','Date_Registered','Customer_ID')
            
class Subscriptions(database.Model):
    __tablename__="subscription"
    Id=database.Column(database.Integer,primary_key=True)
    Plan=database.Column(database.String)
    User=database.Column(database.String)
    Amount=database.Column(database.Integer)
    Duration=database.Column(database.Float)
    Status=database.Column(database.String,default='Ongoing')
    Paid=database.Column(database.String,default='False')
    End_date=database.Column(database.Date)
    Start_date=database.Column(database.Date,nullable=False,default=datetime.utcnow)
    
    def __init__(self,sub):
        
        self.Plan=sub["plan"]
        self.User=sub["user"]
        self.Amount=sub["amount"]
        self.Duration=sub["duration"]
        self.End_date=sub["end_date"]
        self.Status=sub['status']
        self.Paid=sub['paid']
   
    
    
class subSchema(ma.Schema):
    class Meta:
        fields=('Plan','User','Amount','Duration','Start_date','End_date')
            
user=userSchema()
all_users=userSchema(many=True)

single_sub=subSchema()
all_sub=subSchema(many=True)

link="http://localhost:5500/"
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

@login_manager.unauthorized_handler
def Unauthorized():
    return jsonify({
        "status":"unauthorized",
         "redirect":link
    })

def getLoggedUser(user_id):
       logged_user_details=user.dump(Users.query.filter_by(id=user_id).first())
       return logged_user_details
       

@app.route('/login',methods=['POST'])
def Login():
   if req.method=="POST":
       response={
           "status":""
       }
       cred=dict(req.json)
       
       print(cred)
       email=cred["email"]
       password=cred["password"]
       current_user=Users.query.filter_by(Email=email).first()
       if current_user:
           user_cred=dict(user.dump(current_user))
           if user_cred["Password"] != password:
               response["status"]="error"
               response["message"]='Invalid Password'
           else:
               login_user(current_user)
               response['status']='logged_in'
               response['logged_user']=user_cred['Email']
               response['Customer_ID']=user_cred['Customer_ID']
       else:
           response["status"]="error"
           response["message"]="User Does Not Exist"
           
       return jsonify(response) 
   
@app.route('/signup',methods=['POST'])
def Signup():
     response={
         'status':''
     }
     if req.method=='POST':
        user_details=dict(req.json)
        user_exist=Users.query.filter_by(Email=user_details['email']).first()
        user_fullname=Users.query.filter_by(Email=user_details['fullname']).first()
        if user_exist:
            response['status']='failed'
            response['message']='user with that email already exist'
        elif user_fullname:
             response['status']='failed'
             response['message']='User Already Exist'
        else:
            new_user=Users(user_details)
            database.session.add(new_user)
            database.session.commit()
            response['status']="Success"
    

     return response

@app.route('/renew',methods=['POST'])
@login_required
def Renew():
    pass


@app.route('/subscription',methods=['POST'])
@login_required
def getSub():
    response={}
    customer_id=getLoggedUser(session['_user_id'])['Email']
    sub=single_sub.dump(Subscriptions.query.filter_by(User=customer_id).first())
    if sub:
        response['status']='Success'
        response['Sub']=sub
    else:
        response['status']='error'
        response['message']='Sorry Could not Get Subscription Information'
    return jsonify(response)

@app.route('/dashboard',methods=['POST'])
@login_required
def dashboard():
   if req.method == 'POST':
    response={}
    user_id=session['_user_id']
    logged_user=getLoggedUser(user_id)
    response['status']='logged_in'
    response['logged_user']=logged_user['Email']
    response['Customer_ID']=logged_user['Customer_ID']
    return jsonify(response)

@app.route('/logout',methods=['POST'])
@login_required
def Logout():
   if req.method=='POST':
     logout_user()
     print(session)
     response={
        'status':'logged_out',
        'redirect':'link'
    }
  
     return jsonify(response)


@app.route('/pay',methods=['POST'])
def makePayment():
    pass

@app.route('/subscribe',methods=['POST'])
def Subscribe():
    if req.method=='POST':
      response={}
      new_sub=dict(req.json)
      new_sub['end_date']=datetime(2022, 1, 17)
      sub_exist=Subscriptions.query.filter_by(User=new_sub['user']).first()
      if sub_exist:  
        sub_exist.Plan=new_sub["plan"]
        sub_exist.User=new_sub["user"]
        sub_exist.Amount=new_sub["amount"]
        sub_exist.Duration+=new_sub["duration"]
        sub_exist.End_date=new_sub["end_date"]
        sub_exist.Status=new_sub['status']
        sub_exist.Paid=new_sub['paid']
      else:
          user_sub=Subscriptions(new_sub)
          database.session.add(user_sub)
      response['status']='Successfull'
      database.session.commit() 
    return jsonify(response)
    

if __name__ == "__main__":
    database.create_all()
    app.run(debug=True)