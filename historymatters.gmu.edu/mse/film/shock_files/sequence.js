// Plays the four clips in the order picked with the selects. Replaces the old
// Flash drag-and-drop exercise (train_sequence9.swf); the clips were recovered
// from that file (chnm/sustainability#120).
(function () {
  var video = document.getElementById('seq-video');
  var status = document.getElementById('seq-status');
  var queue = [];

  function next() {
    if (!queue.length) { status.textContent = 'Finished.'; return; }
    var clip = queue.shift();
    status.textContent = 'Playing clip ' + clip + '.';
    video.src = 'shock_files/clip_' + clip.toLowerCase() + '.mp4';
    video.play();
  }

  video.addEventListener('ended', next);
  document.getElementById('seq-play').addEventListener('click', function () {
    queue = [1, 2, 3, 4].map(function (n) { return document.getElementById('seq' + n).value; });
    next();
  });
})();
