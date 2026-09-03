// jsdom 验证 v82-fix30 idx + 节点详情
const fs = require('fs');
const { JSDOM, ResourceLoader, VirtualConsole } = require('jsdom');

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
      const idx = window.buildItemIndex();
      const paths = [
        '水产动物及其制品|鲜、冻水产动物|鱼类|非肉食性鱼类',
        '水产动物及其制品|鲜、冻水产动物|鱼类',
        '水产动物及其制品|鲜、冻水产动物',
        '坚果及籽类|生干坚果及籽类（不包括谷物种子和豆类，包括咖啡豆、可可豆）',
      ];
      for (const p of paths) {
        const items = idx.get(p) || [];
        console.log(`\nidx["${p}"]: ${items.length} 条`);
        for (const it of items) {
          console.log(`  - ${it._contaminant || it.pollutant} | ${it.food} | ${it.limit_value || it.limit}`);
        }
      }
    } catch (e) {
      console.error('执行出错:', e.message, e.stack);
    }
  }, 1500);
});

setTimeout(() => process.exit(0), 10000);
