/**
 * Admin Promotions Management JS (Refactored)
 * 全站现代浅色/自适应主题风格、多维度优惠规则配置与可视化商品选择器抽屉
 */

let allPromotions = [];
let availableShopItems = [];
let availableStickerSeries = [];
let availableCanvasSeries = [];

// 分页状态
let currentPage = 1;
let pageSize = 10;
let totalCount = 0;
let totalPages = 1;

// 选择器当前交互上下文（以系列为最小颗粒度）
let currentPickerState = {
    activeRowBox: null,
    selectedType: 'STICKER',      // 'STICKER' | 'CANVAS_SET'
    searchKeyword: '',
    chosenSeriesId: null,
    chosenSeriesType: 'STICKER',
    chosenSeriesName: ''
};

document.addEventListener('DOMContentLoaded', async () => {
    // 注册全局空白处点击与 ESC 按键关闭弹窗事件监听
    setupModalDismissHandlers();
    // 优先加载元数据字典（贴纸/画布系列与商品），再渲染活动列表以确保系列名称与单品名称精准显示
    await loadMetadata();
    await loadPromotions(1);
});

function openCustomConfirm(message, onConfirm) {
    document.getElementById('confirmMessage').textContent = message;
    const modal = document.getElementById('customConfirmModal');
    modal.style.display = 'flex';
    const okBtn = document.getElementById('btnConfirmOK');
    const cancelBtn = document.getElementById('btnConfirmCancel');
    okBtn.onclick = () => {
        modal.style.display = 'none';
        if (onConfirm) onConfirm();
    };
    cancelBtn.onclick = () => {
        modal.style.display = 'none';
    };
}

function setupModalDismissHandlers() {
    // 点击空白遮罩处关闭
    window.addEventListener('click', (e) => {
        const promoModal = document.getElementById('promoModal');
        const seriesPickerModal = document.getElementById('seriesPickerModal');
        const customConfirmModal = document.getElementById('customConfirmModal');
        if (e.target === customConfirmModal) {
            customConfirmModal.style.display = 'none';
        } else if (e.target === seriesPickerModal) {
            closeSeriesPicker();
        } else if (e.target === promoModal) {
            closePromoModal();
        }
    });

    // 按 ESC 键关闭弹出层（优先关闭最顶层确认层，再关闭选择器，最后关闭主弹窗）
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' || e.keyCode === 27) {
            const customConfirmModal = document.getElementById('customConfirmModal');
            const seriesPickerModal = document.getElementById('seriesPickerModal');
            const promoModal = document.getElementById('promoModal');
            if (customConfirmModal && customConfirmModal.style.display !== 'none' && customConfirmModal.style.display !== '') {
                customConfirmModal.style.display = 'none';
            } else if (seriesPickerModal && seriesPickerModal.style.display !== 'none' && seriesPickerModal.style.display !== '') {
                closeSeriesPicker();
            } else if (promoModal && promoModal.style.display !== 'none' && promoModal.style.display !== '') {
                closePromoModal();
            }
        }
    });
}

async function loadMetadata() {
    try {
        const token = localStorage.getItem('token');
        const headers = token ? { 'Authorization': 'Bearer ' + token } : {};

        // 并发加载贴纸系列、画布系列与统一商品
        const [stSeriesRes, cvSeriesRes, itemsRes] = await Promise.all([
            fetch('/api/stickers/config', { headers }).then(r => r.ok ? r.json() : []).catch(() => []),
            fetch('/api/canvases/config', { headers }).then(r => r.ok ? r.json() : []).catch(() => []),
            fetch('/api/shop/items', { headers }).then(r => r.ok ? r.json() : []).catch(() => [])
        ]);

        availableStickerSeries = stSeriesRes || [];
        availableCanvasSeries = cvSeriesRes || [];
        availableShopItems = itemsRes || [];

        // 若促销活动列表已就绪，立即重新渲染以刷新系列名称
        if (allPromotions && allPromotions.length > 0) {
            renderPromotionsList();
        }
    } catch (e) {
        console.error('加载促销元数据失败', e);
    }
}

// 筛选条件状态
let filterState = {
    keyword: '',
    status: '',
    startDate: '',
    endDate: ''
};

async function loadPromotions(page = 1) {
    currentPage = page;
    const container = document.getElementById('promotionsListContainer');
    try {
        const token = localStorage.getItem('token');
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize
        });
        if (filterState.keyword) params.append('keyword', filterState.keyword);
        if (filterState.status) params.append('status', filterState.status);
        if (filterState.startDate) params.append('start_date', filterState.startDate);
        if (filterState.endDate) params.append('end_date', filterState.endDate);

        const res = await fetch(`/api/admin/promotions?${params.toString()}`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!res.ok) throw new Error('获取活动列表失败');
        const data = await res.json();
        allPromotions = data.items || [];
        totalCount = data.total || 0;
        totalPages = data.total_pages || 1;
        renderPromotionsList();
    } catch (err) {
        container.innerHTML = `<div style="text-align: center; padding: 40px; color: #ef4444;">加载失败: ${err.message}</div>`;
    }
}

function applyFilters() {
    const kwInput = document.getElementById('filterKeyword');
    const stSelect = document.getElementById('filterStatus');
    const sdInput = document.getElementById('filterStartDate');
    const edInput = document.getElementById('filterEndDate');

    filterState.keyword = kwInput ? kwInput.value.trim() : '';
    filterState.status = stSelect ? stSelect.value : '';
    filterState.startDate = sdInput ? sdInput.value : '';
    filterState.endDate = edInput ? edInput.value : '';

    loadPromotions(1);
}

function resetFilters() {
    const kwInput = document.getElementById('filterKeyword');
    const stSelect = document.getElementById('filterStatus');
    const sdInput = document.getElementById('filterStartDate');
    const edInput = document.getElementById('filterEndDate');

    if (kwInput) kwInput.value = '';
    if (stSelect) stSelect.value = '';
    if (sdInput) sdInput.value = '';
    if (edInput) edInput.value = '';

    filterState = {
        keyword: '',
        status: '',
        startDate: '',
        endDate: ''
    };

    loadPromotions(1);
}

function changePromoPage(targetPage) {
    if (targetPage < 1 || targetPage > totalPages || targetPage === currentPage) return;
    loadPromotions(targetPage);
}

function changePromoPageSize(newSize) {
    pageSize = parseInt(newSize, 10) || 10;
    currentPage = 1;
    loadPromotions(1);
}


function getPromoStatus(promo) {
    if (!promo.is_active) {
        return { label: '已手动停用', class: 'disabled', icon: '🔴' };
    }
    const now = new Date();
    const start = new Date(promo.start_time);
    const end = new Date(promo.end_time);

    if (now < start) {
        return { label: '未开始', class: 'upcoming', icon: '🟡' };
    } else if (now > end) {
        return { label: '已结束', class: 'ended', icon: '⚪' };
    } else {
        return { label: '进行中', class: 'active', icon: '🟢' };
    }
}

function formatDateTime(isoStr) {
    if (!isoStr) return '--';
    const d = new Date(isoStr);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

function formatRuleSummary(targets) {
    if (!targets || targets.length === 0) return '<span style="color: var(--text-muted);">无生效规则</span>';
    return `<div style="display: flex; flex-direction: column; gap: 4px;">` + targets.map(t => {
        let scopeTxt = '🌟 全场通用';
        if (t.target_scope === 'ITEM_TYPE') {
            scopeTxt = t.target_type === 'STICKER' ? '🎨 所有手账贴纸' : '🖼️ 所有背景画布';
        } else if (t.target_scope === 'SERIES') {
            let seriesList = t.target_type === 'STICKER' ? availableStickerSeries : availableCanvasSeries;
            let ser = seriesList.find(s => String(s.id) === String(t.target_id));
            let finalType = t.target_type;
            if (!ser) {
                const altList = t.target_type === 'STICKER' ? availableCanvasSeries : availableStickerSeries;
                ser = altList.find(s => String(s.id) === String(t.target_id));
                if (ser) {
                    finalType = t.target_type === 'STICKER' ? 'CANVAS_SET' : 'STICKER';
                }
            }
            const name = ser ? ser.name : `系列 #${t.target_id}`;
            const typeLabel = finalType === 'STICKER' ? '贴纸系列' : '画布系列';
            scopeTxt = `📁 [${typeLabel}] ${name}`;
        } else if (t.target_scope === 'SHOP_ITEM') {
            const item = availableShopItems.find(i => String(i.shop_item_id) === String(t.target_id));
            let itemName = item && item.asset ? item.asset.name : null;
            if (!itemName) {
                for (const ser of availableStickerSeries) {
                    const st = (ser.stickers || []).find(s => String(s.id) === String(t.target_id));
                    if (st) { itemName = `${st.name}（${ser.name}）`; break; }
                }
                if (!itemName) {
                    for (const ser of availableCanvasSeries) {
                        const cs = (ser.sets || []).find(s => String(s.id) === String(t.target_id));
                        if (cs) { itemName = `${cs.name}（${ser.name}）`; break; }
                    }
                }
            }
            scopeTxt = `🛍️ [单品] ${itemName || `商品 #${t.target_id}`}`;
        }

        let discTxt = '';
        if (t.fixed_price != null) {
            discTxt = `一口价 <strong>${t.fixed_price}</strong> 蛋能量`;
        } else if (t.discount_rate != null) {
            discTxt = `全场 <strong>${(t.discount_rate * 10).toFixed(1)}</strong> 折`;
        }
        return `<div style="line-height: 1.4;"><span style="color: #8b5cf6;">•</span> ${scopeTxt}（${discTxt}）</div>`;
    }).join('') + `</div>`;
}

function renderPromotionsList() {
    const container = document.getElementById('promotionsListContainer');
    const isFiltered = !!(filterState.keyword || filterState.status || filterState.startDate || filterState.endDate);

    if (!allPromotions || allPromotions.length === 0) {
        if (isFiltered) {
            container.innerHTML = `
                <div style="text-align: center; padding: 60px 20px; background: var(--card-bg, rgba(255,255,255,0.8)); border-radius: 16px; border: 1px dashed var(--card-border, rgba(0,0,0,0.15));">
                    <div style="font-size: 2.5rem; margin-bottom: 12px;">🔍</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: var(--text-main); margin-bottom: 6px;">未找到符合条件的优惠活动</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 16px;">请尝试更换关键字、放宽日期范围或调整活动状态</div>
                    <button class="btn btn-primary-purple" onclick="resetFilters()">↺ 重置筛选条件</button>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div style="text-align: center; padding: 60px 20px; background: var(--card-bg, rgba(255,255,255,0.8)); border-radius: 16px; border: 1px dashed var(--card-border, rgba(0,0,0,0.15));">
                    <div style="font-size: 2.5rem; margin-bottom: 12px;">🏷️</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: var(--text-main); margin-bottom: 6px;">暂无促销活动</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 16px;">点击右上角按钮即可一键配置节日打折或全场大促</div>
                    <button class="btn btn-primary-purple" onclick="openCreatePromotionModal()">创建第一个活动</button>
                </div>
            `;
        }
        return;
    }

    let html = `
        <div class="promo-table-card">
            <table class="promo-table">
                <thead>
                    <tr>
                        <th style="text-align: left; width: 240px; min-width: 180px;">活动名称与文案</th>
                        <th style="text-align: left; width: 185px; min-width: 180px; white-space: nowrap;">活动状态及时间</th>
                        <th style="text-align: left;">优惠规则摘要</th>
                        <th style="width: 75px; min-width: 75px; text-align: center; white-space: nowrap;">操作</th>
                    </tr>
                </thead>
                <tbody>
    `;

    allPromotions.forEach(p => {
        const st = getPromoStatus(p);
        html += `
            <tr>
                <td style="text-align: left;">
                    <div style="font-weight: 800; color: var(--text-main); font-size: 0.95rem;">${p.name}</div>
                    ${p.description ? `<div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 3px;">💬 ${p.description}</div>` : ''}
                </td>
                <td style="text-align: left; line-height: 1.5; white-space: nowrap;">
                    <div style="margin-bottom: 6px;">
                        <span class="promo-badge ${st.class}">
                            ${st.icon} ${st.label}
                        </span>
                    </div>
                    <div style="font-size: 0.82rem; color: var(--text-muted);">起: ${formatDateTime(p.start_time)}</div>
                    <div style="font-size: 0.82rem; color: var(--text-muted);">止: ${formatDateTime(p.end_time)}</div>
                </td>
                <td style="text-align: left; font-size: 0.85rem; color: #7c3aed; font-weight: 600;">
                    ${formatRuleSummary(p.targets)}
                </td>
                <td style="text-align: center; width: 75px; padding: 8px 6px;">
                    <div style="display: flex; flex-direction: column; gap: 6px; align-items: center; justify-content: center;">
                        <button class="btn-sm btn-sm-primary" onclick="openEditPromotionModal(${p.id})" style="padding: 2px 0; font-size: 0.76rem; width: 54px; text-align: center; border-radius: 6px;">编辑</button>
                        <div class="capsule-switch ${p.is_active ? 'active' : 'disabled'}" onclick="togglePromoActive(${p.id}, ${!p.is_active})" title="${p.is_active ? '点击停用活动' : '点击启用活动'}">
                            <span class="capsule-switch-dot"></span>
                            <span class="capsule-switch-text">${p.is_active ? '启用' : '停用'}</span>
                        </div>
                        <button class="btn-sm btn-danger" onclick="deletePromo(${p.id})" style="padding: 2px 0; font-size: 0.76rem; width: 54px; text-align: center; border-radius: 6px;">删除</button>
                    </div>
                </td>
            </tr>
        `;
    });

    html += `</tbody></table>`;

    html += `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 18px; border-top: 1px solid var(--card-border, rgba(0, 0, 0, 0.08)); font-size: 0.85rem; color: var(--text-muted); flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span>共 <strong style="color: var(--text-main);">${totalCount}</strong> 条促销活动</span>
                <span style="color: var(--card-border, rgba(0, 0, 0, 0.15));">|</span>
                <label style="display: inline-flex; align-items: center; gap: 6px;">
                    <span>每页显示</span>
                    <select onchange="changePromoPageSize(this.value)" class="form-control" style="width: auto; padding: 3px 8px; height: 30px; font-size: 0.82rem; border-radius: 6px; cursor: pointer;">
                        <option value="5" ${pageSize === 5 ? 'selected' : ''}>5 条</option>
                        <option value="10" ${pageSize === 10 ? 'selected' : ''}>10 条</option>
                        <option value="20" ${pageSize === 20 ? 'selected' : ''}>20 条</option>
                        <option value="50" ${pageSize === 50 ? 'selected' : ''}>50 条</option>
                    </select>
                </label>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <button class="btn-sm" onclick="changePromoPage(${currentPage - 1})" ${currentPage <= 1 ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''}>上一页</button>
                <span style="font-weight: 700; color: var(--text-main); padding: 0 4px;">${currentPage} / ${totalPages}</span>
                <button class="btn-sm" onclick="changePromoPage(${currentPage + 1})" ${currentPage >= totalPages ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''}>下一页</button>
            </div>
        </div>
    `;

    html += `</div>`;
    container.innerHTML = html;
}

async function togglePromoActive(promoId, isActive) {
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/admin/promotions/${promoId}/toggle-active`, {
            method: 'PATCH',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_active: isActive })
        });
        if (!res.ok) throw new Error('切换状态失败');
        loadPromotions(currentPage);
    } catch (e) {
        alert(e.message);
        loadPromotions(currentPage);
    }
}

async function deletePromo(promoId) {
    const promo = allPromotions.find(p => p.id === promoId);
    const promoName = promo ? `“${promo.name}”` : '';
    openCustomConfirm(`确定要删除优惠活动 ${promoName} 吗？删除后不可恢复。`, async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`/api/admin/promotions/${promoId}`, {
                method: 'DELETE',
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || '删除失败');
            }
            if (typeof showToast === 'function') {
                showToast('优惠活动已删除', 'success');
            }
            loadPromotions(currentPage);
        } catch (e) {
            if (typeof showToast === 'function') {
                showToast(e.message, 'error');
            } else {
                alert(e.message);
            }
        }
    });
}

function toLocalDatetimeInputString(date) {
    const pad = (n) => String(n).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function openCreatePromotionModal() {
    document.getElementById('promoId').value = '';
    document.getElementById('promoModalTitle').textContent = '创建促销活动';
    document.getElementById('promoName').value = '';
    document.getElementById('promoDesc').value = '';

    const now = new Date();
    const nextWeek = new Date(now.getTime() + 7 * 24 * 3600 * 1000);
    document.getElementById('promoStartTime').value = toLocalDatetimeInputString(now);
    document.getElementById('promoEndTime').value = toLocalDatetimeInputString(nextWeek);

    document.getElementById('rulesContainer').innerHTML = '';
    addRuleRow({ target_scope: 'ALL', discount_rate: 0.8 });

    document.getElementById('promoModal').style.display = 'flex';
}

function openEditPromotionModal(promoId) {
    const promo = allPromotions.find(p => p.id === promoId);
    if (!promo) return;

    document.getElementById('promoId').value = promo.id;
    document.getElementById('promoModalTitle').textContent = `编辑促销活动 #${promo.id}`;
    document.getElementById('promoName').value = promo.name;
    document.getElementById('promoDesc').value = promo.description || '';
    document.getElementById('promoStartTime').value = toLocalDatetimeInputString(new Date(promo.start_time));
    document.getElementById('promoEndTime').value = toLocalDatetimeInputString(new Date(promo.end_time));

    const rulesContainer = document.getElementById('rulesContainer');
    rulesContainer.innerHTML = '';
    if (promo.targets && promo.targets.length > 0) {
        promo.targets.forEach(t => addRuleRow(t));
    } else {
        addRuleRow({ target_scope: 'ALL', discount_rate: 0.8 });
    }

    document.getElementById('promoModal').style.display = 'flex';
}

function closePromoModal() {
    document.getElementById('promoModal').style.display = 'none';
}

// ----------------------------------------------------
// 规则配置卡片与交互（系列为最小颗粒度）
// ----------------------------------------------------

function addRuleRow(initData = {}) {
    const container = document.getElementById('rulesContainer');
    const scope = (initData.target_scope === 'SHOP_ITEM' ? 'SERIES' : (initData.target_scope || 'ALL'));
    const rate = initData.discount_rate != null ? (initData.discount_rate * 10).toFixed(1) : '8.0';
    const fixed = initData.fixed_price != null ? initData.fixed_price : '';
    const targetType = initData.target_type || 'STICKER';
    const targetId = initData.target_id || null;

    const row = document.createElement('div');
    row.className = 'rule-item-box';
    row.setAttribute('data-target-id', targetId || '');
    row.setAttribute('data-target-type', targetType);

    row.innerHTML = `
        <button type="button" class="rule-remove-btn" onclick="this.parentElement.remove()" title="移除规则">✕</button>
        <div style="display: grid; grid-template-columns: 1fr 1.3fr; gap: 12px; margin-bottom: 10px;">
            <div>
                <label class="form-label" style="display: block; margin-bottom: 4px;">作用范围</label>
                <select class="form-control rule-scope" onchange="onRuleScopeChange(this)">
                    <option value="ALL" ${scope === 'ALL' ? 'selected' : ''}>🌟 全场通用折扣</option>
                    <option value="ITEM_TYPE" ${scope === 'ITEM_TYPE' ? 'selected' : ''}>📦 按商品大类</option>
                    <option value="SERIES" ${scope === 'SERIES' ? 'selected' : ''}>📁 指定系列优惠</option>
                </select>
            </div>
            
            <div class="rule-target-section">
                <!-- 动态渲染目标选择器 -->
                <div class="scope-all-hint" style="display: ${scope === 'ALL' ? 'block' : 'none'}; padding-top: 24px; font-size: 0.85rem; color: #10b981; font-weight: 700;">
                    ✓ 全场所有贴纸与画布均享此优惠
                </div>
                
                <div class="scope-item-type-box" style="display: ${scope === 'ITEM_TYPE' ? 'block' : 'none'};">
                    <label class="form-label" style="display: block; margin-bottom: 4px;">选择大类</label>
                    <select class="form-control rule-item-type" style="width: 100%;">
                        <option value="STICKER" ${targetType === 'STICKER' ? 'selected' : ''}>🎨 所有手账贴纸</option>
                        <option value="CANVAS_SET" ${targetType === 'CANVAS_SET' ? 'selected' : ''}>🖼️ 所有背景画布</option>
                    </select>
                </div>

                <div class="scope-series-box" style="display: ${scope === 'SERIES' ? 'block' : 'none'};">
                    <label class="form-label" style="display: block; margin-bottom: 4px;">指定优惠系列</label>
                    <div class="target-series-container">
                        <!-- JS 渲染已选系列微卡片或选择按钮 -->
                    </div>
                </div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div>
                <label class="form-label" style="display: block; margin-bottom: 4px;">折扣率 (折，如 8 表示 8折)</label>
                <input type="number" step="0.1" min="0.1" max="9.9" class="form-control rule-rate" value="${rate}" placeholder="例如 8.0">
            </div>
            <div>
                <label class="form-label" style="display: block; margin-bottom: 4px;">或 一口价特惠 (蛋能量整数)</label>
                <input type="number" min="1" class="form-control rule-fixed" value="${fixed}" placeholder="例如 3 (系列全员统一特价)">
            </div>
        </div>
    `;

    container.appendChild(row);
    renderRuleTargetSeriesCard(row, targetType, targetId);
}

function onRuleScopeChange(selectEl) {
    const row = selectEl.closest('.rule-item-box');
    const scope = selectEl.value;
    
    row.querySelector('.scope-all-hint').style.display = (scope === 'ALL') ? 'block' : 'none';
    row.querySelector('.scope-item-type-box').style.display = (scope === 'ITEM_TYPE') ? 'block' : 'none';
    row.querySelector('.scope-series-box').style.display = (scope === 'SERIES') ? 'block' : 'none';

    if (scope === 'SERIES') {
        const currentTargetId = row.getAttribute('data-target-id');
        const currentTargetType = row.getAttribute('data-target-type') || 'STICKER';
        renderRuleTargetSeriesCard(row, currentTargetType, currentTargetId ? parseInt(currentTargetId, 10) : null);
    }
}

function renderRuleTargetSeriesCard(rowBox, seriesType, seriesId) {
    const container = rowBox.querySelector('.target-series-container');
    if (!container) return;

    if (!seriesId) {
        container.innerHTML = `
            <button type="button" class="btn-outline-purple" onclick="openSeriesPicker(this)" style="width: 100%; height: 38px; font-size: 0.85rem; justify-content: center;">
                📁 点击选择系列...
            </button>
        `;
        return;
    }

    let seriesList = (seriesType === 'CANVAS_SET') ? availableCanvasSeries : availableStickerSeries;
    let ser = seriesList.find(s => String(s.id) === String(seriesId));
    let finalType = seriesType;
    if (!ser) {
        const altList = (seriesType === 'CANVAS_SET') ? availableStickerSeries : availableCanvasSeries;
        ser = altList.find(s => String(s.id) === String(seriesId));
        if (ser) {
            finalType = (seriesType === 'CANVAS_SET') ? 'STICKER' : 'CANVAS_SET';
        }
    }
    const name = ser ? ser.name : `系列 #${seriesId}`;
    const typeLabel = (finalType === 'CANVAS_SET') ? '画布系列' : '贴纸系列';
    const count = ser ? (ser.stickers ? ser.stickers.length : (ser.sets ? ser.sets.length : 0)) : 0;

    container.innerHTML = `
        <div class="selected-target-card" style="display: flex; align-items: center; justify-content: space-between; background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 8px; padding: 6px 12px;">
            <div style="display: flex; align-items: center; gap: 8px; overflow: hidden;">
                <span style="font-size: 1.2rem;">📁</span>
                <div>
                    <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-main);">${name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${typeLabel} · 共 ${count} 款</div>
                </div>
            </div>
            <button type="button" class="btn-sm btn-sm-primary" onclick="openSeriesPicker(this)" style="padding: 2px 8px; font-size: 0.78rem;">更换系列</button>
        </div>
    `;
}

// ----------------------------------------------------
// 系列可视化弹出层选择器 (Series Picker)
// ----------------------------------------------------

function openSeriesPicker(triggerEl) {
    const rowBox = triggerEl.closest('.rule-item-box');
    currentPickerState.activeRowBox = rowBox;
    currentPickerState.searchKeyword = '';
    document.getElementById('pickerSearchInput').value = '';

    const currentTargetId = rowBox.getAttribute('data-target-id');
    const currentTargetType = rowBox.getAttribute('data-target-type') || 'STICKER';
    currentPickerState.chosenSeriesId = currentTargetId ? parseInt(currentTargetId, 10) : null;
    currentPickerState.chosenSeriesType = currentTargetType;

    switchSeriesPickerType(currentTargetType);
    document.getElementById('seriesPickerModal').style.display = 'flex';
}

function closeSeriesPicker() {
    document.getElementById('seriesPickerModal').style.display = 'none';
}

function switchSeriesPickerType(itemType) {
    currentPickerState.selectedType = itemType;

    document.getElementById('pickerTabStickers').className = `series-pill ${itemType === 'STICKER' ? 'active' : ''}`;
    document.getElementById('pickerTabCanvases').className = `series-pill ${itemType === 'CANVAS_SET' ? 'active' : ''}`;

    renderSeriesPickerGrid();
}

function renderSeriesPickerGrid() {
    const container = document.getElementById('pickerGridContainer');
    const searchVal = (document.getElementById('pickerSearchInput').value || '').trim().toLowerCase();
    const seriesList = currentPickerState.selectedType === 'STICKER' ? availableStickerSeries : availableCanvasSeries;

    const filtered = seriesList.filter(s => {
        if (!searchVal) return true;
        return (s.name || '').toLowerCase().includes(searchVal);
    });

    if (filtered.length === 0) {
        container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">未找到符合条件的系列</div>`;
        return;
    }

    let html = '';
    filtered.forEach(s => {
        const isSelected = (currentPickerState.chosenSeriesId === s.id && currentPickerState.chosenSeriesType === currentPickerState.selectedType);
        const count = s.stickers ? s.stickers.length : (s.sets ? s.sets.length : 0);
        const typeLabel = currentPickerState.selectedType === 'STICKER' ? '贴纸' : '画布';

        html += `
            <div class="picker-item-card ${isSelected ? 'selected' : ''}" onclick="selectSeriesItem(${s.id}, '${currentPickerState.selectedType}', '${s.name.replace(/'/g, "\\'")}')" style="padding: 14px 10px; cursor: pointer;">
                <div style="font-size: 2rem; margin-bottom: 6px;">📁</div>
                <div class="picker-item-name" title="${s.name}" style="font-weight: 800; font-size: 0.92rem; margin-bottom: 4px;">${s.name}</div>
                <div style="font-size: 0.75rem; color: #8b5cf6; font-weight: 600;">共 ${count} 款${typeLabel}</div>
            </div>
        `;
    });

    container.innerHTML = html;
    updateSeriesPickerSelectedHint();
}

function selectSeriesItem(seriesId, seriesType, seriesName) {
    currentPickerState.chosenSeriesId = seriesId;
    currentPickerState.chosenSeriesType = seriesType;
    currentPickerState.chosenSeriesName = seriesName;
    renderSeriesPickerGrid();
}

function updateSeriesPickerSelectedHint() {
    const hintEl = document.getElementById('pickerSelectedHint');
    if (!currentPickerState.chosenSeriesId) {
        hintEl.innerHTML = `<span style="color: var(--text-muted);">尚未选择系列</span>`;
        return;
    }
    const typeLabel = currentPickerState.chosenSeriesType === 'STICKER' ? '贴纸系列' : '画布系列';
    hintEl.innerHTML = `已选择：<strong style="color: #8b5cf6;">【${currentPickerState.chosenSeriesName}】</strong>（${typeLabel}）`;
}

function confirmSeriesSelection() {
    if (!currentPickerState.chosenSeriesId) {
        return alert('请先在列表中点击选择一个系列');
    }
    if (currentPickerState.activeRowBox) {
        currentPickerState.activeRowBox.setAttribute('data-target-id', currentPickerState.chosenSeriesId);
        currentPickerState.activeRowBox.setAttribute('data-target-type', currentPickerState.chosenSeriesType);
        renderRuleTargetSeriesCard(currentPickerState.activeRowBox, currentPickerState.chosenSeriesType, currentPickerState.chosenSeriesId);
    }
    closeSeriesPicker();
}

// ----------------------------------------------------
// 提交促销活动表单
// ----------------------------------------------------

async function submitPromoForm() {
    const promoId = document.getElementById('promoId').value;
    const name = document.getElementById('promoName').value.trim();
    const description = document.getElementById('promoDesc').value.trim();
    const startTime = document.getElementById('promoStartTime').value;
    const endTime = document.getElementById('promoEndTime').value;

    if (!name) return alert('请输入活动名称');
    if (!startTime || !endTime) return alert('请选择完整的活动起止时间');

    const ruleBoxes = document.querySelectorAll('.rule-item-box');
    const targets = [];

    for (const box of ruleBoxes) {
        const scope = box.querySelector('.rule-scope').value;
        const rateVal = parseFloat(box.querySelector('.rule-rate').value);
        const fixedVal = parseInt(box.querySelector('.rule-fixed').value, 10);

        const targetData = { target_scope: scope };

        if (!isNaN(fixedVal) && fixedVal > 0) {
            targetData.fixed_price = fixedVal;
        } else if (!isNaN(rateVal) && rateVal > 0) {
            targetData.discount_rate = parseFloat((rateVal / 10).toFixed(2));
        }

        if (scope === 'ITEM_TYPE') {
            targetData.target_type = box.querySelector('.rule-item-type').value;
        } else if (scope === 'SERIES') {
            const targetId = parseInt(box.getAttribute('data-target-id'), 10);
            const targetType = box.getAttribute('data-target-type') || 'STICKER';
            if (!targetId || isNaN(targetId)) {
                return alert('请为“指定系列优惠”规则选择具体的系列目标！');
            }
            targetData.target_type = targetType;
            targetData.target_id = targetId;
        }

        targets.push(targetData);
    }

    if (targets.length === 0) {
        return alert('请至少配置一条优惠规则');
    }

    const payload = {
        name,
        description,
        start_time: new Date(startTime).toISOString(),
        end_time: new Date(endTime).toISOString(),
        is_active: true,
        targets
    };

    try {
        const token = localStorage.getItem('token');
        const url = promoId ? `/api/admin/promotions/${promoId}` : '/api/admin/promotions';
        const method = promoId ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method,
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '保存活动失败');
        }

        closePromoModal();
        loadPromotions();
    } catch (e) {
        alert(e.message);
    }
}
