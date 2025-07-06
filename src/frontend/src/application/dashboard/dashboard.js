"use strict";

import { fetchUrlPathByName, sendRequest } from "../../utils/apis/apis";
import { SecureUrlFetcher } from "../../utils/apis/fetch_by_name";
import { RequestHandler } from "../../utils/apis/request_handler";
import { FETCHURLNAMEURL } from "../../utils/constants";
import Chart, { elements } from "chart.js/auto";

document.addEventListener("DOMContentLoaded", (readyEvent) => {
  const mgDashboardHWidgetElements = document.querySelectorAll(".mg-dashboard-h-widget");
  //data-widget-name="jobs"
  //dashboard:manager:management_api:management-dashboard-api
  SecureUrlFetcher.fetchUrlPathByName(
    "dashboard:manager:management_api:management-dashboard-api"
  )
    .then((urlData) => {
      console.warn(urlData);
      const urlPath = urlData["urlPath"];
      RequestHandler.sendRequest({
        url: urlPath,
        method: "POST",
        djangoRequest: true,
        debug: true,
        // environment: process.env.STAGE_ENVIRONMENT || "development",
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
          const chartLoader = chartDashboardWrapper.querySelector(".loader-element");
          const jobChartWrapper = chartDashboardWrapper.querySelector("#jobChartWrapper");
          // console.log(chartLoader);
          // console.log(jobChartWrapper);
          chartLoader.classList.add("hidden");
          const emptyJobsCard = document.querySelector("#emptyJobsCard");

          const jobsChart = document.querySelector("canvas#jobsChart");
          if (newData["jobs_count"] > 0) {
            jobChartWrapper.classList.remove("hidden");
            if (jobsChart) {
              const chart = new Chart(jobsChart, {
                type: "doughnut",

                data: {
                  labels: ["Past due", "Completed", "In progress"],
                  datasets: [
                    {
                      backgroundColor: ["#EF4444", "#22C55E", "#EAB308"],
                      data: [
                        newData["jobs_statistics"]["past_due_jobs_count"],
                        newData["jobs_statistics"]["completed_jobs_count"],
                        newData["jobs_statistics"]["in_progress_jobs_count"],
                      ],
                    },
                  ],
                },
                options: {
                  maintainAspectRation: false,
                  responsive: false,
                  aspectRatio: 2,

                  plugins: {
                    title: {
                      display: true,
                      text: "Jobs",
                    },
                    legend: {
                      display: false,
                    },
                  },
                },
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
  // throw new Error("DF");
});
