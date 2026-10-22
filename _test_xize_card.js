// v4.1.0 细则速查卡片 · 渲染实测
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const D = __dirname;

const html = fs.readFileSync(path.join(D, 'index.html'), 'utf8');
const js = html.match(/<script>([\s\S]*)<\/script>/)[1];
const cats = JSON.parse(fs.readFileSync(path.join(D, 'data/categories_2026.json'), 'utf8')).categories;
const xv = JSON.parse(fs.readFileSync(path.join(D, 'data/xize_variants.json'), 'utf8'));
const xi = JSON.parse(fs.readFileSync(path.join(D, 'data/xize_items.json'), 'utf8'));
const master = JSON.parse(fs.readFileSync(path.join(D, 'data/master.json'), 'utf8'));

const sandbox = {
  console, document: { getElementById: () => null, querySelectorAll: () => [], createElement: () => ({ style: {} }), addEventListener: () => {} },
  window: {}, setTimeout, clearTimeout, AbortController, fetch: () => Promise.reject(new Error('no net')),
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(js + '\n;globalThis.__api={renderXizeCard,findBigNo,state};', sandbox);
const { renderXizeCard, findBigNo, state } = sandbox.__api;
state.categories = cats; state.xizeVariants = xv; state.xizeItems = xi; state.records = master.records;

let pass = 0, fail = 0;
const ck = (name, cond, extra) => { cond ? (pass++, console.log('  PASS  ' + name)) : (fail++, console.log('  FAIL  ' + name + (extra ? '  → ' + extra : ''))); };

console.log('=== 31 餐饮食品 ===');
let hits = master.records.filter(r => r.big_category === '餐饮食品');
let out = renderXizeCard(hits);
ck('序号映射到 31', findBigNo('餐饮食品') === '31', 'got ' + findBigNo('餐饮食品'));
ck('渲染非空', out.length > 200, 'len=' + out.length);
ck('标题含「第 31 类」', out.includes('第 31 类'));
ck('含复用餐饮具品种', out.includes('复用餐饮具（餐馆自行消毒）'));
ck('含集中消毒服务单位品种', out.includes('复用餐饮具（集中清洗消毒服务单位消毒）'));
ck('检验项目数=46', /法定检验项目 46 项/.test(out), (out.match(/法定检验项目 (\d+) 项/) || [])[1]);
ck('餐具chip标红', (out.match(/xz-chip hit/g) || []).length > 0, (out.match(/xz-chip hit/g) || []).length + ' 个');
ck('含数据源说明', out.includes('食品安全监督抽检实施细则（2026 年版）'));
ck('默认折叠(xz-body无open)', !/class="xz-body open"/.test(out));

console.log('\n=== 34 蔬菜（含 sub 分组） ===');
hits = master.records.filter(r => r.big_category === '蔬菜');
out = renderXizeCard(hits);
ck('标题含「第 34 类」', out.includes('第 34 类'));
ck('品种数=23', /细则品种清单（23 个/.test(out), (out.match(/细则品种清单（(\d+) 个/) || [])[1]);
ck('含分组「叶菜类蔬菜」', out.includes('叶菜类蔬菜'));
ck('含分组「根茎类和薯芋类蔬菜」', out.includes('根茎类和薯芋类蔬菜'));
ck('分组块=9', (out.match(/xz-sub-name/g) || []).length === 9, (out.match(/xz-sub-name/g) || []).length + ' 块');
ck('含葱（修复过的）', out.includes('>葱'));
ck('含姜（修复过的）', out.includes('>姜'));

console.log('\n=== 36 水果类 ===');
hits = master.records.filter(r => r.big_category === '水果类');
out = renderXizeCard(hits);
ck('标题含「第 36 类」', out.includes('第 36 类'));
ck('含柑橘类分组', out.includes('柑橘类'));
ck('含热带亚热带分组', out.includes('热带和亚热带水果'));

console.log('\n=== 边界 ===');
ck('空 hits 返回空串', renderXizeCard([]) === '');
const noCat = master.records.filter(r => !r.big_category);
ck('无大类记录返回空串', renderXizeCard(noCat) === '');
const single = master.records.filter(r => r.big_category === '餐饮食品' && (r.sub_category || '').includes('复用餐饮具')).slice(0, 1);
ck('单条餐具可渲染', renderXizeCard(single).includes('第 31 类'));
ck('32 食品添加剂无数据时不出现', !renderXizeCard(master.records).includes('第 32 类'));

console.log('\n=== 39 大类序号全覆盖校验 ===');
const names = cats.map(c => c.name);
let mapBad = [];
names.forEach((n, i) => { if (findBigNo(n) !== String(i + 1)) mapBad.push(n + '->' + findBigNo(n)); });
ck('39 个大类序号全对', mapBad.length === 0, mapBad.join(','));
ck('不存在的类名返回空', findBigNo('不存在的类') === '');
const xzCount = Object.keys(xv).length;
ck('细则品种表覆盖 39 类', xzCount === 39, xzCount + ' 类');
let emptyV = Object.entries(xv).filter(([k, v]) => !(v.variants || []).length).map(([k]) => k);
// 细则原文对第32类食品添加剂标注「（暂无）」，无品种是正确状态
ck('仅32类无品种（细则原文「暂无」）', emptyV.length === 1 && emptyV[0] === '32', '空:' + emptyV.join(','));
const out32 = renderXizeCard([{ big_category: '食品添加剂' }]);
ck('32类可渲染并提示无品种', out32.includes('第 32 类') && out32.includes('细则原表未列品种'), out32.includes('细则原表未列品种') ? '' : '缺提示');

console.log('\n=== 全部记录渲染（最大压力） ===');
const t0 = Date.now();
const all = renderXizeCard(master.records);
ck('1359条全渲染成功', all.length > 1000, 'len=' + all.length);
console.log('  耗时 ' + (Date.now() - t0) + 'ms，覆盖大类 ' + (all.match(/第 \d+ 类/g) || []).length + ' 个');

console.log('\n结果：' + pass + ' 通过 / ' + fail + ' 失败');
process.exit(fail ? 1 : 0);