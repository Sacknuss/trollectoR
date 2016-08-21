__author__ = 'Lucky Hooker'

import config
import math
import musicbrainzngs
import mutagen
import os
import pathlib
import re

root = config.root
api_key_fanart = config.api_key_fanart

musicbrainzngs.set_useragent('TheCollector','0.0.1','anomalitaet@gmail.com')

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
    result = musicbrainzngs.search_artists(artist=name)

    for artist in result['artist-list']:

        artist_name = artist['name']
        artist_mbid = artist['id']

        if artist['ext:score'] == "100":
            artists.update({artist_mbid:artist_name})

    return artists

def get_release_group_by_name(artist_id, album):

    records = dict()
    result = musicbrainzngs.search_release_groups(arid=artist_id,release=album,strict=True)

    for release_group in result['release-group-list']:

        release_group_name = release_group['title']
        release_group_mbid = release_group['id']
        records.update({release_group_name: release_group_mbid})

    return records

def get_releases(artist_id, release_group_id):

	records = dict()
	result = musicbrainzngs.search_releases(arid=artist_id,rgid=release_group_id,strict=True)

	for release in result['release-list']:

		release_name = release['title']
		release_mbid = release['id']
		records.update({release_mbid: release_name})

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
