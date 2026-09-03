// 使用 jsdom 加载 v82-fix27 并模拟点击 非肉食性鱼类
const fs = require('fs');
const path = require('path');
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
      // 测试多个路径的详情页
      const testPaths = [
        ['水产动物及其制品', '水产制品', '鱼糜制品（例如：鱼丸等）'],
        ['水产动物及其制品', '鲜、冻水产动物', '鱼类', '非肉食性鱼类'],
        ['水产动物及其制品', '水产制品', '海蜇制品'],
        ['水产动物及其制品', '水产制品', '鱼类制品'],
      ];
      for (const path of testPaths) {
        window.selectTreeNode(path);
        const tc = window.document.getElementById('treeContent');
        console.log(`\n=== 查询 ${path.join(' > ')} ===`);
        const tables = tc.querySelectorAll('table');
        if (!tables.length) {
          console.log('  无 table (本级 idx 为空)');
        }
        for (const t of tables) {
          const block = t.closest('.level-block');
          const head = block?.querySelector('.level-header');
          const label = head?.textContent.replace(/\s+/g, ' ').trim();
          const rows = t.querySelectorAll('tbody tr');
          console.log(`\n  [${label}]`);
          for (const r of rows) {
            const cells = Array.from(r.querySelectorAll('td')).map(c => c.textContent.replace(/\s+/g, ' ').trim());
            if (cells.length) console.log(`    ${cells.slice(0, 4).join(' | ')}`);
          }
        }
      }
    } catch (e) {
      console.error('执行出错:', e.message, e.stack);
    }
  }, 1500);
});

setTimeout(() => process.exit(0), 10000);