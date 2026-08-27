/* ═══════════════════════════════════════════════════════════════════════════
   МАГАЗИН: витрина, корзина, оформление заказа.

   Товары этот файл не описывает — они лежат в js/merch-catalog.js, и править
   надо только его. Здесь только логика, общая для русской и английской
   страниц: язык каждая страница задаёт сама через MERCH_LANG.

   ── ВКЛЮЧАТЬ РУКАМИ НИЧЕГО НЕ НАДО ────────────────────────────────────────
   Страница сама спрашивает сервис магазина, готов ли он принимать заказы.
   Отвечает — работают и оплата картой, и заказ с оплатой при встрече.
   Молчит (сервис не поднят или ещё без ключей оплаты) — «оформить заказ»
   просто показывает, что ушло бы на сервер, и никуда не отправляет.
   ═══════════════════════════════════════════════════════════════════════ */

var SHOP = {
  live: false,                       // ставится сам, см. askService() ниже
  api: '/api',                       // адрес сервиса магазина
  telegram: 'https://t.me/beloved_dasha',
  thanks: { ru: 'merch-spasibo', en: 'merch-spasibo-en' }
};

(function () {
  'use strict';

  var LANG = (typeof MERCH_LANG !== 'undefined') ? MERCH_LANG : 'ru';
  var KEY = 'sp_merch_cart_v1';

  /* ── тексты интерфейса ──────────────────────────────────────────────── */
  var T = {
    ru: {
      cart: 'корзина', add: 'предзаказ', added: 'добавлено',
      empty: 'пока пусто. выбери что-нибудь на странице',
      total: 'итого', remove: 'убрать', soldout: 'закончилось',
      photosoon: 'фото скоро', close: 'закрыть', checkout: 'оформить предзаказ',
      frame: 'кадр', prev: 'предыдущий кадр', next: 'следующий кадр',
      how: 'как удобно оплатить',
      card: 'картой онлайн',
      cardNote: 'защищённая страница stripe · apple pay и google pay',
      cash: 'наличными при встрече',
      cashNote: 'заберёшь у меня в лиссабоне, когда тираж будет готов',
      order: 'оформление', back: '← вернуться в корзину',
      fName: 'как тебя зовут', fTelegram: 'телеграм',
      fPhone: 'телефон, если удобно', fComment: 'что-то важное про заказ',
      optional: 'необязательно',
      send: 'отправить предзаказ', sending: 'отправляю…',
      req: 'заполни это поле',
      cashFoot: 'оплата при встрече, ничего платить сейчас не нужно. я напишу тебе, когда тираж будет готов',
      pre: 'это предзаказ: вещь шьётся под тебя, изготовление занимает до 4 недель. '+
           'доставка в стоимость не входит и считается отдельно: я напишу тебе, и мы договоримся об удобном способе доставки',
      agree: 'оформляя предзаказ, ты соглашаешься с обработкой персональных данных, ' +
             '<a href="politika" target="_blank" rel="noopener">политика конфиденциальности</a>',
      err: 'что-то пошло не так. напиши мне в телеграм, и я оформлю заказ руками',
      demo: 'оплата ещё не подключена',
      demoText: 'сервис магазина пока не запущен, поэтому заказ никуда не ушёл. вот ровно то, что отправится на сервер, когда всё включим:',
      demoTg: 'написать в телеграм'
    },
    en: {
      cart: 'cart', add: 'pre-order', added: 'added',
      empty: 'empty for now, pick something on the page',
      total: 'total', remove: 'remove', soldout: 'sold out',
      photosoon: 'photo coming', close: 'close', checkout: 'place pre-order',
      frame: 'frame', prev: 'previous frame', next: 'next frame',
      how: 'how would you like to pay',
      card: 'card online',
      cardNote: 'secure stripe page · apple pay and google pay',
      cash: 'cash when we meet',
      cashNote: 'pick it up from me in lisbon once the run is ready',
      order: 'your details', back: '← back to cart',
      fName: 'your name', fTelegram: 'telegram',
      fPhone: 'phone, if convenient', fComment: 'anything important about the order',
      optional: 'optional',
      send: 'send pre-order', sending: 'sending…',
      req: 'please fill this in',
      cashFoot: 'you pay when we meet, nothing to pay now. i will write to you once the run is ready',
      pre: 'this is a pre-order: the piece is made for you and takes up to 4 weeks. '+
           'shipping is not included and is calculated separately: i will write to you, and we will agree on a delivery option that suits you',
      agree: 'by placing the order you agree to the processing of your personal data, ' +
             '<a href="politika-en" target="_blank" rel="noopener">privacy policy</a>',
      err: 'something went wrong. write to me on telegram and i will take the order by hand',
      demo: 'payments are not connected yet',
      demoText: 'the shop service is not running yet, so nothing was sent. this is exactly what will go to the server once it is on:',
      demoTg: 'write on telegram'
    }
  }[LANG];

  /* ── мелкие помощники ───────────────────────────────────────────────── */
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function money(n) { return n + ' €'; }
  function el(id) { return document.getElementById(id); }

  /* sku — то, чем товар опознаётся в корзине и на сервере.
     собирается из латинских id, поэтому одинаков в обеих языковых версиях */
  function skuOf(productId, chosen) {
    return [productId].concat(Object.keys(chosen).sort().map(function (k) {
      return k + ':' + chosen[k];
    })).join('|');
  }

  /* ── состояние ──────────────────────────────────────────────────────── */
  var cart = [];
  try { cart = JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { cart = []; }
  var method = 'card';      // 'card' | 'cash'
  var view = 'cart';        // 'cart' | 'form'
  var products = (typeof MERCH_CATALOG !== 'undefined' ? MERCH_CATALOG : [])
    .filter(function (p) { return !p.hidden; });
  var rendered = [];           // пары {товар, карточка} — чтобы обновлять их на месте
  var STOCK = null;            // остатки по sku с сервера; null — пока не знаем

  function save() { try { localStorage.setItem(KEY, JSON.stringify(cart)); } catch (e) {} }
  function count() { return cart.reduce(function (a, i) { return a + i.qty; }, 0); }
  function total() { return cart.reduce(function (a, i) { return a + i.price * i.qty; }, 0); }

  /* ═══ ВИТРИНА ═══════════════════════════════════════════════════════ */

  /* Кадры карточки: сначала выбранный цвет, потом всё, что лежит в gallery.
     Первый кадр носит класс pcard__img, потому что именно его подменяет
     выбор цвета и именно он уезжает миниатюрой в корзину. */
  function photoBlock(p, alt) {
    if (!p.photo) return '<div class="pcard__ph">' + T.photosoon + '</div>';

    var rest = p.gallery || [];
    var slides = '<img class="pcard__img" src="' + esc(p.photo) + '" alt="' + esc(alt) + '">' +
      rest.map(function (src) {
        return '<img src="' + esc(src) + '" alt="' + esc(alt) + '" loading="lazy">';
      }).join('');

    if (!rest.length) return '<div class="pgal"><div class="pgal__track">' + slides + '</div></div>';

    var dots = [];
    for (var i = 0; i <= rest.length; i++) {
      dots.push('<button class="pgal__dot' + (i ? '' : ' on') + '" type="button" data-i="' + i +
        '" aria-label="' + T.frame + ' ' + (i + 1) + '"></button>');
    }
    return '<div class="pgal">' +
      '<div class="pgal__track">' + slides + '</div>' +
      '<button class="pgal__nav pgal__nav--prev" type="button" aria-label="' + T.prev + '">‹</button>' +
      '<button class="pgal__nav pgal__nav--next" type="button" aria-label="' + T.next + '">›</button>' +
      '<div class="pgal__dots">' + dots.join('') + '</div>' +
    '</div>';
  }

  /* Листание: трек просто прокручивается, поэтому пальцем оно работает само,
     а стрелки и точки только двигают его на кадр. */
  function wireGallery(card) {
    var gal = card.querySelector('.pgal');
    if (!gal) return;
    var track = gal.querySelector('.pgal__track');
    var dots = [].slice.call(gal.querySelectorAll('.pgal__dot'));
    if (!dots.length) return;

    function go(i) {
      i = Math.max(0, Math.min(dots.length - 1, i));
      track.scrollTo({ left: track.clientWidth * i, behavior: 'smooth' });
    }
    function current() { return Math.round(track.scrollLeft / track.clientWidth); }

    gal.querySelector('.pgal__nav--prev').addEventListener('click', function () { go(current() - 1); });
    gal.querySelector('.pgal__nav--next').addEventListener('click', function () { go(current() + 1); });
    dots.forEach(function (dot) {
      dot.addEventListener('click', function () { go(+dot.getAttribute('data-i')); });
    });
    track.addEventListener('scroll', function () {
      var now = current();
      dots.forEach(function (dot, i) { dot.classList.toggle('on', i === now); });
    });
  }

  function renderShop() {
    var grid = el('shopGrid');
    if (!grid) return;

    /* одна-две позиции не должны болтаться в трёхколоночной сетке */
    grid.className = 'pgrid' + (products.length < 3 ? ' pgrid--' + products.length : '');
    grid.innerHTML = '';

    products.forEach(function (p) {
      var t = p[LANG] || p.ru;
      var card = document.createElement('article');
      card.className = 'pcard' + (p.sold_out ? ' pcard--out' : '');
      card.setAttribute('data-id', p.id);

      var opts = (p.options || []).map(function (o) {
        var chips = o.values.map(function (v, i) {
          return '<button class="chip' + (i === 0 ? ' on' : '') + '" type="button"' +
            ' data-val="' + esc(v.id) + '"' +
            (v.photo ? ' data-photo="' + esc(v.photo) + '"' : '') + '>' +
            esc(v[LANG] || v.ru) + '</button>';
        }).join('');
        return '<div class="opt" data-opt="' + esc(o.id) + '">' +
          '<span class="opt__label">' + esc(o[LANG] || o.ru) + '</span>' + chips + '</div>';
      }).join('');

      card.innerHTML =
        photoBlock(p, t.title) +
        '<div class="pcard__body">' +
          '<h3>' + esc(t.title) + '</h3>' +
          (t.desc ? '<p class="pcard__desc">' + esc(t.desc) + '</p>' : '') +
          opts +
          (t.note ? '<p class="pcard__meta">' + esc(t.note) + '</p>' : '') +
          '<div class="pcard__foot">' +
            '<span class="pcard__price">' + money(p.price) + '</span>' +
            '<span class="pcard__out" hidden>' + T.soldout + '</span>' +
            '<button class="btn btn-sm add" type="button" data-umami-event="preorder-add">' + T.add + '</button>' +
          '</div>' +
        '</div>';

      /* выбор варианта: подсветка и, если у варианта есть своё фото, подмена картинки */
      card.querySelectorAll('.opt').forEach(function (group) {
        group.addEventListener('click', function (e) {
          var chip = e.target.closest('.chip');
          if (!chip) return;
          group.querySelectorAll('.chip').forEach(function (c) { c.classList.remove('on'); });
          chip.classList.add('on');
          var photo = chip.getAttribute('data-photo');
          var img = card.querySelector('.pcard__img');
          if (photo && img) {
            img.src = photo;
            var track = card.querySelector('.pgal__track');
            if (track) track.scrollTo({ left: 0, behavior: 'smooth' });
          }
          syncCard(p, card);          /* у другого размера может не быть остатка */
        });
      });

      var addBtn = card.querySelector('.add');
      addBtn.addEventListener('click', function () { addToCart(p, card, addBtn); });

      wireGallery(card);
      grid.appendChild(card);
      rendered.push({ p: p, card: card });
      syncCard(p, card);
    });
  }

  /* что выбрано в карточке прямо сейчас: {size:'lxl', color:'graphite'} */
  function chosenOf(card) {
    var chosen = {};
    card.querySelectorAll('.opt').forEach(function (g) {
      chosen[g.getAttribute('data-opt')] = g.querySelector('.chip.on').getAttribute('data-val');
    });
    return chosen;
  }

  /* закончился ли именно выбранный вариант.
     STOCK приходит с сервера по sku, поэтому «худи l/xl закончилось»
     гасит кнопку, а s/m рядом остаётся доступным */
  function isOut(p, card) {
    if (p.sold_out) return true;
    if (!STOCK) return false;                       // остатки неизвестны — не мешаем
    var sku = skuOf(p.id, chosenOf(card));
    return STOCK[sku] === 0;
  }

  function syncCard(p, card) {
    var out = isOut(p, card);
    card.classList.toggle('pcard--out', out);
    card.querySelector('.pcard__out').hidden = !out;
    card.querySelector('.add').hidden = out;
  }

  function addToCart(p, card, btn) {
    var chosen = {}, labels = [];
    card.querySelectorAll('.opt').forEach(function (g) {
      var on = g.querySelector('.chip.on');
      chosen[g.getAttribute('data-opt')] = on.getAttribute('data-val');
      labels.push(on.textContent);
    });

    var sku = skuOf(p.id, chosen);
    var found = cart.filter(function (x) { return x.sku === sku; })[0];
    if (found) {
      found.qty++;
    } else {
      var img = card.querySelector('.pcard__img');
      cart.push({
        sku: sku, qty: 1,
        title: (p[LANG] || p.ru).title,
        opts: labels.join(' · '),
        price: p.price,
        img: img ? img.getAttribute('src') : null
      });
    }
    save(); renderCart();
    openDrawer();               /* положили вещь — сразу показываем корзину */

    var was = btn.textContent;
    btn.textContent = T.added;
    setTimeout(function () { btn.textContent = was; }, 1200);
  }

  /* ═══ КОРЗИНА ═══════════════════════════════════════════════════════ */

  function renderCart() {
    var n = count();
    ['cartN', 'cartNM'].forEach(function (id) { var e = el(id); if (e) e.textContent = n; });
    ['cartBtn', 'cartBtnM'].forEach(function (id) {
      var e = el(id); if (e) e.classList.toggle('has', n > 0);
    });
    if (view === 'form') { renderForm(); return; }

    el('drawerTitle').textContent = T.cart;
    var body = el('drawerBody'), foot = el('drawerFoot');
    body.innerHTML = '';

    if (!cart.length) {
      body.innerHTML = '<p class="empty">' + T.empty + '</p>';
      foot.innerHTML = '';
      return;
    }

    cart.forEach(function (it, i) {
      var row = document.createElement('div');
      row.className = 'citem';
      row.innerHTML =
        (it.img ? '<img src="' + esc(it.img) + '" alt="">' : '<div class="citem__ph"></div>') +
        '<div><div class="citem__t">' + esc(it.title) + '</div>' +
        (it.opts ? '<div class="citem__o">' + esc(it.opts) + '</div>' : '') +
        '<div class="qty"><button type="button" data-a="-">−</button><span>' + it.qty +
        '</span><button type="button" data-a="+">+</button></div></div>' +
        '<div class="citem__right"><div class="citem__p">' + money(it.price * it.qty) + '</div>' +
        '<button class="citem__x" type="button" data-a="x">' + T.remove + '</button></div>';
      row.addEventListener('click', function (e) {
        var a = e.target.getAttribute('data-a');
        if (!a) return;
        if (a === '+') cart[i].qty++;
        else if (a === '-') cart[i].qty > 1 ? cart[i].qty-- : cart.splice(i, 1);
        else if (a === 'x') cart.splice(i, 1);
        save(); renderCart();
      });
      body.appendChild(row);
    });

    foot.innerHTML =
      '<div class="sum"><span>' + T.total + '</span><b>' + money(total()) + '</b></div>' +
      '<p class="drawer__pre">' + T.pre + '</p>' +
      '<div class="pay"><span class="pay__label">' + T.how + '</span>' +
        payRow('card', T.card, T.cardNote) +
        payRow('cash', T.cash, T.cashNote) +
      '</div>' +
      '<button class="btn" id="goCheckout" type="button" data-umami-event="preorder-checkout">' + T.checkout + '</button>' +
      '<p class="drawer__agree">' + T.agree + '</p>';

    foot.querySelectorAll('.pay__row').forEach(function (row) {
      row.addEventListener('click', function () {
        method = row.getAttribute('data-m');
        renderCart();
      });
    });
    el('goCheckout').addEventListener('click', goCheckout);
  }

  function payRow(id, title, note) {
    return '<button class="pay__row' + (method === id ? ' on' : '') + '" type="button"' +
      ' data-m="' + id + '" aria-pressed="' + (method === id) + '">' +
      '<span class="pay__dot"></span>' +
      '<span><span class="pay__t">' + title + '</span>' +
      '<span class="pay__n">' + note + '</span></span></button>';
  }

  /* ═══ ОФОРМЛЕНИЕ ════════════════════════════════════════════════════ */

  function goCheckout() {
    if (!cart.length) return;
    if (method === 'cash') { view = 'form'; renderCart(); return; }

    var payload = { items: lines(), locale: LANG, method: 'card' };
    if (!SHOP.live) return demo('POST ' + SHOP.api + '/checkout', payload);

    var btn = el('goCheckout');
    btn.disabled = true; btn.textContent = T.sending;
    post('/checkout', payload).then(function (r) {
      window.location.href = r.url;              // страница оплаты stripe
    }).catch(function () {
      btn.disabled = false; btn.textContent = T.checkout;
      fail();
    });
  }

  function lines() {
    return cart.map(function (i) { return { sku: i.sku, qty: i.qty }; });
  }

  function renderForm() {
    el('drawerTitle').textContent = T.order;
    el('drawerBody').innerHTML =
      '<button class="backlink" id="backToCart" type="button">' + T.back + '</button>' +
      '<div class="form">' +
        field('fName', T.fName, 'text', true) +
        field('fTelegram', T.fTelegram, 'text', true) +
        field('fPhone', T.fPhone, 'tel', false) +
        field('fComment', T.fComment, 'textarea', false) +
      '</div>';
    el('drawerFoot').innerHTML =
      '<div class="sum"><span>' + T.total + '</span><b>' + money(total()) + '</b></div>' +
      '<p class="drawer__pre">' + T.pre + '</p>' +
      '<p class="drawer__note">' + T.cashFoot + '</p>' +
      '<button class="btn" id="sendOrder" type="button" data-umami-event="preorder-cash-send">' + T.send + '</button>' +
      '<p class="drawer__agree">' + T.agree + '</p>';

    el('backToCart').addEventListener('click', function () { view = 'cart'; renderCart(); });
    el('sendOrder').addEventListener('click', sendOrder);
  }

  function field(id, label, type, required) {
    var input = type === 'textarea'
      ? '<textarea id="' + id + '" rows="2"></textarea>'
      : '<input id="' + id + '" type="' + type + '">';
    return '<label class="fld"><span class="fld__l">' + label +
      (required ? '' : ' <i>' + T.optional + '</i>') + '</span>' + input +
      '<span class="fld__e"></span></label>';
  }

  function sendOrder() {
    var vals = {}, ok = true;
    [['fName', true], ['fTelegram', true], ['fPhone', false], ['fComment', false]]
      .forEach(function (f) {
        var input = el(f[0]);
        var v = input.value.trim();
        var wrap = input.closest('.fld');
        if (f[1] && !v) {
          wrap.classList.add('bad');
          wrap.querySelector('.fld__e').textContent = T.req;
          ok = false;
        } else {
          wrap.classList.remove('bad');
          wrap.querySelector('.fld__e').textContent = '';
        }
        vals[f[0]] = v;
      });
    if (!ok) return;

    var payload = {
      items: lines(), locale: LANG, method: 'cash_pickup',
      customer: {
        name: vals.fName, telegram: vals.fTelegram,
        phone: vals.fPhone, comment: vals.fComment
      }
    };
    if (!SHOP.live) return demo('POST ' + SHOP.api + '/order', payload);

    var btn = el('sendOrder');
    btn.disabled = true; btn.textContent = T.sending;
    post('/order', payload).then(function (r) {
      cart = []; save();
      window.location.href = SHOP.thanks[LANG] + '?order=' + encodeURIComponent(r.order);
    }).catch(function () {
      btn.disabled = false; btn.textContent = T.send;
      fail();
    });
  }

  function post(path, payload) {
    return fetch(SHOP.api + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }

  /* ═══ ОКНА ══════════════════════════════════════════════════════════ */

  function modal(title, html) {
    var box = el('modal');
    box.innerHTML = '<div class="modal__box"><h3>' + title + '</h3>' + html +
      '<button class="btn btn-outline" id="modalClose" type="button">' + T.close + '</button></div>';
    box.classList.add('on');
    document.body.classList.add('no-scroll');
    el('modalClose').addEventListener('click', closeModal);
    box.addEventListener('click', function (e) { if (e.target === box) closeModal(); });
  }
  function closeModal() {
    el('modal').classList.remove('on');
    if (!el('drawer').classList.contains('on')) document.body.classList.remove('no-scroll');
  }
  function demo(line, payload) {
    modal(T.demo,
      '<p>' + T.demoText + '</p><pre>' + esc(line + '\n\n' + JSON.stringify(payload, null, 2)) + '</pre>' +
      '<p><a href="' + SHOP.telegram + '" target="_blank" rel="noopener">' + T.demoTg + ' →</a></p>');
  }
  function fail() {
    modal(T.demo, '<p>' + T.err + '</p>' +
      '<p><a href="' + SHOP.telegram + '" target="_blank" rel="noopener">' + T.demoTg + ' →</a></p>');
  }

  /* ═══ ЯЩИК КОРЗИНЫ ══════════════════════════════════════════════════ */

  function openDrawer() {
    el('drawer').classList.add('on');
    el('scrim').classList.add('on');
    document.body.classList.add('no-scroll');
  }
  function closeDrawer() {
    el('drawer').classList.remove('on');
    el('scrim').classList.remove('on');
    document.body.classList.remove('no-scroll');
    view = 'cart';
  }

  /* ═══ ЕСТЬ ЛИ СЕРВИС ════════════════════════════════════════════════ */
  /* страница остаётся обычной статикой: она просто спрашивает сервис,
     работает ли магазин, и только после его ответа начинает принимать
     заказы по-настоящему. нет ответа — остаётся витриной без оплаты */
  function askService() {
    fetch(SHOP.api + '/health').then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }).then(function (info) {
      SHOP.live = !!info.selling;
      if (SHOP.live) refreshStock();
    }).catch(function () { /* сервиса нет — витрина работает как раньше */ });
  }

  function refreshStock() {
    if (!SHOP.live) return;
    fetch(SHOP.api + '/stock').then(function (r) { return r.json(); }).then(function (stock) {
      STOCK = stock;
      rendered.forEach(function (r) { syncCard(r.p, r.card); });
    }).catch(function () { /* сервис молчит — витрина остаётся как есть */ });
  }

  /* ═══ СТАРТ ═════════════════════════════════════════════════════════ */

  renderShop();
  renderCart();
  askService();

  ['cartBtn', 'cartBtnM'].forEach(function (id) {
    var b = el(id); if (b) b.addEventListener('click', openDrawer);
  });
  el('scrim').addEventListener('click', closeDrawer);
  el('drawerClose').addEventListener('click', closeDrawer);
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (el('modal').classList.contains('on')) closeModal();
    else closeDrawer();
  });
})();
