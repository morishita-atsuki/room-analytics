let shopData = null;
let rawData = null;

// Fetch and process room_data.json
async function loadData() {
  try {
    const response = await fetch('room_data.json');
    rawData = await response.json();
    
    // Build shopData from room_data.json
    shopData = buildShopData(rawData);
    bootstrap();
  } catch (error) {
    console.error('Failed to load room_data.json:', error);
    // Fallback to empty data
    shopData = buildShopData({ meta: {}, summary: {}, posts: [], items: [], users: [], by_day: [] });
    bootstrap();
  }
}

// Build shopData structure from raw data
function buildShopData(data) {
  const meta = data.meta || {};
  const summary = data.summary || {};
  const posts = data.posts || [];
  const items = data.items || [];
  const users = data.users || [];
  const byDay = data.by_day || [];

  // Calculate KPIs
  const avgLikes = summary.posts > 0 ? Math.round(summary.likes / summary.posts) : 0;
  const commentRecollect = `${summary.comments || 0} / ${summary.recollects || 0}`;

  // Build daily data from by_day
  const daily = byDay.slice(-6).map(d => ({
    label: d.day.slice(5),
    posts: d.n || 0,
    likes: d.likes || 0,
  }));

  // Build share data (top items)
  const share = items.slice(0, 5).map(item => ({
    label: item.item_short || item.item_name,
    value: items.length > 0 ? Math.round(item.posts / items.reduce((a, b) => a + (b.posts || 0), 0) * 100) : 0,
  }));

  // Build efficiency data
  const efficiency = items.slice(0, 5).map(item => ({
    label: item.item_short || item.item_name,
    value: Math.round(item.likes_per_post || 0),
  }));

  // Build trend data (weekday)
  const trend = [
    { label: '月', value: 0 },
    { label: '火', value: 0 },
    { label: '水', value: 0 },
    { label: '木', value: 0 },
    { label: '金', value: 0 },
    { label: '土', value: 0 },
    { label: '日', value: 0 },
  ];
  
  byDay.forEach(d => {
    const date = new Date(d.day + 'T00:00:00Z');
    const dayOfWeek = date.getUTCDay();
    const idx = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    trend[idx].value += (d.likes || 0);
  });
  
  if (trend.some(t => t.value > 0)) {
    const maxVal = Math.max(...trend.map(t => t.value));
    trend.forEach(t => t.value = maxVal > 0 ? Math.round(t.value / maxVal * 100) : 0);
  }

  return {
    shopName: meta.shop_name || 'Shop',
    shopCode: meta.shop_code || '',
    updatedAt: meta.generated_at || '',
    kpis: [
      { label: '総投稿数', value: `${summary.posts || 0} 件` },
      { label: '総いいね数', value: summary.likes || 0 },
      { label: '平均いいね/投稿', value: avgLikes },
      { label: '投稿者数', value: `${summary.users || 0} 人` },
      { label: '商品数', value: `${summary.items || 0} 点` },
      { label: 'コメント/リコレクト', value: commentRecollect },
    ],
    daily,
    share,
    efficiency,
    products: items,
    users,
    posts,
    trend,
  };
}

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
  const summary = rawData?.summary || {};
  funnel.innerHTML = [
    { title: '露出', value: `${summary.posts || 0} 投稿` },
    { title: '関心', value: `${summary.likes || 0} いいね` },
    { title: '拡散', value: `${summary.recollects || 0} リコレクト` },
  ].map((step) => `
    <div class="step">
      <strong>${step.title}</strong>
      <div>${step.value}</div>
    </div>
  `).join('');
}

function renderProducts() {
  const productList = document.getElementById('productList');
  const products = shopData.products.slice(0, 8).map((product) => ({
    name: product.item_short || product.item_name,
    posts: product.posts || 0,
    likes: product.likes || 0,
    efficiency: Math.round(product.likes_per_post || 0),
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
  const users = shopData.users.slice(0, 8).map((user) => ({
    name: user.username || user.name,
    posts: user.posts || 0,
    likes: user.total_likes || user.likes || 0,
  }));
  userList.innerHTML = users.map((user) => `
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
  const posts = shopData.posts.slice(0, 8).map((post) => ({
    title: post.item_short || post.item_name || post.title || '',
    likes: post.likes || 0,
    date: post.created_at ? post.created_at.slice(5, 10) : post.date || '',
  }));
  postList.innerHTML = posts.map((post) => `
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
  if (!shopData) return; // Wait for data to load
  
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

window.addEventListener('DOMContentLoaded', () => {
  loadData(); // 初回読み込み
  // 1時間ごとに自動更新
  setInterval(loadData, 3600000); // 3600000ms = 1時間
});
