const fs = require('fs');

const DATA = JSON.parse(fs.readFileSync('data/gb2762/gb2762_2025.json', 'utf-8'));

function norm(s) {
  if (!s) return '';
  return s.replace(/[()（）\[\]【】:：,，.。、\s]/g, '').toLowerCase().trim();
}
function pathKey(parts) {
  return parts.filter(Boolean).map(norm).join('|');
}

const idx = new Map();
DATA.contaminants.forEach(con => {
  con.items.forEach(it => {
    const parts = [it.a1_l1, it.a1_l2, it.a1_l3, it.a1_l4];
    const pk = pathKey(parts);
    if (pk) {
      const enriched = Object.assign({}, it, {
        _table_no: con.table_no,
        _contaminant: con.contaminant
      });
      if (!idx.has(pk)) idx.set(pk, []);
      idx.get(pk).push(enriched);
    }
  });
});

function checkCrossL2Miss(nodePath) {
  if (nodePath.length !== 3) return [];
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
      const sub = it.sub_value || '';
      crossL2Items.push({
        tno: con.table_no,
        con: con.contaminant,
        l2: it.a1_l2,
        food: it.food,
        limit: it.limit_value,
        sub: sub
      });
    });
  });
  return crossL2Items;
}

const tests = [
  ['蔬菜及其制品（包括薯类，不包括食用菌）', '蔬菜制品', '蔬菜罐头'],
  ['水果及其制品', '水果制品', '水果罐头'],
  ['水产动物及其制品', '鲜、冻水产动物', '鱼糜制品（例如：鱼丸等）'],
  ['蛋及蛋制品', '蛋制品', '卤蛋'],
];

for (const node of tests) {
  const pk = pathKey(node);
  const pi = idx.get(pk) || [];
  const cross = checkCrossL2Miss(node);
  console.log('\n=== ' + node[2] + ' ===');
  console.log('primaryItems.length: ' + pi.length);
  console.log('跨 L2 通类 row 数: ' + cross.length);
  for (const it of cross) {
    var v = it.limit + (it.sub ? '/' + it.sub : '');
    console.log('  [' + it.tno + it.con + '] val=' + v + ' food=' + it.food.slice(0, 30) + ' 来自 L2=' + it.l2.slice(0, 25));
  }
}
