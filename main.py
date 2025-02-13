from flask import Flask, render_template, redirect, url_for, request, session, send_file
from flask_session import Session
from dotenv import load_dotenv
from PIL import Image, ImageOps
from bs4 import BeautifulSoup
from curl_cffi import requests
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from io import BytesIO
import urllib.request
import random
import smtplib
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.secret_key = os.urandom(24)

@app.route('/', methods=["POST", "GET"])
def main_page():

    if request.method == "GET":
        return render_template('index.html')
    else:
        img_address = request.form['pname']
        response = requests.get(img_address)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        try:
            if response.status_code == 200:
                img_tag = soup.find("meta", property="og:image")
                title_tag = soup.find("meta", property="og:title")
                if img_tag and title_tag:
                    img_src = img_tag["content"]
                    title = title_tag["content"]


                response = requests.get(img_src)

                img = Image.open(BytesIO(response.content))
                img.save("/tmp/target_img.png")
                pix = img.load()
                palette_rgb = pix[1, 1]
                resized_img = ImageOps.fit(img, size=(1818, 1818))
                ImageOps.pad(resized_img, (1818, 3840), color=palette_rgb, centering=(0.5, 1)).save("static/images/image_converted.png")

                session['title'] = title
                session['img_src'] = img_src

                return redirect('/create')
            else:
                return f"{response.status_code}: {response.text}"
        except Exception as e:
            return f"An error occurred: {str(e)}"

@app.route('/create', methods=["POST", "GET"])
def create_page():
    if request.method == "GET":
        return render_template('create.html', img_src=session['img_src'], art_title=session['title'])

@app.route('/download')
def download_page():
    path = "static/images/image_converted.png"
    return send_file(path, as_attachment=True)

@app.route('/send')
def send_page():
    img_data = open('static/images/image_converted.png', 'rb').read()
    msg = MIMEMultipart()
    msg['Subject'] = f"Your Generated Wallpaper of {session['title']}"
    msg['From'] = os.getenv('EMAIL')
    msg['To'] = os.getenv('TO_EMAIL')
    text = MIMEText("Thank you for using Meta Kabegami! We've cooked this up for you.")
    msg.attach(text)
    image = MIMEImage(img_data, name=os.path.basename('image_converted.png'))
    msg.attach(image)
    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        connection.starttls()
        connection.login(user=os.getenv('EMAIL'), password=os.getenv('PASSWORD'))
        connection.sendmail(
            from_addr=os.getenv('EMAIL'),
            to_addrs=os.getenv('TO_EMAIL'),
            msg=msg.as_string()
        )
    return redirect("/create")
if __name__ == '__main__':
    app.run(debug=True)
