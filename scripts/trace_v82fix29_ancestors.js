// 用 jsdom 加载 v82-fix29 并 trace 腌制水产品 详情页的 levels
const fs = require('fs');
const { JSDOM, ResourceLoader, VirtualConsole } = require('jsdom');

const html = fs.readFileSync('jianyu-standalone-v82.html', 'utf-8');

const vc = new VirtualConsole();
vc.on('jsdomError', (e) => console.error('[jsdomError]', e.message));
vc.on('error', (e) => console.error('[console.error]', e));
vc.on('log', (...args) => console.log('[console.log]', ...args));
vc.on('warn', (...args) => console.warn('[console.warn]', ...args));

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'http://127.0.0.1:8765/jianyu-standalone-v82.html',
  virtualConsole: vc,
  resources: 'usable',
});

const window = dom.window;

window.addEventListener('load', () => {
  setTimeout(() => {
    try {
      const testPath = ['水产动物及其制品', '水产制品', '腌制水产品'];
      window.selectTreeNode(testPath);
      const tc = window.document.getElementById('treeContent');
      console.log(`\n=== 查询 ${testPath.join(' > ')} ===`);
      const tables = tc.querySelectorAll('table');
      if (!tables.length) {
        console.log('  无 table');
      }
      for (const t of tables) {
        const block = t.closest('.level-block');
        const head = block?.querySelector('.level-header');
        const label = head?.textContent.replace(/\s+/g, ' ').trim();
        const rows = t.querySelectorAll('tbody tr');
        console.log(`\n  [${label}] (${rows.length} 行)`);
        for (const r of rows) {
          const cells = Array.from(r.querySelectorAll('td')).map(c => c.textContent.replace(/\s+/g, ' ').trim());
          if (cells.length) console.log(`    ${cells.slice(0, 4).join(' | ')}`);
        }
      }

      console.log('\n=== debug: 调用 buildItemIndex 看 idx ===');
      const idx = window.buildItemIndex ? window.buildItemIndex() : null;
      if (idx) {
        const paths = [
          '水产动物及其制品',
          '水产动物及其制品|水产制品',
          '水产动物及其制品|水产制品|腌制水产品',
        ];
        for (const p of paths) {
          const items = idx.get(p) || [];
          console.log(`  idx["${p}"]: ${items.length} 条`);
          for (const it of items) {
            console.log(`    - ${it._contaminant || it.pollutant} | ${it.food} | ${it.limit_value || it.limit}`);
          }
        }
      }
    } catch (e) {
      console.error('执行出错:', e.message, e.stack);
    }
  }, 1500);
});

setTimeout(() => process.exit(0), 10000);
