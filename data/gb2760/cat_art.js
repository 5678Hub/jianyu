// GB 2760 分类配图：16 个一级分类各一张内联 SVG 插画
// 说明：全部手写 path，无外部依赖，离线可用；配色按食品属性区分
window.CAT_ART = {
  "01.0": { bg: ["#e8f2fb", "#c9dff5"], ink: "#2c5282", art: `
    <path d="M52 26 h16 a5 5 0 0 1 5 5 v34 a5 5 0 0 1 -5 5 h-16 a5 5 0 0 1 -5 -5 v-34 a5 5 0 0 1 5 -5z" fill="#fff" stroke="#2c5282" stroke-width="2.4"/>
    <path d="M48 26 h24 v-8 h-24z" fill="#2c5282"/>
    <path d="M53 14 h14 v4 h-14z" fill="#2c5282"/>
    <path d="M47 42 h26 v20 h-26z" fill="#e8f2fb"/>
    <circle cx="60" cy="52" r="6" fill="#fff" stroke="#2c5282" stroke-width="1.6"/>` },

  "02.0": { bg: ["#fff4e0", "#f8dcb0"], ink: "#9a6b1f", art: `
    <path d="M56 22 h8 v8 c8 4 12 12 12 22 v14 a4 4 0 0 1 -4 4 h-24 a4 4 0 0 1 -4 -4 v-14 c0 -10 4 -18 12 -22z" fill="#fff" stroke="#9a6b1f" stroke-width="2.4"/>
    <path d="M58 14 h4 v9 h-4z" fill="#9a6b1f"/>
    <path d="M48 52 h24 v14 h-24z" fill="#f5c33b"/>
    <ellipse cx="60" cy="20" rx="7" ry="3" fill="#e8a33d"/>` },

  "03.0": { bg: ["#e6f6fb", "#bfe8f5"], ink: "#1c7a9c", art: `
    <path d="M46 42 h28 l-14 30z" fill="#e8b06a" stroke="#1c7a9c" stroke-width="2.4" stroke-linejoin="round"/>
    <path d="M46 42 h28" stroke="#1c7a9c" stroke-width="2.4"/>
    <circle cx="49" cy="34" r="8" fill="#f7a8bd" stroke="#1c7a9c" stroke-width="2"/>
    <circle cx="71" cy="34" r="8" fill="#f7c9a0" stroke="#1c7a9c" stroke-width="2"/>
    <circle cx="60" cy="26" r="10" fill="#fff3e0" stroke="#1c7a9c" stroke-width="2.2"/>
    <path d="M53 56 l4 8 M67 56 l-4 8" stroke="#c98a4b" stroke-width="1.6"/>` },

  "04.0": { bg: ["#eaf7ec", "#c8e9ce"], ink: "#2f7d43", art: `
    <circle cx="42" cy="40" r="15" fill="#e35d5d" stroke="#2f7d43" stroke-width="2.4"/>
    <path d="M42 25 c0 -6 4 -10 10 -11 c0 6 -4 10 -10 11z" fill="#4aa05e" stroke="#2f7d43" stroke-width="1.8"/>
    <path d="M78 34 c7 -4 14 -1 14 7 c0 10 -10 18 -10 18 s-8 -9 -8 -17 c0 -4 1 -6 4 -8z" fill="#f0a03c" stroke="#2f7d43" stroke-width="2.2"/>
    <path d="M76 30 c3 -5 8 -7 13 -5" stroke="#2f7d43" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M26 66 h68" stroke="#8a6b45" stroke-width="4" stroke-linecap="round"/>
    <ellipse cx="30" cy="34" rx="8" ry="11" fill="#7bbd6a" stroke="#2f7d43" stroke-width="2"/>` },

  "05.0": { bg: ["#f6ecfa", "#ddc4ee"], ink: "#6b3f8f", art: `
    <circle cx="60" cy="45" r="19" fill="#c07ad8" stroke="#6b3f8f" stroke-width="2.4"/>
    <path d="M46 32 c-6 -3 -10 2 -7 7 c2 4 7 5 11 3z" fill="#eeb4e2" stroke="#6b3f8f" stroke-width="2" stroke-linejoin="round"/>
    <path d="M74 32 c6 -3 10 2 7 7 c-2 4 -7 5 -11 3z" fill="#d4a8e8" stroke="#6b3f8f" stroke-width="2" stroke-linejoin="round"/>
    <path d="M52 66 h16 v12 h-16z" fill="#8a5a30" stroke="#6b3f8f" stroke-width="2" stroke-linejoin="round"/>
    <path d="M60 30 c-3 5 -3 11 0 15" stroke="#8a4f9e" stroke-width="1.8" fill="none" stroke-linecap="round"/>` },

  "06.0": { bg: ["#fdf6e3", "#f3e2b3"], ink: "#8a6d1f", art: `
    <path d="M60 20 v52" stroke="#8a6d1f" stroke-width="2.6" stroke-linecap="round"/>
    <path d="M60 28 c-6 -6 -12 -5 -13 -1 c7 1 10 4 13 8z" fill="#d9b352" stroke="#8a6d1f" stroke-width="1.7"/>
    <path d="M60 28 c6 -6 12 -5 13 -1 c-7 1 -10 4 -13 8z" fill="#d9b352" stroke="#8a6d1f" stroke-width="1.7"/>
    <path d="M60 42 c-6 -6 -12 -5 -13 -1 c7 1 10 4 13 8z" fill="#d9b352" stroke="#8a6d1f" stroke-width="1.7"/>
    <path d="M60 42 c6 -6 12 -5 13 -1 c-7 1 -10 4 -13 8z" fill="#d9b352" stroke="#8a6d1f" stroke-width="1.7"/>
    <path d="M60 56 c-6 -6 -12 -5 -13 -1 c7 1 10 4 13 8z" fill="#d9b352" stroke="#8a6d1f" stroke-width="1.7"/>
    <path d="M60 56 c6 -6 12 -5 13 -1 c-7 1 -10 4 -13 8z" fill="#d9b352" stroke="#8a6d1f" stroke-width="1.7"/>
    <path d="M44 72 h32 l-4 8 h-24z" fill="#c9a961" stroke="#8a6d1f" stroke-width="2" stroke-linejoin="round"/>` },

  "07.0": { bg: ["#fdf0e0", "#f2d2a8"], ink: "#a35d21", art: `
    <path d="M34 44 c0 -10 10 -16 26 -16 s26 6 26 16 v18 h-52z" fill="#dba25c" stroke="#a35d21" stroke-width="2.4" stroke-linejoin="round"/>
    <path d="M34 46 h52" stroke="#a35d21" stroke-width="1.8"/>
    <path d="M50 40 c2 -4 5 -5 8 -4 M66 40 c3 -4 6 -4 9 -2" stroke="#a35d21" stroke-width="1.8" stroke-linecap="round" fill="none"/>
    <rect x="30" y="62" width="60" height="10" rx="3" fill="#b87a3d" stroke="#a35d21" stroke-width="2.2"/>` },

  "08.0": { bg: ["#fdecec", "#f6c9c9"], ink: "#a83232", art: `
    <path d="M38 42 c0 -8 8 -14 18 -14 c6 0 11 2 14 6 c7 -1 13 4 13 10 c0 7 -6 12 -14 12 h-18 c-8 0 -13 -6 -13 -14z" fill="#e08a8a" stroke="#a83232" stroke-width="2.4" stroke-linejoin="round"/>
    <path d="M46 37 c3 -3 7 -3 9 0 M64 35 c3 -3 7 -2 9 1" stroke="#a83232" stroke-width="1.9" stroke-linecap="round" fill="none"/>
    <path d="M58 36 c-2 5 -2 9 0 13" stroke="#a83232" stroke-width="1.9" fill="none" stroke-linecap="round"/>
    <rect x="40" y="58" width="38" height="17" rx="4" fill="#fff" stroke="#a83232" stroke-width="2.3"/>
    <path d="M49 66 h20" stroke="#a83232" stroke-width="2.1" stroke-linecap="round"/>
    <path d="M40 66 h-8 M78 66 h8" stroke="#a83232" stroke-width="2.1" stroke-linecap="round"/>` },

  "09.0": { bg: ["#e4f4f7", "#b9e0ea"], ink: "#1a6b7d", art: `
    <path d="M30 46 c10 -12 34 -14 46 -2 c6 6 6 14 -2 18 c-14 7 -38 3 -44 -6 c-2 -3 -1 -7 0 -10z" fill="#7cc4d6" stroke="#1a6b7d" stroke-width="2.3"/>
    <path d="M76 44 l14 -9 v22 l-12 -5z" fill="#a9dce8" stroke="#1a6b7d" stroke-width="2.2" stroke-linejoin="round"/>
    <circle cx="46" cy="47" r="3.4" fill="#1a6b7d"/>
    <path d="M56 62 c4 3 10 3 14 1 M40 60 c4 3 9 4 13 3" stroke="#1a6b7d" stroke-width="1.7" stroke-linecap="round" fill="none"/>` },

  "10.0": { bg: ["#fff9e0", "#f6e6a8"], ink: "#96701a", art: `
    <path d="M46 26 c8 0 14 7 14 16 c0 11 -8 20 -14 20 s-14 -9 -14 -20 c0 -9 6 -16 14 -16z" fill="#fff" stroke="#96701a" stroke-width="2.3"/>
    <path d="M74 30 c7 0 12 6 12 13 c0 9 -7 16 -12 16 s-12 -7 -12 -16 c0 -7 5 -13 12 -13z" fill="#fdfaf0" stroke="#96701a" stroke-width="2.1"/>
    <circle cx="52" cy="52" r="4" fill="#f0c04a"/>
    <circle cx="78" cy="52" r="3.4" fill="#f0c04a"/>` },

  "11.0": { bg: ["#fff5dc", "#f6dfa4"], ink: "#a8761a", art: `
    <path d="M44 30 h32 a4 4 0 0 1 4 4 v34 a4 4 0 0 1 -4 4 h-32 a4 4 0 0 1 -4 -4 v-34 a4 4 0 0 1 4 -4z" fill="#ffc94d" stroke="#a8761a" stroke-width="2.4"/>
    <path d="M40 30 h40 v-7 h-40z" fill="#8a6b45" stroke="#a8761a" stroke-width="2.2"/>
    <path d="M50 46 c0 4 4 4 4 8 s-4 4 -4 8 s4 4 4 7" stroke="#a8761a" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M60 16 l-4 8 h8z" fill="#f0c04a" stroke="#a8761a" stroke-width="1.8" stroke-linejoin="round"/>` },

  "12.0": { bg: ["#fdefe4", "#f3cfb0"], ink: "#8a4a1e", art: `
    <path d="M50 30 h20 v10 c6 4 10 10 10 18 v20 a4 4 0 0 1 -4 4 h-32 a4 4 0 0 1 -4 -4 v-20 c0 -8 4 -14 10 -18z" fill="#7a3a12" stroke="#8a4a1e" stroke-width="2.4" stroke-linejoin="round"/>
    <path d="M50 20 h20 v11 h-20z" fill="#c88a4a" stroke="#8a4a1e" stroke-width="2.2"/>
    <rect x="44" y="50" width="32" height="14" rx="2" fill="#f6e3c8"/>
    <path d="M48 57 h24" stroke="#8a4a1e" stroke-width="1.9" stroke-linecap="round"/>
    <path d="M60 14 c4 -4 8 -3 9 1" stroke="#8a4a1e" stroke-width="1.9" fill="none" stroke-linecap="round"/>` },

  "13.0": { bg: ["#e8f6f4", "#bfe5df"], ink: "#1f6f66", art: `
    <path d="M34 40 h52 a4 4 0 0 1 4 4 v26 a4 4 0 0 1 -4 4 h-52 a4 4 0 0 1 -4 -4 v-26 a4 4 0 0 1 4 -4z" fill="#fff" stroke="#1f6f66" stroke-width="2.4"/>
    <path d="M52 40 v-8 a8 8 0 0 1 16 0 v8" stroke="#1f6f66" stroke-width="2.4" fill="none"/>
    <path d="M48 54 l6 6 l12 -13" stroke="#2a9d8f" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M30 56 h10 M80 56 h10" stroke="#1f6f66" stroke-width="2.4" stroke-linecap="round"/>` },

  "14.0": { bg: ["#e8f4fd", "#c2dff5"], ink: "#22548f", art: `
    <path d="M42 26 h36 l-5 44 a5 5 0 0 1 -5 4 h-16 a5 5 0 0 1 -5 -4z" fill="#fff" stroke="#22548f" stroke-width="2.4" stroke-linejoin="round"/>
    <path d="M44 38 h32 l-4 30 h-24z" fill="#7cc0ea"/>
    <path d="M66 26 l10 -14" stroke="#e05a6d" stroke-width="3.4" stroke-linecap="round"/>
    <path d="M38 22 h44" stroke="#22548f" stroke-width="2.6" stroke-linecap="round"/>` },

  "15.0": { bg: ["#f7e9ef", "#e2bccd"], ink: "#7a2540", art: `
    <path d="M54 18 h12 v14 c8 4 12 12 12 22 v20 a4 4 0 0 1 -4 4 h-28 a4 4 0 0 1 -4 -4 v-20 c0 -10 4 -18 12 -22z" fill="#8b1e3f" stroke="#7a2540" stroke-width="2.4"/>
    <path d="M52 12 h16 v7 h-16z" fill="#c9a33f" stroke="#7a2540" stroke-width="2"/>
    <rect x="46" y="50" width="28" height="14" rx="2" fill="#f6e3ea"/>
    <path d="M50 57 h20" stroke="#7a2540" stroke-width="1.8" stroke-linecap="round"/>` },

  "16.0": { bg: ["#eef1f4", "#d2dae2"], ink: "#4a5b6b", art: `
    <path d="M32 42 l28 -14 l28 14 v30 l-28 14 l-28 -14z" fill="#fff" stroke="#4a5b6b" stroke-width="2.4" stroke-linejoin="round"/>
    <path d="M32 42 l28 14 l28 -14 M60 56 v30" stroke="#4a5b6b" stroke-width="2.2" fill="none"/>
    <path d="M46 35 l28 14 v-9" stroke="#4a5b6b" stroke-width="2" fill="none"/>` }
};
