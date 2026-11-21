<template>
  <div
    class="hs-dropdown relative inline-flex w-full ml-3 max-w-[280px] xs:max-w-[320px] sm:max-w-[350px] lg:max-w-[450px]"
    style="overflow: visible"
  >
    <button
      type="button"
      class="hs-dropdown-toggle w-full py-2.5 px-3 sm:px-4 flex items-center justify-between border border-gray-200 rounded-lg text-sm bg-white text-gray-700 hover:bg-gray-50 dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
      @click="toggleDropdown"
      aria-haspopup="menu"
      :aria-expanded="isOpen"
      aria-label="Select client"
    >
      <div v-if="selectedClient" class="flex items-center gap-3 flex-1 min-w-0">
        <div class="flex-shrink-0">
          <img
            v-if="selectedClient.logo_url && selectedClient.logo_url.trim()"
            :src="selectedClient.logo_url"
            :alt="selectedClient.name"
            class="w-8 h-8 rounded-lg object-cover"
            @error="handleLogoError"
          />
          <div
            v-else
            class="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 flex items-center justify-center text-sm font-semibold"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
        </div>
        <div class="flex flex-col min-w-0 flex-1">
          <span class="text-sm font-medium truncate text-left">{{
            selectedClient.name
          }}</span>
          <span
            v-if="selectedClient.email"
            class="text-xs text-gray-500 dark:text-neutral-400 truncate text-left"
            >{{ selectedClient.email }}</span
          >
        </div>
      </div>
      <div v-else class="flex items-center gap-3 flex-1">
        <div
          class="w-8 h-8 rounded-lg bg-gray-100 text-gray-400 dark:bg-neutral-700 dark:text-neutral-500 flex items-center justify-center"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
        </div>
        <span class="text-sm text-gray-500 dark:text-neutral-400"
          >Select Client</span
        >
      </div>
      <svg
        class="w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>

    <div
      v-show="isOpen"
      id="client-dropdown-menu"
      ref="dropdownMenu"
      class="hs-dropdown-menu transition-[opacity,margin] duration hs-dropdown-open:opacity-100 opacity-0 min-w-full xs:min-w-[320px] sm:min-w-[350px] lg:min-w-[450px] max-h-[400px] overflow-y-auto bg-white shadow-xl rounded-lg dark:bg-neutral-800 dark:border dark:border-neutral-700"
      role="menu"
      aria-orientation="vertical"
      @click.stop
    >
      <div
        class="sticky top-0 p-3 border-b border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 z-10 rounded-t-lg"
      >
        <div class="relative">
          <input
            ref="searchInput"
            v-model="searchQuery"
            type="text"
            placeholder="Search clients..."
            class="w-full py-2 px-3 pl-9 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-neutral-700 dark:border-neutral-600 dark:text-neutral-100 dark:placeholder-neutral-400"
            @keydown.esc="closeDropdown"
            @keydown.arrow-down.prevent="focusFirstResult"
          />
          <svg
            class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      <div class="overflow-y-auto max-h-[340px]">
        <div v-if="isLoading" class="p-4 space-y-3">
          <div
            v-for="i in 3"
            :key="i"
            class="flex items-center gap-3 animate-pulse"
          >
            <div
              class="w-10 h-10 bg-gray-200 dark:bg-neutral-700 rounded-lg"
            ></div>
            <div class="flex-1 space-y-2">
              <div
                class="h-4 bg-gray-200 dark:bg-neutral-700 rounded w-3/4"
              ></div>
              <div
                class="h-3 bg-gray-200 dark:bg-neutral-700 rounded w-1/2"
              ></div>
            </div>
          </div>
        </div>

        <div v-else-if="error" class="p-6 text-center">
          <svg
            class="w-12 h-12 text-red-400 mx-auto mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p class="text-red-500 dark:text-red-400 text-sm mb-3">{{ error }}</p>
          <button
            @click="fetchClients"
            class="inline-flex items-center gap-2 py-2 px-4 text-sm font-medium rounded-lg border border-transparent bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50"
          >
            Retry
          </button>
        </div>

        <div
          v-else-if="filteredClients.length === 0 && hasLoaded"
          class="p-6 text-center"
        >
          <svg
            class="w-12 h-12 text-gray-400 mx-auto mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p class="text-gray-500 dark:text-neutral-400 text-sm">
            {{
              searchQuery
                ? "No clients match your search"
                : "No clients available"
            }}
          </p>
        </div>

        <div v-else class="py-2">
          <div
            v-for="(client, index) in filteredClients"
            :key="client.id"
            ref="clientItems"
            :tabindex="isOpen ? 0 : -1"
            role="menuitem"
            class="px-4 py-3 cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-neutral-700 focus:bg-blue-50 dark:focus:bg-blue-900/20 focus:outline-none"
            :class="{
              'bg-blue-50 dark:bg-blue-900/20': client.id === currentClientId,
            }"
            @click="handleClientClick(client)"
            @keydown.enter="handleClientClick(client)"
            @keydown.arrow-up.prevent="focusPrevious(index)"
            @keydown.arrow-down.prevent="focusNext(index)"
          >
            <div class="flex items-center gap-3">
              <div class="flex-shrink-0">
                <img
                  v-if="client.logo_url && client.logo_url.trim()"
                  :src="client.logo_url"
                  :alt="client.name"
                  class="w-10 h-10 rounded-lg object-cover"
                  @error="handleLogoError($event, client)"
                />
                <div
                  v-else
                  class="w-10 h-10 rounded-lg bg-gray-100 text-gray-600 dark:bg-neutral-700 dark:text-neutral-300 flex items-center justify-center text-sm font-semibold"
                >
                  <svg
                    class="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                    />
                  </svg>
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <p
                  class="text-sm font-medium text-gray-900 dark:text-neutral-100 truncate"
                >
                  {{ client.name }}
                </p>
                <p class="text-xs text-gray-500 dark:text-neutral-400 truncate">
                  {{ client.email || "No email" }}
                </p>
              </div>
              <svg
                v-if="client.id === currentClientId"
                class="w-5 h-5 text-blue-500 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, nextTick, watch } from "vue";
import Swal from "sweetalert2";

const props = defineProps({
  apiEndpoint: { type: String, default: "/dashboard/client/api/dropdown/" },
  currentClientId: { type: [String, Number], default: null },
  currentClientName: { type: String, default: "" },
  currentClientEmail: { type: String, default: "" },
  currentClientLogo: { type: String, default: "" },
});

const emit = defineEmits(["client-selected", "loading", "error", "loaded"]);

const clients = ref([]);
const isLoading = ref(false);
const isOpen = ref(false);
const error = ref(null);
const hasLoaded = ref(false);
const searchQuery = ref("");
const selectedClient = ref(null);
const dropdownMenu = ref(null);
const searchInput = ref(null);
const clientItems = ref([]);

// Set initial selected client if current client data is provided
if (props.currentClientId && props.currentClientName) {
  // Build absolute logo URL if relative
  let logoUrl = props.currentClientLogo || "";
  if (
    logoUrl &&
    !logoUrl.startsWith("http") &&
    !logoUrl.startsWith("/static")
  ) {
    logoUrl = window.location.origin + logoUrl;
  }

  selectedClient.value = {
    id: props.currentClientId,
    name: props.currentClientName,
    email: props.currentClientEmail || "",
    logo_url: logoUrl,
    dashboard_url: `/client-accounting/dashboard/${props.currentClientId}`,
  };
}

const filteredClients = computed(() => {
  if (!searchQuery.value.trim()) return clients.value;
  const query = searchQuery.value.toLowerCase().trim();
  return clients.value.filter(
    (client) =>
      client.name.toLowerCase().includes(query) ||
      (client.email && client.email.toLowerCase().includes(query)),
  );
});

const fetchClients = async () => {
  isLoading.value = true;
  error.value = null;
  emit("loading", true);
  try {
    const response = await fetch(props.apiEndpoint, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();

    // Convert relative logo URLs to absolute URLs
    clients.value = data.map((client) => {
      if (
        client.logo_url &&
        !client.logo_url.startsWith("http") &&
        !client.logo_url.startsWith("/static")
      ) {
        client.logo_url = window.location.origin + client.logo_url;
      }
      return client;
    });

    hasLoaded.value = true;
    emit("loaded", data);
    if (data.length === 0) await showToast("warning", "No clients available");
  } catch (err) {
    error.value = "Failed to load clients. Please try again.";
    emit("error", err);
    await showToast("error", error.value);
  } finally {
    isLoading.value = false;
    emit("loading", false);
  }
};

const toggleDropdown = async () => {
  isOpen.value = !isOpen.value;
  if (isOpen.value) await openDropdown();
};

const openDropdown = async () => {
  if (!hasLoaded.value && !isLoading.value) await fetchClients();
  await nextTick();
  positionDropdown();
  if (searchInput.value) searchInput.value.focus();
};

const positionDropdown = () => {
  if (!dropdownMenu.value) return;
  const trigger = document.querySelector(".hs-dropdown-toggle");
  if (!trigger) return;
  const triggerRect = trigger.getBoundingClientRect();
  dropdownMenu.value.style.position = "absolute";
  dropdownMenu.value.style.zIndex = "9999";
  dropdownMenu.value.style.top = "100%";
  dropdownMenu.value.style.left = "0";
  dropdownMenu.value.style.right = "0";
  dropdownMenu.value.style.margin = "8px 0 0 0";
  dropdownMenu.value.style.width = "auto";
};

const closeDropdown = () => {
  isOpen.value = false;
  searchQuery.value = "";
};

const handleLogoError = (event, client = null) => {
  // Hide the broken image and show fallback
  if (event.target) {
    event.target.style.display = "none";
  }
  // Clear the logo_url so fallback shows
  if (client) {
    client.logo_url = null;
  } else if (selectedClient.value) {
    selectedClient.value.logo_url = null;
  }
};

const handleClientClick = (client) => {
  selectedClient.value = client;
  closeDropdown();
  // Build dashboard URL matching Django URL pattern: client-accounting:dashboard
  const dashboardUrl = `/client-accounting/dashboard/${client.id}`;
  const eventData = { client, url: dashboardUrl };
  emit("client-selected", eventData);
  const customEvent = new CustomEvent("client-selected", {
    detail: eventData,
    bubbles: true,
  });
  if (dropdownMenu.value) dropdownMenu.value.dispatchEvent(customEvent);
};

const focusFirstResult = async () => {
  await nextTick();
  if (clientItems.value.length > 0 && clientItems.value[0])
    clientItems.value[0].focus();
};

const focusPrevious = (index) => {
  const prev = index > 0 ? index - 1 : filteredClients.value.length - 1;
  if (clientItems.value[prev]) clientItems.value[prev].focus();
};

const focusNext = (index) => {
  const next = index < filteredClients.value.length - 1 ? index + 1 : 0;
  if (clientItems.value[next]) clientItems.value[next].focus();
};

const showToast = async (icon, title) => {
  await Swal.fire({
    toast: true,
    position: "top-end",
    icon,
    title,
    showConfirmButton: false,
    timer: 5000,
    timerProgressBar: true,
    zIndex: 10000,
  });
};

const handleClickOutside = (event) => {
  if (
    isOpen.value &&
    dropdownMenu.value &&
    !dropdownMenu.value.contains(event.target) &&
    !event.target.closest(".hs-dropdown-toggle")
  ) {
    closeDropdown();
  }
};

watch(isOpen, (newValue) => {
  if (newValue) {
    document.addEventListener("click", handleClickOutside);
  } else {
    document.removeEventListener("click", handleClickOutside);
  }
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>

<style scoped>
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 3px;
}
.dark .overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: #475569;
}
</style>
