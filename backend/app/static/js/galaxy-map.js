function renderGalaxyMap(svg, stats) {
    if (!svg) return;
    svg.innerHTML = '';
    const width = svg.clientWidth || 300;
    const height = svg.clientHeight || 300;
    const cx = width / 2;
    const cy = height / 2;

    const colorMap = {
        red: '#ef4444',
        orange: '#f97316',
        yellow: '#facc15',
        green: '#22c55e',
        blue: '#3b82f6',
        purple: '#a855f7',
        gray: '#64748b',
        me: '#eab308'
    };

    const nodes = stats.relationship_galaxy.nodes || [];
    const links = stats.relationship_galaxy.links || [];

    // Draw me (center background glow)
    const glow = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    glow.setAttribute('cx', cx);
    glow.setAttribute('cy', cy);
    glow.setAttribute('r', '32');
    glow.setAttribute('fill', 'rgba(234, 179, 8, 0.15)');
    glow.setAttribute('class', 'galaxy-pulse-glow');
    glow.style.transformOrigin = `${cx}px ${cy}px`;
    svg.appendChild(glow);

    // Draw Links
    links.forEach(link => {
        const targetNode = nodes.find(n => n.id === link.target);
        if (targetNode) {
            const index = nodes.indexOf(targetNode) - 1;
            const count = nodes.length - 1;
            const angle = (index * 2 * Math.PI) / count;
            const distance = 110 - Math.min(6, link.weight) * 6;
            
            const tx = cx + Math.cos(angle) * distance;
            const ty = cy + Math.sin(angle) * distance;

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', cx);
            line.setAttribute('y1', cy);
            line.setAttribute('x2', tx);
            line.setAttribute('y2', ty);
            line.setAttribute('stroke', colorMap[targetNode.color_tag] || '#fff');
            line.setAttribute('stroke-width', Math.min(5, 1.5 + link.weight * 0.7));
            line.setAttribute('opacity', '0.55');
            line.setAttribute('class', 'galaxy-flow-line');
            svg.appendChild(line);
        }
    });

    // Draw Nodes
    nodes.forEach((node, index) => {
        let nx = cx;
        let ny = cy;
        
        if (node.id !== 'child') {
            const count = nodes.length - 1;
            const angle = ((index - 1) * 2 * Math.PI) / count;
            const linkObj = links.find(l => l.target === node.id);
            const weight = linkObj ? linkObj.weight : 1;
            const distance = 110 - Math.min(6, weight) * 6;
            
            nx = cx + Math.cos(angle) * distance;
            ny = cy + Math.sin(angle) * distance;
        }

        const isMe = node.id === 'child';
        const radius = isMe ? 18 : 13;
        const color = colorMap[node.color_tag] || '#fff';

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.style.cursor = 'pointer';

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', nx);
        circle.setAttribute('cy', ny);
        circle.setAttribute('r', radius);
        circle.setAttribute('fill', color);
        circle.setAttribute('stroke', 'rgba(255,255,255,0.25)');
        circle.setAttribute('stroke-width', '2');
        circle.setAttribute('class', 'galaxy-node');
        circle.setAttribute('color', color);
        g.appendChild(circle);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', nx);
        text.setAttribute('y', ny + 4);
        text.setAttribute('fill', isMe ? '#000' : '#fff');
        text.setAttribute('font-size', isMe ? '10px' : '9px');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('text-anchor', 'middle');
        text.textContent = node.name.substring(0, 1);
        g.appendChild(text);

        g.addEventListener('click', () => {
            if (!isMe) {
                const linkObj = links.find(l => l.target === node.id);
                const weight = linkObj ? linkObj.weight : 1;
                showBendingHandBook(node, weight);
            }
        });

        if (!isMe) {
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', nx);
            label.setAttribute('y', ny + radius + 11);
            label.setAttribute('fill', 'var(--text-muted)');
            label.setAttribute('font-size', '8px');
            label.setAttribute('text-anchor', 'middle');
            label.textContent = node.name;
            svg.appendChild(label);
        }

        svg.appendChild(g);
    });
}

function showBendingHandBook(node, weight) {
    const levels = ['初识萌芽 🌱', '玩耍伙伴 🌿', '深厚友情 🌸', '黄金搭档 ✨', '挚友知己 🏆'];
    const levelIdx = Math.min(levels.length - 1, Math.floor(weight / 2));
    const bendingText = levels[levelIdx];

    const happyCount = node.happy_count || 0;
    const sadCount = node.sad_count || 0;
    const totalCount = happyCount + sadCount;

    const starCount = happyCount > 0 ? Math.min(5, Math.ceil(happyCount / 2)) : 0;
    const fireCount = weight > 0 ? Math.min(5, Math.ceil(weight / 4)) : 0;
    const eggCount = sadCount > 0 ? Math.min(5, Math.ceil(sadCount / 2)) : 0;

    const starsHtml = starCount > 0 ? '⭐'.repeat(starCount) : '<span style="color:var(--text-muted); opacity:0.4;">无</span>';
    const firesHtml = fireCount > 0 ? '🔥'.repeat(fireCount) : '<span style="color:var(--text-muted); opacity:0.4;">无</span>';
    const eggsHtml = eggCount > 0 ? '🥚'.repeat(eggCount) : '<span style="color:var(--text-muted); opacity:0.4;">无</span>';

    let moodReport = '你们刚开始种下友谊的种子，多和 ta 聊天写写日记吧！🌱';
    let cardIcon = '🌱';

    if (totalCount > 0) {
        if (eggCount >= 3) {
            cardIcon = '🌧️';
            moodReport = `最近和 ta 在一起的时光似乎有些多云转雷雨 🌧️。记录里包含了不少别扭或委屈（共 ${sadCount} 次）。要不要主动送 ta 一个暖暖的拥抱来和好呢？`;
        } else if (starCount >= 3 && eggCount <= 1) {
            cardIcon = '⭐';
            moodReport = `ta 绝对是你的超级晴天星！每次提到 ta，日记本里都洒满了金灿灿的太阳光 ✨（共记录了 ${happyCount} 次晴天陪伴）！`;
        } else if (starCount >= 2 && eggCount >= 2) {
            cardIcon = '🔥';
            moodReport = `你们真是欢喜冤家！相爱相杀，在一起时快乐大笑不断（${happyCount}次），小摩擦也不少（${sadCount}次），但拌嘴之后羁绊反而更火热了！`;
        } else {
            cardIcon = '✨';
            moodReport = `陪伴细水长流，你们在日记本里温馨而平稳地度过。共同面朝晴天 ${happyCount} 次，面朝雷雨 ${sadCount} 次。`;
        }
    }

    let modal = document.getElementById('handbookModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'handbookModal';
        modal.style = 'display:none; position:fixed; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.5); align-items:center; justify-content:center; z-index:9999; backdrop-filter:blur(5px); transition: opacity 0.3s;';
        document.body.appendChild(modal);
    }
    
    const happyPercent = totalCount > 0 ? Math.round((happyCount / totalCount) * 100) : 100;
    const sadPercent = totalCount > 0 ? 100 - happyPercent : 0;
    
    const progressHtml = totalCount > 0 ? `
        <div style="margin-top: 10px; border-top: 1px dashed var(--card-border); padding-top: 8px;">
            <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:var(--text-muted); margin-bottom:4px;">
                <span>☀️ 晴天陪伴: ${happyCount}次 (${happyPercent}%)</span>
                <span>🌧️ 雷雨共面: ${sadCount}次 (${sadPercent}%)</span>
            </div>
            <div style="width:100%; height:6px; border-radius:3px; background:#ef4444; overflow:hidden; display:flex; border:1px solid rgba(255,255,255,0.03);">
                <div style="width:${happyPercent}%; height:100%; background:#22c55e; transition: width 0.3s;"></div>
            </div>
        </div>
    ` : '';

    modal.innerHTML = `
        <div class="card" style="width:340px; padding:25px; border:1px solid var(--card-border); background:var(--card-bg); text-align:center; box-shadow:0 15px 35px rgba(0,0,0,0.3); border-radius:24px; position:relative; animation: zoomIn 0.3s ease;">
            <div style="font-size:2rem; margin-bottom:12px;">${cardIcon}</div>
            <h3 style="font-size:1.3rem; font-weight:800; color:var(--text-main); margin-bottom:6px;">${node.name} 的羁绊手账</h3>
            <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:18px;">秘密基地关系星座小岛</p>
            
            <div style="background:rgba(120,120,120,0.06); padding:14px; border-radius:16px; margin-bottom:20px; text-align:left; font-size:0.85rem; border:1px solid var(--card-border); display:flex; flex-direction:column; gap:8px;">
                <div><strong>羁绊等级：</strong><span style="color:var(--accent-sunny); font-weight:bold;">${bendingText}</span></div>
                <div><strong>陪伴热度：</strong><span>共同记录过 <strong>${weight}</strong> 次</span></div>
                
                <div style="border-top:1px dashed var(--card-border); margin-top:4px; padding-top:6px; display:flex; flex-direction:column; gap:4px; font-size:0.8rem;">
                    <div style="display:flex; justify-content:space-between;"><span>🌟 晴天小星星：</span><span>${starsHtml}</span></div>
                    <div style="display:flex; justify-content:space-between;"><span>💥 友情小火苗：</span><span>${firesHtml}</span></div>
                    <div style="display:flex; justify-content:space-between;"><span>🌧️ 雷雨臭鸡蛋：</span><span>${eggsHtml}</span></div>
                </div>

                ${progressHtml}
                
                <div style="border-top:1px dashed var(--card-border); margin-top:6px; padding-top:8px; line-height:1.4; color:var(--text-main); font-style:italic;">
                    ${moodReport}
                </div>
            </div>
            
            <div style="display:flex; gap:10px; justify-content:center;">
                <button onclick="document.getElementById('handbookModal').style.display='none'" style="padding:8px 16px; border-radius:10px; border:1px solid var(--card-border); background:rgba(255,255,255,0.05); color:var(--text-main); cursor:pointer; font-size:0.85rem; font-weight:bold;">关闭</button>
                <button id="goToDiaryBtn" style="padding:8px 16px; border-radius:10px; border:none; background:var(--accent-sunny); color:#000; cursor:pointer; font-size:0.85rem; font-weight:bold;">翻看日记</button>
            </div>
        </div>
    `;
    
    document.getElementById('goToDiaryBtn').onclick = () => {
        modal.style.display = 'none';
        window.location.href = `/diary?person_uuid=${node.id}`;
    };

    modal.style.display = 'flex';
}

function showOverviewGuide(type) {
    let modal = document.getElementById('handbookModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'handbookModal';
        modal.style = 'display:none; position:fixed; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.5); align-items:center; justify-content:center; z-index:9999; backdrop-filter:blur(5px); transition: opacity 0.3s;';
        document.body.appendChild(modal);
    }

    if (type === 'mood') {
        modal.innerHTML = `
            <div class="card" style="width:360px; padding:25px; border:1px solid var(--card-border); background:var(--card-bg); text-align:center; box-shadow:0 15px 35px rgba(0,0,0,0.3); border-radius:24px; position:relative; animation: zoomIn 0.3s ease;">
                <div style="font-size:2.2rem; margin-bottom:12px;">🍯</div>
                <h3 style="font-size:1.3rem; font-weight:800; color:var(--text-main); margin-bottom:6px;">心情晴雨气球罐</h3>
                <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:18px;">最近30天情绪穿梭魔法瓶</p>
                
                <div style="background:rgba(120,120,120,0.06); padding:14px; border-radius:16px; margin-bottom:20px; text-align:left; font-size:0.85rem; border:1px solid var(--card-border); line-height:1.6; color:var(--text-main); display:flex; flex-direction:column; gap:8px;">
                    <div>🦕 <strong>它是什么？</strong><br/>你在手机端保存的每一次心情记录，都会化作一只彩色情绪气球，浮入玻璃罐中。</div>
                    <div>🎈 <strong>气球色彩情绪：</strong><br/>
                    • <span style="color:#22c55e; font-weight:bold;">晴天气球 (绿色)</span>：快乐、兴奋、得意<br/>
                    • <span style="color:#f59e0b; font-weight:bold;">多云气球 (黄色)</span>：一般、惊讶<br/>
                    • <span style="color:#3b82f6; font-weight:bold;">细雨气球 (蓝色)</span>：紧张、遗憾、后悔<br/>
                    • <span style="color:#ef4444; font-weight:bold;">雷雨气球 (红色)</span>：伤心、愤怒</div>
                    <div>📅 <strong>怎么看时间？</strong><br/>气球下系着日期签，沿左往右依次飘动。越往右说明日期越近（最右侧为今日）。</div>
                </div>
                
                <button onclick="document.getElementById('handbookModal').style.display='none'" style="padding:8px 24px; border-radius:10px; border:none; background:var(--accent-sunny); color:#000; cursor:pointer; font-size:0.85rem; font-weight:bold;">我知道啦</button>
            </div>
        `;
    } else if (type === 'galaxy') {
        modal.innerHTML = `
            <div class="card" style="width:360px; padding:25px; border:1px solid var(--card-border); background:var(--card-bg); text-align:center; box-shadow:0 15px 35px rgba(0,0,0,0.3); border-radius:24px; position:relative; animation: zoomIn 0.3s ease;">
                <div style="font-size:2.2rem; margin-bottom:12px;">🌌</div>
                <h3 style="font-size:1.3rem; font-weight:800; color:var(--text-main); margin-bottom:6px;">亲密人际拓扑星云</h3>
                <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:18px;">秘密小岛社交星座连线</p>
                
                <div style="background:rgba(120,120,120,0.06); padding:14px; border-radius:16px; margin-bottom:20px; text-align:left; font-size:0.85rem; border:1px solid var(--card-border); line-height:1.6; color:var(--text-main); display:flex; flex-direction:column; gap:8px;">
                    <div>✨ <strong>星子与引力：</strong><br/>中心的金星代表你自己，周围飘浮的星子是你日记中提到过的人物。</div>
                    <div>🔗 <strong>能量连线粗细：</strong><br/>你们的连线代表互动深度，共同提及的次数越多，连线越粗、引力越强（离你越近）。</div>
                    <div>🌸 <strong>手账与奖章：</strong><br/>点击任意星子，即可查看和 ta 的<b>羁绊手账</b>。手账根据提及 ta 的全部日记判定 ta 是你的“小晴天⭐”、“友情火花🔥”还是需要温暖拥抱的“雷雨天🌧️”，并授予特制奖章（甚至臭鸡蛋🥚！）。</div>
                </div>
                
                <button onclick="document.getElementById('handbookModal').style.display='none'" style="padding:8px 24px; border-radius:10px; border:none; background:var(--accent-sunny); color:#000; cursor:pointer; font-size:0.85rem; font-weight:bold;">我知道啦</button>
            </div>
        `;
    }
    modal.style.display = 'flex';
}
