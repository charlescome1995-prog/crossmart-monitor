import json

path = r'C:\Users\OPENPC\.openclaw\workspace-openpc_ad\crossmart-monitor\frontend\data\monitor-data.json'
d = json.load(open(path, encoding='utf-8'))

real_images = {
    'B09V7Z4TJG': 'https://m.media-amazon.com/images/I/51MqWeipeaL._AC_SX679_.jpg',
    'B0F2J966QL': 'https://m.media-amazon.com/images/I/71LYpX0VlCL._AC_SX679_.jpg',
    'B0CGB215HR': 'https://m.media-amazon.com/images/I/61bHeKSgL5L._AC_SX679_.jpg',
    'B0GKFD9ZQW': 'https://m.media-amazon.com/images/I/51utpRckeQL._AC_SX679_.jpg',
    'B0BBSP2JNQ': 'https://m.media-amazon.com/images/I/71vMjZY0YzL._AC_SX679_.jpg',
    'B0DSLGHPPW': 'https://m.media-amazon.com/images/I/61iup4xRA0L._AC_SX679_.jpg',
    'B01B0WV6GI': 'https://m.media-amazon.com/images/I/61B+kd4IIwL._AC_SX679_.jpg',
    'B0C52W7NLB': 'https://m.media-amazon.com/images/I/718tsIBHFnL._AC_SX679_.jpg',
    'B0F3Z873VL': 'https://m.media-amazon.com/images/I/71zgpAqJxvL._AC_SX679_.jpg',
    'B0GDSQBRYX': 'https://m.media-amazon.com/images/I/71dDlv2N4HL._AC_SX679_.jpg',
}

updated = 0
for a in d['asins']:
    asin = a['asin']
    if asin in real_images:
        new_url = real_images[asin]
        for snap in a.get('snapshots', []):
            if 'data' in snap and 'main_image' in snap['data']:
                old = snap['data']['main_image']
                if old != new_url:
                    print(f'{asin}: {old[:60]}... -> {new_url[:60]}...')
                    snap['data']['main_image'] = new_url
                    updated += 1

print(f'\nUpdated {updated} image URLs')
json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('Saved')
