import http.client
import json
import requests

CACHE_FILENAME = "nba.json"

def get_url(url):
    resp = requests.get(url)
    json_str = resp.text
    json_data = json.loads(json_str)
    return json_data

def open_cache():
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

FIB_CACHE = open_cache()

def get_url_with_cache(url):
    if url in FIB_CACHE:
        return FIB_CACHE[url]
    else:
        FIB_CACHE[url] = get_url(url)
        save_cache(FIB_CACHE)
        return FIB_CACHE[url]

Nba_url = "http://api.sportradar.us/nba/trial/v7/en/seasons/2022/REG/leaders.json?api_key=nrx8c9ta6wwtgnrkcyw4n22g"

nba_data = get_url_with_cache(Nba_url)

class Node(object):
    def __init__(self, data, name=None, total=None):
        self.data = data 
        self.name = name
        self.total = total
        self.children = []
    
    def add_node(self, rank, obj):
        self.children[rank] = obj