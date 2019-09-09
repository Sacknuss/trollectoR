__author__ = 'Lucky Hooker'

import config
import logging
import logging.config
from math import isclose
import musicbrainzngs
from mutagen.flac import FLAC, Picture
import os
import pathlib
import simplejson
import sys
import urllib.request


root = config.root
music = config.music
musicbrainzngs.set_useragent(config.app, config.version, config.contact)

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('simple')


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
        fanart_api_key = config.fanart_api_key
        url = "http://webservice.fanart.tv/v3/music/%s?api_key=%s" % (artist_id, fanart_api_key)
        result = urllib.request.urlopen(url).read()
        data = simplejson.loads(result)

        album = data['albums'][release_group_id]
        cd_arts = album['cdart']
        counter = 0

        for cover in cd_arts:
            if counter < 1:
                img_url = cover['url']
                img_url = img_url.replace("https://", "http://")
                urllib.request.urlretrieve(img_url, f'{path}/cdart.png')
                logger.info(f'CD Art downloaded: {path}/cdart.png')
            else:
                img_url = cover['url']
                img_url = img_url.replace("https://", "http://")
                urllib.request.urlretrieve(img_url, f'{path}/cdart{str(counter)}.png')
                logger.info(f'CD Art downloaded: {path}/cdart{str(counter)}.png')
            counter += 1

    except urllib.error.HTTPError as e:
        print(e.__dict__)
    except urllib.error.URLError as e:
        print(e.__dict__)


def get_cover_art(artist_id, release_group_id, path):
    try:
        fanart_api_key = config.fanart_api_key
        url = "http://webservice.fanart.tv/v3/music/%s?api_key=%s" % (artist_id, fanart_api_key)
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
                logger.info(f'Cover downloaded: {path}/fanart.jpg')
            else:
                img_url = cover['url']
                img_url = img_url.replace("https://", "http://")
                urllib.request.urlretrieve(img_url, f'{path}/fanart{str(counter)}.jpg')
                logger.info(f'Cover downloaded: {path}/fanart{str(counter)}.jpg')
            counter += 1

    except urllib.error.HTTPError as e:
        print(e.__dict__)
    except urllib.error.URLError as e:
        print(e.__dict__)


def get_cd_art(artist_id, release_group_id, path):
    if not exist_cover_art(path):
        get_cover_art(artist_id, release_group_id, path)
    if not exist_cd_art(path):
        get_disc_art(artist_id, release_group_id, path)


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

    try:
        date = release['date']
    except KeyError:
        date = 'unknown'
    try:
        country = release['country']
    except KeyError:
        country = 'unknown'

    medium_types = ",".join(medium_types_arr)
    album_length = album_length / 1000
    release_dict = {'date': date, 'id': release['id'], 'medium_count': release['medium-count'],
                    'medium_type': medium_types, 'country': country, 'track_count': track_count,
                    'album_length': album_length}

    return release_dict


def get_release_suggestions(artist_name, album_name):
    albums = []
    albums_filtered = {}
    priority = config.priority

    translation = {'/': '-'}
    table = str.maketrans(translation)

    record = get_local_record_list(artist_name, album_name.translate(table))
    release_local = get_local_record_metadata(record['artist'], record['record_name'].translate(table),
                                              record['record_dir'])
    artists = get_musicbrainz_artists_by_name(artist_name)
    logger.info(f'local release info: {release_local}')

    for artist in artists:
        name = artist['artist_name']
        mbid = artist['artist_mbid']
        logger.info(f'artist: {name}')
        release_groups = get_musicbrainz_release_group_by_name(mbid, album_name)
        logger.info(f'found {len(release_groups)} matching release group(s) on musicbrainz')

        for release_group in release_groups:
            release_group_name = release_group['release_group_name']
            release_group_mbid = release_group['release_group_mbid']
            releases = get_musicbrainz_releases(mbid, release_group_mbid)
            get_cd_art(mbid, release_group_mbid, record['record_dir'])

            for release in releases:
                release_musicbrainz = get_musicbrainz_release(release['release_mbid'])
                if (isclose(int(release_musicbrainz['album_length']),
                            int(release_local['album_length']), rel_tol=10.0, abs_tol=0.0)
                    and release_musicbrainz['track_count'] == release_local['track_count']
                    and release_musicbrainz['medium_type'] == 'CD'):
                    release_mbid = release['release_mbid']
                    country = release_musicbrainz['country']
                    logger.info(f'{release_mbid} ({country}) matches with local record')
                    albums.append(release_musicbrainz)

    for i in range(len(priority)):
        country_value = i + 1
        country = priority[country_value]
        album_filter = filter(lambda x: x['country'] == country
                              and ('CD' in x['medium_type'] or x['medium_type'] == 'unknown'), albums)

        for album in album_filter:
            albums_filtered[country_value] = album

    if len(albums_filtered) > 0:
        priority, album = next(iter(sorted(albums_filtered.items())))
        album_id = album['id']
        country = album['country']
        logger.info(f'{album_id} ({country}) was selected due to highest priority ({priority})')
        return album_id
    else:
        album = next(iter(sorted(albums)))
        album_id = album['id']
        country = album['country']
        logger.info(f'{album_id} ({country}) was selected because there are no releases for the defined countries')
        return album_id


def set_release_metadata(artist_name, album_name, record_id):
    translation = {'/': '-'}
    table = str.maketrans(translation)
    record = get_local_record_list(artist_name, album_name.translate(table))
    record_dir = record['record_dir']

    try:
        release = musicbrainzngs.get_release_by_id(record_id, includes=['recordings', ])
        release = release['release']
    except:
        release = musicbrainzngs.get_release_by_id(record_id)
    try:
        album = release['title']
    except KeyError:
        album = 'not defined'
    try:
        date = release['date']
    except KeyError:
        date = 'not defined'
    try:
        country = release['country']
    except KeyError:
        country = 'not defined'
    try:
        mediumtotal = release['medium-count']
    except KeyError:
        mediumtotal = 0

    tracknumber = 1
    for i in range(1, mediumtotal + 1):

        if mediumtotal > 1:
            base_dir = record_dir + f'/CD{i}/'
            base_dir_art = record_dir + '/'
        else:
            base_dir = record_dir + '/'
            base_dir_art = record_dir + '/'

        try:
            pic = Picture()
            with open(f'{base_dir_art}fanart.jpg', "rb") as f:
                pic.data = f.read()
            pic.mime = u"image/jpeg"
            pic.width = 1000
            pic.height = 1000
            pic.depth = 16
        except:
            logger.warning('No Fan Art Available!')

        songs = os.listdir(base_dir)
        for song in songs:
            fullpath = base_dir + song
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
                            trackid = track['recording']['id']
                            track_musicbrainz = musicbrainzngs.get_recording_by_id(trackid, includes=['artists',])
                            artist = track_musicbrainz['recording']['artist-credit-phrase']

                metadata.delete()
                metadata.clear_pictures()
                if pic:
                    metadata.add_picture(pic)
                metadata["Album"] = album
                metadata["Albumartist"] = artist_name
                metadata["Artist"] = artist_name
                metadata["Country"] = country
                metadata["Date"] = date
                metadata["Discnumber"] = str(i)
                metadata["Title"] = tracktitle
                metadata["Tracktotal"] = str(tracktotal)
                metadata["Tracknumber"] = str(tracknumber)
                metadata.save()

                logger.info(f'old name: {song}')
                if mediumtotal != 1:
                    logger.info(f'new name: {artist} - {album.translate(table)} - CD{i} - {tracknumber:02} - {tracktitle}.flac')
                    os.rename(fullpath, f'{base_dir}{artist} - {album.translate(table)} - CD{i} - {tracknumber:02} - {tracktitle}.flac')
                else:
                    logger.info(f'new name: {artist} - {album.translate(table)} - {tracknumber:02} - {tracktitle}.flac')
                    os.rename(fullpath, f'{base_dir}{artist} - {album.translate(table)} - {tracknumber:02} - {tracktitle}.flac')


for artist, albums in music.items():
    for album in albums:
        album_id = get_release_suggestions(artist, album)
        set_release_metadata(artist, album, album_id)
