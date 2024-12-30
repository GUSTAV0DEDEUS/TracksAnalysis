import requests
import pandas as pd
import time
import os

# Função para autenticação na API do Spotify
def get_spotify_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    
    if auth_response.status_code != 200:
        raise Exception(f"Failed to authenticate. Status code: {auth_response.status_code}. Reason: {auth_response.text}")
    
    auth_response_data = auth_response.json()
    return auth_response_data['access_token']

# Função para buscar informações de uma faixa pelo track_id
def get_track_info(track_id, token):
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}. Retrying in 10 seconds...")
        time.sleep(10)
        return get_track_info(track_id, token)

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 1))
        print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        return get_track_info(track_id, token)
    
    if response.status_code != 200:
        print(f"Failed to fetch track info for {track_id}. Status code: {response.status_code}")
        return None

    return response.json()

# Função principal
def update_csv_with_release_date(csv_path, client_id, client_secret, save_every=10):
    # Autenticar na API do Spotify
    token = get_spotify_token(client_id, client_secret)

    # Verificar se já existe um CSV atualizado
    if os.path.exists('updated_tracks.csv'):
        df_updated = pd.read_csv('updated_tracks.csv')
        print("Carregando progresso anterior...")
    else:
        df_updated = pd.read_csv(csv_path)
        df_updated['release_date'] = None

    # Obter índices das músicas que ainda não têm data de lançamento
    df_to_update = df_updated[df_updated['release_date'].isnull()]

    # Iterar sobre cada linha restante para buscar a data de lançamento
    for index, row in df_to_update.iterrows():
        track_id = row['track_id']
        print(f"Fetching data for track ID: {track_id}...")

        # Buscar informações da faixa pela API
        track_info = get_track_info(track_id, token)

        if track_info and 'album' in track_info and 'release_date' in track_info['album']:
            release_date = track_info['album']['release_date']
            df_updated.at[index, 'release_date'] = release_date
            print(f"Track ID: {track_id}, Release Date: {release_date}")
        else:
            print(f"No release date found for track ID: {track_id}.")

        # Salvar progresso a cada N músicas processadas
        if (index + 1) % save_every == 0:
            df_updated.to_csv('updated_tracks.csv', index=False)
            print(f"Progress saved after {index + 1} tracks.")

    # Salvar o CSV final atualizado
    df_updated.to_csv('updated_tracks.csv', index=False)
    print("Arquivo atualizado salvo como 'updated_tracks.csv'.")

# Exemplo de uso
if __name__ == "__main__":
    # Substitua pelos seus valores de client_id e client_secret
    client_id = ''
    client_secret = ''
    
    # Caminho para o arquivo CSV com a coluna 'track_id'
    csv_path = 'cleaned_csv_file.csv'

    # Atualizar o CSV com as datas de lançamento
    update_csv_with_release_date(csv_path, client_id, client_secret)
