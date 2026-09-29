/* ========================================================
   PocketSmart AI: Client-Side Interactive Logic
   ======================================================== */

document.addEventListener("DOMContentLoaded", () => {
  initBudgetSync();
  initDynamicItems();
  initImageDropzone();
  initFormSubmissions();
});

// 1. Budget Slider & Input Sync
function initBudgetSync() {
  const slider = document.getElementById("budgetSlider");
  const input = document.getElementById("totalBudgetInput");
  const display = document.getElementById("budgetDisplay");

  if (slider && input) {
    const update = (val) => {
      slider.value = val;
      input.value = val;
      if (display) {
        display.textContent = new Intl.NumberFormat('en-IN', {
          maximumFractionDigits: 0
        }).format(val);
      }
    };

    slider.addEventListener("input", (e) => update(e.target.value));
    input.addEventListener("input", (e) => update(e.target.value));
  }
}

// 2. Dynamic Item Addition (Home Planner)
function initDynamicItems() {
  const addBtn = document.getElementById("btnAddItem");
  const container = document.getElementById("dynamicItemsContainer");

  if (addBtn && container) {
    addBtn.addEventListener("click", () => {
      const row = document.createElement("div");
      row.className = "dynamic-item-row";
      row.innerHTML = `
        <input type="text" name="item_name" class="form-control" placeholder="e.g. Ceiling Fan, Wall Sconces, Rug" required>
        <input type="number" name="item_quantity" class="form-control" value="1" min="1" max="50">
        <button type="button" class="btn-remove-item" title="Remove Item">✕</button>
      `;
      container.appendChild(row);

      row.querySelector(".btn-remove-item").addEventListener("click", () => {
        row.remove();
      });
    });

    // Delegate existing remove buttons
    container.addEventListener("click", (e) => {
      if (e.target.classList.contains("btn-remove-item")) {
        e.target.closest(".dynamic-item-row").remove();
      }
    });
  }
}

// 3. Multimodal Image Dropzone (Jewelry Planner)
function initImageDropzone() {
  const dropzone = document.getElementById("imageDropzone");
  const fileInput = document.getElementById("outfitImageInput");
  const previewContainer = document.getElementById("uploadPreview");
  const previewImg = document.getElementById("previewImg");
  const base64Input = document.getElementById("imageBase64");

  if (!dropzone || !fileInput) return;

  const handleFile = (file) => {
    if (!file || !file.type.startsWith("image/")) {
      showToast("Please upload an image file (JPG, PNG, WebP).", "error");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      if (previewImg) previewImg.src = dataUrl;
      if (previewContainer) previewContainer.style.display = "block";
      if (base64Input) base64Input.value = dataUrl;
      showToast("Outfit image loaded for AI color analysis!", "success");
    };
    reader.readAsDataURL(file);
  };

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      fileInput.files = e.dataTransfer.files;
      handleFile(e.dataTransfer.files[0]);
    }
  });
}

// 4. Form Submission Loading State
function initFormSubmissions() {
  const forms = document.querySelectorAll(".ajax-planner-form");
  forms.forEach(form => {
    form.addEventListener("submit", () => {
      const submitBtn = form.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
          <svg class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite; margin-right: 8px;">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
            <path d="M12 2a10 10 0 0 1 10 10"></path>
          </svg>
          Gemini AI is analyzing budget...
        `;
      }
    });
  });
}

// 5. Toast Notification System
function showToast(message, type = "info") {
  let toastContainer = document.getElementById("toastContainer");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toastContainer";
    toastContainer.style.position = "fixed";
    toastContainer.style.bottom = "24px";
    toastContainer.style.right = "24px";
    toastContainer.style.zIndex = "99999";
    toastContainer.style.display = "flex";
    toastContainer.style.flexDirection = "column";
    toastContainer.style.gap = "10px";
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  toast.className = `glass-panel toast-${type}`;
  toast.style.padding = "14px 20px";
  toast.style.borderRadius = "12px";
  toast.style.color = "#fff";
  toast.style.fontSize = "0.92rem";
  toast.style.fontWeight = "500";
  toast.style.boxShadow = "0 10px 25px rgba(0,0,0,0.5)";
  toast.style.border = type === "error" ? "1px solid #f43f5e" : "1px solid #10b981";
  toast.style.background = type === "error" ? "rgba(244, 63, 94, 0.9)" : "rgba(16, 185, 129, 0.9)";
  toast.textContent = message;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.4s ease";
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

// Global Delete Recommendation Handler
async function deletePlan(planId) {
  if (!confirm("Are you sure you want to remove this recommendation from your history?")) return;
  try {
    const res = await fetch(`/api/history/${planId}/delete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    if (res.ok) {
      showToast("Plan deleted successfully.", "success");
      const card = document.getElementById(`rec-card-${planId}`);
      if (card) card.remove();
    } else {
      showToast("Could not delete plan.", "error");
    }
  } catch (e) {
    showToast("Network error deleting plan.", "error");
  }
}
