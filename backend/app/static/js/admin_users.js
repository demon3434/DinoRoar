// 1. Fetch & Render users
async function fetchUsers() {
    try {
        const res = await fetch('/api/admin/users', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (res.ok) {
            const users = await res.json();
            renderUsers(users);
        }
    } catch(e) {
        console.error("Failed to load users", e);
    }
}

function renderUsers(users) {
    const tableBody = document.getElementById('userTableBody');
    tableBody.innerHTML = '';
    
    const children = users.filter(u => !u.is_admin);
    
    if (children.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">暂无孩子账号，请点击右上角新增</td></tr>`;
        return;
    }

    children.forEach(user => {
        const pendingBadge = user.lock_reset_flag === 'default_requested' 
            ? ` <span class="pill pill-warn" style="font-size:0.7rem; padding: 2px 6px; margin-left: 5px; cursor: help;" title="待手机端下次网络请求时重置解锁序列">⚠️ 待重置</span>`
            : '';

        // User status badge
        const statusBadge = user.is_active === false
            ? ` <span style="background: rgba(239, 68, 68, 0.12); color: #fca5a5; font-size: 0.72rem; padding: 2px 6px; border-radius: 6px; margin-left: 5px; font-weight: 700; border: 1px solid rgba(239, 68, 68, 0.2);">已停用</span>`
            : '';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-size: 0.88rem; font-weight: 700; color: var(--text-muted);">${user.id}</td>
            <td style="font-weight:600;">${user.username}${pendingBadge}${statusBadge}</td>
            <td>${user.nickname || '<span style="color:var(--text-muted);">未设置</span>'}</td>
            <td><button class="btn-sm btn-sm-primary" onclick="viewUserLockSequence(${user.id}, '${user.username}', '${user.lock_pattern}')" title="查看解锁码序列">👁️ 查看</button></td>
            <td>
                <div class="action-links">
                    <button class="btn-sm btn-sm-primary" onclick="openEditUserModal(${user.id}, '${user.username}', '${user.nickname || ''}')" title="修改账户用户名与昵称">✏️</button>
                    <button class="btn-sm btn-sm-primary" onclick="openResetPasswordModal(${user.id}, '${user.username}')" title="重置安全密码">🔑</button>
                    <button class="btn-sm btn-sm-warning" onclick="openResetLockModal(${user.id}, '${user.username}')" title="重置解锁序列">🦕</button>
                    ${user.is_active !== false 
                        ? `<button class="btn-sm btn-sm-danger" onclick="deactivateUser(${user.id}, '${user.username}')" title="停用该账户 (保留数据)">停用</button>`
                        : `<button class="btn-sm" style="background: rgba(34, 197, 94, 0.15) !important; color: #4ade80 !important; border: 1px solid rgba(34, 197, 94, 0.25) !important;" onclick="activateUser(${user.id}, '${user.username}')" title="重新启用该账户">启用</button>`
                    }
                </div>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

// 2. User modals & Actions
function openAddUserModal() {
    document.getElementById('addUserModal').style.display = 'flex';
}
function closeAddUserModal() {
    document.getElementById('addUserModal').style.display = 'none';
    document.getElementById('newUsername').value = '';
    document.getElementById('newNickname').value = '';
    document.getElementById('newPassword').value = '';
}

async function handleAddUser() {
    const username = document.getElementById('newUsername').value.trim();
    const nickname = document.getElementById('newNickname').value.trim();
    const password = document.getElementById('newPassword').value;

    if (!username) {
        showToast("请填写用户名", "error");
        return;
    }

    try {
        const res = await fetch('/api/admin/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ 
                username, 
                nickname: nickname || null,
                password: password || null 
            })
        });

        if (res.ok) {
            closeAddUserModal();
            fetchUsers();
            showToast("新增孩子账户成功！", "success");
        } else {
            const err = await res.json();
            showToast("创建失败: " + err.detail, "error");
        }
    } catch(e) {
        showToast("网络链接失败，请稍后重试", "error");
    }
}

// Reset password
function openResetPasswordModal(id, name) {
    document.getElementById('resetTargetId').value = id;
    document.getElementById('resetTargetName').textContent = name;
    document.getElementById('resetPasswordModal').style.display = 'flex';
}
function closeResetPasswordModal() {
    document.getElementById('resetPasswordModal').style.display = 'none';
    document.getElementById('resetPasswordVal').value = '';
}

async function handleResetPassword() {
    const id = document.getElementById('resetTargetId').value;
    const newPassword = document.getElementById('resetPasswordVal').value;

    if (!newPassword) {
        showToast("请输入新密码", "error");
        return;
    }

    try {
        const res = await fetch(`/api/admin/users/${id}/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ new_password: newPassword })
        });

        if (res.ok) {
            showToast("密码重置成功！", "success");
            closeResetPasswordModal();
        } else {
            const err = await res.json();
            showToast("重置失败: " + err.detail, "error");
        }
    } catch(e) {
        showToast("网络链接错误", "error");
    }
}

// Lock pattern reset graphical logic
let currentSelectedDinos = [];
const dinoNameMap = {
    1: { name: '霸王龙', img: '/static/images/dinosaurs/t_rex.webp' },
    2: { name: '三角龙', img: '/static/images/dinosaurs/triceratops.webp' },
    3: { name: '剑龙', img: '/static/images/dinosaurs/stegosaurus.webp' },
    4: { name: '翼手龙', img: '/static/images/dinosaurs/pterodactyl.webp' },
    5: { name: '腕龙', img: '/static/images/dinosaurs/brachiosaurus.webp' }
};

function openResetLockModal(id, username) {
    document.getElementById('resetLockTargetId').value = id;
    document.getElementById('resetLockTargetName').innerText = username;
    clearDinoSequence();
    document.getElementById('resetLockModal').style.display = 'flex';
}

function closeResetLockModal() {
    document.getElementById('resetLockModal').style.display = 'none';
    clearDinoSequence();
}

function viewUserLockSequence(id, username, lockPattern) {
    document.getElementById('viewLockSeqTargetName').innerText = username;
    
    const parts = lockPattern.split(',');
    for (let i = 0; i < 3; i++) {
        const slot = document.getElementById(`viewDinoSlot${i}`);
        if (i < parts.length) {
            const dinoId = parseInt(parts[i]);
            if (dinoNameMap[dinoId]) {
                slot.innerHTML = `<img src="${dinoNameMap[dinoId].img}" alt="${dinoNameMap[dinoId].name}" title="${dinoNameMap[dinoId].name}" style="width:100%; height:100%; object-fit:cover; border-radius:8px;">`;
                slot.classList.add('filled');
            } else {
                slot.innerHTML = '<span style="font-size:0.75rem;color:var(--text-muted);">未知</span>';
                slot.classList.remove('filled');
            }
        } else {
            slot.innerHTML = '';
            slot.classList.remove('filled');
        }
    }

    const nameParts = parts.map(p => {
        const dinoId = parseInt(p);
        return dinoNameMap[dinoId] ? dinoNameMap[dinoId].name : '未知';
    });
    document.getElementById('viewDinoText').innerText = nameParts.join(' -> ');
    document.getElementById('viewLockSeqModal').style.display = 'flex';
}

function closeViewLockSeqModal() {
    document.getElementById('viewLockSeqModal').style.display = 'none';
}

function addDinoToSequence(dinoId) {
    if (currentSelectedDinos.length >= 3) {
        return;
    }
    currentSelectedDinos.push(dinoId);
    updateDinoSequenceUI();
}

function clearDinoSequence() {
    currentSelectedDinos = [];
    updateDinoSequenceUI();
}

function updateDinoSequenceUI() {
    for (let i = 0; i < 3; i++) {
        const slot = document.getElementById(`dinoSeqSlot${i}`);
        if (i < currentSelectedDinos.length) {
            const dinoId = currentSelectedDinos[i];
            slot.innerHTML = `<img src="${dinoNameMap[dinoId].img}" alt="${dinoNameMap[dinoId].name}" title="${dinoNameMap[dinoId].name}" style="width:100%; height:100%; object-fit:cover; border-radius:8px;">`;
            slot.classList.add('filled');
        } else {
            slot.innerHTML = '';
            slot.classList.remove('filled');
        }
    }

    const seqText = currentSelectedDinos.join(', ');
    document.getElementById('dinoSeqText').innerText = seqText || '-';

    const submitBtn = document.getElementById('btnSubmitLockReset');
    if (currentSelectedDinos.length === 3) {
        submitBtn.removeAttribute('disabled');
    } else {
        submitBtn.setAttribute('disabled', 'true');
    }
}

async function handleResetLock() {
    if (currentSelectedDinos.length !== 3) {
        showToast("请先选择3个恐龙", "error");
        return;
    }

    const id = document.getElementById('resetLockTargetId').value;
    const pattern = currentSelectedDinos.join(',');

    try {
        const res = await fetch(`/api/admin/users/${id}/reset-lock`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token 
            },
            body: JSON.stringify({ lock_pattern: pattern })
        });
        if (res.ok) {
            showToast("解锁码重置指令挂载成功！手机端下一次同步时生效", "success");
            closeResetLockModal();
            fetchUsers();
        } else {
            const err = await res.json();
            showToast("重置失败: " + (err.detail || "未知错误"), "error");
        }
    } catch(e) {
        showToast("网络请求失败", "error");
    }
}

// Show custom confirm modal (returns Promise)
function showCustomConfirm(message, okLabel) {
    return new Promise((resolve) => {
        const modal = document.getElementById('customConfirmModal');
        const msgEl = document.getElementById('customConfirmMessage');
        const okBtn = document.getElementById('customConfirmOkBtn');
        const cancelBtn = document.getElementById('customConfirmCancelBtn');

        msgEl.innerHTML = message;
        okBtn.textContent = okLabel || '确定停用';
        modal.style.display = 'flex';

        function handleOk() {
            cleanup();
            resolve(true);
        }

        function handleCancel() {
            cleanup();
            resolve(false);
        }

        function cleanup() {
            modal.style.display = 'none';
            okBtn.removeEventListener('click', handleOk);
            cancelBtn.removeEventListener('click', handleCancel);
        }

        okBtn.addEventListener('click', handleOk);
        cancelBtn.addEventListener('click', handleCancel);
    });
}

// Deactivate a user with soft lock
async function deactivateUser(id, name) {
    const confirm = await showCustomConfirm(
        `⚠️ <strong>停用警告</strong>：您确定要停用孩子账户 "<strong>${name}</strong>" 吗？<br><br>停用后该账户将<strong>无法登录使用</strong>，但其全部日记及录音文件均将<strong>完好保留在服务器</strong>，您可随时在后台一键重新启用。`,
        '确定停用'
    );
    if (!confirm) return;
    try {
        const res = await fetch(`/api/admin/users/${id}/deactivate`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (res.ok) {
            showToast("账户停用成功！", "success");
            fetchUsers();
        } else {
            const err = await res.json();
            showToast("停用失败: " + (err.detail || "未知错误"), "error");
        }
    } catch(e) {
        showToast("网络请求异常", "error");
    }
}

// Activate a deactivated user
async function activateUser(id, name) {
    try {
        const res = await fetch(`/api/admin/users/${id}/activate`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (res.ok) {
            showToast("账户已重新启用！", "success");
            fetchUsers();
        } else {
            const err = await res.json();
            showToast("启用失败: " + (err.detail || "未知错误"), "error");
        }
    } catch(e) {
        showToast("网络请求异常", "error");
    }
}

// Edit User Modal handlers
function openEditUserModal(id, username, nickname) {
    document.getElementById('editUserId').value = id;
    document.getElementById('editUsername').value = username;
    document.getElementById('editNickname').value = nickname;
    document.getElementById('editUserModal').style.display = 'flex';
}

// Close Edit User Modal
function closeEditUserModal() {
    document.getElementById('editUserModal').style.display = 'none';
    document.getElementById('editUserId').value = '';
    document.getElementById('editUsername').value = '';
    document.getElementById('editNickname').value = '';
}

async function handleEditUser() {
    const id = document.getElementById('editUserId').value;
    const username = document.getElementById('editUsername').value.trim();
    const nickname = document.getElementById('editNickname').value.trim();

    if (!username) {
        showToast("用户名不能为空", "error");
        return;
    }

    try {
        const res = await fetch(`/api/admin/users/${id}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ username, nickname })
        });

        if (res.ok) {
            showToast("账户信息修改成功", "success");
            closeEditUserModal();
            fetchUsers();
        } else {
            const err = await res.json();
            showToast("修改失败: " + (err.detail || "未知错误"), "error");
        }
    } catch(e) {
        showToast("网络连接异常，请稍后重试", "error");
    }
}

// Click outside to close modals
window.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        const modalId = e.target.id;
        if (modalId === 'addUserModal') closeAddUserModal();
        else if (modalId === 'resetPasswordModal') closeResetPasswordModal();
        else if (modalId === 'resetLockModal') closeResetLockModal();
        else if (modalId === 'viewLockSeqModal') closeViewLockSeqModal();
        else if (modalId === 'editUserModal') closeEditUserModal();
        else if (modalId === 'customConfirmModal') {
            const cancelBtn = document.getElementById('customConfirmCancelBtn');
            if (cancelBtn) cancelBtn.click();
        }
    }
});

// Start rendering on window load
document.addEventListener("DOMContentLoaded", () => {
    fetchUsers();
});
