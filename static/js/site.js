// Mobile menu toggle. The menu stays visible if JavaScript is off (see .no-js in CSS).
(function () {
  document.documentElement.classList.remove('no-js');
  var btn = document.querySelector('.nav-toggle');
  var nav = document.getElementById('primary-nav');
  if (!btn || !nav) return;
  btn.addEventListener('click', function () {
    var open = nav.classList.toggle('is-open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.querySelector('.nav-toggle-label').textContent = open ? 'Close' : 'Menu';
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) { btn.click(); btn.focus(); }
  });
})();

// Forms marked data-placeholder aren't connected to a form service yet: after the browser's
// required-field checks pass, go to the thank-you page without sending anything.
document.querySelectorAll('form[data-placeholder]').forEach(function (form) {
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    window.location.href = form.action;
  });
});
