from flask import Flask, render_template, url_for, request, session, flash, redirect
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import pymysql
import pandas as pd
import numpy as np
import os
import cv2
import random
from PIL import Image
import shutil
import datetime
import time
import requests
facedata = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
cascade = cv2.CascadeClassifier(facedata)

mydb=pymysql.connect(host='localhost', user='root', password='', port=3306, database='smart_voting_system')
sender_address ="nagamchenchulakshmi@gmail.com" 
sender_pass = 'fcgedzzfncmuvole' 


app=Flask(__name__)
app.config['SECRET_KEY']='ajsihh98rw3fyes8o3e9ey3w5dc'

@app.before_first_request
def initialize():
    session['IsAdmin']=False
    session['User']=None

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/admin', methods=['POST','GET'])
def admin():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        if (email=='admin@voting.com') and (password=='admin'):
            session['IsAdmin']=True
            session['User']='admin'
            flash('Admin login successful','success')
    return render_template('admin.html', admin=session['IsAdmin'])

@app.route('/add_nominee', methods=['POST','GET'])
def add_nominee():
    if request.method=='POST':
        member=request.form['member_name']
        party=request.form['party_name']
        logo=request.form['test']
        nominee=pd.read_sql_query('SELECT * FROM nominee', mydb)
        all_members=nominee.member_name.values
        all_parties=nominee.party_name.values
        all_symbols=nominee.symbol_name.values
        if member in all_members:
            flash(r'The member already exists', 'info')
        elif party in all_parties:
            flash(r"The party already exists", 'info')
        elif logo in all_symbols:
            flash(r"The logo is already taken", 'info')
        else:
            sql="INSERT INTO nominee (member_name, party_name, symbol_name) VALUES (%s, %s, %s)"
            cur=mydb.cursor()
            cur.execute(sql, (member, party, logo))
            mydb.commit()
            cur.close() 
            flash(r"Successfully registered a new nominee", 'primary')
    return render_template('nominee.html', admin=session['IsAdmin'])

@app.route('/registration', methods=['POST','GET'])
def registration():
    if request.method=='POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        aadhar_id = request.form['aadhar_id']
        voter_id = request.form['voter_id']
        pno = request.form['pno']
        age = int(request.form['age'])
        email = request.form['email']
        voters=pd.read_sql_query('SELECT * FROM voters', mydb)
        all_aadhar_ids=voters.aadhar_id.values
        all_voter_ids=voters.voter_id.values
        if age >= 18:
            if (aadhar_id in all_aadhar_ids) or (voter_id in all_voter_ids):
                flash(r'Already Registered as a Voter')
            else:
                sql = 'INSERT INTO voters (first_name, middle_name, last_name, aadhar_id, voter_id, email,pno, verified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
                cur=mydb.cursor()
                cur.execute(sql, (first_name, middle_name, last_name, aadhar_id, voter_id, email, pno, 'no'))
                mydb.commit()
                cur.close()
                session['aadhar']=aadhar_id
                session['status']='no'
                session['email']=email
                return redirect(url_for('verify'))
        else:
            flash("if age less than 18 than not eligible for voting","info")
    return render_template('voter_reg.html')

@app.route('/verify', methods=['POST','GET'])
def verify():
    if session['status']=='no':
        if request.method=='POST':
            otp_check=request.form['otp_check']
            if otp_check==session['otp']:
                session['status']='yes'
                sql="UPDATE voters SET verified='%s' WHERE aadhar_id='%s'"%(session['status'], session['aadhar'])
                cur=mydb.cursor()
                cur.execute(sql)
                mydb.commit()
                cur.close()
                flash(r"Email verified successfully",'primary')
                return redirect(url_for('capture_images')) 
            else:
                flash(r"Wrong OTP. Please try again.","info")
                return redirect(url_for('verify'))
        else:
            message = MIMEMultipart()
            receiver_address = session['email']
            message['From'] = sender_address
            message['To'] = receiver_address
            Otp = str(np.random.randint(100000, 999999))
            print(Otp)
            session['otp']=Otp
            message.attach(MIMEText(session['otp'], 'plain'))
            abc = smtplib.SMTP('smtp.gmail.com', 587)
            abc.starttls()
            abc.login(sender_address, sender_pass)
            text = message.as_string()
            abc.sendmail(sender_address, receiver_address, text)
            abc.quit()
            print(session['otp'])
    else:
        flash(r"Your email is already verified", 'warning')
    return render_template('verify.html')

@app.route('/capture_images', methods=['POST','GET'])
def capture_images():
    if request.method=='POST':
        cam=cv2.VideoCapture(0, cv2.CAP_DSHOW)
        sampleNum = 0
        path_to_store=os.path.join(os.getcwd(),"all_images\\"+session['aadhar'])
        try:
            shutil.rmtree(path_to_store)
        except:
            pass
        os.makedirs(path_to_store, exist_ok=True)
        while (True):
            ret, img = cam.read()
            try:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            except:
                continue
            faces = cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                sampleNum = sampleNum + 1
                cv2.imwrite(path_to_store +r'\\'+ str(sampleNum) + ".jpg", gray[y:y + h, x:x + w])
            else:
                cv2.imshow('frame', img)
                cv2.setWindowProperty('frame', cv2.WND_PROP_TOPMOST, 1)
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
            elif sampleNum >= 200:
                break
        cam.release()
        cv2.destroyAllWindows()
        flash("Registration successfully completed","success")
        return redirect(url_for('home'))
    return render_template('capture.html')

from sklearn.preprocessing import LabelEncoder
import pickle
le = LabelEncoder()

def getImagesAndLabels(path):
    folderPaths = [os.path.join(path, f) for f in os.listdir(path)]
    faces = []
    Ids = []
    global le
    for folder in folderPaths:
        imagePaths = [os.path.join(folder, f) for f in os.listdir(folder)]
        aadhar_id = folder.split("\\")[1]
        for imagePath in imagePaths:
            pilImage = Image.open(imagePath).convert('L')
            imageNp = np.array(pilImage, 'uint8')
            faces.append(imageNp)
            Ids.append(aadhar_id)
    Ids_new=le.fit_transform(Ids).tolist()
    output = open('encoder.pkl', 'wb')
    pickle.dump(le, output)
    output.close()
    return faces, Ids_new

@app.route('/train', methods=['POST','GET'])
def train():
    if request.method=='POST':
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        faces, Id = getImagesAndLabels(r"all_images")
        print(Id)
        print(len(Id))
        recognizer.train(faces, np.array(Id))
        recognizer.save("Trained.yml")
        flash(r"Model Trained Successfully", 'Primary')
        return redirect(url_for('home'))
    return render_template('train.html')
@app.route('/update')
def update():
    return render_template('update.html')
@app.route('/updateback', methods=['POST','GET'])
def updateback():
    if request.method=='POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        voter_id = request.form['voter_id']
        email = request.form['email']
        pno = request.form['pno']
        age = int(request.form['age'])
        voters=pd.read_sql_query('SELECT * FROM voters', mydb)
        all_aadhar_ids=voters.aadhar_id.values
        if age >= 18:
            sql="UPDATE VOTERS SET first_name=%s, last_name=%s, voter_id=%s, email=%s,pno=%s where voter_id=%s"
            cur=mydb.cursor()
            cur.execute(sql, (first_name, last_name, voter_id, email, pno, voter_id))
            mydb.commit()
            cur.close()
            flash(r'Database Updated Successfully','Primary')
            return redirect(url_for('home'))
           
        else:
            flash("age should be 18 or greater than 18 is eligible", "info")
    return render_template('update.html')

@app.route('/voting', methods=['POST','GET'])
def voting():
    pkl_file = open('encoder.pkl', 'rb')
    my_le = pickle.load(pkl_file)
    pkl_file.close()
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("Trained.yml")
    cam=cv2.VideoCapture(0, cv2.CAP_DSHOW)
    font = cv2.FONT_HERSHEY_SIMPLEX
    flag = 0
    detected_persons=[]
    global det
    det=0
    while True:
        ret, im = cam.read()
        flag += 1
        if flag==200:
            flash(r"Unable to detect person. Contact help desk for manual voting", "info")
            cv2.destroyAllWindows()
            return render_template('voting.html')
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.2, 5)
        print(faces)
        for (x, y, w, h) in faces:
            cv2.rectangle(im, (x, y), (x + w, y + h), (225, 0, 0), 2)
            Id, conf = recognizer.predict(gray[y:y + h, x:x + w])
            print(conf)
            if (conf > 40):
                det +=1
                det_aadhar = my_le.inverse_transform([Id])[0]
                detected_persons.append(det_aadhar)
                if det >=20:
                    session['select_aadhar']=det_aadhar
                    return redirect(url_for('select_candidate'))

                cv2.putText(im, f"Aadhar: {det_aadhar}", (x, y + h), font, 1, (255, 255, 255), 2)
            else:
                cv2.putText(im, "Unknown", (x, y + h), font, 1, (255, 255, 255), 2)
        cv2.imshow('im', im)
        try:
            cv2.setWindowProperty('im', cv2.WND_PROP_TOPMOST, 1)
        except:
            pass
        if (cv2.waitKey(1) == (ord('q')) ):
            try:
                session['select_aadhar']=det_aadhar
            except:
                cv2.destroyAllWindows()
                return redirect(url_for('home'))
            cv2.destroyAllWindows()
            return redirect(url_for('select_candidate'))
    return render_template('voting.html')


@app.route('/select_candidate', methods=['POST','GET'])
def select_candidate():
    aadhar = session['select_aadhar']

    df_nom = pd.read_sql_query('select * from nominee', mydb)
    all_nom = df_nom['symbol_name'].values
    sq = "select * from vote"
    g = pd.read_sql_query(sq, mydb)
    all_adhar = g['aadhar'].values
    if aadhar in all_adhar:
        flash("You already voted", "warning")
        return redirect(url_for('home'))
    else:
        if request.method == 'POST':
            vote = request.form['test']
            session['vote'] = vote
            sql = "INSERT INTO vote (vote, aadhar) VALUES ('%s', '%s')" % (vote, aadhar)
            cur = mydb.cursor()
            cur.execute(sql)
            mydb.commit()
            cur.close()
            s = "select * from voters where aadhar_id='" + aadhar + "'"
            c = pd.read_sql_query(s, mydb)
            pno = str(c.values[0][7])
            name = str(c.values[0][1])
            ts = time.time()
            date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            url = "https://www.fast2sms.com/dev/bulkV2"

            message = 'Hi ' + name + ' You voted successfully. Thank you for voting at ' + timeStamp + ' on ' + date + '.'
            no = pno
            data1 = {
                "route": "q",
                "message": message,
                "language": "english",
                "flash": 0,
                "numbers": no,
            }

            headers = {
                "authorization": "UwmaiQR5OoA6lSTz93nP0tDxsFEhI7VJrfKkvYjbM2C14Wde8g9lvA2Ghq5VNCjrZ4THWkF1KOwp3Bxd",
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, json=data1)
            print(response)

            flash(r"Voted Successfully", 'Primary')
            return redirect(url_for('home'))
    return render_template('select_candidate.html', noms=sorted(all_nom))
    return render_template('select_candidate.html', noms=sorted(all_nom))

@app.route('/voting_res')
def voting_res():
    votes = pd.read_sql_query('select * from vote', mydb)
    counts = pd.DataFrame(votes['vote'].value_counts())
    counts.reset_index(inplace=True)
    all_imgs=['1.png','2.png','3.jpg','4.png','5.png','6.png']
    all_freqs=[counts[counts['index']==i].iloc[0,1] if i in counts['index'].values else 0 for i in all_imgs]
    df_nom=pd.read_sql_query('select * from nominee', mydb)
    all_nom=df_nom['symbol_name'].values
    return render_template('voting_res.html', freq=all_freqs, noms=all_nom)

if __name__=='__main__':
    app.run(debug=True)

