from pytube import YouTube, Playlist, Search
from moviepy.editor import *
from mutagen.mp3 import MP3
from mutagen.id3 import APIC, error
import os
import argparse
import mutagen
import requests


API_KEY = "acca20b52d107113d1a95a779a59c151"

#funcion que obtiene y agrega los metadatos al archivo mp3
def setMetadata(audioFile, title=None, artist=None):

    try:
        # Hace una peticion a la API de Last.fm de la cancion
        response = requests.get(f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={API_KEY}&artist={artist}&track={title}&format=json")

    except: 
        print("No se puedieron obtener los metadatos, improvisando metadatos de Youtube ...")
    
    else: 

        # Obtiene la informacion de la cancion en last.fm
        song_info = response.json()['track']
        print(f"Obteniendo metadatos desde: {song_info['url']}")
        title = song_info['name']
        artist = song_info['artist']

        try:
            album = song_info['album']['title']
        except KeyError:
            print("No se pudo obtener el cover")
            album = "Desconocido"
        else:
            coverimg = song_info['album']['image'][1]['#text']

            #Descarga el cover del album
            cover_response = requests.get(coverimg)
            with open("cover.jpg", "wb") as f:
                f.write(cover_response.content)
            
            #Pone el cover del album en los metadatos
            with open("cover.jpg" , "rb") as r:
                cover = r.read()
            audio = MP3(audioFile)
            try:
                # Add cover image to the ID3 tags
                
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc=u'Cover',
                    data=cover
                ))
            except: 
                print("Error al poner cover a la cancion")

        #Pone el nombre del album en los metadatos
        song = mutagen.File(audioFile, easy=True)
        song['album'] = album
        song.save()

    #Pone el artista y el titulo en los metadatos
    song = mutagen.File(audioFile, easy=True)
    song['artist'] = artist['name']
    song['title'] = title
    song.save()
        

# Funcion que descarga y convierte un video de YoutubeZ
def download(vid, song_title, song_author):

    special_chars = ["'",",","."]

    #Asigna el titulo y el artista si el usuario los puso por separado
    if song_title is not None and song_author is not None:
        title = song_title
        author = song_author
    else:
        title = vid.title
        author = vid.author
    
    #Descarga el video
    print(f"Descargando: {vid.title} ...")
    vid.streams.filter(progressive=True, file_extension='mp4').first().download()

    # Formatea el titulo de las canciones quitando caracteres especiales
    print(f"Convirtiendo a mp3 ... ")
    for char in special_chars:
        title = vid.title.replace(char, "")
    video_path = vid.title + ".mp4"
    audio_path = vid.title + ".mp3"

    # Covierte a mp3 
    video_file = VideoFileClip(video_path)
    audio_file = video_file.audio
    audio_file.write_audiofile(audio_path)
    video_file.close()
    audio_file.close()

    #Agrega metadatos al mp3 y elimina el video
    print(f"Obteniendo metadatos ...")
    setMetadata(audio_path, title, author)
    os.remove(video_path)

    print(f"{title} se ha descaragado y convertido exitosamente")


parser = argparse.ArgumentParser()
parser.add_argument('option',type=str, help="Descargar Playlist:p \nDescargar Video:v\nBuscar video:s")
parser.add_argument('--linksearch',type=str, help="Link del video o playlist. String de busqueda")
parser.add_argument('--search', type=str, help="Busqueda de Youtube")
parser.add_argument('--title', type=str, help="Titulo de la cancion")
parser.add_argument('--artist', type=str, help="Artista de la cancion")
request = parser.parse_args()

# -------------------------------- Descargar Playlists ----------------------------------------
if request.option == 'p':

    try:
        #Obtiene la playlist
        pl = Playlist(request.linksearch)
    except:
        print("El link pertence a una playlist o no se encontro la playlist o la playlist es privada")
    else:
        for video in pl.videos:
            download(video)
        print("Todos los videos se descargaron exitosamente")

# -------------------------------- Descargar Video ----------------------------------------
elif request.option == 'v':

    if request.title and request.artist is not None:
        title = request.title
        artist = request.artist
    else:
        title, artist = None, None

    try:
        #Obtiene el video
        vid = YouTube(request.linksearch)
    except:
        print("El link no pertenece a un video o no se encontro el video")
    else:
        download(vid, title, artist)

# -------------------------------- Buscar y Descargar video ----------------------------------------
elif request.option == 's':

    if request.search is not None:
        search = Search(request.search)
    elif request.title and request.artist is not None:
        search = Search(request.title + " " + request.artist)
        title = request.title
        artist = request.artist
    index = 1

    print(f"Se encontraron {len(search.results)} resultados: \n")
    for result in search.results:
        print(f"{index}.- {result.title}   Canal: {result.author}")
        index += 1

    opcion = int(input("\nElija el video que quiera descargar y convertir: "))
    download(search.results[opcion-1], title, artist)

# -------------------------------- Error ----------------------------------------
else: 
    print("Parametros no reconocidos")