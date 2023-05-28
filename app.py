from flask import Flask, redirect, request, render_template
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Cargar las variables de entorno desde el archivo .env
load_dotenv()
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

# Crear una instancia de Flask
app = Flask(__name__)

# Configurar la autenticación de Spotify
auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=["playlist-modify-private", "playlist-modify-public"], cache_path='.spotifycache-username')
sp = spotipy.Spotify(auth_manager=auth_manager)

# Definir la ruta de inicio
@app.route('/')
def index():
    # Si el usuario no ha iniciado sesión, redirigirlo a la página de autenticación de Spotify
    if not auth_manager.get_cached_token():
        return redirect(auth_manager.get_authorize_url())
    
    # Si el usuario ha iniciado sesión, cargar la plantilla HTML index.html
    return render_template('index.html')

# Definir la ruta de callback
@app.route('/callback')
def callback():
    # Obtener el código de autorización de Spotify
    code = request.args.get('code')
    
    # Intercambiar el código de autorización por un token de acceso
    auth_manager.get_access_token(code)
    
    # Redirigir al usuario a la página de inicio
    return redirect('/')

@app.route('/generate_playlist', methods=['POST'])
def playlist():
    # Obtener las canciones ingresadas por el usuario
    song_names = request.form.getlist('song_name')
    
    # Verificar si se proporcionó al menos una canción
    if not any(song_names):
        return "Ingrese al menos una canción"
    
    # Buscar las canciones en Spotify
    track_uris = []
    for song_name in song_names:
        if song_name:
            results = sp.search(q=song_name, type='track')
            items = results['tracks']['items']
            if len(items) > 0:
                track_uris.append(items[0]['uri'])

    if len(track_uris) > 1:
        results = sp.recommendations(seed_tracks=track_uris, limit=20)
        track_uris += [track['uri'] for track in results['tracks']]
        playlist_name = f"Playlist generada a partir de {len(song_names)} canciones"
        playlist = sp.user_playlist_create(user=sp.me()['id'], name=playlist_name, public=False, collaborative=False, description='')
        sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)
        playlist_url = playlist['external_urls']['spotify']
        return render_template('playlist.html', playlist_url=playlist_url)
    else:
        return "Ingrese al menos dos canciones"

if __name__ == '__main__':
    app.run(port=8080, debug=False, host='0.0.0.0')
