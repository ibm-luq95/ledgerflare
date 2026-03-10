"use strict";

import { fetchUrlPathByName, sendRequest } from "../../utils/apis/apis.js";
import { SecureUrlFetcher } from "../../utils/apis/fetch_by_name.js";
import { RequestHandler } from "../../utils/apis/request_handler.js";
import { FETCHURLNAMEURL } from "../../utils/constants.js";
import Chart, { elements } from "chart.js/auto";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const mgDashboardHWidgetElements = document.querySelectorAll(".mg-dashboard-h-widget");
  //data-widget-name="jobs"
  //dashboard:manager:management_api:management-dashboard-api
  if (mgDashboardHWidgetElements.length > 0) {
    SecureUrlFetcher.fetchUrlPathByName(
      "dashboard:manager:management_api:management-dashboard-api"
    )
      .then((urlData) => {
        // console.warn(urlData);
        const urlPath = urlData["urlPath"];
        RequestHandler.sendRequest({
          url: urlPath,
          method: "POST",
          djangoRequest: true,
          debug: true,
          environment: process.env.STAGE_ENVIRONMENT || "development",
        })
          .then((newData) => {
            console.log("Request successful:", newData);
            // Handle the response data here
            mgDashboardHWidgetElements.forEach((element) => {
              const widgetName = element.dataset["widgetName"];
              const loaderElement = element.querySelector(".loader-element");
              loaderElement.classList.add("hidden");
              // console.log(element);
              switch (widgetName) {
                case "jobs":
                  element.textContent = newData["jobs_count"];
                  break;
                case "clients":
                  element.textContent = newData["clients_count"];
                  break;
                case "assignments":
                  element.textContent = newData["assignments_counts"];
                  break;
                case "staff":
                  element.textContent = newData["staff_users_count"];
                  break;
                default:
                  break;
              }
            });
            // setup chartjs
            const chartDashboardWrapper = document.querySelector(
              "#chart-dashboard-wrapper"
            );
            console.warn(chartDashboardWrapper)
            const chartLoader = chartDashboardWrapper.querySelector(".loader-element");
            const jobChartWrapper =
              chartDashboardWrapper.querySelector("#jobChartWrapper");
            console.log(chartLoader.classList);
            // console.log(jobChartWrapper);
            chartLoader.classList.remove("inline-block");
            chartLoader.classList.add("hidden");
            const emptyJobsCard = document.querySelector("#emptyJobsCard");

            const jobsChart = document.querySelector("canvas#jobsChart");
            if (newData["jobs_count"] > 0) {
              jobChartWrapper.classList.remove("hidden");
              if (jobsChart) {
                const getAspectRatio = () => window.innerWidth < 768 ? 1.5 : 1.2;
                const getFontSize = () => window.innerWidth < 768 ? 10 : 11;
                const getTitleFontSize = () => window.innerWidth < 768 ? 13 : 14;
                const getLegendPadding = () => window.innerWidth < 768 ? 8 : 12;

                const chart = new Chart(jobsChart, {
                  type: "doughnut",

                  data: {
                    labels: ["Past due", "Completed", "In progress"],
                    datasets: [
                      {
                        backgroundColor: ["#EF4444", "#22C55E", "#EAB308"],
                        borderWidth: 0,
                        hoverOffset: 4,
                        data: [
                          newData["jobs_statistics"]["past_due_jobs_count"],
                          newData["jobs_statistics"]["completed_jobs_count"],
                          newData["jobs_statistics"]["in_progress_jobs_count"],
                        ],
                      },
                    ],
                  },
                  options: {
                    maintainAspectRatio: true,
                    responsive: true,
                    aspectRatio: getAspectRatio(),
                    layout: {
                      padding: {
                        top: 5,
                        bottom: 5,
                      },
                    },
                    plugins: {
                      title: {
                        display: true,
                        text: "Jobs Overview",
                        font: {
                          size: getTitleFontSize(),
                          weight: "600",
                        },
                        color: "#374151",
                        padding: {
                          top: 0,
                          bottom: 10,
                        },
                      },
                      legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                          usePointStyle: true,
                          pointStyle: "circle",
                          padding: getLegendPadding(),
                          font: {
                            size: getFontSize(),
                          },
                          color: "#6B7280",
                        },
                      },
                      tooltip: {
                        backgroundColor: "rgba(17, 24, 39, 0.9)",
                        padding: 12,
                        titleFont: {
                          size: 13,
                        },
                        bodyFont: {
                          size: 12,
                        },
                        cornerRadius: 8,
                        displayColors: true,
                      },
                    },
                    animation: {
                      animateScale: true,
                      animateRotate: true,
                    },
                  },
                });

                // Update chart on window resize
                let resizeTimeout;
                window.addEventListener("resize", () => {
                  clearTimeout(resizeTimeout);
                  resizeTimeout = setTimeout(() => {
                    chart.options.aspectRatio = getAspectRatio();
                    chart.options.plugins.legend.labels.font.size = getFontSize();
                    chart.options.plugins.legend.labels.padding = getLegendPadding();
                    chart.options.plugins.title.font.size = getTitleFontSize();
                    chart.update("none");
                  }, 250);
                });
              }
            } else {
              emptyJobsCard.classList.remove("hidden");
            }
          })
          .catch((error) => {
            console.error("Request failed:", error);
            // Handle the error here
          });
      })
      .catch((error) => console.error("Fetch failed:", error));
  }

  // throw new Error("DF");
});
