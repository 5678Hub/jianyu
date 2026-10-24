// GB 2760 v2.0 · jsdom 真实 DOM 渲染验证
const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');
const D = __dirname;

let pass = 0, fail = 0;
const ck = (n, c, e) => { c ? (pass++, console.log('  PASS  ' + n)) : (fail++, console.log('  FAIL  ' + n + (e ? '  → ' + e : ''))); };

const html = fs.readFileSync(path.join(D, 'gb2760.html'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(D, 'data/gb2760/gb2760_full.json'), 'utf8'));

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  url: 'http://127.0.0.1:8901/gb2760.html',
  resources: 'usable',
  pretendToBeVisual: true,
  beforeParse(window) {
    // 拦截 fetch，直接返回本地数据
    window.fetch = async (url) => {
      const u = String(url);
      if (u.includes('gb2760_full.json')) {
        return { ok: true, json: async () => data };
      }
      return { ok: false, status: 404, json: async () => ({}) };
    };
  },
});

const { window } = dom;
const doc = window.document;

setTimeout(() => {
  console.log('=== 数据加载 ===');
  const st = doc.getElementById('st-add');
  ck('添加剂数已填充', st && st.textContent !== '—', st && st.textContent);
  ck('食品条目数已填充', doc.getElementById('st-item').textContent !== '—', doc.getElementById('st-item').textContent);
  ck('分类节点数已填充', doc.getElementById('st-cat').textContent !== '—', doc.getElementById('st-cat').textContent);
  ck('版本显示 v2.0', doc.getElementById('updatedTag').textContent === 'v2.0', doc.getElementById('updatedTag').textContent);

  console.log('\n=== 切到「按食品查」 ===');
  const catTab = doc.querySelector('.tab[data-tab="by-category"]');
  catTab.dispatchEvent(new window.Event('click', { bubbles: true }));
  ck('Tab 切换成功', doc.getElementById('panel-by-category').hidden === false);

  const cards = doc.querySelectorAll('.hero-card');
  ck('渲染 16 张配图大卡', cards.length === 16, cards.length + ' 张');
  ck('每张卡都有 svg', doc.querySelectorAll('.hero-card svg').length === 16, doc.querySelectorAll('.hero-card svg').length + ' 个');
  ck('每张卡有编号', doc.querySelectorAll('.hero-card .hero-no').length === 16);
  ck('每张卡有分类数角标', doc.querySelectorAll('.hero-card .hero-badge').length === 16);
  ck('每张卡有「查看 →」', doc.querySelectorAll('.hero-card .hero-go').length === 16);

  // SVG 内容抽查
  const firstSvg = cards[0].querySelector('svg');
  ck('SVG 有 viewBox', firstSvg.getAttribute('viewBox') === '0 0 120 90', firstSvg.getAttribute('viewBox'));
  ck('SVG 有渐变定义', !!firstSvg.querySelector('linearGradient'));
  ck('SVG 有图形 path', firstSvg.querySelectorAll('path').length >= 1, firstSvg.querySelectorAll('path').length + ' 个');

  console.log('\n=== 点击大卡 → 弹窗 ===');
  cards[0].dispatchEvent(new window.Event('click', { bubbles: true }));
  const mask = doc.getElementById('modalMask');
  ck('弹窗打开', mask.classList.contains('open'));
  ck('弹窗有配图', doc.getElementById('modalArt').querySelectorAll('svg').length === 1);
  ck('标题=乳及乳制品', doc.getElementById('modalTitle').textContent.includes('乳及乳制品'), doc.getElementById('modalTitle').textContent.trim());
  const subCards = doc.querySelectorAll('.modal-body .sub-card');
  ck('列出 30 个子分类', subCards.length === 30, subCards.length + ' 个');
  ck('子分类含编号', doc.querySelector('.modal-body .sub-card .sc-code').textContent.length > 0);

  console.log('\n=== 点击子分类 → 添加剂明细 ===');
  // 找有添加剂的子分类（01.02.02 风味发酵乳）
  const target = [...subCards].find(s => s.dataset.code === '01.02.02');
  ck('找到 01.02.02 子分类', !!target);
  target.dispatchEvent(new window.Event('click', { bubbles: true }));
  const body = doc.getElementById('modalBody');
  ck('明细表渲染', body.querySelectorAll('table.data-table').length === 1);
  const trs = body.querySelectorAll('tbody tr');
  ck('15 行添加剂数据', trs.length === 15, trs.length + ' 行');
  ck('表头含 CNS', body.querySelector('thead').textContent.includes('CNS'));
  ck('表头含最大使用量', body.querySelector('thead').textContent.includes('最大使用量'));
  ck('有返回按钮', !!doc.getElementById('modalBack'));

  console.log('\n=== 返回上级 ===');
  doc.getElementById('modalBack').dispatchEvent(new window.Event('click', { bubbles: true }));
  ck('返回到一级分类列表', doc.querySelectorAll('.modal-body .sub-card').length === 30);

  console.log('\n=== Esc 关闭 ===');
  doc.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  ck('弹窗已关闭', !mask.classList.contains('open'));

  console.log('\n=== 搜索过滤 ===');
  const search = doc.getElementById('search');
  search.value = '饮料';
  search.dispatchEvent(new window.Event('input', { bubbles: true }));
  const after = doc.querySelectorAll('.hero-card').length;
  ck('搜索后卡片减少', after < 16 && after > 0, after + ' 张');
  ck('命中 14.0 饮料类', [...doc.querySelectorAll('.hero-card')].some(c => c.dataset.code === '14.0'), '');

  search.value = '不存在的分类xyz';
  search.dispatchEvent(new window.Event('input', { bubbles: true }));
  ck('无结果显示空态', doc.getElementById('catEmpty').hidden === false);
  ck('无结果时卡片清空', doc.querySelectorAll('.hero-card').length === 0);

  search.value = '';
  search.dispatchEvent(new window.Event('input', { bubbles: true }));
  ck('清空后恢复 16 张', doc.querySelectorAll('.hero-card').length === 16);

  console.log('\n=== 其他 Tab 未被破坏 ===');
  doc.querySelector('.tab[data-tab="by-additive"]').dispatchEvent(new window.Event('click', { bubbles: true }));
  ck('按添加剂列表渲染', doc.querySelectorAll('#addList .add-card').length === 231, doc.querySelectorAll('#addList .add-card').length + ' 张');
  doc.querySelector('.tab[data-tab="by-function"]').dispatchEvent(new window.Event('click', { bubbles: true }));
  ck('按功能列表渲染', doc.querySelectorAll('#funcList .add-card').length === 21, doc.querySelectorAll('#funcList .add-card').length + ' 张');
  doc.querySelector('.tab[data-tab="exceptions"]').dispatchEvent(new window.Event('click', { bubbles: true }));
  ck('例外表格渲染', doc.querySelectorAll('#excTbody tr').length === 67, doc.querySelectorAll('#excTbody tr').length + ' 行');

  console.log('\n结果：' + pass + ' 通过 / ' + fail + ' 失败');
  process.exit(fail ? 1 : 0);
}, 1500);
