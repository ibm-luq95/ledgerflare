<template>
  <div>
    <!-- ---------------------------------------- -->
    <!-- CURRENT USER MESSAGE (Right Aligned)     -->
    <!-- ---------------------------------------- -->
    <div v-if="isCurrentUser" class="flex flex-row-reverse items-start gap-3">
      <img
        :src="message.sender_avatar || '/static/img/default_staff.png'"
        :alt="message.sender_name || 'You'"
        class="size-9 rounded-full object-cover shrink-0 border border-blue-200 dark:border-blue-800"
        @error="onAvatarError"
      />

      <div class="max-w-[85%] sm:max-w-[75%] space-y-1 text-right">
        <div class="flex items-center justify-end gap-2 text-xs text-gray-500 dark:text-neutral-400">
          <span class="font-medium text-gray-900 dark:text-neutral-200">You</span>
          <span v-if="message.isPending" class="text-[10px] text-blue-500 inline-flex items-center gap-1">
            <i class="fa-solid fa-spinner fa-spin text-[9px]"></i> Sending...
          </span>
          <span v-else class="text-[11px] text-gray-400 dark:text-neutral-500">
            {{ formatTime(message.created_at) }}
          </span>
        </div>

        <div
          class="inline-block text-left bg-blue-600 text-white p-3.5 sm:p-4 rounded-2xl rounded-tr-xs shadow-2xs transition-opacity"
          :class="{ 'opacity-70': message.isPending }"
        >
          <div class="text-sm font-normal leading-relaxed break-words whitespace-pre-wrap">
            {{ message.body }}
          </div>

          <!-- Attachment Pill -->
          <div v-if="message.attachment_url" class="mt-2.5 pt-2.5 border-t border-blue-500/60">
            <a
              :href="message.attachment_url"
              :download="message.attachment_name || 'attachment'"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-2 py-1.5 px-3 rounded-lg bg-blue-700/80 hover:bg-blue-700 text-white text-xs font-medium transition-colors"
            >
              <i class="fa-solid fa-paperclip text-[11px]"></i>
              <span class="truncate max-w-[180px]">{{ message.attachment_name || 'Attachment' }}</span>
              <i class="fa-solid fa-download text-[10px] ml-1 opacity-80"></i>
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- ---------------------------------------- -->
    <!-- TEAM MEMBER MESSAGE (Left Aligned)       -->
    <!-- ---------------------------------------- -->
    <div v-else class="flex items-start gap-3">
      <img
        :src="message.sender_avatar || '/static/img/default_staff.png'"
        :alt="message.sender_name || 'Team Member'"
        class="size-9 rounded-full object-cover shrink-0 border border-gray-200 dark:border-neutral-700"
        @error="onAvatarError"
      />

      <div class="max-w-[85%] sm:max-w-[75%] space-y-1">
        <div class="flex flex-wrap items-center gap-2 text-xs">
          <span class="font-bold text-gray-900 dark:text-white">
            {{ message.sender_name || 'Team Member' }}
          </span>
          <span
            v-if="message.sender_user_type"
            class="py-0.5 px-2 rounded-md text-[10px] font-semibold bg-gray-100 text-gray-700 dark:bg-neutral-800 dark:text-neutral-300 capitalize"
          >
            {{ message.sender_user_type }}
          </span>
          <span class="text-[11px] text-gray-400 dark:text-neutral-500">
            {{ formatTime(message.created_at) }}
          </span>
        </div>

        <div class="bg-gray-50 border border-gray-200/80 p-3.5 sm:p-4 rounded-2xl rounded-tl-xs shadow-2xs dark:bg-neutral-800/80 dark:border-neutral-700/60 text-gray-800 dark:text-neutral-200">
          <div class="text-sm font-normal leading-relaxed break-words whitespace-pre-wrap">
            {{ message.body }}
          </div>

          <!-- Attachment Pill -->
          <div v-if="message.attachment_url" class="mt-2.5 pt-2.5 border-t border-gray-200 dark:border-neutral-700">
            <a
              :href="message.attachment_url"
              :download="message.attachment_name || 'attachment'"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-2 py-1.5 px-3 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 text-gray-800 text-xs font-medium shadow-2xs dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-200 dark:hover:bg-neutral-800 transition-colors"
            >
              <i class="fa-solid fa-paperclip text-blue-500 text-[11px]"></i>
              <span class="truncate max-w-[180px]">{{ message.attachment_name || 'Attachment' }}</span>
              <i class="fa-solid fa-download text-[10px] text-gray-400 ml-1"></i>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
  currentUserId: {
    type: [String, Number],
    required: true,
  },
});

const isCurrentUser = computed(() => {
  if (!props.message) return false;
  const msgSender = String(props.message.sender || props.message.sender_id || '');
  const currUser = String(props.currentUserId || '');
  return Boolean(msgSender && currUser && msgSender === currUser);
});

const formatTime = (dateStr) => {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (e) {
    return dateStr;
  }
};

const onAvatarError = (event) => {
  event.target.src = '/static/img/default_staff.png';
};
</script>
