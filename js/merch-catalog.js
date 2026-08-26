/* ═══════════════════════════════════════════════════════════════════════════
   КАТАЛОГ МЕРЧА

   Это единственный файл, который нужно править, чтобы поменять товары,
   цены или фотографии. Его читают обе страницы сразу — и русская
   (merch.html), и английская (merch-en.html), так что ничего не разъедется.

   ── ЧТО ЗДЕСЬ СЕЙЧАС ──────────────────────────────────────────────────────
   Один лонгслив в трёх цветах печати стоит тремя отдельными карточками, а не
   одной с выбором цвета: так с первого взгляда видно, чем они отличаются.
   Тексты и цена у них одинаковые, разное только имя, id и фотографии.

   ── ДОБАВИТЬ ФОТО ─────────────────────────────────────────────────────────
   photo   — главный кадр карточки, он же уезжает миниатюрой в корзину.
   gallery — остальные кадры, их листают стрелками или пальцем.
   Файлы кладутся в папку images/, сюда вписывается имя файла.
   Пока в photo стоит null, на карточке аккуратная заглушка «фото скоро».

   ── ДОБАВИТЬ ТОВАР ────────────────────────────────────────────────────────
   Скопируй блок { … } целиком, вставь рядом через запятую и поменяй id,
   price, photo и тексты. id пиши латиницей и не повторяй: по нему заказ
   опознаётся на сервере, и такой же id должен появиться в shop/catalog.json.

   ── УБРАТЬ ТОВАР С ВИТРИНЫ ────────────────────────────────────────────────
   hidden: true    — карточка исчезает со страницы.
   sold_out: true  — карточка остаётся, но с пометкой «закончилось»
                     и без кнопки заказа.

   ── ЦЕНЫ ──────────────────────────────────────────────────────────────────
   price — в евро, числом. На сайте цена только показывается: при оплате
   картой сумму считает сервер по своему shop/catalog.json, поэтому
   подменить её из браузера нельзя.
   ═══════════════════════════════════════════════════════════════════════ */

/* Тексты у всех трёх лонгсливов одни и те же, поэтому лежат отдельно:
   поправишь здесь — поменяется сразу во всех карточках. */
var LONGSLEEVE = {
  ru: {
    desc: 'оверсайз из плотного премиального хлопка 230–250 г/м². на спине печать по кругу, ø 22 см. на манжете левого рукава вышивка soft power.',
    note: 'ограниченный тираж · предзаказ до 5 сентября'
  },
  en: {
    desc: 'oversized, heavyweight premium cotton 230–250 gsm. circular screen print on the back, ø 22 cm. soft power embroidery on the left cuff.',
    note: 'limited edition · pre-order till 5 september'
  },
  /* размеры одинаковые у всех цветов */
  sizes: {
    id: 'size',
    ru: 'размер', en: 'size',
    values: [
      { id: 'm',  ru: 'm',  en: 'm'  },
      { id: 'l',  ru: 'l',  en: 'l'  },
      { id: 'xl', ru: 'xl', en: 'xl' }
    ]
  }
};

var MERCH_CATALOG = [

  {
    id: 'longsleeve-pink',
    price: 108,
    photo: 'images/merch-longsleeve-pink.jpg',
    /* спереди вещь у всех цветов одна и та же, манжет розовый только здесь */
    gallery: ['images/merch-longsleeve-front.jpg', 'images/merch-longsleeve-cuff.jpg'],
    hidden: false,
    sold_out: false,
    ru: { title: 'лонгслив dusty pink', desc: LONGSLEEVE.ru.desc, note: LONGSLEEVE.ru.note },
    en: { title: 'dusty pink long sleeve', desc: LONGSLEEVE.en.desc, note: LONGSLEEVE.en.note },
    options: [LONGSLEEVE.sizes]
  },

  {
    id: 'longsleeve-sage',
    price: 108,
    photo: 'images/merch-longsleeve-sage.jpg',
    gallery: ['images/merch-longsleeve-front.jpg'],
    hidden: false,
    sold_out: false,
    ru: { title: 'лонгслив sage', desc: LONGSLEEVE.ru.desc, note: LONGSLEEVE.ru.note },
    en: { title: 'sage long sleeve', desc: LONGSLEEVE.en.desc, note: LONGSLEEVE.en.note },
    options: [LONGSLEEVE.sizes]
  },

  {
    id: 'longsleeve-navy',
    price: 108,
    photo: 'images/merch-longsleeve-navy.jpg',
    gallery: ['images/merch-longsleeve-front.jpg'],
    hidden: false,
    sold_out: false,
    ru: { title: 'лонгслив ink navy', desc: LONGSLEEVE.ru.desc, note: LONGSLEEVE.ru.note },
    en: { title: 'ink navy long sleeve', desc: LONGSLEEVE.en.desc, note: LONGSLEEVE.en.note },
    options: [LONGSLEEVE.sizes]
  }

];
