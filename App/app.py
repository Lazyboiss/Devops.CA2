import PIL.Image
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client
from dotenv import load_dotenv
import os, random, requests, json, PIL, base64, datetime, time, string
import numpy as np
from io import BytesIO
# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
GENERATOR_URL = os.getenv('GENERATOR_URL')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials not found. Check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session key

# LANDING ROUTE

@app.route('/')
def landing_register():
    return render_template('landing_register.html')

# REGISTER/LOGIN ROUTES

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    if not username or not password or not confirm_password:
        flash('All fields are required!', 'warning')
        return redirect(url_for('landing_register'))

    if password != confirm_password:
        flash('Passwords do not match!', 'danger')
        return redirect(url_for('landing_register'))

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    try:
        # Check if username exists
        existing_user = supabase.table("Users").select("username").eq("username", username).execute()
        if existing_user.data:
            flash('Username already taken!', 'danger')
            return redirect(url_for('landing_register'))

        # Insert user into Supabase
        response = supabase.table("Users").insert({"username": username, "password": hashed_password}).execute()

        if response.data:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Try again.', 'danger')

    except Exception as e:
        flash(f"Error: {str(e)}", 'danger')

    return redirect(url_for('landing_register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('All fields are required!', 'warning')
            return redirect(url_for('login'))

        try:
            # Fetch user from Supabase
            user = supabase.table("Users").select("password").eq("username", username).execute()

            if user.data:
                stored_password = user.data[0]['password']
                if check_password_hash(stored_password, password):
                    session['username'] = username
                    flash('Login successful!', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('Invalid username or password!', 'danger')
            else:
                flash('User not found!', 'danger')

        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')

    return render_template('login.html')

# HOME ROUTE

@app.route('/home')
def home():
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('home.html')

# GENERATION ROUTES

@app.route('/generate_letter', methods=['GET', 'POST'])
def generate_letter():
    if request.method == 'POST':
        # Retrieve and validate the letter
        letter = request.form.get('letter', '').strip()
        if len(letter) == 1 and letter.isalpha() and letter.isupper():
            flash(f"Generating content for letter: {letter}", "success")

            latent_vector = [round(random.random(), 2) for _ in range(100)]
            letter_index = ord(letter) - ord('A')

            payload = {
                "instances": [
                    {
                        "keras_tensor_19": [letter_index],
                        "keras_tensor_23": latent_vector
                    }
                ]
            }

            response = requests.post(GENERATOR_URL, json=payload)

            if response.status_code == 200:
                prediction = response.json()
                image_data = prediction["predictions"][0]

                # Convert array -> numpy -> PIL image -> raw bytes
                image_data = np.array(image_data).reshape(28, 28)
                image_data = ((image_data + 1) * 127.5).astype(np.uint8)  # Rescale [-1..1] -> [0..255]
                image = PIL.Image.fromarray(image_data)

                from io import BytesIO
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)
                image_bytes = buffer.read()

                # Base64-encode before storing in a text column
                import base64
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")

                # Insert into Letter_Gen (text column for generated_image)
                username = session.get("username")
                try:
                    response_supabase = supabase.table("Letter_gens").insert({
                        "username": username,
                        "letter": letter,
                        "generated_image": image_b64
                    }).execute()

                    if not response_supabase.data:
                        flash(f"Error saving to Supabase: {response_supabase.error}", "danger")

                except Exception as e:
                    flash(f"Error storing in Supabase: {str(e)}", "danger")

                # Pass the base64 string to the template
                return render_template("generate_letter.html", image_data=image_b64)
            else:
                flash(f"Error generating image: {response.text}", "danger")
                return redirect(url_for("generate_letter"))
        else:
            flash("Please enter exactly one uppercase letter (A–Z).", "danger")
            return redirect(url_for("generate_letter"))

    # GET request: Serve the form
    return render_template("generate_letter.html")

@app.route('/generate_sentence', methods=['GET', 'POST'])
def generate_sentence():
    if request.method == 'POST':
        # 1. Retrieve and validate the text
        text = request.form.get('text', '').strip()
        if not text:
            flash("Please enter some text.", "danger")
            return redirect(url_for('generate_sentence'))
        if len(text) > 20:
            flash("Text cannot exceed 20 characters.", "danger")
            return redirect(url_for('generate_sentence'))

        char_images = []

        for ch in text:
            if ch == ' ':
                # Create a black 28x28 image
                black_img = np.zeros((28, 28), dtype=np.uint8)
                pil_img = PIL.Image.fromarray(black_img)
                char_images.append(pil_img)
            else:
                # Validate uppercase letter if desired
                if not (ch.isalpha() and ch.isupper()):
                    flash("Only uppercase letters and spaces allowed!", "danger")
                    return redirect(url_for('generate_sentence'))

                # Random latent vector for each character
                latent_vector = [round(random.random(), 2) for _ in range(100)]
                letter_index = ord(ch) - ord('A')

                payload = {
                    "instances": [
                        {
                            "keras_tensor_19": [letter_index],
                            "keras_tensor_23": latent_vector
                        }
                    ]
                }

                response = requests.post(GENERATOR_URL, json=payload)
                if response.status_code != 200:
                    flash(f"Error generating letter '{ch}': {response.text}", "danger")
                    return redirect(url_for('generate_sentence'))

                # Convert array -> numpy -> PIL
                prediction = response.json()
                image_data = prediction["predictions"][0]
                image_data = np.array(image_data).reshape(28, 28)
                image_data = ((image_data + 1) * 127.5).astype(np.uint8)  # scale [-1..1]->[0..255]
                pil_img = PIL.Image.fromarray(image_data)
                char_images.append(pil_img)

        # 3. Stitch images side by side
        #    The final width is 28 * number_of_chars, height stays 28
        total_chars = len(char_images)
        final_width = 28 * total_chars
        final_image = PIL.Image.new("L", (final_width, 28))  # "L" mode for 8-bit grayscale

        x_offset = 0
        for img in char_images:
            final_image.paste(img, (x_offset, 0))
            x_offset += 28

        # 4. Convert the final image to base64
        from io import BytesIO
        buffer = BytesIO()
        final_image.save(buffer, format="PNG")
        buffer.seek(0)
        image_bytes = buffer.read()

        import base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # 5. Insert into your table (e.g., Sentence_gens)
        username = session.get("username", "Anonymous")
        try:
            response_supabase = supabase.table("Sentence_gens").insert({
                "username": username,
                "sentence": text,
                "generated_image": image_b64
            }).execute()

            if response_supabase.data:
                flash("Sentence image saved to Supabase successfully!", "success")
            else:
                flash(f"Error saving to Supabase: {response_supabase.error}", "danger")
        except Exception as e:
            flash(f"Error storing in Supabase: {str(e)}", "danger")

        # 6. Return the final image to the template
        return render_template("generate_sentence.html", image_data=image_b64)

    # GET request: Show the form
    return render_template("generate_sentence.html")

# GAME ROUTES

@app.route('/gameinstructions')
def gameinstructions():
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template("gameinstructions.html")

@app.route('/game', methods=['GET', 'POST'])
def game():
    if request.method == 'GET':
        session['score'] = 0
        session['start_time'] = time.time()
        flash("Game started! You have 30 seconds.", "info")
        _generate_new_challenge()
        return render_template("game.html")

    elapsed = time.time() - session.get('start_time', 0)
    if elapsed > 30:
        final_score = session.get('score', 0)
        flash(f"Time's up! Final score: {final_score}", "info")
        return render_template("game_over.html", final_score=final_score)

    user_guess = request.form.get('guess', '').strip().upper()
    current_letter = session.get('current_letter', '')

    if user_guess == current_letter:
        session['score'] = session.get('score', 0) + 1500
        flash("Correct! +1500 points", "success")
    else:
        session['score'] = session.get('score', 0) - 500
        flash(f"Wrong! The letter was {current_letter}. -500 points", "danger")

    _generate_new_challenge()
    return render_template("game.html")

def _generate_new_challenge():
    letter = random.choice(string.ascii_uppercase)
    session['current_letter'] = letter

    latent_vector = [round(random.random(), 2) for _ in range(100)]
    letter_index = ord(letter) - ord('A')
    payload = {
                "instances": [
                    {
                        "keras_tensor_19": [letter_index],
                        "keras_tensor_23": latent_vector
                    }
                ]
            }

    response = requests.post(GENERATOR_URL, json=payload)

    if response.status_code == 200:
        prediction = response.json()
        image_data = prediction["predictions"][0]

        # Convert array -> numpy -> PIL image -> raw bytes
        image_data = np.array(image_data).reshape(28, 28)
        image_data = ((image_data + 1) * 127.5).astype(np.uint8)  # Rescale [-1..1] -> [0..255]
        image = PIL.Image.fromarray(image_data)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        session['current_image'] = base64.b64encode(buffer.read()).decode('utf-8')
    else:
        flash(f"Error generating image, try again later. ")

# HISTORY ROUTES

@app.route('/history')
def history_menu():
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template("history_menu.html")

@app.route('/history/letters')
def letter_history():
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    try:
        username = session.get("username")
        response = supabase.table("Letter_gens").select("*").eq("username", username).execute()
        letter_entries = response.data if response.data else []
    except Exception as e:
        flash(f"Error fetching letter history: {str(e)}", "danger")
        letter_entries = []

    return render_template("letter_history.html", letter_entries=letter_entries)

@app.route('/history/sentences')
def sentence_history():
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    try:
        username = session.get("username")
        response = supabase.table("Sentence_gens").select("*").eq("username", username).execute()
        sentence_entries = response.data if response.data else []
    except Exception as e:
        flash(f"Error fetching sentence history: {str(e)}", "danger")
        sentence_entries = []

    return render_template("sentence_history.html", sentence_entries=sentence_entries)


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
