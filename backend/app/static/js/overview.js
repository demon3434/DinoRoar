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
        loadDashboardPromoBanner();
    } catch (e) {
        console.error("Failed to initialize overview page", e);
    }
}

async function loadDashboardPromoBanner() {
    try {
        const res = await fetch('/api/promotions/active-summary');
        if (!res.ok) return;
        const promos = await res.json();
        const bannerEl = document.getElementById('dashboardPromoBanner');
        const titleEl = document.getElementById('dashboardPromoTitle');
        const descEl = document.getElementById('dashboardPromoDesc');
        if (bannerEl && promos && promos.length > 0) {
            const p = promos[0];
            if (titleEl) titleEl.textContent = `🎉 节日特惠：${p.name}`;
            const ruleText = (p.rules_summary && p.rules_summary.length > 0) 
                ? p.rules_summary.join(' · ') 
                : (p.description ? p.description : '手账商城贴纸、画布特惠打折中，快去选购吧！');
            if (descEl) descEl.textContent = `✨ ${ruleText}`;
            bannerEl.style.display = 'flex';
        }
    } catch (e) {

        console.error('加载看板活动横幅失败', e);
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

// ==========================================
// 蛋能量银行流水账本与电子回单逻辑 (Web PC 端)
// ==========================================
let currentLedgerFilter = 'all'; // 'all' | 'income' | 'expense'
let currentLedgerTimeRange = 'all'; // 'all' | 'today' | 'week' | 'month' | 'last_month' | 'year'
let ledgerCurrentPage = 1;
let ledgerPageSize = 20;
let ledgerTotalCount = 0;
let ledgerTotalPages = 1;
let ledgerIsLoading = false;
let currentLedgerItems = [];
let currentSelectedReceipt = null;

function openEnergyLedgerModal() {
    const modal = document.getElementById('energyLedgerModal');
    if (modal) {
        modal.style.display = 'flex';
        currentLedgerTimeRange = 'all';
        switchLedgerFilter('all');
    }
}

function closeEnergyLedgerModal() {
    const modal = document.getElementById('energyLedgerModal');
    if (modal) modal.style.display = 'none';
}

function switchLedgerFilter(type) {
    currentLedgerFilter = type;
    document.querySelectorAll('.ledger-filter-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.background = 'var(--card-bg)';
        btn.style.color = 'var(--text-muted)';
        btn.style.borderColor = 'var(--card-border)';
    });

    const activeMap = {
        'all': 'btnFilterAll',
        'income': 'btnFilterIncome',
        'expense': 'btnFilterExpense'
    };
    const activeBtn = document.getElementById(activeMap[type]);
    if (activeBtn) {
        if (type === 'expense') {
            activeBtn.style.background = 'var(--dino-orange, #ea580c)';
            activeBtn.style.color = '#ffffff';
            activeBtn.style.borderColor = 'var(--dino-orange, #ea580c)';
        } else if (type === 'income') {
            activeBtn.style.background = 'var(--dino-green, #16a34a)';
            activeBtn.style.color = '#ffffff';
            activeBtn.style.borderColor = 'var(--dino-green, #16a34a)';
        } else {
            activeBtn.style.background = 'var(--accent-sunny, #f59e0b)';
            activeBtn.style.color = 'var(--bg-main, #111)';
            activeBtn.style.borderColor = 'var(--accent-sunny, #f59e0b)';
        }
    }
    loadEnergyLedgerPage(1);
}

function switchTimeRange(range) {
    if (currentLedgerTimeRange === range) {
        currentLedgerTimeRange = 'all'; // 再次点击取消筛选
    } else {
        currentLedgerTimeRange = range;
    }
    loadEnergyLedgerPage(1);
}

function resetTimeAndFilter() {
    currentLedgerTimeRange = 'all';
    switchLedgerFilter('all');
}

function changeLedgerPage(delta) {
    const targetPage = ledgerCurrentPage + delta;
    if (targetPage >= 1 && targetPage <= ledgerTotalPages) {
        loadEnergyLedgerPage(targetPage);
    }
}

function changeLedgerPageSize(size) {
    ledgerPageSize = parseInt(size, 10) || 20;
    loadEnergyLedgerPage(1);
}

// 兼容旧接口调用
function loadEnergyLedger() {
    loadEnergyLedgerPage(ledgerCurrentPage);
}

async function loadEnergyLedgerPage(page = 1) {
    if (ledgerIsLoading) return;
    ledgerIsLoading = true;
    ledgerCurrentPage = page;

    const container = document.getElementById('ledgerListContainer');
    if (!container) {
        ledgerIsLoading = false;
        return;
    }

    container.innerHTML = `<div style="text-align:center; padding:45px; color:var(--text-muted); font-size:0.82rem;">⏳ 正在查询银行流水 (第 ${page} 页)...</div>`;

    try {
        const authToken = typeof token !== 'undefined' ? token : (localStorage.getItem('token') || '');
        const res = await fetch(`/api/energy/transactions?filter_type=${currentLedgerFilter}&time_range=${currentLedgerTimeRange}&page=${page}&page_size=${ledgerPageSize}`, {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        if (!res.ok) throw new Error("获取流水失败");
        const data = await res.json();

        // 1. 渲染 5 列统计栏与余额
        if (data.summary) {
            const balEl = document.getElementById('ledgerBalance');
            const todayEl = document.getElementById('ledgerToday');
            const todayExpEl = document.getElementById('ledgerTodayExp');
            const weekIncEl = document.getElementById('ledgerWeekInc');
            const weekExpEl = document.getElementById('ledgerWeekExp');
            const incEl = document.getElementById('ledgerMonthIncome');
            const expEl = document.getElementById('ledgerMonthExpense');
            const lastIncEl = document.getElementById('ledgerLastMonthIncome');
            const lastExpEl = document.getElementById('ledgerLastMonthExpense');
            const yearIncEl = document.getElementById('ledgerYearIncome');
            const yearExpEl = document.getElementById('ledgerYearExpense');

            if (balEl) balEl.textContent = data.summary.current_balance || 0;
            if (todayEl) todayEl.textContent = `+${data.summary.today_income || 0}`;
            if (todayExpEl) todayExpEl.textContent = `-${data.summary.today_expense || 0}`;
            if (weekIncEl) weekIncEl.textContent = `+${data.summary.week_income || 0}`;
            if (weekExpEl) weekExpEl.textContent = `-${data.summary.week_expense || 0}`;
            if (incEl) incEl.textContent = `+${data.summary.month_total_income || 0}`;
            if (expEl) expEl.textContent = `-${data.summary.month_total_expense || 0}`;
            if (lastIncEl) lastIncEl.textContent = `+${data.summary.last_month_income || 0}`;
            if (lastExpEl) lastExpEl.textContent = `-${data.summary.last_month_expense || 0}`;
            if (yearIncEl) yearIncEl.textContent = `+${data.summary.year_income || 0}`;
            if (yearExpEl) yearExpEl.textContent = `-${data.summary.year_expense || 0}`;
        }

        // 2. 更新 5 个时间段筛选卡片立体边框高亮
        const timeCards = {
            'today': document.getElementById('cardTimeToday'),
            'week': document.getElementById('cardTimeWeek'),
            'month': document.getElementById('cardTimeMonth'),
            'last_month': document.getElementById('cardTimeLastMonth'),
            'year': document.getElementById('cardTimeYear')
        };
        for (const [rKey, cardEl] of Object.entries(timeCards)) {
            if (!cardEl) continue;
            if (rKey === currentLedgerTimeRange) {
                cardEl.style.background = 'rgba(245, 158, 11, 0.14)';
                cardEl.style.borderColor = 'var(--accent-sunny, #f59e0b)';
                cardEl.style.boxShadow = '0 2px 8px rgba(245, 158, 11, 0.2)';
            } else {
                cardEl.style.background = 'var(--card-bg)';
                cardEl.style.borderColor = 'var(--card-border)';
                cardEl.style.boxShadow = 'none';
            }
        }

        const resetBtn = document.getElementById('btnResetTimeRange');
        if (resetBtn) {
            resetBtn.style.display = (currentLedgerTimeRange !== 'all') ? 'inline-block' : 'none';
        }

        // 3. 更新分页状态与控制栏 (精准控制 disabled 与半透明置灰)
        ledgerTotalCount = data.total || 0;
        ledgerTotalPages = Math.max(1, Math.ceil(ledgerTotalCount / ledgerPageSize));
        currentLedgerItems = data.items || [];

        const prevBtn = document.getElementById('btnLedgerPrevPage');
        const nextBtn = document.getElementById('btnLedgerNextPage');
        const pageInfoEl = document.getElementById('ledgerPageInfo');
        const selectEl = document.getElementById('ledgerPageSizeSelect');

        if (selectEl && String(selectEl.value) !== String(ledgerPageSize)) {
            selectEl.value = String(ledgerPageSize);
        }

        const isPrevDisabled = (ledgerCurrentPage <= 1);
        const isNextDisabled = (ledgerCurrentPage >= ledgerTotalPages || ledgerTotalCount === 0);

        if (prevBtn) {
            prevBtn.disabled = isPrevDisabled;
            prevBtn.style.opacity = isPrevDisabled ? '0.35' : '1';
            prevBtn.style.cursor = isPrevDisabled ? 'not-allowed' : 'pointer';
        }
        if (nextBtn) {
            nextBtn.disabled = isNextDisabled;
            nextBtn.style.opacity = isNextDisabled ? '0.35' : '1';
            nextBtn.style.cursor = isNextDisabled ? 'not-allowed' : 'pointer';
        }
        if (pageInfoEl) {
            pageInfoEl.textContent = `第 ${ledgerCurrentPage} / ${ledgerTotalPages} 页 (共 ${ledgerTotalCount} 笔)`;
        }

        renderLedgerList(container);
    } catch (e) {
        console.error("加载蛋能量账本异常", e);
    } finally {
        ledgerIsLoading = false;
    }
}

function renderLedgerList(container) {
    if (currentLedgerItems.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:35px 20px; color:var(--text-muted);">
                <div style="font-size:1.8rem; margin-bottom:6px;">📜</div>
                <div style="font-size:0.85rem; font-weight:bold; color:var(--text-main);">当前筛选条件下暂无蛋能量流水</div>
                <div style="font-size:0.75rem; margin-top:4px;">可切换上方时间段或收支分类查看</div>
            </div>
        `;
        return;
    }

    let html = '';
    currentLedgerItems.forEach((tx, idx) => {
        const isIncome = tx.change_amount > 0;
        const amtStr = isIncome ? `+${tx.change_amount}` : `${tx.change_amount}`;
        const amtColor = isIncome ? 'var(--dino-green, #16a34a)' : 'var(--dino-orange, #ea580c)';
        
        // 1. 类型专属 Emoji 图标与专属背景光晕
        let typeEmoji = isIncome ? '🥚' : '🛍️';
        if (tx.target_type_id === 3 || tx.event_type_id === 201) typeEmoji = '📝';
        else if (tx.target_type_id === 2 || tx.event_type_id === 101) typeEmoji = '🥚';
        else if (tx.target_type_id === 1 || tx.event_type_id === 301) typeEmoji = '🛍️';
        else if (tx.target_type_id === 4 || tx.event_type_id === 401) typeEmoji = '🎁';

        const bgLightColor = isIncome ? 'rgba(34, 197, 94, 0.12)' : 'rgba(234, 88, 12, 0.12)';
        const borderLightColor = isIncome ? 'rgba(34, 197, 94, 0.3)' : 'rgba(234, 88, 12, 0.3)';
        const dirTagText = isIncome ? '📈 获得' : '📉 消耗';
        const dirTagColor = isIncome ? 'var(--dino-green, #16a34a)' : 'var(--dino-orange, #ea580c)';

        const displayTitle = tx.title || tx.event_name || (isIncome ? '获得蛋能量' : '消耗蛋能量');
        const displaySubtitle = tx.subtitle || (tx.asset_display && tx.asset_display.subtitle) || '';
        const rawImgUrl = tx.image_url || (tx.asset_display && tx.asset_display.image_url) || null;
        const timeStr = tx.created_at ? tx.created_at.replace('T', ' ').substring(0, 16) : '';

        html += `
            <div onclick="openEnergyReceiptByIndex(${idx})" style="background:var(--card-bg); border:1px solid var(--card-border); border-radius:12px; padding:10px 12px; display:flex; align-items:center; justify-content:space-between; cursor:pointer; transition:all 0.2s;" onmouseover="this.style.borderColor='var(--accent-sunny, #f59e0b)'" onmouseout="this.style.borderColor='var(--card-border)'">
                <!-- 左侧：类型 Logo 与文字详情 -->
                <div style="display:flex; align-items:center; gap:10px; overflow:hidden; flex:1; min-width:0;">
                    <div style="width:38px; height:38px; border-radius:10px; background:${bgLightColor}; border:1px solid ${borderLightColor}; display:flex; align-items:center; justify-content:center; font-size:1.25rem; flex-shrink:0;">
                        ${typeEmoji}
                    </div>
                    <div style="overflow:hidden; flex:1; min-width:0;">
                        <!-- 第一行：大类主标题 + 收支微标 -->
                        <div style="display:flex; align-items:center; gap:6px;">
                            <span style="font-weight:800; font-size:0.84rem; color:var(--text-main); white-space:nowrap;">${displayTitle}</span>
                            <span style="font-size:0.62rem; font-weight:700; color:${dirTagColor}; background:${bgLightColor}; border:1px solid ${borderLightColor}; padding:1px 5px; border-radius:4px; flex-shrink:0;">${dirTagText}</span>
                        </div>
                        <!-- 第二行：附属详情（日记真实标题 / 兑换商品详情，单行超长省略截断） -->
                        ${displaySubtitle ? `
                            <div style="font-size:0.73rem; color:var(--text-muted); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${displaySubtitle}">
                                ${displaySubtitle}
                            </div>
                        ` : ''}
                        <!-- 第三行：交易时间 -->
                        <div style="font-size:0.68rem; color:var(--text-muted); opacity:0.85; margin-top:2px;">
                            🕒 ${timeStr}
                        </div>
                    </div>
                </div>

                <!-- 蓝框位置：实物缩略图 (贴纸/画布/心情恐龙，36x36px带微圆角) -->
                ${rawImgUrl ? `
                    <div style="width:36px; height:36px; border-radius:8px; background:rgba(0,0,0,0.04); border:1px solid var(--card-border); display:flex; align-items:center; justify-content:center; flex-shrink:0; margin:0 10px; overflow:hidden;">
                        <img src="${rawImgUrl}" onerror="this.parentElement.style.display='none'" style="width:100%; height:100%; object-fit:contain;" />
                    </div>
                ` : ''}

                <!-- 红框位置：变动金额与结余 (去除末尾闪电符号，紧凑宽度) -->
                <div style="text-align:right; flex-shrink:0; min-width:56px;">
                    <div style="font-size:0.96rem; font-weight:900; color:${amtColor}; font-family:monospace;">${amtStr}</div>
                    <div style="font-size:0.68rem; color:var(--text-muted); margin-top:2px; white-space:nowrap;">结余 ${tx.balance_after}</div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}


function openEnergyReceiptByIndex(idx) {
    if (currentLedgerItems && currentLedgerItems[idx]) {
        openEnergyReceipt(currentLedgerItems[idx]);
    }
}

function openEnergyReceipt(item) {
    currentSelectedReceipt = item;
    const modal = document.getElementById('energyReceiptModal');
    if (!modal) return;

    const isIncome = item.change_amount > 0;
    const amtEl = document.getElementById('receiptAmount');
    if (amtEl) {
        amtEl.textContent = isIncome ? `+${item.change_amount}` : `${item.change_amount}`;
        amtEl.style.color = isIncome ? 'var(--dino-green, #16a34a)' : 'var(--dino-orange, #ea580c)';
    }

    const titleEl = document.getElementById('receiptTitle');
    if (titleEl) titleEl.textContent = item.title || item.event_name;

    const badgeEl = document.getElementById('receiptBadge');
    if (badgeEl) {
        badgeEl.textContent = item.badge_label || (isIncome ? '获得奖励' : '商城兑换');
        badgeEl.style.color = item.theme_color || (isIncome ? 'var(--dino-green, #16a34a)' : 'var(--accent-sunny, #ea580c)');
    }

    const timeEl = document.getElementById('receiptTime');
    if (timeEl) timeEl.textContent = item.created_at ? item.created_at.replace('T', ' ').substring(0, 19) : '--';

    const prevEl = document.getElementById('receiptPrevBalance');
    if (prevEl) prevEl.textContent = `${item.balance_after - item.change_amount} ⚡`;

    const afterEl = document.getElementById('receiptAfterBalance');
    if (afterEl) afterEl.textContent = `${item.balance_after} ⚡`;

    // 完整展示流水单号，不截断
    const uuidEl = document.getElementById('receiptUuid');
    const fullUuid = item.transaction_uuid || item.request_uuid || (`TX-2026-${item.id}`);
    if (uuidEl) {
        uuidEl.textContent = fullUuid;
        uuidEl.title = fullUuid;
    }

    // 缩略图与关联档案展示
    const assetBox = document.getElementById('receiptAssetBox');
    const assetImg = document.getElementById('receiptAssetImg');
    const assetName = document.getElementById('receiptAssetName');
    const assetDesc = document.getElementById('receiptAssetDesc');
    if (item.image_url && assetBox && assetImg && assetName) {
        assetImg.src = item.image_url;
        assetName.textContent = item.subtitle || item.title || item.event_name;
        if (assetDesc) {
            assetDesc.textContent = item.detail_info?.series_name ? `系列: ${item.detail_info.series_name}` : (item.detail_info?.mood_name ? `心情恐龙: ${item.detail_info.mood_name}` : '关联实体档案');
        }
        assetBox.style.display = 'flex';
    } else if (assetBox) {
        assetBox.style.display = 'none';
    }

    // 操作按钮
    const btnAction = document.getElementById('btnReceiptAction');
    if (btnAction) {
        if (item.target_type_id === 3 && item.detail_info?.diary_uuid) {
            btnAction.textContent = '📖 查看对应手账';
            btnAction.style.display = 'block';
        } else if (item.target_type_id === 1) {
            btnAction.textContent = '🛍️ 前往手账商城';
            btnAction.style.display = 'block';
        } else {
            btnAction.style.display = 'none';
        }
    }

    modal.style.display = 'flex';
}

function handleReceiptAction() {
    if (!currentSelectedReceipt) return;
    if (currentSelectedReceipt.target_type_id === 3 && currentSelectedReceipt.detail_info?.diary_uuid) {
        window.location.href = `/diary?uuid=${currentSelectedReceipt.detail_info.diary_uuid}`;
    } else if (currentSelectedReceipt.target_type_id === 1) {
        window.location.href = '/mall';
    }
}

function closeEnergyReceipt() {
    const modal = document.getElementById('energyReceiptModal');
    if (modal) modal.style.display = 'none';
}

function copyCurrentReceiptUuid() {
    if (!currentSelectedReceipt) return;
    const fullUuid = currentSelectedReceipt.transaction_uuid || currentSelectedReceipt.request_uuid || (`TX-2026-${currentSelectedReceipt.id}`);
    navigator.clipboard.writeText(fullUuid).then(() => {
        alert('已复制流水凭证单号：\n' + fullUuid);
    }).catch(() => {
        prompt('请手动复制流水单号：', fullUuid);
    });
}

// 显式挂载到 window，确保 HTML 内联 onclick 100% 触发
window.openEnergyLedgerModal = openEnergyLedgerModal;
window.closeEnergyLedgerModal = closeEnergyLedgerModal;
window.switchLedgerFilter = switchLedgerFilter;
window.switchTimeRange = switchTimeRange;
window.resetTimeAndFilter = resetTimeAndFilter;
window.changeLedgerPage = changeLedgerPage;
window.changeLedgerPageSize = changeLedgerPageSize;
window.loadEnergyLedger = loadEnergyLedger;
window.loadEnergyLedgerPage = loadEnergyLedgerPage;
window.openEnergyReceiptByIndex = openEnergyReceiptByIndex;
window.openEnergyReceipt = openEnergyReceipt;
window.closeEnergyReceipt = closeEnergyReceipt;
window.handleReceiptAction = handleReceiptAction;
window.copyCurrentReceiptUuid = copyCurrentReceiptUuid;

// 检查 URL 是否带 open_ledger=1
if (new URLSearchParams(window.location.search).get('open_ledger') === '1') {
    setTimeout(() => {
        openEnergyLedgerModal();
    }, 200);
}

// Start Initialization
initOverviewPage();


