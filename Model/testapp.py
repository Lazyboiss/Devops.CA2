import random
import PIL.Image
import numpy as np
import PIL
import requests
from flask import Flask, jsonify, request
import io
import base64
import json

app = Flask(__name__)

# The URL for the TensorFlow Serving model endpoints
GENERATOR_URL = "http://localhost:8501/v1/models/generator:predict"
DISCRIMINATOR_URL = "http://localhost:8502/v1/models/discriminator:predict"

@app.route('/generate', methods=['POST'])
def generate():
    latent_vector = [round(random.random(), 2) for _ in range(100)]  # Example: Random latent vector with 100 values

    payload = {
        "instances": [
            {
                "keras_tensor_19": [3], 
                "keras_tensor_23": latent_vector
            }
        ]
    }

    response = requests.post(GENERATOR_URL, json=payload)

    if response.status_code == 200:
        prediction = response.json()
        image_data = prediction['predictions'][0]

        print(type(prediction['predictions'][0]))
        image_data = np.array(image_data).reshape(28, 28) 
        image_data = ((image_data + 1) * 127.5).astype(np.uint8)


        image = PIL.Image.fromarray(image_data)
        image_path = 'generated_image.png'
        image.save(image_path)
        return jsonify({"message": "Image generated successfully!", "image_path": image_path})

    else:
        return jsonify({"error": "Failed to generate image", "details": response.text}), 500


def preprocess_image(image: PIL.Image.Image, target_size=(28, 28)):
    """
    Preprocess the image for the discriminator model.
    - Resize the image to the target size.
    - Convert to grayscale (if needed).
    - Normalize pixel values to [0, 1].
    """
    image = image.resize(target_size)
    
    image = image.convert("L")

    image_data = np.array(image, dtype=np.float32) / 255.0 
    
    image_data = image_data.reshape(1, target_size[0], target_size[1], 1)
    
    return image_data

@app.route('/predict', methods=['POST'])
def predict():
    file = request.files.get('image')

    if not file:
        return jsonify({"error": "No image file provided"}), 400

    try:
        image = PIL.Image.open(file)
        
        image_data = preprocess_image(image)

        buffered = io.BytesIO()
        pil_image = PIL.Image.fromarray((image_data[0] * 255).astype(np.uint8)) 
        pil_image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        payload = {
            "instances": [
                {
                    "image": img_base64  
                }
            ]
        }

        discriminator_response = requests.post(DISCRIMINATOR_URL, json=payload)

        if discriminator_response.status_code == 200:
            # Get the predicted class from the discriminator
            discriminator_prediction = discriminator_response.json()
            predicted_class = np.argmax(discriminator_prediction['predictions'][0])

            return jsonify({
                "message": "Image classified successfully!",
                "predicted_class": predicted_class
            })
        else:
            return jsonify({"error": "Failed to classify image", "details": discriminator_response.text}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
