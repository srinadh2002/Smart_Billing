from flask import Flask, render_template, request, session, redirect, url_for, Response, flash
import mysql.connector as mysql 
import re
from twilio.rest import Client 
import random
import cv2
from pyzbar import pyzbar
import os


db=mysql.connect(
    host='localhost',
    user='root',
    password='Srinadh@212002',
    database='smart_billing'
)

cur=db.cursor()


app=Flask(__name__)
app.secret_key="srinadh"


@app.route('/')
def Main_Page():
    return render_template("index.html")

@app.route("/login")
def LoginPage():
    return render_template("login.html")

@app.route('/register')
def RegisterPage():
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def loginData():
    mobno=request.form['mobileno']
    a=0
    Pattern = re.compile("(0|91)?[6-9][0-9]{9}")
    if Pattern.fullmatch(mobno):
        a=1
    else:
        return render_template('login.html',result="Invalid Mobile No!")  
    if a==1:
        password=request.form['loginpassword']
        session['mobileno']=mobno
        session['loginpassword']=password
        sql="SELECT mobileno,password from customer_data where mobileno=%s"
        val=[(session['mobileno'])]
        cur.execute(sql,val)
        logdata = cur.fetchone()
        if logdata:
            if  session['mobileno'] == str(logdata[0]) and session['loginpassword'] == logdata[1]:
                return render_template('home.html')
            else:
                result='Invalid Login'
                return render_template('login.html',result=result)
        else:
            result="No Records Found!! Please Create Account"
            return render_template('login.html', result=result)

@app.route('/register', methods=['POST'])
def registerData():
    fname=request.form['firstname']
    lname=request.form['lastname']
    regpass=request.form['registerpassword']
    confpass=request.form['confirmpassword']
    mobno=request.form['mobileno']

    session['mobileno']=mobno
    sql="SELECT mobileno from customer_data where mobileno=%s"
    un=[(session['mobileno'])]
    cur.execute(sql,un)
    regdata=cur.fetchone()
    if regdata:
        if session['mobileno']==regdata[0]:
            return render_template('register.html',abc="Mobile No Already Exists!",fname=fname,lname=lname,regpass=regpass,confpass=confpass,mobno=mobno)
    else: 
        a=0;b=0;c=0;d=0
        if (fname.isalpha() or bool(re.search(r"\s", fname))) and (lname.isalpha() or bool(re.search(r"\s", lname))):
            a=1
        else:
            return render_template('register.html',abc="First and Last Names should be Characters.",fname=fname,lname=lname,regpass=regpass,confpass=confpass,mobno=mobno)
        if regpass!=confpass:
            return render_template('register.html',abc="No Match of Passwords!",fname=fname,lname=lname,regpass=regpass,confpass=confpass,mobno=mobno) 
        else:
            b=1
        if validate_password(regpass):
            c=1
        else:
            return render_template('register.html',abc="Invalid password!",fname=fname,lname=lname,regpass=regpass,confpass=confpass,mobno=mobno)
        Pattern = re.compile("(0|91)?[6-9][0-9]{9}")
        if Pattern.fullmatch(mobno):
            d=1
        else:
            return render_template('register.html',abc="Invalid Mobile No!",fname=fname,lname=lname,regpass=regpass,confpass=confpass,mobno=mobno)
    if a==1 and b==1 and c==1 and d==1:
        sql="INSERT INTO customer_data(firstname,lastname,password,mobileno) VALUES(%s,%s,%s,%s)"
        val=(fname,lname,regpass,mobno)
        cur.execute(sql,val)
        db.commit() 

        name=fname+' '+lname
        sql1="CREATE TABLE test_%s(barcode varchar(20),items varchar(20),price int)"
        val1=[int(mobno)]
        cur.execute(sql1,val1)
        sql2="CREATE TABLE copy_%s(barcode varchar(20),items varchar(20),price int)"
        val2=[int(mobno)]
        cur.execute(sql2,val2)
        return render_template('register.html',abc="Registration Successful!")
    
def validate_password(password):
    regular_expression = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
    pattern = re.compile(regular_expression)  
    valid = re.search(pattern, password)
    if valid:
        return True
    else:
        return False

@app.route('/delete/<string:barcode>')
def DeleteData(barcode):
    query="DELETE FROM test_%s where barcode=%s limit 1"
    mobno=session['mobileno']
    value=[int(mobno),barcode]
    query1="DELETE FROM copy_%s where barcode=%s limit 1"
    value1=[int(mobno),barcode]
    cur.execute(query,value)
    cur.execute(query1,value1)
    db.commit()
    return redirect('/cart')

@app.route('/queries',methods=['POST'])
def Customerqueries():
    name=request.form['custname']
    mail=request.form['custmail']
    sub=request.form['custsub']
    msg=request.form['custmsg']

    sql="INSERT INTO customer_queries(name,emailid,subject,message) VALUES(%s,%s,%s,%s)"
    val=(name,mail,sub,msg)
    cur.execute(sql,val)
    db.commit()
    return render_template('index.html')

@app.route('/trolleyvalidate', methods=['POST'])
def trolleyValidate():
    trolleyid=request.form['trolleyid']
    return render_template('home.html')

@app.route('/home')
def Home():
    return render_template('home.html')

@app.route('/cart')
def Cart():
    return render_template('cart.html',data=getdata(),total="Total: "+gettotal()+" Rs")
    
def getdata():
    query="SELECT barcode,items,price from test_%s"
    mobno=session['mobileno']
    value=[int(mobno)]
    cur.execute(query,value)
    result=cur.fetchall()
    return result

def gettotal():
    query="SELECT IFNULL(SUM(price), 0) FROM test_%s"
    mobno=session['mobileno']
    value=[int(mobno)]
    cur.execute(query,value)
    result=cur.fetchall()
    s=str(result[0][0])
    return s

@app.route('/billdetails')
def BillDetails():
    return render_template('billdetails.html',detail=getdata(),total="Total: "+gettotal()+" Rs")

@app.route('/back')
def Back():
    return redirect('/cart')

@app.route('/forget')
def ForgetPass():
    return render_template('forget.html')

@app.route('/pass_reset')
def Pass_Reset():
    return render_template('pass_reset.html')

@app.route('/pass_reset', methods=['GET','POST'])
def PassReset():
    passwrd=request.form['password']
    cnfpasswrd=request.form['confirmpassword']
    if passwrd!=cnfpasswrd:
        return render_template('pass_reset.html',result="No match of passwords!",password=passwrd,cnfpassword=cnfpasswrd)
    else:
        if validate_password(passwrd):
            update_password(passwrd)
            return render_template('pass_reset.html',result="Password Updated Successfully!")
        else:
            return render_template('pass_reset.html',result="Invalid Password!",password=passwrd,cnfpassword=cnfpasswrd)

def update_password(password):
    sql="UPDATE customer_data SET password=%s WHERE mobileno=%s"
    mobno=session['mobileno']
    val=[password,int(mobno)]
    cur.execute(sql,val)
    db.commit()

@app.route('/forget', methods=['GET','POST'])
def Forget_Pass():
    mobileno=request.form['mobileno']
    session['mobileno']=mobileno
    mobno="+91"+mobileno
    sql="SELECT mobileno from customer_data where mobileno=%s"
    un=[(session['mobileno'])]
    cur.execute(sql,un)
    regdata=cur.fetchone()
    if regdata:
        if session['mobileno']==regdata[0]:
            val = Get_OTP(mobno)
            if val:
                return render_template('enterotp.html',result="OTP Sent Successful!")
    else:
        return render_template('forget.html',result="Mobile No doesn't Exist!",mobnum=mobileno)

def Generate_OTP():
    return random.randrange(100000,999999)

def Get_OTP(mobileno):
    account_sid='AC01523fc60b88053ffbfe56b1902cea5a'
    auth_token='2772bf2e35636a10c2d81e6105738e67'
    client= Client(account_sid,auth_token)
    otp=Generate_OTP()
    session['otp']=otp
    body='Your OTP is ' + str(otp)
    message=client.messages.create(from_='+14067294598',body=body,to=mobileno)
    if message.sid:
        return True 
    else:
        return False

@app.route('/enterotp', methods=['GET','POST'])
def OTPValidate():
    userotp=request.form['enterotp']
    if str(session['otp'])==userotp:
        return render_template('pass_reset.html')
    else:
        return render_template('enterotp.html',result="Invalid OTP!",userotp=userotp)
    
@app.route('/resend')
def Resend():
    mobileno=session['mobileno']
    mobno="+91"+mobileno
    val = Get_OTP(mobno)
    if val:
        return render_template('enterotp.html',result="OTP Sent Successful!")

@app.route('/checkout')
def logout():
    query="DELETE FROM test_%s"
    mobno=session['mobileno']
    value=[int(mobno)]
    cur.execute(query,value)
    db.commit()
    session.pop('mobileno')
    session.pop('loginpassword')
    return render_template('login.html')

@app.route('/camera')
def Camera():
    return render_template('camera.html')

@app.route('/video')
def video():
    return Response(opencam(),mimetype='multipart/x-mixed-replace; boundary=frame')

def opencam():
    camera = cv2.VideoCapture(0)
    #url = "http://192.168.0.103:8080/video"
    #camera.open(url)
    success, frame = camera.read()
    while success:
        success, frame = camera.read()
        frame = read_barcodes(frame)
        ret,buffer=cv2.imencode('.jpg',frame)
        frame=buffer.tobytes()
        yield(b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
def read_barcodes(frame): 
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        x, y, w, h = barcode.rect
        barcode_info = barcode.data.decode('utf-8')
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        with open("barcode_result.txt", mode ='w') as file:
            file.write(barcode_info)
    return frame

@app.route('/addtocart')
def AddtoCart():
    res=Read_File()
    if res:
        data=Read_Database(res)
        try:
            a=data[0]
            b=data[1]
            c=data[2]
            Insert_Database(a,b,c)
            with open("barcode_result.txt", mode='w') as file:
                file.truncate(0)
            return render_template('camera.html',result="Item added to Cart, Success!")
        except:
            return render_template('camera.html',result="Scan the Item, Again!")
    else:
        return render_template('camera.html',result="Scan the Item, first!")

def Read_File():
    with open("barcode_result.txt", mode='r') as file:
        result=file.read()
    return result

def Read_Database(barcode):
    query="SELECT barcode,name,price FROM product_details where barcode=%s"
    val=[int(barcode)]
    cur.execute(query,val)
    res=cur.fetchone()
    return res

def Insert_Database(barcode,item,price):
    query="INSERT INTO test_%s(barcode,items,price) VALUES(%s,%s,%s)"
    mobno=session['mobileno']
    val=[int(mobno),barcode,item,price]
    cur.execute(query,val)
    query1="INSERT INTO copy_%s(barcode,items,price) VALUES(%s,%s,%s)"
    mobno=session['mobileno']
    val1=[int(mobno),barcode,item,price]
    cur.execute(query1,val1)
    db.commit()


if __name__=="__main__":
    app.run(debug=True)
