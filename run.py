from flask import Flask, render_template, redirect, url_for, request
import os
import time
import flask
from log_analysis import LogAnalysisMgr

app = Flask(__name__, static_url_path='')


@app.route('/')
def index():
    login_url = url_for('logs')
    return redirect(login_url)  # 重定向为登录页面

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/logs.nnt')
def logs():
    return render_template('logs.nnt', logs=LogAnalysisMgr.load_ctime_dict())

@app.route('/logview.nnt')
def logview():
    ctime = request.args.get('time')
    if not ctime is None:
        return render_template('logview2.nnt', logs=LogAnalysisMgr.log_by_time_dict(ctime))
    return ""

@app.route('/download.nnt')
def download():
    ctime = request.args.get('time')
    if not ctime is None:
        zip_path = LogAnalysisMgr.zip_log_by_time(ctime, os.path.join(os.path.abspath(os.getcwd()), "static"))
        file_name = ctime + ".zip"
        return redirect(url_for('static', filename=file_name))
    return ""

@app.route('/login.nnt', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        exe_path = os.path.join(os.path.abspath(os.path.dirname(os.getcwd())), "FutuOpenD.exe")
        os.system("start " + exe_path)
        time.sleep(5)
        index_url = url_for("static", filename="rtl1.html")
        return redirect(index_url)  # 重定向为登录页面
    else:
        return render_template('login.nnt')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
    flask.g.count = 0