import pandas as pd
import requests
import configparser
import json
import os
import tempfile
from urllib.parse import unquote

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return {
        'card_url': config['API']['url_create_card_local'],
        'face_url': config['API']['url_upload_face_local'],
        'token': config['Headers']['token_local']
    }

def create_card(config, name, comment, watch_lists, headers):
    payload = {
        "name": name,
        "comment": comment,
        "watch_lists": watch_lists.split(',') if isinstance(watch_lists, str) else watch_lists
    }
    
    response = requests.post(config['card_url'], json=payload, headers=headers)
    if response.status_code == 201:
        return response.json().get('id')
    else:
        raise Exception(f"Failed to create card: {response.text}")

def download_image(url, headers):
    """Download image from URL and save to temporary file"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Create temp file with .jpg extension
        fd, temp_path = tempfile.mkstemp(suffix='.jpg')
        with os.fdopen(fd, 'wb') as temp_file:
            temp_file.write(response.content)
        return temp_path
    except Exception as e:
        raise Exception(f"Failed to download image from {url}: {str(e)}")

def upload_face(config, card_id, photo_path, headers):
    """Upload face photo to API"""
    try:
        # If photo_path is URL, download it first
        if photo_path.startswith('http'):
            temp_path = download_image(photo_path, headers)
            try:
                return upload_local_face(config, card_id, temp_path, headers)
            finally:
                # Clean up temp file
                os.remove(temp_path)
        else:
            return upload_local_face(config, card_id, photo_path, headers)
    except Exception as e:
        raise Exception(f"Failed to upload face: {str(e)}")

def upload_local_face(config, card_id, photo_path, headers):
    """Upload local face photo file to API"""
    if not os.path.exists(photo_path):
        raise FileNotFoundError(f"Photo file not found: {photo_path}")
        
    with open(photo_path, 'rb') as photo_file:
        files = {
            'source_photo': (os.path.basename(photo_path), photo_file, 'image/jpeg')
        }
        data = {
            'card': card_id
        }
        
        # Remove Content-Type header for multipart form data
        upload_headers = {k:v for k,v in headers.items() if k != 'Content-Type'}
        
        response = requests.post(
            config['face_url'], 
            files=files, 
            data=data, 
            headers=upload_headers
        )
        if response.status_code != 201:
            raise Exception(f"Failed to upload face: {response.text}")

def process_excel():
    config = load_config()
    
    # Read Excel file
    df = pd.read_excel('dossier.xlsx')
    
    # Setup headers for API calls
    headers = {
        'Authorization': f'Token {config["token"]}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Process each row
    for index, row in df.iterrows():
        try:
            print(f"Processing record {index + 1}: {row['Dossier name']}")
            
            # Create card
            card_id = create_card(
                config=config,
                name=row['Dossier name'],
                comment=row['Comment'],
                watch_lists=row['Dossier lists'],
                headers=headers
            )
            
            # Upload face if photo URL/path exists
            if pd.notna(row['Face full frame']):
                photo_path = str(row['Face full frame']).strip()
                upload_face(
                    config=config,
                    card_id=card_id,
                    photo_path=photo_path,
                    headers=headers
                )
            
            print(f"Successfully processed {row['Dossier name']}")
            
        except Exception as e:
            print(f"Error processing row {index + 1}: {str(e)}")

if __name__ == "__main__":
    try:
        config = load_config()
        process_excel()
        print("Processing completed!")
    except Exception as e:
        print(f"Error: {str(e)}")
