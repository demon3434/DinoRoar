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
    const onlyOwnedBtn = document.getElementById('onlyOwnedBtn');

    let currentEnergy = 0;
    let inventoryMap = new Map();
    let allSeriesConfig = [];
    let activeSeriesId = null;
    let onlyOwned = false;

    if (onlyOwnedBtn) {
        onlyOwnedBtn.addEventListener('click', () => {
            onlyOwned = !onlyOwned;
            updateOnlyOwnedBtnState();
            renderSelectedPanel();
        });
    }

    function updateOnlyOwnedBtnState() {
        if (!onlyOwnedBtn) return;
        if (onlyOwned) {
            onlyOwnedBtn.classList.add('active');
            onlyOwnedBtn.textContent = '✓ 已拥有';
        } else {
            onlyOwnedBtn.classList.remove('active');
            onlyOwnedBtn.textContent = '已拥有';
        }
    }

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

            if (allSeriesConfig && allSeriesConfig.length > 0 && !activeSeriesId) {
                activeSeriesId = allSeriesConfig[0].id;
            }

            // 3. 构建左侧系列选单与右侧展现
            renderSeriesNav();
            renderSelectedPanel();
            loadPromoBanner();

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

        // 各个分类系列标签
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
        const totalStats = getTotalStats();

        const currentSeries = allSeriesConfig.find(s => s.id === activeSeriesId) || allSeriesConfig[0];
        if (!currentSeries) {
            panelTitle.innerHTML = `<span>🎨</span> 贴纸商城`;
            panelStats.textContent = `已收集 ${totalStats.ownedDistinct} 款 / 全馆共 ${totalStats.totalCount} 款`;
            return;
        }

        panelTitle.innerHTML = `<span>📦</span> ${currentSeries.name}`;
        panelStats.textContent = `已收集 ${totalStats.ownedDistinct} 款 / 全馆共 ${totalStats.totalCount} 款`;

        let stickersToRender = (currentSeries.stickers || []).filter(s => s.is_active && !s.is_deleted);
        if (onlyOwned) {
            stickersToRender = stickersToRender.filter(s => (inventoryMap.get(s.id) || 0) > 0);
        }

        if (stickersToRender.length === 0) {
            stickersGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 50px 20px;">
                    ${onlyOwned ? '该系列下暂无已拥有的贴纸，快去兑换吧！' : '该系列暂时还没有贴纸哦'}
                </div>
            `;
            return;
        }

        stickersToRender.forEach(sticker => {
            const count = inventoryMap.get(sticker.id) || 0;
            renderSingleStickerCard(sticker, count, stickersGrid);
        });
    }


    // 渲染单个贴纸卡片
    function renderSingleStickerCard(sticker, count, container) {
        const itemCard = document.createElement('div');
        itemCard.className = 'sticker-item';

        // 圆形红底白字持有数量角标 (大于0时展示)
        const badgeHtml = count > 0 ? `<div class="count-badge">${count}</div>` : '';

        // 价格显示 (支持原价删除线与特惠标签)
        const isOnSale = sticker.is_on_sale && sticker.original_price && sticker.original_price > sticker.exchange_price;
        let priceHtml = `🥚 ${sticker.exchange_price} 能量`;
        if (isOnSale) {
            priceHtml = `🥚 <strong style="color: #8b5cf6; font-size: 0.95rem;">${sticker.exchange_price}</strong> <del style="text-decoration: line-through; opacity: 0.5; margin-left: 3px; font-size: 0.75rem;">${sticker.original_price}</del> <span style="background: rgba(239, 68, 68, 0.15); color: #ef4444; font-size: 0.68rem; padding: 1px 4px; border-radius: 4px; font-weight: 800; margin-left: 3px;">特惠</span>`;
        }

        const canAfford = currentEnergy >= sticker.exchange_price;
        const actionHtml = `
            <div class="sticker-action-area">
                <div class="sticker-price">${priceHtml}</div>
                <button class="sticker-exchange-btn" 
                        data-id="${sticker.id}" 
                        data-name="${sticker.name}" 
                        data-price="${sticker.exchange_price}"
                        data-orig="${sticker.original_price || sticker.exchange_price}"
                        data-sale="${isOnSale ? '1' : '0'}"
                        ${canAfford ? '' : 'disabled'}>
                    ${canAfford ? '兑换' : '能量不足'}
                </button>
            </div>
        `;

        let imgPath = sticker.image_url;
        if (imgPath && !imgPath.startsWith('/static/')) {
            imgPath = '/static/images/dinosaurs/' + imgPath;
        }

        itemCard.innerHTML = `
            ${badgeHtml}
            <img class="sticker-img" src="${imgPath}" alt="${sticker.name}" loading="lazy" onerror="this.src='/static/images/ic_launcher.png'" />
            <div class="sticker-name">${sticker.name}</div>
            <div class="sticker-desc">${sticker.description || '精美手账装饰贴纸'}</div>
            ${actionHtml}
        `;

        // 绑定兑换响应
        const exchangeBtn = itemCard.querySelector('.sticker-exchange-btn');
        if (exchangeBtn && canAfford) {
            exchangeBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const stickerId = parseInt(exchangeBtn.getAttribute('data-id'));
                const stickerName = exchangeBtn.getAttribute('data-name');
                const price = parseInt(exchangeBtn.getAttribute('data-price'));
                const orig = parseInt(exchangeBtn.getAttribute('data-orig'));
                const isSale = exchangeBtn.getAttribute('data-sale') === '1';

                let promptMsg = `确认使用 🥚${price} 蛋能量兑换贴纸《${stickerName}》吗？\n兑换后将放入您的贴纸箱！`;
                if (isSale && orig > price) {
                    const saved = orig - price;
                    promptMsg = `✨ 节日特惠兑换贴纸《${stickerName}》\n原价：${orig} 蛋能量\n特惠实付：${price} 蛋能量\n🎉 本次兑换为您立省 ${saved} 蛋能量！\n\n确认立即兑换吗？`;
                }

                const confirmed = await showConfirmModal(promptMsg, "🎯 确认兑换贴纸");
                if (confirmed) {
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


                        webShowToast(`🎉 兑换成功！《${stickerName}》已放入手账贴纸箱！`, "success");
                        loadPageData();
                    } catch(err) {
                        webShowToast("兑换失败：" + err.message, "error");
                    }
                }
            });
        }

        container.appendChild(itemCard);
    }

    async function loadPromoBanner() {
        try {
            const res = await fetch('/api/promotions/active-summary');
            if (!res.ok) return;
            const promos = await res.json();
            const bannerContainer = document.getElementById('promoBannerContainer');
            const bannerText = document.getElementById('promoBannerText');
            if (bannerContainer && bannerText && promos && promos.length > 0) {
                const descList = promos.map(p => {
                    const rText = (p.rules_summary && p.rules_summary.length > 0) ? p.rules_summary.join('，') : p.description;
                    return rText ? `${p.name}（${rText}）` : p.name;
                }).join('； ');
                bannerText.textContent = `节日特惠活动进行中：${descList}`;
                bannerContainer.style.display = 'flex';
            }

        } catch (e) {
            console.error('加载促销横幅失败:', e);
        }
    }

    // 自定义弹出式确认对话框
    function showConfirmModal(message, title = "🎉 确认兑换") {
        return new Promise(resolve => {
            const modal = document.getElementById("confirmModal");
            if (!modal) {
                resolve(confirm(message));
                return;
            }

            const titleEl = document.getElementById("confirmModalTitle");
            const msgEl = document.getElementById("confirmModalMessage");
            const okBtn = document.getElementById("confirmModalConfirmBtn");
            const cancelBtn = document.getElementById("confirmModalCancelBtn");

            if (titleEl) {
                titleEl.textContent = title;
                titleEl.style.color = "var(--text-main)";
            }
            if (msgEl) {
                msgEl.textContent = message;
                msgEl.style.color = "var(--text-main)";
            }
            if (okBtn) {
                okBtn.textContent = "✨ 立即兑换";
                okBtn.style.background = "linear-gradient(135deg, #8b5cf6, #7c3aed)";
                okBtn.style.color = "#ffffff";
            }

            modal.style.display = "flex";

            const handleOk = () => {
                modal.style.display = "none";
                cleanup();
                resolve(true);
            };
            const handleCancel = () => {
                modal.style.display = "none";
                cleanup();
                resolve(false);
            };

            function cleanup() {
                okBtn.removeEventListener("click", handleOk);
                cancelBtn.removeEventListener("click", handleCancel);
            }

            okBtn.addEventListener("click", handleOk);
            cancelBtn.addEventListener("click", handleCancel);
        });
    }

    loadPageData();
});



