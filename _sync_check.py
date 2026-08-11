# -*- coding: utf-8 -*-
import hashlib, pathlib, shutil

SRC = pathlib.Path(r"C:\Users\10487\WorkBuddy\抽检不合格查询助手\data")
DST = pathlib.Path(r"C:\Users\10487\WorkBuddy\jianyu\data")

FILES = [
    "master.json",
    "category_map.json",
    "synonyms.json",
    "categories_2026.json",
    "categories_2026_full.json",
    "subcat_to_items.json",
    "current_period/gb_checklist.json",
    "current_period/gb_checklist_subcat.json",
]

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

diff = []
for rel in FILES:
    sp = SRC / rel
    dp = DST / rel
    if not sp.exists():
        print(f"MISSING-SRC  {rel}")
        continue
    s = md5(sp)
    if not dp.exists():
        print(f"MISSING-DST  {rel}  src={s[:8]} -> copy")
        diff.append(rel)
        continue
    d = md5(dp)
    if s != d:
        print(f"DIFFER       {rel}  src={s[:8]} dst={d[:8]} -> copy")
        diff.append(rel)
    else:
        print(f"OK           {rel}  {s[:8]}")

print("---DIFFER_COUNT", len(diff))
for r in diff:
    print("NEEDCOPY", r)
