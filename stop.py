import urllib.error
import urllib.request

request = urllib.request.Request('http://127.0.0.1:8766/api/shutdown', data=b'',
                                 headers={'X-Local-App': '1'}, method='POST')
try:
    with urllib.request.urlopen(request, timeout=5) as response:
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as exc:
    print(exc.read().decode('utf-8'))
except urllib.error.URLError:
    print('O motor ja esta desligado.')
