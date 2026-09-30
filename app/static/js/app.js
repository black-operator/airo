(() => {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("airo-theme");
  if (savedTheme) root.dataset.theme = savedTheme;

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const next = root.dataset.theme === "light" ? "dark" : "light";
      root.dataset.theme = next;
      localStorage.setItem("airo-theme", next);
    });
  });

  const sidebar = document.querySelector("[data-sidebar]");
  const scrim = document.querySelector("[data-nav-scrim]");
  const toggleNavigation = () => {
    sidebar?.classList.toggle("is-open");
    scrim?.classList.toggle("is-visible");
  };
  document.querySelectorAll("[data-nav-toggle]").forEach((button) => button.addEventListener("click", toggleNavigation));
  scrim?.addEventListener("click", toggleNavigation);

  document.querySelectorAll("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => button.parentElement.remove());
  });
  document.querySelectorAll("[data-confirm]").forEach((button) => {
    button.addEventListener("click", (event) => {
      if (!window.confirm(button.dataset.confirm)) event.preventDefault();
    });
  });

  document.querySelectorAll("[data-avatar-input]").forEach((input) => {
    input.addEventListener("change", () => {
      const file = input.files?.[0];
      const holder = input.closest("[data-avatar-upload]")?.querySelector(".avatar");
      if (!file || !holder) return;
      const image = document.createElement("img");
      image.alt = "Vorschau";
      image.src = URL.createObjectURL(file);
      holder.replaceChildren(image);
    });
  });
})();
