const shopData = {
  shopName: 'さくらマーケット楽天市場店',
  shopCode: 'sakura-market-rakuten',
  updatedAt: '2026-06-29 19:00',
  targetProducts: ['リノクル','ビタスポットセラム','マイシースキニティジェルバームクレンジング','ビアス','ハーブラピール','レチノソームショット','ホワイトプラス','ハーバニエンス'],
  kpis: [
    { label: '総投稿数', value: '1,248 件' },
    { label: '総いいね数', value: '24,180' },
    { label: '平均いいね/投稿', value: '19' },
    { label: '投稿者数', value: '912 人' },
    { label: '商品数', value: '14 点' },
    { label: 'コメント/リコレクト', value: '132 / 158' },
  ],
  daily: [
    { label: '6/23', posts: 36, likes: 410 },
    { label: '6/24', posts: 44, likes: 510 },
    { label: '6/25', posts: 52, likes: 620 },
    { label: '6/26', posts: 58, likes: 760 },
    { label: '6/27', posts: 63, likes: 820 },
    { label: '6/28', posts: 71, likes: 910 },
  ],
  share: [
    { label: '桜あんみつ', value: 28 },
    { label: '季節の和菓子詰合せ', value: 22 },
    { label: '抹茶白玉', value: 17 },
    { label: '桜餅セット', value: 13 },
    { label: '和菓子ギフト', value: 10 },
  ],
  efficiency: [
    { label: '桜あんみつ', value: 24 },
    { label: '季節の和菓子詰合せ', value: 20 },
    { label: '抹茶白玉', value: 18 },
    { label: '桜餅セット', value: 16 },
    { label: '和菓子ギフト', value: 12 },
  ],
  products: [
    { name: '桜あんみつ', posts: 142, likes: 3,420, efficiency: 24 },
    { name: '季節の和菓子詰合せ', posts: 118, likes: 2,760, efficiency: 23 },
    { name: '抹茶白玉', posts: 96, likes: 1,920, efficiency: 20 },
    { name: '桜餅セット', posts: 84, likes: 1,520, efficiency: 18 },
  ],
  users: [
    { name: 'miyako_28', posts: 48, likes: 1,100 },
    { name: 'sakura_bean', posts: 41, likes: 910 },
    { name: 'haru_shop', posts: 36, likes: 780 },
    { name: 'yamae', posts: 31, likes: 690 },
  ],
  posts: [
    { title: '春限定の桜あんみつを紹介', likes: 168, date: '6/28' },
    { title: '和菓子詰合せの見栄えが良い点', likes: 142, date: '6/27' },
    { title: '抹茶白玉の食感を再現したい', likes: 121, date: '6/26' },
  ],
  trend: [
    { label: '月', value: 65 },
    { label: '火', value: 72 },
    { label: '水', value: 88 },
    { label: '木', value: 95 },
    { label: '金', value: 110 },
    { label: '土', value: 124 },
    { label: '日', value: 132 },
  ],
};

const navItems = document.querySelectorAll('.nav-item');
const tabs = document.querySelectorAll('.tab');

navItems.forEach((item) => {
  item.addEventListener('click', () => {
    navItems.forEach((nav) => nav.classList.remove('on'));
    tabs.forEach((tab) => tab.classList.remove('on'));
    item.classList.add('on');
    const targetId = item.dataset.target;
    document.querySelector(`#tab-${targetId}`).classList.add('on');
    document.getElementById('section-title').textContent = item.textContent.trim().replace(/▤|◎|▣|◍|≣|↗/g, '').trim();
  });
});

function buildTimeframeData() {
  return {
    hour: [
      { label: '00-06', posts: 18, likes: 210 },
      { label: '06-12', posts: 42, likes: 540 },
      { label: '12-18', posts: 68, likes: 830 },
      { label: '18-24', posts: 54, likes: 690 },
    ],
    day: [
      { label: '6/23', posts: 28, likes: 320 },
      { label: '6/24', posts: 35, likes: 420 },
      { label: '6/25', posts: 42, likes: 510 },
      { label: '6/26', posts: 53, likes: 640 },
      { label: '6/27', posts: 61, likes: 730 },
      { label: '6/28', posts: 70, likes: 820 },
    ],
    month: [
      { label: '2025/11', posts: 80, likes: 720 },
      { label: '2025/12', posts: 110, likes: 980 },
      { label: '2026/01', posts: 140, likes: 1240 },
      { label: '2026/02', posts: 180, likes: 1580 },
      { label: '2026/03', posts: 220, likes: 1910 },
      { label: '2026/04', posts: 260, likes: 2250 },
      { label: '2026/05', posts: 310, likes: 2640 },
      { label: '2026/06', posts: 350, likes: 3010 },
    ],
  };
}

function renderOverview() {
  const kpis = document.getElementById('kpis');
  kpis.innerHTML = shopData.kpis.map((item) => `
    <div class="kpi-card">
      <div class="label">${item.label}</div>
      <div class="value">${item.value}</div>
    </div>
  `).join('');

  const dailyChart = document.getElementById('dailyChart');
  dailyChart.innerHTML = shopData.daily.map((item) => `
    <div class="chart-row">
      <div>${item.label}</div>
      <div class="bar posts"><span style="width:${Math.min(100, item.posts * 1.4)}%"></span></div>
      <div class="value">${item.posts}</div>
      <div class="bar likes"><span style="width:${Math.min(100, item.likes / 10)}%"></span></div>
      <div class="value">${item.likes}</div>
    </div>
  `).join('');

  const shareChart = document.getElementById('shareChart');
  shareChart.innerHTML = shopData.share.map((item) => `
    <div class="chart-row">
      <div>${item.label}</div>
      <div class="bar posts"><span style="width:${item.value}%"></span></div>
      <div class="value">${item.value}%</div>
    </div>
  `).join('');

  const efficiencyChart = document.getElementById('efficiencyChart');
  efficiencyChart.innerHTML = shopData.efficiency.map((item) => `
    <div class="chart-row">
      <div>${item.label}</div>
      <div class="bar posts"><span style="width:${item.value * 4}%"></span></div>
      <div class="value">${item.value}</div>
    </div>
  `).join('');
}

function renderInfluence() {
  const funnel = document.getElementById('funnel');
  funnel.innerHTML = [
    { title: '露出', value: '1,248 投稿' },
    { title: '関心', value: '24,180 いいね' },
    { title: '拡散', value: '158 リコレクト' },
  ].map((step) => `
    <div class="step">
      <strong>${step.title}</strong>
      <div>${step.value}</div>
    </div>
  `).join('');
}

function renderProducts() {
  const productList = document.getElementById('productList');
  const products = shopData.targetProducts.map((name, index) => ({
    name,
    posts: 18 + index * 6,
    likes: 220 + index * 80,
    efficiency: 12 + index * 2,
  }));
  productList.innerHTML = products.map((product) => `
    <div class="item-row">
      <div>
        <div><strong>${product.name}</strong></div>
        <div class="meta-small">投稿 ${product.posts}件 / いいね ${product.likes}</div>
      </div>
      <div class="meta-small">効率 ${product.efficiency}</div>
    </div>
  `).join('');
}

function renderUsers() {
  const userList = document.getElementById('userList');
  userList.innerHTML = shopData.users.map((user) => `
    <div class="item-row">
      <div>
        <div><strong>${user.name}</strong></div>
        <div class="meta-small">投稿 ${user.posts}件</div>
      </div>
      <div class="meta-small">いいね ${user.likes}</div>
    </div>
  `).join('');
}

function renderPosts() {
  const postList = document.getElementById('postList');
  postList.innerHTML = shopData.posts.map((post) => `
    <div class="item-row">
      <div>
        <div><strong>${post.title}</strong></div>
        <div class="meta-small">${post.date}</div>
      </div>
      <div class="meta-small">いいね ${post.likes}</div>
    </div>
  `).join('');
}

function renderTrend() {
  const trendBars = document.getElementById('trendBars');
  trendBars.innerHTML = shopData.trend.map((item) => `
    <div class="bar-col">
      <div class="fill" style="height:${item.value}%"></div>
      <div class="label">${item.label}</div>
    </div>
  `).join('');
}

function bootstrap() {
  document.getElementById('shopName').textContent = shopData.shopName;
  document.getElementById('shopCode').textContent = shopData.shopCode;
  document.getElementById('updatedAt').textContent = shopData.updatedAt;
  document.getElementById('footerUpdated').textContent = shopData.updatedAt;

  renderOverview();
  renderInfluence();
  renderProducts();
  renderUsers();
  renderPosts();
  renderTrend();
}

window.addEventListener('DOMContentLoaded', bootstrap);
