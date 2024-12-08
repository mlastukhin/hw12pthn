from flask import Flask, render_template, request, redirect, url_for
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

ACCUMULATE_API_KEY = os.getenv("ACCUWEATHER_TOKEN")

def fetch_location_key(city_name):
    try:
        search_url = (
            f"http://dataservice.accuweather.com/locations/v1/cities/search"
            f"?apikey={ACCUMULATE_API_KEY}&q={city_name}&language=ru-ru"
        )
        response = requests.get(search_url)
        response.raise_for_status()
        locations = response.json()
        if locations:
            return locations[0].get('Key')
    except requests.RequestException as error:
        print(f"Ошибка при получении ключа локации: {error}")
    return None

def fetch_current_weather(location_key):
    try:
        weather_url = (
            f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
            f"?apikey={ACCUMULATE_API_KEY}&language=ru-ru&details=true"
        )
        response = requests.get(weather_url)
        response.raise_for_status()
        weather_info = response.json()
        if weather_info:
            weather = weather_info[0]
            return {
                "temperature": weather['Temperature']['Metric']['Value'],
                "humidity": weather['RelativeHumidity'],
                "wind_speed": weather['Wind']['Speed']['Metric']['Value'],
                "precipitation": weather['HasPrecipitation'],
                "description": weather['WeatherText']
            }
    except requests.RequestException as error:
        print(f"Ошибка при получении погодных условий: {error}")
    return None

def retrieve_weather_data(city):
    location_key = fetch_location_key(city)
    if location_key:
        weather_data = fetch_current_weather(location_key)
        if weather_data:
            return {
                "city": city,
                **weather_data
            }
    return None

def evaluate_weather_conditions(weather_data, user_pref):
    unfavorable_conditions = []
    temp = weather_data['temperature']
    humidity = weather_data['humidity']
    
    if user_pref == 'southern':
        if temp < 15 or temp > 30:
            unfavorable_conditions.append('температура')
        if humidity > 80:
            unfavorable_conditions.append('влажность')
    elif user_pref == 'northern':
        if temp < -10 or temp > 20:
            unfavorable_conditions.append('температура')
        if humidity > 60:
            unfavorable_conditions.append('влажность')
    
    return unfavorable_conditions if unfavorable_conditions else None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check_weather', methods=['POST'])
def check_weather():
    start_city = request.form.get('start_city')
    end_city = request.form.get('end_city')
    preference = request.form.get('preference')
    
    start_weather = retrieve_weather_data(start_city)
    end_weather = retrieve_weather_data(end_city)
    
    if not start_weather or not end_weather:
        return redirect(url_for('home'))
    
    start_unfavorable = evaluate_weather_conditions(start_weather, preference)
    end_unfavorable = evaluate_weather_conditions(end_weather, preference)
    
    return render_template(
        'result.html',
        start_weather=start_weather,
        end_weather=end_weather,
        start_unfavorable=start_unfavorable,
        end_unfavorable=end_unfavorable
    )

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
