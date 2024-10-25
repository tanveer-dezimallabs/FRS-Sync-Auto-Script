import requests
import shutil
import os

def process_images(image_path, url_create_card, url_upload_face, headers, watchlist_name, watchlist_name_to_id, comment):
    if image_path.lower().endswith(('.png', '.jpg', '.jpeg')):  
        filename_without_extension = image_path.split('.')[0]
        watchlist_id = watchlist_name_to_id.get(watchlist_name, 2)  # Default to 2 if watchlist_name not found
        payload = {
            "active": True,
            "name": filename_without_extension,
            "comment": comment,
            "watch_lists": [watchlist_id],
            "meta": {}
        }
        
        response = requests.post(url_create_card, json=payload, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            card_id = response.json().get('id')
            
            with open(image_path, 'rb') as img:
                files = {'source_photo': img}
                data = {'card': card_id}
                
                response = requests.post(url_upload_face, headers=headers, data=data, files=files)
                
                if response.status_code == 200 or response.status_code == 201:
                    print(f"Image {filename_without_extension} uploaded successfully")
                else:
                    print(f"Failed to upload image for {filename_without_extension}. Status code: {response.status_code}")
        else:
            print(f"Failed to create card for {filename_without_extension}. Status code: {response.status_code}")


def download_image(url, path):
    retval = False
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            retval = True  
    except Exception as e:
        print(e)
    return retval

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"File {file_path} deleted successfully.")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
