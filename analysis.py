import os
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Load environment variables from .env file
load_dotenv() 

API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build("youtube", "v3", developerKey=API_KEY)


def months_between_dates(first, last):
    """
    Calculate the difference between two dates in months.
    
    Parameters:
    first: The published date of first video
    last: The published date of last video
    
    Returns:
    int: The absolute number of months between the two dates
    """
    # Convert string dates to datetime objects if they're not already
    if isinstance(first, str):
        first = datetime.strptime(first, "%Y-%m-%d")
    if isinstance(last, str):
        last = datetime.strptime(last, "%Y-%m-%d")
        
    # Calculate the difference using relativedelta
    delta = relativedelta(last, first)
    
    # Calculate total months (years * 12 + months)
    total_months = delta.years * 12 + delta.months + 1
    
    return total_months


def consistency_statement(gap, activity_months):
    """
    To calculate consistency of posting videos.
    This considers only published dates of first and last video and not current date.
    This is only to see if the channel was consistent as long as they were active.

    Parameters:
    gap: The gap in months between published date of first and last video.
    activity_months: The total months on which at least a video was published.
    """
    
    if activity_months>gap:
        diff=0
    else:
        diff = gap - activity_months

    if diff==0:
        stmt = "...Consistency?! Consistency Champion!! They have posted at least a video every month since their first video."
    if diff==1:
        stmt = "...Consistency?! Consistency Champion nonetheless!! They've only had one month without posting a video."
    elif 1<diff<5:
        stmt = fr"...Consistency?! Almost Consistent!! They have missed posting a video on {diff} different months"
    elif diff>4:
        stmt = fr"...Consistency?! Not so consistent!! They have not posted any videos for {diff} months in between their first and last video."
    
    return stmt   

def get_isosplit(s, split):
    if split in s:
        n, s = s.split(split)
    else:
        n = 0
    return n, s


def parse_isoduration(s):
        
    # Remove prefix
    s = s.split('P')[-1]
    
    # Step through letter dividers
    days, s = get_isosplit(s, 'D')
    _, s = get_isosplit(s, 'T')
    hours, s = get_isosplit(s, 'H')
    minutes, s = get_isosplit(s, 'M')
    seconds, s = get_isosplit(s, 'S')

    # Convert all to seconds
    dt = timedelta(days=int(days), hours=int(hours), minutes=int(minutes), seconds=int(seconds))
    return int(dt.total_seconds())


def get_channel_id(vid):

    try:
        request = youtube.videos().list(part="statistics,snippet",id=vid)
        response = request.execute()
        channel_id = response['items'][0]['snippet']['channelId']
        return channel_id
    except:
        return None

### Fetch video-ids for the given channel-ID
def get_all_video_ids(channel_id):    
    
    video_ids = []
    next_page_token = None
    
    try:
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
            
            for item in response.get("items", []):
                video_ids.append(item["id"]["videoId"])
            
            # Pagination
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break    
        return video_ids
    
    except:
        return None


### Fetch video-specific statistics
def get_video_stats(video_ids):      

    stats = {}
    for i in range(0, len(video_ids), 50): 
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(video_ids[i:i+50])
        )
        response = request.execute()

        for item in response.get("items", []):
            video_id = item.get("id", None)
            statistics = item.get("statistics", {})
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            stats[video_id] = {
                "Title": snippet.get("title", "N/A"),
                "PublishedDate": snippet.get("publishedAt", "N/A"),                
                "viewCount": statistics.get("viewCount", "N/A"),
                "likeCount": statistics.get("likeCount", "N/A"),
                "commentCount": statistics.get("commentCount", "N/A"),
                "favoriteCount": statistics.get("favoriteCount", "N/A"),
                "duration": content.get("duration",0)
            }
    
    return stats

### Fetch channel-specific statistics
def get_channel_stats(channel_id):    

    request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=channel_id)
    response = request.execute()
    channel = response['items'][0]

    channel_stats = {            
            'title': channel['snippet']['title'],            
            'thumbnail': channel['snippet']['thumbnails']['default']['url'],
            'country': channel['snippet'].get('country', 'Not specified'),
            'viewCount': int(channel['statistics'].get('viewCount', 0)),
            'subscriberCount': int(channel['statistics'].get('subscriberCount', 0)),
            'videoCount': int(channel['statistics'].get('videoCount', 0)),
            }
          
    return channel_stats

### Consolidating stats to send back to app
def get_trivia(vid_stats, ch_stats):

    sort_order = ['00:00 - 05:59','06:00 - 11:59','12:00 - 17:59','18:00 - 23:59']
    metrics = ['engagement_score','viewCount','like_view_ratio','comment_view_ratio']
    title_description = {'engagement_score': "Most Engaged Video",
                         'viewCount': "Most Viewed Video",
                         'like_view_ratio': "Viewers Favourite",
                         'comment_view_ratio': "Buzzing Comments Section"
                         }
    trivia_dict = {}
    videos_list = []
    sixty_days_date = datetime.now().date()- timedelta(days = 60)    

    df = pd.DataFrame.from_dict(vid_stats)
    temp = df.transpose()

    ### Column Transformations
    stats_df = temp.reset_index().rename(columns={'index':'VideoId'})
    stats_df['PublishedDateTime']=pd.to_datetime(stats_df['PublishedDate']).dt.tz_localize(None)
    stats_df['PublishedDate']=pd.to_datetime(stats_df['PublishedDate']).dt.date
    stats_df['PublishedHour']=pd.to_datetime(stats_df['PublishedDateTime']).dt.hour
    stats_df['Day']= stats_df['PublishedDate'].apply(lambda x: x.strftime('%A'))
    stats_df['viewCount']=stats_df['viewCount'].replace("N/A",0).astype("uint32")
    stats_df['likeCount']=stats_df['likeCount'].replace("N/A",0).astype("uint32")
    stats_df['commentCount']=stats_df['commentCount'].replace("N/A",0).astype("uint32")
    stats_df['comment_view_ratio']=np.divide(stats_df['commentCount'],stats_df['viewCount'])
    stats_df['like_view_ratio']=np.divide(stats_df['likeCount'],stats_df['viewCount'])
    stats_df['engagement_score']=stats_df[['viewCount','likeCount','commentCount']].apply(lambda x: 0 if x['viewCount']==0 else round(((x['likeCount']+x['commentCount'])/x['viewCount'])*100,2), axis=1)
    stats_df['duration_secs']=stats_df["duration"].apply(lambda x: parse_isoduration(x))
    stats_df['PublishedMonth']=pd.to_datetime(stats_df['PublishedDate']).dt.strftime('%b-%Y')
    stats_df['PublishedHourBin'] = pd.cut(stats_df['PublishedHour'],
                                          bins=[0,6,12,18,24],
                                          include_lowest=True,
                                          labels=['00:00 - 05:59','06:00 - 11:59','12:00 - 17:59','18:00 - 23:59'])
    
    ### Publishing Window Stats
    videos_by_time = pd.DataFrame(stats_df['PublishedHourBin'].value_counts()).reset_index()
    videos_by_time.columns=['PublishedHourBin', 'counts']
    videos_by_time.index = pd.CategoricalIndex(videos_by_time['PublishedHourBin'],categories=sort_order,ordered=True)
    videos_by_time = videos_by_time.sort_index().reset_index(drop=True)
    videos_by_time_list = videos_by_time.values.tolist()

    ### Trivia Messages
    engagement_flag = (stats_df['likeCount'].sum()==0) | (stats_df['commentCount'].sum()==0) | (len(stats_df)<4) ## To Check If Channel Has Enough Engagement        
    prcntg_incr_engmnt = round(((stats_df['engagement_score'].max()-stats_df['engagement_score'].mean())/stats_df['engagement_score'].mean())*100)
    prcntg_incr_vws = round(((stats_df['viewCount'].max()-stats_df['viewCount'].mean())/stats_df['viewCount'].mean())*100)
    likes_per_mille = round(stats_df['like_view_ratio'].max()*1000)
    comments_per_mille = round(stats_df['comment_view_ratio'].max()*1000)
    total_duration_hrs = round(stats_df["duration_secs"].sum() / 3600)
    most_likely_day = pd.DataFrame(stats_df['Day'].value_counts()).reset_index()['Day'][0]    

    trivia_description = {'engagement_score': f"This got {prcntg_incr_engmnt} % more engagement than the channel average",
                         'viewCount': f"Woah!! {prcntg_incr_vws} % more views than the channel average",
                         'like_view_ratio': f"Statistically, this video has {likes_per_mille} likes per 1K views!!",
                         'comment_view_ratio': f"This video has about {comments_per_mille} comments per 1K views!!"                         
                         }
    
    for metric in metrics:
        trivia_dict[metric] = stats_df.sort_values(by=[metric], ascending=False).head(1).to_dict('records')

    ### Channel Stats

    sixty_day_videos = len(stats_df[stats_df['PublishedDate']>sixty_days_date])
    first_video = stats_df['PublishedDate'].min()
    last_video = stats_df['PublishedDate'].max()

    gap = months_between_dates(first_video, last_video)
    active_months = stats_df['PublishedMonth'].nunique()

    consistency_msg = consistency_statement(gap, active_months)

    channel_info = {"title": ch_stats['title'],
                    "thumbnail": ch_stats['thumbnail'],
                    "country": ch_stats['country'],
                    "subscriberCount": fr"{ch_stats['subscriberCount']:,}",
                    "total_views": fr"{ch_stats['viewCount']:,}",
                    "total_videos": ch_stats['videoCount'],
                    "sixty_day_videos": sixty_day_videos,
                    "first_video": first_video,
                    "last_video": last_video,
                    "watch_days": f"It would take you {total_duration_hrs} hours to watch all the videos in this channel!! And this channel is most likely to post a video on a {most_likely_day}...",
                    "consistency_msg": f"{consistency_msg}"                    
                    }

    for key in trivia_dict.keys():    
        custom_txt=fr"{trivia_dict[key][0]['viewCount']:,} views | {trivia_dict[key][0]['likeCount']:,} likes | {trivia_dict[key][0]['commentCount']:,} comments"
        video_scores=fr"Engagement Score: {trivia_dict[key][0]['engagement_score']}"
        videos_list.append({"type":title_description.get(key, None),
                            "title":trivia_dict[key][0]['Title'],
                            "PublishedDate":trivia_dict[key][0]['PublishedDate'],
                            "id":trivia_dict[key][0]['VideoId'],
                            "text":custom_txt, 
                            "trivia_text": trivia_description.get(key, None),
                            "scores":video_scores})

    return engagement_flag, videos_list, channel_info, videos_by_time_list


def run_analysis(vid:str = 'Ia8s0SCrp6Q'):

    ### video-id gets passed from app
    ### The default value is to test analysis without running app.py

    channel_id = get_channel_id(vid)

    if channel_id:
        video_ids = get_all_video_ids(channel_id)
        if video_ids:
            video_stats = get_video_stats(video_ids)
        else:
            raise AttributeError("Could not fetch video statistics!!")
    
        channel_stats = get_channel_stats(channel_id)
        trivia_dict = get_trivia(video_stats, channel_stats)
        if trivia_dict[0]:
            raise AttributeError("Channel does not have enough content to run Analysis!!")
        else:
            return trivia_dict
    else:
        raise AttributeError("Invalid Video-ID. Unable to fetch channel details!!")


if __name__ == "__main__":

    run_analysis()