const note = document.querySelector('.copy-note');

document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const value = button.dataset.copy;
    try {
      await navigator.clipboard.writeText(value);
      note.textContent = `copied: ${value}`;
      button.textContent = 'done';
      window.setTimeout(() => {
        button.textContent = 'copy';
        note.textContent = '';
      }, 1800);
    } catch {
      note.textContent = 'Copy is unavailable here; select the command manually.';
    }
  });
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.style.animationPlayState = 'running';
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach((element) => {
  element.style.animationPlayState = 'paused';
  observer.observe(element);
});
