// 截图辅助：注入自动切 tab / 开弹窗 的脚本
const fs = require('fs');
const path = require('path');
const D = __dirname;

const mode = process.argv[2] || 'cat';   // cat | modal | submodal
const src = fs.readFileSync(path.join(D, 'gb2760.html'), 'utf8');

let inject = '';
if (mode === 'cat') {
  inject = `<script>
  window.addEventListener('load', () => setTimeout(() => {
    document.querySelector('.tab[data-tab="by-category"]').click();
  }, 800));
  </script>`;
} else if (mode === 'modal') {
  inject = `<script>
  window.addEventListener('load', () => setTimeout(() => {
    document.querySelector('.tab[data-tab="by-category"]').click();
    setTimeout(() => document.querySelector('.hero-card[data-code="01.0"]').click(), 400);
  }, 800));
  </script>`;
} else if (mode === 'submodal') {
  inject = `<script>
  window.addEventListener('load', () => setTimeout(() => {
    document.querySelector('.tab[data-tab="by-category"]').click();
    setTimeout(() => {
      document.querySelector('.hero-card[data-code="01.0"]').click();
      setTimeout(() => {
        const t = document.querySelector('.sub-card[data-code="01.02.02"]');
        if (t) t.click();
      }, 400);
    }, 400);
  }, 800));
  </script>`;
} else if (mode === 'additive') {
  inject = `<script>
  window.addEventListener('load', () => setTimeout(() => {
    document.querySelector('.tab[data-tab="by-additive"]').click();
    setTimeout(() => document.querySelector('#addList .add-card').click(), 400);
  }, 800));
  </script>`;
}

fs.writeFileSync(path.join(D, '_shot_tmp.html'), src.replace('</body>', inject + '</body>'));
console.log('[OK] 已生成 _shot_tmp.html mode=' + mode);
