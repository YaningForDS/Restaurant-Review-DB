#!/usr/bin/env python2.7

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response,flash,session
import time


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


DATABASEURI = "postgresql://yx2376:xv48u@104.196.175.120/postgres"
engine = create_engine(DATABASEURI)


@app.before_request
def before_request():

	try:
		g.conn = engine.connect()
	except:
		print "uh oh, problem connecting to database"
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):

	try:
		g.conn.close()
	except Exception as e:
		pass


@app.route('/')
def index():
	cursor = g.conn.execute("SELECT * FROM Users")
	names = []
	for result in cursor:
		names.append(result[3])
	cursor.close()
	cursor1 = g.conn.execute("SELECT placeID FROM Restaurant")
	l = []
	for i in cursor1:
		l.append(i)
	cursor1.close()
	return render_template("index.html", data = names, name = l)


@app.route('/register')
def register():
	return render_template("register.html")

@app.route('/register2',methods = ['POST'])
def register2():
	#if request.method = "POST":
	newusername = request.form['newusername']
	newpassword= request.form['newpassword']
	gender = request.form['gender']
	zipcode = request.form['zipcode']
	cursor = g.conn.execute("SELECT * FROM Users")
	username = []
	n = 0
	for result in cursor:
		username.append(result[3])
		n = n + 1
	newuserid = 'U'+ str(1000 + n + 1)
	if newusername in username:
		user = "Usename Exist. Please choose another username"
		return redirect('/register'),user
	if int(zipcode) < 10000 or int(zipcode) > 99999:
		invalid = "Invalid Zipcode"
		return redirect('/register'),invalid
	cmd = 'INSERT INTO Users(userID,userName,gender,Zip,passcode) VALUES(:name1,:name2,:name3,:name4,:name5)';
	g.conn.execute(text(cmd), name1 = newuserid, name2 = newusername, name3 = gender, name4=zipcode, name5=newpassword);
	return redirect('/')

		
@app.route('/admin',methods = ['GET','POST'])
def admin():
	username = request.form['username'] 
	password = request.form['password']
	cmd = "SELECT * FROM Users WHERE userName=(:name1) AND passCode=(:name2)"
	cursor = g.conn.execute(text(cmd),name1 = username,name2 = password)
	cmd1 = "SELECT R.resName, C.Date FROM Users U, Restaurant R, check_in C WHERE R.placeID = C.placeID AND U.username = (:name3) AND U.userID = C.userID"
	cursor1 = g.conn.execute(text(cmd1),name3 = username) ##show the history of your check in
	cmd2 = "select bc.catname from check_in C, belongscategory bc,Users U where U.username = (:name4) and U.userid = C.userid and C.placeid = bc.placeid group by bc.catname order by count(*) Desc limit 1";
	cursor2 = g.conn.execute(text(cmd2),name4 = username)
	history = []
	for i in cursor1:
		history.append(i)
	cate = []
	for j in cursor2:
		cate.append(j)
	mylist = []
	for content in cursor:
		mylist.append(content)
	if len(mylist) == 0:
		message1 = "Invalid"
		return redirect('/'),message1
		#return render_template('admin.html', message1 = 'Wrong username or password, please enter again')
	else:
		session['name'] = request.form['username']
		#if len(cate) != 0:
		#	session['recomm'] = True
		#else:
		#	session['recomm'] = False
		return render_template('admin.html', data = mylist, history = history, cate = cate)

@app.route('/admin/admin1', methods = ['POST'])
def function():
	#if request.form['submit2'] == "check":
		#info = 'ok'
	category = request.form['category']
	cmd = "SELECT r.placeID, r.resName, r.resAddress, r.Zip FROM Restaurant r, BelongsCategory bc WHERE r.placeID = bc.placeID AND bc.Catname = (:name1)";
	cursor1 = g.conn.execute(text(cmd),name1=category)
	mylist = []
	for content in cursor1:
		mylist.append(content)
	return render_template('function.html',res = mylist)

	
@app.route('/admin/admin1/admin2', methods = ['POST','GET'])
def review_food():
	placeID = request.form['resid']
	session['place'] = request.form['resid']
	if request.form.get('submit1',None) == "Go":

		placeID = request.form['resid']
		cmd = "SELECT foodName FROM Food WHERE placeID = (:name)"
		cursor = g.conn.execute(text(cmd),name=placeID)
		mylist = []
		for content in cursor:
			mylist.append(content)
		cmd1 = "SELECT AVG(rating) AS R FROM Reviews WHERE placeID = (:name1)"
		cursor1 = g.conn.execute(text(cmd1),name1=placeID)
		for content1 in cursor1:
			mylist.append(content1)
		cmd2 = "SELECT R.content, U.userName FROM Reviews R, Users U WHERE R.placeID = (:name2) AND U.userID = R.userID AND R.follow IS NULL"
		cursor2 = g.conn.execute(text(cmd2),name2=placeID)
		first_review = []
		for content2 in cursor2:
			first_review.append(content2)
		cmd3 = "SELECT R1.content,U.userName FROM Reviews R1, Reviews R2, Users U WHERE R2.reviewID = R1.follow AND R1.placeID = (:name3) And R2.placeID = (:name4) AND R1.userID = U.userID "
		cursor3 = g.conn.execute(text(cmd3),name3=placeID,name4=placeID)
		second_level = []
		for content3 in cursor3:
			second_level.append(content3)

		return render_template('review.html', n = mylist, rating = mylist[-1],first_review=first_review,second_level=second_level)
		#return render_template('fack.html',news = "Hello World")
	
@app.route('/admin/admin1/admin2/admin3/review', methods= ['GET','POST'])	
def add_review():
	#if request.form.get('review', None) == "review":
	if request.form['review'] == "review":
		myplaceid = session['place']
		review_content = request.form['newreview']
		rating = int(request.form['rating'])
		cursor4 = g.conn.execute("SELECT reviewid FROM Reviews")
		myname = session['name']
		n = 0
		for i in cursor4:
			n = n + 1
		new_review_id = n + 1			
		cmd5 = "insert into reviews(reviewid,userid,placeid,content,rating) VALUES (:name10,(select userid from users where username=(:name11)),:name12,:name13,:name14)"
		g.conn.execute(text(cmd5),name10 = new_review_id,name11 = myname, name12=myplaceid,name13=review_content,name14 = rating)		
		return render_template('fack.html',news="add successfully!")


		
		
@app.route('/admin/admin1/admin2/admin3', methods = ['POST','GET'])
def check():
	n = session['name']
	p = session['place']
	if request.form['submit2'] == "check":
		n = session['name']
		p = session['place']
		cmd = "SELECT * from check_in where userid = (select userid from users where userName = (:name1)) AND placeid = (:name2) AND date = (select current_date)"
		cursor = g.conn.execute(text(cmd),name1 = n,name2 = p)
		mylist = []
		for content in cursor:
			mylist.append(content)
		if len(mylist) != 0:
			info = "You can not check in at the same day and at same restaurant"
		else:
			cmd4 = "INSERT INTO check_in (userID,placeID,Date) VALUES ((select userid from users where userName = (:name5)),((:name6)),(select current_date))"
			cursor4 = g.conn.execute(text(cmd4),name5 = n,name6 = p)
			info = 'You have successfilly checked in'
		return render_template('anotherfile.html',info = info)
	
			


@app.route('/login')
def login():
	abort(401)
	this_is_never_executed()

if __name__ == "__main__":
	import click
	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):

		HOST, PORT = host, port	
		print "running on %s:%d" % (HOST, PORT)
		app.secret_key = "2Q\x8b\x03\x9e\x10\x9a\xa7\xb5\t\x9f\xabi^3q8iP\x9d\xfa\xe2\x97"
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
	run()




