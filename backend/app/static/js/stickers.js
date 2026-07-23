document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    const seriesNavList = document.getElementById('seriesNavList');
    const panelTitle = document.getElementById('panelTitle');
    const panelStats = document.getElementById('panelStats');
    const stickersGrid = document.getElementById('stickersGrid');

    let currentEnergy = 0;
    let inventoryMap = new Map();
    let allSeriesConfig = [];
    let activeSeriesId = 'ALL'; // 默认展示“全部已有”页签

    // 网页Toast提示
    function webShowToast(message, type = 'success') {
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            alert(message);
        }
    }

    // 核心加载逻辑
    async function loadPageData() {
        try {
            // 1. 拉取用户贴纸资产和蛋能量
            const invRes = await fetch('/api/stickers/inventory', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (!invRes.ok) throw new Error("获取资产数据失败");
            const assetData = await invRes.json();
            currentEnergy = assetData.egg_energy || 0;

            inventoryMap.clear();
            const rawInventory = assetData.sticker_inventory || "";
            if (rawInventory.trim().length > 0) {
                rawInventory.split(',').forEach(p => {
                    const kv = p.split(':');
                    if (kv.length === 2) {
                        inventoryMap.set(parseInt(kv[0].trim()), parseInt(kv[1].trim()) || 0);
                    }
                });
            }

            // 2. 拉取全量系列与贴纸配置
            const configRes = await fetch('/api/stickers/config', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (!configRes.ok) throw new Error("获取配置清单失败");
            allSeriesConfig = await configRes.json();

            // 3. 构建左侧系列选单与右侧展现
            renderSeriesNav();
            renderSelectedPanel();

        } catch (e) {
            console.error('加载贴纸数据失败:', e);
            stickersGrid.innerHTML = `
                <div style="grid-column: 1/-1; padding: 40px; text-align: center; color: #f87171; font-weight: bold; background: rgba(239, 68, 68, 0.05); border: 1px dashed rgba(239, 68, 68, 0.2); border-radius: 12px;">
                    ⚠️ 获取贴纸数据失败：${e.message}。请稍后刷新重试。
                </div>
            `;
        }
    }

    // 计算某个系列下“持存品种数”（持存数量 > 0 的贴纸款数）
    function getOwnedDistinctCount(seriesStickers) {
        if (!seriesStickers) return 0;
        return seriesStickers.filter(s => (inventoryMap.get(s.id) || 0) > 0).length;
    }

    // 计算全馆“持存总品种数”与“总款式数”
    function getTotalStats() {
        let ownedDistinct = 0;
        let totalCount = 0;
        allSeriesConfig.forEach(series => {
            if (series.stickers) {
                series.stickers.forEach(s => {
                    totalCount++;
                    if ((inventoryMap.get(s.id) || 0) > 0) {
                        ownedDistinct++;
                    }
                });
            }
        });
        return { ownedDistinct, totalCount };
    }

    // 渲染左侧分类选单
    function renderSeriesNav() {
        seriesNavList.innerHTML = '';

        if (!allSeriesConfig || allSeriesConfig.length === 0) {
            seriesNavList.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 10px;">暂无分类</div>`;
            return;
        }

        const totalStats = getTotalStats();

        // 1. “全部已有”全馆标签
        const allNavItem = document.createElement('div');
        allNavItem.className = `series-nav-item ${activeSeriesId === 'ALL' ? 'active' : ''}`;
        allNavItem.innerHTML = `
            <span>🌟 全部已有</span>
            <span class="series-badge">(${totalStats.ownedDistinct}/${totalStats.totalCount})</span>
        `;
        allNavItem.addEventListener('click', () => {
            activeSeriesId = 'ALL';
            renderSeriesNav();
            renderSelectedPanel();
        });
        seriesNavList.appendChild(allNavItem);

        // 2. 各个分类系列标签
        allSeriesConfig.forEach(series => {
            const ownedDistinct = getOwnedDistinctCount(series.stickers);
            const totalInSeries = series.stickers ? series.stickers.length : 0;
            const navItem = document.createElement('div');
            navItem.className = `series-nav-item ${activeSeriesId === series.id ? 'active' : ''}`;
            navItem.innerHTML = `
                <span>📦 ${series.name}</span>
                <span class="series-badge">(${ownedDistinct}/${totalInSeries})</span>
            `;
            navItem.addEventListener('click', () => {
                activeSeriesId = series.id;
                renderSeriesNav();
                renderSelectedPanel();
            });
            seriesNavList.appendChild(navItem);
        });
    }

    // 渲染右侧面板主内容
    function renderSelectedPanel() {
        stickersGrid.innerHTML = '';

        if (activeSeriesId === 'ALL') {
            const totalStats = getTotalStats();
            panelTitle.innerHTML = `<span>🌟</span> 全部已有贴纸`;
            panelStats.textContent = `已收集 ${totalStats.ownedDistinct} 款 / 全馆共 ${totalStats.totalCount} 款`;

            // 收集所有拥有数量 > 0 的贴纸
            const ownedStickers = [];
            allSeriesConfig.forEach(series => {
                if (series.stickers) {
                    series.stickers.forEach(s => {
                        const count = inventoryMap.get(s.id) || 0;
                        if (count > 0) {
                            ownedStickers.push({ ...s, count });
                        }
                    });
                }
            });

            if (ownedStickers.length === 0) {
                stickersGrid.innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 50px 20px;">
                        手头暂时还没有已拥有的贴纸哦，快去手机写日记积累能量吧！
                    </div>
                `;
                return;
            }

            ownedStickers.forEach(sticker => {
                renderSingleStickerCard(sticker, sticker.count, stickersGrid);
            });

        } else {
            const currentSeries = allSeriesConfig.find(s => s.id === activeSeriesId);
            if (!currentSeries) return;

            const ownedDistinct = getOwnedDistinctCount(currentSeries.stickers);
            const totalInSeries = currentSeries.stickers ? currentSeries.stickers.length : 0;

            panelTitle.innerHTML = `<span>📦</span> ${currentSeries.name}`;
            panelStats.textContent = `已收集 ${ownedDistinct} 款 / 本系列共 ${totalInSeries} 款`;

            if (!currentSeries.stickers || currentSeries.stickers.length === 0) {
                stickersGrid.innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 50px 20px;">
                        该系列暂时还没有贴纸哦
                    </div>
                `;
                return;
            }

            currentSeries.stickers.forEach(sticker => {
                const count = inventoryMap.get(sticker.id) || 0;
                renderSingleStickerCard(sticker, count, stickersGrid);
            });
        }
    }

    // 渲染单个贴纸卡片 (保持 100% 原有视觉属性)
    function renderSingleStickerCard(sticker, count, container) {
        const isLocked = count <= 0;

        const itemCard = document.createElement('div');
        itemCard.className = `sticker-item ${isLocked ? 'locked' : ''}`;

        // 圆形红底白字角标
        const badgeHtml = !isLocked ? `<div class="count-badge">${count}</div>` : '';

        // 卡片下方标价/描述区域 (保持原有元素)
        let actionHtml = '';
        if (isLocked) {
            const canAfford = currentEnergy >= sticker.exchange_price;
            actionHtml = `
                <button class="exchange-action-btn" 
                        data-id="${sticker.id}" 
                        data-name="${sticker.name}" 
                        data-price="${sticker.exchange_price}" 
                        style="margin-top: 10px; font-size: 0.72rem; padding: 4px 10px; border-radius: 8px; border: 1px solid ${canAfford ? 'var(--primary)' : 'rgba(255,255,255,0.08)'}; background: ${canAfford ? 'rgba(139, 92, 246, 0.15)' : 'rgba(255,255,255,0.02)'}; color: ${canAfford ? '#c084fc' : 'var(--text-muted)'}; cursor: ${canAfford ? 'pointer' : 'not-allowed'}; font-weight: bold; transition: all 0.2s;" 
                        ${canAfford ? '' : 'disabled'}>
                    兑换 ( 🥚 ${sticker.exchange_price} )
                </button>
            `;
        } else {
            actionHtml = `<div class="sticker-desc" style="margin-top: 6px;">${sticker.description || '精美手账装饰贴纸'}</div>`;
        }

        let imgPath = sticker.image_url;
        if (imgPath && !imgPath.startsWith('/static/')) {
            imgPath = '/static/images/dinosaurs/' + imgPath;
        }

        itemCard.innerHTML = `
            ${badgeHtml}
            <img class="sticker-img" src="${imgPath}" alt="${sticker.name}" loading="lazy" onerror="this.src='/static/images/ic_launcher.png'" />
            <div class="sticker-name">${sticker.name}</div>
            ${actionHtml}
        `;

        // 如果用户在未持有的卡片上点击兑换，绑定兑换响应
        const exchangeBtn = itemCard.querySelector('.exchange-action-btn');
        if (exchangeBtn) {
            exchangeBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const stickerId = parseInt(exchangeBtn.getAttribute('data-id'));
                const stickerName = exchangeBtn.getAttribute('data-name');
                const price = parseInt(exchangeBtn.getAttribute('data-price'));

                if (confirm(`✨ 确认使用 ${price} 蛋能量，兑换一只心仪的【${stickerName}】贴纸守护你吗？`)) {
                    try {
                        const res = await fetch('/api/stickers/exchange', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + token
                            },
                            body: JSON.stringify({ sticker_id: stickerId })
                        });

                        if (!res.ok) {
                            const err = await res.json();
                            throw new Error(err.detail || "兑换交易失败");
                        }

                        webShowToast(`兑换成功！【${stickerName}】已送入你的手账箱！`, "success");
                        loadPageData();
                    } catch(err) {
                        webShowToast("兑换失败：" + err.message, "error");
                    }
                }
            });
        }

        container.appendChild(itemCard);
    }

    loadPageData();
});
