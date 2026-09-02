// 完整模拟 ancestorsLevels 段 + 跨 L2 段渲染
const fs = require('fs');
const DATA = JSON.parse(fs.readFileSync('data/gb2762/gb2762_2025.json', 'utf-8'));

function norm(s) {
  if (!s) return '';
  return s.replace(/[()（）\[\]【】:：,，.。、\s]/g, '').toLowerCase().trim();
}
function pathKey(parts) {
  return parts.filter(Boolean).map(norm).join('|');
}

// 注册到 idx
const idx = new Map();
DATA.contaminants.forEach(con => {
  con.items.forEach(it => {
    const parts = [it.a1_l1, it.a1_l2, it.a1_l3, it.a1_l4];
    const pk = pathKey(parts);
    if (pk) {
      const enriched = Object.assign({}, it, {
        _table_no: con.table_no,
        _contaminant: con.contaminant,
        _symbol: con.symbol,
        _unit: con.unit
      });
      if (!idx.has(pk)) idx.set(pk, []);
      idx.get(pk).push(enriched);
    }
  });
});

function dedupKey(it) {
  return (it._viaSub || '') + '|' + (it._table_no || '') + '|' + (it.food || '') + '|' + (it.limit_value || '') + '|' + (it.sub_value || '');
}

// 模拟 isApplicableToPath (简化版)
function isApplicableToPath(item, currentPath) {
  const food = (item.food || '').toString();
  const a1Path = [item.a1_l1, item.a1_l2, item.a1_l3, item.a1_l4].filter(Boolean);
  const ancestorLevel = a1Path.length;
  if (ancestorLevel === 0) return true;
  // 简化: 只检查 a1l1/a1l2 匹配
  for (let i = 0; i < ancestorLevel && i < currentPath.length; i++) {
    const a = norm(a1Path[i]);
    const c = norm(currentPath[i]);
    if (a !== c) return false;
  }
  return true;
}

// 完整模拟 renderDetail 的 ancestorsLevels 段
function render(nodePath) {
  const pk = pathKey(nodePath);
  let primaryItems = idx.get(pk) || [];

  const ancestorsLevels = [];
  const primKey = new Set(primaryItems.map(dedupKey));

  if (nodePath.length >= 2) {
    for (let i = nodePath.length - 2; i >= 0; i--) {
      const ancestorPath = nodePath.slice(0, i + 1);
      const ancestorKey = pathKey(ancestorPath);
      if (ancestorKey === pk) continue;
      const ancestorName = nodePath[i];
      if (!idx.has(ancestorKey)) continue;
      const items = idx.get(ancestorKey) || [];
      const filtered = items
        .filter(x => isApplicableToPath(x, ancestorPath))
        .filter(x => {
          if (nodePath.length === 2) return true;
          return !(x.a1_l1 && !x.a1_l2 && !x.a1_l3 && !x.a1_l4);
        })
        .map(x => Object.assign({}, x, { _viaSub: ancestorName }))
        .filter(x => !primKey.has(dedupKey(x)));
      if (filtered.length === 0) continue;
      ancestorsLevels.push({
        tag: '上级',
        label: ancestorName + ' 赋予的污染物限量要求',
        items: filtered
      });
    }

    // v82-fix83
    if (nodePath.length === 3 && primaryItems.length === 0 && DATA && DATA.contaminants) {
      const pathL1 = norm(nodePath[0]);
      const pathL2 = nodePath[1];
      const crossL2Items = [];
      DATA.contaminants.forEach(con => {
        con.items.forEach(it => {
          const xL1 = norm(it.a1_l1);
          if (xL1 !== pathL1) return;
          if ((it.a1_l2 || '') === pathL2) return;
          if (it.a1_l3 || it.a1_l4) return;
          if (!it.a1_l1) return;
          crossL2Items.push(Object.assign({}, it, {
            _contaminant: con.contaminant, _symbol: con.symbol, _unit: con.unit,
            _table_no: con.table_no,
            _viaSub: '同章节其他通类'
          }));
        });
      });
      const ancestorL1Path = [nodePath[0]];
      const filtered2 = crossL2Items.filter(x => isApplicableToPath(x, ancestorL1Path));
      const shownKeys = new Set();
      for (const seg of ancestorsLevels) {
        for (const it of seg.items) shownKeys.add(dedupKey(it));
      }
      const crossFiltered = filtered2.filter(x => {
        const k = dedupKey(x);
        if (shownKeys.has(k)) return false;
        shownKeys.add(k);
        return true;
      });
      if (crossFiltered.length > 0) {
        ancestorsLevels.push({
          tag: '跨级',
          label: '同章节其他通类赋予的污染物限量要求',
          items: crossFiltered
        });
      }
    }
  }

  return ancestorsLevels;
}

// 测试关键节点
const tests = [
  ['蔬菜及其制品（包括薯类，不包括食用菌）', '蔬菜制品', '蔬菜罐头'],
  ['水果及其制品', '水果制品', '水果罐头'],
  ['水产动物及其制品', '鲜、冻水产动物', '鱼糜制品（例如：鱼丸等）'],
  ['蛋及蛋制品', '蛋制品', '卤蛋'],
  ['肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品'],
  ['谷物及其制品(不包括焙烤制品)', '谷物制品', '其他谷物制品[例如：带馅（料）面米制品、粥类罐头等]'],
  ['水果及其制品', '水果制品', '其他新鲜水果（包括甘蔗）'],
  ['坚果及籽类', '生干坚果及籽类（不包括谷物种子和豆类，包括咖啡豆、可可豆）', '熟制坚果及籽类（带壳、脱壳、包衣）'],
  ['饮料类', '固体饮料[包括速溶咖啡研磨咖啡]', '植物蛋白饮料'],
  ['调味品', '其他调味品', '固态调味品'],
];

for (const node of tests) {
  console.log('\n=== ' + node[2] + ' ===');
  const segs = render(node);
  let total = 0;
  for (const seg of segs) {
    console.log('  [' + seg.tag + '] ' + seg.label + ': ' + seg.items.length + ' 条');
    total += seg.items.length;
    for (const it of seg.items) {
      var sub = it.sub_value ? '/' + it.sub_value : '';
      console.log('    - [' + it._table_no + it._contaminant + '] val=' + it.limit_value + sub + ' food=' + (it.food || '').slice(0, 30));
    }
  }
  console.log('  总计: ' + total + ' 条 row');
}
