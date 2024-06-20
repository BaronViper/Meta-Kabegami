from flask import Flask, render_template, redirect, url_for, request, session, send_file
from flask_session import Session
from dotenv import load_dotenv
from PIL import Image, ImageOps
from bs4 import BeautifulSoup
from curl_cffi import requests
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import urllib.request
import random
import smtplib
import os


load_dotenv()
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh;     Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

@app.route('/', methods=["POST", "GET"])
def main_page():

    if request.method == "GET":
        return render_template('index.html')
    else:
        user_agent = random.choice(user_agents)
        headers = {
            'User-Agent': user_agent,
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-GPC': '1',
            'Referer': 'https://www.google.com/'
        }

        response = requests.get(
            "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&proxy_format=protocolipport&format=text&protocol=http")
        proxy_list = response.content.decode().split('\n')
        proxy_list = [proxy.strip() for proxy in proxy_list if proxy.strip()]
        proxy = random.choice(proxy_list)
        proxies = {
            'http': proxy
        }
        img_address = request.form['pname']
        response = requests.get(img_address, headers=headers, proxies=proxies)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        try:
            if response.status_code == 200:
                img_src = soup.find("img", class_="Image--image")['src']
                title = soup.find("h1", class_="item--title").get_text()

                urllib.request.urlretrieve(url=img_src, filename="target_img.png")

                # Convert image to wallpaper (3840x1818)
                img = Image.open("target_img.png")
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
