/**
 * Utility to help with style debugging and forced refresh
 * Press CTRL+F5 to force refresh the page and clear cache
 */
(function() {
  // Add a small helper for developers in the console
  console.info(
    '%c ePetCare Style Debug %c Press CTRL+F5 to force refresh and clear cache',
    'background:#573D1C;color:white;padding:4px 8px;border-radius:3px 0 0 3px;',
    'background:#794E24;color:white;padding:4px 8px;border-radius:0 3px 3px 0;'
  );

  // Listen for CTRL+SHIFT+R key combo for quick cache clear
  document.addEventListener('keydown', function(e) {
    // Check for Ctrl+Shift+R
    if (e.ctrlKey && e.shiftKey && e.key === 'R') {
      e.preventDefault();
      console.log('Force refreshing page and clearing style cache...');

      // Clear localStorage cache if you're using it
      try {
        localStorage.removeItem('styleCache');
      } catch (err) {
        // Silent fail if localStorage isn't available
      }

      // Add a random parameter to force new CSS to load
      window.location.href = window.location.href.split('?')[0] +
        '?cache-bust=' + Math.random().toString(36).substring(7);
    }
  });
})();