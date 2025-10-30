<!--
 * @fileoverview Table container component for MyDataTable
 * @module TableContainer
 * @version 1.0.0
 -->

<template>
    <table class="min-w-full divide-y divide-gray-200 dark:divide-neutral-700">
        <thead>
            <tr>
                <th v-for="column in tableColumns" :key="column.key" scope="col"
                    class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase dark:text-neutral-500"
                    :class="{ 'cursor-pointer select-none': column.sortable }" :aria-sort="getAriaSort(column)"
                    @click="column.sortable ? $emit('sort', column) : null">
                    <div class="flex items-center gap-2">
                        <span>{{ column.label }}</span>
                        <span v-if="column.sortable" class="text-xs">
                            {{ getSortIndicator(column) }}
                        </span>
                    </div>
                </th>
                <th scope="col"
                    class="px-6 py-3 text-end text-xs font-medium text-gray-500 uppercase dark:text-neutral-500">Action
                </th>
            </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-neutral-700">
            <template v-if="loading">
                <tr v-for="i in 5" :key="i" class="hover:bg-gray-100 dark:hover:bg-neutral-700">
                    <td v-for="column in tableColumns" :key="column.key" class="px-6 py-4 whitespace-nowrap">
                        <div class="h-4 bg-gray-200 rounded animate-pulse dark:bg-neutral-700"></div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-end">
                        <div class="h-8 bg-gray-200 rounded animate-pulse dark:bg-neutral-700"></div>
                    </td>
                </tr>
            </template>
            <template v-else>
                <tr v-for="row in sortedData" :key="row.id" class="hover:bg-gray-100 dark:hover:bg-neutral-700">
                    <td v-for="column in tableColumns" :key="column.key"
                        class="px-6 py-4 whitespace-nowrap text-sm text-gray-800 dark:text-neutral-200" :class="{
                            'cursor-pointer': column.editable && !loading,
                            'font-medium': column.key === 'name'
                        }" @dblclick="column.editable ? $emit('cell-edit-start', { row, column }) : null">
                        <template v-if="editingCell?.rowId === row.id && editingCell?.columnKey === column.key">
                            <input :data-edit-id="`${row.id}-${column.key}`" type="text" :value="row[column.key]"
                                class="py-1.5 sm:py-2 px-3 block w-full border-gray-200 rounded-lg sm:text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-400 dark:placeholder-neutral-500 dark:focus:ring-neutral-600"
                                @blur="$emit('cell-edit', {
                                    rowId: row.id,
                                    columnKey: column.key,
                                    newValue: $event.target.value,
                                    oldValue: editingCell.originalValue
                                })" @keydown="handleKeydown($event, row, column)" />
                        </template>
                        <template v-else>
                            <template v-if="column.render">
                                {{ column.render(row) }}
                            </template>
                            <template v-else-if="column.type === 'badge'">
                                <span
                                    class="inline-flex items-center gap-x-1.5 py-1.5 px-3 rounded-full text-xs font-medium"
                                    :class="renderBadge(row, column).class">
                                    {{ renderBadge(row, column).label }}
                                </span>
                            </template>
                            <template v-else>
                                {{ row[column.key] }}
                            </template>
                        </template>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-end text-sm font-medium">
                        <button v-if="enableDelete" type="button"
                            class="inline-flex items-center gap-x-2 text-sm font-semibold rounded-lg border border-transparent text-blue-600 hover:text-blue-800 focus:outline-hidden focus:text-blue-800 disabled:opacity-50 disabled:pointer-events-none dark:text-blue-500 dark:hover:text-blue-400 dark:focus:text-blue-400"
                            @click="$emit('row-action', { action: 'delete', row })">
                            Delete
                        </button>
                        <span v-else class="text-gray-400 dark:text-neutral-600 text-xs">Delete disabled</span>
                    </td>
                </tr>
            </template>
        </tbody>
    </table>
</template>

<script setup>
// NUCLEAR OPTION: Completely disable attribute inheritance
defineOptions({
    inheritAttrs: false
});

import { inject } from 'vue';

/**
 * Component props definition
 */
const props = defineProps({
    tableColumns: {
        type: Array,
        required: true,
        default: () => [],
    },
    sortedData: {
        type: Array,
        required: true,
        default: () => [],
    },
    editingCell: {
        type: Object,
        default: null,
    },
    loading: {
        type: Boolean,
        default: false,
    },
    enableDelete: {
        type: Boolean,
        default: true,
    },
});

/**
 * Event emissions definition
 */
const emit = defineEmits([
    'sort',
    'cell-edit-start',
    'cell-edit',
    'row-action',
]);

// Inject functions from parent component with safe fallbacks
const getSortIndicator = inject('getSortIndicator', () => '');
const getAriaSort = inject('getAriaSort', () => 'none');
const handleKeydown = inject('handleKeydown', (event, row, column) => {
    if (event.key === 'Enter') {
        event.target.blur();
    } else if (event.key === 'Escape') {
        emit('cell-edit', {
            rowId: row.id,
            columnKey: column.key,
            newValue: row[column.key],
            oldValue: event.target.value,
        });
    }
});

const renderBadge = inject('renderBadge', (row, column) => ({
    label: String(row[column.key] || ''),
    class: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
}));

const enableDelete = inject('enableDelete', true);
</script>

<style scoped>
/* Enhanced hover effects */
tr {
    transition: background-color 0.2s ease-in-out;
}

/* Improved focus styles for accessibility */
button:focus {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
}

/* Smooth transitions for interactive elements */
th.cursor-pointer {
    transition: background-color 0.2s ease;
}

th.cursor-pointer:hover {
    background-color: #f8fafc;
}

.dark th.cursor-pointer:hover {
    background-color: #1e293b;
}

td.cursor-pointer {
    transition: background-color 0.2s ease;
}
</style>