/**
 * Shared utility functions and authentication configurations for ReviewAI.
 */

/**
 * Initializes and displays the user profile avatar in navigation headers
 */
async function initNavbarProfile() {
  const profileContainer = document.getElementById("profile-container");
  const userNameEl = document.getElementById("user-name");
  const userAvatarEl = document.getElementById("user-avatar");

  const isLoggedIn = localStorage.getItem("is_logged_in") === "true";
  const token = localStorage.getItem("access_token");
  
  if (isLoggedIn && token && profileContainer) {
    profileContainer.style.display = "flex";
    try {
      const response = await fetch("/auth/me", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const user = await response.json();
        if (userNameEl) userNameEl.textContent = user.username;
        if (userAvatarEl) userAvatarEl.src = user.avatar_url;
        localStorage.setItem("username", user.username);
        localStorage.setItem("avatar_url", user.avatar_url);
      } else {
        // Token has likely expired or is invalid
        console.warn("Invalid session credentials on profile sync. Clearing authentication.");
        logoutUser();
      }
    } catch (err) {
      console.warn("Failed to contact auth profiles verification endpoint.", err);
      // Fail gracefully: display local storage cache if server is offline/dry-run
      if (userNameEl) userNameEl.textContent = localStorage.getItem("username") || "Developer";
      if (userAvatarEl) userAvatarEl.src = localStorage.getItem("avatar_url") || "";
    }
  }
}

/**
 * Initiates the actual GitHub OAuth flow by redirecting the browser
 */
function loginWithGitHub() {
  console.log("Redirecting to GitHub OAuth login gateway...");
  document.body.style.opacity = 0;
  setTimeout(() => {
    window.location.href = "/auth/login";
  }, 200);
}

/**
 * Contacts the backend server to clear logs and clears local storage session keys
 */
async function logoutUser() {
  const token = localStorage.getItem("access_token");
  if (token) {
    try {
      await fetch("/auth/logout", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
    } catch (err) {
      console.warn("Server side logout endpoint unreachable.", err);
    }
  }

  localStorage.removeItem("is_logged_in");
  localStorage.removeItem("username");
  localStorage.removeItem("avatar_url");
  localStorage.removeItem("access_token");
  
  document.body.style.opacity = 0;
  setTimeout(() => {
    window.location.href = "/";
  }, 200);
}

// Fade page in on loading completion
document.addEventListener("DOMContentLoaded", () => {
  document.body.style.opacity = 1;
  document.body.style.transition = "opacity 0.25s ease-in-out";
  initNavbarProfile();
});
