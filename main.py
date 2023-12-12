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
            raise ValueError(
                f"Error: OpenAI version {openai.__version__}"
                " is less than the minimum version 1.2.3\n\n"
                ">>You should run 'pip install --upgrade openai')"
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Error: OPENAI_API_KEY environment variable not set.")

        # Instantiate OpenAI - use openai.OpenAIAPI() instead of openai.OpenAI()
        self.client = openai.OpenAIAPI(api_key)

    @staticmethod
    def old_package(version, minimum):
        version_parts = list(map(int, version.split(".")))
        minimum_parts = list(map(int, minimum.split(".")))
        return version_parts < minimum_parts

    def generate_images(self, image_params):
        try:
            return self.client.images.generate(**image_params)
        except openai.APIError as e:
            print(f"OpenAI API error: {e}")
            raise


class ImageProcessor:
    @staticmethod
    def download_image(url, img_filename, max_retries=3):
        for _ in range(max_retries):
            try:
                print(f"getting URL: {url}")
                response = requests.get(url)
                response.raise_for_status()
                break
            except requests.HTTPError as e:
                print(
                    f"Failed to download image from {url}. Error: {e.response.status_code}"
                )
                retry = input("Retry? (y/n): ")
                if retry.lower() not in ["y", "yes"]:
                    raise

        image = Image.open(BytesIO(response.content))
        image.save(f"{img_filename}.png")
        print(f"{img_filename}.png was saved")
        return image

    @staticmethod
    def decode_base64(data, img_filename):
        if data is None:
            print(f"Warning: Base64 data is None for {img_filename}.")
            return None

        try:
            image = Image.open(BytesIO(base64.b64decode(data)))
            image.save(f"{img_filename}.png")
            print(f"{img_filename}.png was saved")
            return image
        except Exception as e:
            print(f"Error decoding base64 data for {img_filename}: {e}")
            return None


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
        "Subject: beautiful lady sitting in a wine bar in a red dress"
        "Style: the style of artist Jack Vettriano, painted in gouache"
    )

    image_params = {
        "model": "dall-e-3",
        "n": 1,
        "size": "1024x1024",
        "prompt": prompt,
        "user": "myName",
    }

    try:
        openai_client = OpenAIClient()
        images_response = openai_client.generate_images(image_params)
    except ValueError as e:
        print(e)
        return

    images_dt = datetime.utcfromtimestamp(images_response.created)
    img_filename = images_dt.strftime("DALLE-%Y%m%d_%H%M%S")

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
