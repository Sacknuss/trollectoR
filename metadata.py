__author__ = 'Lucky Hooker'

from art import get_cd_art
import config
import math
import musicbrainzngs
from mutagen.flac import FLAC, Picture
import os
import pathlib
import pprint

root = config.root
musicbrainzngs.set_useragent('TheCollector','0.0.1','anomalitaet@gmail.com')
pp = pprint.PrettyPrinter(indent=10)

def get_local_artist_list(artist):
    cd_list = []
    records = os.listdir(root + '/' + artist)
    records.sort()

    for record in records:
        record_dir = os.path.join(root + '/' + artist + '/' + record)

        if os.path.isdir(record_dir):
            cd_list.append([artist, record, record_dir])

    return cd_list


def get_local_record_list(artist, record):
    cd_list = dict()
    record_name = record
    records = os.listdir(root + '/' + artist)
    records.sort()

    for record in records:
            record_dir = os.path.join(root + '/' + artist + '/' + record)

            if os.path.isdir(record_dir) and record.lower() == record_name.lower():
                    cd_list.update({'artist': artist, 'record_name': record, 'record_dir': record_dir})

    return cd_list


def get_local_record_metadata(artist, album, record_dir):
    songs = os.listdir(record_dir)
    album_length = 0
    track_count = 0

    dictionary = dict()
    dictionary.update({'artist': artist})
    dictionary.update({'album': album})

    for song in songs:
        path = record_dir + '/' + song
        extension = pathlib.Path(path).suffix

        if extension == '.flac':
            track_count += 1
            metadata = FLAC(path)

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

    dictionary.update({'album_length': album_length})
    dictionary.update({'track_count': track_count})

    return dictionary


def get_musicbrainz_artists_by_name(name):
    artists = []
    result = musicbrainzngs.search_artists(artist=name)

    for artist in result['artist-list']:
        artist_name = artist['name']
        artist_mbid = artist['id']

        if artist['ext:score'] == "100":
            artists.append({'artist_mbid': artist_mbid, 'artist_name': artist_name})

    return artists


def get_musicbrainz_release_group_by_name(artist_id, album):
    records = []
    result = musicbrainzngs.search_release_groups(arid=artist_id,release=album,strict=True)

    for release_group in result['release-group-list']:
        release_group_name = release_group['title']
        release_group_mbid = release_group['id']

        if release_group['ext:score'] == "100":
            records.append({'release_group_mbid': release_group_mbid, 'release_group_name': release_group_name})

    return records


def get_musicbrainz_releases(artist_id, release_group_id):
    releases = []
    result = musicbrainzngs.search_releases(arid=artist_id,rgid=release_group_id,strict=True)

    for release in result['release-list']:
        release_name = release['title']
        release_mbid = release['id']
        releases.append({'release_mbid': release_mbid, 'release_name': release_name})

    return releases


def get_musicbrainz_release(record_id):
    track_count = 0
    album_length = 0
    release = musicbrainzngs.get_release_by_id(record_id, includes=['recordings', ])
    release = release['release']

    for recording in release['medium-list']:
        track_count += int(recording['track-count'])

        for track in recording['track-list']:
            try:
                album_length += int(track['track_or_recording_length'])
            except:
                album_length += 0

    album_length = album_length / 1000
    min, sec = divmod(album_length, 60)
    hours, min = divmod(min, 60)
    album_length = "%d:%02d:%02d" % (hours, min, sec)

    # try/except for values that are optional and might not exist
    try:
        date = release['date']
    except KeyError:
        date = 'unknown'

    try:
        country = release['country']
    except KeyError:
        country = 'unknown'

    release_dict = {'date': date, 'id': release['id'], 'medium-count': release['medium-count'],
                    'country': country, 'track_count': track_count, 'album_length': album_length}

    return release_dict


def get_release_suggestions(artist_name, album_name):
    pp = pprint.PrettyPrinter(indent=10)
    record = get_local_record_list(artist_name, album_name)
    release_local = get_local_record_metadata(record['artist'], record['record_name'], record['record_dir'])
    artists = get_musicbrainz_artists_by_name(artist_name)

    for artist in artists:
        name = artist['artist_name']
        mbid = artist['artist_mbid']
        release_groups = get_musicbrainz_release_group_by_name(mbid, album_name)

        for release_group in release_groups:
            release_group_name = release_group['release_group_name']
            release_group_mbid = release_group['release_group_mbid']
            releases = get_musicbrainz_releases(mbid, release_group_mbid)
            get_cd_art(mbid, release_group_mbid, record['record_dir'])

            for release in releases:
                release_musicbrainz = get_musicbrainz_release(release['release_mbid'])
                if (release_musicbrainz['album_length'] == release_local['album_length'] and
                    release_musicbrainz['track_count'] == release_local['track_count']):
                    pp.pprint(release_musicbrainz)


def set_release_metadata(artist_name, album_name, record_id):
    release = musicbrainzngs.get_release_by_id(record_id, includes=['recordings', ])
    release = release['release']
    record = get_local_record_list(artist_name, album_name)
    record_dir = record['record_dir']
    songs = os.listdir(record_dir)

    artist = artist_name
    album = release['title']
    tracktotal = 0
    for recording in release['medium-list']:
        tracktotal += int(recording['track-count'])
    # try/except for values that are optional and might not exist
    try:
        date = release['date']
    except KeyError:
        date = 'unknown'
    try:
        country = release['country']
    except KeyError:
        country = 'unknown'

    tracknumber = 1
    translation = {'/': '-'}
    table = str.maketrans(translation)

    pic = Picture()
    with open(f'{record_dir}/fanart.jpg', "rb") as f:
        pic.data = f.read()
    pic.mime = u"image/jpeg"
    pic.width = 1000
    pic.height = 1000
    pic.depth = 16 # color depth

    for song in songs:
        path = record['record_dir'] + '/' + song
        extension = pathlib.Path(path).suffix

        if extension == '.flac':
            metadata = FLAC(path)

            for item in metadata.items():
                if item[0] == 'tracknumber':
                    tracknumber = int(item[1].pop())

            for recording in release['medium-list']:
                for track in recording['track-list']:
                    if int(track['number']) == tracknumber:
                        tracktitle = track['recording']['title'].translate(table)

            metadata.delete()
            metadata.add_picture(pic)
            metadata["Album"] = album
            metadata["Albumartist"] = artist
            metadata["Artist"] = artist
            metadata["Country"] = country
            metadata["Date"] = date
            metadata["Title"] = tracktitle
            metadata["Tracktotal"] = str(tracktotal)
            metadata["Tracknumber"] = str(tracknumber)
            metadata.save()

            print(f'Alt: {path}')
            print(f'Neu: {record_dir}/{artist} - {album} - {tracknumber:02} - {tracktitle}.flac')
            os.rename(path, f'{record_dir}/{artist} - {album} - {tracknumber:02} - {tracktitle}.flac')
