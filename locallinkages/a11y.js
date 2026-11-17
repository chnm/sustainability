// Expose the small-screen menu button's state (WCAG 4.1.2); Foundation's ResponsiveToggle does not set aria-expanded.
// Loaded by scripts/locallinkages_a11y.py (chnm/sustainability#152).
document.addEventListener('DOMContentLoaded', function () {
  var button = document.querySelector('.menu-icon'), menu = document.getElementById('mobile-menu');
  if (!button || !menu) return;
  button.setAttribute('aria-controls', 'mobile-menu');
  var sync = function () { button.setAttribute('aria-expanded', getComputedStyle(menu).display === 'none' ? 'false' : 'true'); };
  sync();
  button.addEventListener('click', function () { setTimeout(sync, 0); });
});
