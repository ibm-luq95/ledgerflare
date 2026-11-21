<template>
  <section class="w-full space-y-4">
    <!-- ------------------------------------------ -->
    <!-- 1. DISCUSSION MESSAGE STREAM CONTAINER     -->
    <!-- ------------------------------------------ -->
    <div
      ref="messagesContainer"
      class="overflow-y-auto max-h-[420px] sm:max-h-[480px] space-y-4 p-1 sm:p-2 pr-2 sm:pr-3 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-gray-200 dark:[&::-webkit-scrollbar-thumb]:bg-neutral-700 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-gray-300 dark:hover:[&::-webkit-scrollbar-thumb]:bg-neutral-600 transition-colors"
    >
      <!-- Initial Loading Placeholder (Skeleton) -->
      <MessageSkeleton v-if="isLoading" />

      <!-- Error State with Retry Button -->
      <div
        v-else-if="error"
        class="flex flex-col items-center justify-center py-8 px-4 text-center rounded-2xl border border-red-200 bg-red-50/50 dark:bg-red-900/10 dark:border-red-800"
      >
        <span class="flex items-center justify-center size-10 rounded-full bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 mb-2">
          <i class="fa-solid fa-triangle-exclamation text-base"></i>
        </span>
        <p class="text-xs text-red-600 dark:text-red-400 font-medium">{{ error }}</p>
        <button
          type="button"
          @click="() => fetchMessages(false)"
          class="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-red-300 text-red-700 hover:bg-red-50 dark:bg-neutral-900 dark:border-red-800 dark:text-red-300"
        >
          <i class="fa-solid fa-rotate-right text-xs"></i>
          Retry
        </button>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="messages.length === 0"
        class="flex flex-col items-center justify-center py-8 px-4 text-center rounded-2xl border border-dashed border-gray-200 dark:border-neutral-800"
      >
        <span class="flex items-center justify-center size-12 rounded-full bg-blue-50 text-blue-500 dark:bg-blue-900/30 dark:text-blue-400 mb-3">
          <i class="fa-regular fa-comments text-xl"></i>
        </span>
        <h4 class="text-sm font-semibold text-gray-800 dark:text-white">
          No discussions yet
        </h4>
        <p class="text-xs text-gray-500 dark:text-neutral-400 mt-1 max-w-sm">
          Start the conversation by posting an update or sharing instructions below.
        </p>
      </div>

      <!-- Message Bubbles Feed -->
      <template v-else>
        <MessageBubble
          v-for="msg in messages"
          :key="msg.id || msg.tempId"
          :message="msg"
          :current-user-id="currentUserId"
        />
      </template>
    </div>

    <!-- ------------------------------------------ -->
    <!-- 2. REACTIVE FLOATING COMPOSER DOCK         -->
    <!-- ------------------------------------------ -->
    <form @submit.prevent="sendMessage" class="pt-2">
      <fieldset :disabled="isSending" class="space-y-2.5">
        <div
          class="flex flex-col rounded-2xl border border-gray-200 bg-white shadow-xs p-2.5 sm:p-3 dark:bg-neutral-900 dark:border-neutral-800 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all"
        >
          <div class="flex items-end gap-2">
            <!-- Attachment File Trigger -->
            <label
              for="vue-chatbox-attachment"
              class="flex items-center justify-center size-9 rounded-xl text-gray-500 hover:text-blue-600 hover:bg-gray-100 dark:text-neutral-400 dark:hover:text-blue-400 dark:hover:bg-neutral-800 cursor-pointer transition-colors shrink-0 mb-0.5"
              title="Attach file"
            >
              <i class="fa-solid fa-paperclip text-sm"></i>
            </label>
            <input
              id="vue-chatbox-attachment"
              ref="fileInput"
              type="file"
              class="hidden"
              @change="onFileChange"
            />

            <!-- Auto-expanding Textarea / Composer Input -->
            <textarea
              v-model="messageText"
              rows="1"
              placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
              class="flex-1 bg-transparent border-0 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-neutral-500 focus:outline-hidden focus:ring-0 px-2 py-1.5 resize-none max-h-32 leading-relaxed"
              @keydown="handleKeydown"
            ></textarea>

            <!-- Send Button with Spinner -->
            <button
              type="submit"
              :disabled="(!messageText.trim() && !selectedFile) || isSending"
              class="inline-flex items-center justify-center gap-1.5 py-2 px-3.5 sm:px-4 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-xs sm:text-sm shadow-2xs focus:outline-hidden focus:bg-blue-700 transition-all shrink-0 mb-0.5"
            >
              <span v-if="isSending" class="inline-flex items-center">
                <i class="fa-solid fa-spinner fa-spin text-xs"></i>
              </span>
              <i v-else class="fa-solid fa-paper-plane text-xs"></i>
              <span class="hidden sm:inline">Send</span>
            </button>
          </div>

          <!-- Dynamic File Attachment Preview Tag -->
          <div
            v-if="selectedFile"
            class="flex items-center gap-1.5 px-2 pt-2 border-t border-gray-100 dark:border-neutral-800 mt-2 text-xs"
          >
            <span
              class="inline-flex items-center gap-1.5 py-1 px-2.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-200/60 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800/40"
            >
              <i class="fa-solid fa-file text-[11px]"></i>
              <span class="truncate max-w-[220px]">{{ selectedFile.name }}</span>
              <span class="text-[10px] text-blue-400">({{ formatFileSize(selectedFile.size) }})</span>
              <button
                type="button"
                @click="clearFile"
                class="ml-1 text-blue-500 hover:text-blue-700 dark:hover:text-blue-200"
              >
                <i class="fa-solid fa-xmark text-[10px]"></i>
              </button>
            </span>
          </div>
        </div>
      </fieldset>
    </form>
  </section>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import MessageSkeleton from './MessageSkeleton.vue';
import MessageBubble from './MessageBubble.vue';

const props = defineProps({
  objectId: {
    type: String,
    required: true,
  },
  objectType: {
    type: String,
    default: 'special_assignment', // 'special_assignment' or 'job'
  },
  currentUserId: {
    type: [String, Number],
    required: true,
  },
  currentUserName: {
    type: String,
    default: 'You',
  },
  currentUserAvatar: {
    type: String,
    default: '/static/img/default_staff.png',
  },
  apiEndpoint: {
    type: String,
    default: '/dashboard/discussions/api/discussion-api-router/',
  },
  csrfToken: {
    type: String,
    default: '',
  },
  pollInterval: {
    type: Number,
    default: 15000, // 15 seconds
  },
});

const messages = ref([]);
const isLoading = ref(true);
const isSending = ref(false);
const error = ref(null);
const messageText = ref('');
const selectedFile = ref(null);

const fileInput = ref(null);
const messagesContainer = ref(null);
let pollTimer = null;

const scrollToBottom = async (smooth = true) => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto',
    });
  }
};

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

const getCsrfToken = () => {
  if (props.csrfToken) return props.csrfToken;
  const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
  return cookieMatch ? cookieMatch[1] : '';
};

// ----------------------------------------------------
// FETCH MESSAGES (Async + Polling)
// ----------------------------------------------------
const fetchMessages = async (silent = false) => {
  if (!silent) isLoading.value = true;
  error.value = null;

  try {
    const url = new URL(props.apiEndpoint, window.location.origin);
    url.searchParams.set(props.objectType, props.objectId);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      credentials: 'same-origin',
    });

    if (!response.ok) {
      throw new Error(`Failed to load messages (${response.status})`);
    }

    const data = await response.json();
    const fetchedList = Array.isArray(data) ? data : data.results || [];

    // Sort ascending by created_at (newest at bottom)
    fetchedList.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

    const wasAtBottom = isUserNearBottom();
    messages.value = fetchedList;

    if (!silent || wasAtBottom) {
      await scrollToBottom(!silent ? false : true);
    }
  } catch (err) {
    if (!silent) {
      error.value = err.message || 'Unable to connect to discussion feed.';
    }
  } finally {
    if (!silent) isLoading.value = false;
  }
};

const isUserNearBottom = () => {
  if (!messagesContainer.value) return true;
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value;
  return scrollHeight - scrollTop - clientHeight < 120;
};

// ----------------------------------------------------
// SEND MESSAGE (Optimistic UI + FormData)
// ----------------------------------------------------
const sendMessage = async () => {
  const text = messageText.value.trim();
  const file = selectedFile.value;
  if (!text && !file) return;

  isSending.value = true;

  // Optimistic UI representation
  const tempId = `temp-${Date.now()}`;
  const optimisticItem = {
    tempId,
    body: text,
    sender: props.currentUserId,
    sender_name: props.currentUserName,
    sender_avatar: props.currentUserAvatar,
    created_at: new Date().toISOString(),
    attachment_name: file ? file.name : null,
    attachment_url: file ? URL.createObjectURL(file) : null,
    isPending: true,
  };

  messages.value.push(optimisticItem);
  messageText.value = '';
  clearFile();
  await scrollToBottom(true);

  try {
    const formData = new FormData();
    formData.append('body', text);
    formData.append(props.objectType, props.objectId);
    if (file) {
      formData.append('attachment', file);
    }

    const response = await fetch(props.apiEndpoint, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
      },
      body: formData,
      credentials: 'same-origin',
    });

    if (!response.ok) {
      throw new Error(`Error posting message (${response.status})`);
    }

    const savedRecord = await response.json();
    // Replace optimistic item with server saved item
    const idx = messages.value.findIndex((m) => m.tempId === tempId);
    if (idx !== -1) {
      messages.value[idx] = savedRecord;
    }
    await scrollToBottom(true);
  } catch (err) {
    // Remove failed optimistic message and restore text
    messages.value = messages.value.filter((m) => m.tempId !== tempId);
    messageText.value = text;
    alert(`Failed to send message: ${err.message}`);
  } finally {
    isSending.value = false;
  }
};

const handleKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};

const onFileChange = (event) => {
  const files = event.target.files;
  if (files && files.length > 0) {
    selectedFile.value = files[0];
  }
};

const clearFile = () => {
  selectedFile.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};

onMounted(() => {
  fetchMessages(false);
  if (props.pollInterval > 0) {
    pollTimer = setInterval(() => {
      fetchMessages(true);
    }, props.pollInterval);
  }
});

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
});
</script>
