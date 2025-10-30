<template>
    <div id="app">
        <MyDataTable :data="users" :columns="columns" :show-top-card="true" :top-card-title="'Advanced User Management'"
            :top-card-description="'Complete control over your user database'" :top-card-actions="topCardActions"
            :enable-delete="true" @row-action="handleRowAction" @top-card-action="handleTopCardAction" />
    </div>
</template>

<script setup>
import { ref } from 'vue';
import MyDataTable from './MyDataTable.vue';

const users = ref([
    { id: 1, name: 'John Doe', email: 'john@example.com', status: 'active' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'pending' },
    { id: 3, name: 'Mike Johnson', email: 'mike@example.com', status: 'inactive' },
]);

const columns = ref([
    {
        key: 'name',
        label: 'Full Name',
        sortable: true,
        editable: true,
        type: 'text'
    },
    {
        key: 'email',
        label: 'Email Address',
        sortable: true,
        editable: true,
        type: 'text'
    },
    {
        key: 'status',
        label: 'Status',
        sortable: true,
        type: 'badge',
        badgeMap: {
            active: {
                label: 'Active',
                class: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
            },
            pending: {
                label: 'Pending',
                class: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
            },
            inactive: {
                label: 'Inactive',
                class: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
            }
        }
    }
]);

const loading = ref(false);

// Event handlers
const handleSort = (sortData) => {
    console.log('Sort changed:', sortData);
};

const handleCellEdit = (editData) => {
    console.log('Cell edited:', editData);
    // Update your data store here
    const userIndex = users.value.findIndex(u => u.id === editData.rowId);
    if (userIndex !== -1) {
        users.value[userIndex][editData.column] = editData.newValue;
    }
};

const handleRowAction = (actionData) => {
    console.log('Row action:', actionData);
    if (actionData.action === 'delete') {
        users.value = users.value.filter(u => u.id !== actionData.row.id);
    }
};
const addUser = () => {
    console.log('Add user clicked');
    // Your add user logic
};

const exportData = () => {
    console.log('Export data clicked');
    // Your export logic
};

const refreshData = () => {
    console.log('Refresh data clicked');
    // Your refresh logic
};

const topCardActions = [
    {
        label: 'Add User',
        classes: 'py-2.5 px-4 inline-flex items-center gap-x-2 text-sm font-medium rounded-lg border border-transparent bg-green-100 text-green-800 hover:bg-green-200 focus:outline-hidden focus:bg-green-200 dark:text-green-400 dark:bg-green-800/30 dark:hover:bg-green-800/20',
        handler: addUser,
        icon: '<svg class="flex-shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    },
    {
        label: 'Export Data',
        classes: 'py-2.5 px-4 inline-flex items-center gap-x-2 text-sm font-medium rounded-lg border border-gray-200 bg-white text-gray-800 hover:bg-gray-50 focus:outline-hidden focus:bg-gray-50 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700',
        handler: exportData,
        icon: '<svg class="flex-shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>',
    },
    {
        label: 'Refresh',
        classes: 'py-2.5 px-4 inline-flex items-center gap-x-2 text-sm font-medium rounded-lg border border-transparent bg-blue-100 text-blue-800 hover:bg-blue-200 focus:outline-hidden focus:bg-blue-200 dark:text-blue-400 dark:bg-blue-800/30 dark:hover:bg-blue-800/20',
        handler: refreshData,
        icon: '<svg class="flex-shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9v-9m0-9v9"/></svg>',
    }
];
</script>

<style>
#app {
    font-family: Avenir, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: center;
    color: #2c3e50;
    margin-top: 60px;
}
</style>
