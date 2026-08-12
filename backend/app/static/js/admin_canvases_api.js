const canvasesApi = {
    async fetchConfig() {
        const token = localStorage.getItem("token");
        const res = await fetch("/api/canvases/admin/config", {
            headers: { "Authorization": "Bearer " + token }
        });
        if (!res.ok) throw new Error("加载后台配置失败");
        return await res.json();
    },

    async createSeries(name, sortOrder) {
        const token = localStorage.getItem("token");
        const res = await fetch("/api/canvases/admin/series", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({ name, sort_order: sortOrder })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "新建分类失败");
        }
        return await res.json();
    },

    async updateSeries(seriesId, name, sortOrder) {
        const token = localStorage.getItem("token");
        const res = await fetch(`/api/canvases/admin/series/${seriesId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({ name, sort_order: sortOrder })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "修改分类失败");
        }
        return await res.json();
    },

    async toggleSeriesActive(seriesId) {
        const token = localStorage.getItem("token");
        const res = await fetch(`/api/canvases/admin/series/${seriesId}/toggle-active`, {
            method: "POST",
            headers: { "Authorization": "Bearer " + token }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "切换分类状态失败");
        }
        return await res.json();
    },

    async deleteSeriesCascade(seriesId) {
        const token = localStorage.getItem("token");
        const res = await fetch(`/api/canvases/admin/series/${seriesId}/cascade`, {
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "删除分类失败");
        }
        return await res.json();
    },

    async sortSeries(seriesIds) {
        const token = localStorage.getItem("token");
        const res = await fetch("/api/canvases/admin/series/sort", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({ series_ids: seriesIds })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "分类排序保存失败！");
        }
        return await res.json();
    },

    async createSet(seriesId, name, description, exchangePrice, sortOrder) {
        const token = localStorage.getItem("token");
        const res = await fetch("/api/canvases/admin/sets", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({
                series_id: seriesId,
                name,
                description,
                exchange_price: exchangePrice,
                sort_order: sortOrder
            })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "新建商品失败");
        }
        return await res.json();
    },

    async updateSet(setId, seriesId, name, description, exchangePrice, sortOrder) {
        const token = localStorage.getItem("token");
        const res = await fetch(`/api/canvases/admin/sets/${setId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({
                series_id: seriesId,
                name,
                description,
                exchange_price: exchangePrice,
                sort_order: sortOrder
            })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "修改商品信息失败");
        }
        return await res.json();
    },

    async toggleSetActive(setId) {
        const token = localStorage.getItem("token");
        const res = await fetch(`/api/canvases/admin/sets/${setId}/toggle-active`, {
            method: "POST",
            headers: { "Authorization": "Bearer " + token }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "切换商品状态失败");
        }
        return await res.json();
    },

    async deleteSet(setId) {
        const token = localStorage.getItem("token");
        const res = await fetch(`/api/canvases/admin/sets/${setId}`, {
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "删除商品失败");
        }
        return await res.json();
    },

    async sortSets(setIds) {
        const token = localStorage.getItem("token");
        const res = await fetch("/api/canvases/admin/sets/sort", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({ set_ids: setIds })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "画布排序保存失败！");
        }
        return await res.json();
    },

    async toggleInstanceActive(instanceId) {
        const token = localStorage.getItem("token");
        const res = await fetch(`/api/canvases/admin/instances/${instanceId}/toggle-active`, {
            method: "POST",
            headers: { "Authorization": "Bearer " + token }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "切换实例状态失败");
        }
        return await res.json();
    },

    async deleteInstance(instanceId) {
        const token = localStorage.getItem("token");
        const res = await fetch(`/api/canvases/admin/instances/${instanceId}`, {
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "删除实例失败");
        }
        return await res.json();
    },

    async exportCanvases(seriesIds) {
        const token = localStorage.getItem("token");
        const idsParam = seriesIds.join(",");
        const res = await fetch(`/api/canvases/admin/export?series_ids=${idsParam}`, {
            headers: { "Authorization": "Bearer " + token }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "导出失败");
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "dinoroar_canvases_export.zip";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    async importPreview(file) {
        const token = localStorage.getItem("token");
        const fd = new FormData();
        fd.append("file", file);
        const res = await fetch("/api/canvases/admin/import/preview", {
            method: "POST",
            headers: { "Authorization": "Bearer " + token },
            body: fd
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "上传预览失败");
        }
        return await res.json();
    },

    async importConfirm(tempToken, selectedSeriesNames, conflictResolution) {
        const token = localStorage.getItem("token");
        const res = await fetch("/api/canvases/admin/import/confirm", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({
                temp_token: tempToken,
                selected_series_names: selectedSeriesNames,
                conflict_resolution: conflictResolution
            })
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "确认导入失败");
        }
        return await res.json();
    }
};
