import os
import time
import xml.etree.ElementTree as xml
import requests
import json


class FILM:
    def __init__(self, data: dict):
        rate_request = requests.get(f'https://rating.kinopoisk.ru/{data["filmId"]}.xml').text
        self.kp_id = data['filmId']
        self.name = data['nameRu'] if data['nameEn'] == '' else data['nameEn']
        self.ru_name = data['nameRu']
        self.year = data['year'].split('-')[0] if data['type'] != 'FILM' else data['year']
        self.duration = data['filmLength']
        self.tagline = data['slogan'] if data['slogan'] is not None else '-'
        self.description = data['description']
        self.genres = [genre['genre'] for genre in data['genres']]
        self.countries = [country['country'] for country in data['countries']]
        self.age_rating = data['ratingAgeLimits']
        try:
            self.kp_rate = xml.fromstring(rate_request)[0].text
        except IndexError:
            self.kp_rate = 0
        try:
            self.imdb_rate = xml.fromstring(rate_request)[1].text
        except IndexError:
            self.imdb_rate = 0
        self.kp_url = data['webUrl']
        self.premiere = data['premiereWorld']
        self.poster = data['posterUrl']
        self.poster_preview = data['posterUrlPreview']


class SEARCH:
    def __init__(self, data: dict):
        self.kp_id = data['filmId']
        self.name = data['nameRu'] if data['nameEn'] == '' else data['nameEn']
        self.ru_name = data['nameRu']
        self.year = data['year'].split('-')[0]
        self.duration = data['filmLength']
        self.genres = [genre['genre'] for genre in data['genres']]
        self.countries = [country['country'] for country in data['countries']]
        self.kp_rate = data['rating']
        self.kp_url = f'https://www.kinopoisk.ru/film/{data["filmId"]}/'
        self.poster = data['posterUrl']
        self.poster_preview = data['posterUrlPreview']


class KP:
    def __init__(self, token):
        self.token = token
        self.headers = {"X-API-KEY": self.token}
        self.API = 'https://kinopoiskapiunofficial.tech/api/v2.1/'

    def get_film(self, film_id):
        cache = CACHE().load()
        if str(film_id) in cache:
            data = {}
            for a in cache[str(film_id)]:
                data[a] = cache[str(film_id)][a]
            return FILM(data)

        for _ in range(10):
            try:
                request = requests.get(self.API + 'films/' + str(film_id), headers=self.headers)
                request_json = json.loads(request.text)
                cache[str(film_id)] = request_json['data']
                CACHE().write(cache)
                return FILM(request_json['data'])
            except json.decoder.JSONDecodeError:
                time.sleep(0.5)
                continue

    def search(self, query):
        for _ in range(10):
            try:
                request = requests.get(self.API + 'films/search-by-keyword', headers=self.headers,
                                       params={"keyword": query, "page": 1})
                request_json = json.loads(request.text)
                output = []
                for film in request_json['films']:
                    output.append(SEARCH(film))
                return output
            except json.decoder.JSONDecodeError:
                time.sleep(0.5)
                continue

    def top500(self):
        for _ in range(10):
            try:
                request = requests.get(self.API + 'films/top?type=BEST_FILMS_LIST&page=1&listId=1',
                                       headers=self.headers
                                       )
                request_json = json.loads(request.text)
                output = []
                for film in request_json['films']:
                    output.append(SEARCH(film))
                return output
            except json.decoder.JSONDecodeError:
                time.sleep(0.5)
                continue


class CACHE:
    def __init__(self):
        self.PATH = os.path.dirname(os.path.abspath(__file__))

    def load(self) -> dict:
        try:
            with open(self.PATH + '/cache.json', 'r') as f:
                return json.loads(f.read())
        except FileNotFoundError:
            with open(self.PATH + '/cache.json', 'w') as f:
                f.write('{}')
                return {}

    def write(self, cache: dict, indent: int = 4):
        with open(self.PATH + '/cache.json', 'w') as f:
            return json.dump(cache, f, indent=indent)
