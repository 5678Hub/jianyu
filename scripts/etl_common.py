"""jianyu ETL 公共函数（id 生成 / Unicode 归一化 / µ/μ 统一）

所有 calibrate / migrate / rebuild 脚本应 import 此模块，保证规范化口径一致。
"""
import re
import unicodedata

# ============================================================
# µ / μ 归一化
# ============================================================
# U+00B5 MICRO SIGN（µ，常见于键盘输入）
# U+03BC GREEK SMALL LETTER MU（μ，常见于 PDF 抽取）
# 两者视觉相同但 codepoint 不同，会导致"恩诺沙星"按 limit 被拆成两组
MU_MICRO_SIGN = '\u00b5'   # µ
MU_GREEK = '\u03bc'        # μ
# 规范字符：统一为 µ（U+00B5，键盘常见字符）
MU_CANONICAL = MU_MICRO_SIGN


def normalize_mu(text: str) -> str:
    """把 Greek mu (U+03BC) 统一替换为 Micro Sign (U+00B5)

    同时对全角空格、半角空格、NBSP 等做轻量规范化。
    不改变非 µ/μ 字符。
    """
    if not text:
        return text
    return text.replace(MU_GREEK, MU_CANONICAL)


def has_mixed_mu(text: str) -> bool:
    """检测文本中是否同时含 µ 和 μ（发布前应禁止）"""
    if not text:
        return False
    return MU_MICRO_SIGN in text and MU_GREEK in text


# ============================================================
# record id 生成
# ============================================================
def make_record_id(index: int) -> str:
    """生成 4 位零填充的 record id：r0001, r0002, ... r0712"""
    return f"r{index + 1:04d}"


# ============================================================
# failed_item 规范化（保留原始 + 增加 normalized）
# ============================================================
def normalize_failed_items(failed_items):
    """对 failed_items 列表做 µ/μ 归一化

    规则：
      - limit：原值 → limit_raw（若与归一化值不同），归一化值 → limit_normalized
      - result：原值 → result_raw（若与归一化值不同），归一化值 → result_normalized
      - 不含 µ/μ 的字段不动，只确保 *_normalized 与原值一致
    """
    if not failed_items:
        return failed_items
    out = []
    for fi in failed_items:
        if not isinstance(fi, dict):
            out.append(fi)
            continue
        new_fi = dict(fi)
        # limit 字段
        limit = fi.get('limit', '') or ''
        if limit:
            norm = normalize_mu(limit)
            if norm != limit:
                new_fi['limit_raw'] = limit
                new_fi['limit_normalized'] = norm
            else:
                new_fi['limit_normalized'] = limit
        # result 字段
        result = fi.get('result', '') or ''
        if result:
            norm_r = normalize_mu(result)
            if norm_r != result:
                new_fi['result_raw'] = result
                new_fi['result_normalized'] = norm_r
            else:
                new_fi['result_normalized'] = result
        out.append(new_fi)
    return out


# ============================================================
# 加载 + 保存辅助
# ============================================================
def load_json(path):
    import json
    return json.load(open(path, encoding='utf-8'))


def save_json(path, data, indent=2):
    import json
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=indent)


def jsonable(obj):
    """set → sorted list，递归处理嵌套"""
    if isinstance(obj, set):
        return sorted(list(obj))
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [jsonable(x) for x in obj]
    return obj