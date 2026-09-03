// v82-fix30 jsdom 验证 - 取消「上一级」段，改 ancestor 分层
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
      const testPaths = [
        // 用户的截图: 腌制水产品 (L3, idx 空)
        ['水产动物及其制品', '水产制品', '腌制水产品'],
        // 用户曾经反馈的: 鱼糜制品 (L3, idx 空)
        ['水产动物及其制品', '水产制品', '鱼糜制品（例如：鱼丸等）'],
        // 用户最早反馈的: 非肉食性鱼类 (L4, idx 非空)
        ['水产动物及其制品', '鲜、冻水产动物', '鱼类', '非肉食性鱼类'],
        // idx 非空本级: 坚果及籽类 (L2, idx 命中)
        ['坚果及籽类', '生干坚果及籽类（不包括谷物种子和豆类，包括咖啡豆、可可豆）'],
        // idx 空本级: 蔬菜泥 (L3)
        ['蔬菜及其制品（包括薯类，不包括食用菌）', '蔬菜制品', '蔬菜泥（酱）'],
        // L1 通类项: 鱼糜制品 (idx 空) 上一级从 L2 开始
        ['水产动物及其制品', '水产制品', '鱼糜制品（例如：鱼丸等）'],
      ];
      for (const tp of testPaths) {
        window.selectTreeNode(tp);
        const tc = window.document.getElementById('treeContent');
        console.log(`\n=== ${tp.join(' > ')} ===`);
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
      }
    } catch (e) {
      console.error('执行出错:', e.message, e.stack);
    }
  }, 1500);
});

setTimeout(() => process.exit(0), 12000);
