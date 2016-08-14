__author__ = 'Lucky Hooker'

import config
import metadata
import os
import simplejson
import urllib.request

root = config.root
api_key_fanart = config.api_key_fanart

url_artist = config.url_musicbrainz + 'artist/?query=%s&fmt=json'
url_release_group = config.url_musicbrainz + 'release-group?artist=%s&type=album&fmt=json'
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


def get_disc_art(artist_id, release_id, path):

    try:

        url = "http://webservice.fanart.tv/v3/music/%s?api_key=%s" % (artist_id, api_key_fanart)
        result = urllib.request.urlopen(url).read()
        data = simplejson.loads(result)
        album = data['albums'][release_id]
        cd_arts = album['cdart']
        counter = 0

        for cover in cd_arts:

            if counter < 1:
                img_url = cover['url']
                urllib.request.urlretrieve(img_url, path + '/cdart.png')
            else:
                img_url = cover['url']
                urllib.request.urlretrieve(img_url, path + '/cdart' + str(counter) + '.png')

            counter += 1

    except:

        print("No CD Art Found!")


def get_cover_art(artist_id, release_id, path):

    try:

        url = "http://webservice.fanart.tv/v3/music/%s?api_key=%s" % (artist_id, api_key_fanart)
        result = urllib.request.urlopen(url).read()
        data = simplejson.loads(result)
        album = data['albums'][release_id]
        covers = album['albumcover']
        counter = 0

        for cover in covers:

            if counter < 1:
                img_url = cover['url']
                urllib.request.urlretrieve(img_url, path + '/fanart.jpg')
            else:
                img_url = cover['url']
                urllib.request.urlretrieve(img_url, path + '/fanart' + str(counter) + '.jpg')

            counter += 1

    except:

        print("No Fan Art Found!")


def get_cd_art(artist, album, path):

    artists = metadata.get_artists_by_name(artist)

    for artist_id, artist_name in artists.items():
        
        release_group = metadata.get_release_group_by_name(artist_id, album)
        if len(release_group) > 0:

            print("{'" + artist_name + "': '" + artist_id + "'}")
            print(release_group)

            for release_group_name, release_group_id in release_group.items():

                if not exist_cover_art(path):
                    get_cover_art(artist_id, release_group_id, path)
                if not exist_cd_art(path):
                    get_disc_art(artist_id, release_group_id, path)
