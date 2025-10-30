<!--
 * @fileoverview Enterprise-grade data table component for Vue.js 3
 * @module MyDataTable
 * @version 1.0.0
 -->

<template>
    <div class="space-y-4 p-5">
        <!-- Optional Top Card -->
        <div v-if="showTopCard"
            class="flex flex-col bg-white border border-gray-200 shadow-2xs rounded-xl p-4 md:p-5 dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-400">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div class="flex items-center gap-3">
                    <slot name="top-card-icon">
                        <div class="flex-shrink-0">
                            <svg class="flex-shrink-0 size-5 text-gray-800 dark:text-neutral-400"
                                xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
                                fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                stroke-linejoin="round">
                                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                                <polyline points="9 22 9 12 15 12 15 22"></polyline>
                            </svg>
                        </div>
                    </slot>
                    <div>
                        <h2 class="text-lg font-semibold text-gray-800 dark:text-neutral-200">
                            <slot name="top-card-title">{{ topCardTitle }}</slot>
                        </h2>
                        <p class="text-sm text-gray-600 dark:text-neutral-400">
                            <slot name="top-card-description">{{ topCardDescription }}</slot>
                        </p>
                    </div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <slot name="top-card-actions">
                        <button v-for="(action, index) in topCardActions" :key="index" type="button"
                            :class="action.classes" @click="handleTopCardAction(action)">
                            <span class="flex items-center gap-x-2">
                                <span v-if="action.icon" v-html="action.icon"></span>
                                {{ action.label }}
                            </span>
                        </button>
                    </slot>
                </div>
            </div>
        </div>

        <!-- Table Container -->
        <div class="flex flex-col">
            <div class="-m-1.5 overflow-x-auto">
                <div class="p-1.5 min-w-full inline-block align-middle">
                    <div class="overflow-hidden border border-gray-200 rounded-xl dark:border-neutral-700">
                        <TableContainer :table-columns="tableColumns" :sorted-data="sortedData"
                            :editing-cell="editingCell" :loading="loading" :enable-delete="enableDelete"
                            @sort="handleSort" @cell-edit-start="startEdit" @cell-edit="handleCellEdit"
                            @row-action="handleRowAction" />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import {
    ref,
    computed,
    watch,
    nextTick,
    onMounted,
    provide,
} from 'vue';
import TableContainer from './TableContainer.vue';

/**
 * Component props definition
 */
const props = defineProps({
    data: {
        type: Array,
        default: () => [],
    },
    columns: {
        type: Array,
        default: () => [],
    },
    loading: {
        type: Boolean,
        default: false,
    },
    card: {
        type: Boolean,
        default: false,
    },
    showTopCard: {
        type: Boolean,
        default: false,
    },
    topCardTitle: {
        type: String,
        default: 'Data Management',
    },
    topCardDescription: {
        type: String,
        default: 'Manage your data records efficiently',
    },
    enableDelete: {
        type: Boolean,
        default: true,
    },
    topCardActions: {
        type: Array,
        default: () => [
            {
                label: 'Add New',
                classes: 'py-2.5 px-4 inline-flex items-center gap-x-2 text-sm font-medium rounded-lg border border-transparent bg-blue-100 text-blue-800 hover:bg-blue-200 focus:outline-hidden focus:bg-blue-200 disabled:opacity-50 disabled:pointer-events-none dark:text-blue-400 dark:bg-blue-800/30 dark:hover:bg-blue-800/20 dark:focus:bg-blue-800/20',
                handler: () => console.log('Add new clicked'),
                icon: '<svg class="flex-shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>',
            },
            {
                label: 'Export',
                classes: 'py-2.5 px-4 inline-flex items-center gap-x-2 text-sm font-medium rounded-lg border border-gray-200 bg-white text-gray-800 hover:bg-gray-50 focus:outline-hidden focus:bg-gray-50 disabled:opacity-50 disabled:pointer-events-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700 dark:focus:bg-neutral-700',
                handler: () => console.log('Export clicked'),
                icon: '<svg class="flex-shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>',
            },
        ],
    },
});

/**
 * Event emissions definition
 */
const emit = defineEmits([
    'sort',
    'cell-edit',
    'cell-edit-start',
    'row-action',
    'load-start',
    'load-end',
    'top-card-action',
]);

/**
 * Enhanced sample data with 20 rows for demonstration
 */
const DEFAULT_DATA = Object.freeze([
    { id: 1, name: 'John Brown', age: 45, address: 'New York No. 1 Lake Park', status: 'active', email: 'john.brown@example.com' },
    { id: 2, name: 'Jim Green', age: 27, address: 'London No. 1 Lake Park', status: 'active', email: 'jim.green@example.com' },
    { id: 3, name: 'Joe Black', age: 31, address: 'Sidney No. 1 Lake Park', status: 'pending', email: 'joe.black@example.com' },
    { id: 4, name: 'Edward King', age: 16, address: 'LA No. 1 Lake Park', status: 'active', email: 'edward.king@example.com' },
    { id: 5, name: 'Jim Red', age: 45, address: 'Melbourne No. 1 Lake Park', status: 'inactive', email: 'jim.red@example.com' },
    { id: 6, name: 'Alice Johnson', age: 29, address: 'Chicago No. 1 Lake Park', status: 'active', email: 'alice.johnson@example.com' },
    { id: 7, name: 'Bob Smith', age: 35, address: 'Toronto No. 1 Lake Park', status: 'pending', email: 'bob.smith@example.com' },
    { id: 8, name: 'Carol Davis', age: 42, address: 'Vancouver No. 1 Lake Park', status: 'active', email: 'carol.davis@example.com' },
    { id: 9, name: 'David Wilson', age: 38, address: 'Berlin No. 1 Lake Park', status: 'inactive', email: 'david.wilson@example.com' },
    { id: 10, name: 'Eva Miller', age: 26, address: 'Paris No. 1 Lake Park', status: 'active', email: 'eva.miller@example.com' },
    { id: 11, name: 'Frank Brown', age: 33, address: 'Tokyo No. 1 Lake Park', status: 'pending', email: 'frank.brown@example.com' },
    { id: 12, name: 'Grace Lee', age: 29, address: 'Seoul No. 1 Lake Park', status: 'active', email: 'grace.lee@example.com' },
    { id: 13, name: 'Henry Clark', age: 45, address: 'Moscow No. 1 Lake Park', status: 'inactive', email: 'henry.clark@example.com' },
    { id: 14, name: 'Ivy White', age: 31, address: 'Dubai No. 1 Lake Park', status: 'active', email: 'ivy.white@example.com' },
    { id: 15, name: 'Jack Taylor', age: 28, address: 'Singapore No. 1 Lake Park', status: 'pending', email: 'jack.taylor@example.com' },
    { id: 16, name: 'Karen Harris', age: 36, address: 'Hong Kong No. 1 Lake Park', status: 'active', email: 'karen.harris@example.com' },
    { id: 17, name: 'Leo Martin', age: 41, address: 'Bangkok No. 1 Lake Park', status: 'inactive', email: 'leo.martin@example.com' },
    { id: 18, name: 'Mia Anderson', age: 24, address: 'Sydney No. 1 Lake Park', status: 'active', email: 'mia.anderson@example.com' },
    { id: 19, name: 'Nathan Thomas', age: 39, address: 'Rio No. 1 Lake Park', status: 'pending', email: 'nathan.thomas@example.com' },
    { id: 20, name: 'Olivia Garcia', age: 27, address: 'Mexico City No. 1 Lake Park', status: 'active', email: 'olivia.garcia@example.com' },
]);

/**
 * Default column configuration
 */
const DEFAULT_COLUMNS = Object.freeze([
    {
        key: 'name',
        label: 'Name',
        editable: true,
        sortable: true,
        type: 'text',
    },
    {
        key: 'age',
        label: 'Age',
        editable: true,
        sortable: true,
        type: 'text',
    },
    {
        key: 'email',
        label: 'Email',
        editable: true,
        sortable: true,
        type: 'text',
    },
    {
        key: 'address',
        label: 'Address',
        editable: true,
        sortable: true,
        type: 'text',
    },
    {
        key: 'status',
        label: 'Status',
        sortable: true,
        type: 'badge',
        badgeMap: Object.freeze({
            active: {
                label: 'Active',
                class: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            },
            pending: {
                label: 'Pending',
                class: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
            },
            inactive: {
                label: 'Inactive',
                class: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
            },
        }),
    },
]);

/**
 * Sort direction enumeration
 */
const SORT_DIRECTION = Object.freeze({
    ASC: 'asc',
    DESC: 'desc',
    NONE: 'none',
});

/**
 * Editing state management
 */
const editingCell = ref(null);
const sortConfig = ref(null);

/**
 * Computed table data with fallback to defaults
 */
const tableData = computed(() => {
    const hasData = Array.isArray(props.data) && props.data.length > 0;
    return hasData ? props.data : DEFAULT_DATA;
});

/**
 * Computed columns with fallback to defaults
 */
const tableColumns = computed(() => {
    const hasColumns = Array.isArray(props.columns) && props.columns.length > 0;
    return hasColumns ? props.columns : DEFAULT_COLUMNS;
});

/**
 * Sorted and filtered table data
 */
const sortedData = computed(() => {
    if (!sortConfig.value) {
        return tableData.value;
    }

    const { column, direction } = sortConfig.value;

    if (direction === SORT_DIRECTION.NONE) {
        return tableData.value;
    }

    return [...tableData.value].sort((a, b) => {
        const aValue = a[column];
        const bValue = b[column];

        if (aValue === bValue) return 0;

        const comparison = aValue < bValue ? -1 : 1;
        return direction === SORT_DIRECTION.ASC ? comparison : -comparison;
    });
});

/**
 * Get sort indicator for column header
 */
const getSortIndicator = (column) => {
    if (sortConfig.value?.column !== column.key) return '';
    return sortConfig.value.direction === SORT_DIRECTION.ASC ? '▲' : '▼';
};

/**
 * Get ARIA sort attribute for accessibility
 */
const getAriaSort = (column) => {
    if (sortConfig.value?.column !== column.key) return 'none';
    return sortConfig.value.direction === SORT_DIRECTION.ASC ? 'ascending' : 'descending';
};

/**
 * Handle column header click for sorting
 */
const handleSort = (column) => {
    if (!column.sortable) return;

    let newDirection = SORT_DIRECTION.ASC;

    if (sortConfig.value?.column === column.key) {
        const currentDirection = sortConfig.value.direction;
        newDirection = currentDirection === SORT_DIRECTION.ASC
            ? SORT_DIRECTION.DESC
            : currentDirection === SORT_DIRECTION.DESC
                ? SORT_DIRECTION.NONE
                : SORT_DIRECTION.ASC;
    }

    if (newDirection === SORT_DIRECTION.NONE) {
        sortConfig.value = null;
    } else {
        sortConfig.value = {
            column: column.key,
            direction: newDirection,
        };
    }

    emit('sort', {
        column: column.key,
        direction: sortConfig.value?.direction || SORT_DIRECTION.NONE,
    });
};

/**
 * Start editing a cell
 */
const startEdit = async (eventData) => {
    const { row, column } = eventData;
    if (!column.editable || props.loading) return;

    editingCell.value = {
        rowId: row.id,
        columnKey: column.key,
        originalValue: row[column.key],
    };

    emit('cell-edit-start', {
        rowId: row.id,
        column: column.key,
        value: row[column.key],
    });

    await nextTick();

    const inputElement = document.querySelector(`[data-edit-id="${row.id}-${column.key}"]`);
    if (inputElement instanceof HTMLInputElement) {
        inputElement.focus();
        inputElement.select();
    }
};

/**
 * Handle cell edit completion
 */
const handleCellEdit = (editData) => {
    if (!editingCell.value) return;

    const { rowId, columnKey, newValue, oldValue } = editData;

    if (newValue !== oldValue) {
        emit('cell-edit', {
            rowId,
            column: columnKey,
            oldValue,
            newValue,
        });
    }

    editingCell.value = null;
};

/**
 * Handle key events during editing
 */
const handleKeydown = (event, row, column) => {
    if (event.key === 'Enter') {
        const inputElement = event.target;
        handleCellEdit({
            rowId: row.id,
            columnKey: column.key,
            newValue: inputElement.value,
            oldValue: editingCell.value?.originalValue,
        });
    } else if (event.key === 'Escape') {
        editingCell.value = null;
    }
};

/**
 * Render badge content for status columns
 */
const renderBadge = (row, column) => {
    const value = row[column.key];
    const badgeConfig = column.badgeMap?.[value];

    if (!badgeConfig) {
        return {
            label: String(value),
            class: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
        };
    }

    return badgeConfig;
};

/**
 * Handle row actions with JavaScript confirm for delete
 */
const handleRowAction = (actionData) => {
    if (actionData.action === 'delete' && props.enableDelete) {
        // Show JavaScript confirm before delete
        const confirmed = confirm(`Are you sure you want to delete "${actionData.row.name}"? This action cannot be undone.`);

        if (!confirmed) {
            return; // User cancelled the delete
        }
    }

    emit('row-action', actionData);
};

/**
 * Handle top card actions
 */
const handleTopCardAction = (action) => {
    emit('top-card-action', action);
    if (action.handler) {
        action.handler();
    }
};

/**
 * Watch loading state and emit events
 */
watch(() => props.loading, (newValue, oldValue) => {
    if (newValue && !oldValue) {
        emit('load-start');
    } else if (!newValue && oldValue) {
        emit('load-end');
    }
});

/**
 * Component mounted lifecycle
 */
onMounted(() => {
    if (props.loading) {
        emit('load-start');
    }
});

// Provide functions to child component
provide('getSortIndicator', getSortIndicator);
provide('getAriaSort', getAriaSort);
provide('handleKeydown', handleKeydown);
provide('renderBadge', renderBadge);
provide('enableDelete', props.enableDelete);
</script>