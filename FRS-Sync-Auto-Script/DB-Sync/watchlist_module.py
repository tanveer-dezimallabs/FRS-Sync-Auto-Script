import requests

def get_watchlists(url, headers):
    watchlists = {}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        watchlists_data = response.json().get('results', [])
        for watchlist in watchlists_data:
            watchlist_id = watchlist.get('id')
            watchlist_name = watchlist.get('name')
            watchlists[watchlist_id] = {
                'id': watchlist_id,
                'name': watchlist_name,
                'comment': watchlist.get('comment'),
                'color': watchlist.get('color'),
                'notify': watchlist.get('notify'),
                'acknowledge': watchlist.get('acknowledge'),
                'permissions': watchlist.get('permissions'),
                'camera_groups': watchlist.get('camera_groups'),
                'face_threshold': watchlist.get('face_threshold'),
                'body_threshold': watchlist.get('body_threshold'),
                'car_threshold': watchlist.get('car_threshold'),
                'ignore_events': watchlist.get('ignore_events'),
                'active': watchlist.get('active'),
                'origin': watchlist.get('origin')
            }
    except requests.RequestException as e:
        print(f"Failed to fetch watchlists from {url}. Error: {e}")
    return watchlists

def create_watchlist(url, headers, watchlist_data):
    try:
        response = requests.post(url, json=watchlist_data, headers=headers)
        response.raise_for_status()
        print(f"Watchlist '{watchlist_data['name']}' created successfully.")
        return response
    except requests.RequestException as e:
        print(f"Exception occurred while creating watchlist '{watchlist_data['name']}': {e}")
        return None
