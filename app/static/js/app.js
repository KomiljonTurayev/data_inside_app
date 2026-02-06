/**
 * Cover Art Generator - Frontend JavaScript
 */

document.addEventListener("DOMContentLoaded", () => {
  const coverTypeSelect = document.getElementById("cover-type");
  const positivePrompt = document.getElementById("positive-prompt");
  const negativePrompt = document.getElementById("negative-prompt");
  const seedInput = document.getElementById("seed");
  const stepsInput = document.getElementById("steps");
  const cfgInput = document.getElementById("cfg-scale");
  const widthInput = document.getElementById("width");
  const heightInput = document.getElementById("height");

  const btnGenerate = document.getElementById("btn-generate");
  const btnExport = document.getElementById("btn-export-workflow");

  const placeholder = document.getElementById("placeholder");
  const loading = document.getElementById("loading");
  const loadingMessage = document.getElementById("loading-message");
  const generatedImage = document.getElementById("generated-image");
  const imageMeta = document.getElementById("image-meta");

  // Populate prompts when a preset is selected
  coverTypeSelect.addEventListener("change", () => {
    const type = coverTypeSelect.value;
    if (type && PRESETS[type]) {
      positivePrompt.value = PRESETS[type].positive;
      negativePrompt.value = PRESETS[type].negative;
    }
  });

  // Generate image
  let isGenerating = false;

  btnGenerate.addEventListener("click", async () => {
    const pos = positivePrompt.value.trim();
    if (!pos) {
      showToast("Please enter a positive prompt.");
      return;
    }

    isGenerating = true;
    btnGenerate.disabled = true;
    btnExport.disabled = true;
    placeholder.classList.add("hidden");
    generatedImage.classList.add("hidden");
    imageMeta.classList.add("hidden");
    loading.classList.remove("hidden");
    loadingMessage.textContent = "Connecting to ComfyUI...";

    // Poll status while waiting
    const statusInterval = setInterval(async () => {
      if (!isGenerating) return;
      try {
        const res = await fetch("/api/status");
        if (!res.ok) return;
        const data = await res.json();
        if (isGenerating && data.message) {
          loadingMessage.textContent = data.message;
        }
      } catch (_) {}
    }, 2000);

    try {
      const payload = {
        cover_type: coverTypeSelect.value || null,
        positive_prompt: pos,
        negative_prompt: negativePrompt.value.trim(),
        seed: seedInput.value ? parseInt(seedInput.value, 10) : null,
        steps: stepsInput.value ? parseInt(stepsInput.value, 10) : null,
        cfg_scale: cfgInput.value ? parseFloat(cfgInput.value) : null,
        width: widthInput.value ? parseInt(widthInput.value, 10) : null,
        height: heightInput.value ? parseInt(heightInput.value, 10) : null,
      };

      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Generation failed");
      }

      // Show generated image
      loading.classList.add("hidden");
      generatedImage.src = data.web_path + "?t=" + Date.now();
      generatedImage.classList.remove("hidden");

      // Show metadata
      document.getElementById("meta-time").textContent = data.generation_time + "s";
      document.getElementById("meta-seed").textContent = data.seed;
      document.getElementById("meta-steps").textContent = data.steps;
      document.getElementById("meta-cfg").textContent = data.cfg_scale;
      document.getElementById("meta-res").textContent = data.width + " x " + data.height;
      imageMeta.classList.remove("hidden");

    } catch (err) {
      loading.classList.add("hidden");
      placeholder.classList.remove("hidden");
      showToast(err.message);
    } finally {
      isGenerating = false;
      clearInterval(statusInterval);
      btnGenerate.disabled = false;
      btnExport.disabled = false;
    }
  });

  // Export workflow JSON
  btnExport.addEventListener("click", async () => {
    const pos = positivePrompt.value.trim();
    if (!pos) {
      showToast("Please enter a positive prompt first.");
      return;
    }

    try {
      const payload = {
        positive_prompt: pos,
        negative_prompt: negativePrompt.value.trim(),
        seed: seedInput.value ? parseInt(seedInput.value, 10) : null,
        steps: stepsInput.value ? parseInt(stepsInput.value, 10) : null,
        cfg_scale: cfgInput.value ? parseFloat(cfgInput.value) : null,
        width: widthInput.value ? parseInt(widthInput.value, 10) : null,
        height: heightInput.value ? parseInt(heightInput.value, 10) : null,
      };

      const response = await fetch("/api/workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate workflow");
      }

      // Download as file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "comfyui_workflow.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

    } catch (err) {
      showToast("Failed to export workflow: " + err.message);
    }
  });

  // Toast notification
  function showToast(message) {
    const existing = document.querySelector(".toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }
});
