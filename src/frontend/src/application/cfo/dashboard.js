// "use strict";
// import _ from "lodash";
// import "apexcharts/dist/apexcharts.css";
// import ApexCharts from "apexcharts";
// // Expose it globally so that @preline/helper-apexcharts can find it.
// window.ApexCharts = ApexCharts;
// // Now import the helper
// import "@preline/helper-apexcharts";
// // import "preline/dist/helper-apexcharts.js";
// // import { buildChart } from "preline/dist/helper-apexcharts.js";
// document.addEventListener("DOMContentLoaded", (readyEvent) => {
//   const chartElement = document.querySelector("#hs-single-area-chart");
//   const chartElement2 = document.querySelector("#hs-single-area-chart2");

//   if (chartElement && chartElement2) {
//     const options = {
//       series: [
//         {
//           name: "Desktops",
//           data: [10, 41, 35, 51, 49, 62, 69, 91, 148],
//         },
//       ],
//       chart: {
//         height: 350,
//         type: "line",
//         zoom: {
//           enabled: false,
//         },
//       },
//       dataLabels: {
//         enabled: false,
//       },
//       stroke: {
//         curve: "straight",
//       },
//       title: {
//         text: "Product Trends by Month",
//         align: "left",
//       },
//       grid: {
//         row: {
//           colors: ["#f3f3f3", "transparent"], // takes an array which will be repeated on columns
//           opacity: 0.5,
//         },
//       },
//       xaxis: {
//         categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"],
//       },
//     };

//     const chart = new ApexCharts(chartElement, options);

//     chart.render();

//     const options2 = {
//       title: {
//         text: "PPPP",
//         align: "left",
//       },
//       series: [10, 55, 41, 17, 15],
//       chart: {
//         type: "pie",
//         height: 350,
//         animations: {
//           enabled: false,
//           easing: "easeinout",
//           speed: 800,
//           animateGradually: {
//             enabled: false, // Resolves animation rendering issues
//           },
//         },
//       },
//       labels: ["Team A", "Team B", "Team C", "Team D", "Team E"],
//       colors: ["#FF4560", "#00E396", "#008FFB", "#FEB019", "#775DD0"],
//       legend: {
//         position: "right",
//         markers: {
//           shape: "circle",
//         },
//       },
//       dataLabels: {
//         enabled: true,
//         formatter: (val) => `${val.toFixed(1)}%`, // Show values as percentages
//       },
//       tooltip: {
//         enabled: true,
//         y: {
//           formatter: (val) => `${val} votes`,
//         },
//       },
//       responsive: [
//         {
//           breakpoint: 480,
//           options: {
//             chart: {
//               width: 300,
//             },
//             legend: {
//               position: "bottom",
//             },
//           },
//         },
//       ],
//     };
//     const chart2 = new ApexCharts(chartElement2, options2);
//     chart2.render();
//     // Example of dynamic update
//     // setTimeout(() => {
//     //   chart2.updateSeries([50, 60, 70, 20, 10]);
//     // }, 5000);
//   }
// });
