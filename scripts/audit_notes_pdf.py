import pymupdf, re

PDF = 'data/gb2762/GB_2762-2025.pdf'
doc = pymupdf.open(PDF)
text = '\n'.join(p.get_text() for p in doc)

contaminant_cn = {1:'铅',2:'镉',3:'汞',4:'砷',5:'锡',6:'镍',7:'铬',
    8:'亚硝酸盐、硝酸盐',9:'苯并[a]芘',10:'N-二甲基亚硝胺',11:'多氯联苯',12:'3-氯-1,2-丙二醇'}

def table_block(t):
    title_pat = r'表\s*%d\s*食品中%s限量指标' % (t, re.escape(contaminant_cn[t]))
    m = re.search(title_pat, text)
    if not m:
        return None, None
    start = m.end()
    if t < 12:
        nxt = re.search(r'表\s*%d\s' % (t+1), text[start:])
        end = start + nxt.start() if nxt else len(text)
    else:
        na = re.search(r'(附录|附\s*录|A\.1\s*食品类别|食品类别\(名称\)说明)', text[start:])
        end = start + na.start() if na else len(text)
    return text[start:end], (start, end)

# 提取每个表的脚注：形如 "a 稻谷以糙米计" / "a) ..." / "a. ..." / "b 仅适用于..."
# 也兼容 "a仅限于..." 等无空格
fn_pat = re.compile(r'^\s*([a-e])\s*[\.\)]?\s*([一-鿿0-9].{0,80})')

def extract_footnotes(block):
    out = {}
    for line in block.splitlines():
        line = line.strip()
        m = fn_pat.match(line)
        if m and ('仅限于' in line or '仅适用于' in line or '以' in line or '干重' in line
                  or '折算' in line or '计' in line or '本' in line or '指' in line
                  or '除外' in line or '扣除' in line or '除' in line or '表示' in line):
            out.setdefault(m.group(1), []).append(line)
    return out

# 检验方法段：在每个表块内搜索 "检验方法" 之后的标准号
def extract_methods(block, t):
    # 找 "检验方法" 关键词
    res = []
    for m in re.finditer(r'检验方法', block):
        seg = block[m.start(): m.start()+400]
        stds = re.findall(r'GB\s*/?\s*T?\s*\.?\s*\d+', seg)
        res.append((m.start(), seg[:160].replace('\n',' '), stds))
    return res

for t in range(1, 13):
    block, span = table_block(t)
    if block is None:
        print(f'=== 表{t} 未定位 ==='); continue
    print(f'\n===== 表{t} {contaminant_cn[t]} =====')
    fns = extract_footnotes(block)
    print('--- 脚注字母 ---')
    if fns:
        for k in sorted(fns):
            for ln in fns[k]:
                print(f'  [{k}] {ln}')
    else:
        print('  (无标准脚注字母)')
    print('--- 检验方法段 ---')
    ms = extract_methods(block, t)
    if ms:
        for pos, seg, stds in ms:
            print(f'  ...{seg}')
            print(f'      标准号: {stds}')
    else:
        print('  (表块内无"检验方法"段，可能使用通用方法)')
