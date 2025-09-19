document.addEventListener('DOMContentLoaded', function () {
    // Бургер-меню
    const burger = document.querySelector('.header-button-hamburger');
    if (burger) {
        burger.addEventListener('click', function () {
            document.querySelector('.header-menu').classList.toggle('is-show');
            this.classList.toggle('is-show');
        });
    }

    // Кнопки «Избранное»
    document.querySelectorAll('.product-content-favorite-button').forEach(function (item) {
        item.addEventListener('click', function () {
            this.classList.toggle('is-fav');
        });
    });

    // Увеличение количества
    document.querySelectorAll('.product-quantity-input-increase').forEach(function (item) {
        item.addEventListener('click', function () {
            const input = this.parentElement.querySelector('.product-quantity-input-number');
            const currentValue = parseInt(input.value, 10) || 0;
            const maxValue = parseInt(input.getAttribute('max'), 10);
            if (!isNaN(maxValue) && currentValue >= maxValue) {
                input.value = maxValue;
            } else {
                input.value = currentValue + 1;
            }
        });
    });

    // Уменьшение количества
    document.querySelectorAll('.product-quantity-input-decrease').forEach(function (item) {
        item.addEventListener('click', function () {
            const input = this.parentElement.querySelector('.product-quantity-input-number');
            const currentValue = parseInt(input.value, 10) || 0;
            const minValue = parseInt(input.getAttribute('min'), 10);
            if (!isNaN(minValue) && currentValue <= minValue) {
                input.value = minValue;
            } else {
                input.value = currentValue - 1;
            }
        });
    });

    // Кнопка поиска в шапке
    const searchBtn = document.querySelector('.header-button-search');
    if (searchBtn) {
        searchBtn.addEventListener('click', function () {
            document.querySelector('.header-button').classList.toggle('is-show');
            this.classList.toggle('is-show');
        });
    }

    // Инициализация Swiper на странице товара
    if (document.querySelector('.product-swiper')) {
        // Миниатюры
        const productThumbs = new Swiper('.product-thumb-swiper', {
            spaceBetween: 12,
            slidesPerView: 'auto',
            watchSlidesVisibility: true,
            watchSlidesProgress: true,
            breakpoints: {
                768: {
                    spaceBetween: 24,
                }
            }
        });

        // Основной слайдер
        const productSwiper = new Swiper('.product-swiper', {
            loop: false,
            rewind: true,
            slidesPerView: 1,
            spaceBetween: 0,
            centeredSlides: false,
            watchOverflow: true,
            thumbs: { swiper: productThumbs },
        });

        // Счётчик слайдов на главном слайдере был удалён

        // Кнопки «Вперёд/Назад»
        const nextBtn = document.querySelector('.product-image-order-next');
        const prevBtn = document.querySelector('.product-image-order-previous');

        if (nextBtn) {
            nextBtn.addEventListener('click', function () {
                productSwiper.slideNext();
            });
        }
        if (prevBtn) {
            prevBtn.addEventListener('click', function () {
                productSwiper.slidePrev();
            });
        }
    }
});

    // Lightbox
    const modal      = document.getElementById('image-modal');
    const modalImg   = modal.querySelector('.image-modal__img');
    const modalClose = modal.querySelector('.image-modal__close');
    const modalBg    = modal.querySelector('.image-modal__backdrop');
    const modalPrev  = modal.querySelector('.image-modal__prev');
    const modalNext  = modal.querySelector('.image-modal__next');

    // Collect gallery images (from main swiper). Use currentSrc to prefer chosen source
    const galleryImgs = Array.from(document.querySelectorAll('.product-swiper .swiper-slide img'));
    let currentIndex = -1;

    function updateModalSrcByIndex(idx) {
        if (!galleryImgs.length) return;
        // clamp
        if (idx < 0) idx = galleryImgs.length - 1;
        if (idx >= galleryImgs.length) idx = 0;
        currentIndex = idx;
        const el = galleryImgs[currentIndex];
        // Use currentSrc (falls back to src) to pick the actually loaded source
        const src = el.currentSrc || el.src;
        modalImg.src = src;
    }

    function hideTawk(forceDom) {
        try { if (window.Tawk_API && typeof window.Tawk_API.hideWidget === 'function') { window.Tawk_API.hideWidget(); return; } } catch(e){}
        if (!forceDom) return;
        // Fallback: try to hide common containers
        const candidates = document.querySelectorAll('iframe[src*="tawk.to"], iframe[id^="tawk"], div[id^="tawk"], div[class^="tawk"], #tawkchat-minified-wrapper, #tawkchat-status-text-container, #tawkchat-container, #tawkchat-iframe-container');
        candidates.forEach(n=>{ n.style.setProperty('display','none','important'); n.style.setProperty('visibility','hidden','important'); n.style.setProperty('opacity','0','important'); n.style.setProperty('pointer-events','none','important'); });
    }
    function showTawk() {
        try { if (window.Tawk_API && typeof window.Tawk_API.showWidget === 'function') { window.Tawk_API.showWidget(); return; } } catch(e){}
        // Attempt to revert styles for fallback hidden nodes
        const candidates = document.querySelectorAll('iframe[src*="tawk.to"], iframe[id^="tawk"], div[id^="tawk"], div[class^="tawk"], #tawkchat-minified-wrapper, #tawkchat-status-text-container, #tawkchat-container, #tawkchat-iframe-container');
        candidates.forEach(n=>{ n.style.removeProperty('display'); n.style.removeProperty('visibility'); n.style.removeProperty('opacity'); n.style.removeProperty('pointer-events'); });
    }

    function showModalByIndex(idx) {
        updateModalSrcByIndex(idx);
        modal.style.display = 'block';
        // Hide header, cart button and chat via CSS hook
        document.body.classList.add('modal-open');
        hideTawk(true);
        // Prevent background scroll
        document.body.style.overflow = 'hidden';
    }
    function showModal(src) {
        // derive index by matching src among gallery, else keep direct src
        let idx = galleryImgs.findIndex(el => (el.currentSrc||el.src) === src);
        if (idx === -1) { modalImg.src = src; currentIndex = -1; }
        showModalByIndex(idx === -1 ? 0 : idx);
    }
    function hideModal() {
        modal.style.display = 'none';
        modalImg.src = '';
        document.body.classList.remove('modal-open');
        showTawk();
        // Restore background scroll
        document.body.style.overflow = '';
    }

document.querySelectorAll('.product-swiper .swiper-slide img').forEach(img => {
    img.style.cursor = 'zoom-in';
    img.addEventListener('click', () => showModal(img.src));
});
modalClose.addEventListener('click', hideModal);
modalBg.addEventListener('click', hideModal);
if (modalPrev) modalPrev.addEventListener('click', () => { if (galleryImgs.length) showModalByIndex(currentIndex - 1); });
if (modalNext) modalNext.addEventListener('click', () => { if (galleryImgs.length) showModalByIndex(currentIndex + 1); });

// Close on ESC
document.addEventListener('keydown', (e) => {
  if (!modal || modal.style.display !== 'block') return;
  if (e.key === 'Escape') { hideModal(); }
  else if (e.key === 'ArrowLeft') { if (galleryImgs.length) showModalByIndex(currentIndex - 1); }
  else if (e.key === 'ArrowRight') { if (galleryImgs.length) showModalByIndex(currentIndex + 1); }
});

document.addEventListener('DOMContentLoaded', () => {
  // …существующая инициализация product-swiper…

  // А потом, когда DOM гарантированно готов:
  if (document.querySelector('.tm-featured-carousel')) {
    new Swiper('.tm-featured-carousel', {
      slidesPerView: 4,
      spaceBetween: 20,
      navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
      },
      breakpoints: {
        320:  { slidesPerView: 1 },
        640:  { slidesPerView: 2 },
        1024: { slidesPerView: 4 },
      },
    });
  }
});