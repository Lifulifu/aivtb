# https://developers.facebook.com/docs/graph-api/reference/post
import requests
import json
import time

PAGE = '100064162059756' # Page Id or Username
LIMIT = 100 # https://developers.facebook.com/docs/graph-api/overview/rate-limiting
FIELDS = 'message,created_time' # https://developers.facebook.com/docs/graph-api/reference/post
SLEEP = 3 # Seconds

''' For Access Token
1. Go to https://business.facebook.com/content_management
2. Press Ctrl + U, then Ctrl + F to find the code that contains EAAG. 
3. Copy the highlighted text, that's the Token you need to get.
'''
ACCESS_TOKEN = 'EAAGNO4a7r2wBOxQ7A5tbpfOXSMclKoNfkUcLegcGVNEasjRTOijEsWP0bUvZCkk7KJzsv9S4KVLVIpuBGAjUTPliFGzANQ1fA29BCixvo6ZBrxqY9nWixwAg8e0vE0cZAfXxvL2SuSs4ekf4CXKt3TipDvVqKMSPljfCaAsJ7r0UdYBBD6bWsGBBAZDZD'

''' For Cookie
1. Reload https://graph.facebook.com/me?access_token={YOUR_ACCESS_TOKEN_HERE} with F12
2. Go to the Network Panel and copy value of the cookie param in Request Headers
'''
COOKIE = 'sb=ufgDZEBtTH7oNZCUALtJmKjj; datr=ufgDZOxVuQFg3HDhVQyzHIrg; c_user=100000747848781; wd=1912x932; presence=C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1694935891342%2C%22v%22%3A1%7D; xs=22%3AbuhUvlftsS9Neg%3A2%3A1627746341%3A-1%3A11326%3A%3AAcWI_-DQDh7TmQFsicvRoFF74vwcFhNxPYq6WLHPBoFSxQ; fr=00hIGoKHZzNq5em76.AWWoq1Dk4jA87EyZ6bAsze6KtIQ.BlBqw1.pJ.AAA.0.0.BlBq_p.AWVqnPVGm0A; usida=eyJ2ZXIiOjEsImlkIjoiQXMxNGQ5YW01eGVtaSIsInRpbWUiOjE2OTQ5MzcwNjd9'

url = f'https://graph.facebook.com/{PAGE}/posts?limit={LIMIT}&fields={FIELDS}&access_token={ACCESS_TOKEN}'
fields_set = set(FIELDS.replace(' ', '').split(','))
sess = requests.Session()

def get_data_and_next_url(url):
    response = sess.get(url, headers={'cookie': COOKIE})
    response = json.loads(response.text)

    try: data = response['data']
    except: 
        print(response['error']['message'])
        data = []

    try: 
        next_url = response['paging']['next']
        time.sleep(SLEEP)
    except: 
        print('Cannot find next URL')
        next_url = None
    return data, next_url

with open(f'{PAGE}.jsonl', 'w', encoding='utf-8') as file:
    while url is not None:
        print(f'\nGetting {LIMIT} posts from {url}')
        data, url = get_data_and_next_url(url)
        posts = [
            json.dumps(post) for post in data 
            if fields_set.issubset(post.keys())
        ]
        file.write('\n'.join(posts))
