# much code guided from https://www.thepythoncode.com/article/using-youtube-api-in-python#Searching_by_Keyword

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import urllib.parse as p
import re
import os
import pickle

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def youtube_authenticate():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "credentials.json"
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build(api_service_name, api_version, credentials=creds)

def get_video_id_by_url(url):
    """
    Return the Video ID from the video `url`
    """
    # split URL parts
    parsed_url = p.urlparse(url)
    # get the video ID by parsing the query of the URL
    video_id = p.parse_qs(parsed_url.query).get("v")
    if video_id:
        return video_id[0]
    else:
        raise Exception(f"Wasn't able to parse video URL: {url}")

def get_playlist_id_by_url(url):
    """
    Return the Video ID from the video `url`
    """
    # split URL parts
    parsed_url = p.urlparse(url)
    # get the video ID by parsing the query of the URL
    list_id = p.parse_qs(parsed_url.query).get("list")
    if list_id:
        return list_id[0]
    else:
        raise Exception(f"Wasn't able to parse video URL: {url}")

def get_search_id_by_url(url):
    """
    Return the Video ID from the video `url`
    """
    # split URL parts
    parsed_url = p.urlparse(url)
    # get the video ID by parsing the query of the URL
    search_id = p.parse_qs(parsed_url.query).get("search_query")
    if search_id:
        return search_id[0]
    else:
        raise Exception(f"Wasn't able to parse video URL: {url}")

def search(youtube, **kwargs):
    return youtube.search().list(
        part="snippet",
        **kwargs
    ).execute()

def parse_channel_url(url):
    """
    This function takes channel `url` to check whether it includes a
    channel ID, user ID or channel name
    """
    path = p.urlparse(url).path
    id = path.split("/")[-1]
    if "/c/" in path:
        return "c", id
    elif "/channel/" in path:
        return "channel", id
    elif "/user/" in path:
        return "user", id

def get_channel_id_by_url(youtube, url):
    """
    Returns channel ID of a given `id` and `method`
    - `method` (str): can be 'c', 'channel', 'user'
    - `id` (str): if method is 'c', then `id` is display name
        if method is 'channel', then it's channel id
        if method is 'user', then it's username
    """
    # parse the channel URL
    method, id = parse_channel_url(url)
    if method == "channel":
        # if it's a channel ID, then just return it
        return id
    elif method == "user":
        # if it's a user ID, make a request to get the channel ID
        response = get_channel_details(youtube, forUsername=id)
        items = response.get("items")
        if items:
            channel_id = items[0].get("id")
            return channel_id
    elif method == "c":
        # if it's a channel name, search for the channel using the name
        # may be inaccurate
        response = search(youtube, q=id, maxResults=1)
        items = response.get("items")
        if items:
            channel_id = items[0]["snippet"]["channelId"]
            return channel_id
    raise Exception(f"Cannot find ID:{id} with {method} method")

def get_channel_videos(youtube, **kwargs):
    return youtube.search().list(
        **kwargs
    ).execute()

def get_channel_details(youtube, **kwargs):
    return youtube.channels().list(
        part="statistics,snippet,contentDetails",
        **kwargs
    ).execute()

def playlist_parse(playlist_id):
    nextPageToken = None
    while True:
        pl_request = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=nextPageToken
        )

        pl_response = pl_request.execute()

        vid_ids = []
        for item in pl_response['items']:
            vid_ids.append(item['contentDetails']['videoId'])

        vid_request = youtube.videos().list(
            part="snippet, statistics",
            id=','.join(vid_ids)
        )

        vid_response = vid_request.execute()
        videos = []

        for item in vid_response.get('items'):
            vid_positive = int(item['statistics']['likeCount'])
            vid_negative = int(item['statistics']['dislikeCount'])

            if vid_negative == 0:
                vid_rating = vid_positive
            else:
                vid_rating = vid_positive / vid_negative

            videos.append(
                {
                    'title': item['snippet']['title'],
                    'ratio': vid_rating
                }
            )

        nextPageToken = pl_response.get('nextPageToken')

        if not nextPageToken:
            return videos

def get_video_details(youtube, **kwargs):
    return youtube.videos().list(
        part="snippet,contentDetails,statistics",
        **kwargs
    ).execute()

def get_video_ratio(video_response):
    items = video_response.get("items")[0]

    snippet = items["snippet"]
    statistics = items["statistics"]

    title = snippet['title']
    
    if "likeCount" not in statistics.keys():
        return

    like_count    = int(statistics["likeCount"])
    dislike_count = int(statistics["dislikeCount"])

    if dislike_count == 0:
        ratio = like_count
    else:
        ratio = like_count/dislike_count

    return {'title':title, "ratio":ratio}

# get URL
url = input("Input Youtube URL:")

# authenticate to YouTube API
youtube = youtube_authenticate()

if "v=" in url:
    video_id = get_video_id_by_url(url)
    response = get_video_details(youtube, id=video_id)
    info = get_video_ratio(response)
    print(f"""\
        Title: {info['title']}
        Ratings Ratio: {info['ratio']}
        
        """)
elif "list=" in url:
    playlist_id = get_playlist_id_by_url(url)
    videos = playlist_parse(playlist_id)
    videos.sort(key=lambda vid: vid['ratio'], reverse=True)
    for video in videos:
        print(f"""\
        Title: {video['title']}
        Ratings Ratio: {video['ratio']}

        """)
elif "search_query=" in url:
    search_id = get_search_id_by_url(url)
    response = search(youtube, q=search_id, maxResults = 25)
    items = response.get("items")
    videos = []
    for item in items:
        if item['id']['kind'] == "youtube#video":
            # get the video ID
            video_id = item["id"]["videoId"]
            # get the video details
            video_response = get_video_details(youtube, id=video_id)
            info = get_video_ratio(video_response)
            if info != None:
                videos.append(info)
    videos.sort(key=lambda vid: vid['ratio'], reverse=True)
    for video in videos:
        print(f"""\
        Title: {video['title']}
        Ratings Ratio: {video['ratio']}

        """)   
else:
    channel_id = get_channel_id_by_url(youtube, url)
    n_pages = 10
    videos = []
    next_page_token = None
    for i in range(n_pages):
        params = {
        'part': 'snippet',
        'q': '',
        'channelId': channel_id,
        'type': 'video',
        }
        if next_page_token:
            params['pageToken'] = next_page_token
        res = get_channel_videos(youtube, **params)
        channel_videos = res.get("items")
        for video in channel_videos:
            video_id = video["id"]["videoId"]
            # easily construct video URL by its ID
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_response = get_video_details(youtube, id=video_id)
            videos.append(get_video_ratio(video_response))
        # if there is a next page, then add it to our parameters
        # to proceed to the next page
        if "nextPageToken" in res:
            next_page_token = res["nextPageToken"]
    videos.sort(key=lambda vid: vid['ratio'], reverse=True)
    for video in videos:
        print(f"""\
        Title: {video['title']}
        Ratings Ratio: {video['ratio']}

        """)  