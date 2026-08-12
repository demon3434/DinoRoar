const stickersApi = {
    async fetchConfig() {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/stickers/config', { headers: { 'Authorization': 'Bearer ' + token } });
        if (!res.ok) throw new Error("拉取配置数据失败");
        return await res.json();
    },

    async createSeries(name, sortOrder) {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/stickers/admin/series', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ name, sort_order: sortOrder })
        });
        if (!res.ok) throw new Error("创建分类失败");
        return await res.json();
    },

    async updateSeries(seriesId, name) {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/stickers/admin/series/${seriesId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ name })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "重命名失败");
        }
        return await res.json();
    },

    async toggleSeriesActive(seriesId, is_active) {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/stickers/admin/series/${seriesId}/toggle-active`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ is_active })
        });
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "切换失败");
        }
        return await res.json();
    },

    async deleteSeriesCascade(seriesId) {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/stickers/admin/series/${seriesId}/cascade`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "删除失败");
        }
        return await res.json();
    },

    async deleteSeries(seriesId) {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/stickers/admin/series/${seriesId}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "删除失败");
        }
        return await res.json();
    },

    async sortSeries(seriesIds) {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/stickers/admin/series/sort', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ series_ids: seriesIds })
        });
        if (!res.ok) throw new Error("保存顺序失败");
        return await res.json();
    },

    async sortStickers(stickerIds) {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/stickers/admin/sort', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ sticker_ids: stickerIds })
        });
        if (!res.ok) throw new Error("保存顺序失败");
        return await res.json();
    },

    async deleteSticker(stickerId) {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/stickers/admin/${stickerId}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!res.ok) throw new Error("删除贴纸失败");
        return await res.json();
    },

    async batchDeleteStickers(stickerIds) {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/stickers/admin/batch-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ sticker_ids: stickerIds })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "批量删除失败");
        }
        return await res.json();
    },

    async uploadSticker(formData) {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/stickers/admin/upload', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: formData
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "上传失败");
        }
        return await res.json();
    },

    async updateSticker(id, formData) {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/stickers/admin/${id}`, {
            method: 'PUT',
            headers: { 'Authorization': 'Bearer ' + token },
            body: formData
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "修改失败");
        }
        return await res.json();
    },

    async exportStickers(seriesIds) {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/stickers/export?series_ids=${seriesIds}`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "导出打包失败");
        }
        return res;
    },

    async importPreview(formData) {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/stickers/import/preview', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: formData
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "贴纸包预检解析失败");
        }
        return await res.json();
    },

    async importConfirm(tempToken, selectedSeriesNames, conflictResolution) {
        const token = localStorage.getItem('token');
        const res = await fetch('/api/stickers/import/confirm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({
                temp_token: tempToken,
                selected_series_names: selectedSeriesNames,
                conflict_resolution: conflictResolution
            })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "贴纸落库失败");
        }
        return await res.json();
    }
};
