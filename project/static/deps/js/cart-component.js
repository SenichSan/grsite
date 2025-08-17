document.addEventListener("DOMContentLoaded", function () {
    // Элементы компонента
    const cartComponent = document.getElementById('tm-cart-component');
    const cartButton = cartComponent ? cartComponent.querySelector('.tm-cart-button') : null;
    const cartViewUrl = cartComponent ? cartComponent.dataset.cartViewUrl : null;

    const modalRoot = document.getElementById('tm-cart-modal-root');
    const overlay = modalRoot ? modalRoot.querySelector('.tm-cart-overlay') : null;
    const modal = modalRoot ? modalRoot.querySelector('.tm-cart-modal') : null;
    const modalCloseBtn = modalRoot ? modalRoot.querySelector('.tm-cart-modal-close') : null;
    const itemsContainer = document.getElementById('tm-cart-items-container');
    const counterEl = document.getElementById('tm-cart-count');

    const changeUrl = modalRoot ? modalRoot.dataset.cartUpdateUrl : null; // name: carts:cart_change
    // Кнопка удаления может содержать свой data-cart-remove-url, иначе fallback к общему
    const removeDefaultUrl = modalRoot ? modalRoot.dataset.cartRemoveUrl : null; // name: carts:cart_remove

    // Если нет самой кнопки — выходим. Счётчик и модалка зависят от наличия кнопки.
    if (!cartButton) {
        return;
    }

    // Синхронизация с legacy-частью: реагируем на внешние события обновления корзины
    document.addEventListener('cart:updated', function () {
        loadCartCounter();
    });

    // Инициализируем счётчик сразу при загрузке страницы,
    // чтобы не показывать "0" до первого открытия модалки.
    if (cartViewUrl) {
        loadCartCounter();
        // При возврате на страницу из истории (bfcache) — пересчитать
        window.addEventListener('pageshow', function () {
            loadCartCounter();
        });
        // При переключении вкладки назад — пересчитать
        document.addEventListener('visibilitychange', function () {
            if (document.visibilityState === 'visible') {
                loadCartCounter();
            }
        });
    }

    // Открыть модалку (только если структура модалки присутствует на странице)
    cartButton.addEventListener('click', function () {
        if (modal && overlay && modalRoot) {
            openModal();
            loadCart();
        }
    });

    // Закрыть модалку
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeModal);
    }
    if (overlay) {
        overlay.addEventListener('click', closeModal);
    }

    function openModal() {
        if (!overlay || !modal || !modalRoot) return;
        overlay.hidden = false;
        modal.hidden = false;
        modalRoot.classList.add('open');
        document.body.style.overflow = 'hidden';
        document.body.setAttribute('data-modal-open', 'true');
    }

    function closeModal() {
        if (!overlay || !modal || !modalRoot) return;
        overlay.hidden = true;
        modal.hidden = true;
        modalRoot.classList.remove('open');
        document.body.style.overflow = '';
        document.body.removeAttribute('data-modal-open');
    }

    // Загрузка содержимого корзины
    function loadCart() {
        if (!cartViewUrl) return;
        fetch(cartViewUrl, { credentials: 'same-origin', cache: 'no-store' })
            .then((r) => r.json())
            .then((data) => {
                if (itemsContainer && typeof data.cart_items_html !== 'undefined') {
                    itemsContainer.innerHTML = data.cart_items_html;
                }
                if (counterEl && typeof data.total_quantity !== 'undefined') {
                    counterEl.textContent = data.total_quantity;
                }
                // Итого в модалке, если есть отдельный элемент
                const totalSumEl = document.getElementById('tm-cart-total-sum');
                if (totalSumEl && typeof data.total_sum !== 'undefined') {
                    totalSumEl.textContent = data.total_sum;
                }
            })
            .catch(() => {});
    }

    // Лёгкая версия загрузки: только обновить счётчик и, если есть, сумму
    function loadCartCounter() {
        if (!cartViewUrl) return;
        fetch(cartViewUrl, { credentials: 'same-origin' })
            .then((r) => r.json())
            .then((data) => {
                if (counterEl && typeof data.total_quantity !== 'undefined') {
                    counterEl.textContent = data.total_quantity;
                }
                const totalSumEl = document.getElementById('tm-cart-total-sum');
                if (totalSumEl && typeof data.total_sum !== 'undefined') {
                    totalSumEl.textContent = data.total_sum;
                }
            })
            .catch(() => {});
    }

    // Делегирование кликов: +/- и удаление
    document.addEventListener('click', function (e) {
        // Увеличение количества
        if (e.target.classList.contains('qty-increment')) {
            const input = e.target.closest('.cart-row-qty')?.querySelector('.qty-input');
            if (!input) return;
            const cartId = input.dataset.cartId;
            const newQty = parseInt(input.value || '0', 10) + 1;
            input.value = newQty;
            postChange(cartId, newQty);
        }

        // Уменьшение количества
        if (e.target.classList.contains('qty-decrement')) {
            const input = e.target.closest('.cart-row-qty')?.querySelector('.qty-input');
            if (!input) return;
            const current = parseInt(input.value || '1', 10);
            if (current > 1) {
                const cartId = input.dataset.cartId;
                const newQty = current - 1;
                input.value = newQty;
                postChange(cartId, newQty);
            }
        }

        // Удаление позиции
        if (e.target.classList.contains('remove-from-cart')) {
            const btn = e.target;
            const cartId = btn.dataset.cartId;
            const url = btn.dataset.cartRemoveUrl || removeDefaultUrl;
            if (!cartId || !url) return;
            postRemove(cartId, url);
        }
    });

    function postChange(cartId, quantity) {
        if (!changeUrl || !cartId) return;
        const body = new URLSearchParams();
        body.append('cart_id', String(cartId));
        body.append('quantity', String(quantity));
        fetch(changeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body,
            credentials: 'same-origin',
        })
            .then((r) => r.json())
            .then((data) => {
                applyCartResponse(data);
            })
            .catch(() => {});
    }

    function postRemove(cartId, url) {
        const body = new URLSearchParams();
        body.append('cart_id', String(cartId));
        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body,
            credentials: 'same-origin',
        })
            .then((r) => r.json())
            .then((data) => {
                applyCartResponse(data);
            })
            .catch(() => {});
    }

    function applyCartResponse(data) {
        if (data && typeof data.cart_items_html !== 'undefined') {
            itemsContainer.innerHTML = data.cart_items_html;
        }
        if (counterEl && typeof data.total_quantity !== 'undefined') {
            counterEl.textContent = data.total_quantity;
        }
        const totalSumEl = document.getElementById('tm-cart-total-sum');
        if (totalSumEl && typeof data.total_sum !== 'undefined') {
            totalSumEl.textContent = data.total_sum;
        }
    }

    // Вспомогательная функция получения CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
