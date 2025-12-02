/**
 * Dark Mode Toggle Script for ePetCare
 * Handles dark mode toggle functionality with localStorage persistence
 */

(function() {
  'use strict';

  // Initialize dark mode from localStorage on page load
  function initDarkMode() {
    const darkModeEnabled = localStorage.getItem('darkMode') === 'enabled';
    
    if (darkModeEnabled) {
      document.body.classList.add('dark-mode');
      updateToggleButton(true);
    } else {
      document.body.classList.remove('dark-mode');
      updateToggleButton(false);
    }
  }

  // Toggle dark mode
  function toggleDarkMode() {
    const isDarkMode = document.body.classList.toggle('dark-mode');
    
    // Save preference to localStorage
    if (isDarkMode) {
      localStorage.setItem('darkMode', 'enabled');
      updateToggleButton(true);
    } else {
      localStorage.setItem('darkMode', 'disabled');
      updateToggleButton(false);
    }
  }

  // Update the toggle button appearance
  function updateToggleButton(isDarkMode) {
    const toggleBtn = document.getElementById('darkModeToggle');
    if (!toggleBtn) return;

    if (isDarkMode) {
      toggleBtn.innerHTML = '☀️';
      toggleBtn.setAttribute('aria-label', 'Switch to light mode');
      toggleBtn.setAttribute('title', 'Light Mode');
    } else {
      toggleBtn.innerHTML = '🌙';
      toggleBtn.setAttribute('aria-label', 'Switch to dark mode');
      toggleBtn.setAttribute('title', 'Dark Mode');
    }
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDarkMode);
  } else {
    initDarkMode();
  }

  // Attach toggle function to window for global access
  window.toggleDarkMode = toggleDarkMode;

  // Add event listener when DOM is ready
  document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('darkModeToggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', toggleDarkMode);
    }
  });

})();
