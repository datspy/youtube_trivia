import os
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv() 

API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build("youtube", "v3", developerKey=API_KEY)


def get_channel_id(vid):

    try:
        request = youtube.videos().list(part="statistics,snippet",id=vid)
        response = request.execute()
        channel_id = response['items'][0]['snippet']['channelId']
        return channel_id
    except:
        return False


def get_all_video_ids(channel_id):
    """Fetch all video IDs from a given channel."""   
    
    video_ids = []
    next_page_token = None
    
    while True:
        request = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=50,  # Max limit per request
            order="date",
            type="video",
            pageToken=next_page_token
        )
        response = request.execute()

        # Extract video IDs
        for item in response.get("items", []):
            video_ids.append(item["id"]["videoId"])
        
        # Check if there are more pages
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
    
    return video_ids

def get_video_stats(video_ids):
    """Fetch statistics for a list of video IDs."""    

    stats = {}
    for i in range(0, len(video_ids), 50):  # API allows max 50 videos per request
        request = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids[i:i+50])
        )
        response = request.execute()

        for item in response.get("items", []):
            video_id = item["id"]
            statistics = item["statistics"]
            snippet = item["snippet"]
            stats[video_id] = {
                "Title": snippet.get("title", "N/A"),
                "PublishedDate": snippet.get("publishedAt", "N/A"),                
                "viewCount": statistics.get("viewCount", "N/A"),
                "likeCount": statistics.get("likeCount", "N/A"),
                "commentCount": statistics.get("commentCount", "N/A"),
                "favoriteCount": statistics.get("favoriteCount", "N/A")
            }
    
    return stats


def get_trivia(stats):

    sort_order = ['12am - 6am','6am - 12pm','12pm - 6pm','6pm - 12am']
    metrics = ['engagement_score','viewCount','likeCount','commentCount']
    trivia_dict = {}
    videos_list = []
    sixty_days_date = datetime.now().date()- timedelta(days = 60)
    

    df = pd.DataFrame.from_dict(stats)
    temp = df.transpose()

    ### Column Transformations
    stats_df = temp.reset_index().rename(columns={'index':'VideoId'})
    stats_df['PublishedDateTime']=pd.to_datetime(stats_df['PublishedDate']).dt.tz_localize(None)
    stats_df['PublishedDate']=pd.to_datetime(stats_df['PublishedDate']).dt.date
    stats_df['PublishedHour']=pd.to_datetime(stats_df['PublishedDateTime']).dt.hour
    stats_df['viewCount']=stats_df['viewCount'].replace("N/A",0).astype("uint32")
    stats_df['likeCount']=stats_df['likeCount'].replace("N/A",0).astype("uint32")
    stats_df['commentCount']=stats_df['commentCount'].replace("N/A",0).astype("uint32")
    stats_df['comment_like_ratio']=np.divide(stats_df['commentCount'],stats_df['likeCount'])
    stats_df['like_view_ratio']=np.divide(stats_df['likeCount'],stats_df['viewCount'])
    stats_df['engagement_score']=stats_df[['viewCount','likeCount','commentCount']].apply(lambda x: 0 if x['viewCount']==0 else round(((x['likeCount']+x['commentCount'])/x['viewCount'])*100,2), axis=1)
    stats_df['PublishedHourBin'] = pd.cut(stats_df['PublishedHour'],
                                          bins=[0,6,12,18,24],
                                          include_lowest=True,
                                          labels=['12am - 6am','6am - 12pm','12pm - 6pm','6pm - 12am'])
    
    videos_by_time = pd.DataFrame(stats_df['PublishedHourBin'].value_counts()).reset_index()
    videos_by_time.columns=['PublishedHourBin', 'counts']
    videos_by_time.index = pd.CategoricalIndex(videos_by_time['PublishedHourBin'],categories=sort_order,ordered=True)
    videos_by_time = videos_by_time.sort_index().reset_index(drop=True)
    videos_by_time_list = videos_by_time.values.tolist()
    
    for metric in metrics:
        trivia_dict[metric] = stats_df.sort_values(by=[metric], ascending=False).head(1).to_dict('records')

    ### Channel Stats
    total_videos = len(stats_df)
    sixty_day_videos = len(stats_df[stats_df['PublishedDate']>sixty_days_date])
    first_video = stats_df['PublishedDate'].min()
    last_video = stats_df['PublishedDate'].max()

    channel_stats = {"total_videos": total_videos,
                     "sixty_day_videos": sixty_day_videos,
                     "first_video": first_video,
                     "last_video": last_video,
                     }
    
    title_description = {'engagement_score': "Most Engaged Video",
                     'viewCount': "Most Viewed Video",                     
                     'likeCount': "Most Liked Video",                     
                     'commentCount': "Most Commented Video"}

    for key in trivia_dict.keys():    
        custom_txt=fr"{trivia_dict[key][0]['viewCount']:,} views | {trivia_dict[key][0]['likeCount']:,} likes | {trivia_dict[key][0]['commentCount']:,} comments"
        video_scores=fr"Engagement Score: {trivia_dict[key][0]['engagement_score']}"
        videos_list.append({"type":title_description.get(key, None),
                            "title":trivia_dict[key][0]['Title'],
                            "PublishedDate":trivia_dict[key][0]['PublishedDate'],
                            "id":trivia_dict[key][0]['VideoId'],
                            "text":custom_txt, "scores":video_scores})

    return videos_list, channel_stats, videos_by_time_list


def run_analysis(vid:str = 'Ia8s0SCrp6Q'):

    channel_id = get_channel_id(vid)
    video_ids = get_all_video_ids(channel_id)
    video_stats = get_video_stats(video_ids)
    trivia_dict = get_trivia(video_stats)

    # print(trivia_dict)
    return trivia_dict


if __name__ == "__main__":

    run_analysis()

    
