"""
    export OPENAI_API_KEY="your-api-key"
    python main_script.py

"""

import os
from io import BytesIO
from datetime import datetime
import base64
import requests
from PIL import Image, ImageTk
import tkinter as tk
import openai

class OpenAIClient:
    def __init__(self):
        if self.old_package(openai.__version__, "1.2.3"):
            raise ValueError(f"Error: OpenAI version {openai.__version__}"
                             " is less than the minimum version 1.2.3\n\n"
                             ">>You should run 'pip install --upgrade openai')")

        # Instantiate OpenAI - this requires OpenAI key in environmnet varable
        self.client = openai.OpenAI()


    @staticmethod
    def old_package(version, minimum):
        version_parts = list(map(int, version.split(".")))
        minimum_parts = list(map(int, minimum.split(".")))
        return version_parts < minimum_parts

    def generate_images(self, image_params):
        try:
            return self.client.images.generate(**image_params)
        except openai.APIConnectionError as e:
            print(f"Server connection error: {e.__cause__}")
            raise
        except openai.RateLimitError as e:
            print(f"OpenAI RATE LIMIT error {e.status_code}: {e.response}")
            raise
        except openai.APIStatusError as e:
            print(f"OpenAI STATUS error {e.status_code}: {e.response}")
            raise
        except openai.BadRequestError as e:
            print(f"OpenAI BAD REQUEST error {e.status_code}: {e.response}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise

# request image, decode and convert to png
class ImageProcessor:
    @staticmethod
    def download_image(url, img_filename):
        while True:
            try:
                print(f"getting URL: {url}")
                response = requests.get(url)
                response.raise_for_status()
            except requests.HTTPError as e:
                print(f"Failed to download image from {url}. Error: {e.response.status_code}")
                retry = input("Retry? (y/n): ")
                if retry.lower() in ["n", "no"]:
                    raise
                else:
                    continue
            break

        image = Image.open(BytesIO(response.content))
        image.save(f"{img_filename}.png")
        print(f"{img_filename}.png was saved")
        return image

    @staticmethod
    def decode_base64(data, img_filename):
        if data is None:
            print("Warning: Base64 data is None.")
            return None

        image = Image.open(BytesIO(base64.b64decode(data)))
        image.save(f"{img_filename}.png")
        print(f"{img_filename}.png was saved")
        return image

# view image by clicking link 
class ImageGUI:
    @staticmethod
    def display_image(image, img_index):
        if image.width > 512 or image.height > 512:
            image.thumbnail((512, 512))

        window = tk.Tk()
        window.title(f"Image {img_index}")

        tk_image = ImageTk.PhotoImage(image)
        label = tk.Label(window, image=tk_image)
        label.pack()

        window.mainloop()

def main():
    prompt = (
            "Subject: beautiful lady sitting in a wine bar in a green dress"
        "Style: the style of artist Jack Vettriano"
    )

    image_params = {
        "model": "dall-e-2",
        "n": 1,
        "size": "1024x1024",
        "prompt": prompt, 
        "user": "myName",
    }

    openai_client = OpenAIClient()

    try:
        images_response = openai_client.generate_images(image_params)
    except openai.APIConnectionError as e:
        print(f"Server connection error: {e.__cause__}")
        return
    except openai.RateLimitError as e:
        print(f"OpenAI RATE LIMIT error {e.status_code}: {e.response}")
        return
    except openai.APIStatusError as e:
        print(f"OpenAI STATUS error {e.status_code}: {e.response}")
        return
    except openai.BadRequestError as e:
        print(f"OpenAI BAD REQUEST error {e.status_code}: {e.response}")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

    images_dt = datetime.utcfromtimestamp(images_response.created)
    img_filename = images_dt.strftime('DALLE-%Y%m%d_%H%M%S')

    revised_prompt = images_response.data[0].revised_prompt

    image_url_list = [image.model_dump()["url"] for image in images_response.data]
    image_data_list = [image.model_dump()["b64_json"] for image in images_response.data]

    image_objects = []

    image_processor = ImageProcessor()
    for i, url in enumerate(image_url_list):
        image_objects.append(image_processor.download_image(url, f"{img_filename}_{i}"))

    for i, data in enumerate(image_data_list):
        decoded_image = image_processor.decode_base64(data, f"{img_filename}_{i}")
        if decoded_image is not None:
            image_objects.append(decoded_image)

    if image_objects:
        image_gui = ImageGUI()
        for i, img in enumerate(image_objects):
            image_gui.display_image(img, i)

# main driver
if __name__ == "__main__":
    main()

