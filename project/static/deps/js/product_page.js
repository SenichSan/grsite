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
            spaceBetween: 10,
            thumbs: {
                swiper: productThumbs
            }
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

    function showModal(src) {
        modalImg.src = src;
        modal.style.display = 'block';
    }
    function hideModal() {
        modal.style.display = 'none';
        modalImg.src = '';
    }

document.querySelectorAll('.product-swiper .swiper-slide img').forEach(img => {
    img.style.cursor = 'zoom-in';
    img.addEventListener('click', () => showModal(img.src));
});
modalClose.addEventListener('click', hideModal);
modalBg.addEventListener('click', hideModal);

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