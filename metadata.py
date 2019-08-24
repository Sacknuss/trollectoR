__author__ = 'Lucky Hooker'

from art import get_cd_art
import config
import math
from math import isclose
import musicbrainzngs
from mutagen.flac import FLAC, Picture
import os
import pathlib
import pprint

root = config.root
priority = config.priority
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
    songs = []
    cd_count = 0
    album_length = 0
    track_count = 0

    dictionary = dict()
    dictionary.update({'artist': artist})
    dictionary.update({'album': album})

    for root, dirs, files in os.walk(record_dir):
        if files:
            for file in files:
                songs.append(f'{root}/{file}')
        cd_count += len(dirs)

    for song in songs:
        extension = pathlib.Path(song).suffix

        if extension == '.flac':
            track_count += 1
            metadata = FLAC(song)

            for item in metadata.items():
                if item[0] == 'tracknumber':
                    track_number = int(item[1].pop())

            min, sec  = divmod(metadata.info.length,60)
            song_length = "%d:%02d" % (min, sec)
            album_length += metadata.info.length

    dictionary.update({'album_length': album_length})
    dictionary.update({'track_count': track_count})

    return dictionary


def get_musicbrainz_artists_by_name(name):
    artists = []
    result = musicbrainzngs.search_artists(artist=name)

    for artist in result['artist-list']:
        artist_name = artist['name']
        artist_mbid = artist['id']
        artists.append({'artist_mbid': artist_mbid, 'artist_name': artist_name})

    return artists


def get_musicbrainz_release_group_by_name(artist_id, album):
    records = []
    result = musicbrainzngs.search_release_groups(arid=artist_id,release=album,strict=True)

    for release_group in result['release-group-list']:
        release_group_name = release_group['title']
        release_group_mbid = release_group['id']
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
    medium_types_arr = []

    try:
        release = musicbrainzngs.get_release_by_id(record_id, includes=['recordings', ])
        release = release['release']
    except:
        release = musicbrainzngs.get_release_by_id(record_id)

    for recording in release['medium-list']:
        try:
            medium_types_arr.append(recording['format'])
        except KeyError:
            pass

        track_count += int(recording['track-count'])
        for track in recording['track-list']:
            try:
                album_length += int(track['track_or_recording_length'])
            except:
                album_length += 0

    album_length = album_length / 1000
    # try/except for values that are optional and might not exist
    try:
        date = release['date']
    except KeyError:
        date = 'unknown'

    try:
        country = release['country']
    except KeyError:
        country = 'unknown'
    medium_types = ",".join(medium_types_arr)
    release_dict = {'date': date, 'id': release['id'], 'medium_count': release['medium-count'],
                    'medium_type': medium_types, 'country': country, 'track_count': track_count,
                    'album_length': album_length}

    return release_dict


def get_release_suggestions(artist_name, album_name):
    albums = []
    albums_count = 0
    albums_filtered = []

    translation = {'/': '-'}
    table = str.maketrans(translation)

    record = get_local_record_list(artist_name, album_name.translate(table))
    release_local = get_local_record_metadata(record['artist'], record['record_name'].translate(table),
                                              record['record_dir'])
    artists = get_musicbrainz_artists_by_name(artist_name)
    # pp.pprint(release_local)

    for artist in artists:
        name = artist['artist_name']
        mbid = artist['artist_mbid']
        release_groups = get_musicbrainz_release_group_by_name(mbid, album_name)
        # pp.pprint(release_groups)

        for release_group in release_groups:
            release_group_name = release_group['release_group_name']
            release_group_mbid = release_group['release_group_mbid']
            releases = get_musicbrainz_releases(mbid, release_group_mbid)
            get_cd_art(mbid, release_group_mbid, record['record_dir'])

            for release in releases:
                release_musicbrainz = get_musicbrainz_release(release['release_mbid'])
                if (isclose(int(release_musicbrainz['album_length']),
                            int(release_local['album_length']), rel_tol=10.0, abs_tol=0.0)
                    and release_musicbrainz['track_count'] == release_local['track_count']):
                    # pp.pprint(release_musicbrainz)
                    albums.append(release_musicbrainz)

    for i in range(len(priority)):
        country_value = i + 1
        country = priority[country_value]
        album_filter = filter(lambda x: x['country'] == country
                              and ('CD' in x['medium_type'] or x['medium_type'] == 'unknown'), albums)

        for album in album_filter:
            albums_filtered.append(album)
            albums_count =+ 1

        if albums_count > 0:
            for album in albums_filtered:
                # pp.pprint(album)
                album_id = album['id']
                return album_id

    for album_dif_country in albums:
        # pp.pprint(album)
        album_id = album_dif_country['id']
        return album_id


def set_release_metadata(artist_name, album_name, record_id):
    translation = {'/': '-'}
    table = str.maketrans(translation)

    try:
        release = musicbrainzngs.get_release_by_id(record_id, includes=['recordings', ])
        release = release['release']
    except:
        release = musicbrainzngs.get_release_by_id(record_id)

    record = get_local_record_list(artist_name, album_name.translate(table))
    artist = artist_name
    album = release['title']

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

    mediumtotal = release['medium-count']

    for i in range(1, mediumtotal + 1):

        record_dir = record['record_dir']
        if mediumtotal != 1:
            path = record_dir + f'/CD{i}/'
            art_path = record_dir + '/'
        else:
            path = record_dir + '/'
            art_path = record_dir + '/'

        try:
            pic = Picture()
            with open(f'{art_path}fanart.jpg', "rb") as f:
                pic.data = f.read()
            pic.mime = u"image/jpeg"
            pic.width = 1000
            pic.height = 1000
            pic.depth = 16 # color depth
        except:
            print('No Fan Art Available!')

        songs = os.listdir(path)

        for song in songs:
            fullpath = path + song
            extension = pathlib.Path(fullpath).suffix

            if extension == '.flac':
                metadata = FLAC(fullpath)

                for item in metadata.items():
                    if item[0] == 'tracknumber':
                        tracknumber = int(item[1].pop())

                records = filter(lambda x: int(x['position']) == i, release['medium-list'])
                for recording in records:
                    tracktotal = recording['track-count']
                    for track in recording['track-list']:
                        if int(track['number']) == tracknumber:
                            tracktitle = track['recording']['title'].translate(table)

                metadata.delete()
                metadata.clear_pictures()
                if pic:
                    metadata.add_picture(pic)
                metadata["Album"] = album
                metadata["Albumartist"] = artist
                metadata["Artist"] = artist
                metadata["Country"] = country
                metadata["Date"] = date
                metadata["Discnumber"] = str(i)
                metadata["Title"] = tracktitle
                metadata["Tracktotal"] = str(tracktotal)
                metadata["Tracknumber"] = str(tracknumber)
                metadata.save()

                print(f'Alt: {fullpath}')
                if mediumtotal != 1:
                    print(f'Neu: {path}{artist} - {album.translate(table)} - CD{i} - {tracknumber:02} - {tracktitle}.flac')
                    os.rename(fullpath, f'{path}{artist} - {album.translate(table)} - CD{i} - {tracknumber:02} - {tracktitle}.flac')
                else:
                    print(f'Neu: {path}{artist} - {album.translate(table)} - {tracknumber:02} - {tracktitle}.flac')
                    os.rename(fullpath, f'{path}{artist} - {album.translate(table)} - {tracknumber:02} - {tracktitle}.flac')
