#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

path = 'browser/amazon_browser.py'
content = open(path, 'r', encoding='utf-8').read()

# ─── 1. search_for_asin: 改为点击而非直接跳转 ───
old_search = '''    def search_for_asin(self, asin, search_keyword=None):
        self.current_asin = asin
        kw = search_keyword or random.choice(_COMMON_SEARCHES)
        print(f"\\n  \\U0001f5f2 \\u641c\\u7d22 '{kw}' \\u627e {asin}")
        self.b.navigate(f"https://www.amazon.com/s?k={kw.replace(' ', '+')}", wait_min=3, wait_max=7)
        self.b.scroll_down(times=random.randint(1, 3))
        human_pause(2, 6)
        print(f"  \\U0001f5b0 \\u6253\\u5f00 ASIN {asin}")
        self.b.navigate(f"https://www.amazon.com/dp/{asin}", wait_min=2, wait_max=4)
        read_pause()
        return self'''

new_search = '''    def search_for_asin(self, asin, search_keyword=None):
        self.current_asin = asin
        kw = search_keyword or random.choice(_COMMON_SEARCHES)
        print(f"\\n  \\U0001f5f2 \\u641c\\u7d22 '{kw}' \\u627e {asin}")
        self.b.navigate(f"https://www.amazon.com/s?k={kw.replace(' ', '+')}", wait_min=2, wait_max=4)
        self.b.scroll_down(times=random.randint(1, 2))
        human_pause(1, 3)
        # \\u4ece\\u641c\\u7d22\\u7ed3\\u679c\\u9875\\u627e ASIN \\u94fe\\u63a5\\u5e76\\u70b9\\u51fb\\uff0c\\u800c\\u975e\\u76f4\\u63a5\\u8df3\\u8f6c
        clicked = self._click_asin_in_results(asin)
        if not clicked:
            print(f"  \\u26a0\\ufe0f \\u641c\\u7d22\\u7ed3\\u679c\\u672a\\u627e\\u5230 ASIN {asin}\\uff0cfallback \\u76f4\\u63a5\\u8df3\\u8f6c")
            self.b.navigate(f"https://www.amazon.com/dp/{asin}", wait_min=2, wait_max=4)
        read_pause()
        return self

    def _click_asin_in_results(self, asin):
        """\\u4ece\\u641c\\u7d22\\u7ed3\\u679c\\u9875\\u627e\\u76ee\\u6807 ASIN \\u5e76\\u70b9\\u51fb"""
        js = (
            "(() => {"
            "const links = document.querySelectorAll("
            "'a.a-link-normal.s-no-outline[href*=\"/dp/" + asin + "\"],"
            " a.a-link-normal[href*=\"/dp/" + asin + "?\"]');"
            "const natural = Array.from(links).filter(a => "
            "!a.closest('[class*=\"advertisement\"],[class*=\"Sponsored\"]') && "
            "a.href.includes('/dp/" + asin + "'));"
            "if (natural.length > 0) {"
            "const el = natural[0];"
            "el.scrollIntoView({behavior:'smooth', block:'center'});"
            "setTimeout(() => el.click(), 300);"
            "return JSON.stringify({ok: true, href: el.href});"
            "}"
            "return JSON.stringify({ok: false});"
            "})()"
        )
        import json as _j
        result = _j.loads(self.b.eval(js) or '{"ok":false}')
        if result.get('ok'):
            print(f"  \\U0001f5b0 \\u70b9\\u51fb\\u641c\\u7d22\\u7ed3\\u679c\\u4e2d\\u7684 ASIN {asin}")
            import time as _time
            _time.sleep(random.uniform(2, 4))
            return True
        return False'''

content = content.replace(old_search, new_search)

# ─── 2. full_asin_check: 删除view_reviews，降低随机行为概率 ───
old_full = '''    def full_asin_check(self, asin, search_keyword=None, competitors=None):
        print(f"\\n{'='*60}")
        print(f"\\U0001f5f2 \\u68c0\\u67e5 ASIN: {asin}")
        print(f"   {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        if random.random() < 0.7:
            self.browse_homepage()
        if random.random() < 0.5:
            self.browse_category()
        if random.random() < 0.4:
            self.random_search()

        self.search_for_asin(asin, search_keyword)
        self.b.scroll_down(times=random.randint(1, 3))
        think_pause()
        self.screenshot_asin()

        if random.random() < 0.6:
            self.view_reviews()

        if competitors and random.random() < 0.5:
            n = random.randint(1, min(2, len(competitors)))
            selected = random.sample(competitors, n)
            for comp in selected:
                self.view_competitor(comp)
        return self'''

new_full = '''    def full_asin_check(self, asin, search_keyword=None, competitors=None):
        print(f"\\n{'='*60}")
        print(f"\\U0001f5f2 \\u68c0\\u67e5 ASIN: {asin}")
        print(f"   {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        if random.random() < 0.1:
            self.browse_homepage()

        self.search_for_asin(asin, search_keyword)
        self.b.scroll_down(times=random.randint(1, 2))
        think_pause()
        self.screenshot_asin()

        if competitors and random.random() < 0.3:
            n = random.randint(1, min(2, len(competitors)))
            selected = random.sample(competitors, n)
            for comp in selected:
                self.view_competitor(comp)
        return self'''

content = content.replace(old_full, new_full)

# ─── 3. 删除 view_reviews 方法 ───
old_reviews = '''    def view_reviews(self):
        if not self.current_asin:
            return self
        print(f"\\n  \\U0001f49c \\u770b\\u8bc4\\u4ef7...")
        self.b.navigate(f"https://www.amazon.com/product-reviews/{self.current_asin}/", wait_min=2, wait_max=4)
        self.b.scroll_down(times=random.randint(1, 2))
        read_pause()
        return self

    def screenshot_asin(self):'''

new_reviews = '''    def screenshot_asin(self):'''

content = content.replace(old_reviews, new_reviews)

# ─── 4. 删除 asin_monitor.py 中的 amazon.view_reviews() ───
asin_path = 'browser/asin_monitor.py'
asin_content = open(asin_path, 'r', encoding='utf-8').read()
asin_content = asin_content.replace('amazon.view_reviews()\\n', '')
open(asin_path, 'w', encoding='utf-8').write(asin_content)

open(path, 'w', encoding='utf-8').write(content)
print("Done")