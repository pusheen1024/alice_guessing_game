import logging
import random
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
cities = {
    'Париж': ['965417/7bb8c8bdd1b1e6a879cd',
              '965417/105715204193334014dc'],
    'Нью-йорк': ['1652229/71feccc645bd490944a2',
                 '1030494/d5b2f5278bebe7d8a736'],
    'Москва': ['1030494/eff5c97fb8e5e7f8a84f',
               '997614/74bb2eccbfa244636dae']
}
sessionStorage = dict()


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {'end_session': False}
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)


@app.route('/information')
def information():
    return render_template('information.html')


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {'first_name': None, 'game_started': False}

    elif sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'

        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_cities'] = list()
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = [{'title': 'Да', 'hide': True},
                                          {'title': 'Нет', 'hide': True}]

    else:
        res['response']['buttons'] = [{"title": "Помощь",
                                       "url": "https://canary-aquatic-handbell.glitch.me/information",
                                       "hide": False}]
        if not sessionStorage[user_id]['game_started']:
            if req['request']['text'] == 'Покажи город на карте':
                res['response']['buttons'].extend([{'title': 'Да', 'hide': True},
                                                   {'title': 'Нет', 'hide': True}])

            elif 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['guessed_cities']) == len(cities):
                    res['response']['text'] = 'Ты отгадал все города!'
                    res['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req)

            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True

            else:
                res['response']['text'] = 'Извините, не поняла ответа!'
                res['response']['buttons'].extend([{'title': 'Да', 'hide': True},
                                                   {'title': 'Нет', 'hide': True}])

        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        sessionStorage[user_id]['city'] = city
        res['response']['card'] = dict()
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'

    else:
        city = sessionStorage[user_id]['city']
        if get_city(req) == city:
            res['response']['text'] = 'Правильно! Сыграем ещё?'
            res['response']['buttons'].append({'title': 'Покажи город на карте',
                                               'url': f'https://yandex.ru/maps/?mode=search&text={city}',
                                               'hide': True})
            sessionStorage[user_id]['game_started'] = False
            sessionStorage[user_id]['guessed_cities'].append(city)
            return
        else:
            if attempt == 3:
                res['response']['text'] = f'Вы пытались. Это {city.title()}. Сыграем ещё?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'А вот и не угадал!'
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)

if __name__ == '__main__':
    app.run()