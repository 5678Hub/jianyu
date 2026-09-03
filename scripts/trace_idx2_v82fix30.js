// v82-fix30 详细 trace idx
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');

const html = fs.readFileSync('jianyu-standalone-v82.html', 'utf-8');

const vc = new VirtualConsole();
vc.on('jsdomError', (e) => console.error('[jsdomError]', e.message));
vc.on('error', (e) => console.error('[console.error]', e));
vc.on('log', (...args) => {});
vc.on('warn', (...args) => {});

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
      // 触发 loadData + renderTree
      window.dispatchEvent(new window.Event('DOMContentLoaded'));

      setTimeout(() => {
        // 用 selectTreeNode 触发 renderTreeDetail (内部会 buildItemIndex)
        // 现在 idx 是 closure 局部变量, 拿不到
        // 通过查询 DOM 看渲染结果
        for (const path of [
          ['水产动物及其制品', '鲜、冻水产动物', '鱼类', '非肉食性鱼类'],
          ['水产动物及其制品', '鲜、冻水产动物', '鱼类'],
          ['坚果及籽类'],
          ['坚果及籽类', '生干坚果及籽类（不包括谷物种子和豆类，包括咖啡豆、可可豆）'],
        ]) {
          window.selectTreeNode(path);
          const tc = window.document.getElementById('treeContent');
          console.log(`\n=== ${path.join(' > ')} ===`);
          const tables = tc.querySelectorAll('table');
          if (!tables.length) {
            console.log('  无 table');
            // 看是否有 "该食品暂无污染物限量记录" 提示
            const empty = tc.textContent.includes('暂无污染物限量记录');
            console.log(`  empty placeholder: ${empty}`);
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
        }
      }, 1000);
    } catch (e) {
      console.error('执行出错:', e.message, e.stack);
    }
  }, 1500);
});

setTimeout(() => process.exit(0), 12000);
