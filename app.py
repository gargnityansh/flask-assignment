from flask import Flask,session,redirect,request,request, render_template
from google_auth_oauthlib.flow import Flow
import os
import pathlib
import requests
from pip._vendor import cachecontrol
import google.auth.transport.requests
from google.oauth2 import id_token
import psycopg2
import random

app = Flask(__name__)
app.secret_key = "This is a Flask app"
GOOGLE_CLIENT_ID = '812356535309-ciqnb7vdigcoevuvag6qt7d3qb42c1mc.apps.googleusercontent.com'
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow = Flow.from_client_secrets_file(
	client_secrets_file=client_secrets_file,
	scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
	redirect_uri="https://google-flask-login.herokuapp.com/callback")

def is_login(function):
	def wrapper(*args, **kwargs):
		if 'userid' not in session:
			return "You need to signin first!<br><a href='/'><button>Back</button></a>"
		else:
			return function()
	wrapper.__name__ = function.__name__
	return wrapper

@app.route("/login")
def login():
	authorization_url, state = flow.authorization_url()
	session['state'] = state
	return redirect(authorization_url)

@app.route("/callback")
def callback():
	flow.fetch_token(authorization_response=request.url)
	if not session['state'] == request.args['state']:
		return "not allowed"
	credentials = flow.credentials
	request_session = requests.session()
	cached_session = cachecontrol.CacheControl(request_session)
	token_request = google.auth.transport.requests.Request(session=cached_session)
	id_info = id_token.verify_oauth2_token(
		id_token=credentials._id_token,
		request=token_request,
		audience=GOOGLE_CLIENT_ID)
	session['userid'] =  id_info['name']
	return redirect("/interface")

@app.route("/logout")
def logout():
	session.clear()
	return redirect("/")

@app.route("/")
def index():
	return render_template('index.html')

@app.route("/interface")
@is_login
def interface():
	return render_template('interface.html', msg=False)

@app.route("/iris", methods=['get','post'])
@is_login
def iris():
	if request.method == 'POST':
		s_l = request.form.get('sepal_length')
		s_w = request.form.get('sepal_width')
		p_l = request.form.get('petal_length')
		p_w = request.form.get('petal_width')
		name = request.form.get('species_name')
		try:	
			connection = psycopg2.connect(user="rzblrgulzldnjg",
				dbname="dbd5bktp4lh82l",
				password="e9915d023001a43d29ddc91bf01b797f519ce53984a45e5daaabf2a545b9f059",
				host="ec2-107-20-24-247.compute-1.amazonaws.com",
				port="5432")
			cursor = connection.cursor()
			cursor.execute("INSERT INTO iris (sepal_length,sepal_width,petal_length,petal_width,name,id) Values (%s,%s,%s,%s,%s,%s)", (s_l,s_w,p_l,p_w,name,random.randint(150,1000000000)))
			if (connection):
				connection.commit()
				cursor.close()
				connection.close()
			return render_template('interface.html', msg=True)
		except (Exception, psycopg2.Error) as error:
			return str(error)
	return "Service is UP!"

if __name__ == "__main__":
	app.run(debug=True)