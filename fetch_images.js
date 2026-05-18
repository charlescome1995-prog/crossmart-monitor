const https = require('https');
const asins = ['B09V7Z4TJG','B0F2J966QL','B0CGB215HR','B0GKFD9ZQW','B0BBSP2JNQ','B0DSLGHPPW','B01B0WV6GI','B0C52W7NLB','B0F3Z873VL','B0GDSQBRYX'];

function fetchPage(asin) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: 'www.amazon.com',
      path: '/dp/' + asin,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache'
      }
    };
    const req = https.get(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        const regex = /https?:\/\/m\.media-amazon\.com\/images\/I\/[^"',\\\s)]+/g;
        const matches = data.match(regex);
        const unique = matches ? [...new Set(matches)] : [];
        // Find the main product image (not sprite/icon)
        const productImgs = unique.filter(u => u.includes('_AC_SX') || u.includes('_SL'));
        resolve({ asin, images: unique, productImages: productImgs });
      });
    });
    req.on('error', reject);
    req.setTimeout(10000, () => { req.destroy(); resolve({ asin, images: [], productImages: [] }); });
    req.end();
  });
}

(async () => {
  for (const asin of asins) {
    const result = await fetchPage(asin);
    console.log('--- ' + asin + ' ---');
    if (result.productImages.length > 0) {
      result.productImages.slice(0, 3).forEach(u => console.log(u));
    } else if (result.images.length > 0) {
      result.images.slice(0, 3).forEach(u => console.log(u));
    } else {
      console.log('NO IMAGES FOUND');
    }
  }
})();
