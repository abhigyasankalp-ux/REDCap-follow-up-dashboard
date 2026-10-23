// REDCap Newborn Follow-up Dashboard - JavaScript Core

// Global State
let dbData = null;
let activeMonths = ['ALL'];
let activeBlock = 'ALL';
let activeDelivCoord = 'ALL';
let activeFollowupCoord = 'ALL';

// Active Tab
let activeTab = 'overview';
let activeDiscrepancyFilterNotifReg = 'ALL';
let activeDiscrepancyFilterDay29 = 'ALL';
let activeDeathBaby = 'ALL';
let activeStillbirthBaby = 'ALL';
let activePendingType = 'ALL';

let activeDeathPlace = 'ALL';
let activeDeathDelivPlace = 'ALL';
let activeStillbirthLoc = 'ALL';
let activeStillbirthPlace = 'ALL';
let activeDelivLocFilter = 'ALL';

let activeSncuMatchStatus = 'ALL';
let activeSncuDelivPlace = 'ALL';
let activeKhandwaMatchStatus = 'ALL';
let activeKhandwaDelivPlace = 'ALL';
let activeHomeMatchStatus = 'ALL';
let activeOutMatchStatus = 'ALL';

// Search Queries
let searchOverall = '';
let searchPending = '';
let searchDeaths = '';
let searchStillbirths = '';
let searchOutRangeDeaths = '';
let searchHomeDeliveries = '';
let searchOutDistrictDeliveries = '';
let searchSncuQuery = '';
let searchKhandwaSncuQuery = '';
let searchLostFollowup = '';
let activeLostCategory = 'ALL';

// Pagination Offsets
let visibleOverall = 20;
let visiblePending = 20;
let visibleDeaths = 20;
let visibleStillbirths = 20;
let visibleOutRangeDeaths = 20;
let visibleHomeDeliveries = 20;
let visibleOutDistrictDeliveries = 20;
let visibleSncu = 20;
let visibleKhandwaSncu = 50;
let visibleLostFollowup = 20;

// Sorting States
let sortFieldOverall = 'id', sortOrderOverall = 'asc';
let sortFieldPending = 'id', sortOrderPending = 'asc';
let sortFieldDeaths = 'id', sortOrderDeaths = 'asc';
let sortFieldStillbirths = 'id', sortOrderStillbirths = 'asc';
let sortFieldOutRangeDeaths = 'id', sortOrderOutRangeDeaths = 'asc';
let sortFieldHomeDeliveries = 'delivery_date', sortOrderHomeDeliveries = 'desc';
let sortFieldOutDistrictDeliveries = 'delivery_date', sortOrderOutDistrictDeliveries = 'desc';
let sortFieldLostFollowup = 'id', sortOrderLostFollowup = 'asc';
let sortFieldSncu = 'adm_id', sortOrderSncu = 'asc';
let sortFieldKhandwaSncu = 'adm_id', sortOrderKhandwaSncu = 'asc';

// Chart references
let trendChart = null;
let blockChart = null;
let mortalityChart = null;
let placeOfDeliveryChart = null;

// DOM Elements
const selectBlock = document.getElementById('filter-block');
const selectDelivCoord = document.getElementById('filter-deliv-coord');
const selectFollowupCoord = document.getElementById('filter-followup-coord');

const btnReset = document.getElementById('reset-filters');
const selectDiscrepancyNotifReg = document.getElementById('filter-discrepancy-notif-reg');
const selectDiscrepancyDay29 = document.getElementById('filter-discrepancy-day29');
const selectDeathBaby = document.getElementById('filter-death-baby-num');
const selectDeathPlace = document.getElementById('filter-death-place');
const selectStillbirthLoc = document.getElementById('filter-stillbirth-loc');
const selectStillbirthBaby = document.getElementById('filter-stillbirth-baby-num');
const selectPendingType = document.getElementById('filter-pending-type');
const selectStillbirthPlace = document.getElementById('filter-stillbirth-place');
const selectDeathDelivPlace = document.getElementById('filter-death-deliv-place');

// Initialize
function initApp() {
    loadData();
    setupTabSwitching();
    setupFilterListeners();
    setupSearchListeners();
}

if (document.readyState === 'complete' || document.readyState === 'interactive') {
    initApp();
} else {
    document.addEventListener('DOMContentLoaded', initApp);
}

// Load Inline or External Data
async function loadData() {
    // 1. Direct window.dbData from lightweight dashboard_data.js script
    if (typeof window.dbData !== 'undefined' && window.dbData) {
        console.log("Loaded dashboard data from dashboard_data.js (window.dbData)");
        dbData = window.dbData;
        initializeDashboard();
        return;
    }

    const dataEl = document.getElementById('dashboard-data-json');
    if (dataEl && dataEl.textContent) {
        console.log("Parsing fast-path inline JSON data...");
        try {
            dbData = JSON.parse(dataEl.textContent);
            console.log("Fast-path JSON parsed successfully! Total overall records:", dbData.overall_list ? dbData.overall_list.length : 0);
            initializeDashboard();
            return;
        } catch (e) {
            console.error("Error parsing fast-path inline JSON data:", e);
        }
    }

    if (typeof INLINED_DASHBOARD_DATA !== 'undefined') {
        console.log("Using inlined JS object dashboard data...");
        dbData = INLINED_DASHBOARD_DATA;
        initializeDashboard();
        return;
    }

    console.log("Inlined data not found, fetching external JSON...");
    try {
        const response = await fetch('dashboard_data.json');
        if (!response.ok) throw new Error("HTTP error");
        dbData = await response.json();
        initializeDashboard();
    } catch (e) {
        console.error("Failed to load dashboard data:", e);
        document.querySelectorAll('.cards-list-container').forEach(el => {
            el.innerHTML = `<div class="no-records-msg" style="color: var(--color-danger); border-color: var(--color-danger);">
                <strong>Error Loading Dashboard Data:</strong> Make sure you have run the python generator script.
            </div>`;
        });
    }
}

// Initialize UI Options
function initializeDashboard() {
    initializeFilters();
    setupSortingHeaders();
    updateDashboard();
}

// Setup Filters
window.toggleMonthDropdown = function(event) {
    event.stopPropagation();
    const dropdown = document.getElementById('multiselect-options-month');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
};

window.selectMonthPreset = function(preset, event) {
    if (event) event.stopPropagation();
    if (preset === 'ALL') {
        activeMonths = ['ALL'];
    } else {
        activeMonths = [];
    }
    
    const checkboxes = document.querySelectorAll('#multiselect-checkbox-list-month input');
    checkboxes.forEach(cb => {
        cb.checked = (preset === 'ALL');
    });
    
    updateMonthMultiselectLabel();
    resetAllPagination();
    updateDashboard();
};

function updateMonthMultiselectLabel() {
    const labelSpan = document.getElementById('multiselect-label-month');
    if (!labelSpan) return;
    if (activeMonths.includes('ALL') || activeMonths.length === 0) {
        labelSpan.textContent = 'All Months';
    } else if (activeMonths.length === 1) {
        const parts = activeMonths[0].split('-');
        if (parts.length === 2) {
            const dateObj = new Date(parts[0], parts[1] - 1);
            labelSpan.textContent = dateObj.toLocaleDateString('default', { month: 'short', year: 'numeric' });
        } else {
            labelSpan.textContent = activeMonths[0];
        }
    } else {
        labelSpan.textContent = `${activeMonths.length} Months selected`;
    }
}

function populateMonthDropdown() {
    if (!dbData) return;
    const listContainer = document.getElementById('multiselect-checkbox-list-month');
    if (!listContainer) return;
    listContainer.innerHTML = '';
    
    dbData.metadata.months.forEach(m => {
        const div = document.createElement('div');
        div.style.padding = '6px 12px';
        div.style.display = 'flex';
        div.style.alignItems = 'center';
        div.style.gap = '8px';
        div.style.fontSize = '0.75rem';
        div.style.cursor = 'pointer';
        div.style.transition = 'background 0.2s';
        
        div.onmouseover = () => { div.style.background = 'var(--color-bg-sunken)'; };
        div.onmouseout = () => { div.style.background = 'transparent'; };
        
        div.onclick = (e) => {
            e.stopPropagation();
            const checkbox = div.querySelector('input');
            checkbox.checked = !checkbox.checked;
            handleMonthSelectionChange(m, checkbox.checked);
        };
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.style.cursor = 'pointer';
        checkbox.value = m;
        checkbox.checked = activeMonths.includes('ALL') || activeMonths.includes(m);
        checkbox.onclick = (e) => {
            e.stopPropagation();
            handleMonthSelectionChange(m, checkbox.checked);
        };
        
        const label = document.createElement('label');
        label.style.cursor = 'pointer';
        label.style.flex = '1';
        label.style.userSelect = 'none';
        const parts = m.split('-');
        if (parts.length === 2) {
            const dateObj = new Date(parts[0], parts[1] - 1);
            label.textContent = dateObj.toLocaleDateString('default', { month: 'short', year: 'numeric' });
        } else {
            label.textContent = m;
        }
        
        div.appendChild(checkbox);
        div.appendChild(label);
        listContainer.appendChild(div);
    });
    
    updateMonthMultiselectLabel();
}

function handleMonthSelectionChange(month, isChecked) {
    if (activeMonths.includes('ALL')) {
        activeMonths = [...dbData.metadata.months];
    }
    
    if (isChecked) {
        if (!activeMonths.includes(month)) {
            activeMonths.push(month);
        }
    } else {
        activeMonths = activeMonths.filter(m => m !== month);
    }
    
    if (activeMonths.length === dbData.metadata.months.length || activeMonths.length === 0) {
        activeMonths = ['ALL'];
    }
    
    updateMonthMultiselectLabel();
    const checkboxes = document.querySelectorAll('#multiselect-checkbox-list-month input');
    checkboxes.forEach(cb => {
        cb.checked = activeMonths.includes('ALL') || activeMonths.includes(cb.value);
    });
    
    resetAllPagination();
    updateDashboard();
}

// Add global listener to close month dropdown on outside clicks
document.addEventListener('click', (e) => {
    const container = document.getElementById('multiselect-options-month');
    const multiselectBox = document.getElementById('multiselect-month');
    if (container && multiselectBox && !multiselectBox.contains(e.target)) {
        container.style.display = 'none';
    }
});

function initializeFilters() {
    if (dbData && dbData.metadata && dbData.metadata.last_updated) {
        const updEl = document.getElementById('dashboard-last-updated');
        if (updEl) updEl.textContent = `(${dbData.metadata.last_updated})`;
    }
    let { months, blocks, deliv_coordinators, followup_coordinators } = dbData.metadata;
    months = months.filter(m => activeMonths.includes('ALL') || activeMonths.includes(m));
    
    if (selectBlock) selectBlock.innerHTML = '<option value="ALL">All Blocks</option>';
    if (selectDelivCoord) selectDelivCoord.innerHTML = '<option value="ALL">All Delivery Coords</option>';
    if (selectFollowupCoord) selectFollowupCoord.innerHTML = '<option value="ALL">All Follow-up Coords</option>';

    populateMonthDropdown();

    if (selectBlock) {
        blocks.forEach(b => {
            const option = document.createElement('option');
            option.value = b;
            option.textContent = b;
            selectBlock.appendChild(option);
        });
    }

    if (selectDelivCoord) {
        deliv_coordinators.forEach(c => {
            const option = document.createElement('option');
            option.value = c;
            option.textContent = c;
            selectDelivCoord.appendChild(option);
        });
    }

    if (selectFollowupCoord) {
        followup_coordinators.forEach(c => {
            const option = document.createElement('option');
            option.value = c;
            option.textContent = c;
            selectFollowupCoord.appendChild(option);
        });
    }

    if (selectDeathPlace && dbData.metadata.places_of_death) {
        selectDeathPlace.innerHTML = '<option value="ALL">All Places</option>';
        dbData.metadata.places_of_death.forEach(p => {
            const option = document.createElement('option');
            option.value = p;
            option.textContent = p;
            selectDeathPlace.appendChild(option);
        });
    }
    if (selectStillbirthPlace && dbData.metadata.stillbirth_places) {
        selectStillbirthPlace.innerHTML = '<option value="ALL">All Places</option>';
        dbData.metadata.stillbirth_places.forEach(p => {
            const option = document.createElement('option');
            option.value = p;
            option.textContent = p;
            selectStillbirthPlace.appendChild(option);
        });
    }

    if (selectDeathDelivPlace && (dbData.metadata.stillbirth_places || dbData.metadata.places_of_delivery)) {
        const places = dbData.metadata.stillbirth_places || dbData.metadata.places_of_delivery || [];
        selectDeathDelivPlace.innerHTML = '<option value="ALL">All Places of Delivery</option>';
        places.forEach(p => {
            const option = document.createElement('option');
            option.value = p;
            option.textContent = p;
            selectDeathDelivPlace.appendChild(option);
        });
    }

    const selectSncuDelivPlace = document.getElementById('filter-sncu-deliv-place');
    if (selectSncuDelivPlace && dbData.sncu_deaths_list) {
        const places = Array.from(new Set(dbData.sncu_deaths_list.map(d => d.deliv_place).filter(p => p && p.trim() !== ''))).sort();
        selectSncuDelivPlace.innerHTML = '<option value="ALL">All Places of Delivery</option>';
        places.forEach(p => {
            const option = document.createElement('option');
            option.value = p;
            option.textContent = p;
            selectSncuDelivPlace.appendChild(option);
        });
    }

    const selectKhandwaDelivPlace = document.getElementById('filter-khandwa-deliv-place');
    if (selectKhandwaDelivPlace && dbData.khandwa_sncu_deaths_list) {
        const places = Array.from(new Set(dbData.khandwa_sncu_deaths_list.map(d => d.deliv_place).filter(p => p && p.trim() !== ''))).sort();
        selectKhandwaDelivPlace.innerHTML = '<option value="ALL">All Places of Delivery</option>';
        places.forEach(p => {
            const option = document.createElement('option');
            option.value = p;
            option.textContent = p;
            selectKhandwaDelivPlace.appendChild(option);
        });
    }

    if (selectDeathBaby) selectDeathBaby.value = 'ALL';
    if (selectDiscrepancyNotifReg) selectDiscrepancyNotifReg.value = 'ALL';
if (selectDiscrepancyDay29) selectDiscrepancyDay29.value = 'ALL';
    if (selectStillbirthLoc) selectStillbirthLoc.value = 'ALL';
    if (selectStillbirthBaby) selectStillbirthBaby.value = 'ALL';
    if (selectPendingType) selectPendingType.value = 'ALL';
    if (selectStillbirthPlace) selectStillbirthPlace.value = 'ALL';
        if (selectDeathDelivPlace) selectDeathDelivPlace.value = 'ALL';
}

// Setup Tab switching
function setupTabSwitching() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            // Toggle buttons
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Toggle panels
            tabPanels.forEach(p => p.classList.remove('active'));
            document.getElementById(`panel-${tabName}`).classList.add('active');
            
            activeTab = tabName;
            renderActiveTabContent();
        });
    });
}

// Hook Header Clicks for Dynamic Sorting
function setupSortingHeaders() {
    const sortableHeaders = document.querySelectorAll('.dashboard-table th.sortable');
    sortableHeaders.forEach(th => {
        th.addEventListener('click', () => {
            const tableId = th.closest('table').id;
            const sortField = th.dataset.sort;
            
            let currentField, currentOrder;
            
            if (tableId === 'overall-table') {
                if (sortFieldOverall === sortField) {
                    sortOrderOverall = sortOrderOverall === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldOverall = sortField;
                    sortOrderOverall = 'asc';
                }
                currentField = sortFieldOverall;
                currentOrder = sortOrderOverall;
            } else if (tableId === 'pending-table') {
                if (sortFieldPending === sortField) {
                    sortOrderPending = sortOrderPending === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldPending = sortField;
                    sortOrderPending = 'asc';
                }
                currentField = sortFieldPending;
                currentOrder = sortOrderPending;
            } else if (tableId === 'lost-followup-table') {
                if (sortFieldLostFollowup === sortField) {
                    sortOrderLostFollowup = sortOrderLostFollowup === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldLostFollowup = sortField;
                    sortOrderLostFollowup = 'asc';
                }
                currentField = sortFieldLostFollowup;
                currentOrder = sortOrderLostFollowup;
            } else if (tableId === 'deaths-table') {
                if (sortFieldDeaths === sortField) {
                    sortOrderDeaths = sortOrderDeaths === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldDeaths = sortField;
                    sortOrderDeaths = 'asc';
                }
                currentField = sortFieldDeaths;
                currentOrder = sortOrderDeaths;
            } else if (tableId === 'stillbirths-table') {
                if (sortFieldStillbirths === sortField) {
                    sortOrderStillbirths = sortOrderStillbirths === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldStillbirths = sortField;
                    sortOrderStillbirths = 'asc';
                }
                currentField = sortFieldStillbirths;
                currentOrder = sortOrderStillbirths;
            } else if (tableId === 'out-range-deaths-table') {
                if (sortFieldOutRangeDeaths === sortField) {
                    sortOrderOutRangeDeaths = sortOrderOutRangeDeaths === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldOutRangeDeaths = sortField;
                    sortOrderOutRangeDeaths = 'asc';
                }
                currentField = sortFieldOutRangeDeaths;
                currentOrder = sortOrderOutRangeDeaths;
            } else if (tableId === 'home-deliveries-table') {
                if (sortFieldHomeDeliveries === sortField) {
                    sortOrderHomeDeliveries = sortOrderHomeDeliveries === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldHomeDeliveries = sortField;
                    sortOrderHomeDeliveries = 'asc';
                }
                currentField = sortFieldHomeDeliveries;
                currentOrder = sortOrderHomeDeliveries;
            } else if (tableId === 'out-district-deliveries-table') {
                if (sortFieldOutDistrictDeliveries === sortField) {
                    sortOrderOutDistrictDeliveries = sortOrderOutDistrictDeliveries === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldOutDistrictDeliveries = sortField;
                    sortOrderOutDistrictDeliveries = 'asc';
                }
                currentField = sortFieldOutDistrictDeliveries;
                currentOrder = sortOrderOutDistrictDeliveries;
            } else if (tableId === 'khandwa-sncu-deaths-table') {
                if (sortFieldKhandwaSncu === sortField) {
                    sortOrderKhandwaSncu = sortOrderKhandwaSncu === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldKhandwaSncu = sortField;
                    sortOrderKhandwaSncu = 'asc';
                }
                currentField = sortFieldKhandwaSncu;
                currentOrder = sortOrderKhandwaSncu;
            } else if (tableId === 'sncu-deaths-table') {
                if (sortFieldSncu === sortField) {
                    sortOrderSncu = sortOrderSncu === 'asc' ? 'desc' : 'asc';
                } else {
                    sortFieldSncu = sortField;
                    sortOrderSncu = 'asc';
                }
                currentField = sortFieldSncu;
                currentOrder = sortOrderSncu;
            }

            // Update indicators in the same table
            const tableHeaders = th.closest('table').querySelectorAll('th.sortable');
            tableHeaders.forEach(h => {
                h.classList.remove('sorted-asc', 'sorted-desc');
                const indicator = h.querySelector('.sort-indicator');
                if (indicator) indicator.textContent = '↕';
            });

            th.classList.add(currentOrder === 'asc' ? 'sorted-asc' : 'sorted-desc');
            const thIndicator = th.querySelector('.sort-indicator');
            if (thIndicator) thIndicator.textContent = currentOrder === 'asc' ? '▲' : '▼';

            // Trigger re-render
            renderActiveTabContent();
        });
    });
}

// Sorting logic with natural comparison
function sortDataList(data, sortField, sortOrder) {
    if (!sortField) return data;
    
    return data.sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];

        // Handle case where we have undefined or nulls
        if (valA === undefined || valA === null) valA = '';
        if (valB === undefined || valB === null) valB = '';

        if (typeof valA === 'boolean') valA = valA ? 1 : 0;
        if (typeof valB === 'boolean') valB = valB ? 1 : 0;

        let comparison = 0;
        if (typeof valA === 'number' && typeof valB === 'number') {
            comparison = valA - valB;
        } else {
            // Natural comparative sorting (useful for IDs like 49-2 vs 49-10)
            comparison = String(valA).localeCompare(String(valB), undefined, { numeric: true, sensitivity: 'base' });
        }

        return sortOrder === 'asc' ? comparison : -comparison;
    });
}

// Filter listeners
function setupFilterListeners() {
    const selectKhandwaDelivPlace = document.getElementById('filter-khandwa-deliv-place');
    if (selectKhandwaDelivPlace) {
        selectKhandwaDelivPlace.addEventListener('change', (e) => {
            activeKhandwaDelivPlace = e.target.value;
            visibleKhandwaSncu = 50;
            renderKhandwaSncuDeathsList();
        });
    }

    document.querySelectorAll('.khandwa-kpi-filter-card').forEach(card => {
        card.addEventListener('click', () => {
            const filterVal = card.getAttribute('data-khandwa-filter');
            activeKhandwaMatchStatus = filterVal;
            visibleKhandwaSncu = 50;
            renderKhandwaSncuDeathsList();
        });
    });




    selectBlock.addEventListener('change', (e) => {
        activeBlock = e.target.value;
        resetAllPagination();
        updateDashboard();
    });

    selectDelivCoord.addEventListener('change', (e) => {
        activeDelivCoord = e.target.value;
        resetAllPagination();
        updateDashboard();
    });

    selectFollowupCoord.addEventListener('change', (e) => {
        activeFollowupCoord = e.target.value;
        resetAllPagination();
        updateDashboard();
    });

    btnReset.addEventListener('click', () => {
        activeMonths = ['ALL'];
        activeBlock = 'ALL';
        activeDelivCoord = 'ALL';
        activeFollowupCoord = 'ALL';
        activeDiscrepancyFilterNotifReg = 'ALL';
        activeDiscrepancyFilterDay29 = 'ALL';
        activeDeathBaby = 'ALL';
        activeDeathPlace = 'ALL';

        selectMonthPreset('ALL');
        selectBlock.value = 'ALL';
        selectDelivCoord.value = 'ALL';
        selectFollowupCoord.value = 'ALL';
        if (selectDiscrepancyNotifReg) selectDiscrepancyNotifReg.value = 'ALL';
if (selectDiscrepancyDay29) selectDiscrepancyDay29.value = 'ALL';
        if (selectDeathBaby) selectDeathBaby.value = 'ALL';
        if (selectDeathPlace) selectDeathPlace.value = 'ALL';
        if (selectStillbirthLoc) selectStillbirthLoc.value = 'ALL';
    if (selectStillbirthBaby) selectStillbirthBaby.value = 'ALL';
    if (selectPendingType) selectPendingType.value = 'ALL';
        if (selectStillbirthPlace) selectStillbirthPlace.value = 'ALL';
        if (selectDeathDelivPlace) selectDeathDelivPlace.value = 'ALL';
        
        
        const selectDelivLocFilter = document.getElementById('filter-deliv-loc');
        if (selectDelivLocFilter) selectDelivLocFilter.value = 'ALL';
        activeDelivLocFilter = 'ALL';
        activeStillbirthLoc = 'ALL';
        activeStillbirthPlace = 'ALL';
        
        document.getElementById('search-overall').value = '';
        document.getElementById('search-pending').value = '';
        document.getElementById('search-deaths').value = '';
        document.getElementById('search-stillbirths').value = '';
        document.getElementById('search-out-range-deaths').value = '';
        document.getElementById('search-home-deliveries').value = '';
        document.getElementById('search-out-district-deliveries').value = '';
        
        searchOverall = '';
        searchPending = '';
        searchDeaths = '';
        searchStillbirths = '';
        searchOutRangeDeaths = '';
        searchHomeDeliveries = '';
            searchOutDistrictDeliveries = '';
    searchSncuQuery = '';
            activeKhandwaMatchStatus = 'ALL';
        activeKhandwaDelivPlace = 'ALL';
        searchKhandwaSncuQuery = '';
        if (document.getElementById('filter-khandwa-deliv-place')) document.getElementById('filter-khandwa-deliv-place').value = 'ALL';
        if (document.getElementById('search-khandwa-sncu')) document.getElementById('search-khandwa-sncu').value = '';
        activeSncuMatchStatus = 'ALL';
        activeHomeMatchStatus = 'ALL';
        activeOutMatchStatus = 'ALL';
    
    if (document.getElementById('search-sncu')) document.getElementById('search-sncu').value = '';
    

        

        resetAllPagination();
        updateDashboard();
    });

    if (selectDiscrepancyNotifReg) {
        selectDiscrepancyNotifReg.addEventListener('change', (e) => {
            activeDiscrepancyFilterNotifReg = e.target.value;
            visibleOverall = 20;
            renderOverallList();
        });
    }
    if (selectDiscrepancyDay29) {
        selectDiscrepancyDay29.addEventListener('change', (e) => {
            activeDiscrepancyFilterDay29 = e.target.value;
            visibleOverall = 20;
            renderOverallList();
        });
    }

    if (selectDeathBaby) {
        selectDeathBaby.addEventListener('change', (e) => {
            activeDeathBaby = e.target.value;
            visibleDeaths = 20;
            renderDeathsList();
        });
    }

    if (selectDeathPlace) {
        selectDeathPlace.addEventListener('change', (e) => {
            activeDeathPlace = e.target.value;
            visibleDeaths = 20;
            renderDeathsList();
        });
    }

    if (selectStillbirthLoc) {
        selectStillbirthLoc.addEventListener('change', (e) => {
            activeStillbirthLoc = e.target.value;
            visibleStillbirths = 20;
            renderStillbirthsList();
        });
    }

    if (selectStillbirthBaby) {
        selectStillbirthBaby.addEventListener('change', (e) => {
            activeStillbirthBaby = e.target.value;
            visibleStillbirths = 20;
            renderStillbirthsList();
        });
    }

    if (selectPendingType) {
        selectPendingType.addEventListener('change', (e) => {
            activePendingType = e.target.value;
            visiblePending = 20;
            renderPendingList();
        });
    }

    if (selectStillbirthPlace) {
        selectStillbirthPlace.addEventListener('change', (e) => {
            activeStillbirthPlace = e.target.value;
            visibleStillbirths = 20;
            renderStillbirthsList();
        });
    }

    const selectHomeMatch = document.getElementById('filter-home-match-status');
    if (selectHomeMatch) {
        selectHomeMatch.addEventListener('change', (e) => {
            visibleHomeDeliveries = 20;
            renderHomeDeliveriesList();
        });
    }

    const selectOutMatch = document.getElementById('filter-out-match-status');
    if (selectOutMatch) {
        selectOutMatch.addEventListener('change', (e) => {
            visibleOutDistrictDeliveries = 20;
            renderOutDistrictDeliveriesList();
        });
    }

    const selectDelivLocFilter = document.getElementById('filter-deliv-loc');
    if (selectDelivLocFilter) {
        selectDelivLocFilter.addEventListener('change', (e) => {
            activeDelivLocFilter = e.target.value;
            visibleOverall = 20;
            renderOverallList();
        });
    }

    const filterSncuMatch = document.getElementById('filter-sncu-match-status');
    if (filterSncuMatch) {
        filterSncuMatch.addEventListener('change', (e) => {
            activeSncuMatchStatus = e.target.value;
            visibleSncu = 20;
            renderSncuDeathsList();
        });
    }

    // Attach click listeners to all 5 SNCU KPI cards for instant filtering
    document.querySelectorAll('.sncu-kpi-filter-card').forEach(card => {
        card.addEventListener('click', () => {
            const filterVal = card.getAttribute('data-sncu-filter');
            if (filterVal) {
                activeSncuMatchStatus = filterVal;
                visibleSncu = 20;
                renderSncuDeathsList();
            }
        });
    });

    // Attach click listeners to Home Deliveries KPI cards for 1-click filtering
    document.querySelectorAll('.home-kpi-filter-card').forEach(card => {
        card.addEventListener('click', () => {
            const filterVal = card.getAttribute('data-home-filter');
            if (filterVal) {
                activeHomeMatchStatus = filterVal;
                visibleHomeDeliveries = 20;
                renderHomeDeliveriesList();
            }
        });
    });

    // Attach click listeners to Out-of-District Deliveries KPI cards for 1-click filtering
    document.querySelectorAll('.out-kpi-filter-card').forEach(card => {
        card.addEventListener('click', () => {
            const filterVal = card.getAttribute('data-out-filter');
            if (filterVal) {
                activeOutMatchStatus = filterVal;
                visibleOutDistrictDeliveries = 20;
                renderOutDistrictDeliveriesList();
            }
        });
    });
}

function resetAllPagination() {
    visibleOverall = 20;
    visiblePending = 20;
    visibleDeaths = 20;
    visibleStillbirths = 20;
    visibleOutRangeDeaths = 20;
    visibleHomeDeliveries = 20;
    visibleOutDistrictDeliveries = 20;
    visibleSncu = 20;
    visibleKhandwaSncu = 50;
}

// Setup Search Inputs
function setupSearchListeners() {
    let timeoutOverall, timeoutPending, timeoutDeaths, timeoutStillbirths, timeoutOutRange, timeoutHome, timeoutOutDist, timeoutSncu;

    const sOverall = document.getElementById('search-overall');
    if (sOverall) {
        sOverall.addEventListener('input', (e) => {
            clearTimeout(timeoutOverall);
            timeoutOverall = setTimeout(() => {
                searchOverall = e.target.value.toLowerCase().trim();
                visibleOverall = 20;
                renderOverallList();
            }, 300);
        });
    }

    const sPending = document.getElementById('search-pending');
    if (sPending) {
        sPending.addEventListener('input', (e) => {
            clearTimeout(timeoutPending);
            timeoutPending = setTimeout(() => {
                searchPending = e.target.value.toLowerCase().trim();
                visiblePending = 20;
                renderPendingList();
            }, 300);
        });
    }

    const sLost = document.getElementById('search-lost-followup');
    let timeoutLost;
    if (sLost) {
        sLost.addEventListener('input', (e) => {
            clearTimeout(timeoutLost);
            timeoutLost = setTimeout(() => {
                searchLostFollowup = e.target.value.toLowerCase().trim();
                visibleLostFollowup = 20;
                renderLostFollowupList();
            }, 300);
        });
    }

    const fLostCat = document.getElementById('filter-lost-category');
    if (fLostCat) {
        fLostCat.addEventListener('change', (e) => {
            activeLostCategory = e.target.value;
            visibleLostFollowup = 20;
            renderLostFollowupList();
        });
    }

    const loadMoreLostBtn = document.getElementById('load-more-lost-followup');
    if (loadMoreLostBtn) {
        loadMoreLostBtn.addEventListener('click', () => {
            visibleLostFollowup += 20;
            renderLostFollowupList();
        });
    }

    const sDeaths = document.getElementById('search-deaths');
    if (sDeaths) {
        sDeaths.addEventListener('input', (e) => {
            clearTimeout(timeoutDeaths);
            timeoutDeaths = setTimeout(() => {
                searchDeaths = e.target.value.toLowerCase().trim();
                visibleDeaths = 20;
                renderDeathsList();
            }, 300);
        });
    }

    const sStillbirths = document.getElementById('search-stillbirths');
    if (sStillbirths) {
        sStillbirths.addEventListener('input', (e) => {
            clearTimeout(timeoutStillbirths);
            timeoutStillbirths = setTimeout(() => {
                searchStillbirths = e.target.value.toLowerCase().trim();
                visibleStillbirths = 20;
                renderStillbirthsList();
            }, 300);
        });
    }

    const sOutRange = document.getElementById('search-out-range-deaths');
    if (sOutRange) {
        sOutRange.addEventListener('input', (e) => {
            clearTimeout(timeoutOutRange);
            timeoutOutRange = setTimeout(() => {
                searchOutRangeDeaths = e.target.value.toLowerCase().trim();
                visibleOutRangeDeaths = 20;
                renderOutRangeDeathsList();
            }, 300);
        });
    }

    const sHome = document.getElementById('search-home-deliveries');
    if (sHome) {
        sHome.addEventListener('input', (e) => {
            clearTimeout(timeoutHome);
            timeoutHome = setTimeout(() => {
                searchHomeDeliveries = e.target.value.toLowerCase().trim();
                visibleHomeDeliveries = 20;
                renderHomeDeliveriesList();
            }, 300);
        });
    }

    const sOutDist = document.getElementById('search-out-district-deliveries');
    if (sOutDist) {
        sOutDist.addEventListener('input', (e) => {
            clearTimeout(timeoutOutDist);
            timeoutOutDist = setTimeout(() => {
                searchOutDistrictDeliveries = e.target.value.toLowerCase().trim();
                visibleOutDistrictDeliveries = 20;
                renderOutDistrictDeliveriesList();
            }, 300);
        });
    }

    const sSncu = document.getElementById('search-sncu');
    if (sSncu) {
        sSncu.addEventListener('input', (e) => {
            clearTimeout(timeoutSncu);
            timeoutSncu = setTimeout(() => {
                searchSncuQuery = e.target.value.toLowerCase().trim();
                visibleSncu = 20;
                renderSncuDeathsList();
            }, 300);
        });
    }

    // Load More click handlers
    const lmOverall = document.getElementById('load-more-overall');
    if (lmOverall) {
        lmOverall.addEventListener('click', () => {
            visibleOverall += 20;
            renderOverallList();
        });
    }
    
    const lmPending = document.getElementById('load-more-pending');
    if (lmPending) {
        lmPending.addEventListener('click', () => {
            visiblePending += 20;
            renderPendingList();
        });
    }

    const lmDeaths = document.getElementById('load-more-deaths');
    if (lmDeaths) {
        lmDeaths.addEventListener('click', () => {
            visibleDeaths += 20;
            renderDeathsList();
        });
    }

    const lmStillbirths = document.getElementById('load-more-stillbirths');
    if (lmStillbirths) {
        lmStillbirths.addEventListener('click', () => {
            visibleStillbirths += 20;
            renderStillbirthsList();
        });
    }

    const lmOutRange = document.getElementById('load-more-out-range-deaths');
    if (lmOutRange) {
        lmOutRange.addEventListener('click', () => {
            visibleOutRangeDeaths += 20;
            renderOutRangeDeathsList();
        });
    }

    const lmHome = document.getElementById('load-more-home-deliveries');
    if (lmHome) {
        lmHome.addEventListener('click', () => {
            visibleHomeDeliveries += 20;
            renderHomeDeliveriesList();
        });
    }

    const lmOutDist = document.getElementById('load-more-out-district-deliveries');
    if (lmOutDist) {
        lmOutDist.addEventListener('click', () => {
            visibleOutDistrictDeliveries += 20;
            renderOutDistrictDeliveriesList();
        });
    }

    const lmSncu = document.getElementById('load-more-sncu');
    if (lmSncu) {
        lmSncu.addEventListener('click', () => {
            visibleSncu += 20;
            renderSncuDeathsList();
        });
    }
}

// Update KPI analytics cards
function updateDashboard() {
    if (!dbData) return;

    let totalBirths = 0;
    let liveBirths = 0;
    let liveBirthsEligible = 0; // Live births that have completed 28 days
    let stillbirths = 0;
    let neonatalDeaths = 0;
    let pending = 0;
    let lostToFollowup = 0;
    let completed = 0;

    // Aggregate dynamic statistics from overall_list using Block, Month, and BOTH Coordinator filters
    dbData.overall_list.forEach(item => {
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.deliv_date.substring(0, 7))) return;
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return;

        const ageInDays = getBabyAgeInDays(item.deliv_date);

        item.babies.forEach(baby => {
            totalBirths++;
            if (baby.is_stillbirth) {
                stillbirths++;
            } else {
                liveBirths++;
                if (ageInDays >= 28) {
                    liveBirthsEligible++;
                }
                if (baby.is_neonatal_death) {
                    neonatalDeaths++;
                }
            }
            
            if (baby.status === 'Pending') {
                if (ageInDays >= 29) {
                    pending++;
                }
            } else if (baby.is_lost_to_followup || (baby.status && baby.status.startsWith('Lost:'))) {
                lostToFollowup++;
            } else {
                completed++;
            }
        });
    });

    // Populate Last 7 Days Activity Table dynamically based on filters
    const activityBody = document.getElementById('activity-report-body');
    if (activityBody && dbData.activity_report) {
        let html = '';
        dbData.activity_report.forEach(row => {
            const date = row.date;
            let entriesCount = 0;
            let followupsCount = 0;
            
            dbData.overall_list.forEach(item => {
                // Filter dynamically by Block, Delivery Coordinator, and Follow-up Coordinator
                if (activeBlock !== 'ALL' && item.block !== activeBlock) return;
                if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return;
                if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return;
                
                if (item.entry_date === date) {
                    entriesCount++;
                }
                
                item.babies.forEach(baby => {
                    if (baby.call_dates) {
                        baby.call_dates.forEach(cd => {
                            if (cd === date) {
                                followupsCount++;
                            }
                        });
                    }
                });
            });
            
            html += `
                <tr style="border-bottom:1px solid var(--color-border);">
                    <td style="padding:10px; font-weight:700;">${formatDateStr(date)}</td>
                    <td style="padding:10px; font-weight:700; color:var(--color-primary);">${entriesCount.toLocaleString()}</td>
                    <td style="padding:10px; font-weight:700; color:var(--color-secondary);">${followupsCount.toLocaleString()}</td>
                </tr>
            `;
        });
        activityBody.innerHTML = html;
    }

    const liveBirthsCompleted = Math.max(0, completed - stillbirths);
    // Completion rate percentage includes only babies whose 28 days completed
    const completionRate = liveBirthsEligible > 0 ? (liveBirthsCompleted / liveBirthsEligible) * 100 : 0;
    
    document.getElementById('kpi-completion-rate').textContent = `${completionRate.toFixed(1)}%`;
    document.getElementById('kpi-completion-detail').textContent = `${liveBirthsCompleted.toLocaleString()} of ${liveBirthsEligible.toLocaleString()} eligible live births (≥ 28 days)`;

    document.getElementById('kpi-pending-count').textContent = pending.toLocaleString();
    document.getElementById('kpi-pending-detail').textContent = `${pending.toLocaleString()} babies remaining`;

    const kpiLostCount = document.getElementById('kpi-lost-count');
    if (kpiLostCount) {
        kpiLostCount.textContent = lostToFollowup.toLocaleString();
    }
    const kpiLostDetail = document.getElementById('kpi-lost-detail');
    if (kpiLostDetail) {
        const lostRate = liveBirthsEligible > 0 ? ((lostToFollowup / liveBirthsEligible) * 100).toFixed(1) : 0;
        kpiLostDetail.textContent = `${lostRate}% of eligible (${lostToFollowup.toLocaleString()} cases)`;
    }

    const nmr = liveBirths > 0 ? (neonatalDeaths / liveBirths) * 1000 : 0;
    document.getElementById('kpi-nmr-rate').textContent = nmr.toFixed(2);
    document.getElementById('kpi-nmr-detail').textContent = `${neonatalDeaths.toLocaleString()} deaths / ${liveBirths.toLocaleString()} LB`;

    const sbRate = totalBirths > 0 ? (stillbirths / totalBirths) * 1000 : 0;
    document.getElementById('kpi-stillbirth-rate').textContent = sbRate.toFixed(2);
    document.getElementById('kpi-stillbirth-detail').textContent = `${stillbirths.toLocaleString()} stillbirths / ${totalBirths.toLocaleString()} births`;

    updateTabBadges();
    renderOverviewCharts();
    renderActiveTabContent();
}

// Update badge quantities
function updateTabBadges() {
    const { overall_list, pending_list, neonatal_deaths_list, stillbirths_list, out_of_range_deaths_list, home_deliveries_list, out_district_deliveries_list } = dbData;
    
    const countOverall = overall_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.deliv_date.substring(0, 7))) return false;
        return true;
    }).length;
    document.getElementById('badge-overall').textContent = countOverall.toLocaleString();

    const countPending = pending_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        
        // Exclude infants in their neonatal period (< 29 days of age)
        const ageInDays = getBabyAgeInDays(item.delivery_date);
        return ageInDays >= 29;
    }).length;
    document.getElementById('badge-pending').textContent = countPending.toLocaleString();

    const lostList = dbData.lost_to_followup_list || [];
    const countLost = lostList.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        return true;
    }).length;
    const badgeLost = document.getElementById('badge-lost-followup');
    if (badgeLost) {
        badgeLost.textContent = countLost.toLocaleString();
    }

    const countDeaths = neonatal_deaths_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        return true;
    }).length;
    document.getElementById('badge-deaths').textContent = countDeaths.toLocaleString();

    const countStillbirths = stillbirths_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        return true;
    }).length;
    document.getElementById('badge-stillbirths').textContent = countStillbirths.toLocaleString();

    const countOutRange = out_of_range_deaths_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        return true;
    }).length;
    document.getElementById('badge-out-range-deaths').textContent = countOutRange.toLocaleString();

    const countHome = home_deliveries_list ? home_deliveries_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        return true;
    }).length : 0;
    document.getElementById('badge-home-deliveries').textContent = countHome.toLocaleString();

    const countOutDist = out_district_deliveries_list ? out_district_deliveries_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        return true;
    }).length : 0;
    document.getElementById('badge-out-district-deliveries').textContent = countOutDist.toLocaleString();

    const countSncu = (dbData && dbData.sncu_deaths_list) ? dbData.sncu_deaths_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.month)) return false;
        return true;
    }).length : 0;
    const badgeSncuEl = document.getElementById('badge-sncu-deaths');
    if (badgeSncuEl) badgeSncuEl.textContent = countSncu.toLocaleString();

    const countKhandwaSncu = (dbData && dbData.khandwa_sncu_deaths_list) ? dbData.khandwa_sncu_deaths_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.month)) return false;
        return true;
    }).length : 0;
    const badgeKhandwaSncuEl = document.getElementById('badge-khandwa-sncu-deaths');
    if (badgeKhandwaSncuEl) badgeKhandwaSncuEl.textContent = countKhandwaSncu.toLocaleString();
}

function renderActiveTabContent() {
    if (activeTab === 'overview') {
        renderOverviewCharts();
    } else if (activeTab === 'overall') {
        renderOverallList();
    } else if (activeTab === 'pending') {
        renderPendingList();
    } else if (activeTab === 'lost-followup') {
        renderLostFollowupList();
    } else if (activeTab === 'deaths') {
        renderDeathsList();
    } else if (activeTab === 'stillbirths') {
        renderStillbirthsList();
    } else if (activeTab === 'out-range-deaths') {
        renderOutRangeDeathsList();
    } else if (activeTab === 'home-deliveries') {
        renderHomeDeliveriesList();
    } else if (activeTab === 'out-district-deliveries') {
        renderOutDistrictDeliveriesList();
    } else if (activeTab === 'sncu-deaths') {
        renderSncuDeathsList();
    } else if (activeTab === 'khandwa-sncu-deaths') {
        renderKhandwaSncuDeathsList();
    }
}

// Chart Renderings
function renderOverviewCharts() {
    if (typeof Chart === 'undefined') {
        console.warn("[WARN] Chart.js is not loaded. Skipping chart rendering.");
        return;
    }

    let { months, blocks, deliv_coordinators, followup_coordinators } = dbData.metadata;
    months = months.filter(m => activeMonths.includes('ALL') || activeMonths.includes(m));

    const monthlyData = {};
    months.forEach(m => { monthlyData[m] = { completed: 0, pending: 0 }; });

    dbData.overall_list.forEach(item => {
        
        const rMonth = item.deliv_date.substring(0, 7);
        if (!monthlyData[rMonth]) return;
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return;

        item.babies.forEach(baby => {
            if (baby.is_stillbirth) return;
            if (baby.status === 'Pending') {
                monthlyData[rMonth].pending++;
            } else {
                monthlyData[rMonth].completed++;
            }
        });
    });

    const trendLabels = [];
    const trendCompleted = [];
    const trendPending = [];
    const trendRate = [];

    months.forEach(m => {
        const parts = m.split('-');
        let label = m;
        if (parts.length === 2) {
            const dateObj = new Date(parts[0], parts[1] - 1);
            label = dateObj.toLocaleDateString('default', { month: 'short', year: '2-digit' });
        }
        trendLabels.push(label);
        const comp = monthlyData[m].completed;
        const pend = monthlyData[m].pending;
        const total = comp + pend;
        const rate = total > 0 ? parseFloat(((comp / total) * 100).toFixed(1)) : 0;

        trendCompleted.push(comp);
        trendPending.push(pend);
        trendRate.push(rate);
    });

    if (trendChart) trendChart.destroy();
    
    const ctxTrend = document.getElementById('monthlyTrendChart').getContext('2d');
    trendChart = new Chart(ctxTrend, {
        data: {
            labels: trendLabels,
            datasets: [
                {
                    label: 'Completed Follow-ups',
                    data: trendCompleted,
                    backgroundColor: '#0f766e',
                    stack: 'Stack 0',
                    type: 'bar',
                    yAxisID: 'y',
                    order: 2
                },
                {
                    label: 'Pending Follow-ups',
                    data: trendPending,
                    backgroundColor: '#f59e0b',
                    stack: 'Stack 0',
                    type: 'bar',
                    yAxisID: 'y',
                    order: 2
                },
                {
                    label: 'Follow-up Completion Rate (%)',
                    data: trendRate,
                    borderColor: '#10b981',
                    backgroundColor: '#10b981',
                    borderWidth: 2.5,
                    pointRadius: 3.5,
                    pointHoverRadius: 5.5,
                    type: 'line',
                    fill: false,
                    tension: 0.3,
                    yAxisID: 'y1',
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 12, font: { family: 'Plus Jakarta Sans', size: 10 } }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.type === 'line' || context.dataset.yAxisID === 'y1') {
                                return `Completion Rate: ${context.parsed.y.toFixed(1)}%`;
                            }
                            return `${context.dataset.label}: ${context.parsed.y.toLocaleString()} cases`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    grid: { display: false },
                    ticks: { font: { family: 'Plus Jakarta Sans', size: 9 } }
                },
                y: {
                    stacked: true,
                    position: 'left',
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: { font: { family: 'Plus Jakarta Sans', size: 9 } }
                },
                y1: {
                    position: 'right',
                    beginAtZero: true,
                    min: 0,
                    max: 100,
                    grid: { display: false },
                    ticks: {
                        font: { family: 'Plus Jakarta Sans', size: 9 },
                        callback: function(value) { return value + '%'; }
                    }
                }
            }
        }
    });

    const isBlockFiltered = activeBlock !== 'ALL';
    const compareLabels = [];
    const compareIssues = [];

    if (!isBlockFiltered) {
        const blockIssues = {};
        blocks.forEach(b => { blockIssues[b] = 0; });

        dbData.overall_list.forEach(item => {
            if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.deliv_date.substring(0, 7))) return;
            if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return;
            if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return;

            if (item.has_disc) {
                blockIssues[item.block] += item.disc_reasons.length;
            }
        });

        const sorted = Object.keys(blockIssues)
            .map(b => ({ name: b, count: blockIssues[b] }))
            .sort((a, b) => b.count - a.count);

        sorted.forEach(item => {
            compareLabels.push(item.name);
            compareIssues.push(item.count);
        });
    } else {
        const coordIssues = {};
        deliv_coordinators.forEach(c => { coordIssues[c] = 0; });

        dbData.overall_list.forEach(item => {
            if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.deliv_date.substring(0, 7))) return;
            if (item.block !== activeBlock) return;

            if (item.has_disc) {
                coordIssues[item.coord] += item.disc_reasons.length;
            }
        });

        const sorted = Object.keys(coordIssues)
            .map(c => ({ name: c, count: coordIssues[c] }))
            .filter(item => item.count > 0)
            .sort((a, b) => b.count - a.count);

        sorted.forEach(item => {
            compareLabels.push(item.name);
            compareIssues.push(item.count);
        });
    }

    if (blockChart) blockChart.destroy();

    const ctxCompare = document.getElementById('blockCompletionChart').getContext('2d');
    blockChart = new Chart(ctxCompare, {
        type: 'bar',
        data: {
            labels: compareLabels,
            datasets: [{ 
                label: 'Validation Errors', 
                data: compareIssues, 
                backgroundColor: '#dc2626', 
                borderRadius: 4 
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Errors: ${context.parsed.x}`;
                        }
                    }
                }
            },
            scales: {
                x: { 
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' }, 
                    ticks: { 
                        font: { family: 'Plus Jakarta Sans', size: 9 }, 
                        precision: 0
                    } 
                },
                y: { grid: { display: false }, ticks: { font: { family: 'Plus Jakarta Sans', size: 9, weight: 'bold' } } }
            }
        }
    });

    // --- Mixed Mortality & Stillbirth Trends Chart (NMR & SBR) ---
    const monthlyLiveBirths = {};
    const monthlyTotalBirths = {};
    const monthlyDeaths = {};
    const monthlyStillbirths = {};
    months.forEach(m => {
        monthlyLiveBirths[m] = 0;
        monthlyTotalBirths[m] = 0;
        monthlyDeaths[m] = 0;
        monthlyStillbirths[m] = 0;
    });

    dbData.overall_list.forEach(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return;

        const rMonth = item.deliv_date.substring(0, 7);
        if (monthlyLiveBirths[rMonth] === undefined) return;

        item.babies.forEach(baby => {
            if (baby.is_stillbirth) {
                monthlyStillbirths[rMonth]++;
                monthlyTotalBirths[rMonth]++;
            } else {
                monthlyLiveBirths[rMonth]++;
                monthlyTotalBirths[rMonth]++;
                if (baby.is_neonatal_death) {
                    monthlyDeaths[rMonth]++;
                }
            }
        });
    });

    const trendLabels2 = [];
    const monthlyNMR = [];
    const monthlySBR = [];

    months.forEach(m => {
        const parts = m.split('-');
        let label = m;
        if (parts.length === 2) {
            const dateObj = new Date(parts[0], parts[1] - 1);
            label = dateObj.toLocaleDateString('default', { month: 'short', year: '2-digit' });
        }
        trendLabels2.push(label);
        
        const nmr = monthlyLiveBirths[m] > 0 ? (monthlyDeaths[m] / monthlyLiveBirths[m]) * 1000 : 0;
        const sbr = monthlyTotalBirths[m] > 0 ? (monthlyStillbirths[m] / monthlyTotalBirths[m]) * 1000 : 0;
        
        monthlyNMR.push(parseFloat(nmr.toFixed(2)));
        monthlySBR.push(parseFloat(sbr.toFixed(2)));
    });

    const getMovingAverage = (arr) => {
        const ma = [];
        for (let i = 0; i < arr.length; i++) {
            let sum = 0;
            let count = 0;
            for (let j = Math.max(0, i - 2); j <= i; j++) {
                sum += arr[j];
                count++;
            }
            ma.push(count > 0 ? parseFloat((sum / count).toFixed(2)) : 0);
        }
        return ma;
    };

    const nmrMA = getMovingAverage(monthlyNMR);
    const sbrMA = getMovingAverage(monthlySBR);

    if (mortalityChart) mortalityChart.destroy();

    const ctxMortality = document.getElementById('mortalityTrendChart').getContext('2d');
    mortalityChart = new Chart(ctxMortality, {
        type: 'bar',
        data: {
            labels: trendLabels2,
            datasets: [
                {
                    label: 'NMR (per 1000 LB)',
                    data: monthlyNMR,
                    backgroundColor: 'rgba(239, 68, 68, 0.65)',
                    borderColor: '#ef4444',
                    borderWidth: 1.5,
                    type: 'bar',
                    order: 2
                },
                {
                    label: 'SBR (per 1000 Births)',
                    data: monthlySBR,
                    backgroundColor: 'rgba(59, 130, 246, 0.65)',
                    borderColor: '#3b82f6',
                    borderWidth: 1.5,
                    type: 'bar',
                    order: 2
                },
                {
                    label: 'NMR (3-Mo MA)',
                    data: nmrMA,
                    borderColor: '#b91c1c',
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    type: 'line',
                    fill: false,
                    tension: 0.3,
                    order: 1
                },
                {
                    label: 'SBR (3-Mo MA)',
                    data: sbrMA,
                    borderColor: '#1d4ed8',
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    type: 'line',
                    fill: false,
                    tension: 0.3,
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: { family: 'Plus Jakarta Sans', size: 10 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const month = months[context.dataIndex];
                            if (context.dataset.label.includes('NMR (per 1000 LB)')) {
                                const deaths = monthlyDeaths[month] || 0;
                                const lb = monthlyLiveBirths[month] || 0;
                                return `NMR: ${context.parsed.y.toFixed(2)} per 1000 LB (${deaths} deaths / ${lb.toLocaleString()} live births)`;
                            }
                            if (context.dataset.label.includes('SBR (per 1000 Births)')) {
                                const sb = monthlyStillbirths[month] || 0;
                                const tb = monthlyTotalBirths[month] || 0;
                                return `SBR: ${context.parsed.y.toFixed(2)} per 1000 Total Births (${sb} stillbirths / ${tb.toLocaleString()} total births)`;
                            }
                            if (context.dataset.label.includes('NMR (3-Mo MA)')) {
                                return `NMR (3-Mo MA): ${context.parsed.y.toFixed(2)} per 1000 LB`;
                            }
                            if (context.dataset.label.includes('SBR (3-Mo MA)')) {
                                return `SBR (3-Mo MA): ${context.parsed.y.toFixed(2)} per 1000 Total Births`;
                            }
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Plus Jakarta Sans', size: 9 } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: { font: { family: 'Plus Jakarta Sans', size: 9 }, precision: 1 }
                }
            }
        }
    });

    // --- Place of Delivery Distribution Chart ---
    const placeCounts = {
        'Public Facility (In-District)': [],
        'Private Facility (In-District)': [],
        'Home (In-District)': [],
        'On the Way': [],
        'Out of District': [],
        'Other/Unspecified': []
    };

    months.forEach(m => {
        let pub_in = 0, priv_in = 0, home_in = 0, otw = 0;
        let out_dist = 0, other_unspec = 0;

        dbData.overall_list.forEach(item => {
            if (activeBlock !== 'ALL' && item.block !== activeBlock) return;
            if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return;
            if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return;

            const rMonth = item.deliv_date.substring(0, 7);
            if (rMonth !== m) return;

            const cat = item.place_cat || 'Other/Unspecified';
            if (cat === 'Public Facility (In-District)') pub_in++;
            else if (cat === 'Private Facility (In-District)') priv_in++;
            else if (cat === 'Home (In-District)') home_in++;
            else if (cat === 'On the Way') otw++;
            else if (cat === 'Out of District') out_dist++;
            else other_unspec++;
        });

        placeCounts['Public Facility (In-District)'].push(pub_in);
        placeCounts['Private Facility (In-District)'].push(priv_in);
        placeCounts['Home (In-District)'].push(home_in);
        placeCounts['On the Way'].push(otw);
        placeCounts['Out of District'].push(out_dist);
        placeCounts['Other/Unspecified'].push(other_unspec);
    });

    if (placeOfDeliveryChart) placeOfDeliveryChart.destroy();

    const ctxPlace = document.getElementById('placeOfDeliveryChart').getContext('2d');
    placeOfDeliveryChart = new Chart(ctxPlace, {
        type: 'bar',
        data: {
            labels: trendLabels2,
            datasets: [
                {
                    label: 'Public (In-District)',
                    data: placeCounts['Public Facility (In-District)'],
                    backgroundColor: '#3b82f6',
                },
                {
                    label: 'Private (In-District)',
                    data: placeCounts['Private Facility (In-District)'],
                    backgroundColor: '#10b981',
                },
                {
                    label: 'Home (In-District)',
                    data: placeCounts['Home (In-District)'],
                    backgroundColor: '#f59e0b',
                },
                {
                    label: 'On the Way',
                    data: placeCounts['On the Way'],
                    backgroundColor: '#64748b',
                },
                {
                    label: 'Out of District',
                    data: placeCounts['Out of District'],
                    backgroundColor: '#8b5cf6',
                },
                {
                    label: 'Other/Unspecified',
                    data: placeCounts['Other/Unspecified'],
                    backgroundColor: '#cbd5e1',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: { family: 'Plus Jakarta Sans', size: 10 }
                    }
                }
            },
            scales: {
                x: { stacked: true, grid: { display: false }, ticks: { font: { family: 'Plus Jakarta Sans', size: 9 } } },
                y: { stacked: true, beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { family: 'Plus Jakarta Sans', size: 9 }, precision: 0 } }
            }
        }
    });
}

function formatDateStr(str) {
    if (!str || str === 'N/A' || str === 'Not Recorded') return str || "N/A";
    const parts = str.split(' ')[0].split(/[T\-]/);
    if (parts.length === 3) {
        if (parts[0].length === 4) {
            // yyyy-mm-dd
            return `${parts[2].padStart(2, '0')}-${parts[1].padStart(2, '0')}-${parts[0]}`;
        } else if (parts[2].length === 4) {
            // dd-mm-yyyy or mm-dd-yyyy
            return `${parts[0].padStart(2, '0')}-${parts[1].padStart(2, '0')}-${parts[2]}`;
        }
    }
    const dateObj = new Date(str);
    if (isNaN(dateObj.getTime())) return str;
    const dd = String(dateObj.getDate()).padStart(2, '0');
    const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
    const yyyy = dateObj.getFullYear();
    return `${dd}-${mm}-${yyyy}`;
}

function getBabyBadgeClass(status) {
    status = status.toLowerCase();
    if (status === 'pending') return 'pending';
    if (status === 'completed') return 'completed';
    if (status === 'dead') return 'dead';
    return 'stillbirth';
}

// Generate call status timelines
function renderCallTimelineHtml(baby) {
    const s = baby.call_statuses[2]; // Call 3 is at index 2 (final status)
    return `
        <div class="calls-timeline" style="grid-template-columns: 1fr;">
            <div class="call-step" style="display:flex; justify-content:space-between; align-items:center; width:100%; border-left: 3px solid var(--color-primary); padding-left: 8px;">
                <span class="call-label" style="font-weight:700;">Final Status</span>
                <span class="call-status-val ${s ? s.toLowerCase() : 'empty'}">${s || 'Pending'}</span>
            </div>
        </div>
    `;
}

// Toggle drawer details in Desktop table layouts
function toggleDesktopRow(rowEl, recordId, type) {
    const nextEl = rowEl.nextElementSibling;
    if (nextEl && nextEl.classList.contains('table-detail-row')) {
        nextEl.remove();
        rowEl.classList.remove('expanded-row');
        return;
    }

    rowEl.classList.add('expanded-row');
    
    let record = null;
    let colspanVal = 10;
    
    if (type === 'overall') {
        record = (dbData.overall_list || []).find(x => String(x.id) === String(recordId));
        colspanVal = 11;
    } else if (type === 'pending') {
        record = (dbData.pending_list || []).find(x => String(x.id) === String(recordId));
        colspanVal = 9;
    } else if (type === 'home-deliveries') {
        record = (dbData.home_deliveries_list || []).find(x => String(x.id) === String(recordId));
        colspanVal = 8;
    } else if (type === 'out-district-deliveries') {
        record = (dbData.out_district_deliveries_list || []).find(x => String(x.id) === String(recordId));
        colspanVal = 9;
    } else if (type === 'sncu') {
        record = (dbData.sncu_deaths_list || []).find(x => String(x.adm_id) === String(recordId));
        colspanVal = 10;
    } else if (type === 'khandwa_sncu') {
        record = (dbData.khandwa_sncu_deaths_list || []).find(x => String(x.adm_id) === String(recordId));
        colspanVal = 10;
    }
    
    if (!record) {
        console.warn("[WARN] Record not found for row toggle:", recordId, type);
        return;
    }

    // -------------------------------------------------------------
    // CASE A: SNCU DEATHS (7-STEP CHRONOLOGICAL COMPARISON)
    // -------------------------------------------------------------
    if (type === 'sncu' || type === 'khandwa_sncu') {
        const mc = record.match_criteria || {};
        const isAccurate = record.match_type === 'accurate';
        const isSpelling = record.match_type === 'spelling';
        const isUnmatched = !isAccurate && !isSpelling;

        const isDeadInRC = record.redcap_status === 'dead' || record.redcap_status === 'stillbirth';
        const isPendingInRC = record.redcap_status === 'pending';
        const isHealthyInRC = record.redcap_status === 'healthy';

        let borderClr = '#64748b';
        let bgClr = '#f8fafc';
        let txtClr = '#334155';
        let titleStr = 'Not Recorded in REDCap Repository';

        if (isDeadInRC) {
            borderClr = '#10b981';
            bgClr = '#ecfdf5';
            txtClr = '#047857';
            titleStr = 'Verified Neonatal Death in REDCap Repository';
        } else if (isPendingInRC) {
            borderClr = '#f59e0b';
            bgClr = '#fffbeb';
            txtClr = '#b45309';
            titleStr = 'Action Required: Died in SNCU, but REDCap Status is Still Pending Follow-up';
        } else if (isHealthyInRC) {
            borderClr = '#ec4899';
            bgClr = '#fdf2f8';
            txtClr = '#be185d';
            titleStr = 'Discrepancy Alert: Died in SNCU, but REDCap Status is Recorded as Healthy / Completed';
        } else if (isAccurate || isSpelling) {
            borderClr = isAccurate ? '#10b981' : '#f59e0b';
            bgClr = isAccurate ? '#ecfdf5' : '#fffbeb';
            txtClr = isAccurate ? '#047857' : '#b45309';
            titleStr = isAccurate ? 'Matched Record in REDCap Repository' : 'Matched with Spelling / Data Difference in REDCap';
        }

        let actionCallout = '';
        if (isPendingInRC) {
            actionCallout = `
                <div style="background-color: #fff7ed; border: 1px solid #fdba74; padding: 8px 12px; border-radius: var(--radius-sm); margin-bottom: 10px; color: #9a3412; font-size: 0.78rem; display: flex; align-items: flex-start; gap: 6px;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" style="width:16px; height:16px; flex-shrink:0; margin-top:1px;">
                        <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
                    </svg>
                    <div><strong>Telecaller Follow-up Note:</strong> This infant expired in SNCU (${type === 'khandwa_sncu' ? 'GMC Khandwa' : 'DH Khargone'}) on <strong>${formatDateStr(record.death_date)}</strong>. In REDCap (${record.redcap_id}), follow-up is currently <strong>PENDING</strong>. Status should be updated to 'Dead' with recorded date of death.</div>
                </div>
            `;
        } else if (isHealthyInRC) {
            actionCallout = `
                <div style="background-color: #fef2f2; border: 1px solid #fecaca; padding: 8px 12px; border-radius: var(--radius-sm); margin-bottom: 10px; color: #991b1b; font-size: 0.78rem; display: flex; align-items: flex-start; gap: 6px;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" style="width:16px; height:16px; flex-shrink:0; margin-top:1px;">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" />
                    </svg>
                    <div><strong>Critical Outcome Discrepancy:</strong> REDCap follow-up recorded baby as <strong>HEALTHY / COMPLETED</strong>, but SNCU clinical records confirm infant passed away on <strong>${formatDateStr(record.death_date)}</strong>. Supervisor investigation recommended.</div>
                </div>
            `;
        }

        const matchDetailsBlock = `
            <div style="background-color: ${bgClr}; border: 1px solid ${borderClr}; padding: 14px 16px; border-radius: var(--radius-sm); margin-bottom: 12px; color: ${txtClr};">
                <div style="font-weight:700; font-size:0.85rem; display:flex; align-items:center; gap:6px; margin-bottom:10px; text-transform:uppercase;">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" style="width:16px; height:16px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
                    </svg>
                    ${titleStr}
                </div>
                ${actionCallout}
                
                

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px 24px; font-size: 0.82rem; border-bottom: 1px dashed ${borderClr}; padding-bottom: 10px; margin-bottom: 10px;">
                    <!-- Record IDs -->
                    <div>SNCU Admission ID: <strong>${record.adm_id}</strong></div>
                    <div>REDCap Record ID: <strong>${record.redcap_id || '<span style="color:var(--color-text-muted);">None</span>'}</strong></div>

                    <!-- 1. Block -->
                    <div>1. SNCU Block: <strong>${record.block}</strong> ${record.village ? `(${record.village})` : ''}</div>
                    <div>1. REDCap Block: <strong>${record.redcap_block || '<span style="color:var(--color-text-muted);">None</span>'}</strong> ${mc.block ? '<span style="color:#047857; font-weight:700;">(✓ Matched)</span>' : '<span style="color:#b91c1c;">(✗ Mismatched)</span>'}</div>

                    <!-- 2. Place of Delivery -->
                    <div>2. SNCU Place of Delivery: <strong>${record.deliv_place || 'Not Recorded'}</strong></div>
                    <div>2. REDCap Place of Delivery: <strong>${record.redcap_deliv_place || '<span style="color:var(--color-text-muted);">Not Recorded</span>'}</strong> ${mc.deliv_place ? '<span style="color:#047857; font-weight:700;">(✓ Matched)</span>' : '<span style="color:#64748b;">(Unverified)</span>'}</div>

                    <!-- 3. Place of Death -->
                    <div>3. SNCU Place of Death: <strong>${type === 'khandwa_sncu' ? 'GMC Khandwa (SNCU)' : 'DH Khargone (SNCU)'}</strong></div>
                    <div>3. REDCap Place of Death: <strong>${record.rc_place_of_death || '<span style="color:var(--color-text-muted);">Not Recorded</span>'}</strong> ${mc.death_place ? '<span style="color:#047857; font-weight:700;">(✓ Matched)</span>' : '<span style="color:#64748b;">(Unverified)</span>'}</div>

                    <!-- 4. Delivery Date / DOB -->
                    <div>4. SNCU Date of Birth (DOB): <strong>${formatDateStr(record.dob)}</strong></div>
                    <div>4. REDCap Delivery Date: <strong>${formatDateStr(record.redcap_deliv_date)}</strong> ${mc.dob ? '<span style="color:#047857; font-weight:700;">(✓ Exact Match)</span>' : '<span style="color:#b91c1c;">(✗ Mismatched)</span>'}</div>

                    <!-- 5. Mother Name -->
                    <div>5. SNCU Mother Name: <strong>${record.mother_name}</strong></div>
                    <div>5. REDCap Mother Name: <strong>${record.redcap_mother || '<span style="color:var(--color-text-muted);">None</span>'}</strong> ${mc.mother_name ? '<span style="color:#047857; font-weight:700;">(✓ Matched)</span>' : '<span style="color:#b91c1c;">(✗ Mismatched)</span>'}</div>

                    <!-- 6. Father Name -->
                    <div>6. SNCU Father Name: <strong>${record.father_name || '<span style="color:var(--color-text-muted);">Not Recorded</span>'}</strong></div>
                    <div>6. REDCap Father Name: <strong>${record.redcap_father || '<span style="color:var(--color-text-muted);">None</span>'}</strong> ${mc.father_name ? '<span style="color:#047857; font-weight:700;">(✓ Matched)</span>' : (record.father_name ? '<span style="color:#b91c1c;">(✗ Mismatched)</span>' : '<span style="color:#64748b;">(Not Recorded)</span>')}</div>

                    <!-- 7. Contact / Mobile Number -->
                    <div>7. SNCU Contact No.: <strong>${record.contact || 'N/A'}</strong></div>
                    <div>7. REDCap Mobile No.: <strong>${record.redcap_phone || '<span style="color:var(--color-text-muted);">None</span>'}</strong> ${mc.phone ? '<span style="color:#047857; font-weight:700;">(✓ Matched)</span>' : '<span style="color:#b91c1c;">(✗ Mismatched)</span>'}</div>

                    <!-- 8. Date of Death vs Date of Discharge -->
                    <div>8. SNCU Discharge Date (Date of Death): <strong>${formatDateStr(record.death_date)}</strong></div>
                    <div>8. REDCap Date of Death: <strong>${record.rc_death_date ? formatDateStr(record.rc_death_date) : '<span style="color:var(--color-text-muted);">Not Recorded</span>'}</strong> ${mc.death_date ? '<span style="color:#047857; font-weight:700;">(✓ Matched)</span>' : '<span style="color:#64748b;">(Unverified)</span>'}</div>

                    <!-- 9. Birth Weight -->
                    <div>9. SNCU Birth Weight: <strong>${record.weight_g ? record.weight_g + 'g (' + record.weight + ' kg)' : (record.weight ? record.weight + ' kg' : 'N/A')}</strong></div>
                    <div>9. REDCap Birth Weight: <strong>${record.rc_weight_g ? record.rc_weight_g + 'g' : '<span style="color:var(--color-text-muted); font-weight:400;">Not Recorded</span>'}</strong> ${mc.weight ? '<span style="color:#047857; font-weight:700;">(✓ Matched)</span>' : '<span style="color:#64748b;">(Unverified)</span>'}</div>

                    <!-- Age at Death (Additional Details) -->
                    <div>SNCU Age at Death: <strong style="color: var(--color-danger); font-weight:700;">${record.age_at_death !== null && record.age_at_death !== undefined ? record.age_at_death + ' days' : 'N/A'}</strong></div>
                    <div>REDCap Age at Death: <strong style="color: var(--color-danger); font-weight:700;">${record.rc_age_at_death !== null && record.rc_age_at_death !== undefined ? record.rc_age_at_death + ' days' : '<span style="color:var(--color-text-muted); font-weight:400;">Not Recorded</span>'}</strong> ${mc.age_death ? '<span style="color:#047857; font-weight:700;">(✓ Matched)</span>' : ''}</div>
                </div>

                <div style="font-weight:700; font-size:0.75rem; display:block; margin-bottom:6px; text-transform:uppercase;">
                    Match Criteria Verification (${record.matched_criteria_count || 0}/9 Matched):
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:8px 16px; font-size: 0.75rem; border-bottom: 1px dashed ${borderClr}; padding-bottom: 8px; margin-bottom: 8px;">
                    <div style="display:flex; align-items:center; gap:4px;">
                        ${mc.block ? '<span style="color:#10b981; font-weight:900;">✓</span> <span>1. Block</span>' : '<span style="color:#94a3b8; font-weight:900;">—</span> <span style="color:#64748b;">1. Block</span>'}
                    </div>
                    <div style="display:flex; align-items:center; gap:4px;">
                        ${mc.deliv_place ? '<span style="color:#10b981; font-weight:900;">✓</span> <span>2. Place of Delivery</span>' : '<span style="color:#94a3b8; font-weight:900;">—</span> <span style="color:#64748b;">2. Place of Delivery</span>'}
                    </div>
                    <div style="display:flex; align-items:center; gap:4px;">
                        ${mc.death_place ? '<span style="color:#10b981; font-weight:900;">✓</span> <span>3. Place of Death</span>' : '<span style="color:#94a3b8; font-weight:900;">—</span> <span style="color:#64748b;">3. Place of Death</span>'}
                    </div>
                    <div style="display:flex; align-items:center; gap:4px;">
                        ${mc.dob ? '<span style="color:#10b981; font-weight:900;">✓</span> <span>4. Delivery Date/DOB</span>' : '<span style="color:#ef4444; font-weight:900;">✗</span> <span style="color:#ef4444;">4. Delivery Date/DOB</span>'}
                    </div>
                    <div style="display:flex; align-items:center; gap:4px;">
                        ${mc.mother_name ? '<span style="color:#10b981; font-weight:900;">✓</span> <span>5. Mother Name</span>' : '<span style="color:#ef4444; font-weight:900;">✗</span> <span style="color:#ef4444;">5. Mother Name</span>'}
                    </div>
                    <div style="display:flex; align-items:center; gap:4px;">
                        ${mc.father_name ? '<span style="color:#10b981; font-weight:900;">✓</span> <span>6. Father Name</span>' : '<span style="color:#94a3b8; font-weight:900;">—</span> <span style="color:#64748b;">6. Father Name</span>'}
                    </div>
                    <div style="display:flex; align-items:center; gap:4px;">
                        ${mc.phone ? '<span style="color:#10b981; font-weight:900;">✓</span> <span>7. Mobile/Contact No.</span>' : '<span style="color:#ef4444; font-weight:900;">✗</span> <span style="color:#ef4444;">7. Mobile/Contact No.</span>'}
                    </div>
                    <div style="display:flex; align-items:center; gap:4px;">
                        ${mc.death_date ? '<span style="color:#10b981; font-weight:900;">✓</span> <span>8. Date of Death</span>' : '<span style="color:#94a3b8; font-weight:900;">—</span> <span style="color:#64748b;">8. Date of Death</span>'}
                    </div>
                    <div style="display:flex; align-items:center; gap:4px;">
                        ${mc.weight ? '<span style="color:#10b981; font-weight:900;">✓</span> <span>9. Birth Weight</span>' : '<span style="color:#94a3b8; font-weight:900;">—</span> <span style="color:#64748b;">9. Birth Weight</span>'}
                    </div>
                </div>
                <div style="font-size:0.8rem; line-height:1.4;">
                    <strong>Cause of Death / Clinical Diagnosis:</strong> <span style="color: #334155; font-weight:600;">${record.cause || 'Not Recorded'}</span>
                    ${record.address ? ` | <strong>Address:</strong> ${record.address}` : ''}
                </div>
            </div>
        `;

        const detailRow = document.createElement('tr');
        detailRow.className = 'table-detail-row';
        detailRow.innerHTML = `
            <td colspan="${colspanVal}">
                <div class="desktop-detail-container" onclick="event.stopPropagation()">
                    ${matchDetailsBlock}
                </div>
            </td>
        `;
        rowEl.parentNode.insertBefore(detailRow, rowEl.nextSibling);
        return;
    }

    // -------------------------------------------------------------
    // CASE B: ANMOL DELIVERIES (HOME & OUT-OF-DISTRICT)
    // -------------------------------------------------------------
    if (record.is_anmol_data || type === 'home-deliveries' || type === 'out-district-deliveries') {
        let matchDetailsBlock = '';
        if (record.match_status === 'spelling' || record.match_status === 'exact') {
            const borderClr = record.match_status === 'exact' ? '#10b981' : '#f59e0b';
            const bgClr = record.match_status === 'exact' ? '#ecfdf5' : '#fffbeb';
            const txtClr = record.match_status === 'exact' ? '#047857' : '#b45309';
            const titleStr = record.match_status === 'exact' ? 'Accurately Recorded in REDCap' : 'Recorded with Spelling / Data Mismatch in REDCap';
            
            const mc = record.match_criteria || {};
            matchDetailsBlock = `
                <div style="background-color: ${bgClr}; border: 1px solid ${borderClr}; padding: 12px 16px; border-radius: var(--radius-sm); margin-bottom: 12px; color: ${txtClr};">
                    <div style="font-weight:700; font-size:0.85rem; display:flex; align-items:center; gap:6px; margin-bottom:8px; text-transform:uppercase;">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" style="width:14px; height:14px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
                        </svg>
                        ${titleStr}
                    </div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px 16px; font-size: 0.8rem; border-bottom: 1px dashed ${borderClr}; padding-bottom: 8px; margin-bottom: 8px;">
                        <div>REDCap Record ID: <strong>${record.redcap_id}</strong></div>
                        <div>&nbsp;</div>
                        <div>Anmol Mother Name: <strong>${record.pw_name}</strong></div>
                        <div>REDCap Mother Name: <strong>${record.redcap_mother}</strong></div>
                        <div>Anmol Husband Name: <strong>${record.husband_name || 'N/A'}</strong></div>
                        <div>REDCap Husband Name: <strong>${record.redcap_husband || 'N/A'}</strong></div>
                        <div>Anmol Delivery Date: <strong>${formatDateStr(record.delivery_date)}</strong></div>
                        <div>REDCap Delivery Date: <strong>${formatDateStr(record.redcap_deliv_date)}</strong></div>
                        <div>Anmol Mobile No.: <strong>${record.phone || 'N/A'}</strong></div>
                        <div>REDCap Mobile No.: <strong>${record.redcap_phone || 'N/A'}</strong></div>
                        <div>Anmol Block: <strong>${record.block || 'N/A'}</strong></div>
                        <div>REDCap Block: <strong>${record.redcap_block || 'N/A'}</strong></div>
                    </div>
                    <div style="font-weight:700; font-size:0.75rem; display:block; margin-bottom:6px; text-transform:uppercase;">
                        Match Criteria Verification:
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:8px 16px; font-size: 0.75rem;">
                        <div style="display:flex; align-items:center; gap:4px;">
                            ${mc.mp_id ? `
                                <span style="color:#10b981; font-weight:900;">✓</span> <span style="text-decoration:underline;">MP ID Matched</span>
                            ` : `
                                <span style="color:#ef4444; font-weight:900;">✗</span> <span>MP ID Mismatched/Empty</span>
                            `}
                        </div>
                        <div style="display:flex; align-items:center; gap:4px;">
                            ${mc.name ? `
                                <span style="color:#10b981; font-weight:900;">✓</span> <span style="text-decoration:underline;">Names Matched</span>
                            ` : `
                                <span style="color:#ef4444; font-weight:900;">✗</span> <span>Names Mismatched</span>
                            `}
                        </div>
                        <div style="display:flex; align-items:center; gap:4px;">
                            ${mc.date ? `
                                <span style="color:#10b981; font-weight:900;">✓</span> <span style="text-decoration:underline;">Delivery Date Matched</span>
                            ` : `
                                <span style="color:#ef4444; font-weight:900;">✗</span> <span>Delivery Date Mismatched</span>
                            `}
                        </div>
                        <div style="display:flex; align-items:center; gap:4px;">
                            ${mc.phone ? `
                                <span style="color:#10b981; font-weight:900;">✓</span> <span style="text-decoration:underline;">Mobile No. Matched</span>
                            ` : `
                                <span style="color:#ef4444; font-weight:900;">✗</span> <span>Mobile No. Mismatched</span>
                            `}
                        </div>
                        <div style="display:flex; align-items:center; gap:4px;">
                            ${mc.block ? `
                                <span style="color:#10b981; font-weight:900;">✓</span> <span style="text-decoration:underline;">Block Matched</span>
                            ` : `
                                <span style="color:#ef4444; font-weight:900;">✗</span> <span>Block Mismatched</span>
                            `}
                        </div>
                    </div>
                </div>
            `;
        }

        const addressBlock = `
            <div class="mother-address-block" style="margin-bottom:12px; grid-template-columns: repeat(3, 1fr); gap: 12px 20px;">
                <div class="address-item">
                    <span class="address-label">Village Name</span>
                    <span class="address-val">${record.village || 'N/A'}</span>
                </div>
                <div class="address-item">
                    <span class="address-label">GP / Ward Name</span>
                    <span class="address-val">${record.gp || 'N/A'}</span>
                </div>
                <div class="address-item">
                    <span class="address-label">Block Name</span>
                    <span class="address-val">${record.block || 'N/A'}</span>
                </div>
                <div class="address-item" style="grid-column: span 3; border-top: 1px dashed var(--color-border); padding-top: 8px; margin-top: 4px;">
                    <span class="address-label" style="color:var(--color-primary); font-weight:800; font-size:0.7rem;">Subcentre & Health Center Staff (Fallback Contacts)</span>
                    <div style="display:flex; flex-wrap:wrap; gap:20px; margin-top: 4px; font-size: 0.8rem;">
                        <div>Subcentre: <strong>${record.subcentre || 'Not Found'}</strong></div>
                        ${record.anm_name && record.anm_name !== 'Not Found' ? `<div>ANM: <strong>${record.anm_name}</strong> ${record.anm_phone ? `(<a href="tel:${record.anm_phone}" style="color:var(--color-primary); font-weight:700;">${record.anm_phone}</a>)` : ''}</div>` : ''}
                        ${record.cho_name && record.cho_name !== 'Not Found' ? `<div>CHO: <strong>${record.cho_name}</strong> ${record.cho_phone ? `(<a href="tel:${record.cho_phone}" style="color:var(--color-primary); font-weight:700;">${record.cho_phone}</a>)` : ''}</div>` : ''}
                    </div>
                </div>
            </div>
        `;

        let clinicalBlock = '';
        if (record.bp_admission) {
            clinicalBlock = `
            <div style="background-color: var(--color-bg); border: 1px solid var(--color-border); padding: 12px 16px; border-radius: var(--radius-sm); margin-bottom: 8px;">
                <div style="font-weight:700; font-size:0.85rem; color:var(--color-primary); display:flex; align-items:center; gap:6px; margin-bottom: 8px; text-transform:uppercase;">
                    Clinical Admission & Delivery Summary
                </div>
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap: 12px 20px; font-size: 0.8rem;">
                    <div>BP at Admission: <strong>${record.bp_admission}</strong></div>
                    <div>BP at Discharge: <strong>${record.bp_discharge}</strong></div>
                    <div>Type of Delivery: <strong>${record.delivery_type}</strong></div>
                    <div>Complications at Admission: <strong style="${record.complication_admission !== 'None' && record.complication_admission !== 'No' ? 'color:#b91c1c' : ''}">${record.complication_admission}</strong></div>
                    <div>Complications at Delivery: <strong style="${record.complication_delivery !== 'None' && record.complication_delivery !== 'No' ? 'color:#b91c1c' : ''}">${record.complication_delivery}</strong></div>
                    <div>Maternal Death: <strong style="${record.maternal_death !== 'No' ? 'color:#b91c1c; font-weight:800;' : ''}">${record.maternal_death}</strong></div>
                    <div>Date of Discharge: <strong>${formatDateStr(record.discharge_date)}</strong></div>
                    ${record.delivery_district !== 'West Nimar (Khargone)' ? `<div>Delivery Place Block/District: <strong>${record.delivery_block} / ${record.delivery_district}</strong></div>` : ''}
                    ${record.facility_name ? `<div>Facility Name: <strong>${record.facility_name}</strong></div>` : ''}
                </div>
            </div>
            `;
        }

        const detailRow = document.createElement('tr');
        detailRow.className = 'table-detail-row';
        detailRow.innerHTML = `
            <td colspan="${colspanVal}">
                <div class="desktop-detail-container" onclick="event.stopPropagation()">
                    ${matchDetailsBlock}
                    ${addressBlock}
                    ${clinicalBlock}
                </div>
            </td>
        `;
        rowEl.parentNode.insertBefore(detailRow, rowEl.nextSibling);
        return;
    }

    // -------------------------------------------------------------
    // CASE C: REDCAP RECORDS (OVERALL & PENDING LISTS)
    // -------------------------------------------------------------
    // Discrepancies Alert block
    let discBox = '';
    if (record.has_disc || (record.disc_reasons && record.disc_reasons.length > 0)) {
        discBox = `
            <div style="background-color: var(--color-danger-light); border: 1px solid var(--color-danger-border); padding: 12px; border-radius: var(--radius-sm); margin-bottom: 12px; color: #991b1b;">
                <div style="font-weight:700; font-size:0.85rem; display:flex; align-items:center; gap:6px;">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" style="width:14px; height:14px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                    </svg>
                    Data Validation Errors (${record.disc_reasons.length})
                </div>
                <ul style="margin-left: 20px; font-size: 0.8rem; margin-top: 4px; padding-left:12px;">
                    ${record.disc_reasons.map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Babies layout
    let babiesHtml = '';
    if (record.babies && record.babies.length > 0) {
        record.babies.forEach((baby, idx) => {
            const statusBadge = `<span class="baby-status-badge ${getBabyBadgeClass(baby.status)}" style="font-size:0.6rem">${baby.status}</span>`;
            const stats = `
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.75rem; margin-bottom:6px;">
                    <div>Sex: <strong>${baby.sex}</strong></div>
                    <div>Weight: <strong>${baby.weight ? baby.weight+'g' : 'N/A'}</strong></div>
                    ${baby.is_stillbirth ? `
                        <div style="grid-column: span 2;">Delivery Location: <strong>${record.deliv_loc || 'Not Recorded'}</strong></div>
                        <div style="grid-column: span 2;">Delivery Place Name: <strong>${record.deliv_place || 'Not Recorded'}</strong></div>
                    ` : `
                        ${baby.age_at_death !== null ? `<div>Age at Death: <strong style="color:var(--color-danger)">${baby.age_at_death} days</strong></div>` : ''}
                        ${baby.place_of_death ? `<div>Place of Death: <strong>${baby.place_of_death}</strong></div>` : ''}
                    `}
                </div>
            `;
            babiesHtml += `
                <div style="background:#fff; border:1px solid var(--color-border); border-radius:6px; padding:12px; flex:1; min-width:240px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-weight:700; font-size:0.8rem;">
                        <span>Baby ${idx+1}: ${baby.baby_id}</span>
                        ${statusBadge}
                    </div>
                    ${stats}
                    <div style="font-size:0.7rem; font-weight:700; color:var(--color-text-muted); margin-bottom:4px; border-top:1px dashed var(--color-border); padding-top:4px;">CALL TIMELINE</div>
                    ${renderCallTimelineHtml(baby)}
                </div>
            `;
        });
    }

    // Address block details
    const addressBlock = `
        <div class="mother-address-block" style="margin-bottom:12px; grid-template-columns: repeat(3, 1fr); gap: 12px 20px;">
            <div class="address-item">
                <span class="address-label">Village / GP Name</span>
                <span class="address-val">${record.village || 'N/A'} (${record.gp || 'N/A'})</span>
            </div>
            <div class="address-item">
                <span class="address-label">ASHA Mobile</span>
                <span class="address-val">${record.asha_mobile || 'Not Recorded'}</span>
            </div>
            <div class="address-item">
                <span class="address-label">Block / Taluk</span>
                <span class="address-val">${record.block || 'N/A'}</span>
            </div>
            <div class="address-item">
                <span class="address-label">Delivery Location</span>
                <span class="address-val">${record.deliv_loc || 'Not Recorded'}</span>
            </div>
            <div class="address-item" style="grid-column: span 2;">
                <span class="address-label">Delivery Place Name</span>
                <span class="address-val">${record.deliv_place || 'Not Recorded'}</span>
            </div>
            <div class="address-item" style="grid-column: span 3; border-top: 1px dashed var(--color-border); padding-top: 8px; margin-top: 4px;">
                <span class="address-label" style="color:var(--color-primary); font-weight:800; font-size:0.7rem;">Subcentre & Health Center Staff (Fallback Contacts)</span>
                <div style="display:flex; flex-wrap:wrap; gap:20px; margin-top: 4px; font-size: 0.8rem;">
                    <div>Subcentre: <strong>${record.subcentre || 'Not Found'}</strong></div>
                    ${record.anm_name && record.anm_name !== 'Not Found' ? `<div>ANM: <strong>${record.anm_name}</strong> ${record.anm_phone ? `(<a href="tel:${record.anm_phone}" style="color:var(--color-primary); font-weight:700;">${record.anm_phone}</a>)` : ''}</div>` : ''}
                    ${record.cho_name && record.cho_name !== 'Not Found' ? `<div>CHO: <strong>${record.cho_name}</strong> ${record.cho_phone ? `(<a href="tel:${record.cho_phone}" style="color:var(--color-primary); font-weight:700;">${record.cho_phone}</a>)` : ''}</div>` : ''}
                </div>
            </div>
        </div>
    `;

    const detailRow = document.createElement('tr');
    detailRow.className = 'table-detail-row';
    detailRow.innerHTML = `
        <td colspan="${colspanVal}">
            <div class="desktop-detail-container" onclick="event.stopPropagation()">
                ${discBox}
                ${addressBlock}
                ${babiesHtml ? `
                    <div style="font-size:0.8rem; font-weight:700; text-transform:uppercase; color:var(--color-text-muted); margin-bottom:8px;">Baby Tracking & Call Logs</div>
                    <div style="display:flex; flex-wrap:wrap; gap:12px;">
                        ${babiesHtml}
                    </div>
                ` : ''}
            </div>
        </td>
    `;
    rowEl.parentNode.insertBefore(detailRow, rowEl.nextSibling);
}

// Expandable card drawer in Mobile card views
function toggleCardExpansion(summaryEl) {
    const cardEl = summaryEl.parentElement;
    cardEl.classList.toggle('expanded');
}

// ================= RENDER 1: OVERALL LINE LIST =================
function renderOverallList() {
    const tableBody = document.getElementById('overall-table-body');
    const cardsContainer = document.getElementById('overall-cards-container');
    const loadMoreBtn = document.getElementById('load-more-overall');
    
    // Filter
    let filtered = dbData.overall_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        // Delivery location filter
        if (activeDelivLocFilter !== 'ALL' && item.place_cat !== activeDelivLocFilter) return false;
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.deliv_date.substring(0, 7))) return false;
        
        // Categorized validation filter checks - Notification & Registration (Form 1)
    if (activeDiscrepancyFilterNotifReg !== 'ALL') {
        const notifList = item.disc_notif_reg || [];
        if (activeDiscrepancyFilterNotifReg === 'ANY' && notifList.length === 0) return false;
        if (activeDiscrepancyFilterNotifReg === 'NONE' && notifList.length > 0) return false;
        if (activeDiscrepancyFilterNotifReg !== 'ANY' && activeDiscrepancyFilterNotifReg !== 'NONE') {
            if (!notifList.some(r => r.startsWith(activeDiscrepancyFilterNotifReg))) return false;
        }
    }

    // Categorized validation filter checks - Day 29 Follow-up (Form 2)
    if (activeDiscrepancyFilterDay29 !== 'ALL') {
        const day29List = item.disc_day29 || [];
        if (activeDiscrepancyFilterDay29 === 'ANY' && day29List.length === 0) return false;
        if (activeDiscrepancyFilterDay29 === 'NONE' && day29List.length > 0) return false;
        if (activeDiscrepancyFilterDay29 !== 'ANY' && activeDiscrepancyFilterDay29 !== 'NONE') {
            if (!day29List.some(r => r.startsWith(activeDiscrepancyFilterDay29))) return false;
        }
    }

    if (searchOverall) {
            const matchName = item.name.toLowerCase().includes(searchOverall);
            const matchId = item.id.toLowerCase().includes(searchOverall);
            const matchPhone = item.phone1.includes(searchOverall) || (item.phone2 && item.phone2.includes(searchOverall));
            if (!matchName && !matchId && !matchPhone) return false;
        }
        return true;
    });

    // Sort Data
    filtered = sortDataList(filtered, sortFieldOverall, sortOrderOverall);
    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['overall'] = filtered;

    document.getElementById('overall-count-badge').textContent = `${filtered.length.toLocaleString()} record${filtered.length === 1 ? '' : 's'}`;

    if (filtered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="no-records-msg">No records match the active criteria.</td></tr>';
        cardsContainer.innerHTML = '<div class="no-records-msg">No records match the active criteria.</div>';
        loadMoreBtn.style.display = 'none';
        return;
    }

    const sliced = filtered.slice(0, visibleOverall);
    
    // Desktop Table rendering
    let tableHtml = '';
    sliced.forEach(item => {
        const trClass = item.has_disc ? 'row-discrepancy mother-row-expandable' : 'mother-row-expandable';
        const discBadge = item.has_disc ? `<span class="discrepancy-reason-badge" style="cursor:pointer">Issue (${item.disc_reasons.length})</span>` : '<span style="color:var(--color-text-muted)">Normal</span>';
        
        let b1 = 'None', b2 = 'None', b3 = 'None';
        if (item.babies.length > 0) {
            const b = item.babies[0];
            b1 = `<span class="baby-status-badge ${getBabyBadgeClass(b.status)}">${b.status}</span><br><small style="color:var(--color-text-muted)">${b.baby_id}</small>`;
        }
        if (item.babies.length > 1) {
            const b = item.babies[1];
            b2 = `<span class="baby-status-badge ${getBabyBadgeClass(b.status)}">${b.status}</span><br><small style="color:var(--color-text-muted)">${b.baby_id}</small>`;
        }
        if (item.babies.length > 2) {
            const b = item.babies[2];
            b3 = `<span class="baby-status-badge ${getBabyBadgeClass(b.status)}">${b.status}</span><br><small style="color:var(--color-text-muted)">${b.baby_id}</small>`;
        }

        tableHtml += `
            <tr class="${trClass}" onclick="toggleDesktopRow(this, '${item.id}', 'overall')">
                <td style="font-weight:700">${item.id}</td>
                <td>${item.block}</td>
                <td><strong>${item.name}</strong><br><small style="color:var(--color-text-muted)">Coord: ${item.coord.replace(/_/g, ' ')}</small></td>
                <td>${formatDateStr(item.deliv_date)}</td>
                <td>${item.deliv_loc || "N/A"}</td>
                <td>${item.deliv_place || "N/A"}</td>
                <td>${item.phone1 || "N/A"}</td>
                <td>${b1}</td>
                <td>${b2}</td>
                <td>${b3}</td>
                <td><strong>${discBadge}</strong></td>
            </tr>
        `;
    });
    tableBody.innerHTML = tableHtml;

    // Mobile Cards Rendering
    let cardsHtml = '';
    sliced.forEach(item => {
        const cardClass = item.has_disc ? 'discrepancy' : '';
        
        let discBox = '';
        if (item.has_disc) {
            discBox = `
                <div class="discrepancy-card-alert">
                    <div class="discrepancy-alert-title">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" style="width:14px; height:14px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                        </svg>
                        Data Inconsistency Details
                    </div>
                    <ul class="discrepancy-alert-list">
                        ${item.disc_reasons.map(r => `<li>${r}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        let babiesStatusGrid = '';
        item.babies.forEach((b, idx) => {
            const s = b.call_statuses[2];
            let timeline = `
                <div class="call-step" style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                    <span class="call-label" style="font-weight:700;">Final Status</span>
                    <span class="call-status-val ${s ? s.toLowerCase() : 'empty'}">${s || 'Pending'}</span>
                </div>
            `;
            babiesStatusGrid += `
                <div class="baby-detail-card">
                    <div class="baby-header">
                        <span class="baby-id">${b.baby_id}</span>
                        <span class="baby-status-badge ${getBabyBadgeClass(b.status)}">${b.status}</span>
                    </div>
                    <div class="baby-stats-grid">
                        <div>Sex: <strong>${b.sex}</strong></div>
                        <div>Weight: <strong>${b.weight ? b.weight+'g' : 'N/A'}</strong></div>
                        ${b.age_at_death !== null ? `<div>Age at Death: <strong style="color:var(--color-danger)">${b.age_at_death} days</strong></div>` : ''}
                    </div>
                    <div class="call-history-wrap">
                        <div class="calls-timeline">${timeline}</div>
                    </div>
                </div>
            `;
        });

        cardsHtml += `
            <div class="mother-card ${cardClass}" data-id="${item.id}">
                <div class="mother-card-summary" onclick="toggleCardExpansion(this)">
                    <div class="mother-card-header">
                        <div>
                            <span class="mother-name">${item.name}</span>
                            <span class="record-id-tag">ID: ${item.id}</span>
                        </div>
                        <span class="delivery-date-badge">${formatDateStr(item.deliv_date)}</span>
                    </div>
                    
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; font-size:0.8rem; margin:8px 0 0 0;">
                        <div><span style="color:var(--color-text-muted)">Block:</span> <strong>${item.block}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Coordinator:</span> <strong>${item.coord.replace(/_/g, ' ')}</strong></div>
                    </div>

                    <div class="expand-indicator-row">
                        <svg class="expand-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                        </svg>
                    </div>
                </div>
                <div class="mother-card-details">
                    ${discBox}
                    <div class="babies-detail-title">Baby Registry Details</div>
                    <div class="babies-list">
                        ${babiesStatusGrid}
                    </div>
                </div>
            </div>
        `;
    });
    cardsContainer.innerHTML = cardsHtml;

    if (filtered.length > visibleOverall) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }
}

// ================= RENDER 2: PENDING FOLLOW UP LINE LIST =================
// Helper to calculate baby's age in days
function getBabyAgeInDays(deliveryDateStr) {
    if (!deliveryDateStr) return 0;
    const delDate = new Date(deliveryDateStr);
    const today = new Date();
    delDate.setHours(0, 0, 0, 0);
    today.setHours(0, 0, 0, 0);
    const diffTime = today - delDate;
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}


// Render Lost to Follow-up cases list
function renderLostFollowupList() {
    const tableBody = document.getElementById('lost-followup-table-body');
    const cardsContainer = document.getElementById('lost-followup-cards-container');
    const loadMoreBtn = document.getElementById('load-more-lost-followup');
    if (!tableBody) return;

    const list = dbData.lost_to_followup_list || [];

    let filtered = list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;

        // Filter by Lost Reason Category
        if (activeLostCategory !== 'ALL') {
            const hasCat = (item.babies || []).some(b => b.lost_category === activeLostCategory);
            if (!hasCat) return false;
        }

        if (searchLostFollowup) {
            const matchName = (item.name || '').toLowerCase().includes(searchLostFollowup);
            const matchId = (item.id || '').toLowerCase().includes(searchLostFollowup);
            const matchPhone = (item.phone1 || '').includes(searchLostFollowup) || (item.phone2 && item.phone2.includes(searchLostFollowup));
            const matchVillage = (item.village || '').toLowerCase().includes(searchLostFollowup);
            const matchReason = (item.babies || []).some(b => (b.lost_category || '').toLowerCase().includes(searchLostFollowup) || (b.lost_remark || '').toLowerCase().includes(searchLostFollowup));
            if (!matchName && !matchId && !matchPhone && !matchVillage && !matchReason) return false;
        }
        return true;
    });

    filtered = sortDataList(filtered, sortFieldLostFollowup, sortOrderLostFollowup);
    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['lost-followup'] = filtered;

    const countBadge = document.getElementById('lost-followup-count-badge');
    if (countBadge) {
        countBadge.textContent = `${filtered.length.toLocaleString()} cases`;
    }

    if (filtered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="no-records-msg">No lost to follow-up cases found matching filters.</td></tr>';
        if (cardsContainer) cardsContainer.innerHTML = '<div class="no-records-msg">No lost to follow-up cases.</div>';
        if (loadMoreBtn) loadMoreBtn.style.display = 'none';
        return;
    }

    const sliced = filtered.slice(0, visibleLostFollowup);

    let tableHtml = '';
    sliced.forEach(item => {
        let contactsHtml = '';
        if (item.subcentre && item.subcentre !== 'Not Found' && item.subcentre !== 'Blank') {
            contactsHtml += `<div style="font-size:0.7rem; color:#475569; margin-bottom:2px; font-weight:600;">📍 ${item.subcentre}</div>`;
        }
        if (item.anm_name && item.anm_name !== 'Not Found') {
            if (item.anm_phone) {
                contactsHtml += `<a href="tel:${item.anm_phone}" class="anm-pill" title="Call ANM: ${item.anm_name}">ANM: ${item.anm_name} (${item.anm_phone})</a><br>`;
            } else {
                contactsHtml += `<span class="anm-pill" style="background:#f1f5f9; color:#64748b; border-color:#cbd5e1;">ANM: ${item.anm_name}</span><br>`;
            }
        }
        if (item.cho_name && item.cho_name !== 'Not Found') {
            if (item.cho_phone) {
                contactsHtml += `<a href="tel:${item.cho_phone}" class="cho-pill" title="Call CHO: ${item.cho_name}">CHO: ${item.cho_name} (${item.cho_phone})</a><br>`;
            } else {
                contactsHtml += `<span class="cho-pill" style="background:#f1f5f9; color:#64748b; border-color:#cbd5e1;">CHO: ${item.cho_name}</span><br>`;
            }
        }
        if (!contactsHtml) contactsHtml = '<span style="color:var(--color-text-muted); font-size:0.75rem;">Not Available</span>';

        let phoneHtml = `<div style="font-weight:600; color:var(--color-primary);">${item.phone1 || 'No Phone'}</div>`;
        if (item.phone2) {
            phoneHtml += `<div style="font-size:0.75rem; color:var(--color-text-muted);">Alt: ${item.phone2}</div>`;
        }

        let babiesHtml = '';
        (item.babies || []).forEach(baby => {
            const cat = baby.lost_category || 'Other Reason';
            const remark = baby.lost_remark || '';
            babiesHtml += `
                <div style="border:1px solid #fed7aa; padding:6px; border-radius:4px; margin-bottom:6px; background:#fffaf0;">
                    <strong>${baby.baby_id}</strong> (${baby.sex || 'N/A'}${baby.weight ? ', ' + baby.weight + 'g' : ''})
                    <div style="margin-top:3px;">
                        <span class="badge" style="background:#fef3c7; color:#92400e; font-weight:700; font-size:0.7rem; padding:2px 6px; border-radius:4px; border:1px solid #fde68a;">
                            ${cat}
                        </span>
                    </div>
                    ${remark ? `<div style="font-size:0.7rem; color:#78350f; margin-top:3px; font-style:italic;">"${remark}"</div>` : ''}
                </div>
            `;
        });

        tableHtml += `
            <tr class="mother-row-expandable" onclick="toggleDesktopRow(this, '${item.id}', 'lost-followup')">
                <td style="font-weight:700">${item.id}</td>
                <td>${item.block}</td>
                <td><strong>${item.name}</strong></td>
                <td>${formatDateStr(item.delivery_date)}<br><small style="color:var(--color-text-muted)">Age: ${getBabyAgeInDays(item.delivery_date)} days</small></td>
                <td>${item.followup_coord || item.coord || "N/A"}</td>
                <td><strong>${item.village}</strong><br><small style="color:var(--color-text-muted)">GP: ${item.gp || 'N/A'}</small></td>
                <td>${contactsHtml}</td>
                <td>${phoneHtml}</td>
                <td>${babiesHtml}</td>
            </tr>
        `;
    });
    tableBody.innerHTML = tableHtml;

    if (cardsContainer) {
        let cardsHtml = '';
        sliced.forEach(item => {
            let babiesCardHtml = '';
            (item.babies || []).forEach(baby => {
                babiesCardHtml += `
                    <div style="margin-top:6px; padding:6px; background:#fffaf0; border-radius:4px; border:1px solid #fed7aa;">
                        <strong>${baby.baby_id}</strong>: <span style="font-weight:700; color:#92400e;">${baby.lost_category || 'Lost'}</span>
                        ${baby.lost_remark ? `<br><small style="color:#78350f;">"${baby.lost_remark}"</small>` : ''}
                    </div>
                `;
            });
            cardsHtml += `
                <div class="mobile-record-card">
                    <div class="card-header">
                        <span class="card-id">#${item.id}</span>
                        <span class="badge" style="background:#fef3c7; color:#92400e;">Lost to Follow-up</span>
                    </div>
                    <div class="card-body">
                        <div><strong>Mother:</strong> ${item.name}</div>
                        <div><strong>Block:</strong> ${item.block} | <strong>Village:</strong> ${item.village}</div>
                        <div><strong>Delivery:</strong> ${formatDateStr(item.delivery_date)} (${getBabyAgeInDays(item.delivery_date)} days)</div>
                        <div><strong>Phone:</strong> ${item.phone1 || 'N/A'}</div>
                        ${babiesCardHtml}
                    </div>
                </div>
            `;
        });
        cardsContainer.innerHTML = cardsHtml;
    }

    if (loadMoreBtn) {
        loadMoreBtn.style.display = visibleLostFollowup < filtered.length ? 'block' : 'none';
    }
}

function renderPendingList() {
    const tableBody = document.getElementById('pending-table-body');
    const cardsContainer = document.getElementById('pending-cards-container');
    const loadMoreBtn = document.getElementById('load-more-pending');

    let filtered = dbData.pending_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        
        // Pending timeline policy: exclude infants under 29 days of age
        const ageInDays = getBabyAgeInDays(item.delivery_date);
        if (ageInDays < 29) return false;

        // Pending Type Filter (29th Day vs Overdue)
        if (activePendingType !== 'ALL') {
            if (activePendingType === 'D29' && ageInDays !== 29) return false;
            if (activePendingType === 'OVERDUE' && ageInDays < 30) return false;
        }

        if (searchPending) {
            const matchName = item.name.toLowerCase().includes(searchPending);
            const matchId = item.id.toLowerCase().includes(searchPending);
            const matchPhone = item.phone1.includes(searchPending) || (item.phone2 && item.phone2.includes(searchPending));
            const matchVillage = item.village.toLowerCase().includes(searchPending);
            if (!matchName && !matchId && !matchPhone && !matchVillage) return false;
        }
        return true;
    });

    filtered = sortDataList(filtered, sortFieldPending, sortOrderPending);
    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['pending'] = filtered;

    document.getElementById('pending-count-badge').textContent = `${filtered.length.toLocaleString()} pending`;

    if (filtered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="no-records-msg">No pending follow-ups.</td></tr>';
        cardsContainer.innerHTML = '<div class="no-records-msg">No pending cases.</div>';
        loadMoreBtn.style.display = 'none';
        return;
    }

    const sliced = filtered.slice(0, visiblePending);

    // Desktop Table Rendering
    let tableHtml = '';
    sliced.forEach(item => {
        let callActionsHtml = `<a href="tel:${item.phone1}" class="phone-link-btn" style="height:32px; padding:0 8px; font-size:0.75rem; margin-bottom:4px; display:inline-flex;">Primary: ${item.phone1}</a><br>`;
        if (item.phone2) {
            callActionsHtml += `<a href="tel:${item.phone2}" class="phone-link-btn secondary" style="height:32px; padding:0 8px; font-size:0.75rem; margin-bottom:4px; display:inline-flex;">Alt: ${item.phone2}</a><br>`;
        }
        
        let contactsHtml = '';
        if (item.asha_mobile && item.asha_mobile !== 'Not Recorded' && item.asha_mobile !== 'Not Available-Not Available') {
            const phoneMatch = item.asha_mobile.match(/\d+$/);
            if (phoneMatch) {
                contactsHtml += `<a href="tel:${phoneMatch[0]}" class="asha-pill" title="Call ASHA Coordinator">ASHA: ${item.asha_mobile}</a><br>`;
            } else {
                contactsHtml += `<span class="asha-pill" style="background:#f1f5f9; color:#64748b; border-color:#cbd5e1;">ASHA: ${item.asha_mobile}</span><br>`;
            }
        } else {
            contactsHtml += '<span class="asha-pill" style="background:#fef2f2; color:#ef4444; border-color:#fee2e2;">No ASHA contact</span><br>';
        }

        if (item.subcentre && item.subcentre !== 'Not Found' && item.subcentre !== 'Blank') {
            contactsHtml += `<div style="font-size:0.7rem; color:#475569; margin:4px 0 2px 0; font-weight:600;">📍 ${item.subcentre}</div>`;
        }
        if (item.anm_name && item.anm_name !== 'Not Found') {
            if (item.anm_phone) {
                contactsHtml += `<a href="tel:${item.anm_phone}" class="anm-pill" title="Call ANM: ${item.anm_name}">ANM: ${item.anm_name} (${item.anm_phone})</a><br>`;
            } else {
                contactsHtml += `<span class="anm-pill" style="background:#f1f5f9; color:#64748b; border-color:#cbd5e1;">ANM: ${item.anm_name}</span><br>`;
            }
        }
        if (item.cho_name && item.cho_name !== 'Not Found') {
            if (item.cho_phone) {
                contactsHtml += `<a href="tel:${item.cho_phone}" class="cho-pill" title="Call CHO: ${item.cho_name}">CHO: ${item.cho_name} (${item.cho_phone})</a><br>`;
            } else {
                contactsHtml += `<span class="cho-pill" style="background:#f1f5f9; color:#64748b; border-color:#cbd5e1;">CHO: ${item.cho_name}</span><br>`;
            }
        }

        let babiesHtml = '';
        item.babies.forEach(baby => {
            babiesHtml += `
                <div style="border:1px solid var(--color-border); padding:6px; border-radius:4px; margin-bottom:6px; background:#fff;">
                    <strong>${baby.baby_id}</strong> (${baby.sex}) - ${baby.weight ? baby.weight + 'g' : 'no weight'}
                    <div style="font-size:0.75rem; color:var(--color-text-muted); margin-top:2px;">
                        Final Status: <strong class="baby-status-badge ${getBabyBadgeClass(baby.call_statuses[2] || 'Pending')}" style="padding:1px 6px; font-size:0.65rem;">${baby.call_statuses[2] || 'Pending'}</strong>
                    </div>
                </div>
            `;
        });

        tableHtml += `
            <tr class="mother-row-expandable" onclick="toggleDesktopRow(this, '${item.id}', 'pending')">
                <td style="font-weight:700">${item.id}</td>
                <td>${item.block}</td>
                <td><strong>${item.name}</strong></td>
                <td>${formatDateStr(item.delivery_date)}<br><small style="color:var(--color-text-muted)">Age: ${getBabyAgeInDays(item.delivery_date)} days</small></td>
                <td>${item.coord || "N/A"}</td>
                <td><strong>${item.village}</strong><br><small style="color:var(--color-text-muted)">GP: ${item.gp}</small></td>
                <td>${contactsHtml}</td>
                <td onclick="event.stopPropagation()">${callActionsHtml}</td>
                <td>${babiesHtml}</td>
            </tr>
        `;
    });
    tableBody.innerHTML = tableHtml;

    // Mobile Cards Rendering
    let cardsHtml = '';
    sliced.forEach(item => {
        let phoneButtons = '';
        if (item.phone1) {
            phoneButtons += `<a href="tel:${item.phone1}" class="phone-link-btn" onclick="event.stopPropagation();">Call Primary</a>`;
        }
        if (item.phone2) {
            phoneButtons += `<a href="tel:${item.phone2}" class="phone-link-btn secondary" onclick="event.stopPropagation();">Call Alt</a>`;
        }
        if (item.anm_phone) {
            phoneButtons += `<a href="tel:${item.anm_phone}" class="phone-link-btn anm" onclick="event.stopPropagation();">Call ANM</a>`;
        }
        if (item.cho_phone) {
            phoneButtons += `<a href="tel:${item.cho_phone}" class="phone-link-btn cho" onclick="event.stopPropagation();">Call CHO</a>`;
        }

        let ashaAction = '';
        if (item.asha_mobile && item.asha_mobile !== 'Not Recorded' && item.asha_mobile !== 'Not Available-Not Available') {
            const phoneMatch = item.asha_mobile.match(/\d+$/);
            if (phoneMatch) {
                ashaAction = `<a href="tel:${phoneMatch[0]}" class="asha-pill" onclick="event.stopPropagation();">Call ASHA: ${item.asha_mobile.split('-')[0]}</a>`;
            } else {
                ashaAction = `<span class="asha-pill" style="background:#f1f5f9; color:#64748b;">ASHA: ${item.asha_mobile}</span>`;
            }
        } else {
            ashaAction = '<span class="asha-pill" style="background:#fef2f2; color:#ef4444;">No ASHA assigned</span>';
        }

        let babiesDetail = '';
        item.babies.forEach(baby => {
            const s = baby.call_statuses[2];
            let timeline = `
                <div class="call-step" style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                    <span class="call-label" style="font-weight:700;">Final Status</span>
                    <span class="call-status-val ${s ? s.toLowerCase() : 'empty'}">${s || 'Pending'}</span>
                </div>
            `;
            babiesDetail += `
                <div class="baby-detail-card">
                    <div class="baby-header">
                        <span class="baby-id">${baby.baby_id}</span>
                        <span class="baby-status-badge pending">Pending</span>
                    </div>
                    <div class="baby-stats-grid">
                        <div>Sex: <strong>${baby.sex}</strong></div>
                        <div>Weight: <strong>${baby.weight ? baby.weight+'g' : 'N/A'}</strong></div>
                    </div>
                    <div class="call-history-wrap">
                        <div class="call-history-title">Call Attempts Timeline</div>
                        <div class="calls-timeline">${timeline}</div>
                    </div>
                </div>
            `;
        });

        cardsHtml += `
            <div class="mother-card" data-id="${item.id}">
                <div class="mother-card-summary" onclick="toggleCardExpansion(this)">
                    <div class="mother-card-header">
                        <div>
                            <span class="mother-name">${item.name}</span>
                            <span class="record-id-tag">ID: ${item.id}</span>
                        </div>
                        <span class="delivery-date-badge">${formatDateStr(item.delivery_date)}</span>
                    </div>

                    <div class="mother-address-block">
                        <div class="address-item">
                            <span class="address-label">Village / GP</span>
                            <span class="address-val">${item.village} (${item.gp})</span>
                        </div>
                        <div class="address-item">
                            <span class="address-label">ASHA Details</span>
                            ${ashaAction}
                        </div>
                    </div>

                    <div class="mother-address-block" style="grid-template-columns: 1fr; margin-top: 8px;">
                        <div class="address-item">
                            <span class="address-label">Sub-Health Centre Contact</span>
                            <span class="address-val" style="font-size: 0.75rem; line-height: 1.4;">
                                📍 <strong>${item.subcentre}</strong><br>
                                ${item.anm_name !== 'Not Found' ? `👩‍⚕️ ANM: <strong>${item.anm_name}</strong> ${item.anm_phone ? '('+item.anm_phone+')' : ''}<br>` : ''}
                                ${item.cho_name !== 'Not Found' ? `🩺 CHO: <strong>${item.cho_name}</strong> ${item.cho_phone ? '('+item.cho_phone+')' : ''}` : ''}
                            </span>
                        </div>
                    </div>

                    <div class="phone-links-wrap" onclick="event.stopPropagation();" style="margin-top: 10px;">
                        ${phoneButtons}
                    </div>

                    <div class="expand-indicator-row">
                        <svg class="expand-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                        </svg>
                    </div>
                </div>
                <div class="mother-card-details">
                    <div class="babies-detail-title">Baby Follow-up Details</div>
                    <div class="babies-list">
                        ${babiesDetail}
                    </div>
                </div>
            </div>
        `;
    });
    cardsContainer.innerHTML = cardsHtml;

    if (filtered.length > visiblePending) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }
}

// ================= RENDER 3: NEONATAL DEATHS LINE LIST =================
function renderDeathsList() {
    const tableBody = document.getElementById('deaths-table-body');
    const cardsContainer = document.getElementById('deaths-cards-container');
    const loadMoreBtn = document.getElementById('load-more-deaths');

    let filtered = dbData.neonatal_deaths_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        
        // Neonatal Deaths sub-filters
        if (activeDeathBaby !== 'ALL' && item.baby_num !== activeDeathBaby) return false;
        if (activeDeathPlace !== 'ALL' && item.place_of_death !== activeDeathPlace) return false;
        if (activeDeathDelivPlace !== 'ALL' && item.deliv_place !== activeDeathDelivPlace) return false;

        if (searchDeaths) {
            const matchName = item.name.toLowerCase().includes(searchDeaths);
            const matchId = item.id.toLowerCase().includes(searchDeaths);
            const matchBaby = item.baby_num.toLowerCase().includes(searchDeaths);
            if (!matchName && !matchId && !matchBaby) return false;
        }
        return true;
    });

    filtered = sortDataList(filtered, sortFieldDeaths, sortOrderDeaths);
    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['deaths'] = filtered;

    document.getElementById('deaths-count-badge').textContent = `${filtered.length.toLocaleString()} death${filtered.length === 1 ? '' : 's'}`;

    if (filtered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="10" class="no-records-msg">No neonatal deaths recorded.</td></tr>';
        cardsContainer.innerHTML = '<div class="no-records-msg">No neonatal deaths recorded.</div>';
        loadMoreBtn.style.display = 'none';
        return;
    }

    const sliced = filtered.slice(0, visibleDeaths);

    // Desktop Table Rendering
    let tableHtml = '';
    sliced.forEach(item => {
        tableHtml += `
            <tr>
                <td style="font-weight:700">${item.id}</td>
                <td>${item.block}</td>
                <td><strong>${item.name}</strong></td>
                <td style="color:var(--color-danger); font-weight:700">${item.baby_num}</td>
                <td>${item.sex}</td>
                <td>${item.weight ? item.weight+'g' : 'N/A'}</td>
                <td>${formatDateStr(item.delivery_date)}</td>
                <td>${formatDateStr(item.death_date)}</td>
                <td><strong style="color:var(--color-danger)">${item.age_at_death !== null ? item.age_at_death + ' days' : 'ASHA report'}</strong></td>
                <td>${item.place_of_death}</td>
                <td>${item.phone1 || "N/A"}</td>
            </tr>
        `;
    });
    tableBody.innerHTML = tableHtml;

    // Mobile Cards Rendering
    let cardsHtml = '';
    sliced.forEach(item => {
        cardsHtml += `
            <div class="mother-card" style="border-left: 4px solid var(--color-danger)">
                <div style="padding:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                        <div>
                            <span class="mother-name">${item.name}</span>
                            <span class="record-id-tag">ID: ${item.id}</span>
                        </div>
                        <span class="delivery-date-badge" style="background-color:var(--color-danger-light); color:var(--color-danger); border-color:var(--color-danger-border)">Neonatal Death</span>
                    </div>

                    <div style="background:var(--color-bg-sunken); padding:10px; border-radius:6px; margin:10px 0;">
                        <div style="font-size:0.75rem; color:var(--color-text-muted)">BABY DETAILS</div>
                        <div style="font-weight:700; font-size:0.9rem; color:var(--color-danger); margin-bottom:4px;">${item.baby_num}</div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.8rem;">
                            <div>Sex: <strong>${item.sex}</strong></div>
                            <div>Weight: <strong>${item.weight ? item.weight+'g' : 'N/A'}</strong></div>
                            <div>Age at Death: <strong style="color:var(--color-danger)">${item.age_at_death !== null ? item.age_at_death + ' days' : 'N/A'}</strong></div>
                            <div>Place of Death: <strong>${item.place_of_death}</strong></div>
                            <div style="grid-column: span 2">Death Date: <strong>${formatDateStr(item.death_date)}</strong></div>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.8rem;">
                        <div><span style="color:var(--color-text-muted)">Delivered:</span> <strong>${formatDateStr(item.delivery_date)}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Block:</span> <strong>${item.block}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Phone:</span> <strong>${item.phone1 || "N/A"}</strong></div>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr; gap:4px; font-size:0.8rem; border-top: 1px dashed var(--color-border); padding-top: 8px; margin-top: 8px;">
                        <div><span style="color:var(--color-text-muted)">Location:</span> <strong>${item.deliv_loc || "Not Recorded"}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Place Name:</span> <strong>${item.deliv_place || "Not Recorded"}</strong></div>
                    </div>
                </div>
            </div>
        `;
    });
    cardsContainer.innerHTML = cardsHtml;

    if (filtered.length > visibleDeaths) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }
}

// ================= RENDER 4: STILLBIRTH LINE LIST =================
function renderStillbirthsList() {
    const tableBody = document.getElementById('stillbirths-table-body');
    const cardsContainer = document.getElementById('stillbirths-cards-container');
    const loadMoreBtn = document.getElementById('load-more-stillbirths');

    let filtered = dbData.stillbirths_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        
        // Stillbirth sub-filters
        if (activeStillbirthLoc !== 'ALL' && item.deliv_loc !== activeStillbirthLoc) return false;
        if (activeStillbirthPlace !== 'ALL' && item.deliv_place !== activeStillbirthPlace) return false;
        if (activeStillbirthBaby !== 'ALL' && item.baby_num !== activeStillbirthBaby) return false;

        if (searchStillbirths) {
            const matchName = item.name.toLowerCase().includes(searchStillbirths);
            const matchId = item.id.toLowerCase().includes(searchStillbirths);
            const matchBaby = item.baby_id.toLowerCase().includes(searchStillbirths) || (item.baby_num && item.baby_num.toLowerCase().includes(searchStillbirths));
            if (!matchName && !matchId && !matchBaby) return false;
        }
        return true;
    });

    filtered = sortDataList(filtered, sortFieldStillbirths, sortOrderStillbirths);
    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['stillbirths'] = filtered;

    document.getElementById('stillbirths-count-badge').textContent = `${filtered.length.toLocaleString()} stillbirth${filtered.length === 1 ? '' : 's'}`;

    if (filtered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="10" class="no-records-msg">No stillbirth records found.</td></tr>';
        cardsContainer.innerHTML = '<div class="no-records-msg">No stillbirth records found.</div>';
        loadMoreBtn.style.display = 'none';
        return;
    }

    const sliced = filtered.slice(0, visibleStillbirths);

    // Desktop Table Rendering
    let tableHtml = '';
    sliced.forEach(item => {
        tableHtml += `
            <tr>
                <td style="font-weight:700">${item.id}</td>
                <td>${item.block}</td>
                <td><strong>${item.name}</strong></td>
                <td style="color:#64748b; font-weight:700">${item.baby_num}</td>
                <td>${item.sex}</td>
                <td>${item.weight ? item.weight+'g' : 'Not Recorded'}</td>
                <td>${formatDateStr(item.delivery_date)}</td>
                <td>${item.deliv_loc || "Not Recorded"}</td>
                <td>${item.deliv_place || "Not Recorded"}</td>
                <td>${item.phone1 || "N/A"}</td>
            </tr>
        `;
    });
    tableBody.innerHTML = tableHtml;

    // Mobile Cards Rendering
    let cardsHtml = '';
    sliced.forEach(item => {
        cardsHtml += `
            <div class="mother-card" style="border-left: 4px solid #64748b">
                <div style="padding:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                        <div>
                            <span class="mother-name">${item.name}</span>
                            <span class="record-id-tag">ID: ${item.id}</span>
                        </div>
                        <span class="delivery-date-badge" style="background-color:#f1f5f9; color:#64748b; border-color:#cbd5e1">Stillbirth / IUD</span>
                    </div>

                    <div style="background:var(--color-bg-sunken); padding:10px; border-radius:6px; margin:10px 0;">
                        <div style="font-size:0.75rem; color:var(--color-text-muted)">BABY DETAILS</div>
                        <div style="font-weight:700; font-size:0.9rem; color:#64748b; margin-bottom:4px;">ID: ${item.baby_id} (${item.baby_num})</div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.8rem;">
                            <div>Sex: <strong>${item.sex}</strong></div>
                            <div>Weight: <strong>${item.weight ? item.weight+'g' : 'N/A'}</strong></div>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.8rem;">
                        <div><span style="color:var(--color-text-muted)">Delivered:</span> <strong>${formatDateStr(item.delivery_date)}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Block:</span> <strong>${item.block}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Phone:</span> <strong>${item.phone1 || "N/A"}</strong></div>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr; gap:4px; font-size:0.8rem; border-top: 1px dashed var(--color-border); padding-top: 8px; margin-top: 8px;">
                        <div><span style="color:var(--color-text-muted)">Location:</span> <strong>${item.deliv_loc || "Not Recorded"}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Place Name:</span> <strong>${item.deliv_place || "Not Recorded"}</strong></div>
                    </div>
                </div>
            </div>
        `;
    });
    cardsContainer.innerHTML = cardsHtml;

    if (filtered.length > visibleStillbirths) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }
}

// ================= RENDER 5: OUT-OF-RANGE DEATHS LINE LIST =================
function renderOutRangeDeathsList() {
    const tableBody = document.getElementById('out-range-deaths-table-body');
    const cardsContainer = document.getElementById('out-range-deaths-cards-container');
    const loadMoreBtn = document.getElementById('load-more-out-range-deaths');

    let filtered = dbData.out_of_range_deaths_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        
        if (activeDelivCoord !== 'ALL' && item.coord !== activeDelivCoord) return false;
        if (activeFollowupCoord !== 'ALL' && item.followup_coord !== activeFollowupCoord) return false;
        
        
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;

        if (searchOutRangeDeaths) {
            const matchName = item.name.toLowerCase().includes(searchOutRangeDeaths);
            const matchId = item.id.toLowerCase().includes(searchOutRangeDeaths);
            const matchBaby = item.baby_id.toLowerCase().includes(searchOutRangeDeaths) || (item.baby_num && item.baby_num.toLowerCase().includes(searchOutRangeDeaths));
            if (!matchName && !matchId && !matchBaby) return false;
        }
        return true;
    });

    filtered = sortDataList(filtered, sortFieldOutRangeDeaths, sortOrderOutRangeDeaths);
    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['out_range_deaths'] = filtered;

    document.getElementById('out-range-deaths-count-badge').textContent = `${filtered.length.toLocaleString()} out-of-range`;

    if (filtered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="12" class="no-records-msg">No out-of-range deaths recorded (All deaths are within 0-28 days!).</td></tr>';
        cardsContainer.innerHTML = '<div class="no-records-msg">No out-of-range deaths recorded.</div>';
        loadMoreBtn.style.display = 'none';
        return;
    }

    const sliced = filtered.slice(0, visibleOutRangeDeaths);

    // Desktop Table Rendering
    let tableHtml = '';
    sliced.forEach(item => {
        tableHtml += `
            <tr class="row-discrepancy">
                <td style="font-weight:700">${item.id}</td>
                <td>${item.block}</td>
                <td><strong>${item.name}</strong></td>
                <td style="color:var(--color-danger); font-weight:700">${item.baby_num}</td>
                <td>${item.sex}</td>
                <td>${item.weight ? item.weight+'g' : 'N/A'}</td>
                <td>${formatDateStr(item.delivery_date)}</td>
                <td>${formatDateStr(item.death_date)}</td>
                <td><strong style="color:var(--color-danger); font-size: 0.9rem;">${item.age_at_death} days</strong></td>
                <td>${item.deliv_place || 'Not Recorded'}</td>
                <td>${item.place_of_death || 'Not Recorded'}</td>
                <td>${item.phone1 && item.phone1 !== 'N/A' ? `<a href="tel:${item.phone1}">${item.phone1}</a>` : 'N/A'}</td>
            </tr>
        `;
    });
    tableBody.innerHTML = tableHtml;

    // Mobile Cards Rendering
    let cardsHtml = '';
    sliced.forEach(item => {
        cardsHtml += `
            <div class="mother-card discrepancy">
                <div style="padding:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                        <div>
                            <span class="mother-name">${item.name}</span>
                            <span class="record-id-tag">ID: ${item.id}</span>
                        </div>
                        <span class="delivery-date-badge" style="background-color:var(--color-danger-light); color:var(--color-danger); border-color:var(--color-danger-border)">Anomalous Death Age</span>
                    </div>

                    <div style="background:var(--color-bg-sunken); padding:10px; border-radius:6px; margin:10px 0; border: 1px solid var(--color-danger-border);">
                        <div style="font-size:0.75rem; color:var(--color-text-muted)">ANOMALOUS DATA DETAILS</div>
                        <div style="font-weight:700; font-size:0.9rem; color:var(--color-danger); margin-bottom:4px;">ID: ${item.baby_id} (${item.baby_num})</div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.8rem;">
                            <div>Sex: <strong>${item.sex}</strong></div>
                            <div>Weight: <strong>${item.weight ? item.weight+'g' : 'N/A'}</strong></div>
                            <div>Birth Date: <strong>${formatDateStr(item.delivery_date)}</strong></div>
                            <div>Death Date: <strong>${formatDateStr(item.death_date)}</strong></div>
                            <div style="grid-column: span 2; margin-top: 4px; padding-top: 4px; border-top: 1px dashed var(--color-danger-border);">
                                Calculated Age: <strong style="color:var(--color-danger); font-size: 0.95rem;">${item.age_at_death} days</strong>
                            </div>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.8rem;">
                        <div><span style="color:var(--color-text-muted)">Block:</span> <strong>${item.block}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Phone:</span> <strong>${item.phone1 || "N/A"}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Delivery Place:</span> <strong>${item.deliv_place || "Not Recorded"}</strong></div>
                        <div><span style="color:var(--color-text-muted)">Place of Death:</span> <strong>${item.place_of_death || "Not Recorded"}</strong></div>
                    </div>
                </div>
            </div>
        `;
    });
    cardsContainer.innerHTML = cardsHtml;

    if (filtered.length > visibleOutRangeDeaths) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }
}

// ================= RENDER 7: HOME DELIVERIES =================
function renderHomeDeliveriesList() {
    const tableBody = document.getElementById('home-deliveries-table-body');
    const cardsContainer = document.getElementById('home-deliveries-cards-container');
    const loadMoreBtn = document.getElementById('load-more-home-deliveries');

    if (!dbData || !dbData.home_deliveries_list) return;

    // Highlight active KPI card
    document.querySelectorAll('.home-kpi-filter-card').forEach(card => {
        const fVal = card.getAttribute('data-home-filter');
        if (fVal === activeHomeMatchStatus) {
            card.classList.add('active-kpi-card');
        } else {
            card.classList.remove('active-kpi-card');
        }
    });

    // Calculate stats dynamically based on main filters (Block, Month)
    const statsFilteredHome = dbData.home_deliveries_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        return true;
    });
    const totalCountHome = statsFilteredHome.length;
    const exactCountHome = statsFilteredHome.filter(x => x.match_status === 'exact').length;
    const spellingCountHome = statsFilteredHome.filter(x => x.match_status === 'spelling').length;
    const unmatchedCountHome = statsFilteredHome.filter(x => x.match_status === 'unmatched').length;
    
    if (document.getElementById('anmol-home-total')) document.getElementById('anmol-home-total').textContent = totalCountHome.toLocaleString();
    if (document.getElementById('anmol-home-exact')) document.getElementById('anmol-home-exact').textContent = exactCountHome.toLocaleString();
    if (document.getElementById('anmol-home-spelling')) document.getElementById('anmol-home-spelling').textContent = spellingCountHome.toLocaleString();
    if (document.getElementById('anmol-home-unmatched')) document.getElementById('anmol-home-unmatched').textContent = unmatchedCountHome.toLocaleString();

    let filtered = statsFilteredHome.filter(item => {
        if (activeHomeMatchStatus !== 'ALL' && item.match_status !== activeHomeMatchStatus) {
            return false;
        }
        if (searchHomeDeliveries) {
            const query = searchHomeDeliveries.toLowerCase();
            const matchName = item.name ? item.name.toLowerCase().includes(query) : false;
            const matchMpid = item.id ? String(item.id).toLowerCase().includes(query) : false;
            const matchBlock = item.block ? item.block.toLowerCase().includes(query) : false;
            const matchVillage = item.village ? item.village.toLowerCase().includes(query) : false;
            const matchPhone = item.phone ? item.phone.includes(query) : false;
            const matchRc = item.redcap_id ? String(item.redcap_id).toLowerCase().includes(query) : false;
            if (!matchName && !matchMpid && !matchBlock && !matchVillage && !matchPhone && !matchRc) return false;
        }
        return true;
    });

    filtered = sortDataList(filtered, sortFieldHomeDeliveries, sortOrderHomeDeliveries);
    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['home_deliveries'] = filtered;

    document.getElementById('home-deliveries-count-badge').textContent = `${filtered.length.toLocaleString()} cases`;

    if (filtered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="8" class="no-records-msg">No home delivery cases found matching the criteria.</td></tr>';
        cardsContainer.innerHTML = '<div class="no-records-msg">No home delivery cases found.</div>';
        loadMoreBtn.style.display = 'none';
        return;
    }

    const sliced = filtered.slice(0, visibleHomeDeliveries);

    // Desktop rendering
    let tableHtml = '';
    sliced.forEach(item => {
        let callActionsHtml = '';
        if (item.phone) {
            callActionsHtml = `<a href="tel:${item.phone}" class="phone-link-btn" style="height:32px; padding:0 8px; font-size:0.75rem; display:inline-flex;">Call: ${item.phone}</a>`;
        } else {
            callActionsHtml = '<span style="color:var(--color-text-muted); font-size:0.75rem;">No Phone</span>';
        }

        let contactsHtml = '';
        if (item.subcentre && item.subcentre !== 'Not Found') {
            contactsHtml += `<div style="font-size:0.7rem; color:#475569; margin-bottom:2px; font-weight:600;"> ${item.subcentre}</div>`;
        }
        if (item.anm_name && item.anm_name !== 'Not Found') {
            if (item.anm_phone) {
                contactsHtml += `<a href="tel:${item.anm_phone}" class="anm-pill" title="Call ANM: ${item.anm_name}">ANM: ${item.anm_name} (${item.anm_phone})</a><br>`;
            } else {
                contactsHtml += `<span class="anm-pill" style="background:#f1f5f9; color:#64748b; border-color:#cbd5e1;">ANM: ${item.anm_name}</span><br>`;
            }
        }
        if (item.cho_name && item.cho_name !== 'Not Found') {
            if (item.cho_phone) {
                contactsHtml += `<a href="tel:${item.cho_phone}" class="cho-pill" title="Call CHO: ${item.cho_name}">CHO: ${item.cho_name} (${item.cho_phone})</a><br>`;
            } else {
                contactsHtml += `<span class="cho-pill" style="background:#f1f5f9; color:#64748b; border-color:#cbd5e1;">CHO: ${item.cho_name}</span><br>`;
            }
        }

        let matchBadge = '';
        if (item.match_status === 'exact') {
            matchBadge = `<span class="baby-status-badge healthy" style="margin-left:8px; font-size:0.6rem;">REDCap Match (Exact: ID ${item.redcap_id})</span>`;
        } else if (item.match_status === 'spelling') {
            matchBadge = `<span class="baby-status-badge sick" style="margin-left:8px; font-size:0.6rem; background:#fffbeb; color:#b45309; border-color:#f59e0b;">Data/Spelling Mismatch (REDCap ID: ${item.redcap_id})</span>`;
        } else {
            matchBadge = `<span class="baby-status-badge" style="margin-left:8px; font-size:0.6rem; background:#fef2f2; color:#b91c1c; border-color:#fecaca;">Not Recorded in REDCap</span>`;
        }

        tableHtml += `
            <tr class="mother-row-expandable" onclick="toggleDesktopRow(this, '${item.id}', 'home-deliveries')">
                <td style="font-weight:700">${item.id}</td>
                <td>${item.block}</td>
                <td><strong>${item.name}</strong>${matchBadge}</td>
                <td><strong>${item.village}</strong><br><small style="color:var(--color-text-muted)">Subcentre: ${item.gp}</small></td>
                <td>${formatDateStr(item.delivery_date)}</td>
                <td><span style="font-size:0.8rem; font-weight:600; color:var(--color-primary);">${item.newborns}</span></td>
                <td onclick="event.stopPropagation()">${callActionsHtml}</td>
                <td>${contactsHtml}</td>
            </tr>
        `;
    });
    tableBody.innerHTML = tableHtml;

    // Mobile rendering
    let cardsHtml = '';
    sliced.forEach(item => {
        let phoneButtons = '';
        if (item.phone) {
            phoneButtons += `<a href="tel:${item.phone}" class="phone-link-btn" onclick="event.stopPropagation();">Call Beneficiary</a>`;
        }
        if (item.anm_phone) {
            phoneButtons += `<a href="tel:${item.anm_phone}" class="phone-link-btn anm" onclick="event.stopPropagation();">Call ANM</a>`;
        }
        if (item.cho_phone) {
            phoneButtons += `<a href="tel:${item.cho_phone}" class="phone-link-btn cho" onclick="event.stopPropagation();">Call CHO</a>`;
        }

        cardsHtml += `
            <div class="mother-card" data-id="${item.id}">
                <div class="mother-card-summary" onclick="toggleCardExpansion(this)">
                    <div class="mother-card-header">
                        <div>
                            <span class="mother-name">${item.name}</span>
                            <span class="record-id-tag">MPID: ${item.id}</span>
                        </div>
                        <span class="delivery-date-badge" style="background-color:#fee2e2; color:#ef4444; border-color:#fecaca;">Home Delivery</span>
                    </div>

                    <div class="mother-address-block">
                        <div class="address-item">
                            <span class="address-label">Village / Subcentre</span>
                            <span class="address-val">${item.village} (${item.gp})</span>
                        </div>
                        <div class="address-item">
                            <span class="address-label">Delivery Date</span>
                            <span class="address-val"><strong>${formatDateStr(item.delivery_date)}</strong></span>
                        </div>
                    </div>

                    <div class="mother-address-block" style="grid-template-columns: 1fr; margin-top: 8px;">
                        <div class="address-item">
                            <span class="address-label">Newborn Details</span>
                            <span class="address-val" style="font-weight:700; color:var(--color-primary);">${item.newborns}</span>
                        </div>
                    </div>

                    <div class="mother-address-block" style="grid-template-columns: 1fr; margin-top: 8px;">
                        <div class="address-item">
                            <span class="address-label">Sub-Health Centre Contact</span>
                            <span class="address-val" style="font-size: 0.75rem; line-height: 1.4;">
                                 <strong>${item.subcentre}</strong><br>
                                ${item.anm_name !== 'Not Found' ? ` ANM: <strong>${item.anm_name}</strong> ${item.anm_phone ? '('+item.anm_phone+')' : ''}<br>` : ''}
                                ${item.cho_name !== 'Not Found' ? ` CHO: <strong>${item.cho_name}</strong> ${item.cho_phone ? '('+item.cho_phone+')' : ''}` : ''}
                            </span>
                        </div>
                    </div>

                    <div class="phone-links-wrap" onclick="event.stopPropagation();" style="margin-top: 10px;">
                        ${phoneButtons}
                    </div>

                    <div class="expand-indicator-row">
                        <svg class="expand-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                        </svg>
                    </div>
                </div>
                <div class="mother-card-details">
                    <div class="babies-detail-title">Clinical Admission & Delivery Details</div>
                    <div style="background-color: #f8fafc; border: 1px solid var(--color-border); padding: 12px; border-radius: var(--radius-sm); font-size: 0.8rem; line-height: 1.5;">
                        <div>BP at Admission: <strong>${item.bp_admission}</strong></div>
                        <div>BP at Discharge: <strong>${item.bp_discharge}</strong></div>
                        <div>Type of Delivery: <strong>${item.delivery_type}</strong></div>
                        <div>Complications at Admission: <strong>${item.complication_admission}</strong></div>
                        <div>Complications at Delivery: <strong>${item.complication_delivery}</strong></div>
                        <div>Maternal Death: <strong>${item.maternal_death}</strong></div>
                        <div>Discharge Date: <strong>${formatDateStr(item.discharge_date)}</strong></div>
                    </div>
                </div>
            </div>
        `;
    });
    cardsContainer.innerHTML = cardsHtml;

    if (filtered.length > visibleHomeDeliveries) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }
}

// ================= RENDER 8: OUT-OF-DISTRICT DELIVERIES =================
function renderOutDistrictDeliveriesList() {
    const tableBody = document.getElementById('out-district-deliveries-table-body');
    const cardsContainer = document.getElementById('out-district-deliveries-cards-container');
    const loadMoreBtn = document.getElementById('load-more-out-district-deliveries');

    if (!dbData || !dbData.out_district_deliveries_list) return;

    // Highlight active KPI card
    document.querySelectorAll('.out-kpi-filter-card').forEach(card => {
        const fVal = card.getAttribute('data-out-filter');
        if (fVal === activeOutMatchStatus) {
            card.classList.add('active-kpi-card');
        } else {
            card.classList.remove('active-kpi-card');
        }
    });

    // Calculate stats dynamically based on main filters (Block, Month)
    const statsFilteredOut = dbData.out_district_deliveries_list.filter(item => {
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return false;
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.delivery_date.substring(0, 7))) return false;
        return true;
    });
    const totalCountOut = statsFilteredOut.length;
    const exactCountOut = statsFilteredOut.filter(x => x.match_status === 'exact').length;
    const spellingCountOut = statsFilteredOut.filter(x => x.match_status === 'spelling').length;
    const unmatchedCountOut = statsFilteredOut.filter(x => x.match_status === 'unmatched').length;
    
    if (document.getElementById('anmol-out-total')) document.getElementById('anmol-out-total').textContent = totalCountOut.toLocaleString();
    if (document.getElementById('anmol-out-exact')) document.getElementById('anmol-out-exact').textContent = exactCountOut.toLocaleString();
    if (document.getElementById('anmol-out-spelling')) document.getElementById('anmol-out-spelling').textContent = spellingCountOut.toLocaleString();
    if (document.getElementById('anmol-out-unmatched')) document.getElementById('anmol-out-unmatched').textContent = unmatchedCountOut.toLocaleString();

    let filtered = statsFilteredOut.filter(item => {
        if (activeOutMatchStatus !== 'ALL' && item.match_status !== activeOutMatchStatus) {
            return false;
        }
        if (searchOutDistrictDeliveries) {
            const query = searchOutDistrictDeliveries.toLowerCase();
            const matchName = item.name ? item.name.toLowerCase().includes(query) : false;
            const matchMpid = item.id ? String(item.id).toLowerCase().includes(query) : false;
            const matchBlock = item.block ? item.block.toLowerCase().includes(query) : false;
            const matchVillage = item.village ? item.village.toLowerCase().includes(query) : false;
            const matchPhone = item.phone ? item.phone.includes(query) : false;
            const matchRc = item.redcap_id ? String(item.redcap_id).toLowerCase().includes(query) : false;
            const matchDistrict = item.delivery_district ? item.delivery_district.toLowerCase().includes(query) : false;
            if (!matchName && !matchMpid && !matchBlock && !matchVillage && !matchPhone && !matchRc && !matchDistrict) return false;
        }
        return true;
    });

    filtered = sortDataList(filtered, sortFieldOutDistrictDeliveries, sortOrderOutDistrictDeliveries);
    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['out_district_deliveries'] = filtered;

    document.getElementById('out-district-deliveries-count-badge').textContent = `${filtered.length.toLocaleString()} cases`;

    if (filtered.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="no-records-msg">No out-of-district delivery cases found matching the criteria.</td></tr>';
        cardsContainer.innerHTML = '<div class="no-records-msg">No out-of-district delivery cases found.</div>';
        loadMoreBtn.style.display = 'none';
        return;
    }

    const sliced = filtered.slice(0, visibleOutDistrictDeliveries);

    // Desktop rendering
    let tableHtml = '';
    sliced.forEach(item => {
        let callActionsHtml = '';
        if (item.phone) {
            callActionsHtml = `<a href="tel:${item.phone}" class="phone-link-btn" style="height:32px; padding:0 8px; font-size:0.75rem; display:inline-flex;">Call: ${item.phone}</a>`;
        } else {
            callActionsHtml = '<span style="color:var(--color-text-muted); font-size:0.75rem;">No Phone</span>';
        }

        let contactsHtml = '';
        if (item.subcentre && item.subcentre !== 'Not Found') {
            contactsHtml += `<div style="font-size:0.7rem; color:#475569; margin-bottom:2px; font-weight:600;"> ${item.subcentre}</div>`;
        }
        if (item.anm_name && item.anm_name !== 'Not Found') {
            if (item.anm_phone) {
                contactsHtml += `<a href="tel:${item.anm_phone}" class="anm-pill" title="Call ANM: ${item.anm_name}">ANM: ${item.anm_name} (${item.anm_phone})</a><br>`;
            } else {
                contactsHtml += `<span class="anm-pill" style="background:#f1f5f9; color:#64748b; border-color:#cbd5e1;">ANM: ${item.anm_name}</span><br>`;
            }
        }
        if (item.cho_name && item.cho_name !== 'Not Found') {
            if (item.cho_phone) {
                contactsHtml += `<a href="tel:${item.cho_phone}" class="cho-pill" title="Call CHO: ${item.cho_name}">CHO: ${item.cho_name} (${item.cho_phone})</a><br>`;
            } else {
                contactsHtml += `<span class="cho-pill" style="background:#f1f5f9; color:#64748b; border-color:#cbd5e1;">CHO: ${item.cho_name}</span><br>`;
            }
        }

        let matchBadge = '';
        if (item.match_status === 'exact') {
            matchBadge = `<span class="baby-status-badge healthy" style="margin-left:8px; font-size:0.6rem;">REDCap Match (Exact: ID ${item.redcap_id})</span>`;
        } else if (item.match_status === 'spelling') {
            matchBadge = `<span class="baby-status-badge sick" style="margin-left:8px; font-size:0.6rem; background:#fffbeb; color:#b45309; border-color:#f59e0b;">Data/Spelling Mismatch (REDCap ID: ${item.redcap_id})</span>`;
        } else {
            matchBadge = `<span class="baby-status-badge" style="margin-left:8px; font-size:0.6rem; background:#fef2f2; color:#b91c1c; border-color:#fecaca;">Not Recorded in REDCap</span>`;
        }

        tableHtml += `
            <tr class="mother-row-expandable" onclick="toggleDesktopRow(this, '${item.id}', 'out-district-deliveries')">
                <td style="font-weight:700">${item.id}</td>
                <td>${item.block}</td>
                <td><strong>${item.name}</strong>${matchBadge}</td>
                <td><strong>${item.village}</strong><br><small style="color:var(--color-text-muted)">Subcentre: ${item.gp}</small></td>
                <td><strong>${item.delivery_district}</strong><br><small style="color:var(--color-text-muted)">${item.delivery_block}</small></td>
                <td>${formatDateStr(item.delivery_date)}</td>
                <td><span style="font-size:0.8rem; font-weight:600; color:var(--color-primary);">${item.newborns}</span></td>
                <td onclick="event.stopPropagation()">${callActionsHtml}</td>
                <td>${contactsHtml}</td>
            </tr>
        `;
    });
    tableBody.innerHTML = tableHtml;

    // Mobile rendering
    let cardsHtml = '';
    sliced.forEach(item => {
        let phoneButtons = '';
        if (item.phone) {
            phoneButtons += `<a href="tel:${item.phone}" class="phone-link-btn" onclick="event.stopPropagation();">Call Beneficiary</a>`;
        }
        if (item.anm_phone) {
            phoneButtons += `<a href="tel:${item.anm_phone}" class="phone-link-btn anm" onclick="event.stopPropagation();">Call ANM</a>`;
        }
        if (item.cho_phone) {
            phoneButtons += `<a href="tel:${item.cho_phone}" class="phone-link-btn cho" onclick="event.stopPropagation();">Call CHO</a>`;
        }

        cardsHtml += `
            <div class="mother-card" data-id="${item.id}">
                <div class="mother-card-summary" onclick="toggleCardExpansion(this)">
                    <div class="mother-card-header">
                        <div>
                            <span class="mother-name">${item.name}</span>
                            <span class="record-id-tag">MPID: ${item.id}</span>
                        </div>
                        <span class="delivery-date-badge" style="background-color:#e0e7ff; color:#3730a3; border-color:#c7d2fe;">Out-District Delivery</span>
                    </div>

                    <div class="mother-address-block">
                        <div class="address-item">
                            <span class="address-label">Beneficiary Village / Subcentre</span>
                            <span class="address-val">${item.village} (${item.gp})</span>
                        </div>
                        <div class="address-item">
                            <span class="address-label">Delivery Place (District / Block)</span>
                            <span class="address-val"><strong>${item.delivery_district} / ${item.delivery_block}</strong></span>
                        </div>
                        <div class="address-item">
                            <span class="address-label">Delivery Date</span>
                            <span class="address-val"><strong>${formatDateStr(item.delivery_date)}</strong></span>
                        </div>
                    </div>

                    <div class="mother-address-block" style="grid-template-columns: 1fr; margin-top: 8px;">
                        <div class="address-item">
                            <span class="address-label">Newborn Details</span>
                            <span class="address-val" style="font-weight:700; color:var(--color-primary);">${item.newborns}</span>
                        </div>
                    </div>

                    <div class="mother-address-block" style="grid-template-columns: 1fr; margin-top: 8px;">
                        <div class="address-item">
                            <span class="address-label">Sub-Health Centre Contact</span>
                            <span class="address-val" style="font-size: 0.75rem; line-height: 1.4;">
                                 <strong>${item.subcentre}</strong><br>
                                ${item.anm_name !== 'Not Found' ? ` ANM: <strong>${item.anm_name}</strong> ${item.anm_phone ? '('+item.anm_phone+')' : ''}<br>` : ''}
                                ${item.cho_name !== 'Not Found' ? ` CHO: <strong>${item.cho_name}</strong> ${item.cho_phone ? '('+item.cho_phone+')' : ''}` : ''}
                            </span>
                        </div>
                    </div>

                    <div class="phone-links-wrap" onclick="event.stopPropagation();" style="margin-top: 10px;">
                        ${phoneButtons}
                    </div>

                    <div class="expand-indicator-row">
                        <svg class="expand-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                        </svg>
                    </div>
                </div>
                <div class="mother-card-details">
                    <div class="babies-detail-title">Clinical Admission & Delivery Details</div>
                    <div style="background-color: #f8fafc; border: 1px solid var(--color-border); padding: 12px; border-radius: var(--radius-sm); font-size: 0.8rem; line-height: 1.5;">
                        <div>BP at Admission: <strong>${item.bp_admission}</strong></div>
                        <div>BP at Discharge: <strong>${item.bp_discharge}</strong></div>
                        <div>Type of Delivery: <strong>${item.delivery_type}</strong></div>
                        <div>Complications at Admission: <strong>${item.complication_admission}</strong></div>
                        <div>Complications at Delivery: <strong>${item.complication_delivery}</strong></div>
                        <div>Maternal Death: <strong>${item.maternal_death}</strong></div>
                        <div>Discharge Date: <strong>${formatDateStr(item.discharge_date)}</strong></div>
                        <div>Facility Name: <strong>${item.facility_name || 'Not Recorded'}</strong></div>
                    </div>
                </div>
            </div>
        `;
    });
    cardsContainer.innerHTML = cardsHtml;

    if (filtered.length > visibleOutDistrictDeliveries) {
        loadMoreBtn.style.display = 'block';
    } else {
        loadMoreBtn.style.display = 'none';
    }
}

// =================================================================
//                 EXPORT TO EXCEL & COPY CLIPBOARD
// =================================================================
function escapeCsvCell(val) {
    if (val === null || val === undefined) return '""';
    const str = String(val).replace(/"/g, '""');
    return `"${str}"`;
}

function getTabExportData(tabName) {
    const data = window.currentFilteredData && window.currentFilteredData[tabName];
    if (!data || data.length === 0) return null;

    let headers = [];
    let rows = [];

    if (tabName === 'overall') {
        headers = [
            "Record ID", "Mother Name", "Block", "Delivery Date",
            "Delivery Location", "Delivery Place", "Village", "GP",
            "Follow-up Status", "Baby Details", "Primary Mobile", "Alternate Mobile",
            "Delivery Coordinator", "Follow-up Coordinator",
            "Data Issues Count", "Discrepancy Details"
        ];
        rows = data.map(r => {
            const babyDetailsStr = (r.babies || []).map(b => `${b.baby_id || ('Baby ' + b.baby_index)} (${b.sex || 'N/A'}, ${b.weight ? b.weight + 'g' : 'no wt'}, Status: ${b.status || 'Pending'})`).join('; ');
            const isCompleted = (r.babies || []).length > 0 && (r.babies || []).every(b => b.status === 'Completed' || b.status === 'Stillbirth' || b.status === 'Deceased' || b.is_stillbirth || b.is_neonatal_death);
            const followupStatus = isCompleted ? 'Completed' : 'Pending';
            return [
                r.id,
                r.name,
                r.block,
                formatDateStr(r.deliv_date),
                r.deliv_loc || 'Not Recorded',
                r.deliv_place || 'Not Recorded',
                r.village || 'Not Recorded',
                r.gp || 'Not Recorded',
                followupStatus,
                babyDetailsStr,
                r.phone1 || '',
                r.phone2 || '',
                r.coord || '',
                r.followup_coord || '',
                r.disc_reasons ? r.disc_reasons.length : 0,
                r.disc_reasons ? r.disc_reasons.join('; ') : ''
            ];
        });
    } else if (tabName === 'lost-followup') {
        headers = [
            "Record ID", "Mother Name", "Husband Name", "Block", "Delivery Date",
            "Baby Age (Days)", "Primary Mobile", "Alternate Mobile", "Village", "Subcentre",
            "ANM Name", "ANM Phone", "CHO Name", "CHO Phone", "Follow-up Coordinator",
            "Baby ID", "Sex", "Weight", "Lost Reason Category", "Original Remark"
        ];
        rows = [];
        data.forEach(r => {
            const ageDays = getBabyAgeInDays(r.delivery_date);
            (r.babies || []).forEach(b => {
                rows.push([
                    r.id,
                    r.mother_name || r.name,
                    r.husband_name || '',
                    r.block,
                    formatDateStr(r.delivery_date),
                    ageDays,
                    r.phone1 || '',
                    r.phone2 || '',
                    r.village || 'Not Recorded',
                    r.subcentre || 'Not Recorded',
                    r.anm_name || '',
                    r.anm_phone || '',
                    r.cho_name || '',
                    r.cho_phone || '',
                    r.followup_coord || r.coord || '',
                    b.baby_id || ('Baby ' + b.baby_index),
                    b.sex || '',
                    b.weight || '',
                    b.lost_category || '',
                    b.lost_remark || ''
                ]);
            });
        });
    } else if (tabName === 'pending') {
        headers = [
            "Record ID", "Mother Name", "Block", "Delivery Date",
            "Primary Mobile", "Alternate Mobile", "Village", "GP",
            "Subcentre", "ASHA Mobile", "ANM Name", "ANM Phone",
            "CHO Name", "CHO Phone", "Baby ID", "Baby Age (Days)", "Status",
            "Delivery Coordinator", "Follow-up Coordinator"
        ];
        rows = data.map(r => {
            const ageDays = getBabyAgeInDays(r.delivery_date);
            const pendingStatus = ageDays === 29 ? "Day 29 Follow-up" : (ageDays >= 30 ? `Overdue (${ageDays}d)` : `Pending (${ageDays}d)`);
            const babyIdsStr = (r.babies || []).map(b => b.baby_id || ('Baby ' + b.baby_index)).join('; ');
            return [
                r.id,
                r.name,
                r.block,
                formatDateStr(r.delivery_date),
                r.phone1 || '',
                r.phone2 || '',
                r.village || 'Not Recorded',
                r.gp || 'Not Recorded',
                r.subcentre || 'Not Recorded',
                r.asha_mobile || '',
                r.anm_name || 'Not Recorded',
                r.anm_phone || '',
                r.cho_name || 'Not Recorded',
                r.cho_phone || '',
                babyIdsStr,
                ageDays !== null ? ageDays : 'N/A',
                pendingStatus,
                r.coord || '',
                r.followup_coord || ''
            ];
        });
    } else if (tabName === 'stillbirths') {
        headers = [
            "Record ID", "Mother Name", "Block", "Delivery Date",
            "Delivery Location", "Delivery Place", "Village", "GP",
            "Reason / Notes", "Baby ID", "Baby Number", "Sex",
            "Birth Weight (g)", "Family Mobile", "Delivery Coordinator"
        ];
        rows = data.map(r => [
            r.id,
            r.name,
            r.block,
            formatDateStr(r.delivery_date),
            r.deliv_loc || 'Not Recorded',
            r.deliv_place || 'Not Recorded',
            r.village || 'Not Recorded',
            r.gp || 'Not Recorded',
            r.reasons || r.notes || 'Still Born / IUD',
            r.baby_id || '',
            r.baby_num || 'Baby 1',
            r.sex || '',
            r.weight ? r.weight + 'g' : 'Not Recorded',
            r.phone1 || '',
            r.coord || ''
        ]);
    } else if (tabName === 'home_deliveries') {
        headers = [
            "S.No", "Registration Date", "Delivery Date", "Mother Name",
            "Husband Name", "Mobile Number", "Block", "Village",
            "Subcentre", "ANM Name", "ANM Mobile", "Delivery Place",
            "Anmol MPID", "Newborn Status", "REDCap Match Status",
            "Matched REDCap ID", "CHO Name", "CHO Mobile",
            "Delivery Type", "Maternal Death"
        ];
        rows = data.map((r, idx) => [
            r.s_no || (idx + 1),
            r.reg_date || 'N/A',
            formatDateStr(r.delivery_date),
            r.pw_name || r.name,
            r.husband_name || '',
            r.phone || '',
            r.block,
            r.village || 'Not Recorded',
            r.gp || r.subcentre || 'Not Recorded',
            r.anm_name || 'Not Recorded',
            r.anm_phone || '',
            r.delivery_at || 'Home',
            r.id,
            r.newborns || '',
            (r.match_status || 'unmatched').toUpperCase(),
            r.redcap_id || 'N/A',
            r.cho_name || 'Not Recorded',
            r.cho_phone || '',
            r.delivery_type || 'Normal',
            r.maternal_death || 'No'
        ]);
    } else if (tabName === 'out_district_deliveries') {
        headers = [
            "S.No", "Registration Date", "Delivery Date", "Mother Name",
            "Husband Name", "Mobile Number", "Block", "Village",
            "Subcentre", "ANM Name", "ANM Mobile", "Delivery Place",
            "Delivery District / Block", "Anmol MPID", "Newborn Status",
            "REDCap Match Status", "Matched REDCap ID", "CHO Name", "CHO Mobile"
        ];
        rows = data.map((r, idx) => [
            r.s_no || (idx + 1),
            r.reg_date || 'N/A',
            formatDateStr(r.delivery_date),
            r.pw_name || r.name,
            r.husband_name || '',
            r.phone || '',
            r.block,
            r.village || 'Not Recorded',
            r.gp || r.subcentre || 'Not Recorded',
            r.anm_name || 'Not Recorded',
            r.anm_phone || '',
            r.facility_name || r.deliv_place || 'Not Recorded',
            `${r.delivery_district || ''} / ${r.delivery_block || ''}`,
            r.id,
            r.newborns || '',
            (r.match_status || 'unmatched').toUpperCase(),
            r.redcap_id || 'N/A',
            r.cho_name || 'Not Recorded',
            r.cho_phone || ''
        ]);
    } else if (tabName === 'deaths') {
        headers = [
            "Record ID", "MP ID / RCH ID", "Block", "Mother Name", "Husband Name",
            "Baby Number", "Sex", "Birth Weight", "Delivery Date", "Death Date",
            "Age at Death", "Place of Death", "Family Mobile"
        ];
        rows = data.map(r => [
            r.id,
            r.mp_id_rch || '',
            r.block,
            r.mother_name || r.name || '',
            r.husband_name || '',
            r.baby_num,
            r.sex,
            r.weight ? r.weight + 'g' : 'N/A',
            formatDateStr(r.delivery_date),
            formatDateStr(r.death_date),
            r.age_at_death !== null ? r.age_at_death + ' days' : 'N/A',
            r.place_of_death || 'Not Recorded',
            r.phone1 || ''
        ]);
    } else if (tabName === 'khandwa_sncu') {
        headers = [
            "Admission ID", "Block", "District", "Mother Name", "Father Name",
            "Sex", "Birth Weight", "Delivery Date", "Death Date",
            "Age at Death", "Place of Delivery", "Phone", "Village", "Address",
            "REDCap Match Status", "Matched REDCap Record ID", "Matched REDCap Mother", "Matched REDCap Father", "REDCap Place of Death",
            "Date of Death Verification", "Birth Weight Verification", "Cause of Death"
        ];
        rows = data.map(r => [
            r.adm_id,
            r.block,
            r.district || '',
            r.mother_name,
            r.father_name || '',
            r.sex || '',
            r.weight_g ? r.weight_g + 'g' : (r.weight ? r.weight + ' kg' : ''),
            formatDateStr(r.dob),
            formatDateStr(r.death_date),
            r.age_at_death !== null && r.age_at_death !== undefined ? r.age_at_death + ' days' : '',
            r.deliv_place || '',
            r.contact || '',
            r.village || '',
            r.address || '',
            r.match_type === 'accurate' ? `Accurate (${r.matched_criteria_count || 0}/9)` : (r.match_type === 'spelling' ? `Spelling Mismatch (${r.matched_criteria_count || 0}/9)` : 'Not in REDCap'),
            r.redcap_id || 'N/A',
            r.redcap_mother || 'N/A',
            r.redcap_father || 'N/A',
            r.rc_place_of_death || 'Not Recorded',
            (r.match_criteria && r.match_criteria.death_date) ? 'Yes' : 'No',
            (r.match_criteria && r.match_criteria.weight) ? 'Yes' : 'No',
            r.cause || ''
        ]);
    } else if (tabName === 'sncu') {
        headers = [
            "Admission ID", "Block", "Mother Name", "Father Name",
            "Sex", "Birth Weight", "Delivery Date", "Death Date",
            "Age at Death", "Place of Delivery", "Phone", "Village", "Address",
            "REDCap Match Status", "Matched REDCap Record ID", "Matched REDCap Mother", "Matched REDCap Father", "REDCap Place of Death",
            "Date of Death Verification", "Birth Weight Verification", "Cause of Death"
        ];
        rows = data.map(r => [
            r.adm_id,
            r.block,
            r.mother_name,
            r.father_name || '',
            r.sex || '',
            r.weight_g ? r.weight_g + 'g' : (r.weight ? r.weight + ' kg' : 'N/A'),
            formatDateStr(r.dob),
            formatDateStr(r.death_date),
            r.age_at_death !== null && r.age_at_death !== undefined ? r.age_at_death + ' days' : 'N/A',
            r.deliv_place || 'Not Recorded',
            r.contact || '',
            r.village || '',
            r.address || '',
            r.match_type === 'accurate' ? `Accurate (${r.matched_criteria_count || 0}/9)` : (r.match_type === 'spelling' ? `Spelling Mismatch (${r.matched_criteria_count || 0}/9)` : 'Not in REDCap'),
            r.redcap_id || 'N/A',
            r.redcap_mother || 'N/A',
            r.redcap_father || 'N/A',
            r.rc_place_of_death || 'Not Recorded',
            (r.match_criteria && r.match_criteria.death_date) ? 'Yes' : 'No',
            (r.match_criteria && r.match_criteria.weight) ? 'Yes' : 'No',
            r.cause || 'Not Recorded'
        ]);
    } else if (tabName === 'out_range_deaths') {
        headers = [
            "Record ID", "Block", "Mother Name", "Baby Number",
            "Baby ID", "Sex", "Birth Weight", "Delivery Date",
            "Death Date", "Age at Death", "Place of Delivery", "Place of Death", "Family Mobile"
        ];
        rows = data.map(r => [
            r.id,
            r.block,
            r.name,
            r.baby_num,
            r.baby_id,
            r.sex,
            r.weight ? r.weight + 'g' : 'N/A',
            formatDateStr(r.delivery_date),
            formatDateStr(r.death_date),
            r.age_at_death + ' days',
            r.deliv_place || 'Not Recorded',
            r.place_of_death || 'Not Recorded',
            r.phone1 || ''
        ]);
    }

    return { headers, rows };
}

function exportToCSV(tabName) {
    const exportData = getTabExportData(tabName);
    if (!exportData || !exportData.rows || exportData.rows.length === 0) {
        alert("No records to export.");
        return;
    }
    const { headers, rows } = exportData;

    const csvRows = [headers.map(escapeCsvCell).join(',')];
    rows.forEach(r => {
        csvRows.push(r.map(escapeCsvCell).join(','));
    });

    const csvString = csvRows.join('\r\n');
    const blob = new Blob(["\uFEFF" + csvString], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);

    const timestamp = new Date().toISOString().slice(0, 10);
    link.setAttribute("download", `Sankalp_${tabName}_filtered_export_${timestamp}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function copyToClipboard(tabName) {
    const exportData = getTabExportData(tabName);
    if (!exportData || !exportData.rows || exportData.rows.length === 0) {
        alert("No records to copy.");
        return;
    }
    const { headers, rows } = exportData;

    const textRows = [headers.join('\t')];
    rows.forEach(r => {
        textRows.push(r.map(val => {
            const valStr = val === null || val === undefined ? '' : String(val);
            return valStr.replace(/[\t\r\n]/g, ' ');
        }).join('\t'));
    });

    const textContent = textRows.join('\n');

    navigator.clipboard.writeText(textContent).then(() => {
        showToast("List copied to clipboard!");
    }).catch(err => {
        console.error("Clipboard copy failed: ", err);
        try {
            const textarea = document.createElement("textarea");
            textarea.value = textContent;
            textarea.style.position = "fixed";
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand("copy");
            document.body.removeChild(textarea);
            showToast("List copied to clipboard!");
        } catch (e) {
            alert("Failed to copy list automatically. Please try exporting instead.");
        }
    });
}

function showToast(message) {
    let toast = document.getElementById("clipboard-toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "clipboard-toast";
        toast.style.position = "fixed";
        toast.style.bottom = "24px";
        toast.style.left = "50%";
        toast.style.transform = "translateX(-50%)";
        toast.style.background = "#333";
        toast.style.color = "#fff";
        toast.style.padding = "10px 20px";
        toast.style.borderRadius = "20px";
        toast.style.fontSize = "13px";
        toast.style.fontWeight = "600";
        toast.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
        toast.style.zIndex = "9999";
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.2s ease";
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = "1";
    setTimeout(() => {
        toast.style.opacity = "0";
    }, 2000);
}


function renderSncuDeathsList() {
    const rawList = dbData.sncu_deaths_list || [];
    const tbody = document.getElementById('sncu-table-body');
    const cardsContainer = document.getElementById('sncu-cards-container');
    const badgeCount = document.getElementById('sncu-count-badge');
    const badgeTab = document.getElementById('badge-sncu-deaths');
    
    // KPI card elements
    const elTotal = document.getElementById('card-sncu-total');
    const elDhKhargone = document.getElementById('card-sncu-dh-khargone');
    const elAccurate = document.getElementById('card-sncu-accurate');
    const elSpelling = document.getElementById('card-sncu-spelling');
    const elRecHealthy = document.getElementById('card-sncu-rec-healthy');
    const elRecPending = document.getElementById('card-sncu-rec-pending');
    const elNotInRedcap = document.getElementById('card-sncu-not-in-redcap');

    if (!tbody) return;
    tbody.innerHTML = '';
    if (cardsContainer) cardsContainer.innerHTML = '';

    // Highlight the active KPI card
    document.querySelectorAll('.sncu-kpi-filter-card').forEach(card => {
        const filterVal = card.getAttribute('data-sncu-filter');
        if (filterVal === activeSncuMatchStatus) {
            card.classList.add('active-kpi-card');
        } else {
            card.classList.remove('active-kpi-card');
        }
    });

    // Calculate dynamic KPI card counts based on main block/month filters
    let totalCnt = 0, accurateCnt = 0, spellingCnt = 0, recHealthyCnt = 0, recPendingCnt = 0, notInRedcapCnt = 0;
    const blockFilteredList = [];

    rawList.forEach(item => {
        // Block filter
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return;
        // Month filter
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.month)) return;

        blockFilteredList.push(item);
        totalCnt++;
        if (item.match_type === 'accurate') accurateCnt++;
        else if (item.match_type === 'spelling') spellingCnt++;
        else notInRedcapCnt++;

        if (item.redcap_status === 'healthy') {
            recHealthyCnt++;
        } else if (item.redcap_status === 'pending') {
            recPendingCnt++;
        }
    });

    // Calculate REDCap DH Khargone deaths count for active block/month filters
    let dhKhargoneCnt = 0;
    const rcDhList = dbData.dh_khargone_redcap_deaths_by_filter || [];
    rcDhList.forEach(r => {
        if (activeBlock !== 'ALL' && r.b !== activeBlock) return;
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(r.m)) return;
        dhKhargoneCnt++;
    });

    if (elTotal) elTotal.textContent = totalCnt.toLocaleString();
    if (elDhKhargone) elDhKhargone.textContent = dhKhargoneCnt.toLocaleString();
    if (elAccurate) elAccurate.textContent = accurateCnt.toLocaleString();
    if (elSpelling) elSpelling.textContent = spellingCnt.toLocaleString();
    if (elRecHealthy) elRecHealthy.textContent = recHealthyCnt.toLocaleString();
    if (elRecPending) elRecPending.textContent = recPendingCnt.toLocaleString();
    if (elNotInRedcap) elNotInRedcap.textContent = notInRedcapCnt.toLocaleString();
    if (badgeTab) badgeTab.textContent = totalCnt.toLocaleString();

    // Filter by match/REDCap status and search query
    const filteredList = blockFilteredList.filter(item => {
        if (activeSncuDelivPlace !== 'ALL' && item.deliv_place !== activeSncuDelivPlace) return false;
        if (activeSncuMatchStatus !== 'ALL') {
            if (activeSncuMatchStatus === 'accurate' && item.match_type !== 'accurate') return false;
            else if (activeSncuMatchStatus === 'spelling' && item.match_type !== 'spelling') return false;
            else if (activeSncuMatchStatus === 'unmatched' && item.match_type !== 'unmatched') return false;
            else if (activeSncuMatchStatus === 'not_in_redcap' && item.match_type !== 'unmatched') return false;
            else if (activeSncuMatchStatus === 'dead' && (item.redcap_status !== 'dead' && item.redcap_status !== 'stillbirth')) return false;
            else if (activeSncuMatchStatus === 'pending' && item.redcap_status !== 'pending') return false;
            else if (activeSncuMatchStatus === 'healthy' && item.redcap_status !== 'healthy') return false;
            else if (activeSncuMatchStatus === 'dh_khargone' && !item.is_rc_dh_khargone_death) return false;
        }
        if (searchSncuQuery) {
            const haystack = `${item.adm_id} ${item.mother_name} ${item.father_name} ${item.contact} ${item.block} ${item.village} ${item.cause} ${item.redcap_id} ${item.redcap_mother} ${item.redcap_deliv_place || ''} ${item.redcap_status_label || ''}`.toLowerCase();
            if (!haystack.includes(searchSncuQuery)) return false;
        }
        return true;
    });

    if (badgeCount) badgeCount.textContent = `${filteredList.length} deaths`;

    const sorted = sortDataList(filteredList, sortFieldSncu, sortOrderSncu);
    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['sncu'] = filteredList;

    const visibleItems = sorted.slice(0, visibleSncu);

    if (visibleItems.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--color-text-muted); padding: 24px;">No SNCU neonatal death cases match the current filter criteria.</td></tr>`;
        return;
    }

    visibleItems.forEach(item => {
        let statusPill = '';
        if (item.match_type === 'accurate') {
            statusPill = `<span class="baby-status-badge healthy" style="margin-left:6px; font-size:0.65rem;">Accurate Match (${item.matched_criteria_count || 0}/9)</span>`;
        } else if (item.match_type === 'spelling') {
            statusPill = `<span class="baby-status-badge pending" style="margin-left:6px; font-size:0.65rem; background:#fffbeb; color:#b45309; border-color:#f59e0b;">Spelling/Data Mismatch (${item.matched_criteria_count || 0}/9)</span>`;
        } else {
            statusPill = `<span style="margin-left:6px; font-size:0.65rem; color:#64748b; background:#f1f5f9; padding:2px 6px; border-radius:4px; border:1px solid #cbd5e1;">Not in REDCap</span>`;
        }

        const motherDisplay = `<b>${item.mother_name}</b>${item.father_name ? ` <span style="font-size:0.75rem; color:var(--color-text-muted);">(W/o ${item.father_name})</span>` : ''}${statusPill}`;

        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.className = 'mother-row-expandable';
        tr.setAttribute('onclick', `toggleDesktopRow(this, '${item.adm_id}', 'sncu')`);
        tr.innerHTML = `
            <td><b>${item.adm_id}</b></td>
            <td><b>${item.block}</b>${item.village ? `<br/><span style="font-size:0.72rem; color:var(--color-text-muted);">${item.village}</span>` : ''}</td>
            <td>${motherDisplay}</td>
            <td>${item.sex || 'N/A'}</td>
            <td>${item.weight_g ? item.weight_g + 'g' : (item.weight ? item.weight + ' kg' : 'N/A')}</td>
            <td>${formatDateStr(item.dob)}</td>
            <td>${formatDateStr(item.death_date)}</td>
            <td><span style="font-weight:700; color:var(--color-danger);">${item.age_at_death !== null ? item.age_at_death + ' days' : 'N/A'}</span></td>
            <td>${item.deliv_place || 'Not Recorded'}</td>
            <td>${item.contact ? `<a href="tel:${item.contact}" onclick="event.stopPropagation()">${item.contact}</a>` : 'N/A'}</td>
        `;
        tbody.appendChild(tr);
    });

    const btnLoadMoreSncu = document.getElementById('load-more-sncu');
    if (btnLoadMoreSncu) {
        btnLoadMoreSncu.style.display = (visibleSncu < filteredList.length) ? 'block' : 'none';
    }
}


function renderKhandwaSncuDeathsList() {
    const rawList = dbData.khandwa_sncu_deaths_list || [];
    const tbody = document.getElementById('khandwa-sncu-table-body');
    const cardsContainer = document.getElementById('khandwa-sncu-cards-container');
    const badgeCount = document.getElementById('khandwa-sncu-count-badge');
    const badgeTab = document.getElementById('badge-khandwa-sncu-deaths');
    const loadMoreBtn = document.getElementById('load-more-khandwa-sncu');
    
    // KPI card elements
    const elTotal = document.getElementById('card-khandwa-total');
    const elAccurate = document.getElementById('card-khandwa-accurate');
    const elSpelling = document.getElementById('card-khandwa-spelling');
    const elRecHealthy = document.getElementById('card-khandwa-rec-healthy');
    const elRecPending = document.getElementById('card-khandwa-rec-pending');
    const elNotInRedcap = document.getElementById('card-khandwa-not-in-redcap');

    if (!tbody) return;
    tbody.innerHTML = '';
    if (cardsContainer) cardsContainer.innerHTML = '';

    // Highlight the active KPI card
    document.querySelectorAll('.khandwa-kpi-filter-card').forEach(card => {
        const filterVal = card.getAttribute('data-khandwa-filter');
        if (filterVal === activeKhandwaMatchStatus) {
            card.classList.add('active-kpi-card');
        } else {
            card.classList.remove('active-kpi-card');
        }
    });

    // Calculate dynamic KPI card counts based on main block/month filters
    let totalCnt = 0, accurateCnt = 0, spellingCnt = 0, recHealthyCnt = 0, recPendingCnt = 0, notInRedcapCnt = 0;
    const blockFilteredList = [];

    rawList.forEach(item => {
        // Block filter
        if (activeBlock !== 'ALL' && item.block !== activeBlock) return;
        // Month filter
        if (activeMonths.length > 0 && !activeMonths.includes('ALL') && !activeMonths.includes(item.month)) return;

        blockFilteredList.push(item);
        totalCnt++;
        if (item.match_type === 'accurate') accurateCnt++;
        else if (item.match_type === 'spelling') spellingCnt++;
        else notInRedcapCnt++;

        if (item.redcap_status === 'healthy') {
            recHealthyCnt++;
        } else if (item.redcap_status === 'pending') {
            recPendingCnt++;
        }
    });

    if (elTotal) elTotal.textContent = totalCnt.toLocaleString();
    if (elAccurate) elAccurate.textContent = accurateCnt.toLocaleString();
    if (elSpelling) elSpelling.textContent = spellingCnt.toLocaleString();
    if (elRecHealthy) elRecHealthy.textContent = recHealthyCnt.toLocaleString();
    if (elRecPending) elRecPending.textContent = recPendingCnt.toLocaleString();
    if (elNotInRedcap) elNotInRedcap.textContent = notInRedcapCnt.toLocaleString();
    if (badgeTab) badgeTab.textContent = totalCnt.toLocaleString();

    // Filter by match/REDCap status and search query
    const filteredList = blockFilteredList.filter(item => {
        if (activeKhandwaDelivPlace !== 'ALL' && item.deliv_place !== activeKhandwaDelivPlace) return false;
        if (activeKhandwaMatchStatus !== 'ALL') {
            if (activeKhandwaMatchStatus === 'accurate' && item.match_type !== 'accurate') return false;
            else if (activeKhandwaMatchStatus === 'spelling' && item.match_type !== 'spelling') return false;
            else if ((activeKhandwaMatchStatus === 'unmatched' || activeKhandwaMatchStatus === 'not_in_redcap') && item.match_type !== 'unmatched') return false;
            else if (activeKhandwaMatchStatus === 'healthy' && item.redcap_status !== 'healthy') return false;
            else if (activeKhandwaMatchStatus === 'pending' && item.redcap_status !== 'pending') return false;
        }
        if (searchKhandwaSncuQuery) {
            const haystack = `${item.adm_id} ${item.mother_name} ${item.father_name} ${item.contact} ${item.block} ${item.village} ${item.cause} ${item.redcap_id} ${item.redcap_mother} ${item.redcap_deliv_place || ''} ${item.redcap_status_label || ''}`.toLowerCase();
            if (!haystack.includes(searchKhandwaSncuQuery)) return false;
        }
        return true;
    });

    if (!window.currentFilteredData) window.currentFilteredData = {};
    window.currentFilteredData['khandwa_sncu'] = filteredList;

    if (badgeCount) badgeCount.textContent = `${filteredList.length} deaths`;

    const sorted = sortDataList(filteredList, sortFieldKhandwaSncu, sortOrderKhandwaSncu);
    const visibleItems = sorted.slice(0, visibleKhandwaSncu);

    if (loadMoreBtn) {
        loadMoreBtn.style.display = sorted.length > visibleKhandwaSncu ? 'block' : 'none';
    }

    if (visibleItems.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--color-text-muted); padding: 24px;">No Khandwa SNCU neonatal death cases match the current filter criteria.</td></tr>`;
        return;
    }

    visibleItems.forEach(item => {
        let statusPill = '';
        if (item.match_type === 'accurate') {
            statusPill = `<span class="baby-status-badge healthy" style="margin-left:6px; font-size:0.65rem;">Accurate Match (${item.matched_criteria_count || 0}/9)</span>`;
        } else if (item.match_type === 'spelling') {
            statusPill = `<span class="baby-status-badge pending" style="margin-left:6px; font-size:0.65rem; background:#fffbeb; color:#b45309; border-color:#f59e0b;">Spelling/Data Mismatch (${item.matched_criteria_count || 0}/9)</span>`;
        } else {
            statusPill = `<span style="margin-left:6px; font-size:0.65rem; color:#64748b; background:#f1f5f9; padding:2px 6px; border-radius:4px; border:1px solid #cbd5e1;">Not in REDCap</span>`;
        }

        const motherDisplay = `<b>${item.mother_name}</b>${item.father_name ? ` <span style="font-size:0.75rem; color:var(--color-text-muted);">(W/o ${item.father_name})</span>` : ''}${statusPill}`;

        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.className = 'mother-row-expandable';
        tr.setAttribute('onclick', `toggleDesktopRow(this, '${item.adm_id}', 'khandwa_sncu')`);
        tr.innerHTML = `
            <td><b>${item.adm_id}</b></td>
            <td><b>${item.block}</b>${item.village ? `<br/><span style="font-size:0.72rem; color:var(--color-text-muted);">${item.village}</span>` : ''}</td>
            <td>${motherDisplay}</td>
            <td>${item.sex || 'N/A'}</td>
            <td>${item.weight_g ? item.weight_g + 'g' : (item.weight ? item.weight + ' kg' : 'N/A')}</td>
            <td>${formatDateStr(item.dob)}</td>
            <td>${formatDateStr(item.death_date)}</td>
            <td><span style="font-weight:700; color:var(--color-danger);">${item.age_at_death !== null ? item.age_at_death + ' days' : 'N/A'}</span></td>
            <td>${item.deliv_place || 'Not Recorded'}</td>
            <td>${item.contact ? `<a href="tel:${item.contact}" onclick="event.stopPropagation()">${item.contact}</a>` : 'N/A'}</td>
        `;
        tbody.appendChild(tr);


    });
}
