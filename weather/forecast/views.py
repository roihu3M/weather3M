from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseNotFound
import requests, openmeteo_requests
import datetime

import requests_cache
from retry_requests import retry
from .forms import SearchForm

# Словарь кодов погоды
wmo_to_map_icon = {
    "0": ["Clear", "Clear sky.", "01"],
    "1": ["MainlyClear", "Mainly clear sky.", "02"],
    "2": ["PartlyCloudy", "Partly cloudy sky.", "02"],
    "3": ["Overcast", "Overcast sky.", "03"],
    "45": ["Fog", "Foggy.", "50"],
    "48": ["Fog", "Depositing rime fog.", "50"],
    "51": ["Drizzle", "Light drizzle.", "10"],
    "53": ["Drizzle", "Moderate drizzle.", "09"],
    "55": ["Drizzle", "Dense drizzle.", "09"],
    "56": ["FreezingDrizzle", "Light freezing drizzle.", "09"],
    "57": ["FreezingDrizzle", "Dense freezing drizzle.", "09"],
    "61": ["Rain", "Slight rain.", "10"],
    "63": ["Rain", "Moderate rain.", "09"],
    "65": ["Rain", "Heavy rain.", "09"],
    "66": ["FreezingRain", "Light freezing rain.", "09"],
    "67": ["FreezingRain", "Heavy freezing rain.", "09"],
    "71": ["Snow", "Slight snow fall.", "13"],
    "73": ["Snow", "Moderate snow fall.", "13"],
    "75": ["Snow", "Heavy snow fall.", "13"],
    "77": ["Snow", "Snow grains falling.", "13"],
    "80": ["Rain", "Slight rain showers.", "10"],
    "81": ["Rain", "Moderate rain showers.", "09"],
    "82": ["Rain", "Violent rain showers.", "09"],
    "85": ["Snow", "Slight snow showers.", "13"],
    "86": ["Snow", "Heavy snow showers.", "13"],
    "95": ["Thunderstorm", "Thunderstorm.", "07"],
    "96": ["Thunderstorm", "Thunderstorm with slight hail.", "07"],
    "99": ["Thunderstorm", "Thunderstorm with heavy hail.", "07"],
}

def index(request):
    search_form = SearchForm()
    context = {
            "search_form": search_form
            }
    if request.method == 'POST':
        search_form = SearchForm(request.POST)
        if search_form.is_valid:
            city = request.POST["name"]
            return HttpResponseRedirect('search/?name=' + str(city))
        else:
            return HttpResponseRedirect('')
    value = request.COOKIES.get('last_search')
    if value is not None:
        context['last_search'] = value
    return render(request, 'index.html', context)

def search(request):
    #Форма поиска
    if request.method == 'POST':
        search_form = SearchForm(request.POST)
        if search_form.is_valid:
            city = request.POST["name"]
            return HttpResponseRedirect('search/?name=' + str(city))
    else:
        search_form = SearchForm()
   
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    #Находим координаты города
    city = request.GET.get('name')
    get_city = 'https://geocoding-api.open-meteo.com/v1/search?name=' + str(city) + '&count=1&language=en&format=json'
    city_response = requests.get(get_city).json()
    if not 'results' in city_response or city == None:
        return HttpResponseNotFound("<h2>City not found. <a href='/'>Go to main page</a></h2>")
    city_data = city_response['results'][0]
    city_longitude = city_data['longitude']
    city_latitude = city_data['latitude']

    #Находим погоду по координатам
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude" : city_latitude,
        "longitude" : city_longitude,
	    "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
	    "current": ["temperature_2m", "is_day", "weather_code"],
	    "timezone": "Europe/Moscow"
    }
    responses = openmeteo.weather_api(url, params=params)
    weather_response = responses[0]

# Current values. The order of variables needs to be the same as requested.
    current = weather_response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_is_day = current.Variables(1).Value()
    current_weather_code = current.Variables(2).Value()
    current_weather = wmo_to_map_icon[str(round(current_weather_code))]

# Process daily data. The order of variables needs to be the same as requested.
    daily = weather_response.Daily()
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy().tolist()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy().tolist()
    daily_weather_code = daily.Variables(2).ValuesAsNumpy().tolist()
    forecast = []
    for i in range(0, 7):
        day_forecast = {}
        t = datetime.date.fromtimestamp(daily.Time() + i * 86400)
        day_forecast['day'] = t.strftime('%d/%m/%Y')
        day_forecast['temp_max'] = round(daily_temperature_2m_max[i])
        day_forecast['temp_min'] = round(daily_temperature_2m_min[i])
        day_forecast['weather'] = wmo_to_map_icon[str(round(daily_weather_code[i]))]
        forecast.append(day_forecast)

    context = {
        'city_name' : city,
        'country_name' : city_data['country'],
        'current_temp' : round(current_temperature_2m),
        'is_day' : current_is_day,
        'current_weather' : current_weather,
        'forecast' : forecast,
        'search_form' : search_form
    }
    response = render(request, 'search.html', context)
    response.set_cookie('last_search', request.GET.get('name'))
    return response