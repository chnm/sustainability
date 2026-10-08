// The Making Sense of Evidence quizzes write feedback into a textarea or text box when a
// radio is clicked; screen readers don't announce that. Echo whatever a click
// changed into a status region (WCAG 4.1.3, chnm/sustainability#120).
(function () {
  var status = document.createElement('div');
  status.setAttribute('role', 'status');
  status.className = 'visually-hidden';
  document.body.appendChild(status);

  document.addEventListener('click', function () {
    var areas = document.querySelectorAll('textarea, input[type="text"]');
    var before = Array.prototype.map.call(areas, function (a) { return a.value; });
    setTimeout(function () { // after the page's own onclick handler has run
      Array.prototype.forEach.call(areas, function (a, i) {
        if (a.value !== before[i]) status.textContent = a.value;
      });
    }, 0);
  }, true);
})();
