from flask import Flask, render_template, redirect, url_for, request, session
from flask_session import Session
from dotenv import load_dotenv
from PIL import Image, ImageOps
from bs4 import BeautifulSoup
import requests
import urllib.request
import os

load_dotenv()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

@app.route('/', methods=["POST", "GET"])
def main_page():

    if request.method == "GET":
        return render_template('index.html')
    else:
        img_address = request.form['pname']
        response = requests.get(img_address,
                                headers=headers)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        try:
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
        except:
            print("Timed out waiting for page to load")
            return render_template('index.html')


@app.route('/create', methods=["POST", "GET"])
def create_page():
    if request.method == "GET":
        return render_template('create.html', img_src=session['img_src'], art_title=session['title'])


@app.route('/create/test', methods=["POST", "GET"])
def create_page_test():
    if request.method == "GET":
        return render_template('create.html', img_src=r"https://i.seadn.io/s/raw/files/0d304ef87f29306ae752b241871ec0d3.png?auto=format&dpr=1&w=1000", art_title="Azuki #5334")


if __name__ == '__main__':
    app.run(debug=True)
