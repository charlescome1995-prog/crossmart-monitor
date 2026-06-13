
(() => {
    const $ = (sel) => document.querySelector(sel);
    const body = document.body.innerText || '';

    const titleEl = document.querySelector('#productTitle');
    const title = (titleEl ? titleEl.textContent.trim() : (document.querySelector('h1') || {textContent: ''}).textContent.trim()).substring(0, 200);
    // title 备选：从 meta og:title 或 JSON-LD
    if (!title) {
        const ogT = document.querySelector('meta[property="og:title"]');
        if (ogT) title = ogT.content.substring(0, 200);
    }
    if (!title) {
        const ld = document.querySelector('script[type="application/ld+json"]');
        if (ld) { try { const d = JSON.parse(ld.textContent); if (d && d.name) title = d.name.substring(0, 200); } catch(e){} }
    }

    const priceWholeEl = document.querySelector('#corePrice_feature_div .a-price-whole');
    const priceOffscreenEl = document.querySelector('#corePrice_feature_div .a-offscreen');
    const corePrice = priceOffscreenEl ? priceOffscreenEl.textContent.trim() : (priceWholeEl ? '$' + priceWholeEl.textContent.trim() : '');
    let price = corePrice || (document.querySelector('.a-price .a-offscreen') || {textContent: ''}).textContent.trim();
    // price 备选：从页面 body 文本匹配 $xx.xx 或 $xx
    if (!price) { const pm = body.match(/\$\d+\.\d{2}/); if (pm) price = pm[0]; }
    if (!price) { const pm2 = body.match(/\$\d+(?:\.\d+)?/); if (pm2) price = pm2[0]; }

    const ratingEl = document.querySelector('.a-icon-alt');
    const ratingM = (ratingEl ? ratingEl.textContent.trim() : '').match(/([\d.]+)/);
    let rating = ratingM ? ratingM[1] : '';
    // rating 备选：从 body 文本匹配 "X.X out of 5 stars"
    if (!rating) { const rm = body.match(/([\d.]+)\s*out\s*of\s*5\s*stars?/i); if (rm) rating = rm[1]; }

    const reviewEl = document.querySelector('#acrCustomerReviewText');
    const reviewM = (reviewEl ? reviewEl.textContent.trim() : '').match(/([\d,]+)/);
    const review_count = reviewM ? reviewM[1].replace(/,/g, '') : '';

    const brandEl = document.querySelector('#bylineInfo');
    let brand = (brandEl ? brandEl.textContent.trim() : '').replace(/^Visit the /, '').replace(/ Store$/, '').replace(/^访问/, '').replace(/品牌旗舰店$/, '').trim();
    if (brand.length > 60) brand = brand.substring(0, 60);

    const soldByEl = document.querySelector('#merchantInfoFeature_feature_div .a-link-normal') || document.querySelector('#merchant-info');
    const soldBy = soldByEl ? soldByEl.textContent.trim() : '';

    // ── 产品图片（多个备选选择器 + 高分辨率替换）──
    let mainImg = '';
    const imgSelectors = [
        '#landingImage',
        '#imgTagWrapperId img',
        '#main-image',
        '#imgBlkFront',
        '#mainImage',
        '#ebay-image img',
        '.a-dynamic-image',
        '#altImages img',
        '#richThumbnails img',
    ];
    for (const sel of imgSelectors) {
        const el = document.querySelector(sel);
        if (el) {
            mainImg = el.getAttribute('src') || el.getAttribute('data-old-hires') || '';
            if (mainImg) break;
        }
    }
    // 尝试从 data-a-dynamic-image 提取最高分辨率图片
    if (!mainImg) {
        const dynEl = document.querySelector('[data-a-dynamic-image]');
        if (dynEl) {
            try {
                const dynData = JSON.parse(dynEl.getAttribute('data-a-dynamic-image') || '{}');
                const urls = Object.keys(dynData);
                if (urls.length > 0) {
                    // 取分辨率最高的（最后一张通常是主图）
                    mainImg = urls[urls.length - 1];
                }
            } catch(e) {}
        }
    }
    // 升级到高分辨率
    if (mainImg) {
        mainImg = mainImg.replace(/\._AC_\w+_\.jpg/, '._AC_SL1500_.jpg');
        mainImg = mainImg.replace(/\._SY\d+_\.jpg/, '._AC_SL1500_.jpg');
        mainImg = mainImg.replace(/\._SX\d+_\.jpg/, '._AC_SL1500_.jpg');
        // 去掉尺寸后缀参数
        mainImg = mainImg.replace(/\?.*$/, '');
    }
    // main_image 备选：从 meta og:image
    if (!mainImg) {
        const ogI = document.querySelector('meta[property="og:image"]');
        if (ogI && ogI.content) mainImg = ogI.content;
    }
    // main_image 备选：从 JSON-LD product image
    if (!mainImg) {
        const ldI = document.querySelector('script[type="application/ld+json"]');
        if (ldI) {
            try {
                const d = JSON.parse(ldI.textContent);
                if (d && d.image) mainImg = Array.isArray(d.image) ? d.image[0] : d.image;
                else if (d && d.@graph) { const g = d.@graph.find(x => x['@type'] === 'Product'); if (g && g.image) mainImg = Array.isArray(g.image) ? g.image[0] : g.image; }
            } catch(e){}
        }
    }

    // ── BSR ──
    let bsr = '', bsrSubCategory = '', bsrSubRank = '', bsrAllSubRanks = [];
    const bsrSection = body.match(/Best Sellers Rank[\s\S]{0,500}/);
    if (bsrSection) {
        bsr = bsrSection[0].substring(0, 300);
        const topM = bsr.match(/#([\d,]+)\s+in\s+([^#\n\r]+)/);
        if (topM) { bsrSubRank = topM[1].replace(/,/g, ''); bsrSubCategory = topM[2].trim().substring(0, 100); }
        // 提取所有 #数字（第一个是大类，其余是小类/子分类排名）
        const allMatches = bsr.matchAll(/#([\d,]+)\s+in\s+([^\n\r]+)/g);
        let idx = 0;
        for (const m of allMatches) {
            if (idx === 0) { idx++; continue; } // 跳过第一个（已作为大类）
            bsrAllSubRanks.push(m[1].replace(/,/g, ''));
            idx++;
            if (bsrAllSubRanks.length >= 5) break; // 最多取5个
        }
    }

    // ── Badges (多个来源) ──
    const badges = [];
    const lowerBody = body.toLowerCase();
    if (lowerBody.includes("bestseller") || document.querySelector('[class*="bestseller"], #detailBulletsWrapper_feature_div [class*="bestseller"]')) badges.push('BS');
    if (lowerBody.includes("amazon's choice") || document.querySelector('[class*="choices"], #acBadge')) badges.push('AC');
    if (lowerBody.includes("new release") || document.querySelector('[class*="new-releases"]')) badges.push('NR');
    if (document.querySelector('#aplusBrandLogo, #aplus_feature_div iframe, #aplus3pFeatureText')) badges.push('A+');
    const badgeEl = document.querySelector('.a-badge-container');
    if (badgeEl) {
        const bt = badgeEl.innerText || '';
        if (bt.includes('Bestseller')) badges.push('BS');
        if (bt.includes('New')) badges.push('NR');
    }
    // A+ badge
    if (badges.indexOf('A+') === -1 && document.querySelector('#aplus_feature_div')) badges.push('A+');

    // ── Deal 活动 ──
    let deal_activity = '无';
    const dealEl = document.querySelector('#dealBadge_feature_div, #dealsLabel_feature_div, .deal-sash, [class*="deal-badge"]');
    if (dealEl) {
        const dt = dealEl.innerText || '';
        if (dt.includes('Lightning Deal')) deal_activity = 'Lightning Deal';
        else if (dt.includes('Deal of the Day') || dt.includes('DOTD')) deal_activity = 'Deal of the Day';
        else if (dt.includes('Best Deal')) deal_activity = 'Best Deal';
        else if (dt.includes('Deal')) deal_activity = 'Deal';
        else deal_activity = dt.trim() || 'Deal';
    }
    // 从 body 文本二次确认
    if (deal_activity === '无') {
        if (lowerBody.includes('lightning deal')) deal_activity = 'Lightning Deal';
        else if (lowerBody.includes('deal of the day')) deal_activity = 'Deal of the Day';
        else if (lowerBody.includes('best deal')) deal_activity = 'Best Deal';
    }

    // ── 优惠券 ──
    let coupon = '无';
    const couponEl = document.querySelector('#couponPopoverFeature, [data-coupon], .coupon-badge, #sidesheet看到她 .coupon');
    if (couponEl) {
        const ct = couponEl.innerText || '';
        const pctM = ct.match(/(\d+)%/);
        const amtM = ct.match(/\$(\d+\.?\d*)/);
        if (pctM) coupon = pctM[1] + '% off';
        else if (amtM) coupon = '$' + amtM[1] + ' off';
        else if (ct.trim()) coupon = ct.trim();
        else coupon = '有优惠券';
    }
    if (coupon === '无' && lowerBody.includes('coupon')) {
        const cM = body.match(/(\d+)%\s*off.*coupon|save\s*\$(\d+\.?\d*)/i);
        if (cM) coupon = cM[1] ? cM[1] + '% off' : '$' + cM[2] + ' off';
    }

    // ── Prime 专享折扣 ──
    let prime_discount = '未开启';
    const primeEl = document.querySelector('#primeExclusiveExtraContent, #primeBenefits, .prime-benefits, #prime-ingress-features');
    if (primeEl) {
        const pt = primeEl.innerText || '';
        const discM = pt.match(/(\d+)%/);
        if (discM) prime_discount = discM[1] + '%';
        else if (pt.includes('Prime')) prime_discount = pt.trim().substring(0, 30);
    }
    if (prime_discount === '未开启') {
        if (lowerBody.includes('prime member') && lowerBody.includes('%')) {
            const pdM = body.match(/prime.*?(\d+)%/i);
            if (pdM) prime_discount = pdM[1] + '%';
        }
    }

    const result = {
        title, price, rating, review_count, brand, soldBy,
        main_image: mainImg,
        bsr: bsr, bsr_subcategory: bsrSubCategory, bsr_subrank: bsrSubRank, bsr_all_subranks: bsrAllSubRanks,
        badges: badges,
        deal_activity: deal_activity,
        coupon: coupon,
        prime_discount: prime_discount,
        snapshot_time: new Date().toISOString(),
    };
    return JSON.stringify(result);