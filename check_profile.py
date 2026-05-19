import subprocess, os, time, urllib.request, json

CDP_PORT = 9224
exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
profile_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")

print("Profile:", profile_dir)
print("Profile exists:", os.path.exists(profile_dir))

# 检查profile下是否有Default目录（带收藏夹）
default_dir = os.path.join(profile_dir, "Default")
print("Default dir exists:", os.path.exists(default_dir))

# 检查Bookmarks文件
bookmarks_file = os.path.join(default_dir, "Bookmarks")
print("Bookmarks file exists:", os.path.exists(bookmarks_file))

# 列出profile下有哪些profile目录
for item in os.listdir(profile_dir):
    item_path = os.path.join(profile_dir, item)
    if os.path.isdir(item_path):
        bm = os.path.join(item_path, "Bookmarks")
        if os.path.exists(bm):
            try:
                import json
                with open(bm, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                roots = data.get('roots', {})
                total = 0
                for key, root in roots.items():
                    if isinstance(root, dict) and 'children' in root:
                        total += len(root['children'])
                print("  Profile '%s' has %d bookmark entries" % (item, total))
            except:
                print("  Profile '%s' has Bookmarks (can't read)" % item)
