(function () {
  "use strict";

  // Footer year
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Mobile nav toggle
  var navToggle = document.getElementById("navToggle");
  var mainNav = document.getElementById("mainNav");
  var headerActions = document.querySelector(".header-actions");

  if (navToggle && mainNav) {
    navToggle.addEventListener("click", function () {
      var isOpen = navToggle.getAttribute("aria-expanded") === "true";
      navToggle.setAttribute("aria-expanded", String(!isOpen));
      mainNav.classList.toggle("open", !isOpen);
      if (headerActions) headerActions.classList.toggle("open", !isOpen);
    });

    mainNav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        navToggle.setAttribute("aria-expanded", "false");
        mainNav.classList.remove("open");
        if (headerActions) headerActions.classList.remove("open");
      });
    });
  }

  // Contact form -> mailto fallback (no backend wired up yet)
  var form = document.getElementById("contactForm");
  var formNote = document.getElementById("formNote");

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }

      var name = form.name.value.trim();
      var email = form.email.value.trim();
      var phone = form.phone.value.trim();
      var service = form.service.value;
      var message = form.message.value.trim();

      var subject = "Quote request: " + service;
      var bodyLines = [
        "Name: " + name,
        "Email: " + email,
        "Phone: " + (phone || "-"),
        "Service: " + service,
        "",
        message
      ];
      var body = bodyLines.join("\n");

      var mailto =
        "mailto:info@jwdc.co.uk" +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(body);

      window.location.href = mailto;

      if (formNote) {
        formNote.textContent = "Opening your email client with these details filled in — send the email to complete your enquiry.";
      }
    });
  }

  // Scroll reveal
  var revealTargets = document.querySelectorAll(
    ".service-card, .feature, .process-step, .gallery-item, .about-grid, .contact-grid"
  );

  if ("IntersectionObserver" in window && revealTargets.length) {
    revealTargets.forEach(function (el) {
      el.style.opacity = "0";
      el.style.transform = "translateY(16px)";
      el.style.transition = "opacity .5s ease, transform .5s ease";
    });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0)";
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    revealTargets.forEach(function (el) { observer.observe(el); });
  }
})();
