__author__ = 'Lucky Hooker'

import config
import os
import simplejson
import urllib.request

root = config.root
api_key_fanart = config.api_key_fanart

url_artist = "http://musicbrainz-mirror.eu:5000/ws/2/artist/?query=%s&fmt=json"
url_release_group = "http://musicbrainz-mirror.eu:5000/ws/2/release-group?artist=%s&type=album&fmt=json"
user_agent = {'User-Agent': 'TheCollector/0.0.1 ( anomalitaet@gmail.com )'}


def create_cd_list():

    cd_list = []
    artists = os.listdir(root)
    artists.sort()

    for artist in artists:

        artist_dir = os.path.join(root + '/' + artist)
        records = os.listdir(artist_dir)
        records.sort()

        for record in records:

            record_dir = os.path.join(root + '/' + artist + '/' + record)
            if os.path.isdir(record_dir):
                cd_list.append([artist, record, record_dir])

    return cd_list


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


def get_artists_by_name(name):

    artists = dict()
    name = urllib.request.quote(name)
    req = urllib.request.Request(url=url_artist % name, data=None, headers=user_agent)
    handler = urllib.request.urlopen(req)
    response = handler.read()
    result = simplejson.loads(response)

    for artist in result['artists']:

        artist_name = artist['name']
        artist_mbid = artist['id']

        if artist['score'] == "100":
            artists.update({artist_mbid:artist_name})

    return artists


def get_release_group_by_name(artist_id, name):

    records = dict()
    artist_id = urllib.request.quote(artist_id)
    req = urllib.request.Request(url=url_release_group % artist_id, data=None, headers=user_agent)
    handler = urllib.request.urlopen(req)
    response = handler.read()
    result = simplejson.loads(response)

    for release_group in result['release-groups']:

        release_group_name = release_group['title']
        release_group_mbid = release_group['id']

        if name.lower() in  release_group_name.lower():

            records.update({release_group_name: release_group_mbid})

    return records


def get_cd_art(artist, album, path):

    artists = get_artists_by_name(artist)

    for artist_id, artist_name in artists.items():
        
        release_group = get_release_group_by_name(artist_id, album)
        if len(release_group) > 0:

            print("{'" + artist_name + "': '" + artist_id + "'}")
            print(release_group)

            for release_group_name, release_group_id in release_group.items():

                if not exist_cover_art(path):
                    get_cover_art(artist_id, release_group_id, path)
                if not exist_cd_art(path):
                    get_disc_art(artist_id, release_group_id, path)
