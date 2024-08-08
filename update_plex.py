import requests
import json
import logging
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
import pprint
import os
from plexapi.server import PlexServer

# Disable SSL warnings
disable_warnings(InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Plex server configuration
#PLEX_SERVER_URL = os.environ.get('PLEX_SERVER_URL', 'http://127.0.0.1:32400')
#PLEX_AUTH_TOKEN = os.environ.get('PLEX_AUTH_TOKEN')

PLEX_SERVER_URL = "http://127.0.0.1:32400"
PLEX_AUTH_TOKEN = "Ysxr7YE71sdLd_yjGPzX"

plex = PlexServer(PLEX_SERVER_URL, PLEX_AUTH_TOKEN)

if not PLEX_AUTH_TOKEN:
    raise ValueError("PLEX_AUTH_TOKEN environment variable is not set")


class PlexAPIError(Exception):
    """Custom exception for Plex API errors"""
    pass


class PlexLibraryManager:
    def __init__(self, server_url, auth_token):
        self.server_url = server_url
        self.auth_token = auth_token
        self.headers = {
            "Accept": "application/json",
            "X-Plex-Token": self.auth_token
        }

    def _make_request(self, url, method='GET'):
        """Make a request to the Plex API and handle potential errors"""
        try:
            # Append the token to the URL
            if '?' in url:
                url += f"&X-Plex-Token={self.auth_token}"
            else:
                url += f"?X-Plex-Token={self.auth_token}"

            if method == 'GET':
                response = requests.get(url, headers=self.headers, verify=False)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, verify=False)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes

            if not response.content:
                raise PlexAPIError("Empty response received from Plex API")

            return json.loads(response.content)
        except requests.exceptions.RequestException as e:
            if response.status_code == 401:
                raise PlexAPIError("Access denied. Please check your Plex authentication token.") from e
            else:
                raise PlexAPIError(f"Error communicating with Plex API: {str(e)}") from e
        except json.JSONDecodeError as e:
            raise PlexAPIError(f"Error decoding JSON response: {str(e)}") from e

    def get_library_sections(self):
        """Fetch all library sections from Plex server."""
        try:
            data = self._make_request(f"{self.server_url}/library/sections")
            sections = data["MediaContainer"]["Directory"]
            section_keys = [section["key"] for section in sections]

            #print("Library Sections:")
            #pprint.pprint(sections)
            print("\nSection Keys:")
            pprint.pprint(section_keys)

            return section_keys
        except KeyError as e:
            raise PlexAPIError(f"Unexpected response structure: {str(e)}") from e

    def get_media_metadata(self):
        """Fetch metadata for all media items in Plex libraries."""
        media_data = {}
        for section in self.get_library_sections():
            try:
                url = f"{self.server_url}/library/sections/{section}/all"
                data = self._make_request(url)
                items = data["MediaContainer"]["Metadata"]

                #print(f"\nItems in Section {section}:")
                #pprint.pprint(items)

                for item in items:
                    try:
                        file_path = item["Media"][0]["Part"][0]["file"]
                        #print(file_path)
                        media_id = item["ratingKey"]
                        media_data[file_path] = media_id
                    except KeyError as e:
                        print (f"Keyerror: {e}")
                        print(item)
                        media_data[item["title"]] = item["ratingKey"]

            except KeyError as e:
                logging.error(f"Error processing section {section}: {str(e)}")
                continue

        #print("\nFull Media Data:")
        #pprint.pprint(media_data)

        return media_data

    def refresh_metadata(self, directory):
        """Refresh metadata for a specific directory."""
        print(f"\nAttempting to refresh metadata for directory: {directory}")

        try:
            media_info = self.get_media_metadata()
            #print(media_info)

            matching_path = (path for path in media_info if directory in path)
            #print (f"Matching path: {list(matching_path)}")
            matching_item = next(matching_path, None)

            if not matching_item:
                logging.error(f"Directory not found in Plex library: {directory}")
                return False

            media_id = media_info[matching_item]
            print(media_id)
            print(f"Matching item found: {matching_item}")
            print(f"Media ID for refresh: {media_id}")

            refresh_url = f"{self.server_url}/library/metadata/{media_id}/refresh"
            print(f"Refresh URL: {refresh_url}")

            self._make_request(refresh_url, method='PUT')

            logging.info(f"Successfully refreshed metadata for: {directory}")
            return True
        except PlexAPIError as e:
            logging.error(f"Failed to refresh metadata for {directory}: {str(e)}")
            return False


def main():
    plex_manager = PlexLibraryManager(PLEX_SERVER_URL, PLEX_AUTH_TOKEN)
    plexmedia = plex.library.search("Fantasmas")
    print(plexmedia)
    print(plexmedia[0].refresh())
    # Example usage
    directory_to_refresh = "Fantasmas"
    #result = plex_manager.refresh_metadata(directory_to_refresh)

    #if result:
        #print(f"Metadata refresh for {directory_to_refresh} was successful.")
    #else:
        #print(f"Failed to refresh metadata for {directory_to_refresh}.")


if __name__ == "__main__":
    main()