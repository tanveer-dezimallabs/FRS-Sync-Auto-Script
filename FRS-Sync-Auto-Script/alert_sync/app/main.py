import logging
import threading
import time
from flask import Blueprint, request, jsonify
from .config import get_config
from .central_server import send_event_to_central, check_server_connection, write_event_to_file, read_events_from_file, clear_buffer_file

bp = Blueprint('webhook', __name__)

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Read configuration
config = get_config()
post_url = config['API']['url_post_event_central']
get_url = config['API']['url_get_events_central']
auth_token = config['Headers']['token_central']
event_creation_token = config['Events']['creation_token']

# Cache to store processed event IDs
processed_event_ids = set()

def connectivity_check_loop(get_url, post_url, interval, auth_token):
    while True:
        if check_server_connection(get_url, auth_token):
            logging.info("Central server connection established")
            events = read_events_from_file()
            all_success = True
            for event in events:
                success = send_event_to_central(post_url, auth_token, event)
                if not success:
                    all_success = False
                    logging.info("Failed to resend some events, buffer not cleared")
                    break
            if all_success:
                clear_buffer_file()
                logging.info("Successfully resent all events from buffer")
        else:
            logging.info("Central server not reachable")
        time.sleep(interval)

@bp.route('/webhook', methods=['POST'])
def webhook():
    try:
        logging.info("Webhook endpoint hit")
        data = request.get_json()
        logging.debug(f"Received data: {data}")

        for event in data:
            event_id = event.get('id', 'N/A')
            
            # Check if event has already been processed
            if event_id in processed_event_ids:
                logging.info(f"Event with ID {event_id} has already been processed. Skipping.")
                continue
            
            created_date = event.get('created_date', 'N/A')
            camera = event.get('camera', 'N/A')
            camera_group = event.get('camera_group', 'N/A')
            thumbnail = event.get('thumbnail', 'N/A')
            fullframe_url = event.get('fullframe', 'N/A')
            matched = event.get('matched', 'N/A')
            mf_selector = 'biggest'  # You can set this value based on your requirement
            
            print(f"Created Date: {created_date}")
            print(f"Camera: {camera}")
            print(f"Camera Group: {camera_group}")
            print(f"Thumbnail: {thumbnail}")
            print(f"Fullframe: {fullframe_url}")
            print(f"Matched: {matched}")
            print(f"ID: {event_id}")
            print(f"Event Token: {event_creation_token}")
            print('-' * 40)

            # Add the event creation token to the event data
            event['event_token'] = event_creation_token
            event['mf_selector'] = mf_selector

            # Send event to central server
            if check_server_connection(get_url, auth_token):
                success = send_event_to_central(post_url, auth_token, event)
                if success:
                    processed_event_ids.add(event_id)
                else:
                    logging.error(f"Failed to send event with ID {event_id}, adding to buffer")
                    write_event_to_file(event)
            else:
                logging.info("Central server not reachable, adding event to buffer")
                write_event_to_file(event)

        return jsonify({'status': 'success', 'received_data': data})
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

# Start the connectivity check loop in a background thread
thread = threading.Thread(target=connectivity_check_loop, args=(get_url, post_url, 3, auth_token))
thread.daemon = True
thread.start()
