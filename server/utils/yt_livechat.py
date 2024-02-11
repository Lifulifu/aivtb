import googleapiclient.discovery
import google_auth_oauthlib.flow


class YTLiveChat:
    def __init__(self, client_secrets: str):
        self.youtube = self.get_youtube_client(client_secrets=client_secrets)
        self.page_token = None

    def get_youtube_client(self, client_secrets: str):
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets, ["https://www.googleapis.com/auth/youtube.readonly"]
        )
        credentials = flow.run_local_server(port=0)
        return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    def get_live_streams(self):
        request = self.youtube.liveBroadcasts().list(
            part="snippet", broadcastType="all", broadcastStatus="active"
        )
        response = request.execute()
        return response["items"]

    def get_live_chat_id(self, item):
        return item["snippet"]["liveChatId"]

    def get_live_chat_messages(self, live_chat_id: str, max_results=10):
        request = self.youtube.liveChatMessages().list(
            part="snippet",
            liveChatId=live_chat_id,
            maxResults=max_results,
        )
        response = request.execute()
        return response["items"]

    def get_unread_live_chat_messages(self, live_chat_id: str, max_results=10):
        request = self.youtube.liveChatMessages().list(
            part="snippet,authorDetails",
            liveChatId=live_chat_id,
            maxResults=max_results,
            pageToken=self.page_token,
        )
        response = request.execute()
        self.page_token = response.get("nextPageToken")
        return response["items"]
