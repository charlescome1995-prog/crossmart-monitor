content = open('snapshot_storage.py', 'rb').read().decode('utf-8')
old = '    d = os.path.join(DATA_DIR, f"kw_{safe}")\n    os.makedirs(d, exist_ok=True)\n    return d\n\n\ndef save_asin_snapshot'

new = '    d = os.path.join(DATA_DIR, f"kw_{safe}")\n    os.makedirs(d, exist_ok=True)\n    return d\n\n\n# ══════════════════════════════════════════════════\n# ASIN 元数据（首次写入后锁定）\n# ══════════════════════════════════════════════════\n\nMETA_FILE = "_meta.json"\n\n\ndef save_asin_meta(asin, related_asins):\n    d = _asin_dir(asin)\n    meta_path = os.path.join(d, META_FILE)\n    if os.path.exists(meta_path):\n        print(f"  [meta] _meta.json 已存在，跳过写入")\n        return\n    meta = {\n        "asin": asin,\n        "related_asins": related_asins,\n        "first_seen": datetime.now().isoformat(),\n    }\n    with open(meta_path, 'w', encoding='utf-8') as f:\n        json.dump(meta, f, ensure_ascii=False, indent=2)\n    print(f"  [meta] _meta.json 已写入，{len(related_asins)} 个关联ASIN（首次固定）")\n\n\ndef load_asin_meta(asin):\n    meta_path = os.path.join(_asin_dir(asin), META_FILE)\n    if not os.path.exists(meta_path):\n        return None\n    with open(meta_path, 'r', encoding='utf-8') as f:\n        return json.load(f)\n\n\ndef save_asin_snapshot'

if old in content:
    print('found')
    new_content = content.replace(old, new, 1)
    open('snapshot_storage.py', 'wb').write(new_content.encode('utf-8'))
    print('done')
else:
    print('not found')
    idx = content.find('def save_asin_snapshot')
    print(repr(content[idx-300:idx+30]))