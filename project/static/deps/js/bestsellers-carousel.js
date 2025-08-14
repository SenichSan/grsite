<script>
document.addEventListener('click', function(e){
  const btn = e.target.closest('.add-to-cart-btn');
  if(!btn) return;
  const pressed = btn.getAttribute('aria-pressed') === 'true';
  btn.setAttribute('aria-pressed', String(!pressed));
  btn.animate([{ transform: 'translateY(0)' }, { transform: 'translateY(-4px)' }, { transform: 'translateY(0)' }], { duration: 220 });
  // сюда позже можно добавить AJAX-запрос добавления в корзину
});
</script>
