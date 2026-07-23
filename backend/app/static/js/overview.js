// Global Variables for Overview (token is already declared in base.html)
let currentOverviewStats = {};
let globalPersons = [];
let globalPersonsMap = {};

let dinoImgMap = {};
let dinoMap = {};
let moodTipMap = {};

let currentPeriodReviews = {};
let currentActivePeriod = 'week';
let currentCategorySummaries = [];
let currentActiveCategoryUuid = null;

const fallbackDinos = [
    { id: 1, legacy_key: 'Triceratops', name: '快乐三角龙', mood_label: '😊 开心', image_url: 'mood_triceratops.png', mood_tip: '快乐是会传染的，今天也要开心哦！' },
    { id: 2, legacy_key: 'Pterodactyl_happy', name: '冲天翼手龙', mood_label: '🤩 兴奋', image_url: 'mood_pterodactyl_happy.png', mood_tip: '有什么新鲜好玩的事？快跟好朋友分享吧！' },
    { id: 3, legacy_key: 'T-Rex_proud', name: '挺胸霸王龙', mood_label: '😎 得意', image_url: 'mood_t_rex_proud.png', mood_tip: '真棒！为你感到骄傲！继续加油！' },
    { id: 4, legacy_key: 'Brachiosaurus', name: '大眼睛雷龙', mood_label: '🌟 期待', image_url: 'mood_brachiosaurus.png', mood_tip: '满怀期待地迎接新的一天，好运正在路上！' },
    { id: 5, legacy_key: 'Stegosaurus', name: '呆呆剑龙', mood_label: '😮 惊讶', image_url: 'mood_stegosaurus.png', mood_tip: '哇！世界真奇妙，今天又发现了什么新奇事？' },
    { id: 6, legacy_key: 'Velociraptor', name: '佛系迅猛龙', mood_label: '😐 一般', image_url: 'mood_velociraptor.png', mood_tip: '平静的一天，吹吹风晒晒太阳也挺不错。' },
    { id: 7, legacy_key: 'Ankylosaurus_scared', name: '缩壳甲龙', mood_label: '😰 紧张', image_url: 'mood_ankylosaurus_scared.png', mood_tip: '别害怕，抱抱自己，或者找爸爸妈妈聊聊。' },
    { id: 8, legacy_key: 'Pachycephalosaurus', name: '叹气肿头龙', mood_label: '🍃 遗憾', image_url: 'mood_pachycephalosaurus.png', mood_tip: '没关系，轻轻叹口气，把不开心都吹走吧。' },
    { id: 9, legacy_key: 'Parasaurolophus_regret', name: '耷拉角副栉龙', mood_label: '😣 后悔', image_url: 'mood_parasaurolophus_regret.png', mood_tip: '每个人都会做错事，吸取教训下次会更好。' },
    { id: 10, legacy_key: 'Spinosaurus', name: '细雨棘龙', mood_label: '😭 伤心', image_url: 'mood_spinosaurus.png', mood_tip: '难过的时候可以哭出来，泪水会洗去阴霾。' },
    { id: 11, legacy_key: 'Dilophosaurus', name: '怒火双脊龙', mood_label: '😡 愤怒', image_url: 'mood_dilophosaurus.png', mood_tip: '深呼吸，慢慢吐气，褶伞张开，把肚子里的火喷出来！' }
];

async function fetchDinoConfig() {
    try {
        const authToken = typeof token !== 'undefined' ? token : (localStorage.getItem('token') || '');
        const res = await fetch('/api/dino/config', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (res.ok) {
            const list = await res.json();
            populateMaps(list);
        } else {
            throw new Error("API failed");
        }
    } catch (e) {
        console.warn("fetchDinoConfig failed, using fallback:", e);
        populateMaps(fallbackDinos);
    }
}

function populateMaps(list) {
    dinoImgMap = {};
    dinoMap = {};
    moodTipMap = {};
    list.forEach(item => {
        dinoImgMap[item.id] = item.image_url;
        dinoMap[item.id] = `${item.mood_label} ${item.name}`;
        moodTipMap[item.id] = item.mood_tip;
    });
}

async function initOverviewPage() {
    try {
        await fetchDinoConfig();
        await fetchPersons();
        await updateOverview();
    } catch (e) {
        console.error("Failed to initialize overview page", e);
    }
}

async function fetchPersons() {
    try {
        const authToken = typeof token !== 'undefined' ? token : (localStorage.getItem('token') || '');
        const res = await fetch('/api/persons/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + authToken
            },
            body: JSON.stringify({ persons: [], deleted_uuids: [] })
        });
        if (res.ok) {
            globalPersons = await res.json();
            globalPersonsMap = {};
            globalPersons.forEach(p => {
                globalPersonsMap[p.uuid] = p;
            });
        }
    } catch (e) {
        console.error("Failed to load persons", e);
    }
}

function showLogDetail(logUuid) {
    window.location.href = `/diary/detail?uuid=${logUuid}`;
}

async function updateOverview() {
    try {
        const authToken = typeof token !== 'undefined' ? token : (localStorage.getItem('token') || '');
        const res = await fetch('/api/logs/stats/overview', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (!res.ok) {
            console.error("API overview failed with status:", res.status);
            return;
        }
        const stats = await res.json();
        console.log("Overview stats received:", stats);
        currentOverviewStats = stats;

        // A. Render 板块 1: 蛋能量
        if (stats.egg_energy) {
            renderEggEnergy(stats.egg_energy);
        }

        // B. Render 板块 2: 时光机
        if (stats.period_reviews) {
            currentPeriodReviews = stats.period_reviews;
            renderPeriodReview();
        }

        // C. Render 板块 3: 日记中的 ta
        if (stats.category_summaries) {
            currentCategorySummaries = stats.category_summaries;
            if (currentCategorySummaries.length > 0) {
                currentActiveCategoryUuid = currentCategorySummaries[0].uuid;
            }
            renderCategoryPersons();
        }

    } catch (e) {
        console.error("Failed to load dashboard overview data", e);
    }
}

window.showEggEnergyHelp = function() {
    const modal = document.getElementById('eggEnergyHelpModal');
    if (modal) modal.style.display = 'flex';
};

function renderEggEnergy(data) {
    const balanceEl = document.getElementById('eggEnergyBalance');
    let bal = data.balance;
    if (!bal) {
        const navEl = document.getElementById('navEggEnergy');
        if (navEl && navEl.textContent && parseInt(navEl.textContent) > 0) {
            bal = parseInt(navEl.textContent);
        }
    }
    if (balanceEl) balanceEl.textContent = bal || 0;
    
    const todayEl = document.getElementById('deltaToday');
    if (todayEl) todayEl.textContent = `+${data.today || 0} ⚡`;
    
    const weekEl = document.getElementById('deltaThisWeek');
    if (weekEl) weekEl.textContent = `+${data.this_week || 0} ⚡`;
    
    const lastWeekEl = document.getElementById('deltaLastWeek');
    if (lastWeekEl) lastWeekEl.textContent = `+${data.last_week || 0} ⚡`;
    
    const monthEl = document.getElementById('deltaThisMonth');
    if (monthEl) monthEl.textContent = `+${data.this_month || 0} ⚡`;
}

window.switchPeriodTab = function(periodKey) {
    currentActivePeriod = periodKey;
    const btnIds = {
        'week': 'pTab-week',
        'month': 'pTab-month',
        'last_month': 'pTab-last_month',
        'year': 'pTab-year'
    };
    Object.keys(btnIds).forEach(k => {
        const btn = document.getElementById(btnIds[k]);
        if (btn) {
            if (k === periodKey) {
                btn.style.background = 'var(--accent-sunny, #f59e0b)';
                btn.style.color = 'var(--bg-main, #111)';
            } else {
                btn.style.background = 'transparent';
                btn.style.color = 'var(--text-muted)';
            }
        }
    });
    renderPeriodReview();
};

function renderPeriodReview() {
    const data = currentPeriodReviews[currentActivePeriod];
    if (!data) return;

    const dateRangeEl = document.getElementById('periodDateRange');
    if (dateRangeEl) dateRangeEl.textContent = `📅 周期范围: ${data.date_range_str || ''}`;

    const countEl = document.getElementById('periodLogCount');
    if (countEl) countEl.textContent = `${data.count || 0} 篇`;
    
    const diffEl = document.getElementById('periodLogDiff');
    if (diffEl) {
        const diffVal = data.diff || 0;
        if (diffVal > 0) {
            diffEl.textContent = `(比上期 +${diffVal} 📈)`;
            diffEl.style.color = '#22c55e';
        } else if (diffVal < 0) {
            diffEl.textContent = `(比上期 ${diffVal} 📉)`;
            diffEl.style.color = '#ef4444';
        } else {
            diffEl.textContent = '(与上期持平)';
            diffEl.style.color = 'var(--text-muted)';
        }
    }

    const pcts = data.mood_percentages || [0, 0, 0];
    const high = pcts[0] || 0;
    const mid = pcts[1] || 0;
    const low = pcts[2] || 0;

    const barHigh = document.getElementById('moodBarHigh');
    const barMid = document.getElementById('moodBarMid');
    const barLow = document.getElementById('moodBarLow');
    if (barHigh) barHigh.style.width = `${high}%`;
    if (barMid) barMid.style.width = `${mid}%`;
    if (barLow) barLow.style.width = `${low}%`;

    const pctHighEl = document.getElementById('pctHigh');
    const pctMidEl = document.getElementById('pctMid');
    const pctLowEl = document.getElementById('pctLow');
    if (pctHighEl) pctHighEl.textContent = `${high}%`;
    if (pctMidEl) pctMidEl.textContent = `${mid}%`;
    if (pctLowEl) pctLowEl.textContent = `${low}%`;

    // Render Top 3 Persons
    const container = document.getElementById('periodTopPersonsContainer');
    if (container) {
        container.innerHTML = '';

        const topList = data.top_persons || [];
        if (topList.length === 0) {
            container.innerHTML = `
                <div style="grid-column: span 3; font-size: 0.75rem; color: var(--text-muted); font-family: monospace; text-align: center; padding: 16px;">
                    本周期还没有写过小伙伴呢 🦖
                </div>
            `;
            return;
        }

        const rankColors = ['#f59e0b', '#3b82f6', '#22c55e'];
        topList.forEach((item, idx) => {
            const color = rankColors[idx] || '#22c55e';
            const card = document.createElement('div');
            card.style = `background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; font-family: monospace;`;
            card.innerHTML = `
                <div style="width: 18px; height: 18px; border-radius: 50%; background: ${color}20; color: ${color}; font-size: 0.65rem; font-weight: bold; display: flex; align-items: center; justify-content: center;">${idx + 1}</div>
                <div style="font-size: 0.75rem; font-weight: bold; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%;">${item.name}</div>
                <div style="font-size: 0.65rem; color: var(--text-muted);">提及 ${item.count} 次</div>
            `;
            container.appendChild(card);
        });
    }
}

window.switchCategoryTab = function(catUuid) {
    currentActiveCategoryUuid = catUuid;
    renderCategoryPersons();
};

function renderCategoryPersons() {
    const tabsContainer = document.getElementById('categoryTabsContainer');
    const personsContainer = document.getElementById('categoryPersonsContainer');

    if (!tabsContainer || !personsContainer) return;

    tabsContainer.innerHTML = '';
    personsContainer.innerHTML = '';

    if (!currentCategorySummaries || currentCategorySummaries.length === 0) {
        personsContainer.innerHTML = `
            <div style="font-size: 0.8rem; color: var(--text-muted); font-family: monospace; text-align: center; padding: 30px;">
                🌴 还没有创建任何关系人分类哦
            </div>
        `;
        return;
    }

    // Render Tabs
    currentCategorySummaries.forEach(cat => {
        const isSelected = cat.uuid === currentActiveCategoryUuid;
        const btn = document.createElement('button');
        btn.style = `background: ${isSelected ? 'var(--accent-sunny, #f59e0b)' : 'var(--card-bg)'}; color: ${isSelected ? 'var(--bg-main, #111)' : 'var(--text-muted)'}; border: 1px solid var(--card-border); padding: 4px 12px; border-radius: 10px; font-size: 0.75rem; font-weight: bold; cursor: pointer; white-space: nowrap; font-family: monospace; transition: all 0.2s;`;
        btn.textContent = `${cat.name} (${cat.persons ? cat.persons.length : 0})`;
        btn.onclick = () => switchCategoryTab(cat.uuid);
        tabsContainer.appendChild(btn);
    });

    // Render Persons list under active category
    const activeCat = currentCategorySummaries.find(c => c.uuid === currentActiveCategoryUuid) || currentCategorySummaries[0];
    if (!activeCat || !activeCat.persons || activeCat.persons.length === 0) {
        personsContainer.innerHTML = `
            <div style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace; text-align: center; padding: 24px; background: var(--card-bg); border-radius: 12px; border: 1px dashed var(--card-border);">
                该分类下暂无小伙伴，可在关系人管理中添加哦
            </div>
        `;
        return;
    }

    activeCat.persons.forEach(p => {
        const item = document.createElement('div');
        item.style = `background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; font-family: monospace;`;
        
        const initial = p.name ? p.name.charAt(0) : '👤';
        
        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: var(--text-main); font-weight: bold; font-size: 0.8rem; display: flex; align-items: center; justify-content: center;">${initial}</div>
                <div>
                    <div style="font-size: 0.8rem; font-weight: bold; color: var(--text-main);">${p.name}</div>
                    <div style="font-size: 0.65rem; color: var(--text-muted);">📝 记录了 ${p.diary_count || 0} 篇日记</div>
                </div>
            </div>
            <div style="display: flex; gap: 6px; align-items: center;">
                ${p.happy_count > 0 ? `<span style="font-size: 0.7rem; background: rgba(34,197,94,0.12); color: #22c55e; border: 1px solid rgba(34,197,94,0.25); padding: 2px 6px; border-radius: 6px; font-weight: bold;">😊 ${p.happy_count}</span>` : ''}
                ${p.calm_count > 0 ? `<span style="font-size: 0.7rem; background: rgba(59,130,246,0.12); color: #3b82f6; border: 1px solid rgba(59,130,246,0.25); padding: 2px 6px; border-radius: 6px; font-weight: bold;">😐 ${p.calm_count}</span>` : ''}
                ${p.sad_count > 0 ? `<span style="font-size: 0.7rem; background: rgba(239,68,68,0.12); color: #ef4444; border: 1px solid rgba(239,68,68,0.25); padding: 2px 6px; border-radius: 6px; font-weight: bold;">😢 ${p.sad_count}</span>` : ''}
                ${(p.happy_count === 0 && p.calm_count === 0 && p.sad_count === 0) ? `<span style="font-size: 0.65rem; color: var(--text-muted);">暂无心情</span>` : ''}
            </div>
        `;
        personsContainer.appendChild(item);
    });
}

// Start Initialization
initOverviewPage();
