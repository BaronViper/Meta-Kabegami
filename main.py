from flask import Flask, render_template, send_from_directory, redirect, url_for, request, session, send_file, flash
from flask_session import Session
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageOps, ImageDraw, ImageFilter
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


@app.route('/', methods=["POST", "GET"])
def main_page():
    if request.method == "GET":
        tmp_folder = '/tmp'
        try:
            for filename in os.listdir(tmp_folder):
                file_path = os.path.join(tmp_folder, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except Exception as e:
            print(e)
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
                    # Get a color from near the top-left to use as background fill
                    palette_rgb = pix[30, 1]

                    # Crop a bit from the top to remove any curve (adjust as needed)
                    cropped_img = img.crop((0, 20, img.width, img.height))

                    # Resize the image to square dimensions
                    resized_img = ImageOps.fit(cropped_img, size=(1818, 1818))

                    # Create a new empty image with extended height
                    final_img = Image.new('RGB', (1818, 3840), color=palette_rgb)

                    # Paste the NFT image at the very bottom
                    final_img.paste(resized_img, (0, 3840 - 1818))

                    # Add a gradient blending from the top down to the NFT image
                    gradient = Image.new('RGB', (1818, 3840), color=palette_rgb)
                    draw = ImageDraw.Draw(gradient)

                    for y in range(3840 - 1818):
                        blend = int(255 * (1 - y / (3840 - 1818)))
                        blended_color = (
                            (palette_rgb[0] * (255 - blend) + palette_rgb[0] * blend) // 255,
                            (palette_rgb[1] * (255 - blend) + palette_rgb[1] * blend) // 255,
                            (palette_rgb[2] * (255 - blend) + palette_rgb[2] * blend) // 255
                        )
                        draw.line([(0, y), (1818, y)], fill=blended_color)

                    # Composite the gradient onto the final image
                    final_img.paste(gradient.crop((0, 0, 1818, 3840 - 1818)), (0, 0))

                    # Create a blur zone where the two sections meet
                    blur_zone = final_img.crop((0, 3840 - 1818 - 100, 1818, 3840 - 1818 + 100))
                    blurred = blur_zone.filter(ImageFilter.GaussianBlur(80))

                    # Paste the blurred section back onto the final image
                    final_img.paste(blurred, (0, 3840 - 1818 - 100))

                    # Save the final image
                    final_img.save('/tmp/image_converted.png')

                    session['title'] = title
                    session['img_src'] = img_src

                    return redirect('/create')
                else:
                    flash('Unable to retrieve NFT details. Please check the link and try again.', 'error')
                    return render_template('index.html')
            else:
                flash('Unable to retrieve NFT details. Please check the link and try again.', 'error')
                return render_template('index.html')
        except Exception as e:
            return f"An error occurred: {str(e)}"


@app.route('/image/<filename>')
def get_image(filename):
    return send_from_directory('/tmp', filename)


@app.route('/create', methods=["POST", "GET"])
def create_page():
    if request.method == "GET":
        return render_template('create.html', img_src=session['img_src'], art_title=session['title'],
                               time_now=datetime.now().timestamp())


@app.route('/download')
def download_page():
    path = "/tmp/image_converted.png"
    return send_file(path, as_attachment=True)


# @app.route('/send')
# def send_page():
#     img_data = open('static/images/image_converted.png', 'rb').read()
#     msg = MIMEMultipart()
#     msg['Subject'] = f"Your Generated Wallpaper of {session['title']}"
#     msg['From'] = os.getenv('EMAIL')
#     msg['To'] = os.getenv('TO_EMAIL')
#     text = MIMEText("Thank you for using Meta Kabegami! We've cooked this up for you.")
#     msg.attach(text)
#     image = MIMEImage(img_data, name=os.path.basename('image_converted.png'))
#     msg.attach(image)
#     with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
#         connection.starttls()
#         connection.login(user=os.getenv('EMAIL'), password=os.getenv('PASSWORD'))
#         connection.sendmail(
#             from_addr=os.getenv('EMAIL'),
#             to_addrs=os.getenv('TO_EMAIL'),
#             msg=msg.as_string()
#         )
#     return redirect("/create")
if __name__ == '__main__':
    app.run(debug=True)
