from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from fake_headers import Headers
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import urllib.request
from PIL import Image, ImageOps
import os

from selenium.webdriver.support.wait import WebDriverWait

load_dotenv()
chrome_driver_path = "C:\Development\chromedriver.exe"
options = webdriver.ChromeOptions()

header = Headers(
    browser="chrome",  # Generate only Chrome UA
    os="win",  # Generate only Windows platform
    headers=False # generate misc headers
)
customUserAgent = header.generate()['User-Agent']

options.add_argument(f"user-agent={customUserAgent}")
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")


@app.route('/', methods=["POST", "GET"])
def main_page():
    if request.method == "GET":
        return render_template('index.html')
    else:
        img_address = request.form['pname']
        driver.get(url=img_address)
        try:
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Image--image"))
            )

            # Get img url
            img = driver.find_element(By.CLASS_NAME, 'Image--image')
            img_src = img.get_attribute('src')

            urllib.request.urlretrieve(url=img_src, filename="target_img.png")

            # Convert image to wallpaper (3840x1818)
            img = Image.open("target_img.png")
            pix = img.load()
            palette_rgb = pix[1, 1]
            resized_img = ImageOps.fit(img, size=(1818, 1818))
            ImageOps.pad(resized_img, (1818, 3840), color=palette_rgb, centering=(0.5, 1)).save("static/images/image_converted.png")

            return render_template('create.html', img_src=img_src)
        except TimeoutException:
            print("Timed out waiting for page to load")
            return render_template('index.html')


@app.route('/create', methods=["POST", "GET"])
def create_page():
    if request.method == "GET":
        return render_template('create.html', img_src="static/images/test.png")


if __name__ == '__main__':
    app.run(debug=True)
