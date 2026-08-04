# design.md — дизайн-система текущего сайта

Извлечено из живых страниц репозитория (`index.html`, `praktika.html`, `rabotat-so-mnoy.html`,
`retreat.html`, `pass.html`, `connection.html`, `faq.html` + их `-en` версии).
Это описание **того, что реально есть в коде**, а не пожелание на будущее.

> Не путать с `design/DESIGN.md` — там лежит внешний стилевой референс «New Genre»
> (тёмные градиенты, IBM Plex/Inter). На сайте он **не используется**.

---

## 1. Характер

Тихий редакторский минимализм: тёплый почти-белый фон, чёрно-серая типографика,
никаких скруглений, теней и акцентных цветов. Всё держится на трёх вещах:

- **тёплая бумага** вместо белого (`#fbfaf8`);
- **волосяные линии** (1px `#e7e5e0`) вместо карточек с тенью;
- **контраст двух гарнитур** — Georgia для заголовков и «голосовых» фраз,
  системный sans для всего остального.

Единственное цветовое событие на странице — чёрные секции (`.dark`, `.cta`) и фото.
Тексты набраны строчными буквами (капслок только в микро-лейблах).

---

## 2. Токены

### 2.1 Цвет

```css
:root{
  --ink:#141414;    /* основной текст, кнопки, чёрные секции */
  --soft:#6f6f6f;   /* вторичный текст, ссылки в навигации и футере */
  --faint:#a8a8a8;  /* микро-лейблы, подписи, футер */
  --line:#e7e5e0;   /* все разделители и рамки */
  --bg:#fbfaf8;     /* фон страницы */
  --card:#ffffff;   /* фон карточек */
  --warm:#f3ece4;   /* тёплая заливка выделенной карточки */
}
```

`--card` объявлен везде кроме `faq.html`; `--warm` — только в `rabotat-so-mnoy.html`
и `pass.html` (там же `card--soft` с рамкой `#e6ddd2`).

Литералы вне переменных (используются как есть, стоит держать в голове):

| Значение | Где |
|---|---|
| `#fff` | текст на `.btn`, кружок play, `.card__count` |
| `#333` | ховер основной кнопки |
| `#f4f2ee` | текст на чёрных секциях, заголовки/крестики модалок |
| `#b9b6b0` | вторичный текст на чёрном (`.cta p`, `.dark .dtext`) |
| `#8b8680` | `sec-label` внутри `.dark` |
| `#ece8e2` | плейсхолдер медиа в карточке |
| `rgba(20,20,20,.55)` / `.72` | оверлей видео-карточки / бейдж счётчика |
| `rgba(18,18,18,.94)` | подложка лайтбокса и модалки отзывов |
| `rgba(251,250,248,.95)` + `blur(8px)` | «стеклянная» навигация — **только `faq.html`** |

### 2.2 Типографика

```css
body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
       font-size:16px; line-height:1.7; -webkit-font-smoothing:antialiased; }
h1,h2,h3 { font-family:Georgia,"Times New Roman",serif; font-weight:400; }
```

Веб-шрифты не подключаются вообще — только системные стеки. Georgia отвечает за
«голос»: заголовки, `.mission`, `.statement p`, `.dark .lead`, цены, имя в навигации.

| Роль | Размер | Прочее |
|---|---|---|
| H1 | 33–38px (моб. 27–29px) | `line-height:1.28–1.3`, `letter-spacing:-.01em` |
| H2 | 26px | `margin-bottom:22px` |
| H3 (карточки) | 20–23px | |
| Statement / лид | 24–27px Georgia (моб. 20–22px) | `line-height:1.5`, по центру, `max-width:720–780px` |
| Body | 16px / 1.7 | |
| Текст в карточках | 14.5–15.5px | `color:var(--soft)` |
| `.kicker` | 11px | `letter-spacing:.24em`, uppercase, `--faint` |
| `.sec-label` | 11px | `letter-spacing:.22em`, uppercase, `--faint` |
| `.card__label` | 10.5px | `letter-spacing:.2em`, uppercase |
| Навигация | 14px | `--soft`, имя — 17px Georgia |
| Мобильное меню | 27px Georgia | |
| Футер | 13px / 1.9 | `--faint`, ссылки `--soft` |
| Кнопка | 14px | `letter-spacing:.04em` (мелкая `.btn-sm` — 13px) |

Разброс H1 по страницам (осознанная, но невыровненная деталь):
`rabotat` 33 · `praktika` 34 · `index`/`pass` 36 · `retreat`/`connection`/`faq` 38.

### 2.3 Сетка и ритм

```css
.wrap      { max-width:960px;  margin:0 auto; padding:0 24px; }
.wrap-wide { max-width:1080px; margin:0 auto; padding:0 24px; }  /* только praktika.html */
section    { padding:56px 0; }
.prose     { max-width:680px; }
```

- Ширины контента: **960** (основная), 1080 (широкая), 860/820/760/720/680 — для
  узких блоков (`.paths`, `.rlist`, `.trust`, `.faq`, `.context`, `.statement`).
- Вертикальный ритм: секция 56px, hero 64–72px сверху (`index` 72, остальные 64),
  чёрная секция 84–88px, футер 44px.
- Гэпы: 56px (hero-колонки), 48px (двухколонники), 18–20px (сетки карточек), 14px (галерея).
- Отступы внутри: карточка 26–34px по вертикали / 26–40px по горизонтали.
- **Радиусов нет** (единственный `border-radius:50%` — кружок play и аватар в отзыве).
  **Теней нет.** Глубина создаётся только линиями и фоном `--card`.
- Переходы: `.2s` (кнопки, ховеры), `.25s` (бургер), `.3s ease` (выезд меню).

---

## 3. Компоненты

### Навигация (на всех страницах одинаковая)

```html
<nav><div class="wrap">
  <a class="name" href="/">даша простова</a>
  <span class="links">
    <a href="rabotat-so-mnoy" class="active">работать со мной</a>
    <a href="praktika">практиковать со мной</a>
    <a href="faq">FAQ</a>
    <a href="https://t.me/beloved_dasha" target="_blank" rel="noopener">написать мне</a>
    <a class="lang" href="rabotat-so-mnoy-en">en</a>
  </span>
  <span class="mtools"><a class="lang-m" href="…-en">en</a>
    <button class="burger" id="burger" aria-label="меню" aria-expanded="false">
      <span></span><span></span><span></span></button></span>
</div></nav>
```

- `position:sticky; top:0; z-index:50`, фон `--bg`, снизу линия `--line`.
- Вместо логотипа — **имя** «даша простова» (17px Georgia). Логотипы `logo-*.svg`
  остались только на легаси-странице.
- Переключатель языка `en` отделён вертикальной линией слева (`padding-left:26px`).
- На мобильном: `.links` скрывается, показываются `.mtools` (текстовый `en` + бургер).
  Языковой переключатель **вне** бургер-меню, рядом с иконкой.
- Активный пункт — `.active` (цвет `--ink`).

### Мобильное меню `.mnav`

Полноэкранная панель `position:fixed; inset:0; z-index:60`, выезжает справа
(`translateX(100%) → 0`), пункты 27px Georgia, выключка влево, крестик `✕` справа сверху.
На открытии: `body.mnav-open{overflow:hidden}` и `nav{display:none}`.

### Кнопки

```css
.btn        { padding:15px 28px; font-size:14px; letter-spacing:.04em;
              background:var(--ink); color:#fff; border:1px solid var(--ink); }
.btn:hover  { background:#333; border-color:#333; }
.btn-outline{ background:transparent; color:var(--ink); border-color:var(--line); }
.btn-outline:hover { border-color:var(--ink); }
.btn-white  { background:#fff; color:var(--ink); border-color:#fff; }   /* retreat */
.btn-sm     { padding:12px 22px; font-size:13px; }
```

Прямоугольные, без радиуса. **Все основные кнопки одного цвета — чёрные**
(в `index.html` в комментарии зафиксирована альтернатива `#e9cfc9`;
`.btn-dark` / `.btn-light` остались как пустые классы для совместимости).
На чёрном фоне кнопка инвертируется: прозрачная с рамкой `#f4f2ee`, на ховер — заливка.

### Секция

```html
<section><div class="wrap">
  <div class="sec-label">обо мне</div>
  <h2>…</h2>
  <div class="prose"><p>…</p></div>
</div></section>
```

`.sec-label` — микро-лейбл капслоком над заголовком, основной приём навигации по странице.
Разделитель между блоками — `<div class="wrap"><hr class="hr"></div>` (линия внутри контейнера).

### Hero

Две вариации:

- **Сетка текст+фото** — `.hero` / `.phero`: `grid-template-columns` от `1.05fr .95fr`
  до `1.2fr .8fr`, gap 56px, `align-items:center`. Фото `aspect-ratio:3/4` (портрет)
  или `4/5`, `object-fit:cover`. Порядок: kicker → H1 → лид (Georgia 18–19px) → кнопки.
- **Центрированный** — `connection.html`, `faq.html`: без фото, текст по центру,
  подзаголовок `max-width:640px`.

На ≤760px hero схлопывается в одну колонку (gap 32–36px).

### Statement

Полноширинная цитата-утверждение по центру: Georgia 24–27px, `max-width:720–780px`.
Ритмическая пауза между смысловыми блоками. Опции: `strong` с подчёркиванием
`border-bottom:1px solid var(--faint)`, приписка `.note` мелким sans.

### Карточки

| Класс | Страница | Устройство |
|---|---|---|
| `.path` | index | Две «дорожки», `1fr 1fr`, gap 18px, кнопка внизу |
| `.card` (сетка `.grid`) | rabotat, pass | Рамка + `--card`; в rabotat с `.card__media` (16/10), `.card__body`, `.card__head`, `.card__price` Georgia 21px, `.card__link` подчёркнутая |
| `.card--soft` / `.card--wide` | pass | Тёплая заливка `--warm` / карточка на всю ширину сетки |
| `.fcard` | praktika | Крупный формат `340px + 1fr` (`.fcard--rev` зеркалит), внутри `.fcard__groups` — 3 колонки расписания |
| `.plan` | connection | Фото 3/4 сверху, тело по центру, кнопка прижата вниз (`margin-top:auto`) |
| `.review` | rabotat, retreat, connection | Отзыв: рамка, 28–32px паддинг, автор снизу (`.review__name` 600, `.review__role` `--faint`), в retreat — круглый аватар 52px |

Общее правило карточки: `border:1px solid var(--line)`, фон `--card`,
`display:flex; flex-direction:column`, кнопка `align-self:flex-start`.

### Списки

- `.rlist` (rabotat) — таймлайн: линия сверху у каждого пункта, псевдо-элемент-тире
  8×1px слева, дата капслоком 10px.
- `.gift-list`, `.inside-list` — линия сверху + символ `—` в `:before`.
- `.fcard__groups` — три колонки с линией сверху.

### Горизонтальные карусели

`.hscroll` / `.reviews-row`: флекс с `overflow-x:auto`, `scroll-snap-type:x mandatory`,
скроллбар скрыт. Ширина элемента фиксирована (`flex:0 0 420px` отзывы / `330px`
в connection; на мобильном 280–300px). Управление — квадратные стрелки
`.rarrow` 44×44 с рамкой `--line`, шаг = ширина элемента + 20px, `behavior:'smooth'`.
Галерея на retreat — тот же паттерн, но картинки фиксированной высоты 420px (моб. 320px).

### Тёмные блоки

- `.cta` (index, retreat) — чёрный фон, текст `#f4f2ee`, заголовок 30px, кнопка-контур.
- `.dark` (rabotat) — то же плюс `.lead` Georgia 23px и `.dtext` `#b9b6b0`,
  паддинг 84px, `sec-label` перекрашен в `#8b8680`.
- `.vcard` (retreat) — фото 420px с оверлеем `rgba(20,20,20,.55)`, заголовок белым по центру.

### Оверлеи

- **Лайтбокс** `.lb` (rabotat) — подложка `rgba(18,18,18,.94)`, колонка картинок
  `max-width:820px`, заголовок Georgia 22px, `✕` 30px зафиксирован в углу.
- **Модалка отзывов** `.reviews-modal` (rabotat) — `max-width:1040px`, заголовок 30px,
  внутри та же сетка `.reviews` с уплотнёнными карточками.

Оба закрываются кликом по подложке и `Escape`, блокируют скролл (`body.lb-open` /
`body.reviews-open`) и прячут `nav`.

### Футер

Одинаков на всех страницах: по центру, 13px/1.9, `--faint`, линия сверху
(на главной без неё), три строки — имя и география, строчка про soft power,
ряд ссылок telegram · instagram · linkedin · почта · © 2026.

---

## 4. Адаптив

Единственный брейкпоинт — **760px**. Что происходит:

```css
@media(max-width:760px){
  nav .links{display:none;} .mtools{display:flex;} .burger{display:block;}
  .hero .wrap,.phero .wrap{grid-template-columns:1fr; gap:32–36px;}
  .grid,.paths,.plans,.trust,.reviews{grid-template-columns:1fr;}
  .fcard,.fcard--rev{grid-template-columns:1fr; min-height:0;}
  .gallery{grid-template-columns:1fr 1fr;}     /* pass */
  h1{font-size:27–29px;} .statement p{font-size:20–22px;}
}
```

Всё остальное (шрифты, отступы секций, карточки) не меняется — макет однопоточный
и переживает сужение сам.

---

## 5. Композиция страниц

| Страница | Скелет |
|---|---|
| `index` | hero (портрет + 2 кнопки) → `hr` → обо мне (`.prose` + соцсети) → две дорожки `.paths` → FAQ-выжимка → личный контекст `.context` → чёрный CTA → футер |
| `praktika` | hero → statement → медиа-блок с видео → форматы `.fcard` ×3 → ретрит `.fcard` → soft power pass → футер |
| `rabotat-so-mnoy` | hero → statement → кейсы `.card` с медиа → карьера `.rlist` → форматы работы `.card` ×6 → отзывы (+ модалка «все отзывы») → чёрная секция → футер |
| `retreat` | hero → statement → `.vcard` с видео → отзывы-карусель → галерея-карусель → CTA → футер |
| `pass` | hero → варианты `.card` (3 + широкая) → statement → закрывающая галерея 3/4 → футер |
| `connection` | центрированный hero → «что внутри» (2 колонки: список + фото) → тарифы `.plan` ×3 → отзывы-карусель → футер |
| `faq` | hero → длинный список `.faq-item` → `.context` → футер |

Повторяющийся ритм страницы: **hero → утверждение → доказательство (карточки/списки) →
отзывы → CTA → футер**.

---

## 6. Архитектура кода

- Каждая страница — **самостоятельный HTML со своим `<style>` в `<head>`**.
  Общего CSS-файла нет, база (`:root`, reset, nav, `.btn`, `.wrap`, секции, футер)
  скопирована в каждый файл. При правке базового компонента менять надо во всех файлах.
- JS — маленькие IIFE в конце `<body>`: бургер-меню (везде), стрелки каруселей
  (retreat, connection), лайтбокс и модалка отзывов (rabotat). Без библиотек и сборки.
- RU и EN версии страницы имеют **побайтово одинаковый CSS** (различие в `index` —
  только комментарии). Любое изменение стиля применяется к обеим версиям в одном коммите.
- Ссылки без расширения `.html` (`href="praktika"`), внешние — с `target="_blank" rel="noopener"`.
- Картинки — `/images/*.jpg`, всегда `object-fit:cover` с заданным `aspect-ratio`.
- **Исключение:** `politika.html` живёт на старой системе (`css/style.css` + `css/page.css`,
  Google Fonts IBM Plex Serif + Inter, логотип-SVG в навигации). Под новый стиль не переведена.
  `dlya-uchiteley-i-komand.html` — редирект-заглушка.

---

## 7. Правила

**Делать**

- Новые страницы начинать с копии `<style>` любой соседней страницы — база идентична.
- Держать текст строчными; капслок — только `.kicker`, `.sec-label`, `.card__label`, бейджи.
- Georgia — заголовкам, цитатам, цене и лиду. Всё остальное — системный sans.
- Разделять блоки линией `--line` или сменой фона (`--card`, `--ink`), не тенью.
- Вторичный текст — `--soft`, подписи и мета — `--faint`; чёрный `--ink` беречь для главного.
- Кнопку в карточке прижимать `margin-top:auto`, чтобы низ карточек сетки выравнивался.
- Любое изменение — синхронно в RU и EN файле.

**Не делать**

- Не добавлять акцентные цвета, градиенты, тени и скругления.
- Не подключать веб-шрифты и внешние библиотеки.
- Не вводить второй брейкпоинт без необходимости — макет рассчитан на один (760px).
- Не использовать `.btn-dark` / `.btn-light` как реальные модификаторы — они пустые.
- Не тащить в новые страницы `css/style.css` и `css/page.css` — это легаси.
