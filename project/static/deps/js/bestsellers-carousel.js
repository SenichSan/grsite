document.addEventListener('click', function(e){
  const btn = e.target.closest('.add-to-cart-btn');
  if (!btn) return;
  const pressed = btn.getAttribute('aria-pressed') === 'true';
  btn.setAttribute('aria-pressed', String(!pressed));
  if (btn.animate) {
    btn.animate(
      [ { transform: 'translateY(0)' }, { transform: 'translateY(-4px)' }, { transform: 'translateY(0)' } ],
      { duration: 220 }
    );
  }
  // AJAX обрабатывает jquery-ajax.js
});
