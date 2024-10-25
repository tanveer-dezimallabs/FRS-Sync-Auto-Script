import requests
from watchlist_module import get_watchlists

def fetch_cards(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(e)
        return None

def get_face_card_attachment(url, headers, card_id):
    next_url = url
    while next_url:
        response_json = fetch_cards(next_url, headers)
        if response_json:
            next_url = response_json.get('next_page')
            results = response_json.get('results', [])
            for item in results:
                if item.get('card') == card_id:
                    return item.get('source_photo')
    return None

def get_face_card_attachment_central(central_url, headers, card_id):
    return get_face_card_attachment(central_url, headers, card_id)

def get_face_card_attachment_local(local_url, headers, card_id):
    return get_face_card_attachment(local_url, headers, card_id)

def get_face_cards(host_url, headers, watchlist_url):
    name_list = []
    name_id_dict = {}
    watchlist_dict = get_watchlists(watchlist_url, headers)
    next_url = host_url

    while next_url:
        response_json = fetch_cards(next_url, headers)
        if response_json:
            next_url = response_json.get('next_page')
            results = response_json.get('results', [])
            for item in results:
                name = item.get('name')
                id1 = item.get('id')
                watchlist_ids = item.get('watch_lists', [])
                watchlist_id1 = watchlist_ids[0] if watchlist_ids else None

                if name and id1:
                    name_list.append(name)
                    name_id_dict[name] = id1

                    # Print card name and corresponding watchlist name
                    if watchlist_id1 in watchlist_dict:
                        watchlist_name = watchlist_dict[watchlist_id1].get('name', 'Unknown Watchlist')
                    else:
                        watchlist_name = 'Unknown Watchlist'
                    
                    #print(f"Card: {name}, WID: {watchlist_id1} , Watchlist: {watchlist_name}, URL: {watchlist_url}")

        else:
            next_url = None

    return name_list, name_id_dict, bool(next_url)

def fetch_card_details(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(e)
        return None
