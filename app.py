from flask import Flask, render_template, request, jsonify, flash
import os
import pandas as pd
import re
from fuzzywuzzy import process  # Import fuzzywuzzy for fuzzy matching

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Folder to store uploaded images (temporary storage)
UPLOAD_FOLDER = 'static/Food_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load the CSV dataset
csv_file = 'cuisine_updated.csv'
df = pd.read_csv(csv_file)

# Function to clean and format names (for comparison)
def clean_name(name):
    return re.sub(r'[^\w\s]', '', name).replace(' ', '_').lower()

# Function to get the relevant data for a matched food name
def get_recipe_data(food_name):
    cleaned_food_name = clean_name(food_name)
    row = df[df['name'].apply(lambda x: clean_name(x) == cleaned_food_name)]

    if not row.empty:
        return {
            'description': row['description'].values[0],
            'cuisine': row['cuisine'].values[0],
            'course': row['course'].values[0],
            'diet': row['diet'].values[0],
            'prep_time': row['prep_time'].values[0],
            'ingredients': row['ingredients'].values[0],
            'instructions': row['instructions'].values[0]
        }
    return None

# Function to get related food items using fuzzy matching
def get_related_foods(food_name):
    food_names = df['name'].tolist()
    matches = process.extract(food_name, food_names, limit=5)  # Get top 5 matches
    return [match[0] for match in matches]  # Return food names of the matches

# Home route, renders the chat interface
@app.route('/')
def index():
    return render_template('index4.html')

# Route to handle AJAX requests
@app.route('/chat', methods=['POST'])
def chat():
    # Handle file uploads for image-based search
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        image_name = os.path.splitext(file.filename)[0]
        recipe_data = get_recipe_data(image_name)
        return jsonify({
            'recipe': recipe_data,
            'image_url': file_path,
            'search_type': 'image',
            'user_message': "Uploaded an image for search."
        })

    # Handle food name search
    elif 'food_name' in request.form and request.form['food_name']:
        food_name = request.form['food_name']
        recipe_data = get_recipe_data(food_name)

        # Get related food suggestions
        related_foods = get_related_foods(food_name)

        return jsonify({
            'recipe': recipe_data,
            'related_foods': related_foods,  # Return related food suggestions
            'image_url': None,
            'search_type': 'name',
            'user_message': f"Searched for food name: {food_name}"
        })

    return jsonify({
        'recipe': None,
        'related_foods': [],
        'image_url': None,
        'search_type': None,
        'user_message': None
    })

if __name__ == '__main__':
    app.run(debug=True)
