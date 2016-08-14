__author__ = 'Lucky Hooker'

import config
import math
import mutagen
import os
import pathlib
import re
import simplejson
import urllib.request

root = config.root
api_key_fanart = config.api_key_fanart

url_artist = "http://musicbrainz-mirror.eu:5000/ws/2/artist/?query=%s&fmt=json"
url_release_group = "http://musicbrainz-mirror.eu:5000/ws/2/release-group?artist=%s&type=album&fmt=json"
user_agent = {'User-Agent': 'TheCollector/0.0.1 ( anomalitaet@gmail.com )'}

def create_list_complete():

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

def create_list_artist(artist):

	cd_list = []
	records = os.listdir(root + '/' + artist)
	records.sort()

	for record in records:

		record_dir = os.path.join(root + '/' + artist + '/' + record)
		
		if os.path.isdir(record_dir):
			cd_list.append([artist, record, record_dir])

	return cd_list		

def create_list_record(artist, record):

        cd_list = []
        record_name = record
        records = os.listdir(root + '/' + artist)
        records.sort()

        for record in records:

                record_dir = os.path.join(root + '/' + artist + '/' + record)

                if os.path.isdir(record_dir) and record.lower() == record_name.lower():
                        cd_list.append([artist, record, record_dir])

        return cd_list

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

def get_release_group_by_name(artist_id, album):

    records = dict()
    artist_id = urllib.request.quote(artist_id)
    req = urllib.request.Request(url=url_release_group % artist_id, data=None, headers=user_agent)
    handler = urllib.request.urlopen(req)
    response = handler.read()
    result = simplejson.loads(response)

    for release_group in result['release-groups']:

        release_group_name = release_group['title']
        release_group_mbid = release_group['id']

        album = re.sub('[^a-zA-Z0-9\s]','',album.lower())
        release_group_name = re.sub('[^a-zA-Z0-9\s]','',release_group_name.lower())

        if album == release_group_name:
            records.update({release_group_name: release_group_mbid})

    return records

def get_record_metadata(artist, album, record_dir):

	songs = os.listdir(record_dir)
	
	album_length = 0

	dictionary = dict()	
	dictionary.update({'artist': artist})
	dictionary.update({'album': album})	

	for song in songs:

		path = record_dir + '/' + song
		extension = pathlib.Path(path).suffix

		if extension == '.flac':
			metadata = mutagen.File(path)
			
			for item in metadata.items():
				if item[0] == 'tracknumber':
					track_number = int(item[1].pop())			

			min, sec  = divmod(metadata.info.length,60)
			song_length = "%d:%02d" % (min, sec)
			dictionary.update({track_number: song_length})

			album_length += metadata.info.length
	
	min, sec = divmod(album_length, 60)
	hours, min = divmod(min, 60)
	album_length = "%d:%02d:%02d" % (hours, min, sec)
	dictionary.update({'album length': album_length})

	return dictionary
