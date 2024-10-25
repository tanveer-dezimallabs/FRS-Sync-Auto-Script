import logging
import requests
from datetime import datetime
import json

# Buffer file path
BUFFER_FILE = 'buffer.json'
# Public IP of the local machine
LOCAL_PUBLIC_IP = '16.16.230.97'

def replace_localhost_with_public_ip(url):
    if '127.0.0.1' in url:
        return url.replace('127.0.0.1', LOCAL_PUBLIC_IP)
    return url

def download_image(url):
    if not url.startswith("http"):
        logging.error(f"Invalid URL: {url}")
        return None
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download image from {url}: {e}")
        return None

def send_event_to_central(post_url, auth_token, event):
    headers = {'Authorization': f'Token {auth_token}'}
    
    # Extract necessary fields
    fullframe_url = event.get('fullframe_url', None)
    event_token = event.get('event_token', None)
    camera = event.get('camera', None)
    mf_selector = event.get('mf_selector', 'all')
    timestamp = event.get('created_date', None)
    
    # Check for missing fields
    missing_fields = []
    if not event_token:
        missing_fields.append('event_token')
    if not camera:
        missing_fields.append('camera')
    if not timestamp:
        missing_fields.append('timestamp')
    if not mf_selector:
        missing_fields.append('mf_selector')

    if missing_fields:
        logging.error(f"Missing required fields in event: {', '.join(missing_fields)}")
        return False
    
    # Validate the URL
    if fullframe_url is None or not fullframe_url.startswith("http"):
        logging.error(f"Invalid fullframe URL")
        return False

    # Replace localhost with public IP
    fullframe_url = replace_localhost_with_public_ip(fullframe_url)
    
    # Download fullframe image
    fullframe_image = download_image(fullframe_url)
    if not fullframe_image:
        logging.error(f"Fullframe image could not be downloaded")
        return False

    # Prepare the multipart/form-data payload
    files = {
        'fullframe': ('fullframe.jpg', fullframe_image, 'image/jpeg'),
        'timestamp': (None, timestamp),
        'token': (None, event_token),
        'camera': (None, str(camera)),
        'mf_selector': (None, mf_selector)
    }

    try:
        response = requests.post(post_url, headers=headers, files=files)
        response.raise_for_status()
        logging.info(f"Event has been successfully pushed to central server at {post_url}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send event to central server: {e}")
        return False

def write_event_to_file(event):
    relevant_data = {
        'fullframe_url': replace_localhost_with_public_ip(event.get('fullframe', 'N/A')),
        'event_token': event.get('event_token', 'N/A'),
        'camera': event.get('camera', 'N/A'),
        'created_date': event.get('created_date', 'N/A'),
        'mf_selector': event.get('mf_selector', 'all')
    }
    try:
        with open(BUFFER_FILE, 'a') as file:
            file.write(json.dumps(relevant_data) + "\n")
        logging.info(f"Event written to buffer")
    except Exception as e:
        logging.error(f"Failed to write event to buffer: {e}")

def read_events_from_file():
    try:
        with open(BUFFER_FILE, 'r') as file:
            events = [json.loads(line) for line in file]
        logging.info(f"Read {len(events)} events from buffer")
        return events
    except FileNotFoundError:
        logging.info("Buffer file not found")
        return []
    except Exception as e:
        logging.error(f"Failed to read events from buffer: {e}")
        return []

def clear_buffer_file():
    try:
        open(BUFFER_FILE, 'w').close()
        logging.info("Buffer file cleared")
    except Exception as e:
        logging.error(f"Failed to clear buffer file: {e}")

def check_server_connection(url, auth_token):
    headers = {'Authorization': f'Token {auth_token}'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False
