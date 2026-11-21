"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const calendarGrid = document.getElementById("calendar-grid");
  const currentMonthEl = document.getElementById("current-month");
  const jobModal = document.getElementById("job-modal");
  const modalDate = document.getElementById("modal-date");
  const cancelModal = document.getElementById("cancel-modal");
  let currentDate = new Date();

  // Demo jobs for placeholders (multiple jobs per day)
  const demoJobs = {
    1: [
      { description: "Team Meeting", status: "in-progress" },
      { description: "Submit Report", status: "completed" },
    ],
    5: [
      { description: "Submit Report", status: "completed" },
      { description: "Client Call", status: "overdue" },
      { description: "Code Review", status: "in-progress" },
    ],
    10: [
      { description: "Client Call", status: "overdue" },
      { description: "Project Deadline", status: "completed" },
    ],
    15: [
      { description: "Code Review", status: "in-progress" },
      { description: "Marketing Plan", status: "completed" },
      { description: "Bug Fixing", status: "overdue" },
      { description: "User Testing", status: "in-progress" },
    ],
    20: [
      { description: "Project Deadline", status: "completed" },
      { description: "Team Standup", status: "in-progress" },
    ],
    22: [
      { description: "Project Deadline", status: "completed" },
      { description: "Team Standup", status: "in-progress" },
    ],
    25: [
      { description: "Launch Event", status: "overdue" },
      { description: "Performance Review", status: "completed" },
      { description: "Sprint Planning", status: "in-progress" },
    ],
    30: [
      { description: "Launch Event", status: "overdue" },
      { description: "Performance Review", status: "completed" },
      { description: "Sprint Planning", status: "in-progress" },
    ],
  };

  const renderCalendar = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const lastDay = new Date(year, month + 1, 0).getDate();
    // alert(lastDay);

    // Update month/year display
    /**
     * currentMonthEl.textContent = date.toLocaleDateString("en-US", {
      month: "long",
      year: "numeric",
    });
     */

    // Clear existing days
    calendarGrid.innerHTML = "";

    // Generate days
    for (let day = 1; day <= lastDay; day++) {
      const dayCell = document.createElement("div");
      dayCell.setAttribute("data-month", month);
      dayCell.setAttribute("data-year", year);
      dayCell.className =
        "p-2 border rounded-md bg-gray-100 relative group cursor-pointer hover:bg-gray-200 transition";
      dayCell.innerHTML = `
        <div class="flex justify-between">
          <span class="font-bold text-gray-700">${day}</span>
        </div>
        <ul id="jobs-${day}" class="mt-2 space-y-1 max-h-16 overflow-hidden"></ul>
      `;

      // Add click event to open the modal
      dayCell.addEventListener("click", (event) => openJobModal(event, day));

      // Retrieve jobs for this day
      if (demoJobs[day] && demoJobs[day].length > 0) {
        const jobsList = dayCell.querySelector(`#jobs-${day}`);

        demoJobs[day].forEach((job, index) => {
          if (index < 2) {
            // Show up to 2 jobs directly
            const jobEl = document.createElement("li");
            let bgColor;
            if (job.status === "in-progress") bgColor = "bg-blue-100 text-blue-800";
            else if (job.status === "completed") bgColor = "bg-green-100 text-green-800";
            else if (job.status === "overdue") bgColor = "bg-red-100 text-red-800";

            jobEl.className = `${bgColor} px-2 py-1 rounded-md text-xs font-medium truncate`;
            jobEl.textContent = job.description;
            jobsList.appendChild(jobEl);
          }
        });

        // If there are more than 2 jobs, show a "+X more" button
        if (demoJobs[day].length > 2) {
          const moreJobs = document.createElement("button");
          moreJobs.className = "text-xs text-blue-500 mt-1 hover:underline";
          moreJobs.textContent = `+${demoJobs[day].length - 2} more`;
          moreJobs.addEventListener("click", (event) => showJobTooltip(day, event));
          jobsList.appendChild(moreJobs);
        }
      }

      calendarGrid.appendChild(dayCell);
    }
  };

  // Function to show all jobs in a tooltip
  const showJobTooltip = (day, event) => {
    // Remove any existing tooltips
    document.querySelectorAll(".tooltip").forEach((el) => el.remove());

    const tooltip = document.createElement("div");
    tooltip.className =
      "absolute left-0 top-full mt-2 w-48 bg-white border shadow-lg rounded-lg p-2 text-xs text-gray-800 z-50 tooltip";
    tooltip.innerHTML = demoJobs[day]
      .map(
        (job) =>
          `<p class="py-1 px-2 rounded-md ${
            job.status === "in-progress"
              ? "bg-blue-100 text-blue-800"
              : job.status === "completed"
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
          }">${job.description}</p>`,
      )
      .join("");

    // Append tooltip to the button
    event.target.parentElement.appendChild(tooltip);

    // Remove tooltip when clicking outside
    document.addEventListener(
      "click",
      () => {
        tooltip.remove();
      },
      { once: true },
    );
  };

  const openJobModal = (event, day) => {
    const clickedYear = event.currentTarget.dataset["year"];
    const clickedMonth = event.currentTarget.dataset["month"] + 1;
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1; // Month is 0-indexed
    modalDate.textContent = ` ${clickedMonth}/${day}/${clickedYear}`;
    // taskInput.value =
    //   jobs[`${year}-${month}-${day}`]?.map((t) => t.description).join("\n") || "";
    // alert(clickedYear);
    // alert(`${clickedYear}-${clickedMonth}-${day}`);

    jobModal.classList.remove("hidden");
  };

  const closeJobsModal = () => {
    jobModal.classList.add("hidden");
  };

  const saveJobModal = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1; // Month is 0-indexed
    const day = parseInt(modalDate.textContent.split("/")[1]);

    /* if (taskText) {
      jobs[`${year}-${month}-${day}`] = taskText.split("\n").map((desc) => ({
        description: desc,
        status,
      }));
    } else {
      delete jobs[`${year}-${month}-${day}`];
    } */

    closeJobsModal();
    renderCalendar(currentDate);
  };

  // Event Listeners
  if (document.getElementById("prev-month")) {
    document.getElementById("prev-month").addEventListener("click", () => {
      currentDate.setMonth(currentDate.getMonth() - 1);
      renderCalendar(currentDate);
    });
  }
  if (document.getElementById("next-month")) {
    document.getElementById("next-month").addEventListener("click", () => {
      currentDate.setMonth(currentDate.getMonth() + 1);
      renderCalendar(currentDate);
    });
  }
  if (document.getElementById("today-btn")) {
    document.getElementById("today-btn").addEventListener("click", () => {
      currentDate = new Date();
      renderCalendar(currentDate);
    });
  }
  if (cancelModal) {
    cancelModal.addEventListener("click", closeJobsModal);
  }
  /* if (savejobs) {
    savejobs.addEventListener("click", saveJobModal);
  } */

  if (calendarGrid) {
    // Initial render
    renderCalendar(currentDate);
  }
});
