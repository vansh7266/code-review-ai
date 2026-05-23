/**
 * Review Audit UI handlers. Fetches static reports from the DB and displays
 * Gemini's review annotations grouped by affected code files.
 */

document.addEventListener("DOMContentLoaded", () => {
  if (localStorage.getItem("is_logged_in") !== "true") {
    window.location.href = "/";
    return;
  }

  initNavbarProfile();
  
  // Extract target review ID from URL query parameters
  const params = new URLSearchParams(window.location.search);
  const reviewId = params.get("id") || "1";
  
  loadReviewReport(reviewId);
});

/**
 * Contacts the database to load the review record and files review comments list
 */
async function loadReviewReport(reviewId) {
  const loader = document.getElementById("review-loader");
  const token = localStorage.getItem("access_token");
  
  try {
    const response = await fetch(`/review/${reviewId}`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (response.ok) {
      const data = await response.json();
      renderReviewUI(data);
    } else {
      loadFallbackReviewReport(reviewId);
    }
  } catch (err) {
    console.warn("Failed to contact review details API. Render fallback report data.", err);
    loadFallbackReviewReport(reviewId);
  } finally {
    if (loader) loader.style.display = "none";
  }
}

/**
 * Maps out the report, updates metadata header, and parses comments into files
 */
function renderReviewUI(data) {
  // Update Header details
  document.getElementById("meta-repo-name").textContent = data.repo_name || "unknown/repository";
  document.getElementById("meta-pr-number").textContent = `#${data.pr_number || "--"}`;
  
  const statusEl = document.getElementById("meta-status");
  statusEl.className = `badge badge-${data.status || 'pending'}`;
  statusEl.textContent = data.status || "Pending";

  const comments = data.comments || [];
  
  // Calculate sidebar severity tallies
  let counts = { critical: 0, major: 0, minor: 0, info: 0 };
  
  // Group comments by their target file path
  const filesMap = {};
  
  comments.forEach(comment => {
    // Increase matching counters
    const sev = (comment.severity || 'minor').toLowerCase();
    if (counts.hasOwnProperty(sev)) {
      counts[sev]++;
    } else {
      counts.minor++;
    }

    const path = comment.file_path || "Other Changes";
    if (!filesMap[path]) {
      filesMap[path] = [];
    }
    filesMap[path].push(comment);
  });

  // Write counters to sidebar
  document.getElementById("count-critical").textContent = counts.critical;
  document.getElementById("count-major").textContent = counts.major;
  document.getElementById("count-minor").textContent = counts.minor;
  document.getElementById("count-info").textContent = counts.info;

  // Render comments inside files cards
  const container = document.getElementById("file-comments-container");
  if (!container) return;

  if (comments.length === 0) {
    container.innerHTML = `
      <div class="glass-card" style="text-align: center; padding: 4rem;">
        <h3 style="font-family: var(--font-heading); margin-bottom: 0.5rem; color: var(--color-minor);">No Issues Found!</h3>
        <p style="color: var(--text-secondary); font-size: 0.95rem;">Gemini AI reviewed your pull request and found no security flaws or bug leaks.</p>
      </div>`;
    return;
  }

  // Iterate files mapping and create high-fidelity UI cards
  container.innerHTML = Object.entries(filesMap).map(([filePath, fileComments]) => {
    const commentsListHTML = fileComments.map(item => {
      const lineText = item.line_number ? `Line ${item.line_number}` : "Diff";
      const sevClass = `severity-${(item.severity || 'minor').toLowerCase()}`;
      
      return `
        <div class="comment-item">
          <div class="line-info-column">
            <span class="line-badge">${lineText}</span>
          </div>
          <div class="comment-body-column">
            <div class="comment-meta-row">
              <span class="severity-label ${sevClass}">${item.severity}</span>
              <span class="category-label">${item.category}</span>
            </div>
            <p class="comment-text">${item.comment}</p>
          </div>
        </div>`;
    }).join("");

    return `
      <div class="file-review-card glass-card" style="padding: 0; margin-bottom: 2rem;">
        <div class="file-header">
          <span class="file-name">${filePath}</span>
          <span class="file-badge-count">${fileComments.length} finding${fileComments.length > 1 ? 's' : ''}</span>
        </div>
        <div class="comment-list">
          ${commentsListHTML}
        </div>
      </div>`;
  }).join("");
}

/**
 * Fallback values in unconfigured environments
 */
function loadFallbackReviewReport(reviewId) {
  const mockReport = {
    review_id: reviewId,
    repo_name: "acme-corp/payment-gateway",
    pr_number: 14,
    status: "completed",
    comments: [
      {
        file_path: "backend/routes/auth.py",
        line_number: 42,
        severity: "critical",
        category: "security",
        comment: "JWT session key secret is read from hardcoded default fallback properties if environment configs fail. This poses a major security hazard in deployments."
      },
      {
        file_path: "backend/database.py",
        line_number: 18,
        severity: "major",
        category: "performance",
        comment: "Database async connection pools do not specify timeout parameters. This could cause execution freezes or thread lockouts if multiple API endpoints saturate the pool."
      },
      {
        file_path: "frontend/js/dashboard.js",
        line_number: 88,
        severity: "minor",
        category: "style",
        comment: "Found console logs in active client UI scripts. Clean production branches should avoid committing verbose logs."
      },
      {
        file_path: "frontend/js/dashboard.js",
        line_number: 104,
        severity: "info",
        category: "style",
        comment: "Redundant DOM declarations. Re-declaring navbar variables could trigger memory retention overheads."
      }
    ]
  };
  renderReviewUI(mockReport);
}
