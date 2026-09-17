let draggedNode = null;
let draggedType = null; // 'card' or 'column'

function setupPersonsDragAndDrop() {
    const cards = document.querySelectorAll('.kanban-card');
    const columns = document.querySelectorAll('.kanban-column');
    const containers = document.querySelectorAll('.kanban-cards-container');

    cards.forEach(card => {
        card.addEventListener('dragstart', (e) => {
            draggedNode = card;
            draggedType = 'card';
            card.classList.add('dragging');
            e.dataTransfer.setData('text/plain', card.getAttribute('data-uuid'));
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            draggedNode = null;
            draggedType = null;
        });
    });

    columns.forEach((col, index) => {
        col.addEventListener('dragstart', (e) => {
            if (draggedType === 'card') return;
            draggedNode = col;
            draggedType = 'column';
            e.dataTransfer.setData('column-index', index);
        });

        col.addEventListener('dragend', () => {
            draggedNode = null;
            draggedType = null;
        });

        col.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (draggedType === 'column' && draggedNode !== col) {
                col.classList.add('dragover');
            }
        });

        col.addEventListener('dragleave', () => {
            col.classList.remove('dragover');
        });

        col.addEventListener('drop', async (e) => {
            col.classList.remove('dragover');
            if (draggedType === 'column') {
                const fromUuid = draggedNode.getAttribute('data-uuid');
                const targetUuid = col.getAttribute('data-uuid');
                const fromIndex = globalCategories.findIndex(c => c.uuid === fromUuid);
                const toIndex = globalCategories.findIndex(c => c.uuid === targetUuid);
                if (fromIndex !== toIndex && fromIndex >= 0 && toIndex >= 0) {
                    const [moved] = globalCategories.splice(fromIndex, 1);
                    globalCategories.splice(toIndex, 0, moved);
                    
                    const activeCategories = globalCategories.filter(c => !c.is_deleted);
                    activeCategories.forEach((c, idx) => {
                        c.sort_order = idx;
                    });

                    await syncCategoriesOrder();
                }
            }
        });
    });

    containers.forEach(container => {
        container.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (draggedType === 'card') {
                container.closest('.kanban-column').classList.add('dragover');
                const afterElement = getDragAfterElement(container, e.clientY);
                if (afterElement == null) {
                    container.appendChild(draggedNode);
                } else {
                    container.insertBefore(draggedNode, afterElement);
                }
            }
        });

        container.addEventListener('dragleave', () => {
            const col = container.closest('.kanban-column');
            if (col) col.classList.remove('dragover');
        });

        container.addEventListener('drop', async (e) => {
            const col = container.closest('.kanban-column');
            if (col) col.classList.remove('dragover');
            if (draggedType === 'card') {
                const personUuid = e.dataTransfer.getData('text/plain');
                const targetColUuid = container.getAttribute('data-uuid');
                
                const personObj = globalPersons.find(p => p.uuid === personUuid);
                if (!personObj) return;

                personObj.category_uuid = targetColUuid;

                const cardElements = [...container.querySelectorAll('.person-card')];
                const syncList = [];

                cardElements.forEach((el, index) => {
                    const uuid = el.getAttribute('data-uuid');
                    const p = globalPersons.find(item => item.uuid === uuid);
                    if (p) {
                        p.sort_order = index;
                        syncList.push(p);
                    }
                });

                if (!syncList.find(p => p.uuid === personObj.uuid)) {
                    syncList.push(personObj);
                }

                await syncPersonsBatch(syncList);
            }
        });
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.person-card:not(.dragging)')];
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}
