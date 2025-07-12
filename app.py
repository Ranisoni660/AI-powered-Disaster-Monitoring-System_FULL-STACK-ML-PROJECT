import os
import pickle
import spacy
import re
import nltk
import json
import langdetect
from deep_translator import GoogleTranslator
from flask import Flask, render_template, request, jsonify, make_response
from werkzeug.utils import secure_filename
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import logging
import io
import csv

logging.basicConfig(filename='disaster_errors.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

nltk.download('vader_lexicon', quiet=True)

# -------- LOGIC FROM FINAL FUNCTION STARTS HERE --------

try:
    nlp_en = spacy.load("en_core_web_sm")
    nlp_multi = spacy.load("xx_ent_wiki_sm")
except Exception as e:
    logging.error(f"Failed to load spaCy models: {e}")
    raise

sia = SentimentIntensityAnalyzer()

def load_disaster_keywords(file_path='disaster_keywords.txt'):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError as e:
        logging.error(f"Disaster keywords file not found: {e}")
        print(f"Error: {file_path} not found.")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in disaster keywords file: {e}")
        print(f"Error: {file_path} is not a valid JSON file.")
        return {}

def load_severity_weights(file_path='disaster_severity.json'):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError as e:
        logging.error(f"Severity weights file not found: {e}")
        print(f"Error: {file_path} not found.")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in severity weights file: {e}")
        print(f"Error: {file_path} is not a valid JSON file.")
        return {
            "earthquake": 0.8, "flood": 0.7, "hurricane": 0.9, "tornado": 0.75,
            "wildfire": 0.65, "tsunami": 0.85, "volcanic eruption": 0.7,
            "landslide": 0.6, "drought": 0.5, "heatwave": 0.55
        }

def load_city_aliases():
    return {
        'ny': 'New York', 'nyc': 'New York', 'big apple': 'New York','la': 'Los Angeles', 'la la land': 'Los Angeles', 'chi': 'Chicago', 'chi-town': 'Chicago',
        'sf': 'San Francisco', 'bay area': 'San Francisco', 'vegas': 'Las Vegas', 'sin city': 'Las Vegas','philly': 'Philadelphia', 'bmore': 'Baltimore', 'atl': 'Atlanta', 'nola': 'New Orleans',
        'beantown': 'Boston', 'motor city': 'Detroit', 'mia': 'Miami', 'hou': 'Houston','phx': 'Phoenix', 'sd': 'San Diego', 'tampa': 'Tampa', 'dc': 'Washington','mum': 'Mumbai', 'mumbai': 'Mumbai', 'del': 'Delhi', 'delhi': 'Delhi','blr': 'Bangalore', 'bengaluru': 'Bangalore', 'hyd': 'Hyderabad', 'madras': 'Chennai',
        'cal': 'Kolkata', 'kolkata': 'Kolkata', 'pune': 'Pune', 'ahmd': 'Ahmedabad', 'kochi': 'Kochi','ldn': 'London', 'par': 'Paris', 'paris': 'Paris', 'berlin': 'Berlin', 'ams': 'Amsterdam',
        'barca': 'Barcelona', 'madriz': 'Madrid', 'roma': 'Rome', 'dub': 'Dublin','syd': 'Sydney', 'sydney': 'Sydney', 'melbs': 'Melbourne', 'mel': 'Melbourne','brissy': 'Brisbane', 'auck': 'Auckland', 'welly': 'Wellington','t-dot': 'Toronto', 'yyz': 'Toronto', 'van': 'Vancouver', 'vancity': 'Vancouver','sao': 'São Paulo', 'rio': 'Rio de Janeiro', 'lima': 'Lima', 'bogota': 'Bogotá',
        'buenos aires': 'Buenos Aires', 'méxico': 'Mexico', 'mexico city': 'Mexico','capetown': 'Cape Town', 'cape town': 'Cape Town', 'joburg': 'Johannesburg','lagos': 'Lagos', 'cairo': 'Cairo', 'nairobi': 'Nairobi', 'addis': 'Addis Ababa','tok': 'Tokyo', 'tokyo': 'Tokyo', 'osaka': 'Osaka', 'jkt': 'Jakarta', 'jakarta': 'Jakarta',
        'bkk': 'Bangkok', 'kl': 'Kuala Lumpur', 'hk': 'Hong Kong', 'shanghai': 'Shanghai','bj': 'Beijing', 'seoul': 'Seoul', 'manila': 'Manila', 'vn': 'Hanoi', 'taipai': 'Taipei','tehran': 'Tehran', 'riyadh': 'Riyadh', 'colombo': 'Colombo', 'kathmandu': 'Kathmandu','karachi': 'Karachi', 'dubai': 'Dubai', 'istanbul': 'Istanbul', 'ank': 'Ankara'
    }

disaster_keywords = load_disaster_keywords()
severity_weights = load_severity_weights()
city_aliases = load_city_aliases()

def clean_tweet(tweet):
    tweet = re.sub(r'https?://\S+', '', tweet)
    tweet = re.sub(r'#\w+', '', tweet)
    tweet = re.sub(r'@\w+', '', tweet)
    tweet = re.sub(r'[*%!]', '', tweet)
    tweet = ' '.join(tweet.split()).strip()
    return tweet if tweet else 'Empty'

def detect_language(tweet):
    try:
        return langdetect.detect(tweet)
    except:
        logging.warning("Language detection failed; defaulting to English")
        return 'en'

def translate_tweet(tweet, source_lang):
    if source_lang == 'en':
        return tweet
    try:
        translator = GoogleTranslator(source=source_lang, target='en')
        return translator.translate(tweet)
    except Exception as e:
        logging.error(f"Translation error: {e}")
        print(f"Translation error: {e}")
        return tweet

def extract_locations(tweet, language):
    nlp = nlp_en if language == 'en' else nlp_multi
    try:
        doc = nlp(tweet)
        locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"] and (' ' not in ent.text or ent.text in city_aliases.values())]
    except Exception as e:
        logging.error(f"spaCy processing error: {e}")
        locations = []

    for alias, city in city_aliases.items():
        if alias.lower() in tweet.lower():
            locations.append(city)

    patterns = [
        r"\b\w+(?: city| town| village| state| province| country)\b",
        r"\b\w+(?: mountain| river| lake| ocean| sea)\b",
        r"\b[A-Z][a-z]+, [A-Z]{2}\b",
        r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b",
        r"\b(?:Eiffel Tower|Statue of Liberty|Big Ben|Colosseum|Sydney Opera House|Taj Mahal)\b"
    ]

    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for pattern in compiled_patterns:
        regex_locations = pattern.findall(tweet)
        locations.extend(regex_locations)

    return list(set(locations))

def calculate_severity(tweet, sentiment_scores, is_disaster, category):
    severity = 0.0
    if is_disaster:
        severity += 0.4
    compound_score = sentiment_scores['compound']
    if compound_score <= -0.05:
        severity += 0.3
    elif compound_score >= 0.05:
        severity -= 0.1
    else:
        severity += 0.1

    category_mappings = {
        "tsunami warning": "tsunami",
        "flash flood warning": "flash flood",
        "severe thunderstorm warning": "thunderstorm",
        "tornado warning": "tornado",
        "hurricane warning": "hurricane",
        "blizzard warning": "blizzard",
        "ice storm warning": "ice storm",
        "flood warning": "flood",
        "drought warning": "drought",
        "heat wave warning": "heatwave",
        "cold wave warning": "cold wave",
        "windstorm warning": "windstorm",
        "smog warning": "smog",
        "fog warning": "fog",
        "extreme weather warning": "storm",
        "disaster warning": "storm",
        "storm surge warning": "hurricane",
        "wildland fire": "wildfire",
        "forest fire": "wildfire",
        "brush fire": "wildfire",
        "avalanche": "snow avalanche",
        "cyclone": "hurricane",
        "storm": "hurricane"
    }

    category_lower = category.lower()
    if category_lower in category_mappings:
        category_lower = category_mappings[category_lower]

    severity += severity_weights.get(category_lower, 0.1)
    keyword_count = sum(1 for keywords in disaster_keywords.values() for word in keywords if word.lower() in tweet.lower())
    severity += min(keyword_count * 0.05, 0.2)
    return round(severity, 2)

def predict_tweet(tweet):
    try:
        lr_model = pickle.load(open('lr_model.pkl', 'rb'))
        vectorizer = pickle.load(open('vectorizer.pkl', 'rb'))
        st = pickle.load(open('scaler.pkl', 'rb'))
    except FileNotFoundError as e:
        logging.error(f"Model file not found: {e}")
        print(f"Error: Model file not found - {e}")
        return None
    except pickle.UnpicklingError as e:
        logging.error(f"Failed to unpickle model: {e}")
        print(f"Error: Failed to unpickle model - {e}")
        return None

    cleaned_tweet = clean_tweet(tweet)
    language = detect_language(tweet)
    translated_tweet = translate_tweet(tweet, language)

    try:
        tweet_vectorized = vectorizer.transform([translated_tweet])
        tweet_scaled = st.transform(tweet_vectorized.toarray())
    except Exception as e:
        logging.error(f"Vectorization/scaling error: {e}")
        print(f"Error in vectorization/scaling: {e}")
        return None

    locations = extract_locations(tweet, language)

    try:
        prediction = lr_model.predict(tweet_scaled)[0]
        is_disaster = 1 if prediction == 'Disaster' else 0
        confidence = lr_model.predict_proba(tweet_scaled)[0].max() if hasattr(lr_model, 'predict_proba') else None
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        print(f"Error in prediction: {e}")
        is_disaster = 0
        confidence = None

    category = 'Unknown Category'
    base_disasters = [
        "earthquake", "flood", "drought", "landslide", "wildfire", "hurricane",
        "tornado", "tsunami", "volcanic eruption", "heatwave", "cloud burst",
        "blizzard", "ice storm", "dust storm", "fog", "snow avalanche", "flash flood",
        "water pollution", "oil spill", "chemical spill", "nuclear accident",
        "pandemic", "power outage", "building collapse", "plane crash", "train crash",
        "ship sinking", "economic crisis", "food shortage", "water shortage",
        "terrorist attack", "cyber attack", "heavy rainfall", "low pressure",
        "thunderstorm", "gale", "hail storm", "sandstorm", "smog", "heat stress",
        "cold wave", "windstorm", "winter storm", "tropical storm", "ice jam",
        "fog bank", "mudflow", "rockfall"
    ]

    for keyword in base_disasters:
        words = disaster_keywords.get(keyword, [])
        for word in words:
            if word.lower() in translated_tweet.lower():
                category = keyword.capitalize()
                break
        if category != 'Unknown Category':
            break

    if category == 'Unknown Category':
        for keyword, words in disaster_keywords.items():
            for word in words:
                if word.lower() in translated_tweet.lower():
                    category = keyword.capitalize()
                    break
            if category != 'Unknown Category':
                break

    sentiment_scores = sia.polarity_scores(translated_tweet)
    sentiment = 'Positive' if sentiment_scores['compound'] >= 0.05 else 'Negative' if sentiment_scores['compound'] <= -0.05 else 'Neutral'

    severity_score = calculate_severity(translated_tweet, sentiment_scores, is_disaster, category)

    return {
        'tweet': tweet,
        'cleaned_tweet': cleaned_tweet,
        'translated_tweet': translated_tweet if language != 'en' else None,
        'language': language,
        'is_disaster': is_disaster,
        'confidence': float(round(confidence, 2)) if confidence is not None else None,
        'location': locations[0] if locations else 'Unknown',
        'category': category,
        'sentiment': sentiment,
        'severity_score': severity_score
    }
# -------- LOGIC FROM FINAL FUNCTION ENDS HERE --------

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dash.html')

@app.route('/browse')
def browse():
    return render_template('index.html')

@app.route('/details')
def details():
    return render_template('dash.html')

@app.route('/streams')
def streams():
    return render_template('index.html')

@app.route('/profile')
def profile():
    return render_template('index.html')

@app.route('/more_categories')
def more_categories():
    return render_template('index.html')  # Or create a dedicated template for more categories

@app.route('/login')
def login():
    return render_template('login.html')  # Or create a dedicated login template

@app.route('/analyze', methods=['POST'])
def analyze():
    tweet = request.form.get('tweet') or (request.json.get('tweet') if request.is_json else None)
    if not tweet:
        return jsonify({'error': 'No tweet provided.'}), 400
    try:
        result = predict_tweet(tweet)
        if not result:
            return jsonify({'error': 'Prediction failed.'}), 500
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in /analyze: {e}")
        return jsonify({'error': 'An error occurred during tweet analysis.'}), 500

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                tweet = line.strip()
                if tweet:
                    res = predict_tweet(tweet)
                    if res:
                        results.append(res)
        output = io.StringIO()
        writer = csv.writer(output)
        header = ["Tweet", "Cleaned Tweet", "Translated Tweet", "Language", "Is Disaster", "Confidence", "Location", "Category", "Sentiment", "Severity Score"]
        writer.writerow(header)
        for res in results:
            writer.writerow([
                res.get('tweet', ''),
                res.get('cleaned_tweet', ''),
                res.get('translated_tweet', ''),
                res.get('language', ''),
                'Yes' if res.get('is_disaster') else 'No',
                f"{(res.get('confidence', 0) * 100):.2f}%" if res.get('confidence') is not None else '',
                res.get('location', ''),
                res.get('category', ''),
                res.get('sentiment', ''),
                res.get('severity_score', '')
            ])
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=tweet_analysis_results.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        return jsonify({'error': 'File processing failed.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
