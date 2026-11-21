<template>
  <div class="space-y-4 p-1 sm:p-2 animate-pulse">
    <!-- Message Left (Team Member Skeleton) -->
    <div class="flex items-start gap-3">
      <div class="size-9 rounded-full bg-gray-200 dark:bg-neutral-800 shrink-0"></div>
      <div class="space-y-2 max-w-[75%] w-64">
        <div class="flex items-center gap-2">
          <div class="h-3 w-20 bg-gray-200 dark:bg-neutral-800 rounded"></div>
          <div class="h-3 w-12 bg-gray-200 dark:bg-neutral-800 rounded"></div>
        </div>
        <div class="h-16 bg-gray-100 dark:bg-neutral-800/60 rounded-2xl rounded-tl-xs p-3"></div>
      </div>
    </div>

    <!-- Message Right (Current User Skeleton) -->
    <div class="flex flex-row-reverse items-start gap-3">
      <div class="size-9 rounded-full bg-blue-100 dark:bg-blue-950/50 shrink-0"></div>
      <div class="space-y-2 max-w-[75%] w-72 text-right">
        <div class="flex items-center justify-end gap-2">
          <div class="h-3 w-16 bg-gray-200 dark:bg-neutral-800 rounded"></div>
        </div>
        <div class="h-12 bg-blue-100 dark:bg-blue-900/30 rounded-2xl rounded-tr-xs"></div>
      </div>
    </div>

    <!-- Message Left (Another Member Skeleton) -->
    <div class="flex items-start gap-3">
      <div class="size-9 rounded-full bg-gray-200 dark:bg-neutral-800 shrink-0"></div>
      <div class="space-y-2 max-w-[75%] w-56">
        <div class="flex items-center gap-2">
          <div class="h-3 w-24 bg-gray-200 dark:bg-neutral-800 rounded"></div>
        </div>
        <div class="h-14 bg-gray-100 dark:bg-neutral-800/60 rounded-2xl rounded-tl-xs p-3"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Shimmer skeleton placeholder for discussion message stream
</script>
