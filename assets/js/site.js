// Site-wide interactive behaviors for SmartPark
document.addEventListener('DOMContentLoaded', function () {
  // Initialize Bootstrap tooltips
  try {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
      new bootstrap.Tooltip(tooltipTriggerEl);
    });
  } catch (e) { }

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      var href = this.getAttribute('href');
      if (href.length > 1) {
        var target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });

  // Create toast container helper
  function showToast(message, type) {
    type = type || 'info';
    var toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    var toastEl = document.createElement('div');
    toastEl.className = 'toast align-items-center text-bg-' + (type === 'error' ? 'danger' : (type === 'success' ? 'success' : 'secondary')) + ' border-0';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    toastContainer.appendChild(toastEl);
    var toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    toast.show();
    // remove after hidden
    toastEl.addEventListener('hidden.bs.toast', function () { toastEl.remove(); });
  }

  // Turn Django server messages into toasts (if present)
  var serverMessages = document.querySelectorAll('#server-messages .p-4');
  if (serverMessages && serverMessages.length) {
    serverMessages.forEach(function (el) {
      var text = el.textContent.trim();
      if (text) showToast(text, 'success');
    });
  }

  // AJAX subscribe form handler
  var subscribeForm = document.getElementById('subscribe-form');
  if (subscribeForm) {
    subscribeForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var form = this;
      var url = form.getAttribute('action') || window.location.href;
      var data = new FormData(form);

      // Get CSRF token from cookie
      function getCookie(name) {
        var v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return v ? v.pop() : '';
      }
      var csrftoken = getCookie('csrftoken');

      fetch(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrftoken
        },
        body: data
      }).then(function (resp) {
        if (!resp.ok) throw new Error('Network response was not ok');
        return resp.json();
      }).then(function (json) {
        if (json.success) {
          showToast(json.message || 'Subscribed successfully!', 'success');
          form.reset();
        } else {
          showToast(json.message || 'Subscription failed', 'error');
        }
      }).catch(function (err) {
        showToast('Subscription failed: ' + err.message, 'error');
      });
    });
  }

  // Reveal-on-scroll using IntersectionObserver (adds 'visible' to .reveal elements)
  try {
    var revealObserver = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if(entry.isIntersecting){
          entry.target.classList.add('visible');
          // if element has data-once, unobserve after visible
          if(entry.target.dataset.once !== undefined){
            revealObserver.unobserve(entry.target);
          }
        }
      });
    }, { threshold: 0.12 });

    document.querySelectorAll('.reveal').forEach(function(el){
      // allow staggered delays by reading data-delay (ms)
      var d = el.dataset.delay;
      if(d){ el.style.transitionDelay = d + 'ms'; }
      revealObserver.observe(el);
    });
  } catch(e) { /* IntersectionObserver not supported — leave elements visible */
    document.querySelectorAll('.reveal').forEach(function(el){ el.classList.add('visible'); });
  }

});
