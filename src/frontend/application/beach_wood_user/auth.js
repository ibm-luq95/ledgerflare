/**
 * LedgerFlare - Authentication Module
 * Handles password visibility toggling, login submission states, and role selection UX.
 */

export function initAuthModule() {
  // Password Visibility Toggle
  const togglePasswordBtns = document.querySelectorAll("[data-auth-password-toggle]");
  togglePasswordBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const targetInputId = btn.getAttribute("data-target-input") || "id_password";
      const targetInput = document.getElementById(targetInputId);
      const icon = btn.querySelector("i");

      if (targetInput) {
        const isPassword = targetInput.getAttribute("type") === "password";
        targetInput.setAttribute("type", isPassword ? "text" : "password");

        if (icon) {
          if (isPassword) {
            icon.classList.remove("fa-eye");
            icon.classList.add("fa-eye-slash");
            btn.setAttribute("aria-label", "Hide password");
          } else {
            icon.classList.remove("fa-eye-slash");
            icon.classList.add("fa-eye");
            btn.setAttribute("aria-label", "Show password");
          }
        }
      }
    });
  });

  // Login Form Submission State
  const loginForm = document.getElementById("bw-login-form");
  const submitBtn = document.getElementById("bw-login-submit-btn");

  if (loginForm && submitBtn) {
    loginForm.addEventListener("submit", () => {
      const emailInput = document.getElementById("id_email");
      const passwordInput = document.getElementById("id_password");

      // Only show loading if basic inputs are filled
      if (emailInput && emailInput.value && passwordInput && passwordInput.value) {
        submitBtn.disabled = true;
        const spinner = submitBtn.querySelector("[data-submit-spinner]");
        const text = submitBtn.querySelector("[data-submit-text]");
        const icon = submitBtn.querySelector("[data-submit-icon]");

        if (spinner) {
          spinner.style.display = "inline-block";
          spinner.classList.remove("hidden");
        }
        if (text) {
          text.textContent = "Authenticating...";
        }
        if (icon) {
          icon.style.display = "none";
          icon.classList.add("hidden");
        }
      }
    });
  }
}

// Auto-initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initAuthModule);
} else {
  initAuthModule();
}
