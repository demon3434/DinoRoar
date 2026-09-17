async function changeTheme(themeName) {
    document.documentElement.className = 'theme-' + themeName;
    // 立即缓存到 localStorage，下次页面加载无需等待网络即可恢复
    localStorage.setItem('cachedTheme', themeName);
    try {
        await fetch('/api/auth/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ theme: themeName })
        });
    } catch(e) {
        console.error("Failed to save theme preference", e);
    }
}

async function handleChangePassword() {
    const currentPass = document.getElementById('currentPasswordInput').value;
    const newPass = document.getElementById('newPasswordInput').value;
    const confirmPass = document.getElementById('confirmPasswordInput').value;
    
    if (!currentPass || !newPass || !confirmPass) {
        alert("请填写完整的密码输入项！");
        return;
    }
    
    if (newPass !== confirmPass) {
        alert("两次输入的新密码不一致哦，请重新检查！");
        return;
    }
    
    try {
        const res = await fetch('/api/auth/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                current_password: currentPass,
                new_password: newPass
            })
        });
        
        if (res.ok) {
            alert("密码修改成功！");
            document.getElementById('currentPasswordInput').value = '';
            document.getElementById('newPasswordInput').value = '';
            document.getElementById('confirmPasswordInput').value = '';
        } else {
            const data = await res.json();
            alert("修改密码失败: " + (data.detail || "未知错误"));
        }
    } catch(e) {
        console.error("Change password error", e);
        alert("请求失败，请检查 network 再试！");
    }
}
