import requests
from pyparsing import Literal, SkipTo, StringEnd, Group

pat_videoid = Literal("https://www.youtube.com/watch?v=").suppress() + Group(SkipTo(StringEnd()))("video_id")

def search_youtube(api_key, search_query):
    """
    Searches YouTube for a given query and returns the top 5 matches.

    :param api_key: Your YouTube Data API key.
    :param search_query: The search term.
    :return: A list of dictionaries containing video details.
    """
    url = "https://www.googleapis.com/youtube/v3/search"

    # Parameters for the API request
    params = {
        "part": "snippet",
        "q": search_query,
        "type": "video",
        "maxResults": 5,
        "key": api_key,
    }

    # Making the request to the YouTube API
    response = requests.get(url, params=params)

    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        results = []
        for item in data.get("items", []):
            video_details = {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "published_at": item["snippet"]["publishedAt"],
                "video_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }
            results.append(video_details)
        return results
    else:
        # Handle errors from the API
        print(f"Error: {response.status_code}, {response.text}")
        return []

# Example usage
def find_renditions(title) -> str:
    # Replace 'YOUR_API_KEY' with your actual YouTube Data API key
    API_KEY = "AIzaSyD5fNw09yCaJ0pZZbxFspNipG6U5lnMOEI"

    videos = search_youtube(API_KEY, title)
    vid_ids: list[str] = []

    for idx, video in enumerate(videos):
        vid_ids.append(parse_id(video["video_url"]))
        print(f"{idx}. {video['title']} Channel: {video['channel']} URL: {video['video_url']}")

    choice = input("Enter choice [0]: ") or "0"
    return vid_ids[int(choice)] if choice != "9" else ""

def main():
    print(find_renditions("ennallu urake"))

def parse_id(url):
    parsed = pat_videoid.parse_string(url).as_dict()
    return parsed["video_id"][0]
