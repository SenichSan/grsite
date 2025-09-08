/* create_order.js: behaviors for the checkout page */
(function() {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function formatCurrency(n) {
    const val = Math.round(Number(n) || 0).toString();
    return val + ' ₴';
  }

  function parseNum(val) {
    if (val == null) return 0;
    if (typeof val === 'number') return val;
    const s = String(val)
      .replace(/[^0-9,\.\-]/g, '') // strip currency, spaces, nbsp
      .replace(',', '.');
    const n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  }

  function initCommentPlaceholder() {
    const ta = document.getElementById('order_comment');
    if (!ta) return;
    // keep original placeholder
    const original = ta.getAttribute('placeholder') || '';
    ta.dataset.placeholder = original;
    ta.addEventListener('focus', function() {
      // hide placeholder immediately on focus
      ta.setAttribute('placeholder', '');
    });
    ta.addEventListener('blur', function() {
      if (!ta.value.trim()) {
        ta.setAttribute('placeholder', ta.dataset.placeholder || original);
      }
    });
  }

  function formatUaPhone(digits) {
    // Normalize to UA format starting with 380 and total 12 digits (380 + 9)
    if (!digits) return '';
    // Convert common inputs to 380XXXXXXXXX
    if (digits[0] === '0' && digits.length >= 10) {
      digits = '380' + digits.slice(1);
    } else if (digits.startsWith('80') && digits.length >= 11) {
      digits = '3' + digits; // 380...
    } else if (!digits.startsWith('380')) {
      // If user started typing without country code, prepend progressively
      if (digits.length <= 9) digits = '380' + digits.padStart(9, '');
    }
    // Keep only first 12 digits
    digits = digits.replace(/\D/g, '').slice(0, 12);
    // If we still don't have 380 prefix, bail with raw
    if (!digits.startsWith('380')) return '+' + digits;

    // Build +380 XX XXX XX XX
    const c = '+380';
    const op = digits.slice(3, 5);
    const p1 = digits.slice(5, 8);
    const p2 = digits.slice(8, 10);
    const p3 = digits.slice(10, 12);
    let out = c;
    if (op) out += ' ' + op;
    if (p1) out += ' ' + p1;
    if (p2) out += ' ' + p2;
    if (p3) out += ' ' + p3;
    return out;
  }

  function isValidUaPhone(val) {
    return /^\+?380\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}$/.test(val.trim());
  }

  function initPhoneMask() {
    const input = document.getElementById('id_phone_number');
    if (!input) return;
    const err = document.getElementById('phone_number_error');

    function updateMaskFromRaw() {
      const rawDigits = input.value.replace(/\D/g, '');
      const formatted = formatUaPhone(rawDigits);
      input.value = formatted;
    }

    function showError(show) {
      if (!err) return;
      err.style.display = show ? '' : 'none';
      if (show) input.classList.add('is-invalid'); else input.classList.remove('is-invalid');
    }

    input.addEventListener('input', function() {
      const pos = input.selectionStart;
      updateMaskFromRaw();
      // Best-effort caret keep near end
      input.setSelectionRange(input.value.length, input.value.length);
      if (isValidUaPhone(input.value)) showError(false);
    });

    input.addEventListener('blur', function() {
      if (!input.value.trim()) { showError(false); return; }
      if (!isValidUaPhone(input.value)) showError(true); else showError(false);
    });

    const form = document.getElementById('create_order_form');
    if (form) {
      form.addEventListener('submit', function(e) {
        if (!isValidUaPhone(input.value)) {
          showError(true);
          e.preventDefault();
          e.stopPropagation();
          input.focus();
        }
      });
    }

    // Initialize once on load
    updateMaskFromRaw();
  }

  function initEmailValidation() {
    const email = document.getElementById('id_email');
    if (!email) return;
    function toggle() {
      if (!email.value) { email.classList.remove('is-invalid'); return; }
      if (email.checkValidity()) email.classList.remove('is-invalid');
      else email.classList.add('is-invalid');
    }
    email.addEventListener('blur', toggle);
    email.addEventListener('input', function(){ if (email.classList.contains('is-invalid')) toggle(); });
  }

  function recalcTotals() {
    let total = 0;
    let totalDiscount = 0;

    document.querySelectorAll('.order-item-row').forEach(function(row) {
      const qtyEl = row.querySelector('.qty-value');
      const qty = parseNum(qtyEl ? qtyEl.textContent.trim() : row.dataset.quantity);
      const unit = parseNum(row.dataset.unitPrice || row.getAttribute('data-unit-price'));
      let sell = parseNum(row.dataset.sellPrice || row.getAttribute('data-sell-price'));
      if (!sell) {
        // try to read from DOM new price
        const newPriceEl = row.querySelector('.unit-price .new-price');
        if (newPriceEl) sell = parseNum(newPriceEl.textContent);
      }
      if (!sell) {
        const discountPct = parseNum(row.dataset.discount || row.getAttribute('data-discount'));
        if (discountPct) sell = Math.max(0, unit - unit * (discountPct / 100));
        else sell = unit;
      }
      const lineSum = sell * qty;
      const perUnitDiscount = Math.max(0, unit - sell);
      total += lineSum;
      totalDiscount += perUnitDiscount * qty;
      const lineSumCell = row.querySelector('.line-sum');
      if (lineSumCell) lineSumCell.textContent = formatCurrency(lineSum);
    });

    const totalCell = document.querySelector('.table-total td.text-end:last-child, .table-total td:last-child');
    if (totalCell) {
      const strong = totalCell.querySelector('strong');
      const val = formatCurrency(total);
      if (strong) strong.textContent = val; else totalCell.textContent = val;
    }

    const discountEl = document.getElementById('order-total-discount');
    if (discountEl) discountEl.textContent = formatCurrency(totalDiscount);
  }

  function bindQtyButtons() {
    const container = document.querySelector('.checkout-order-summary');
    if (!container) return;
    const changeUrl = container.getAttribute('data-cart-change-url');
    if (!changeUrl) return;

    container.addEventListener('click', function(e) {
      const incBtn = e.target.closest('.order-qty-inc');
      const decBtn = e.target.closest('.order-qty-dec');
      if (!incBtn && !decBtn) return;
      const row = e.target.closest('.order-item-row');
      if (!row) return;
      const cartId = row.getAttribute('data-cart-id');
      if (!cartId) return;

      const action = incBtn ? 'increment' : 'decrement';
      const csrftoken = getCookie('csrftoken');
      fetch(changeUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
          'X-CSRFToken': csrftoken
        },
        body: new URLSearchParams({ cart_id: cartId, action })
      }).then(function(res) { return res.json(); })
        .then(function(_data) {
          // Update UI locally based on action
          const qtyEl = row.querySelector('.qty-value');
          let qty = Number(qtyEl.textContent.trim()) || 0;
          if (action === 'increment') qty += 1; else qty -= 1;
          if (qty <= 0) {
            row.remove();
          } else {
            qtyEl.textContent = String(qty);
            row.setAttribute('data-quantity', String(qty));
          }
          recalcTotals();
        })
        .catch(function() {
          // no-op; keep UI unchanged on error
        });
    });
  }

  function initNovaPoshta() {
    const $ = window.jQuery;
    if (!$) return;
    // Use backend proxy endpoints to avoid CORS and keep API key server-side
    const ENDPOINT_SEARCH_CITY = "/orders/ajax/search-city/";
    const ENDPOINT_GET_WAREHOUSES = "/orders/ajax/get-warehouses/";
    let selectedCity = "";
    // Track in-flight XHR to cancel when a newer request starts
    let inflightSearch = null;
    let inflightWarehouses = null;

    $(function() {
      $("#nova_city").autocomplete({
        minLength: 2,
        source(request, response) {
          const term = String(request.term || '').trim();
          if (term.length < 2) { response([]); return; }
          requestCitiesDebounced(term, response);
        },
        select(event, ui) {
          $('#nova_city_ref').val(ui.item.ref);
          selectedCity = ui.item.label;
          $('#nova_city').val(selectedCity);

          // Prepare warehouses select
          const $w = $('#warehouse_display');
          // If Select2 already initialized, destroy to avoid duplicates
          if ($w.hasClass('select2-hidden-accessible')) {
            try { $w.select2('destroy'); } catch(e) {}
          }
          // Reset and show loading state
          $w.empty().prop('disabled', true).append(new Option('Завантаження...', ''));

          // Abort previous warehouses request if still running
          if (inflightWarehouses && inflightWarehouses.readyState !== 4) {
            try { inflightWarehouses.abort(); } catch(e) {}
          }

          inflightWarehouses = $.ajax({
            url: ENDPOINT_GET_WAREHOUSES,
            method: "GET",
            dataType: "json",
            timeout: 10000,
            data: { settlement_ref: ui.item.ref }
          }).done(function(res){
            const list = (res && res.success && Array.isArray(res.warehouses)) ? res.warehouses : [];
            $w.empty();
            if (list.length === 0) {
              $w.append(new Option('Відділення не знайдені', ''));
            } else {
              list.forEach(function(desc){ $w.append(new Option(desc, desc)); });
            }
            $w.prop('disabled', false);

            // Re-init Select2 and bind change handler once
            $w.off('change');
            $w.select2({ placeholder: 'Оберіть відділення', width: '100%' });
            $w.on('change', function () {
              const warehouseText = $(this).find('option:selected').text();
              $('#id_delivery_address').val(`${selectedCity}, ${warehouseText}`);
            });
          }).fail(function(){
            $w.empty().prop('disabled', false).append(new Option('Помилка завантаження відділень', ''));
          });
        }
      });

      $('#create_order_form').on('submit', function() {
        const city = $('#nova_city').val();
        const wh = $('#warehouse_display option:selected').text();
        if (city && wh) {
          $('#id_delivery_address').val(`${city}, ${wh}`);
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    bindQtyButtons();
    recalcTotals();
    initNovaPoshta();
    initCommentPlaceholder();
    initPhoneMask();
    initEmailValidation();
  });
})();
