"use strict";

import { SecureUrlFetcher } from "../../utils/apis/fetch_by_name.js";
import { RequestHandler } from "../../utils/apis/request_handler.js";
import Chart from "chart.js/auto";

/**
 * LedgerFlare Manager Dashboard Widget Loader
 *
 * Handles AJAX loading of dashboard widgets for the Manager role.
 * Loads KPI stats, tables, and charts from API endpoints.
 */
class LFManagerDashboardLoader {
  constructor() {
    /**
     * Widget configuration
     * Each widget has:
     * - urlName: Django URL name for fetching the endpoint
     * - elementIds: IDs of elements to update (for KPIs)
     * - containerId: ID of container to render into (for tables/charts)
     * - chartId: ID of canvas element (for charts)
     */
    this.widgets = {
      kpiStats: {
        urlName: "dashboard:manager:kpi-stats",
        elementIds: {
          staff: "mgTotalStaffMembers",
          clients: "mgTotalClients",
          jobs: "mgTotalJobs",
          assignments: "mgTotalAssignments",
          pastDue: "lfPastDueJobs",
          completionRate: "lfJobCompletionRate",
          tasksThisWeek: "lfTasksDueThisWeek",
          jobsNeedInfo: "lfJobsNeedInfo",
        },
      },
      pastDueJobsTable: {
        urlName: "dashboard:manager:past-due-jobs",
        containerId: "lfPastDueJobsTableContainer",
      },
      tasksThisWeekTable: {
        urlName: "dashboard:manager:tasks-this-week",
        containerId: "lfTasksThisWeekTableContainer",
      },
      staffWorkloadChart: {
        urlName: "dashboard:manager:staff-workload",
        chartId: "lfStaffWorkloadChart",
        containerId: "lfStaffWorkloadChartContainer",
      },
    };

    // Chart instances to keep track of for updates
    this.chartInstances = {};

    // Store resize handler reference to prevent memory leaks
    this.resizeHandler = null;
  }

  /**
   * Initialize all widgets
   * Called when DOM is ready
   */
  async initialize() {
    console.log("[LFManagerDashboardLoader] Initializing dashboard widgets...");

    // Load all widgets in parallel for better performance
    await Promise.all([
      this.loadKPIStats(),
      this.loadPastDueJobsTable(),
      this.loadTasksThisWeekTable(),
      this.loadStaffWorkloadChart(),
    ]);

    console.log("[LFManagerDashboardLoader] All widgets loaded");
  }

  /**
   * Load KPI Stats from API and update all KPI elements
   */
  async loadKPIStats() {
    try {
      const urlData = await SecureUrlFetcher.fetchUrlPathByName(
        this.widgets.kpiStats.urlName,
      );

      const data = await RequestHandler.sendRequest({
        url: urlData.urlPath,
        method: "GET",
        djangoRequest: true,
        debug: true,
      });

      console.log("[LFManagerDashboardLoader] KPI Stats loaded:", data);

      // Update each KPI element
      Object.entries(this.widgets.kpiStats.elementIds).forEach(
        ([key, elementId]) => {
          const element = document.getElementById(elementId);
          if (element) {
            const loader = element.querySelector(".loader-element");
            if (loader) loader.classList.add("hidden");

            // Format value based on type
            let value = "0";
            switch (key) {
              case "completionRate":
                value = `${data["job_completion_rate"] || "0"}%`;
                break;
              case "pastDue":
                value = data["past_due_jobs_count"] || "0";
                // Add alert styling if there are past due jobs
                if (data["past_due_jobs_count"] > 0) {
                  element
                    .closest(".bg-white")
                    ?.classList.add("border-l-4", "border-l-red-500");
                }
                break;
              case "tasksThisWeek":
                value = data["tasks_not_completed_count"] || "0";
                break;
              case "jobsNeedInfo":
                value = data["jobs_need_info_count"] || "0";
                break;
              default:
                value = data[`${key}_count`] || "0";
                break;
            }

            element.textContent = value;
          }
        },
      );
    } catch (error) {
      console.error(
        "[LFManagerDashboardLoader] Failed to load KPI stats:",
        error,
      );
    }
  }

  /**
   * Load Past Due Jobs Table
   */
  async loadPastDueJobsTable() {
    try {
      const urlData = await SecureUrlFetcher.fetchUrlPathByName(
        this.widgets.pastDueJobsTable.urlName,
      );

      const data = await RequestHandler.sendRequest({
        url: urlData.urlPath,
        method: "GET",
        djangoRequest: true,
        debug: true,
      });

      console.log("[LFManagerDashboardLoader] Past Due Jobs loaded:", data);

      const container = document.getElementById(
        this.widgets.pastDueJobsTable.containerId,
      );

      if (!container) {
        console.warn(
          "[LFManagerDashboardLoader] Container not found:",
          this.widgets.pastDueJobsTable.containerId,
        );
        return;
      }

      if (data.count === 0) {
        this.renderEmptyState(
          container,
          "No past due jobs",
          "All jobs are on track!",
          "fa-check-circle",
        );
      } else {
        this.renderPastDueJobsTable(container, data);
      }
    } catch (error) {
      console.error(
        "[LFManagerDashboardLoader] Failed to load past due jobs:",
        error,
      );
      const container = document.getElementById(
        this.widgets.pastDueJobsTable.containerId,
      );
      if (container) {
        this.renderErrorState(container, "Failed to load past due jobs");
      }
    }
  }

  /**
   * Render Past Due Jobs Table with Preline Card (Compact Dashboard Widget)
   */
  renderPastDueJobsTable(container, data) {
    const getUrgencyLevel = (days) => {
      if (days >= 14)
        return { class: "bg-red-500 text-white", label: "Critical" };
      if (days >= 7)
        return { class: "bg-orange-500 text-white", label: "High" };
      return { class: "bg-yellow-500 text-white", label: "Medium" };
    };

    const rows = data.data
      .map((job, index) => {
        const urgency = getUrgencyLevel(job.days_overdue);
        return `
        <tr class="group hover:bg-gray-50 dark:hover:bg-neutral-800/50 transition-colors duration-200">
          <td class="px-4 py-3 whitespace-nowrap">
            <div class="flex items-center space-x-3">
              <div class="flex-shrink-0">
                <div class="w-7 h-7 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                  <i class="fas fa-file-alt text-xs text-red-600 dark:text-red-400"></i>
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <a href="${job.url}"
                   class="text-sm font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-200 block truncate"
                   title="View job details: ${job.title}">
                  ${job.title.length > 25 ? job.title.slice(0, 25) + "..." : job.title}
                </a>
              </div>
            </div>
          </td>
          <td class="px-4 py-3 whitespace-nowrap">
            <span class="text-sm text-gray-900 dark:text-gray-100 truncate block" style="max-width: 100px;">${job.client_name}</span>
          </td>
          <td class="px-4 py-3 whitespace-nowrap">
            <div class="flex items-center space-x-2">
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${urgency.class} flex-shrink-0">
                <i class="fas fa-exclamation-triangle mr-1 text-xs"></i>
                ${job.days_overdue} days
              </span>
            </div>
          </td>
        </tr>
      `;
      })
      .join("");

    container.innerHTML = `

      <!-- Card -->
      <div class="flex flex-col bg-white border border-gray-200 rounded-xl shadow-sm dark:bg-neutral-900 dark:border-neutral-800 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
          <!-- Card Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="flex items-center justify-center w-8 h-8 bg-red-50 rounded-lg dark:bg-red-900/20">
                <i class="fas fa-exclamation-circle text-red-600 dark:text-red-400"></i>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                  Past Due Jobs
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  ${data.count} job${data.count !== 1 ? "s" : ""} requiring attention
                </p>
              </div>
            </div>
            <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
              <i class="fas fa-bell mr-1 animate-pulse"></i>
              Action Required
            </span>
          </div>
        </div>

        <!-- Table -->
        <div class="flex-1 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-neutral-700" role="table" aria-label="Past due jobs table">
              <thead class="bg-gray-50 dark:bg-neutral-800/50">
                <tr>
                  <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Job
                  </th>
                  <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Client
                  </th>
                  <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Overdue
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white dark:bg-neutral-900 divide-y divide-gray-200 dark:divide-neutral-700" role="rowgroup">
                ${rows}
              </tbody>
            </table>
          </div>

          <!-- Card Footer -->
          <div class="px-6 py-3 border-t border-gray-200 dark:border-neutral-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <span>Showing ${Math.min(data.count, 10)} of ${data.count} past due jobs</span>
              </div>
              <a class="inline-flex items-center gap-x-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
                 href="/dashboard/jobs/?status=past_due"
                 title="View all past due jobs">
                View All Jobs
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>
      <!-- End Card -->
    `;
  }

  /**
   * Load Tasks Due This Week Table
   */
  async loadTasksThisWeekTable() {
    try {
      const urlData = await SecureUrlFetcher.fetchUrlPathByName(
        this.widgets.tasksThisWeekTable.urlName,
      );

      const data = await RequestHandler.sendRequest({
        url: urlData.urlPath,
        method: "GET",
        djangoRequest: true,
        debug: true,
      });

      console.log("[LFManagerDashboardLoader] Tasks This Week loaded:", data);

      const container = document.getElementById(
        this.widgets.tasksThisWeekTable.containerId,
      );

      if (!container) {
        console.warn(
          "[LFManagerDashboardLoader] Container not found:",
          this.widgets.tasksThisWeekTable.containerId,
        );
        return;
      }

      if (data.count === 0) {
        this.renderEmptyState(
          container,
          "No tasks due this week",
          "All caught up!",
          "fa-calendar-check",
        );
      } else {
        this.renderTasksThisWeekTable(container, data);
      }
    } catch (error) {
      console.error(
        "[LFManagerDashboardLoader] Failed to load tasks this week:",
        error,
      );
      const container = document.getElementById(
        this.widgets.tasksThisWeekTable.containerId,
      );
      if (container) {
        this.renderErrorState(container, "Failed to load tasks");
      }
    }
  }

  /**
   * Render Tasks This Week Table with Preline Card (Compact Dashboard Widget)
   */
  renderTasksThisWeekTable(container, data) {
    const getStatusInfo = (status) => {
      const statusMap = {
        IN_PROGRESS: {
          class:
            "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
          icon: "fa-spinner",
          label: "In Progress",
        },
        PENDING: {
          class:
            "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
          icon: "fa-clock",
          label: "Pending",
        },
        COMPLETED: {
          class:
            "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
          icon: "fa-check-circle",
          label: "Completed",
        },
        REVIEW: {
          class:
            "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
          icon: "fa-eye",
          label: "Under Review",
        },
      };
      return statusMap[status] || statusMap.PENDING;
    };

    const rows = data.data
      .map((task, index) => {
        const statusInfo = getStatusInfo(task.status);

        return `
        <tr class="group hover:bg-gray-50 dark:hover:bg-neutral-800/50 transition-colors duration-200">
          <td class="px-4 py-3 whitespace-nowrap">
            <div class="flex items-center space-x-3">
              <div class="flex-shrink-0">
                <div class="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <i class="fas ${statusInfo.icon} text-xs text-blue-600 dark:text-blue-400"></i>
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <a href="${task.url}" 
                   class="text-sm font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-200 block truncate"
                   title="View task details: ${task.title}">
                  ${task.title.slice(0, 25)}...
                </a>
              </div>
            </div>
          </td>
          <td class="px-4 py-3 whitespace-nowrap">
            <div class="flex items-center space-x-2">
              <div class="w-5 h-5 rounded bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center flex-shrink-0">
                <svg class="w-2.5 h-2.5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
              </div>
              <span class="text-sm text-gray-900 dark:text-gray-100 truncate" style="max-width: 120px;">${task.job_title.slice(0, 20)}...</span>
            </div>
          </td>
          <td class="px-4 py-3 whitespace-nowrap">
            <span class="text-sm text-gray-900 dark:text-gray-100 truncate block" style="max-width: 100px;">${task.client_name}</span>
          </td>
          <td class="px-4 py-3 whitespace-nowrap">
            <div class="flex items-center space-x-2">
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusInfo.class} flex-shrink-0">
                <i class="fas ${statusInfo.icon} mr-1 text-xs"></i>
                ${statusInfo.label}
              </span>
              ${
                task.assigned_to
                  ? `
                <div class="w-4 h-4 rounded-full bg-blue-500 border border-white dark:border-gray-800 flex items-center justify-center flex-shrink-0">
                  <span class="text-[10px] text-white font-medium leading-none">${task.assigned_to.charAt(0).toUpperCase()}</span>
                </div>
              `
                  : ""
              }
            </div>
          </td>
        </tr>
      `;
      })
      .join("");

    container.innerHTML = /*html*/ `

      <!-- Card -->
      <div class="flex flex-col bg-white border border-gray-200 rounded-xl shadow-sm dark:bg-neutral-900 dark:border-neutral-800 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
          <!-- Card Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="flex items-center justify-center w-8 h-8 bg-blue-50 rounded-lg dark:bg-blue-900/20">
                <i class="fas fa-tasks text-blue-600 dark:text-blue-400"></i>
              </div>
              <div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                  Tasks This Week
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  ${data.count} task${data.count !== 1 ? "s" : ""} due this week
                </p>
              </div>
            </div>
            <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
              This Week
            </span>
          </div>
        </div>

        <!-- Table -->
        <div class="flex-1 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-neutral-700" role="table" aria-label="Tasks due this week table">
              <thead class="bg-gray-50 dark:bg-neutral-800/50">
                <tr>
                  <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Task
                  </th>
                  <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Job
                  </th>
                  <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Client
                  </th>
                  <th scope="col" class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white dark:bg-neutral-900 divide-y divide-gray-200 dark:divide-neutral-700" role="rowgroup">
                ${rows}
              </tbody>
            </table>
          </div>

          <!-- Card Footer -->
          <div class="px-6 py-3 border-t border-gray-200 dark:border-neutral-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <span>Showing ${Math.min(data.count, 10)} of ${data.count} tasks</span>
              </div>
              <a class="inline-flex items-center gap-x-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
                 href="/dashboard/task/?status=past_due"
                 title="View all tasks">
                View All Tasks
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>
      <!-- End Card -->
    `;
  }

  /**
   * Load Staff Workload Chart
   */
  async loadStaffWorkloadChart() {
    try {
      const urlData = await SecureUrlFetcher.fetchUrlPathByName(
        this.widgets.staffWorkloadChart.urlName,
      );

      const data = await RequestHandler.sendRequest({
        url: urlData.urlPath,
        method: "GET",
        djangoRequest: true,
        debug: true,
      });

      console.log("[LFManagerDashboardLoader] Staff Workload loaded:", data);

      const canvas = document.getElementById(
        this.widgets.staffWorkloadChart.chartId,
      );

      if (!canvas) {
        console.warn(
          "[LFManagerDashboardLoader] Canvas not found:",
          this.widgets.staffWorkloadChart.chartId,
        );
        return;
      }

      // Hide loader and show chart container
      const container = document.getElementById(
        this.widgets.staffWorkloadChart.containerId,
      );
      if (container) {
        const loaderContainer = container.querySelector(".loader-container");
        const chartContainer = container.querySelector(".chart-container");
        if (loaderContainer) loaderContainer.classList.add("hidden");
        if (chartContainer) chartContainer.classList.remove("hidden");
      }

      if (!data.labels || data.labels.length === 0) {
        // Hide chart container and show empty state
        if (container) {
          const chartContainer = container.querySelector(".chart-container");
          if (chartContainer) chartContainer.classList.add("hidden");
          this.renderEmptyState(
            container,
            "No staff data available",
            "Add bookkeepers to see workload",
            "fa-users",
          );
        }
        return;
      }

      // Destroy existing chart if it exists
      if (this.chartInstances.staffWorkload) {
        this.chartInstances.staffWorkload.destroy();
        this.chartInstances.staffWorkload = null;
      }

      // Clean up existing resize handler to prevent memory leaks
      if (this.resizeHandler) {
        window.removeEventListener("resize", this.resizeHandler);
        this.resizeHandler = null;
      }

      this.renderStaffWorkloadChart(canvas, data);
    } catch (error) {
      console.error(
        "[LFManagerDashboardLoader] Failed to load staff workload:",
        error,
      );
      const container = document.getElementById(
        this.widgets.staffWorkloadChart.containerId,
      );
      if (container) {
        // Hide loader and chart containers
        const loaderContainer = container.querySelector(".loader-container");
        const chartContainer = container.querySelector(".chart-container");
        if (loaderContainer) loaderContainer.classList.add("hidden");
        if (chartContainer) chartContainer.classList.add("hidden");
        this.renderErrorState(container, "Failed to load chart");
      }
    }
  }

  /**
   * Render Staff Workload Chart
   */
  renderStaffWorkloadChart(canvas, data) {
    try {
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        throw new Error("Failed to get canvas context");
      }

      // Color palette for bars (professional enterprise colors)
      const barColors = [
        "rgba(37, 99, 235, 0.8)", // Blue
        "rgba(16, 185, 129, 0.8)", // Green
        "rgba(245, 158, 11, 0.8)", // Amber
        "rgba(139, 92, 246, 0.8)", // Purple
        "rgba(239, 68, 68, 0.8)", // Red
        "rgba(59, 130, 246, 0.8)", // Light Blue
        "rgba(168, 85, 247, 0.8)", // Light Purple
        "rgba(14, 165, 233, 0.8)", // Sky
      ];

      const barBorderColors = [
        "rgb(37, 99, 235)",
        "rgb(16, 185, 129)",
        "rgb(245, 158, 11)",
        "rgb(139, 92, 246)",
        "rgb(239, 68, 68)",
        "rgb(59, 130, 246)",
        "rgb(168, 85, 247)",
        "rgb(14, 165, 233)",
      ];

      // Apply colors to datasets if not already set
      data.datasets.forEach((dataset, datasetIndex) => {
        // Use API-provided colors or apply default colors based on dataset type
        if (
          !dataset.backgroundColor ||
          (Array.isArray(dataset.backgroundColor) &&
            dataset.backgroundColor.length === 0)
        ) {
          // API already provides colors, but ensure they're arrays for proper legend rendering
          if (typeof dataset.backgroundColor === "string") {
            // Convert single color to array for all bars in this dataset
            const colors = [];
            const borderColors = [];

            data.labels.forEach((label, labelIndex) => {
              colors.push(dataset.backgroundColor);
              borderColors.push(dataset.borderColor);
            });

            dataset.backgroundColor = colors;
            dataset.borderColor = borderColors;
          } else {
            // Apply default colors if none provided
            const defaultColor = barColors[datasetIndex % barColors.length];
            const defaultBorderColor =
              barBorderColors[datasetIndex % barBorderColors.length];

            const colors = [];
            const borderColors = [];

            data.labels.forEach((label, labelIndex) => {
              colors.push(defaultColor);
              borderColors.push(defaultBorderColor);
            });

            dataset.backgroundColor = colors;
            dataset.borderColor = borderColors;
          }
        }

        // Ensure other styling properties are set
        dataset.borderWidth = dataset.borderWidth || 1;
        dataset.borderRadius = dataset.borderRadius || 6;
        dataset.barThickness = dataset.barThickness || "flex";
        dataset.maxBarThickness = dataset.maxBarThickness || 80;
      });

      // Responsive helpers - optimized for card container
      const getAspectRatio = () => {
        const containerWidth =
          canvas.parentElement?.offsetWidth || window.innerWidth;
        if (window.innerWidth < 768) return 1;
        if (containerWidth < 400) return 1.2;
        return 1.8; // Wider for large screens to fill container
      };
      const getFontSize = (base = 10) =>
        window.innerWidth < 768 ? base - 1 : base;
      const getLegendPadding = () => (window.innerWidth < 768 ? 8 : 12);

      this.chartInstances.staffWorkload = new Chart(ctx, {
        type: "bar",
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: true,
          // aspectRatio: getAspectRatio(),  // TODO: check this option
          layout: {
            padding: {
              top: 4,
              bottom: 12,
              left: 0,
              right: 0,
            },
          },
          plugins: {
            legend: {
              position: "bottom",
              labels: {
                usePointStyle: true,
                pointStyle: "circle",
                padding: getLegendPadding(),
                boxWidth: 12,
                boxHeight: 12,
                font: {
                  size: getFontSize(11),
                  weight: "500",
                },
                color: (ctx) => {
                  // Match legend text color to corresponding dataset color
                  if (
                    ctx.datasetIndex !== undefined &&
                    data.datasets.length > 0
                  ) {
                    const ds = data.datasets[ctx.datasetIndex];
                    const colors = ds.backgroundColor;
                    if (Array.isArray(colors)) {
                      return colors[0]; // Use first color for the dataset
                    } else if (colors) {
                      return colors;
                    }
                  }
                  return "#4B5563";
                },
                generateLabels: function (chart) {
                  const data = chart.data;
                  if (data.datasets.length) {
                    return data.datasets.map((dataset, i) => {
                      const bgColor = Array.isArray(dataset.backgroundColor)
                        ? dataset.backgroundColor[0] // Use first color for the dataset
                        : dataset.backgroundColor;
                      const borderColor = Array.isArray(dataset.borderColor)
                        ? dataset.borderColor[0] // Use first color for the dataset
                        : dataset.borderColor;
                      return {
                        text: dataset.label, // Use dataset label (Active Jobs, Completed Jobs, etc.)
                        fillStyle: bgColor,
                        strokeStyle: borderColor,
                        lineWidth: dataset.borderWidth,
                        pointStyle: "circle",
                        hidden: false,
                        index: i,
                        datasetIndex: i, // Add datasetIndex for proper reference
                      };
                    });
                  }
                  return [];
                },
              },
              onClick: function (e, legendItem, legend) {
                // Disable click handler to prevent hiding bars
              },
            },
            tooltip: {
              backgroundColor: "rgba(17, 24, 39, 0.95)",
              padding: 12,
              titleFont: {
                size: 13,
                weight: "600",
              },
              bodyFont: {
                size: 12,
              },
              cornerRadius: 8,
              displayColors: true,
              boxPadding: 6,
              callbacks: {
                label: function (context) {
                  const value = context.parsed.y;
                  return `Tasks: ${value}`;
                },
              },
            },
          },
          scales: {
            x: {
              grid: {
                display: false,
                drawBorder: false,
              },
              ticks: {
                font: {
                  size: getFontSize(11),
                  weight: "500",
                },
                color: "#6B7280",
                maxRotation: 0,
                minRotation: 0,
                autoSkip: true,
                autoSkipPadding: 10,
              },
            },
            y: {
              beginAtZero: true,
              grid: {
                color: "rgba(107, 114, 128, 0.1)",
                drawBorder: false,
              },
              ticks: {
                font: {
                  size: getFontSize(10),
                },
                color: "#6B7280",
                stepSize: 1,
                padding: 8,
              },
              border: {
                display: false,
              },
            },
          },
          animation: {
            duration: 750,
            easing: "easeOutQuart",
          },
        },
      });

      // Update chart on window resize with proper cleanup
      this.resizeHandler = () => {
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
          if (this.chartInstances.staffWorkload && canvas.parentElement) {
            const chart = this.chartInstances.staffWorkload;
            const containerWidth = canvas.parentElement.offsetWidth;

            // Batch all option updates for better performance
            const newAspectRatio = containerWidth < 400 ? 1.2 : 1.8;
            const newFontSize = window.innerWidth < 768 ? 9 : 10;
            const newLegendFontSize = window.innerWidth < 768 ? 10 : 11;
            const newLegendPadding = window.innerWidth < 768 ? 8 : 12;

            // Update all options at once
            chart.options.aspectRatio = newAspectRatio;
            chart.options.plugins.legend.labels.font.size = newLegendFontSize;
            chart.options.plugins.legend.labels.padding = newLegendPadding;
            chart.options.scales.x.ticks.font.size = newLegendFontSize;
            chart.options.scales.y.ticks.font.size = newFontSize;

            chart.update("none");
          }
        }, 250);
      };

      window.addEventListener("resize", this.resizeHandler);
    } catch (error) {
      console.error(
        "[LFManagerDashboardLoader] Failed to create staff workload chart:",
        error,
      );
      const container = document.getElementById(
        this.widgets.staffWorkloadChart.containerId,
      );
      if (container) {
        this.renderErrorState(container, "Failed to create chart");
      }
    }
  }

  /**
   * Render Empty State
   */
  renderEmptyState(
    container,
    message,
    subMessage = null,
    iconClass = "fa-check-circle",
  ) {
    container.innerHTML = `
      <div class="flex flex-col items-center justify-center py-12 text-center">
        <i class="fa-solid ${iconClass} text-4xl text-green-500 dark:text-green-400 mb-3"></i>
        <p class="text-gray-600 dark:text-gray-400 font-medium">${message}</p>
        ${subMessage ? `<p class="text-sm text-gray-500 dark:text-gray-500 mt-1">${subMessage}</p>` : ""}
      </div>
    `;
  }

  /**
   * Render Error State
   */
  renderErrorState(container, message) {
    container.innerHTML = `
      <div class="flex flex-col items-center justify-center py-12 text-center">
        <i class="fa-solid fa-circle-exclamation text-4xl text-red-500 dark:text-red-400 mb-3"></i>
        <p class="text-gray-600 dark:text-gray-400 font-medium">${message}</p>
        <p class="text-sm text-gray-500 dark:text-gray-500 mt-1">Please refresh the page to try again</p>
      </div>
    `;
  }
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  // Check if we're on the manager dashboard
  const managerDashboardWidgets = document.querySelectorAll(
    ".lf-manager-dashboard",
  );
  if (managerDashboardWidgets.length > 0) {
    const dashboardLoader = new LFManagerDashboardLoader();
    dashboardLoader.initialize();
  }
});
