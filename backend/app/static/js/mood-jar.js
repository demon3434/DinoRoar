function renderMoodJar(jarSvg, stats) {
    if (!jarSvg) return;
    jarSvg.innerHTML = '';
    const jarWidth = 500;
    const jarHeight = 180;
    const ns = 'http://www.w3.org/2000/svg';

    // Draw Soft Cork
    const cork = document.createElementNS(ns, 'rect');
    cork.setAttribute('x', jarWidth / 2 - 20);
    cork.setAttribute('y', 9);
    cork.setAttribute('width', '40');
    cork.setAttribute('height', '12');
    cork.setAttribute('rx', '3');
    cork.setAttribute('fill', '#c68e65');
    cork.setAttribute('stroke', '#8a5229');
    cork.setAttribute('stroke-width', '1.2');
    cork.style.opacity = '0.9';
    jarSvg.appendChild(cork);

    // Draw Jar Neck
    const neck = document.createElementNS(ns, 'rect');
    neck.setAttribute('x', jarWidth / 2 - 28);
    neck.setAttribute('y', 20);
    neck.setAttribute('width', '56');
    neck.setAttribute('height', '8');
    neck.setAttribute('rx', '1.5');
    neck.setAttribute('fill', 'rgba(255, 255, 255, 0.08)');
    neck.setAttribute('stroke', 'rgba(255, 255, 255, 0.22)');
    neck.setAttribute('stroke-width', '1.2');
    jarSvg.appendChild(neck);

    // Draw Jar Body
    const body = document.createElementNS(ns, 'rect');
    body.setAttribute('x', '20');
    body.setAttribute('y', '27');
    body.setAttribute('width', jarWidth - 40);
    body.setAttribute('height', '138');
    body.setAttribute('rx', '24');
    body.setAttribute('ry', '24');
    body.setAttribute('fill', 'rgba(255, 255, 255, 0.015)');
    body.setAttribute('stroke', 'rgba(255, 255, 255, 0.2)');
    body.setAttribute('stroke-width', '1.8');
    jarSvg.appendChild(body);

    // Draw Jar Highlight
    const hl = document.createElementNS(ns, 'path');
    hl.setAttribute('d', `M 32 50 Q 27 95, 32 138`);
    hl.setAttribute('stroke', 'rgba(255, 255, 255, 0.25)');
    hl.setAttribute('stroke-width', '2');
    hl.setAttribute('fill', 'none');
    jarSvg.appendChild(hl);

    // Draw Ribbon Bow
    const ribbonColor = '#f43f5e';
    const bowGroup = document.createElementNS(ns, 'g');
    
    const leftWing = document.createElementNS(ns, 'path');
    leftWing.setAttribute('d', 'M 250 24 C 238 12, 232 26, 250 24');
    leftWing.setAttribute('fill', ribbonColor);
    leftWing.style.opacity = '0.9';
    bowGroup.appendChild(leftWing);

    const rightWing = document.createElementNS(ns, 'path');
    rightWing.setAttribute('d', 'M 250 24 C 262 12, 268 26, 250 24');
    rightWing.setAttribute('fill', ribbonColor);
    rightWing.style.opacity = '0.9';
    bowGroup.appendChild(rightWing);

    const centerKnot = document.createElementNS(ns, 'circle');
    centerKnot.setAttribute('cx', '250');
    centerKnot.setAttribute('cy', '24');
    centerKnot.setAttribute('r', '2.5');
    centerKnot.setAttribute('fill', '#ffe4e6');
    centerKnot.setAttribute('stroke', ribbonColor);
    centerKnot.setAttribute('stroke-width', '1');
    bowGroup.appendChild(centerKnot);

    const leftTail = document.createElementNS(ns, 'path');
    leftTail.setAttribute('d', 'M 250 24 L 244 33');
    leftTail.setAttribute('stroke', ribbonColor);
    leftTail.setAttribute('stroke-width', '1.2');
    bowGroup.appendChild(leftTail);

    const rightTail = document.createElementNS(ns, 'path');
    rightTail.setAttribute('d', 'M 250 24 L 256 33');
    rightTail.setAttribute('stroke', ribbonColor);
    rightTail.setAttribute('stroke-width', '1.2');
    bowGroup.appendChild(rightTail);

    jarSvg.appendChild(bowGroup);

    // Draw sky elements
    for (let c = 0; c < 3; c++) {
        const cloud = document.createElementNS(ns, 'text');
        cloud.setAttribute('x', 40 + c * ((jarWidth - 80) / 3) + Math.random() * 15);
        cloud.setAttribute('y', 55 + Math.random() * 15);
        cloud.setAttribute('font-size', '16');
        cloud.setAttribute('fill', 'var(--text-muted)');
        cloud.style.opacity = '0.08';
        cloud.style.animation = 'float 6s ease-in-out infinite';
        cloud.style.animationDelay = `${c * 1.5}s`;
        cloud.textContent = '☁️';
        jarSvg.appendChild(cloud);
    }

    const moodMetaMap = {
        1: { emoji: '😊', color: '#22c55e', name: '快乐' },
        2: { emoji: '🤩', color: '#22c55e', name: '兴奋' },
        3: { emoji: '😎', color: '#22c55e', name: '得意' },
        4: { emoji: '🌟', color: '#22c55e', name: '期待' },
        5: { emoji: '😮', color: '#f59e0b', name: '惊讶' },
        6: { emoji: '😐', color: '#f59e0b', name: '一般' },
        7: { emoji: '😰', color: '#3b82f6', name: '紧张' },
        8: { emoji: '🍃', color: '#3b82f6', name: '遗憾' },
        9: { emoji: '😣', color: '#3b82f6', name: '后悔' },
        10: { emoji: '😭', color: '#ef4444', name: '伤心' },
        11: { emoji: '😡', color: '#ef4444', name: '愤怒' },
        
        Triceratops: { emoji: '😊', color: '#22c55e', name: '快乐' },
        Pterodactyl_happy: { emoji: '🤩', color: '#22c55e', name: '兴奋' },
        Pterodactyl: { emoji: '🤩', color: '#22c55e', name: '兴奋' },
        'T-Rex_proud': { emoji: '😎', color: '#22c55e', name: '得意' },
        Brachiosaurus: { emoji: '🌟', color: '#22c55e', name: '期待' },
        Stegosaurus: { emoji: '😮', color: '#f59e0b', name: '惊讶' },
        Ankylosaurus: { emoji: '😐', color: '#f59e0b', name: '一般' },
        Ankylosaurus_scared: { emoji: '😰', color: '#3b82f6', name: '紧张' },
        'Ankylosaurus_Shell': { emoji: '😰', color: '#3b82f6', name: '紧张' },
        Pterodactyl_Sigh: { emoji: '🍃', color: '#3b82f6', name: '遗憾' },
        Parasaurolophus_regret: { emoji: '😣', color: '#3b82f6', name: '后悔' },
        'Parasaurolophus_Regret': { emoji: '😣', color: '#3b82f6', name: '后悔' },
        Parasaurolophus: { emoji: '😭', color: '#ef4444', name: '伤心' },
        'T-Rex': { emoji: '😡', color: '#ef4444', name: '愤怒' },
        'T-Rex_Angry': { emoji: '😡', color: '#ef4444', name: '愤怒' }
    };

    const rawHeatmap = stats.mood_heatmap || [];

    const textLeft = document.createElementNS(ns, 'text');
    textLeft.setAttribute('x', 20);
    textLeft.setAttribute('y', jarHeight - 12);
    textLeft.setAttribute('font-size', '9px');
    textLeft.setAttribute('fill', 'var(--text-muted)');
    textLeft.style.opacity = '0.5';
    textLeft.textContent = '← 30天前';
    jarSvg.appendChild(textLeft);

    const textRight = document.createElementNS(ns, 'text');
    textRight.setAttribute('x', jarWidth - 65);
    textRight.setAttribute('y', jarHeight - 12);
    textRight.setAttribute('font-size', '9px');
    textRight.setAttribute('fill', 'var(--text-muted)');
    textRight.style.opacity = '0.5';
    textRight.textContent = '今日心情 →';
    jarSvg.appendChild(textRight);

    const textTitle = document.createElementNS(ns, 'text');
    textTitle.setAttribute('x', 20);
    textTitle.setAttribute('y', 22);
    textTitle.setAttribute('font-size', '10px');
    textTitle.setAttribute('font-weight', 'bold');
    textTitle.setAttribute('fill', 'var(--text-muted)');
    textTitle.style.opacity = '0.6';
    textTitle.textContent = `最近30天，你共收获了 ${rawHeatmap.length} 个心情气球 🎈`;
    jarSvg.appendChild(textTitle);

    if (rawHeatmap.length === 0) {
        const emptyMoods = [
            { emoji: '🦖', color: '#10b981', x: jarWidth * 0.3, delay: 0 },
            { emoji: '🦕', color: '#3b82f6', x: jarWidth * 0.5, delay: 1.2 },
            { emoji: '🌴', color: '#f59e0b', x: jarWidth * 0.7, delay: 0.6 }
        ];
        emptyMoods.forEach(item => {
            drawBalloon(jarSvg, item.x, 90, item.color, item.emoji, '没有日记的时光...', item.delay, '');
        });
    } else {
        rawHeatmap.forEach((item, index) => {
            const meta = moodMetaMap[item.mood] || { emoji: '😐', color: 'rgba(120, 120, 120, 0.4)', name: '记录' };
            let x = 40;
            if (rawHeatmap.length > 1) {
                x = 40 + (index * (jarWidth - 80)) / (rawHeatmap.length - 1);
            } else {
                x = jarWidth / 2;
            }
            const y = 78 + (index % 3) * 12;
            const delay = (index * 0.3) % 4;
            const dateTag = item.date.substring(5);
            drawBalloon(jarSvg, x, y, meta.color, meta.emoji, `${item.date}: 心情【${meta.name}】`, delay, dateTag);
        });
    }
}

function drawBalloon(svgEl, x, y, color, emoji, titleText, delay, dateStr) {
    const ns = 'http://www.w3.org/2000/svg';
    const group = document.createElementNS(ns, 'g');
    group.style.cursor = 'pointer';
    group.style.animation = `float 5s ease-in-out infinite`;
    group.style.animationDelay = `${delay}s`;
    group.style.transformOrigin = `${x}px ${y}px`;
    
    // Add title tooltip
    const titleEl = document.createElementNS(ns, 'title');
    titleEl.textContent = titleText;
    group.appendChild(titleEl);

    // 1. Balloon Line
    const line = document.createElementNS(ns, 'path');
    line.setAttribute('d', `M ${x} ${y + 19} Q ${x + 6} ${y + 40}, ${x} ${y + 65}`);
    line.setAttribute('stroke', 'rgba(120, 120, 120, 0.3)');
    line.setAttribute('stroke-width', '1.2');
    line.setAttribute('fill', 'none');
    group.appendChild(line);

    // 2. Balloon Knot
    const knot = document.createElementNS(ns, 'polygon');
    knot.setAttribute('points', `${x - 4},${y + 22} ${x + 4},${y + 22} ${x},${y + 18}`);
    knot.setAttribute('fill', color);
    group.appendChild(knot);

    // 3. Balloon Body
    const ellipse = document.createElementNS(ns, 'ellipse');
    ellipse.setAttribute('cx', x);
    ellipse.setAttribute('cy', y);
    ellipse.setAttribute('rx', '18');
    ellipse.setAttribute('ry', '21');
    ellipse.setAttribute('fill', color);
    ellipse.setAttribute('stroke', 'rgba(255, 255, 255, 0.15)');
    ellipse.setAttribute('stroke-width', '1');
    ellipse.style.transition = 'transform 0.2s';
    
    // Hover animation
    ellipse.onmouseover = function() {
        this.setAttribute('rx', '22');
        this.setAttribute('ry', '25');
    };
    ellipse.onmouseout = function() {
        this.setAttribute('rx', '18');
        this.setAttribute('ry', '21');
    };
    group.appendChild(ellipse);

    // 4. Emoji Text
    const txt = document.createElementNS(ns, 'text');
    txt.setAttribute('x', x);
    txt.setAttribute('y', y);
    txt.setAttribute('font-size', '17');
    txt.setAttribute('text-anchor', 'middle');
    txt.setAttribute('dominant-baseline', 'central');
    txt.setAttribute('fill', '#fff');
    txt.style.pointerEvents = 'none';
    txt.textContent = emoji;
    group.appendChild(txt);

    // 5. Date Tag
    if (dateStr) {
        const tag = document.createElementNS(ns, 'text');
        tag.setAttribute('x', x);
        tag.setAttribute('y', y + 78);
        tag.setAttribute('font-size', '8px');
        tag.setAttribute('fill', 'var(--text-muted)');
        tag.setAttribute('text-anchor', 'middle');
        tag.style.opacity = '0.75';
        tag.style.pointerEvents = 'none';
        tag.textContent = dateStr;
        group.appendChild(tag);
    }

    svgEl.appendChild(group);
}
