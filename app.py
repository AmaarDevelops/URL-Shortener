from flask import Flask,request,redirect,render_template,url_for,flash,session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
import random,string
from datetime import datetime
import os


app = Flask(__name__)

app.secret_key = 'super_secret'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,'urls.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    username = db.Column(db.String(100),unique=True,nullable=False)
    password = db.Column(db.String(200),nullable=False)
    urls = db.relationship('URL',backref='user',lazy=True)

#URL MODEL
class URL(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    original_url = db.Column(db.String(500),nullable=False)
    short_id = db.Column(db.String(10),unique=True,nullable=False)
    clicks = db.Column(db.Integer,default=0)
    timestamp = db.Column(db.DateTime,default=datetime.utcnow)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=True)



@app.route("/",methods = ['POST','GET'])
def home():
    if request.method == 'POST':
        original_url = request.form.get('original_url')
        custom_id = request.form.get('custom_id')
        if custom_id:
            if URL.query.filter_by(short_id=custom_id).first():
                flash('Custom short id already taken','danger')
                return redirect(url_for('home'))
            short_id = custom_id
        else: 
            short_id = ''.join(random.choices(string.ascii_letters + string.digits,k=6))   
        

        user_id = session.get('user_id') 
        new_url = URL(original_url=original_url,short_id=short_id,user_id=user_id)
        db.session.add(new_url)
        db.session.commit()

        short_url = request.host_url + short_id
        
        return render_template("result.html",short_url=short_url,clicks=new_url.clicks)
    
    return render_template('home.html')



#Register
@app.route("/register",methods=['GET','POST'])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Username Already Taken','danger')
            return redirect(url_for('register'))
        
        user = User(username = username,password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully','success')
        return redirect(url_for('login'))
    return render_template('register.html')


#login
@app.route('/login',methods=["POST",'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()

        if user and check_password_hash(user.password,password):
            session['user_id'] = user.id
            flash('Logged In Successfully','success')
            return redirect(url_for('home'))
        else:
            flash('Invalid Credentials','danger')
    return render_template('login.html')     

#Logout

@app.route('/logout')
def logout():
    session.pop("user_id",None)
    flash("Logged Out","info")
    return redirect(url_for('home'))   


@app.route('/<short_id>')
def redirect_url(short_id):
    url = URL.query.filter_by(short_id=short_id).first()
    if url:
        url.clicks+=1
        db.session.commit()
        return redirect(url.original_url)
    return 'URL NOT FOUND',404
    
@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please Log In to view your dashboard',"warning")
        return redirect(url_for('login'))
    urls = URL.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html',urls=urls)
    
@app.route('/delete/<int:url_id>',methods=['POST'])
def delete_url(url_id):
    user_id = URL.query.filter_by('user_id')
    url = URL.query.get_or_404(url_id)

    if url.user_id != user_id:
        flash('You dont Have permission to delete this URL','danger')
        return redirect(url_for('dashboard'))
    db.session.delete(url)
    db.session.commit()
    flash("URL deleted successfully",'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=False)
