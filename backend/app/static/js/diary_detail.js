// Global Variables for Detail page
let globalPersons = [];
let globalPersonsMap = {};
let stickerImgMap = {};

let dinoImgMap = {};
let dinoMap = {};
let moodTipMap = {};

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
        const res = await fetch('/api/dino/config', {
            headers: { 'Authorization': 'Bearer ' + token }
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

function formatFileSize(bytes) {
    if (bytes === undefined || bytes === null || isNaN(bytes)) return '未知大小';
    if (bytes < 1024) return bytes + ' B';
    const kb = bytes / 1024;
    if (kb < 1024) return kb.toFixed(1) + ' KB';
    const mb = kb / 1024;
    return mb.toFixed(1) + ' MB';
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
            globalPersons.forEach(p => {
                globalPersonsMap[p.uuid] = p;
            });
        }
    } catch (e) {
        console.error("Failed to load persons", e);
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
                    });
                }
            });
        }
    } catch (e) {
        console.warn("Failed to fetch stickers config:", e);
    }
}

async function initDetailPage() {
    await fetchDinoConfig();
    await fetchPersons();
    await fetchStickersConfig();
    const urlParams = new URLSearchParams(window.location.search);
    const uuid = urlParams.get('uuid');
    if (!uuid) {
        window.location.href = '/diary';
        return;
    }
    
    try {
        const res = await fetch(`/api/logs/detail/${uuid}`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (res.ok) {
            const log = await res.json();
            renderLogDetail(log);
        } else {
            document.getElementById('detailLogContentBody').innerHTML = `
                <div style="text-align: center; color: var(--dino-red); padding: 30px;">
                    获取日记详情失败，日记可能已被删除！
                </div>
            `;
        }
    } catch (e) {
        console.error("Failed to load log detail", e);
    }
}

function renderLogDetail(log) {
    const titleEl = document.getElementById('detailLogTitleHeader');
    if (!titleEl) return;
    const displayTitle = (log.title && log.title.trim()) 
        ? (log.title.length > 10 ? log.title.substring(0, 10) + "..." : log.title) 
        : "无标题";
    titleEl.textContent = displayTitle;
    
    const contentBody = document.getElementById('detailLogContentBody');
    if (!contentBody) return;
    contentBody.innerHTML = '';
    
    const dinoText = dinoMap[log.mood_dino_id] || `🦕 ${log.mood_dino || ''}`;
    const imgName = dinoImgMap[log.mood_dino_id] || "mood_triceratops.png";
    const tipText = moodTipMap[log.mood_dino_id] || "";
    
    const incidentDateStr = log.incident_date ? log.incident_date.replace('T', ' ').substring(0, 19) : '';
    const updatedAtStr = log.updated_at ? log.updated_at.replace('T', ' ').substring(0, 19) : '';
    const incDate = log.incident_date ? new Date(log.incident_date) : null;
    const updDate = log.updated_at ? new Date(log.updated_at) : null;
    const isEdited = (log.version > 1) && incDate && updDate && (updDate.getTime() - incDate.getTime() > 10000);

    
    let metaHtml = `
        <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:12px; border-radius:12px; border:1px solid rgba(255,255,255,0.05); flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="/static/images/dinosaurs/${imgName}" style="width:40px; height:40px; border-radius:50%; background:rgba(255,255,255,0.15);" />
                <div>
                    <div style="font-weight:700; color:var(--text-main); font-size:0.95rem;">${dinoText}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">${tipText}</div>
                </div>
            </div>
            <div style="font-size:0.75rem; color:var(--text-muted); text-align:right;">
                <div>写于：${incidentDateStr}</div>
                ${isEdited ? `<div style="margin-top:2px;">改于：${updatedAtStr}</div>` : ''}
            </div>
        </div>
    `;
    
    let personsHtml = '';
    if (log.person_uuids && log.person_uuids.length > 0) {
        personsHtml = '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:5px;">';
        log.person_uuids.forEach(pUuid => {
            const pObj = globalPersonsMap[pUuid];
            if (pObj) {
                personsHtml += getPersonTagHtml(pObj);
            }
        });
        personsHtml += '</div>';
    }
    
    const rawContent = log.content || '';
    
    // Parse stickers
    const stickersList = [];
    const stickerRegex = /\[sticker:([^:]+):([0-9.-]+),([0-9.-]+)(?:,([0-9.-]+),([0-9.-]+),([0-1]),([0-1]))?\]/g;
    let match;
    while ((match = stickerRegex.exec(rawContent)) !== null) {
        stickersList.push({
            dinoId: match[1],
            x: parseFloat(match[2]),
            y: parseFloat(match[3]),
            scale: match[4] !== undefined ? parseFloat(match[4]) : 1.0,
            rotation: match[5] !== undefined ? parseFloat(match[5]) : 0.0,
            flipH: match[6] !== undefined ? parseInt(match[6]) === 1 : false,
            flipV: match[7] !== undefined ? parseInt(match[7]) === 1 : false
        });
    }
    
    const displayContent = rawContent.replace(/\[sticker:[^\]]+\]/g, '').trim();

    const contentParagraphs = displayContent.split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(line => `<p style="text-indent: 2em; line-height: 1.6; margin-bottom: 12px; font-size: 0.95rem; white-space: pre-wrap;">${line}</p>`)
        .join('');
        
    // Generate stickers HTML
    let stickersHtml = '';
    if (stickersList.length > 0) {
        const aspectStr = log.canvas_aspect_ratio || "2:1";
        const parts = aspectStr.split(":");
        const wPart = parseFloat(parts[0]) || 2;
        const hPart = parseFloat(parts[1]) || 1;
        const ratioVal = wPart / hPart;
        const logicalHeight = 360 / ratioVal;

        let fallbackUrl = '/static/images/canvas_fallback_2_1.jpg';
        if (aspectStr === "16:9") {
            fallbackUrl = '/static/images/canvas_fallback_16_9.jpg';
        } else if (aspectStr === "4:3") {
            fallbackUrl = '/static/images/canvas_fallback_4_3.jpg';
        } else if (aspectStr === "1:1") {
            fallbackUrl = '/static/images/canvas_fallback_1_1.jpg';
        } else if (aspectStr === "2:1") {
            fallbackUrl = '/static/images/canvas_fallback_2_1.jpg';
        }

        let bgStyle = '';
        if (log.canvas_instance_id) {
            if (log.canvas_image_url) {
                bgStyle = `background-image: url('${log.canvas_image_url}'); background-size: cover; background-position: center;`;
            } else {
                bgStyle = `background-image: url('${fallbackUrl}'); background-size: cover; background-repeat: no-repeat; background-position: center;`;
            }
        } else {
            bgStyle = `background-color: var(--card-bg, #ffffff);`;
        }

        stickersHtml = `
            <div style="margin-top: 15px; width: 100%; aspect-ratio: ${wPart} / ${hPart}; position: relative; overflow: hidden; border: 1px solid var(--card-border); border-radius: 12px; box-shadow: inset 0 2px 8px rgba(0,0,0,0.08); ${bgStyle}">
        `;
        
        const dinoIconMap = {
            1: 'mood_triceratops',
            2: 'mood_pterodactyl_happy',
            3: 'mood_t_rex_proud',
            4: 'mood_brachiosaurus',
            5: 'mood_stegosaurus',
            6: 'mood_ankylosaurus',
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
            Ankylosaurus: 'mood_ankylosaurus',
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

        stickersList.forEach(st => {
            let srcUrl = '';
            if (stickerImgMap[st.dinoId]) {
                srcUrl = stickerImgMap[st.dinoId];
            } else {
                const numId = parseInt(st.dinoId);
                if (!isNaN(numId) && stickerImgMap[numId]) {
                    srcUrl = stickerImgMap[numId];
                } else {
                    let legacyKey = st.dinoId;
                    if (!isNaN(numId) && numId >= 1000) {
                        legacyKey = numId - 1000;
                    }
                    const assetName = dinoIconMap[legacyKey] || 'mood_triceratops';
                    srcUrl = `/static/images/dinosaurs/${assetName}.png`;
                }
            }
            
            const xMin = Math.max(0, 28 * (st.scale - 1));
            const xMax = 360 - 28 * (st.scale + 1);
            const yMin = Math.max(0, 28 * (st.scale - 1));
            const yMax = logicalHeight - 28 * (st.scale + 1);
            const safeX = Math.max(xMin, Math.min(st.x, xMax));
            const safeY = Math.max(yMin, Math.min(st.y, yMax));

            const leftPercent = (safeX / 360) * 100;
            const topPercent = (safeY / logicalHeight) * 100;
            
            let transformStr = `scale(${st.scale}) rotate(${st.rotation}deg)`;
            if (st.flipH || st.flipV) {
                transformStr += ` scale(${st.flipH ? -1 : 1}, ${st.flipV ? -1 : 1})`;
            }
            
            stickersHtml += `
                <div style="position: absolute; 
                            left: ${leftPercent}%; 
                            top: ${topPercent}%; 
                            width: 15.5556%; 
                            aspect-ratio: 1 / 1; 
                            transform: ${transformStr}; 
                            transform-origin: center; 
                            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));">
                    <img src="${srcUrl}" style="width: 100%; height: 100%; object-fit: contain;" onerror="this.src='/static/images/ic_launcher.png'" />
                </div>
            `;
        });
        stickersHtml += `</div>`;
    }
        
    const mainContentHtml = `
        <div style="color:var(--text-main); margin-top:10px;">
            ${contentParagraphs}
        </div>
        ${stickersHtml}
    `;
    
    let reflectionHtml = '';
    if (log.own_thoughts && log.own_thoughts.trim()) {
        const thoughtsParagraphs = log.own_thoughts.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0)
            .map(line => `<p style="text-indent: 2em; line-height: 1.5; margin-bottom: 6px; white-space: pre-wrap;">${line}</p>`)
            .join('');
        reflectionHtml = `
            <div class="log-reflection" style="margin-top:10px;">
                <span style="display:block; color:#c084fc; font-weight:700; margin-bottom:6px;">🤫 我的悄悄话：</span>
                ${thoughtsParagraphs}
            </div>
        `;
    }
    
    let mediaHtml = '';
    if (log.attachments && log.attachments.length > 0) {
        const images = log.attachments.filter(att => att.mime_type.startsWith('image/'));
        const videos = log.attachments.filter(att => att.mime_type.startsWith('video/'));
        const audios = log.attachments.filter(att => att.mime_type.startsWith('audio/'));
        const others = log.attachments.filter(att => 
            !att.mime_type.startsWith('image/') && 
            !att.mime_type.startsWith('video/') && 
            !att.mime_type.startsWith('audio/')
        );

        mediaHtml = '<div class="log-attachments" style="margin-top:15px; border-top: 1px solid rgba(255,255,255,0.05); padding-top:15px;">';
        
        const renderAttachment = (att) => {
            const dlUrl = `/api/attachments/download/${att.uuid}?token=${token}`;
            const sizeStr = formatFileSize(att.file_size);
            const displayTitle = att.title ? att.title : att.file_name;
            const titleStr = ` - "${displayTitle}"`;
            
            if (att.mime_type.startsWith('image/')) {
                return `
                    <div style="display:flex; flex-direction:column; gap:4px; width:100%; margin-bottom:10px;">
                        <span style="font-size:0.75rem; color:var(--text-muted);">📷 图片印记${titleStr} (${sizeStr})：</span>
                        <a href="${dlUrl}" target="_blank" style="display:inline-block;"><img class="media-attachment" src="${dlUrl}" alt="${att.file_name}" style="max-height:160px; border-radius:10px; border:1px solid rgba(255,255,255,0.1);"></a>
                    </div>
                `;
            } else if (att.mime_type.startsWith('video/')) {
                return `
                    <div style="display:flex; flex-direction:column; gap:4px; width:100%; margin-bottom:10px;">
                        <span style="font-size:0.75rem; color:var(--text-muted);">🎥 视频备忘${titleStr} (${sizeStr})：</span>
                        <video class="media-video" controls src="${dlUrl}" style="width:100%; max-width:450px; border-radius:10px;"></video>
                    </div>
                `;
            } else if (att.mime_type.startsWith('audio/')) {
                return `
                    <div style="display:flex; flex-direction:column; gap:4px; width:100%; margin-bottom:10px;">
                        <span style="font-size:0.75rem; color:var(--text-muted);">🎵 录音记事${titleStr} (${sizeStr})：</span>
                        <audio class="media-audio" controls src="${dlUrl}" style="width:100%; max-width:400px;"></audio>
                    </div>
                `;
            } else {
                return `
                    <div style="display:flex; flex-direction:column; gap:4px; width:100%; margin-bottom:10px;">
                        <span style="font-size:0.75rem; color:var(--text-muted);">📎 附件${titleStr} (${sizeStr})：</span>
                        <a href="${dlUrl}" target="_blank" style="font-size:0.9rem; color:var(--primary); text-decoration:underline;">下载附件</a>
                    </div>
                `;
            }
        };

        images.forEach(att => { mediaHtml += renderAttachment(att); });
        videos.forEach(att => { mediaHtml += renderAttachment(att); });
        audios.forEach(att => { mediaHtml += renderAttachment(att); });
        others.forEach(att => { mediaHtml += renderAttachment(att); });

        mediaHtml += '</div>';
    }
    
    contentBody.innerHTML = metaHtml + personsHtml + mainContentHtml + reflectionHtml + mediaHtml;
}

function goBackToSearch() {
    const contentBody = document.getElementById('detailLogContentBody');
    if (contentBody) {
        const audios = contentBody.querySelectorAll('audio');
        const videos = contentBody.querySelectorAll('video');
        audios.forEach(a => a.pause());
        videos.forEach(v => v.pause());
    }
    window.location.href = '/diary';
}

// Start Initialization
initDetailPage();
