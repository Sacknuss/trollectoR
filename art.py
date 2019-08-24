__author__ = 'Lucky Hooker'

import config
import os
import pprint
import simplejson
import urllib.request

api_key_fanart = config.api_key_fanart
pp = pprint.PrettyPrinter(indent=10)
root = config.root
user_agent = {'User-Agent': 'TheCollector/0.0.1 ( anomalitaet@gmail.com )'}

def exist_cd_art(path):
    counter = 0
    files = os.listdir(path)

    for file in files:
        if 'cdart' in file:
            counter += 1

    if counter > 0:
        return True
    else:
        return False


def exist_cover_art(path):
    counter = 0
    files = os.listdir(path)

    for file in files:
        if 'fanart' in file:
            counter += 1

    if counter > 0:
        return True
    else:
        return False


def get_disc_art(artist_id, release_group_id, path):
    try:
        url = "http://webservice.fanart.tv/v3/music/%s?api_key=%s" % (artist_id, api_key_fanart)
        result = urllib.request.urlopen(url).read()
        data = simplejson.loads(result)
        # pp.pprint(data['albums'])
        album = data['albums'][release_group_id]
        cd_arts = album['cdart']
        counter = 0

        for cover in cd_arts:
            if counter < 1:
                img_url = cover['url']
                img_url = img_url.replace("https://", "http://")
                urllib.request.urlretrieve(img_url, f'{path}/cdart.png')
            else:
                img_url = cover['url']
                img_url = img_url.replace("https://", "http://")
                urllib.request.urlretrieve(img_url, f'{path}/cdart{str(counter)}.png')
            counter += 1

    except urllib.error.HTTPError as e:
        print(e.__dict__)
    except urllib.error.URLError as e:
        print(e.__dict__)
    except:
        pp.pprint({'disc_art':'unavailable'})


def get_cover_art(artist_id, release_group_id, path):
    try:
        url = "http://webservice.fanart.tv/v3/music/%s?api_key=%s" % (artist_id, api_key_fanart)
        result = urllib.request.urlopen(url).read()
        data = simplejson.loads(result)
        album = data['albums'][release_group_id]

        covers = album['albumcover']
        counter = 0

        for cover in covers:
            if counter < 1:
                img_url = cover['url']
                img_url = img_url.replace("https://", "http://")
                urllib.request.urlretrieve(img_url, f'{path}/fanart.jpg')
            else:
                img_url = cover['url']
                img_url = img_url.replace("https://", "http://")
                urllib.request.urlretrieve(img_url, f'{path}/fanart{str(counter)}.jpg')
            counter += 1

    except urllib.error.HTTPError as e:
        print(e.__dict__)
    except urllib.error.URLError as e:
        print(e.__dict__)
    except:
        pp.pprint({'fanart':'unavailable'})


def get_cd_art(artist_id, release_group_id, path):
    if not exist_cover_art(path):
        get_cover_art(artist_id, release_group_id, path)
    if not exist_cd_art(path):
        get_disc_art(artist_id, release_group_id, path)
