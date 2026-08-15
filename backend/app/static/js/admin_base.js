// Sidebar Toggle
let isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
if (isSidebarCollapsed) {
    const sidebar = document.getElementById('appSidebar');
    if (sidebar) sidebar.classList.add('collapsed');
    const icon = document.getElementById('collapseIcon');
    if (icon) icon.textContent = '▶';
}
function toggleSidebar() {
    const sidebar = document.getElementById('appSidebar');
    const icon = document.getElementById('collapseIcon');
    sidebar.classList.toggle('collapsed');
    const collapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', collapsed);
    icon.textContent = collapsed ? '▶' : '◀';
}

// Submenu Toggle
function toggleSubmenu(submenuId) {
    const submenu = document.getElementById(submenuId);
    if (!submenu) return;
    const parentMap = {
        'users-submenu': 'menu-users-tab',
        'system-submenu': 'menu-system-tab',
        'personal-submenu': 'menu-personal-tab',
        'stickers-submenu': 'menu-stickers-tab'
    };
    const parentMenu = document.getElementById(parentMap[submenuId]);
    const isOpen = submenu.classList.contains('open');
    if (!isOpen) {
        submenu.classList.add('open');
        submenu.style.maxHeight = '200px';
        submenu.style.opacity = '1';
        if (parentMenu) parentMenu.classList.add('active');
    } else {
        submenu.classList.remove('open');
        submenu.style.maxHeight = '0px';
        submenu.style.opacity = '0';
        if (parentMenu) parentMenu.classList.remove('active');
    }
}

// Logout
function handleLogout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// Global Toast Notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toastNotification');
    if (!toast) return;
    toast.innerText = message;
    
    // Reset class
    toast.className = 'toast-notification';
    
    // Add custom type
    if (type === 'success') {
        toast.classList.add('success');
    } else if (type === 'error') {
        toast.classList.add('error');
    }
    
    // Show toast
    toast.classList.add('show');
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
