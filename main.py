from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/create', methods=["POST"])
def create_page():
    pname = request.form['pname']
    return render_template('create.html', pname=pname)


if __name__ == '__main__':
    app.run(debug=True)
