import subprocess
import sys
import os
import pkg_resources
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def install_packages():
    try:
        # Upgrade pip to the latest version
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # List of required packages
        required_packages = ['spotipy']
        
        # Check currently installed packages
        installed_packages = {pkg.key for pkg in pkg_resources.working_set}
        missing_packages = [pkg for pkg in required_packages if pkg not in installed_packages]
        
        # Install missing packages
        if missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while installing packages: {e}")
        sys.exit(1)

def read_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Configs', 'config.txt')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, 'r') as file:
        lines = file.read().splitlines()
    return {
        "client_id": lines[0],
        "client_secret": lines[1],
        "redirect_uri": lines[2]
    }

def search_track(sp, track_name):
    results = sp.search(q=track_name, type='track', limit=1)
    tracks = results['tracks']['items']
    if tracks:
        return tracks[0]['uri']
    else:
        print(f"Track not found: {track_name}")
        return None

def read_song_uris():
    songs_path = os.path.join(os.path.dirname(__file__), '..', 'Configs', 'songs.txt')
    if not os.path.exists(songs_path):
        raise FileNotFoundError(f"Songs file not found: {songs_path}")
    
    uris = []
    with open(songs_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line.startswith("#"):
                if line.startswith("http"):
                    uris.append(line)
                else:
                    # Search for track URI if the line is not a URL
                    track_uri = search_track(sp, line)
                    if track_uri:
                        uris.append(track_uri)
    return uris

def create_playlist(sp, user_id, playlist_name, uris):
    try:
        # Create a new playlist, setting it to public
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
        
        # Add items to the playlist
        if uris:
            sp.playlist_add_items(playlist_id=playlist['id'], items=uris)
        else:
            print("No URIs provided for the playlist.")
        
        return playlist
    except Exception as e:
        print(f"An error occurred while creating the playlist: {e}")
        sys.exit(1)

def run_main_script(sp):
    config = read_config()
    sp_oauth = SpotifyOAuth(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        redirect_uri=config['redirect_uri'],
        scope="playlist-modify-public"
    )
    token_info = sp_oauth.get_access_token(as_dict=False)
    sp = spotipy.Spotify(auth=token_info)
    user_id = sp.current_user()['id']
    
    uris = read_song_uris()
    playlist_name = input("What should the playlist be named? ")  # Prompt for playlist name
    playlist = create_playlist(sp, user_id, playlist_name, uris)
    print(f'Playlist "{playlist["name"]}" created successfully!')
    
    # Write the playlist URL to Playlists.txt
    playlists_path = os.path.join(os.path.dirname(__file__), '..', 'Playlists.txt')
    with open(playlists_path, 'w') as playlists_file:
        playlists_file.write(f'{playlist_name}: {playlist["external_urls"]["spotify"]}\n')
    
    # Open the Playlists.txt file
    if os.path.exists(playlists_path):
        os.startfile(playlists_path)
    else:
        print("Playlists.txt file not found.")

def main():
    install_packages()
    
    # Check if 'Configs/config.txt' and 'Configs/songs.txt' exist
    config_path = os.path.join(os.path.dirname(__file__), '..', 'Configs', 'config.txt')
    songs_path = os.path.join(os.path.dirname(__file__), '..', 'Configs', 'songs.txt')
    
    if not os.path.exists(config_path) or not os.path.exists(songs_path):
        print("Configuration or songs file is missing. Please check your setup.")
        sys.exit(1)
    
    # Initialize Spotify client
    config = read_config()
    sp_oauth = SpotifyOAuth(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        redirect_uri=config['redirect_uri'],
        scope="playlist-modify-public"
    )
    token_info = sp_oauth.get_access_token(as_dict=False)
    sp = spotipy.Spotify(auth=token_info)
    
    run_main_script(sp)
    
    # Ask user if they are done
    done = input("Are you done with the song list? (yes/no): ").strip().lower()
    if done == 'yes':
        print("Playlist created and saved.")
        # Open the Playlists.txt file
        playlists_path = os.path.join(os.path.dirname(__file__), '..', 'Playlists.txt')
        if os.path.exists(playlists_path):
            os.startfile(playlists_path)
        else:
            print("Playlists.txt file not found.")
    else:
        print("You chose not to finalize the playlist creation.")

if __name__ == "__main__":
    main()
