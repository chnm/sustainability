/* Self-contained, accessible image lightbox — replaces the defunct Zoom.it
   viewer. No dependencies. Targets links with class "zoomit_images" (each
   points to a full-resolution image).

   Accessibility (WCAG 2.2 AA):
   - Modal dialog: role="dialog" + aria-modal, focus moved in on open, focus
     trapped (Tab cycles), Esc closes, focus returned to the trigger on close.
   - Fully keyboard-operable: Prev/Next/Zoom/Close are real <button>s; Left/Right
     browse; the zoom toggle is a button (no mouse-only zoom).
   - Pan without dragging: when zoomed the stage scrolls — pointer users pan with
     the scrollbars (no drag, SC 2.5.7), keyboard users focus the stage and use
     arrow keys (SC 2.1.1). Mouse drag is an optional extra.
   - Controls are white on a near-black overlay (high contrast) with visible
     focus rings and >=24px targets. */
(function () {
  "use strict";
  var links = Array.prototype.slice.call(document.querySelectorAll(".zoomit_images"));
  if (!links.length) return;

  var css =
    ".lb-overlay{position:fixed;inset:0;background:#0b0b0b;z-index:10000;display:none;flex-direction:column}" +
    ".lb-overlay.lb-open{display:flex}" +
    ".lb-bar{display:flex;align-items:center;gap:10px;padding:8px 14px;color:#fff;flex:0 0 auto}" +
    ".lb-caption{flex:1;font-weight:bold;font-size:1.05em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
    ".lb-btn{min-width:44px;min-height:36px;background:#000;color:#fff;border:1px solid #fff;border-radius:3px;font-size:1.05em;line-height:1.2;padding:6px 12px;cursor:pointer}" +
    ".lb-btn:hover{background:#333}" +
    ".lb-stage{flex:1 1 auto;overflow:auto;display:flex;align-items:center;justify-content:center;padding:6px}" +
    ".lb-stage:focus{outline:2px dashed #ffe000;outline-offset:-4px}" +
    ".lb-img{max-width:100%;max-height:100%;user-select:none;-webkit-user-drag:none}" +
    ".lb-stage.lb-zoomed{align-items:start;justify-content:start;cursor:grab}" +
    ".lb-stage.lb-zoomed .lb-img{max-width:none;max-height:none}" +
    ".lb-stage.lb-panning{cursor:grabbing}" +
    ".lb-hint{flex:0 0 auto;color:#d0d0d0;text-align:center;font-size:.85em;padding:6px}";
  var style = document.createElement("style");
  style.appendChild(document.createTextNode(css));
  document.head.appendChild(style);

  var ov = document.createElement("div");
  ov.className = "lb-overlay";
  ov.setAttribute("role", "dialog");
  ov.setAttribute("aria-modal", "true");
  ov.setAttribute("aria-label", "Image viewer");
  ov.innerHTML =
    '<div class="lb-bar">' +
      '<button type="button" class="lb-btn lb-prev" aria-label="Previous image">&#8249;</button>' +
      '<button type="button" class="lb-btn lb-next" aria-label="Next image">&#8250;</button>' +
      '<button type="button" class="lb-btn lb-zoom" aria-pressed="false">Zoom in</button>' +
      '<span class="lb-caption" aria-live="polite"></span>' +
      '<button type="button" class="lb-btn lb-close" aria-label="Close image viewer">&#10005; Close</button>' +
    "</div>" +
    '<div class="lb-stage" tabindex="0" aria-label="Image (arrow keys scroll when zoomed)">' +
      '<img class="lb-img" alt="">' +
    "</div>" +
    '<p class="lb-hint">Use Zoom, then pan with the scrollbars or arrow keys · &#8249; &#8250; browse · Esc closes</p>';
  document.body.appendChild(ov);

  var stage = ov.querySelector(".lb-stage"),
      img = ov.querySelector(".lb-img"),
      cap = ov.querySelector(".lb-caption"),
      zoomBtn = ov.querySelector(".lb-zoom"),
      idx = 0, trigger = null, zoomed = false,
      drag = false, sx = 0, sy = 0;

  function setZoom(on) {
    zoomed = on;
    stage.classList.toggle("lb-zoomed", on);
    zoomBtn.setAttribute("aria-pressed", on ? "true" : "false");
    zoomBtn.textContent = on ? "Zoom out" : "Zoom in";
    stage.scrollTop = 0; stage.scrollLeft = 0;
  }
  function show(i) {
    idx = (i + links.length) % links.length;
    var a = links[idx], label = (a.textContent || "Image").trim();
    setZoom(false);
    img.src = a.href;
    img.alt = label;
    cap.textContent = label;
  }
  function open(i) {
    trigger = document.activeElement;
    show(i);
    ov.classList.add("lb-open");
    ov.querySelector(".lb-close").focus();
    document.addEventListener("keydown", onKey, true);
  }
  function close() {
    ov.classList.remove("lb-open");
    document.removeEventListener("keydown", onKey, true);
    img.removeAttribute("src");
    if (trigger && trigger.focus) trigger.focus();
  }

  zoomBtn.addEventListener("click", function () { setZoom(!zoomed); if (zoomed) stage.focus(); });
  ov.querySelector(".lb-close").addEventListener("click", close);
  ov.querySelector(".lb-prev").addEventListener("click", function () { show(idx - 1); });
  ov.querySelector(".lb-next").addEventListener("click", function () { show(idx + 1); });
  ov.addEventListener("mousedown", function (e) { if (e.target === ov) close(); });

  // optional mouse drag-pan (scrollbars + keyboard are the accessible pan paths)
  stage.addEventListener("mousedown", function (e) {
    if (!zoomed || e.target !== img) return;
    drag = true; stage.classList.add("lb-panning");
    sx = e.clientX + stage.scrollLeft; sy = e.clientY + stage.scrollTop; e.preventDefault();
  });
  window.addEventListener("mousemove", function (e) {
    if (!drag) return; stage.scrollLeft = sx - e.clientX; stage.scrollTop = sy - e.clientY;
  });
  window.addEventListener("mouseup", function () { drag = false; stage.classList.remove("lb-panning"); });

  function onKey(e) {
    if (!ov.classList.contains("lb-open")) return;
    if (e.key === "Escape") { e.preventDefault(); close(); return; }
    if (e.key === "Tab") {
      var f = ov.querySelectorAll("button, .lb-stage");
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      return;
    }
    // let the focused, zoomed stage scroll natively with the arrow keys
    if (document.activeElement === stage && zoomed) return;
    if (e.key === "ArrowLeft") { e.preventDefault(); show(idx - 1); }
    else if (e.key === "ArrowRight") { e.preventDefault(); show(idx + 1); }
  }

  links.forEach(function (a, i) {
    a.addEventListener("click", function (e) { e.preventDefault(); open(i); });
  });
})();
