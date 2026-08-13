// Global Variables for Diary
let childLogs = [];
let totalLogsCount = 0;
let currentPage = 1;
let limitPerPage = 10;

let searchKeyword = '';
let filterPersonUuid = '';
let filterMood = '';
let filterStartDate = '';
let filterEndDate = '';

let globalPersons = [];
let globalPersonsMap = {};

let fetchLogsCount = 0; // Request ID Tracker for race condition prevention

let dinoImgMap = {};
let dinoMap = {};
let moodTipMap = {};
let stickerImgMap = {};
let stickerNameMap = {};

const fallbackDinos = [
    { id: 1, legacy_key: 'Triceratops', name: '快乐三角龙', mood_label: '😊 开心', image_url: 'mood_triceratops.png' },
    { id: 2, legacy_key: 'Pterodactyl_happy', name: '冲天翼手龙', mood_label: '🤩 兴奋', image_url: 'mood_pterodactyl_happy.png' },
    { id: 3, legacy_key: 'T-Rex_proud', name: '挺胸霸王龙', mood_label: '😎 得意', image_url: 'mood_t_rex_proud.png' },
    { id: 4, legacy_key: 'Brachiosaurus', name: '大眼睛雷龙', mood_label: '🌟 期待', image_url: 'mood_brachiosaurus.png' },
    { id: 5, legacy_key: 'Stegosaurus', name: '呆呆剑龙', mood_label: '😮 惊讶', image_url: 'mood_stegosaurus.png' },
    { id: 6, legacy_key: 'Velociraptor', name: '佛系迅猛龙', mood_label: '😐 一般', image_url: 'mood_velociraptor.png' },
    { id: 7, legacy_key: 'Ankylosaurus_scared', name: '缩壳甲龙', mood_label: '😰 紧张', image_url: 'mood_ankylosaurus_scared.png' },
    { id: 8, legacy_key: 'Pachycephalosaurus', name: '叹气肿头龙', mood_label: '🍃 遗憾', image_url: 'mood_pachycephalosaurus.png' },
    { id: 9, legacy_key: 'Parasaurolophus_regret', name: '耷拉角副栉龙', mood_label: '😣 后悔', image_url: 'mood_parasaurolophus_regret.png' },
    { id: 10, legacy_key: 'Spinosaurus', name: '细雨棘龙', mood_label: '😭 伤心', image_url: 'mood_spinosaurus.png' },
    { id: 11, legacy_key: 'Dilophosaurus', name: '怒火双脊龙', mood_label: '😡 愤怒', image_url: 'mood_dilophosaurus.png' }
];

async function fetchDinoConfig() {
    try {
        const res = await fetch('/api/dino/config', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (res.ok) {
            const list = await res.json();
            populateMaps(list);
            renderMoodDropdown(list);
        } else {
            throw new Error("API failed");
        }
    } catch (e) {
        console.warn("fetchDinoConfig failed, using fallback:", e);
        populateMaps(fallbackDinos);
        renderMoodDropdown(fallbackDinos);
    }
}

async function fetchStickersConfig() {
    try {
        const res = await fetch('/api/stickers/config', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (res.ok) {
            const seriesList = await res.json();
            seriesList.forEach(series => {
                if (series.stickers) {
                    series.stickers.forEach(st => {
                        let url = st.image_url;
                        if (url && !url.startsWith('/') && !url.startsWith('http')) {
                            url = '/static/images/dinosaurs/' + url;
                        }
                        stickerImgMap[st.id] = url;
                        stickerNameMap[st.id] = st.name;
                    });
                }
            });
        }
    } catch (e) {
        console.warn("Failed to fetch stickers config:", e);
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

function renderMoodDropdown(list) {
    const moodDropdown = document.getElementById('moodFilter');
    if (moodDropdown) {
        moodDropdown.innerHTML = '<option value="">全部心情</option>';
        list.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.id;
            opt.textContent = `${item.mood_label} ${item.name}`;
            moodDropdown.appendChild(opt);
        });
    }
}

function getPersonTagHtml(pObj) {
    const isLight = document.documentElement.className.includes('theme-light-warm') ||
                    document.documentElement.className.includes('theme-nordic-cool') ||
                    document.documentElement.className.includes('theme-sakura-peach');
    const borderStyle = isLight ? `border: 1px solid rgba(0, 0, 0, 0.12);` : `border: 1px solid rgba(255, 255, 255, 0.1);`;
    const colorMap = {
        red: { bg: 'rgba(239, 68, 68, 0.15)', text: '#fca5a5', lightText: '#b91c1c' },
        orange: { bg: 'rgba(249, 115, 22, 0.15)', text: '#fed7aa', lightText: '#c2410c' },
        yellow: { bg: 'rgba(234, 179, 8, 0.15)', text: '#fef08a', lightText: '#a16207' },
        green: { bg: 'rgba(34, 197, 94, 0.15)', text: '#bbf7d0', lightText: '#15803d' },
        blue: { bg: 'rgba(59, 130, 246, 0.15)', text: '#bfdbfe', lightText: '#1d4ed8' },
        purple: { bg: 'rgba(168, 85, 247, 0.15)', text: '#e9d5ff', lightText: '#7e22ce' },
        gray: { bg: 'rgba(100, 116, 139, 0.15)', text: '#cbd5e1', lightText: '#475569' }
    };
    const colors = colorMap[pObj.color_tag] || colorMap.red;
    const txtColor = isLight ? colors.lightText : colors.text;
    
    return `<span style="padding: 2px 8px; font-size: 0.72rem; border-radius: 6px; background:${colors.bg}; color:${txtColor}; font-weight:bold; ${borderStyle}">${pObj.name} (${pObj.relationship})</span>`;
}

async function initDiaryPage() {
    try {
        await fetchDinoConfig();
        await fetchPersons();
        await fetchStickersConfig();
        
        // Parse url search params for filters
        const urlParams = new URLSearchParams(window.location.search);
        const pUuid = urlParams.get('person_uuid');
        if (pUuid) {
            filterPersonUuid = pUuid;
            const filterEl = document.getElementById('personFilter');
            if (filterEl) filterEl.value = pUuid;
        }
        const queryVal = urlParams.get('query');
        if (queryVal) {
            searchKeyword = queryVal;
            const kwEl = document.getElementById('keywordFilter');
            if (kwEl) kwEl.value = queryVal;
        }

        // Bind Filters Listeners with Debounce
        let debounceTimer;
        document.getElementById('keywordFilter').addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                searchKeyword = e.target.value.trim();
                currentPage = 1;
                fetchLogs();
            }, 300);
        });

        document.getElementById('personFilter').addEventListener('change', (e) => {
            filterPersonUuid = e.target.value;
            currentPage = 1;
            fetchLogs();
        });

        document.getElementById('moodFilter').addEventListener('change', (e) => {
            filterMood = e.target.value;
            currentPage = 1;
            fetchLogs();
        });

        document.getElementById('startDateFilter').addEventListener('change', (e) => {
            filterStartDate = e.target.value;
            currentPage = 1;
            fetchLogs();
        });

        document.getElementById('endDateFilter').addEventListener('change', (e) => {
            filterEndDate = e.target.value;
            currentPage = 1;
            fetchLogs();
        });

        await fetchLogs();
    } catch (e) {
        console.error("Diary init error", e);
    }
}

async function fetchPersons() {
    try {
        const res = await fetch('/api/persons/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ persons: [], deleted_uuids: [] })
        });
        if (res.ok) {
            globalPersons = await res.json();
            globalPersonsMap = {};
            
            const filterDropdown = document.getElementById('personFilter');
            if (filterDropdown) filterDropdown.innerHTML = '<option value="">全部人物</option>';
            
            globalPersons.forEach(p => {
                globalPersonsMap[p.uuid] = p;
                if (!p.is_deleted && !p.is_temporary) {
                    const opt = document.createElement('option');
                    opt.value = p.uuid;
                    opt.textContent = `${p.name} (${p.relationship})`;
                    if (filterDropdown) filterDropdown.appendChild(opt);
                }
            });
        }
    } catch (e) {
        console.error("Failed to load persons", e);
    }
}

async function fetchLogs() {
    const currentFetchId = ++fetchLogsCount; // Increment request version number
    try {
        checkActiveFilters();
        let url = `/api/logs/list?page=${currentPage}&limit=${limitPerPage}`;
        if (searchKeyword) url += `&query=${encodeURIComponent(searchKeyword)}`;
        if (filterMood) url += `&mood_dino_id=${encodeURIComponent(filterMood)}`;
        if (filterStartDate) url += `&start_date=${encodeURIComponent(filterStartDate)}`;
        if (filterEndDate) url += `&end_date=${encodeURIComponent(filterEndDate)}`;
        if (filterPersonUuid) url += `&person_uuid=${encodeURIComponent(filterPersonUuid)}`;

        const res = await fetch(url, {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (res.ok) {
            // Check if this response is still the latest one
            if (currentFetchId !== fetchLogsCount) {
                return; // Discard outdated response
            }
            const data = await res.json();
            childLogs = data.items;
            totalLogsCount = data.total;
            
            renderLogs();
            renderPagination();
        }
    } catch(e) {
        console.error("Failed to load logs", e);
    }
}

function renderLogs() {
    const container = document.getElementById('logsContainer');
    if (!container) return;
    container.innerHTML = '';

    if (childLogs.length === 0) {
        const hasFilters = searchKeyword || filterPersonUuid || filterMood || filterStartDate || filterEndDate;
        const emptyMsg = hasFilters
            ? '没有找到符合当前筛选条件的日记，试试<a onclick="clearFilters()" href="#" style="color:#c084fc;">清空筛选条件</a>？'
            : '还没有写过任何日记哦，快去 App 记录第一篇吧！';
        container.innerHTML = `
            <div class="card empty-placeholder">
                <div class="empty-icon">🦕</div>
                <h3>这里空空如也哦</h3>
                <p style="margin-top: 8px;">${emptyMsg}</p>
            </div>
        `;
        return;
    }

    const dinoIconMap = {
        1: 'mood_triceratops',
        2: 'mood_pterodactyl_happy',
        3: 'mood_t_rex_proud',
        4: 'mood_brachiosaurus',
        5: 'mood_stegosaurus',
        6: 'mood_velociraptor',
        7: 'mood_ankylosaurus_scared',
        8: 'mood_pachycephalosaurus',
        9: 'mood_parasaurolophus_regret',
        10: 'mood_spinosaurus',
        11: 'mood_dilophosaurus',
        
        // Legacy mapping
        Triceratops: 'mood_triceratops',
        Pterodactyl_happy: 'mood_pterodactyl_happy',
        Pterodactyl: 'mood_pachycephalosaurus',                    // 历史旧遗憾映射到新肿头龙
        'T-Rex_proud': 'mood_t_rex_proud',
        Brachiosaurus: 'mood_brachiosaurus',
        Stegosaurus: 'mood_stegosaurus',
        Velociraptor: 'mood_velociraptor',
        Ankylosaurus: 'mood_ankylosaurus_scared',
        Ankylosaurus_scared: 'mood_ankylosaurus_scared',
        'Ankylosaurus_Shell': 'mood_ankylosaurus_scared',
        Pterodactyl_Sigh: 'mood_pachycephalosaurus',
        Parasaurolophus_regret: 'mood_parasaurolophus_regret',
        'Parasaurolophus_Regret': 'mood_parasaurolophus_regret',
        Parasaurolophus: 'mood_spinosaurus',                         // 历史旧伤心映射到新棘龙
        'T-Rex': 'mood_dilophosaurus',                               // 历史旧愤怒映射到新双脊龙
        'T-Rex_Angry': 'mood_dilophosaurus',
        Spinosaurus: 'mood_spinosaurus',
        Pachycephalosaurus: 'mood_pachycephalosaurus',
        Dilophosaurus: 'mood_dilophosaurus'
    };

    childLogs.forEach(log => {
        const dinoText = dinoMap[log.mood_dino_id] || `🦕 ${log.mood_dino || ''}`;
        const incidentDateStr = log.incident_date ? log.incident_date.replace('T', ' ').substring(0, 19) : '';
        
        let timeHtml = `<div style="font-size:0.75rem; color:var(--text-muted); line-height:1.4;">
            <span>写于：${incidentDateStr}</span></div>`;

        // Associate persons labels
        let personsHtml = '';
        if (log.person_uuids && log.person_uuids.length > 0) {
            personsHtml = '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:6px; align-items:center;">';
            log.person_uuids.forEach(pUuid => {
                const pObj = globalPersonsMap[pUuid];
                if (pObj) {
                    personsHtml += getPersonTagHtml(pObj);
                }
            });
            personsHtml += '</div>';
        }

        // Parse stickers from content
        const stickers = [];
        const stickerRegex = /\[sticker:([^:]+):[^\]]+\]/g;
        let match;
        while ((match = stickerRegex.exec(log.content || '')) !== null) {
            stickers.push(match[1].trim());
        }

        // Generate stickers preview HTML
        let stickersHtml = '';
        if (stickers.length > 0) {
            const isLight = document.documentElement.className.includes('theme-light-warm') ||
                            document.documentElement.className.includes('theme-nordic-cool') ||
                            document.documentElement.className.includes('theme-sakura-peach');
            const stickerBg = isLight ? 'rgba(0, 0, 0, 0.03)' : 'rgba(255, 255, 255, 0.05)';
            const stickerBorder = isLight ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.15)';
            
            stickersHtml = `<div class="log-stickers-preview" style="display: flex; gap: 6px; align-items: center; max-width: 240px; overflow-x: auto; white-space: nowrap; padding: 2px;">`;
            stickers.forEach(stickerId => {
                let srcUrl = '';
                let name = '';
                
                if (stickerImgMap[stickerId]) {
                    srcUrl = stickerImgMap[stickerId];
                    name = stickerNameMap[stickerId] || '';
                } else {
                    const numId = parseInt(stickerId);
                    if (!isNaN(numId) && stickerImgMap[numId]) {
                        srcUrl = stickerImgMap[numId];
                        name = stickerNameMap[numId] || '';
                    } else {
                        let legacyKey = stickerId;
                        if (!isNaN(numId) && numId >= 1000) {
                            legacyKey = numId - 1000;
                        }
                        const assetName = dinoIconMap[legacyKey] || 'mood_triceratops';
                        srcUrl = `/static/images/dinosaurs/${assetName}.png`;
                    }
                }

                const titleAttr = name ? `title="${name}"` : '';
                stickersHtml += `
                    <img src="${srcUrl}" ${titleAttr} 
                         style="width: 36px; height: 36px; border-radius: 6px; background: ${stickerBg}; border: 1px solid ${stickerBorder}; object-fit: contain; box-shadow: 0 2px 5px rgba(0,0,0,0.15);" 
                         onerror="this.src='/static/images/ic_launcher.png'" />
                `;
            });
            stickersHtml += `</div>`;
        }

        const content = (log.content || '').replace(/\[sticker:[^\]]+\]/g, '').trim();
        const displayTitle = (log.title && log.title.trim()) 
            ? (log.title.length > 10 ? log.title.substring(0, 10) + "..." : log.title) 
            : "无标题";
        const summaryText = content.length > 120 ? content.substring(0, 120) + '...' : content;

        let mediaMetaHtml = '';
        if (log.attachments && log.attachments.length > 0) {
            const imagesCount = log.attachments.filter(a => a.mime_type.startsWith('image/')).length;
            const videosCount = log.attachments.filter(a => a.mime_type.startsWith('video/')).length;
            const audiosCount = log.attachments.filter(a => a.mime_type.startsWith('audio/')).length;

            mediaMetaHtml = '<div style="display:flex; gap:12px; margin-top:8px; font-size:0.8rem; color:var(--text-muted);">';
            if (imagesCount > 0) mediaMetaHtml += `<span>📸 图片 x${imagesCount}</span>`;
            if (videosCount > 0) mediaMetaHtml += `<span>🎥 视频 x${videosCount}</span>`;
            if (audiosCount > 0) mediaMetaHtml += `<span>🔊 语音 x${audiosCount}</span>`;
            mediaMetaHtml += '</div>';
        }

        const card = document.createElement('div');
        card.className = 'log-card';
        card.style.cursor = 'pointer';
        card.onclick = () => showLogDetail(log.uuid);
        
        const imgName = dinoImgMap[log.mood_dino_id] || "mood_triceratops.png";

        card.innerHTML = `
            <div class="log-header" style="align-items: center;">
                <div class="log-meta">
                    ${timeHtml}
                    <span class="log-mood-dino" style="font-weight:600; color:var(--text-main);">
                        <img src="/static/images/dinosaurs/${imgName}" style="width:38px; height:38px; border-radius:50%; object-fit:cover; background:rgba(255,255,255,0.25); box-shadow: 0 3px 8px rgba(0,0,0,0.15);" />
                        <span>${dinoText}</span>
                    </span>
                </div>
                ${stickersHtml}
            </div>
            ${personsHtml}
            <div style="margin-top: 10px;">
                <h4 style="font-size:1.1rem; font-weight:700; color:var(--accent-sunny); margin-bottom:6px;">${displayTitle}</h4>
                <p style="font-size:0.95rem; line-height:1.5; color:var(--text-main); white-space:pre-wrap; margin:0;">${summaryText}</p>
            </div>
            ${mediaMetaHtml}
        `;
        container.appendChild(card);
    });
}

function renderPagination() {
    const container = document.getElementById('paginationContainer');
    if (!container) return;
    container.innerHTML = '';

    const totalPages = Math.max(1, Math.ceil(totalLogsCount / limitPerPage));

    const prevBtn = document.createElement('button');
    prevBtn.className = 'logout-btn';
    prevBtn.textContent = '上一页';
    prevBtn.style.cursor = 'pointer';
    prevBtn.disabled = currentPage === 1;
    prevBtn.style.opacity = currentPage === 1 ? 0.5 : 1;
    prevBtn.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            fetchLogs();
        }
    };
    container.appendChild(prevBtn);

    const infoSpan = document.createElement('span');
    infoSpan.textContent = `第 ${currentPage} / ${totalPages} 页 (共 ${totalLogsCount} 条)`;
    infoSpan.style = "font-size:0.9rem; color:var(--text-muted); font-family:Monospace; margin: 0 10px;";
    container.appendChild(infoSpan);

    const nextBtn = document.createElement('button');
    nextBtn.className = 'logout-btn';
    nextBtn.textContent = '下一页';
    nextBtn.style.cursor = 'pointer';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.style.opacity = currentPage === totalPages ? 0.5 : 1;
    nextBtn.onclick = () => {
        if (currentPage < totalPages) {
            currentPage++;
            fetchLogs();
        }
    };
    container.appendChild(nextBtn);

    const sizeSelect = document.createElement('select');
    sizeSelect.id = 'pageSizeSelect';
    sizeSelect.style = "padding: 6px 12px; font-size: 0.8rem; border-radius: 8px; background: rgba(255,255,255,0.06); border: 1px solid var(--card-border); color: var(--text-main); outline: none; cursor: pointer; margin-left: 15px;";
    [10, 20, 50].forEach(val => {
        const opt = document.createElement('option');
        opt.value = val;
        opt.textContent = `${val} 条/页`;
        if (val === limitPerPage) opt.selected = true;
        opt.style.background = '#0d1b31';
        opt.style.color = '#fff';
        sizeSelect.appendChild(opt);
    });
    sizeSelect.onchange = (e) => {
        limitPerPage = parseInt(e.target.value);
        currentPage = 1;
        fetchLogs();
    };
    container.appendChild(sizeSelect);
}

function showLogDetail(logUuid) {
    window.location.href = `/diary/detail?uuid=${logUuid}`;
}

function clearFilters() {
    document.getElementById('keywordFilter').value = '';
    document.getElementById('personFilter').value = '';
    document.getElementById('moodFilter').value = '';
    document.getElementById('startDateFilter').value = '';
    document.getElementById('endDateFilter').value = '';
    
    searchKeyword = '';
    filterPersonUuid = '';
    filterMood = '';
    filterStartDate = '';
    filterEndDate = '';
    
    currentPage = 1;
    fetchLogs();
}

let isFiltersCollapsed = false;
function toggleFiltersPanel() {
    const content = document.getElementById('collapsibleFiltersContent');
    const icon = document.getElementById('toggleFiltersIcon');
    if (!content || !icon) return;
    
    if (isFiltersCollapsed) {
        content.style.maxHeight = '500px';
        content.style.opacity = '1';
        icon.style.transform = 'rotate(0deg)';
        isFiltersCollapsed = false;
    } else {
        content.style.maxHeight = '0px';
        content.style.opacity = '0';
        icon.style.transform = 'rotate(-90deg)';
        isFiltersCollapsed = true;
    }
}

function checkActiveFilters() {
    const hasActive = searchKeyword || filterPersonUuid || filterMood || filterStartDate || filterEndDate;
    const badge = document.getElementById('filtersActiveBadge');
    if (badge) {
        badge.style.display = hasActive ? 'inline-block' : 'none';
    }
}

// Start Initialization
initDiaryPage();
