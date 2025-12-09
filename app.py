import os
import pickle 
from flask import Flask, render_template,request,redirect,session
import numpy as np
import pandas as pd 
from sklearn.preprocessing import StandardScaler
from src.pipeline.predict_pipeline import CustomData, PredictPipeline
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt



application = Flask(__name__)
app = application
app.secret_key = 'your_secret_key'  
# Replace with a secure key in production
bcrypt = Bcrypt(app)

# Absolute path to ensure database.db is created inside E:\mlproject
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


#----------Database Model for User----------------

class User(db.Model):
    # This is a table structure of DB
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150),nullable=False)
    email = db.Column(db.String(150),nullable=False, unique=True)
    password = db.Column(db.String(150))

    def __init__(self,name,email,password):
        self.name = name
        self.email = email
        #Hash the password before storing it
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
    
with app.app_context():
    db.create_all()


# ----------Routes for Web App----------------
# Home Route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict',methods=['GET','POST'])
def predict_datapoint():
    if 'email' not in session:
        return redirect('/login')
    
    if request.method == 'GET':
        return render_template('home.html')
    else:
        data = CustomData(
        gender=request.form.get('gender'),
        race_ethnicity=request.form.get('race_ethnicity'),
        parental_level_of_education=request.form.get('parental_level_of_education'),
        lunch=request.form.get('lunch'),
        test_preparation_course=request.form.get('test_preparation_course'),
        reading_score=int(request.form.get('reading_score')),
        writing_score=int(request.form.get('writing_score'))
        )
        pred_df = data.get_data_as_dataframe()
        print(pred_df)

        predict_pipeline = PredictPipeline()
        results = predict_pipeline.predict(pred_df)

        return render_template('home.html', results=results[0])
    


#---------User Registration and Login Routes----------------
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', message="User already exists)")
        
        #hash password and create new user
        # hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        # create new User
        new_user = User(name=name,email=email,password=password)

        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    
    return render_template('register.html')

#Login Route

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # session['name'] = user.name
            session['email'] = user.email
            session['name'] = user.name
            return redirect('/predict')
        else:
            return render_template('login.html', message="Invalid email or password")
    return render_template('login.html')

# Dashboard Route    
@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('dashboard.html',user = user)
    
    return redirect('/login')

#Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

    


if __name__ == '__main__':
    # app.run(host="0.0.0.0") # debug=True
    app.run(debug=True)




