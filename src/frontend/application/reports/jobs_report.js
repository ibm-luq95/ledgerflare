"use strict";
import ApexCharts from "apexcharts";

document.addEventListener("DOMContentLoaded", () => {
  // 1. View Switcher
  const matrixContainer = document.getElementById("matrixViewContainer");
  const cardContainer = document.getElementById("cardViewContainer");
  const btnMatrix = document.getElementById("btnMatrixView");
  const btnCard = document.getElementById("btnCardView");

  if (matrixContainer && cardContainer && btnMatrix && btnCard) {
    const applyJobReportView = (mode) => {
      if (mode === "card") {
        matrixContainer.classList.add("hidden");
        matrixContainer.classList.remove("block");
        cardContainer.classList.remove("hidden");
        cardContainer.classList.add("block");

        btnCard.className =
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all bg-white text-gray-800 shadow-sm dark:bg-slate-900 dark:text-white";
        btnMatrix.className =
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white transition-all";
        localStorage.setItem("lf_jobs_report_view_mode", "card");
      } else {
        cardContainer.classList.add("hidden");
        cardContainer.classList.remove("block");
        matrixContainer.classList.remove("hidden");
        matrixContainer.classList.add("block");

        btnMatrix.className =
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all bg-white text-gray-800 shadow-sm dark:bg-slate-900 dark:text-white";
        btnCard.className =
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white transition-all";
        localStorage.setItem("lf_jobs_report_view_mode", "matrix");
      }
    };

    btnMatrix.addEventListener("click", () => applyJobReportView("matrix"));
    btnCard.addEventListener("click", () => applyJobReportView("card"));

    const savedMode = localStorage.getItem("lf_jobs_report_view_mode");
    if (savedMode) {
      applyJobReportView(savedMode);
    } else if (window.innerWidth < 1024) {
      applyJobReportView("card");
    } else {
      applyJobReportView("matrix");
    }
  }

  // 2. Collapsible Panels (Filters & Chart)
  const setupToggle = (btnId, targetId) => {
    const btn = document.getElementById(btnId);
    const target = document.getElementById(targetId);
    if (btn && target) {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const isCollapsed = target.classList.contains("hidden");
        const icon = btn.querySelector("i.fa-chevron-down");
        if (isCollapsed) {
          target.classList.remove("hidden");
          if (icon) {
            icon.classList.add("rotate-180");
          }
        } else {
          target.classList.add("hidden");
          if (icon) {
            icon.classList.remove("rotate-180");
          }
        }
      });
    }
  };

  setupToggle("reportFilterCollapseToggle", "reportFilterCollapseArea");
  setupToggle("trendChartCollapseToggle", "trendChartCollapseArea");

  // 3. Saved Custom Views & Presets
  const presetsContainer = document.getElementById("customPresetsContainer");
  const btnSavePreset = document.getElementById("btnSaveFilterPreset");
  const btnClearAllPresets = document.getElementById("btnClearAllPresets");
  const STORAGE_KEY = "lf_jobs_report_custom_presets";

  const getCustomPresets = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  };

  const saveCustomPresets = (presets) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(presets));
    } catch (e) {
      console.error("Failed to save custom presets:", e);
    }
  };

  const updateSystemPresetsActiveState = () => {
    const currentParams = new URLSearchParams(window.location.search);
    const currentHealth = currentParams.get("health_status") || "";
    const currentOrderBy = currentParams.get("order_by") || "";
    const hasSpecialFilter = currentHealth !== "" || currentOrderBy !== "";

    const systemLinks = document.querySelectorAll(".system-preset-link");
    systemLinks.forEach((link) => {
      const presetType = link.getAttribute("data-preset-type");
      let isActive = false;

      if (presetType === "all" && !hasSpecialFilter) {
        isActive = true;
      } else if (presetType === "action_needed" && currentHealth === "action_needed") {
        isActive = true;
      } else if (presetType === "at_risk" && currentHealth === "at_risk") {
        isActive = true;
      } else if (presetType === "jobs_count" && currentOrderBy === "jobs_count") {
        isActive = true;
      } else if (presetType === "current_week" && currentOrderBy === "current_week") {
        isActive = true;
      }

      if (isActive) {
        link.className =
          "system-preset-link inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold shadow-sm ring-2 ring-offset-1 transition-all ";
        if (presetType === "all") {
          link.className +=
            "bg-gray-800 text-white border-gray-800 ring-gray-400 dark:bg-slate-700 dark:border-slate-600";
        } else if (presetType === "action_needed") {
          link.className +=
            "bg-rose-600 text-white border-rose-600 ring-rose-400 dark:bg-rose-600";
        } else if (presetType === "at_risk") {
          link.className +=
            "bg-amber-500 text-white border-amber-500 ring-amber-300 dark:bg-amber-500";
        } else if (presetType === "jobs_count") {
          link.className +=
            "bg-blue-600 text-white border-blue-600 ring-blue-400 dark:bg-blue-600";
        } else if (presetType === "current_week") {
          link.className +=
            "bg-emerald-600 text-white border-emerald-600 ring-emerald-400 dark:bg-emerald-600";
        }
        const icon = link.querySelector("i");
        if (icon) {
          icon.className = icon.className.replace(/text-[a-z]+-[0-9]+/g, "text-white");
        }
      }
    });
  };

  const renderCustomPresets = () => {
    if (!presetsContainer) return;
    presetsContainer.innerHTML = "";
    const presets = getCustomPresets();
    const currentSearch = window.location.search;

    if (btnClearAllPresets) {
      if (presets.length > 0) {
        btnClearAllPresets.classList.remove("hidden");
      } else {
        btnClearAllPresets.classList.add("hidden");
      }
    }

    presets.forEach((preset) => {
      const pill = document.createElement("div");
      const isCurrentActive =
        currentSearch &&
        (currentSearch === preset.query ||
          currentSearch.includes(preset.query.replace("?", "")));

      if (isCurrentActive) {
        pill.className =
          "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border shadow-sm bg-purple-600 text-white border-purple-600 ring-2 ring-purple-400 ring-offset-1 transition-all";
      } else {
        pill.className =
          "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border shadow-2xs bg-white text-purple-700 hover:bg-purple-50 border-purple-200 dark:bg-slate-800 dark:text-purple-300 dark:border-purple-900/50 dark:hover:bg-purple-950/30 transition-all";
      }

      const link = document.createElement("a");
      const baseUrl = window.location.pathname;
      link.href = `${baseUrl}${preset.query.startsWith("?") ? preset.query : "?" + preset.query}`;
      link.className = `inline-flex items-center gap-1 ${
        isCurrentActive ? "text-white hover:underline" : "text-purple-700 dark:text-purple-300 hover:underline"
      }`;
      link.innerHTML = `<i class="fa-solid fa-star text-[9px] ${
        isCurrentActive ? "text-white" : "text-purple-500"
      }"></i> <span>${preset.name}</span>`;

      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.className = isCurrentActive
        ? "text-white/80 hover:text-white p-0.5 rounded-full transition-colors cursor-pointer"
        : "text-gray-400 hover:text-rose-600 dark:hover:text-rose-400 p-0.5 rounded-full transition-colors cursor-pointer";
      deleteBtn.title = "Delete Preset";
      deleteBtn.innerHTML = `<i class="fa-solid fa-xmark text-[9px]"></i>`;
      deleteBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (confirm(`Remove preset "${preset.name}"?`)) {
          const updated = getCustomPresets().filter((p) => p.id !== preset.id);
          saveCustomPresets(updated);
          renderCustomPresets();
        }
      });

      pill.appendChild(link);
      pill.appendChild(deleteBtn);
      presetsContainer.appendChild(pill);
    });
  };

  if (btnSavePreset) {
    btnSavePreset.addEventListener("click", (e) => {
      e.preventDefault();
      const form = document.getElementById("clientJobsReportFilterForm");
      let searchParams = "";
      if (form) {
        const formData = new FormData(form);
        const params = new URLSearchParams();
        for (const [k, v] of formData.entries()) {
          if (v && String(v).trim() !== "") {
            params.append(k, String(v));
          }
        }
        searchParams = "?" + params.toString();
      } else {
        searchParams = window.location.search || "?period_year=2026";
      }

      const presetName = prompt(
        "Enter a name for this custom filter preset (e.g. My Tax Clients):"
      );
      if (presetName && presetName.trim() !== "") {
        const presets = getCustomPresets();
        const newPreset = {
          id: Date.now().toString(),
          name: presetName.trim(),
          query: searchParams,
        };
        presets.push(newPreset);
        saveCustomPresets(presets);
        renderCustomPresets();
      }
    });

    if (btnClearAllPresets) {
      btnClearAllPresets.addEventListener("click", (e) => {
        e.preventDefault();
        if (confirm("Are you sure you want to clear all saved custom presets?")) {
          saveCustomPresets([]);
          renderCustomPresets();
        }
      });
    }

    renderCustomPresets();
    updateSystemPresetsActiveState();
  }

  // 4. 12-Month Macro Trend Chart
  const chartElement = document.getElementById("jobsReportTrendChart");
  const chartDataElement = document.getElementById("jobsReportChartData");

  if (chartElement && chartDataElement) {
    try {
      const rawData = JSON.parse(chartDataElement.textContent || "[]");
      if (Array.isArray(rawData) && rawData.length > 0) {
        const categories = rawData.map((d) => d.month);
        const completedSeries = rawData.map((d) => d.completed || 0);
        const inProgressSeries = rawData.map((d) => d.in_progress || 0);
        const pastDueSeries = rawData.map((d) => d.past_due || 0);
        const notStartedSeries = rawData.map((d) => d.not_started || 0);

        const isDark = document.documentElement.classList.contains("dark");

        const options = {
          series: [
            {
              name: "Completed",
              data: completedSeries,
            },
            {
              name: "In Progress",
              data: inProgressSeries,
            },
            {
              name: "Past Due",
              data: pastDueSeries,
            },
            {
              name: "Not Started",
              data: notStartedSeries,
            },
          ],
          chart: {
            type: "bar",
            height: 290,
            stacked: true,
            toolbar: {
              show: false,
            },
            fontFamily: "inherit",
            animations: {
              enabled: true,
              speed: 400,
            },
          },
          colors: ["#10B981", "#3B82F6", "#F43F5E", "#94A3B8"],
          plotOptions: {
            bar: {
              horizontal: false,
              columnWidth: "45%",
              borderRadius: 4,
            },
          },
          dataLabels: {
            enabled: false,
          },
          stroke: {
            width: 1,
            colors: ["#fff"],
          },
          xaxis: {
            categories: categories,
            labels: {
              style: {
                colors: isDark ? "#94A3B8" : "#64748B",
                fontSize: "12px",
                fontWeight: 500,
              },
            },
            axisBorder: {
              show: false,
            },
            axisTicks: {
              show: false,
            },
          },
          yaxis: {
            title: {
              text: undefined,
            },
            labels: {
              style: {
                colors: isDark ? "#94A3B8" : "#64748B",
                fontSize: "12px",
              },
            },
          },
          grid: {
            borderColor: isDark ? "#334155" : "#E2E8F0",
            strokeDashArray: 4,
          },
          tooltip: {
            theme: isDark ? "dark" : "light",
            y: {
              formatter: function (val) {
                return val + " jobs";
              },
            },
          },
          legend: {
            position: "top",
            horizontalAlign: "right",
            fontSize: "12px",
            labels: {
              colors: isDark ? "#E2E8F0" : "#334155",
            },
            markers: {
              radius: 4,
            },
          },
        };

        const chart = new ApexCharts(chartElement, options);
        chart.render();
      }
    } catch (e) {
      console.warn("Failed to initialize Jobs Report Trend Chart:", e);
    }
  }
});
