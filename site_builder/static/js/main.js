/**
 * ToolNest Main Frontend Script
 * Handles FAQ accordions, navigation, clipboard helpers, dropzone file uploads, and execution.
 */
document.addEventListener('DOMContentLoaded', function () {
  // 1. FAQ Accordions
  const faqQuestions = document.querySelectorAll('.faq-question');
  faqQuestions.forEach(btn => {
    btn.addEventListener('click', function () {
      const item = this.closest('.faq-item');
      if (item) {
        item.classList.toggle('open');
      }
    });
  });

  // 2. Mobile Menu Toggle
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  const siteNav = document.querySelector('.site-nav');
  if (mobileToggle && siteNav) {
    mobileToggle.addEventListener('click', function () {
      siteNav.classList.toggle('active');
    });
  }

  // 3. Pre-warm server for tool pages that require backend processing
  if (document.querySelector('.server-tool-btn')) {
    ToolNestAPI.prewarmBackend();
  }

  // 4. Copy to clipboard buttons
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', async function () {
      const targetSelector = this.getAttribute('data-copy-target');
      const targetEl = document.querySelector(targetSelector);
      if (targetEl) {
        const textToCopy = targetEl.value || targetEl.innerText;
        try {
          await navigator.clipboard.writeText(textToCopy);
          const originalText = this.innerText;
          this.innerText = 'Copied!';
          setTimeout(() => { this.innerText = originalText; }, 2000);
        } catch (err) {
          console.error('Failed to copy', err);
        }
      }
    });
  });

  // 5. Server Upload Tool Workspace (Dropzone, File Selection & Processing)
  const uploadApp = document.getElementById('upload-tool-app');
  if (uploadApp) {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const fileListContainer = document.getElementById('file-list-container');
    const selectedFilesList = document.getElementById('selected-files-list');
    const startBtn = document.getElementById('start-process-btn');
    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressStatus = document.getElementById('progress-status');
    const progressPercentage = document.getElementById('progress-percentage');
    const errorBox = document.getElementById('error-message-box');
    const endpoint = uploadApp.getAttribute('data-endpoint');

    let selectedFiles = [];

    function formatBytes(bytes) {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
    }

    function showError(msg) {
      if (!errorBox) return;
      errorBox.textContent = msg;
      errorBox.style.display = 'block';
    }

    function clearError() {
      if (errorBox) {
        errorBox.textContent = '';
        errorBox.style.display = 'none';
      }
    }

    function renderFileList() {
      if (!selectedFilesList) return;
      selectedFilesList.innerHTML = '';
      if (selectedFiles.length === 0) {
        if (fileListContainer) fileListContainer.style.display = 'none';
        if (startBtn) startBtn.setAttribute('disabled', 'disabled');
        return;
      }

      if (fileListContainer) fileListContainer.style.display = 'block';
      if (startBtn) startBtn.removeAttribute('disabled');

      selectedFiles.forEach((file, index) => {
        const li = document.createElement('li');
        li.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 0.625rem 1rem; background: var(--bg-subtle); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); font-size: 0.875rem;';

        const nameSpan = document.createElement('span');
        nameSpan.style.cssText = 'overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 75%; font-weight: 500;';
        nameSpan.textContent = `${file.name} (${formatBytes(file.size)})`;

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.textContent = '✕';
        removeBtn.style.cssText = 'background: none; border: none; color: var(--danger); font-size: 1rem; cursor: pointer; padding: 0 0.5rem;';
        removeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          selectedFiles.splice(index, 1);
          renderFileList();
        });

        li.appendChild(nameSpan);
        li.appendChild(removeBtn);
        selectedFilesList.appendChild(li);
      });
    }

    function handleFiles(newFiles) {
      clearError();
      const isMultiple = fileInput && fileInput.hasAttribute('multiple');
      if (isMultiple) {
        selectedFiles = selectedFiles.concat(Array.from(newFiles));
      } else {
        selectedFiles = Array.from(newFiles).slice(0, 1);
      }
      renderFileList();
    }

    // Split PDF mode switcher
    const splitRadios = document.querySelectorAll('input[name="split-mode"]');
    const splitRangeBox = document.getElementById('split-range-container');
    const splitAllBox = document.getElementById('split-all-container');
    if (splitRadios.length > 0 && splitRangeBox && splitAllBox) {
      splitRadios.forEach(radio => {
        radio.addEventListener('change', () => {
          if (radio.value === 'ranges') {
            splitRangeBox.style.display = 'block';
            splitAllBox.style.display = 'none';
          } else {
            splitRangeBox.style.display = 'none';
            splitAllBox.style.display = 'block';
          }
        });
      });
    }

    if (dropzone && fileInput) {
      dropzone.addEventListener('click', () => fileInput.click());
      dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
      dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
      dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer && e.dataTransfer.files) {
          handleFiles(e.dataTransfer.files);
        }
      });
      fileInput.addEventListener('change', () => {
        if (fileInput.files) handleFiles(fileInput.files);
      });
    }

    if (startBtn && endpoint) {
      startBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) return;
        clearError();

        startBtn.setAttribute('disabled', 'disabled');
        if (progressContainer) progressContainer.classList.add('active');
        if (progressFill) progressFill.style.width = '20%';
        if (progressPercentage) progressPercentage.textContent = '20%';
        if (progressStatus) progressStatus.textContent = 'Uploading files...';

        const formData = new FormData();
        const isMultiple = fileInput && fileInput.hasAttribute('multiple');

        if (isMultiple) {
          selectedFiles.forEach(file => formData.append('files', file));
        } else {
          formData.append('file', selectedFiles[0]);
        }

        // Additional tool-specific form inputs
        const compressRadio = document.querySelector('input[name="compress-level"]:checked');
        if (compressRadio) formData.append('level', compressRadio.value);

        const splitMode = document.querySelector('input[name="split-mode"]:checked');
        const splitRange = document.getElementById('split-range-input');
        if (splitMode && splitMode.value === 'ranges' && splitRange && splitRange.value.trim()) {
          formData.append('ranges', splitRange.value.trim());
        }

        const formatSelect = document.getElementById('image-target-format');
        if (formatSelect) formData.append('target_format', formatSelect.value);

        try {
          if (progressFill) progressFill.style.width = '55%';
          if (progressPercentage) progressPercentage.textContent = '55%';
          if (progressStatus) progressStatus.textContent = 'Processing securely...';

          const blob = await ToolNestAPI.request(endpoint, {
            method: 'POST',
            body: formData,
          });

          if (progressFill) progressFill.style.width = '100%';
          if (progressPercentage) progressPercentage.textContent = '100%';
          if (progressStatus) progressStatus.textContent = 'Completed!';

          // Trigger browser file download
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.style.display = 'none';
          a.href = url;
          // Determine appropriate download filename
          const mime = blob.type || '';
          let downloadName = 'toolnest_output';
          if (mime.includes('pdf')) downloadName = 'toolnest_document.pdf';
          else if (mime.includes('zip')) downloadName = 'toolnest_archive.zip';
          else if (mime.includes('jpeg') || mime.includes('jpg')) downloadName = 'toolnest_image.jpg';
          else if (mime.includes('png')) downloadName = 'toolnest_image.png';
          else if (mime.includes('webp')) downloadName = 'toolnest_image.webp';

          a.download = downloadName;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          a.remove();

          setTimeout(() => {
            if (progressContainer) progressContainer.classList.remove('active');
            startBtn.removeAttribute('disabled');
          }, 1500);

        } catch (err) {
          if (progressContainer) progressContainer.classList.remove('active');
          showError(err.message || 'Operation failed. Please try again.');
          startBtn.removeAttribute('disabled');
        }
      });
    }
  }
});
