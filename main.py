import telebot
import requests
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from config import TOKEN, WINDY_API_KEY

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id,
                     "Привет! Отправь мне свою геолокацию для получения данных о погоде! "
                     "Если хочешь узнать больше, используй /help")


@bot.message_handler(commands=['help'])
def help_inf(message):
    bot.send_message(message.chat.id,
                     "Данный бот позволяет получить информацию о погодных условиях для твоей геолокации."
                     "Данные предоставляются в формате [время, температура, осадки, "
                     "скорость "
                     "ветра, направление ветра]. Так же прилагаются графики динамики температуры и осадков.\n"
                     "Чтобы получить данные, просто "
                     "отправь отправь боту свою геолокацию. Информация о погоде получена с сайта windy.com")


@bot.message_handler(content_types=['text'])
def lalala(message):
    bot.send_message(message.chat.id, "Чтобы получить данные о погоде, отправь свою геолокацию.")


def get_data_from_windy(loc: list[int, int]):
    data = {"lat": loc[1],
            "lon": loc[0],
            "model": "gfs",
            "parameters": ["temp", "wind", "precip"],
            # "levels": ["150h"],
            "key": WINDY_API_KEY
            }
    header = {"Content-Type": "application/json"}
    s = requests.post("https://api.windy.com/api/point-forecast/v2", json=data, headers=header)
    return s


def data_processing(data):
    weather_values = data.json()
    weather_values['ts'] = [int(i / 1000) + 25200 for i in weather_values['ts']]
    weather_values['temp-surface'] = [int(i - 273.15) for i in weather_values['temp-surface']]
    weather_values['wind_u-surface'] = np.array(weather_values['wind_u-surface'])
    weather_values['wind_v-surface'] = np.array(weather_values['wind_v-surface'])
    return weather_values


def answer(weather_values):
    wind_direction = []
    for i in range(weather_values['wind_u-surface'].size):
        if weather_values['wind_u-surface'][i] >= 0 and weather_values['wind_v-surface'][i] >= 0:
            wind_direction.append('ЮЗ')  # юго-западный
        if weather_values['wind_u-surface'][i] < 0 and weather_values['wind_v-surface'][i] >= 0:
            wind_direction.append('ЮВ')  # юго-восточный
        if weather_values['wind_u-surface'][i] >= 0 and weather_values['wind_v-surface'][i] < 0:
            wind_direction.append('СЗ')  # северо-западный
        if weather_values['wind_u-surface'][i] < 0 and weather_values['wind_v-surface'][i] < 0:
            wind_direction.append('СВ')  # северо-восточный

    wind_u = np.power(weather_values['wind_u-surface'], 2)
    wind_v = np.power(weather_values['wind_v-surface'], 2)
    wind_speed = np.power(wind_v + wind_u, 1 / 2)

    time = []
    for i in weather_values['ts']:
        time.append(datetime.utcfromtimestamp(i).strftime('%Y-%m-%d %H:%M:%S')[11:16])

    text = 'Погода на ближайшие сутки:\n\n'
    plot_time = np.array(time[:8])
    temp_surface = np.array(weather_values['temp-surface'][:8])
    precip_surface = np.array(weather_values['past3hprecip-surface'][:8])

    for i in range(9):
        text += time[i] + '  ' + str(weather_values['temp-surface'][i]) + '°C  ' + \
                str(float(weather_values['past3hprecip-surface'][i]))[:3] + 'mm  ' \
                + str(wind_speed[i])[:3] + 'm/s, ' + wind_direction[i] + '\n\n'

    plt.plot(plot_time, temp_surface, color='r')
    plt.savefig('D:/HSE/practis/tgbot2/temperature_dynamics.png', dpi=100)
    plt.clf()
    plt.ylim(ymin=0)
    plt.plot(plot_time, precip_surface, color='m')
    plt.savefig('D:/HSE/practis/tgbot2/Precipitation_dynamics.png', dpi=100)
    return text


def send_image(chat_id):
    bot.send_photo(chat_id, photo=open('D:/HSE/practis/tgbot2/temperature_dynamics.png', 'rb'),
                   caption="Динамика температуры")
    bot.send_photo(chat_id, photo=open('D:/HSE/practis/tgbot2/Precipitation_dynamics.png', 'rb'),
                   caption="Динамика осадков")


@bot.message_handler(content_types=['location'])
def location(message):
    if message.location is not None:
        loc = [message.location.longitude, message.location.latitude]
        data = get_data_from_windy(loc)
        weather_values = data_processing(data)
        text = answer(weather_values)
        bot.send_message(message.chat.id, text)
        send_image(message.chat.id)


bot.polling(none_stop=True)
