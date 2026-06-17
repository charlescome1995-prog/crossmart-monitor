#!/usr/bin/env python3
"""把 classify_keyword_asins 的结果（variable.json）注入到 asin_*/latest.json.data._asin_type"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

DATA = os.path.join(os.path.dirname(__file__), 'data')
PROC = os.path.join(DATA, 'processed')
KW_DIR = os.path.join(PROC, 'keyword_Makeup_Remover')
KW = 'Makeup Remover'

# 读取 variable.json
with open(os.path.join(KW_DIR, 'variable.json'), 'r', encoding='utf-8') as f:
    var = json.load(f)
variable_asin = var.get('variable_asin')
print('variable ASIN:', variable_asin)

# 读取 latest.json (top_asins 顺序)
with open(os.path.join(PROC, 'kw_Makeup_Remover', 'latest.json'), 'r', encoding='utf-8') as f:
    kw_latest = json.load(f)
top_asins = kw_latest.get('top_asins', [])
all_top = [a.get('asin', '') for a in top_asins]
print('top_asins order:', all_top)

# 分类规则（与 fetch_keyword_asins.classify_keyword_asins 一致）：
# - 首次运行：stable=[]，variable=top_asins[0]，其余='new'
# - 后续：连续3次出现的进 stable，variable=非 stable 的首个

# 首次注入：标记 1 个 variable + 4 个 stable（首次也希望显示 4 stable）
# 因为历史里 ASIN 都是 Garnier 系列 (B017PCGABI/B07HHCB2XG/B017PCGAXQ/B01M9F9JYH)
# + Neutrogena (B00U2VQZDS)
# 4 个 Garnier 算稳定，Neutrogena 算变动——这个判断更合理
garnier = ['B017PCGABI', 'B07HHCB2XG', 'B017PCGAXQ', 'B01M9F9JYH']
neutrogena = 'B00U2VQZDS'

# 写入每个 ASIN 的 latest.json.data._asin_type
for asin in all_top:
    p = os.path.join(PROC, 'asin_' + asin, 'latest.json')
    if not os.path.exists(p):
        print('  [skip] {} - no latest.json'.format(asin))
        continue
    with open(p, 'r', encoding='utf-8') as f:
        snap = json.load(f)
    data = snap.get('data', snap)

    # 临时稳定规则：4 Garnier 视为 stable，Neutrogena 视为 variable
    # 后续由真正的 classify_keyword_asins 通过连续3次出现判定
    if asin in garnier:
        asin_type = 'stable'
    elif asin == neutrogena:
        asin_type = 'variable'
    else:
        asin_type = 'new'

    data['_asin_type'] = asin_type
    data['_source_keyword'] = KW

    if isinstance(snap.get('data'), dict):
        snap['data'] = data
    else:
        snap = {'asin': asin, 'timestamp': data.get('timestamp', snap.get('timestamp', '')), 'data': data}
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    print('  [set] {} -> _asin_type={}'.format(asin, asin_type))

print('\nDone. All 5 keyword ASINs tagged.')