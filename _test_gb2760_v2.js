// GB 2760 v2.0 配图卡片 + 弹窗 · 渲染实测
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const D = __dirname;

const html = fs.readFileSync(path.join(D, 'gb2760.html'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(D, 'data/gb2760/gb2760_full.json'), 'utf8'));

// 构造 DOM 桩
function mkEl(id) {
  const el = {
    id, innerHTML: '', textContent: '', value: '', hidden: false,
    style: new Proxy({}, { set: () => true, get: () => '' }),
    dataset: {},
    classList: { _s: new Set(), add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); }, toggle(c) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); }, contains(c) { return this._s.has(c); } },
    scrollTop: 0,
    _listeners: {},
    querySelectorAll: () => [],
    addEventListener(ev, fn) { (this._listeners[ev] = this._listeners[ev] || []).push(fn); },
    scrollIntoView() {},
    after() {}, remove() {},
  };
  return el;
}
const els = {};
const doc = {
  getElementById: (id) => (els[id] = els[id] || mkEl(id)),
  querySelectorAll: () => [],
  querySelector: () => null,
  createElement: () => mkEl('tmp'),
  addEventListener() {},
  body: { style: {}, innerHTML: '' },
};

const sandbox = { console, document: doc, setTimeout, clearTimeout, fetch: () => Promise.reject(new Error('no net')) };
sandbox.globalThis = sandbox;
sandbox.window = sandbox;   // window 指向沙箱自身，window.CAT_ART 才能被主脚本读到
vm.createContext(sandbox);

// 抽取所有 script 内容并执行（第一个是内联 CAT_ART，第二个是主逻辑）
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
scripts.forEach(js => vm.runInContext(js, sandbox));
vm.runInContext('globalThis.__api={renderByCategory,renderByAdditive,renderByFunction,renderExceptions,showCategoryModal,showAdditiveTable,showAdditiveDetail,showFunctionDetail,artSVG,openModal,closeModal,CAT_ART:window.CAT_ART,setData:(d)=>{DATA=d;}};', sandbox);
const A = sandbox.__api;
A.setData(data);

let pass = 0, fail = 0;
const ck = (n, c, e) => { c ? (pass++, console.log('  PASS  ' + n)) : (fail++, console.log('  FAIL  ' + n + (e ? '  → ' + e : ''))); };

console.log('=== 配图数据 ===');
ck('16 个分类都有配图', Object.keys(A.CAT_ART).length === 16, Object.keys(A.CAT_ART).length + ' 个');
const l1codes = data.by_category.categories.map(c => c.code);
const missing = l1codes.filter(c => !A.CAT_ART[c]);
ck('覆盖全部一级分类', missing.length === 0, '缺:' + missing.join(','));
ck('每张配图含渐变+图形', Object.values(A.CAT_ART).every(a => a.bg && a.bg.length === 2 && a.art && a.art.length > 60));

console.log('\n=== 按食品查：配图大卡 ===');
A.renderByCategory('');
const heroHtml = doc.getElementById('catList').innerHTML;
ck('渲染出 16 张大卡', (heroHtml.match(/hero-card/g) || []).length === 16, (heroHtml.match(/hero-card/g) || []).length + ' 张');
ck('每张卡含 svg', (heroHtml.match(/<svg/g) || []).length === 16, (heroHtml.match(/<svg/g) || []).length + ' 个');
ck('含编号角标', heroHtml.includes('hero-no'));
ck('含分类数角标', heroHtml.includes('hero-badge'));
ck('含"查看 →"', heroHtml.includes('查看 →'));
ck('标题含乳及乳制品', heroHtml.includes('乳及乳制品'));
ck('SVG id 唯一', (() => { const ids = [...heroHtml.matchAll(/id="g_([^"]+)"/g)].map(m => m[1]); return new Set(ids).size === ids.length; })());

console.log('\n=== 搜索过滤 ===');
// 注意：搜索命中时标题会被 highlight() 拆成 <mark>片段</mark>，断言要按「去标签后」判断
const stripTags = s => s.replace(/<[^>]*>/g, '');
A.renderByCategory('乳');
const sHtml = doc.getElementById('catList').innerHTML;
ck('搜索后卡片数减少', (sHtml.match(/hero-card/g) || []).length < 16, (sHtml.match(/hero-card/g) || []).length + ' 张');
ck('搜索命中乳制品卡', stripTags(sHtml).includes('乳及乳制品'), stripTags(sHtml).slice(0, 120));
ck('命中词被高亮', sHtml.includes('<mark'), '');
ck('meta 显示命中子分类数', doc.getElementById('catListMeta').textContent.includes('命中子分类'));
// 搜索「饮料」应命中 14.0 饮料类
A.renderByCategory('饮料');
const sHtml2 = doc.getElementById('catList').innerHTML;
ck('搜"饮料"命中饮料类', stripTags(sHtml2).includes('饮料类'), stripTags(sHtml2).slice(0, 120));

console.log('\n=== 一级分类弹窗 ===');
A.showCategoryModal('01.0');
const mask = doc.getElementById('modalMask');
ck('弹窗已打开', mask.classList.contains('open'));
ck('弹窗标题=乳及乳制品', doc.getElementById('modalTitle').innerHTML.includes('乳及乳制品'));
ck('弹窗头含配图', doc.getElementById('modalArt').innerHTML.includes('<svg'));
ck('弹窗 chip 含编号', doc.getElementById('modalChips').innerHTML.includes('01.0'));
ck('弹窗列出 30 个子分类', (doc.getElementById('modalBody').innerHTML.match(/sub-card/g) || []).length === 30, (doc.getElementById('modalBody').innerHTML.match(/sub-card/g) || []).length + ' 个');
ck('子分类含 01.01 巴氏杀菌乳', doc.getElementById('modalBody').innerHTML.includes('巴氏杀菌乳'));
ck('子分类含 L3 层级标', doc.getElementById('modalBody').innerHTML.includes('>L3<'));

console.log('\n=== 子分类弹窗（添加剂明细） ===');
// 01.02.02 风味发酵乳 = 有添加剂的真实分类
A.showAdditiveTable('01.02.02', '01.0');
const body2 = doc.getElementById('modalBody').innerHTML;
ck('弹窗标题=风味发酵乳', doc.getElementById('modalTitle').innerHTML.includes('风味发酵乳'), doc.getElementById('modalTitle').innerHTML);
ck('含返回按钮', body2.includes('modal-back'));
ck('含添加剂表格', body2.includes('data-table'));
ck('含 CNS 列', body2.includes('CNS'));
ck('含最大使用量', body2.includes('最大使用量'));
const rows2 = (body2.match(/<tr>/g) || []).length;
ck('有数据行(15种添加剂)', rows2 === 16, rows2 + ' 行(含表头)');

console.log('\n=== 例外类别（A.2 / 0 添加剂） ===');
// 01.01 巴氏杀菌乳 = 0 添加剂
A.showAdditiveTable('01.01', '01.0');
const body3 = doc.getElementById('modalBody').innerHTML;
ck('0添加剂显示A.2例外警示', body3.includes('A.2 例外') && body3.includes('不允许使用食品添加剂'), body3.slice(0, 100));

console.log('\n=== 按添加剂查 → 弹窗 ===');
A.showAdditiveDetail(data.by_additive.additives[0]);
ck('添加剂弹窗打开', doc.getElementById('modalMask').classList.contains('open'));
ck('含使用范围表', doc.getElementById('modalBody').innerHTML.includes('使用范围'));
ck('含 CNS chip', doc.getElementById('modalChips').innerHTML.includes('CNS'));

console.log('\n=== 按功能查 → 弹窗 ===');
A.showFunctionDetail(data.by_function.function_list[0]);
ck('功能弹窗打开', doc.getElementById('modalMask').classList.contains('open'));
ck('含添加剂表', doc.getElementById('modalBody').innerHTML.includes('data-table'));

console.log('\n=== 关闭 ===');
A.closeModal();
ck('弹窗已关闭', !doc.getElementById('modalMask').classList.contains('open'));

console.log('\n=== 原有功能未被破坏 ===');
A.renderByAdditive('');
ck('按添加剂列表仍渲染', doc.getElementById('addList').innerHTML.length > 500);
A.renderByFunction('');
ck('按功能列表仍渲染', doc.getElementById('funcList').innerHTML.length > 100);
A.renderExceptions('');
ck('例外表格仍渲染', doc.getElementById('excTbody').innerHTML.length > 100);

console.log('\n结果：' + pass + ' 通过 / ' + fail + ' 失败');
process.exit(fail ? 1 : 0);
