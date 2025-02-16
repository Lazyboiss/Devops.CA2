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
    # Generate a latent vector with 100 random values between 0 and 1
    latent_vector = [round(random.random(), 2) for _ in range(100)]  # Example: Random latent vector with 100 values

    # Prepare the input data in the expected format
    payload = {
        "instances": [
            {
                "keras_tensor_19": [3],  # Example label or scalar value
                "keras_tensor_23": latent_vector  # Latent vector with 100 random values
            }
        ]
    }

    # Send the POST request to the generator model
    response = requests.post(GENERATOR_URL, json=payload)

    if response.status_code == 200:
        # If the request was successful, process the response

        prediction = response.json()
        image_data = prediction['predictions'][0]

        print(type(prediction['predictions'][0]))
        # Process the image data (reshape and rescale)
        image_data = np.array(image_data).reshape(28, 28)  # Assuming a 28x28 grayscale image

        # Rescale the data to the range 0-255 for proper image display
        # Assuming the model output is in the range [-1, 1], rescale it to [0, 255]
        image_data = ((image_data + 1) * 127.5).astype(np.uint8)

        # Convert to image using PIL
        image = PIL.Image.fromarray(image_data)

        # Save the image to the same directory
        image_path = 'generated_image.png'
        image.save(image_path)

        # Return the response with the image path
        return jsonify({"message": "Image generated successfully!", "image_path": image_path})

    else:
        # If there was an error, return the error
        return jsonify({"error": "Failed to generate image", "details": response.text}), 500


def preprocess_image(image: PIL.Image.Image, target_size=(28, 28)):
    """
    Preprocess the image for the discriminator model.
    - Resize the image to the target size.
    - Convert to grayscale (if needed).
    - Normalize pixel values to [0, 1].
    """
    # Resize the image to match the model's input dimensions
    image = image.resize(target_size)
    
    # Convert image to grayscale (if necessary, assuming the model works with grayscale images)
    image = image.convert("L")  # 'L' mode for grayscale

    # Convert to numpy array and normalize
    image_data = np.array(image, dtype=np.float32) / 255.0  # Normalize to [0, 1]
    
    # Reshape for the model, assuming the model expects a batch size of 1
    image_data = image_data.reshape(1, target_size[0], target_size[1], 1)
    
    return image_data

@app.route('/predict', methods=['POST'])
def predict():
    # Get the image file from the request
    file = request.files.get('image')

    if not file:
        return jsonify({"error": "No image file provided"}), 400

    try:
        # Open the image and preprocess it
        image = PIL.Image.open(file)
        
        # Preprocess the image to match the model input requirements
        image_data = preprocess_image(image)

        # Convert the processed image data into a base64-encoded string
        buffered = io.BytesIO()
        pil_image = PIL.Image.fromarray((image_data[0] * 255).astype(np.uint8))  # Rescale if normalized
        pil_image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Prepare the payload with the base64 image data
        payload = {
            "instances": [
                {
                    "image": img_base64  # Sending the base64 encoded image as part of the JSON payload
                }
            ]
        }

        # Send the base64-encoded image to the discriminator model
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
