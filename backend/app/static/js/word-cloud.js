function renderAICaringTips(tipsEl, stats) {
    if (tipsEl) {
        tipsEl.textContent = stats.ai_word_cloud_tips.tips || "你最近的秘密草地一片晴朗！继续保持开心哦！";
    }
}

function renderWordCloud(wordCloud, stats) {
    if (wordCloud) {
        wordCloud.innerHTML = '';
        const words = stats.ai_word_cloud_tips.words || [];
        if (words.length === 0) {
            wordCloud.innerHTML = '<span style="font-size:0.85rem; color:var(--text-muted);">多写写悄悄话日记，这里就会飘出你最常提到的话题词云哦！🌬️</span>';
        } else {
            words.forEach(word => {
                const span = document.createElement('span');
                const randomHue = Math.floor(Math.random() * 360);
                span.style = `font-size: ${11 + word.value * 3.5}px; font-weight: bold; color: hsl(${randomHue}, 75%, 72%); text-shadow: 0 2px 5px rgba(0,0,0,0.35); cursor: pointer; transition: transform 0.2s; padding: 4px; display: inline-block;`;
                span.textContent = word.text;
                span.title = `提到过 ${word.value} 次`;
                span.onmouseover = function() {
                    this.style.transform = 'scale(1.2) rotate(3deg)';
                };
                span.onmouseout = function() {
                    this.style.transform = 'scale(1) rotate(0deg)';
                };
                span.onclick = function() {
                    window.location.href = `/diary?query=${encodeURIComponent(word.text)}`;
                };
                wordCloud.appendChild(span);
            });
        }
    }
}
