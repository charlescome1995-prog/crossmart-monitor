# _archive/

临时归档目录。**不是产品代码**，不要从这里 import。

## 调试脚本归档 (`debug_scripts/`)
2026-06-16 从根目录清理掉的诊断/探针脚本，移到这里保留以备回查。
- `fix_am*.py` - 早期 Amazon 商品页提取修复尝试
- `inspect_*.py` - 卖家精灵 vxe-table DOM 探针
- `test_*.py` - 单次运行的端到端测试脚本

## 后端测试归档 (`backend/`)
- `test_jike.py` / `test_jike_flow.py` - 积加 API 单次调试脚本

## 恢复方法
如果某个脚本需要恢复查看，直接 `cp _archive/debug_scripts/<name>.py ./` 即可。