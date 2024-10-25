import os
from configparser import ConfigParser
from utils import process_images, download_image, delete_file
from cards_module import get_face_cards, get_face_card_attachment_central, get_face_card_attachment_local, fetch_card_details
from watchlist_module import get_watchlists, create_watchlist

config = ConfigParser()
config.read('config.ini')

# API URLs
url_create_card_central = config.get('API', 'url_create_card_central')
url_upload_face_central = config.get('API', 'url_upload_face_central')
url_create_card_local = config.get('API', 'url_create_card_local')
url_upload_face_local = config.get('API', 'url_upload_face_local')
watchlist_url_central = config.get('API', 'url_watchlists_central')
watchlist_url_local = config.get('API', 'url_watchlists_local')

# Headers
token_central = config.get('Headers', 'token_central')
token_local = config.get('Headers', 'token_local')

if __name__ == '__main__':
    loop = 1
    headers_central = {
        'Authorization': f'Token {token_central}'
    }
    headers_local = {
        'Authorization': f'Token {token_local}'
    }

    # Fetch watchlists from central and local servers
    watchlists_central = get_watchlists(watchlist_url_central, headers_central)
    watchlists_local = get_watchlists(watchlist_url_local, headers_local)

    # Create mappings of watchlist names to their corresponding IDs
    watchlist_name_to_id_central = {watchlist['name']: watchlist['id'] for watchlist in watchlists_central.values()}
    watchlist_name_to_id_local = {watchlist['name']: watchlist['id'] for watchlist in watchlists_local.values()}

    # Function to create a watchlist if it does not exist
    def ensure_watchlist_exists(watchlist_name, watchlist_data, watchlist_url, headers, watchlist_name_to_id):
        if watchlist_name not in watchlist_name_to_id:
            response = create_watchlist(watchlist_url, headers, watchlist_data)
            if response and (response.status_code == 200 or response.status_code == 201):
                new_watchlist_id = response.json().get('id')
                watchlist_name_to_id[watchlist_name] = new_watchlist_id
                return new_watchlist_id
        return watchlist_name_to_id[watchlist_name]

    while True:
        print("IN LOOP", loop)
        name_list_central, name_id_dict_central, is_fail_central = get_face_cards(url_create_card_central, headers_central, watchlist_url_central)
        name_list_local, name_id_dict_local, is_fail_local = get_face_cards(url_create_card_local, headers_local, watchlist_url_local)
        if not is_fail_central and not is_fail_local:
            name_list_central_set = set(name_list_central)
            name_list_local_set = set(name_list_local)
            name_list_only_in_central = list(name_list_central_set.difference(name_list_local_set))
            name_list_only_in_local = list(name_list_local_set.difference(name_list_central_set))

            print("Name list only in central", list(name_list_only_in_central))
            print("Name list only in local", list(name_list_only_in_local))
            
            for item in name_list_only_in_central:
                id_name = name_id_dict_central[item]
                url = get_face_card_attachment_central(url_upload_face_central, headers_central, id_name)
                if url is not None:
                    filename = url.split('/')[-1]
                    filename_Ext = filename.split('.')[-1]
                    filename_to_Save = item + '.' + filename_Ext
                    print("filename local", filename_to_Save)
                    download_image(url, filename_to_Save)

                    card_details = fetch_card_details(url_create_card_central + str(id_name) + '/', headers_central)
                    if card_details:
                        watchlist_ids = card_details.get('watch_lists', [])
                        if watchlist_ids:
                            watchlist_id = watchlist_ids[0]
                            watchlist_name = watchlists_central[watchlist_id]['name']

                            if watchlist_name:
                                watchlist_data = watchlists_central[watchlist_id]
                                watchlist_id_local = ensure_watchlist_exists(watchlist_name, watchlist_data, watchlist_url_local, headers_local, watchlist_name_to_id_local)
                                process_images(filename_to_Save, url_create_card_local, url_upload_face_local, headers_local, watchlist_name, watchlist_name_to_id_local, "Central Sync")
                    
                    delete_file(filename_to_Save)  # Delete file after upload

            for item in name_list_only_in_local:
                id_name = name_id_dict_local[item]
                url = get_face_card_attachment_local(url_upload_face_local, headers_local, id_name)
                if url is not None:
                    filename = url.split('/')[-1]
                    filename_Ext = filename.split('.')[-1]
                    filename_to_Save = item + '.' + filename_Ext

                    print("filename central", filename_to_Save)
                    download_image(url, filename_to_Save)

                    card_details = fetch_card_details(url_create_card_local + str(id_name) + '/', headers_local)
                    if card_details:
                        watchlist_ids = card_details.get('watch_lists', [])
                        if watchlist_ids:
                            watchlist_id = watchlist_ids[0]
                            watchlist_name = watchlists_local[watchlist_id]['name']

                            if watchlist_name:
                                watchlist_data = watchlists_local[watchlist_id]
                                watchlist_id_central = ensure_watchlist_exists(watchlist_name, watchlist_data, watchlist_url_central, headers_central, watchlist_name_to_id_central)
                                process_images(filename_to_Save, url_create_card_central, url_upload_face_central, headers_central, watchlist_name, watchlist_name_to_id_central, "Local Sync")
                    
                    delete_file(filename_to_Save)  # Delete file after upload

        loop += 1  # Increment the loop counter
