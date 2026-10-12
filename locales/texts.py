"""Mijoz, to'lov va bildirishnoma matnlari: uz / ru / en."""

TEXTS: dict[str, dict[str, str]] = {
  "uz": {
    "btn_catalog": "🛍 Katalog",
    "btn_cart": "🛒 Savat",
    "btn_orders": "📦 Buyurtmalarim",
    "btn_language": "🌐 Tilni o'zgartirish",
    "btn_pickup": "📍 Qayerdan olib ketaman?",
    "btn_cancel": "❌ Bekor qilish",
    "btn_share_phone": "📱 Raqamni ulashish",
    "btn_open_shop": "🛍 Do'konni ochish",
    "btn_admin_menu": "⚙️ Admin menyu",
    "btn_add_one": "🛒 Savatga +1",
    "btn_buy_one": "⚡️ 1 dona buyurtma",
    "btn_add_qty": "🛒 Boshqa miqdor",
    "btn_buy_qty": "⚡️ Boshqa miqdor",
    "btn_back_catalog": "◀️ Katalog",
    "btn_checkout": "✅ Buyurtma berish",
    "btn_clear_cart": "🗑 Savatni tozalash",
    "btn_to_catalog": "🛍 Katalogga",
    "btn_pay_click": "💳 Click orqali to'lash",
    "btn_pay_payme": "🟢 Payme orqali to'lash",
    "btn_qr": "🏷 Olib ketish kodi (QR)",
    "btn_no_products": "Mahsulotlar yo'q",
    "choose_language": (
      "🌐 <b>Tilni tanlang</b>\n"
      "Выберите язык\n"
      "Choose a language"
    ),
    "language_saved": "✅ Til saqlandi: O'zbekcha",
    "language_save_failed": (
      "❌ Til saqlanmadi. Supabase'da users jadvali yo'q. "
      "SQL yangilanishini ishga tushiring va qayta tanlang."
    ),
    "welcome": (
      "🏛 <b>{shop}</b>\n\n"
      "Xush kelibsiz! Sizning rolingiz: <b>{role}</b>\n"
      "Pastdagi menyudan foydalaning."
    ),
    "role_admin": "Admin",
    "role_client": "Mijoz",
    "help_admin": (
      "⚙️ <b>Admin yordam</b>\n\n"
      "• Mahsulot qo'shish / kirim / boshqarish\n"
      "• Yangi buyurtmalarni tasdiqlash yoki rad etish\n"
      "• 480-xonada kod (#TATU-42 yoki 42) yoki mijoz QR ini tekshirish\n"
      "• Statistika va tarix\n"
      "• «Mijoz menyusi» orqali katalogni ko'rish"
    ),
    "help_client": (
      "ℹ️ <b>Yordam</b>\n\n"
      "• Katalogdan mahsulot tanlang\n"
      "• Savatga qo'shing yoki tezkor buyurtma bering\n"
      "• «Buyurtmalarim»da olib ketish kartasi va QR\n"
      "• «Qayerdan olib ketaman?» — C-bino, 480-xona\n"
      "• «Tilni o'zgartirish» — o'zbek / rus / ingliz"
    ),
    "client_menu_opened": (
      "🛍 Mijoz menyusi ochildi.\n"
      "Admin panelga qaytish: «⚙️ Admin menyu»."
    ),
    "admin_menu_opened": "⚙️ Admin menyusi ochildi.",
    "no_permission": "⛔ Ruxsat yo'q.",
    "use_menu": "ℹ️ Menyudagi tugmalardan foydalaning.",
    "cancelled": "❌ Bekor qilindi.",
    "order_cancelled": "❌ Buyurtma bekor qilindi.",
    "ordering_busy": (
      "⏳ Buyurtma jarayoni davom etmoqda.\n"
      "Telefon yoki miqdorni yuboring, yoki «{cancel}» ni bosing."
    ),
    "catalog_title": "🛍 <b>Katalog</b>",
    "catalog_empty": "Hozircha sotuvda mahsulot yo'q.",
    "catalog_pick": "Mavjud mahsulotni tanlang:",
    "catalog_body": "🛍 <b>Katalog</b>\n\nMavjud mahsulotni tanlang:",
    "product_unavailable": "Mahsulot mavjud emas.",
    "product_missing": "Mahsulot topilmadi.",
    "product_link_missing": (
      "❌ Bu mahsulot topilmadi yoki hozircha sotuvda emas.\n"
      "Katalogdan boshqa mahsulotni tanlang."
    ),
    "product_link_opened": "🛍 QR / deep link orqali mahsulot ochildi:",
    "added_toast": "Savatga qo'shildi ✅",
    "added_hint": (
      "✅ Savatga qo'shildi: <b>{name}</b> × 1\n"
      "Yana mahsulot qo'shing yoki «{cart}» orqali bitta buyurtma qiling."
    ),
    "added_named": "✅ Savatga qo'shildi: <b>{name}</b> × {qty}",
    "order_line": (
      "⚡️ <b>Buyurtma:</b> {name} × {qty}\n"
      "💰 {price}\n\n"
      "📞 Telefon raqamingizni yuboring yoki tugmani bosing:"
    ),
    "stock_left": (
      "🛒 <b>{name}</b>\n"
      "Qoldiq: <b>{qty}</b> dona\n\n"
      "Nechta dona qo'shiladi? Raqam kiriting:"
    ),
    "buy_qty_prompt": (
      "⚡️ <b>Tezkor buyurtma</b>\n"
      "Mahsulot: <b>{name}</b>\n"
      "Qoldiq: <b>{qty}</b> dona\n\n"
      "Nechta dona kerak? Raqam kiriting:"
    ),
    "bad_qty": "❌ Musbat butun son kiriting:",
    "not_enough_stock": (
      "❌ Omborda faqat <b>{qty}</b> dona bor.\n"
      "Kamroq miqdor kiriting:"
    ),
    "ask_phone": (
      "📞 Telefon raqamingizni yuboring yoki «{share}» ni bosing\n"
      "(masalan: +998901234567):"
    ),
    "cart_cleared_toast": "Savat tozalandi.",
    "cart_empty_short": "🛒 Savat bo'sh.",
    "cart_empty_alert": "Savat bo'sh.",
    "checkout_intro": (
      "✅ Buyurtma summasi: <b>{total}</b>\n"
      "🛍 {count} xil mahsulot\n\n"
      "📞 Telefon raqamingizni yuboring yoki «{share}» ni bosing:"
    ),
    "restart_error": "Xatolik. Qaytadan boshlang.",
    "stock_short": "❌ Qoldiq yetarli emas ({qty} dona).",
    "cart_empty_long": "🛒 Savat bo'sh. Avval katalogdan mahsulot qo'shing.",
    "order_failed_error": "❌ Buyurtma yaratilmadi: {error}",
    "order_failed_stock": (
      "❌ Buyurtma yaratilmadi. Qoldiqni tekshirib, qayta urinib ko'ring."
    ),
    "order_created": (
      "✅ <b>Buyurtma yaratildi!</b>\n\n"
      "🆔 Raqam: <b>#{order_id}</b>\n"
      "🛍 Mahsulotlar: <b>{rows}</b> qator\n"
      "💰 Summa: <b>{total}</b>\n"
      "📞 Tel: <b>{phone}</b>\n"
      "⏳ Holat: <b>To'lov kutilmoqda</b>"
    ),
    "pay_finish": "💳 {label} orqali to'lovni yakunlang:",
    "invoice_not_opened": "Invoys ochilmadi. Qayta urinib ko'ring:",
    "choose_payment": "💳 To'lov usulini tanlang:",
    "payments_off": (
      "⚠️ Onlayn to'lov vaqtincha o'chirilgan. Admin tasdiqlashini kuting."
    ),
    "invoice_saved_failed": (
      "⚠️ Buyurtma saqlandi, lekin to'lov oynasi ochilmadi.\n{error}"
    ),
    "phone_missing": "❌ Telefon olinmadi. Qayta yuboring:",
    "phone_bad": "❌ Telefon raqam noto'g'ri. Qayta yuboring:",
    "phone_bad_share": (
      "❌ Telefon raqam noto'g'ri. Qayta yuboring\n"
      "yoki «{share}» ni bosing:"
    ),
    "qty_hint": "🔢 Miqdorni raqam bilan yozing:",
    "phone_hint": "📞 Telefon raqamni yuboring yoki «{share}» ni bosing:",
    "cart_title": "🛒 <b>Savat</b>",
    "cart_empty_hint": "Savat bo'sh. Mahsulot qo'shish uchun katalogga o'ting.",
    "cart_total": "\n💰 Jami: <b>{total}</b>",
    "pickup_short": "TATU, C-bino, 480-xona (Dush-Juma 09:00-17:00)",
    "pickup_address": "TATU, C-bino, 480-xona",
    "pickup_hours": "Dush-Juma 09:00-17:00",
    "pickup_guide": (
      "📍 <b>Qayerdan olib ketaman?</b>\n\n"
      "TATU, C-bino, 480-xona (Dush-Juma 09:00-17:00)\n"
      "4-qavat, 480-eshik.\n\n"
      "To'langan buyurtma kartasidagi QR ni xodimga ko'rsating.\n"
      "📞 {contact} ({phone})"
    ),
    "status_pending": "⏳ To'lov kutilmoqda",
    "status_paid": "🔘 Tayyor (480-xonadan olib ketishingiz mumkin)",
    "status_approved": "🔘 Tayyor (480-xonadan olib ketishingiz mumkin)",
    "status_delivered": "🎓 Topshirildi",
    "status_rejected": "❌ Bekor qilindi",
    "no_orders": "📦 Sizda hali buyurtmalar yo'q.",
    "no_active": "📦 Hozir olib ketiladigan buyurtma yo'q.",
    "history_title": "🗂 <b>Oldingi buyurtmalar</b>",
    "slip_id": "🆔 <b>Buyurtma ID:</b> <code>{code}</code>",
    "slip_product": "🛍 <b>Mahsulot:</b> {name} ({qty} dona)",
    "slip_status": "🔘 <b>Holati:</b> {status}",
    "slip_sum": "💰 <b>Summa:</b> {total}",
    "slip_address": "📍 <b>Manzil:</b> {address}",
    "slip_hours": "🕒 <b>Ish vaqti:</b> {hours}",
    "slip_contact": "📞 <b>Aloqa / Mas'ul:</b> {contact} ({phone})",
    "product_fallback": "Mahsulot",
    "qr_caption": (
      "🏷 <b>Olib ketish kodi</b> {code}\n"
      "480-xona xodimi shu QR ni skaner qiladi."
    ),
    "qr_paid_only": "QR faqat to'langan buyurtma uchun.",
    "your_claim_code": (
      "Bu sizning olib ketish kodingiz. Uni 480-xona xodimiga ko'rsating."
    ),
    "claim_staff_only": "Bu kod faqat 480-xona xodimi uchun.",
    "staff_only": "⛔ Bu amal faqat 480-xona xodimi uchun.",
    "order_not_found": "Buyurtma topilmadi.",
    "already_delivered": "ℹ️ {code} allaqachon topshirilgan.",
    "not_paid_yet": (
      "Bu buyurtma hali to'lanmagan. Topshirishdan oldin to'lovni tekshiring."
    ),
    "delivered_ok": "✅ {code} topshirildi.",
    "delivered_notice": (
      "🎉 Buyurtmangiz ({code}) muvaffaqiyatli topshirildi! "
      "TATU Brand Shop'ni tanlaganingiz uchun rahmat 🎓"
    ),
    "staff_slip": (
      "🆔 <b>Buyurtma:</b> <code>{code}</code>\n"
      "👤 <b>Xaridor:</b> {name}\n"
      "📞 <b>Telefon:</b> {phone}\n"
      "💰 <b>To'langan summa:</b> {total}\n"
      "🔘 <b>Holat:</b> {status}\n\n"
      "🛍 <b>Mahsulot:</b>\n{goods}"
    ),
    "stock_line": "• {name} × {qty} (omborda {left} dona)",
    "pay_provider_off": "⚠️ Bu to'lov usuli sozlanmagan. Boshqa usulni tanlang.",
    "pay_min": (
      "❌ {label} orqali minimal to'lov {amount}.\n"
      "Buyurtma saqlandi — boshqa usulni tanlang yoki savatga mahsulot qo'shing."
    ),
    "pay_window_failed": (
      "❌ {label} oynasi ochilmadi. Buyurtma saqlandi — "
      "quyidagi tugma orqali qayta urinib ko'ring.\n"
      "<code>{detail}</code>"
    ),
    "pay_intro": "💳 Buyurtma #{order_id} — {label}:",
    "pre_checkout_fail": "To'lovni vaqtincha tekshirib bo'lmadi. Qayta urinib ko'ring.",
    "pay_unknown_order": "❌ To'lov qabul qilindi, lekin buyurtma topilmadi.",
    "pay_db_fail": (
      "⚠️ To'lov qabul qilindi, lekin buyurtma #{order_id} ni "
      "yangilab bo'lmadi.\nSabab: {reason}\n"
      "🧾 {label} ID: <code>{charge}</code>\n"
      "Iltimos, admin bilan bog'laning."
    ),
    "pay_ok": (
      "✅ <b>To'lov tasdiqlandi</b>\n\n"
      "🆔 Buyurtma: <b>#{order_id}</b>\n"
      "💰 Summa: <b>{total}</b>\n"
      "🧾 {label} ID: <code>{charge}</code>\n\n"
      "{items}\n\n"
      "Mahsulotni TATU, C-bino, 480-xonadan olib ketasiz. Karta va QR pastda."
    ),
    "admin_new_order": (
      "🔔 <b>Yangi buyurtma #{order_id}</b>\n"
      "👤 {name}\n"
      "📞 {phone}\n"
      "🛍 {rows} qator\n"
      "💰 {total}\n"
      "💳 To'lov: kutilmoqda\n\n"
      "Tasdiqlash: «📋 Yangi buyurtmalar»"
    ),
    "admin_pay_db_fail": (
      "🚨 To'lov o'tdi, baza xato!\n"
      "Buyurtma #{order_id}\n"
      "👤 {name}\n"
      "📞 {phone}\n"
      "💰 {total}\n"
      "{reason}\n"
      "🧾 {label}: <code>{charge}</code>"
    ),
    "admin_paid": (
      "💳 <b>To'langan buyurtma #{order_id}</b>\n"
      "👤 {name}\n"
      "📞 {phone}\n"
      "💰 {total}\n"
      "🧾 {label}: <code>{charge}</code>\n\n"
      "{items}"
    ),
    "err_bad_payload": "Noto'g'ri to'lov ma'lumoti.",
    "err_order_missing": "Buyurtma topilmadi.",
    "err_not_owner": "Bu to'lov sizning buyurtmangizga tegishli emas.",
    "err_amount_changed": "To'lov summasi o'zgargan. Qaytadan urinib ko'ring.",
    "err_currency": "Valyuta qo'llab-quvvatlanmaydi.",
    "err_already_paid": "Buyurtma allaqachon to'langan.",
    "err_not_payable": "Bu buyurtma uchun to'lov qabul qilinmaydi.",
    "err_bad_total": "Buyurtma summasi noto'g'ri.",
    "err_no_items": "Buyurtmada mahsulot yo'q.",
    "err_not_for_sale": "«{name}» sotuvda emas.",
  },
  "ru": {
    "btn_catalog": "🛍 Каталог",
    "btn_cart": "🛒 Корзина",
    "btn_orders": "📦 Мои заказы",
    "btn_language": "🌐 Сменить язык",
    "btn_pickup": "📍 Где забрать?",
    "btn_cancel": "❌ Отмена",
    "btn_share_phone": "📱 Отправить номер",
    "btn_open_shop": "🛍 Открыть магазин",
    "btn_admin_menu": "⚙️ Admin menyu",
    "btn_add_one": "🛒 В корзину +1",
    "btn_buy_one": "⚡️ Заказать 1 шт.",
    "btn_add_qty": "🛒 Другое количество",
    "btn_buy_qty": "⚡️ Другое количество",
    "btn_back_catalog": "◀️ Каталог",
    "btn_checkout": "✅ Оформить заказ",
    "btn_clear_cart": "🗑 Очистить корзину",
    "btn_to_catalog": "🛍 В каталог",
    "btn_pay_click": "💳 Оплатить через Click",
    "btn_pay_payme": "🟢 Оплатить через Payme",
    "btn_qr": "🏷 Код выдачи (QR)",
    "btn_no_products": "Нет товаров",
    "choose_language": (
      "🌐 <b>Tilni tanlang</b>\n"
      "Выберите язык\n"
      "Choose a language"
    ),
    "language_saved": "✅ Язык сохранён: Русский",
    "language_save_failed": (
      "❌ Не удалось сохранить язык. В Supabase нет таблицы users. "
      "Запустите SQL-обновление и выберите язык снова."
    ),
    "welcome": (
      "🏛 <b>{shop}</b>\n\n"
      "Добро пожаловать! Ваша роль: <b>{role}</b>\n"
      "Пользуйтесь меню ниже."
    ),
    "role_admin": "Админ",
    "role_client": "Клиент",
    "help_admin": (
      "⚙️ <b>Помощь админу</b>\n\n"
      "• Добавление / приход / управление товарами\n"
      "• Подтверждение и отклонение новых заказов\n"
      "• В комнате 480: код (#TATU-42 или 42) или QR клиента\n"
      "• Статистика и история\n"
      "• Каталог через «Меню клиента»"
    ),
    "help_client": (
      "ℹ️ <b>Помощь</b>\n\n"
      "• Выберите товар в каталоге\n"
      "• Добавьте в корзину или оформите быстрый заказ\n"
      "• В «Мои заказы» — карточка выдачи и QR\n"
      "• «Где забрать?» — корпус C, комната 480\n"
      "• «Сменить язык» — узбекский / русский / английский"
    ),
    "client_menu_opened": (
      "🛍 Открыто меню клиента.\n"
      "Вернуться в админку: «⚙️ Admin menyu»."
    ),
    "admin_menu_opened": "⚙️ Меню админа открыто.",
    "no_permission": "⛔ Нет доступа.",
    "use_menu": "ℹ️ Используйте кнопки меню.",
    "cancelled": "❌ Отменено.",
    "order_cancelled": "❌ Заказ отменён.",
    "ordering_busy": (
      "⏳ Оформление заказа ещё идёт.\n"
      "Отправьте телефон или количество, либо нажмите «{cancel}»."
    ),
    "catalog_title": "🛍 <b>Каталог</b>",
    "catalog_empty": "Сейчас нет товаров в продаже.",
    "catalog_pick": "Выберите товар:",
    "catalog_body": "🛍 <b>Каталог</b>\n\nВыберите товар:",
    "product_unavailable": "Товар недоступен.",
    "product_missing": "Товар не найден.",
    "product_link_missing": (
      "❌ Товар не найден или сейчас не продаётся.\n"
      "Выберите другой товар в каталоге."
    ),
    "product_link_opened": "🛍 Товар открыт по QR / ссылке:",
    "added_toast": "Добавлено в корзину ✅",
    "added_hint": (
      "✅ В корзину: <b>{name}</b> × 1\n"
      "Добавьте ещё или оформите заказ через «{cart}»."
    ),
    "added_named": "✅ В корзину: <b>{name}</b> × {qty}",
    "order_line": (
      "⚡️ <b>Заказ:</b> {name} × {qty}\n"
      "💰 {price}\n\n"
      "📞 Отправьте номер телефона или нажмите кнопку:"
    ),
    "stock_left": (
      "🛒 <b>{name}</b>\n"
      "Остаток: <b>{qty}</b> шт.\n\n"
      "Сколько добавить? Введите число:"
    ),
    "buy_qty_prompt": (
      "⚡️ <b>Быстрый заказ</b>\n"
      "Товар: <b>{name}</b>\n"
      "Остаток: <b>{qty}</b> шт.\n\n"
      "Сколько нужно? Введите число:"
    ),
    "bad_qty": "❌ Введите целое число больше нуля:",
    "not_enough_stock": (
      "❌ На складе только <b>{qty}</b> шт.\n"
      "Введите меньшее количество:"
    ),
    "ask_phone": (
      "📞 Отправьте номер или нажмите «{share}»\n"
      "(например: +998901234567):"
    ),
    "cart_cleared_toast": "Корзина очищена.",
    "cart_empty_short": "🛒 Корзина пуста.",
    "cart_empty_alert": "Корзина пуста.",
    "checkout_intro": (
      "✅ Сумма заказа: <b>{total}</b>\n"
      "🛍 {count} поз.\n\n"
      "📞 Отправьте номер или нажмите «{share}»:"
    ),
    "restart_error": "Ошибка. Начните заново.",
    "stock_short": "❌ Недостаточно остатка ({qty} шт.).",
    "cart_empty_long": "🛒 Корзина пуста. Сначала добавьте товар из каталога.",
    "order_failed_error": "❌ Заказ не создан: {error}",
    "order_failed_stock": "❌ Заказ не создан. Проверьте остаток и попробуйте снова.",
    "order_created": (
      "✅ <b>Заказ создан!</b>\n\n"
      "🆔 Номер: <b>#{order_id}</b>\n"
      "🛍 Позиций: <b>{rows}</b>\n"
      "💰 Сумма: <b>{total}</b>\n"
      "📞 Тел: <b>{phone}</b>\n"
      "⏳ Статус: <b>Ожидает оплату</b>"
    ),
    "pay_finish": "💳 Завершите оплату через {label}:",
    "invoice_not_opened": "Счёт не открылся. Попробуйте ещё раз:",
    "choose_payment": "💳 Выберите способ оплаты:",
    "payments_off": "⚠️ Онлайн-оплата временно отключена. Дождитесь подтверждения админа.",
    "invoice_saved_failed": "⚠️ Заказ сохранён, но окно оплаты не открылось.\n{error}",
    "phone_missing": "❌ Номер не получен. Отправьте ещё раз:",
    "phone_bad": "❌ Неверный номер. Отправьте ещё раз:",
    "phone_bad_share": (
      "❌ Неверный номер. Отправьте ещё раз\n"
      "или нажмите «{share}»:"
    ),
    "qty_hint": "🔢 Напишите количество числом:",
    "phone_hint": "📞 Отправьте номер или нажмите «{share}»:",
    "cart_title": "🛒 <b>Корзина</b>",
    "cart_empty_hint": "Корзина пуста. Перейдите в каталог, чтобы добавить товар.",
    "cart_total": "\n💰 Итого: <b>{total}</b>",
    "pickup_short": "ТУИТ, корпус C, комната 480 (Пн-Пт 09:00-17:00)",
    "pickup_address": "ТУИТ, корпус C, комната 480",
    "pickup_hours": "Пн-Пт 09:00-17:00",
    "pickup_guide": (
      "📍 <b>Где забрать заказ?</b>\n\n"
      "ТУИТ, корпус C, комната 480 (Пн-Пт 09:00-17:00)\n"
      "4-й этаж, дверь 480.\n\n"
      "Покажите сотруднику QR с карточки оплаченного заказа.\n"
      "📞 {contact} ({phone})"
    ),
    "status_pending": "⏳ Ожидает оплату",
    "status_paid": "🔘 Готово (можно забрать в комнате 480)",
    "status_approved": "🔘 Готово (можно забрать в комнате 480)",
    "status_delivered": "🎓 Выдано",
    "status_rejected": "❌ Отменён",
    "no_orders": "📦 У вас пока нет заказов.",
    "no_active": "📦 Сейчас нет заказов к выдаче.",
    "history_title": "🗂 <b>Прошлые заказы</b>",
    "slip_id": "🆔 <b>ID заказа:</b> <code>{code}</code>",
    "slip_product": "🛍 <b>Товар:</b> {name} ({qty} шт.)",
    "slip_status": "🔘 <b>Статус:</b> {status}",
    "slip_sum": "💰 <b>Сумма:</b> {total}",
    "slip_address": "📍 <b>Адрес:</b> {address}",
    "slip_hours": "🕒 <b>Часы:</b> {hours}",
    "slip_contact": "📞 <b>Контакт:</b> {contact} ({phone})",
    "product_fallback": "Товар",
    "qr_caption": (
      "🏷 <b>Код выдачи</b> {code}\n"
      "Сотрудник комнаты 480 сканирует этот QR."
    ),
    "qr_paid_only": "QR только для оплаченного заказа.",
    "your_claim_code": "Это ваш код выдачи. Покажите его сотруднику комнаты 480.",
    "claim_staff_only": "Этот код только для сотрудника комнаты 480.",
    "staff_only": "⛔ Это действие только для сотрудника комнаты 480.",
    "order_not_found": "Заказ не найден.",
    "already_delivered": "ℹ️ {code} уже выдан.",
    "not_paid_yet": "Этот заказ ещё не оплачен. Проверьте оплату перед выдачей.",
    "delivered_ok": "✅ {code} выдан.",
    "delivered_notice": (
      "🎉 Ваш заказ ({code}) успешно выдан! "
      "Спасибо, что выбрали TATU Brand Shop 🎓"
    ),
    "staff_slip": (
      "🆔 <b>Заказ:</b> <code>{code}</code>\n"
      "👤 <b>Покупатель:</b> {name}\n"
      "📞 <b>Телефон:</b> {phone}\n"
      "💰 <b>Сумма:</b> {total}\n"
      "🔘 <b>Статус:</b> {status}\n\n"
      "🛍 <b>Товар:</b>\n{goods}"
    ),
    "stock_line": "• {name} × {qty} (на складе {left} шт.)",
    "pay_provider_off": "⚠️ Этот способ оплаты не настроен. Выберите другой.",
    "pay_min": (
      "❌ Минимальная оплата через {label}: {amount}.\n"
      "Заказ сохранён — выберите другой способ или добавьте товар."
    ),
    "pay_window_failed": (
      "❌ Окно {label} не открылось. Заказ сохранён — "
      "попробуйте кнопкой ниже.\n"
      "<code>{detail}</code>"
    ),
    "pay_intro": "💳 Заказ #{order_id} — {label}:",
    "pre_checkout_fail": "Не удалось проверить оплату. Попробуйте ещё раз.",
    "pay_unknown_order": "❌ Оплата принята, но заказ не найден.",
    "pay_db_fail": (
      "⚠️ Оплата принята, но заказ #{order_id} не обновлён.\n"
      "Причина: {reason}\n"
      "🧾 {label} ID: <code>{charge}</code>\n"
      "Свяжитесь с администратором."
    ),
    "pay_ok": (
      "✅ <b>Оплата подтверждена</b>\n\n"
      "🆔 Заказ: <b>#{order_id}</b>\n"
      "💰 Сумма: <b>{total}</b>\n"
      "🧾 {label} ID: <code>{charge}</code>\n\n"
      "{items}\n\n"
      "Заберите товар: ТУИТ, корпус C, комната 480. Карточка и QR ниже."
    ),
    "admin_new_order": (
      "🔔 <b>Новый заказ #{order_id}</b>\n"
      "👤 {name}\n"
      "📞 {phone}\n"
      "🛍 {rows} поз.\n"
      "💰 {total}\n"
      "💳 Оплата: ожидается\n\n"
      "Подтверждение: «📋 Yangi buyurtmalar»"
    ),
    "admin_pay_db_fail": (
      "🚨 Оплата прошла, ошибка базы!\n"
      "Заказ #{order_id}\n"
      "👤 {name}\n"
      "📞 {phone}\n"
      "💰 {total}\n"
      "{reason}\n"
      "🧾 {label}: <code>{charge}</code>"
    ),
    "admin_paid": (
      "💳 <b>Оплаченный заказ #{order_id}</b>\n"
      "👤 {name}\n"
      "📞 {phone}\n"
      "💰 {total}\n"
      "🧾 {label}: <code>{charge}</code>\n\n"
      "{items}"
    ),
    "err_bad_payload": "Неверные данные оплаты.",
    "err_order_missing": "Заказ не найден.",
    "err_not_owner": "Эта оплата не относится к вашему заказу.",
    "err_amount_changed": "Сумма изменилась. Попробуйте снова.",
    "err_currency": "Валюта не поддерживается.",
    "err_already_paid": "Заказ уже оплачен.",
    "err_not_payable": "Оплата по этому заказу не принимается.",
    "err_bad_total": "Неверная сумма заказа.",
    "err_no_items": "В заказе нет товаров.",
    "err_not_for_sale": "«{name}» нет в продаже.",
  },
  "en": {
    "btn_catalog": "🛍 Catalog",
    "btn_cart": "🛒 Cart",
    "btn_orders": "📦 My Orders",
    "btn_language": "🌐 Change Language",
    "btn_pickup": "📍 Where to pick up?",
    "btn_cancel": "❌ Cancel",
    "btn_share_phone": "📱 Share phone number",
    "btn_open_shop": "🛍 Open shop",
    "btn_admin_menu": "⚙️ Admin menyu",
    "btn_add_one": "🛒 Add 1 to cart",
    "btn_buy_one": "⚡️ Order 1 item",
    "btn_add_qty": "🛒 Other quantity",
    "btn_buy_qty": "⚡️ Other quantity",
    "btn_back_catalog": "◀️ Catalog",
    "btn_checkout": "✅ Place order",
    "btn_clear_cart": "🗑 Clear cart",
    "btn_to_catalog": "🛍 Back to catalog",
    "btn_pay_click": "💳 Pay with Click",
    "btn_pay_payme": "🟢 Pay with Payme",
    "btn_qr": "🏷 Pickup code (QR)",
    "btn_no_products": "No products",
    "choose_language": (
      "🌐 <b>Tilni tanlang</b>\n"
      "Выберите язык\n"
      "Choose a language"
    ),
    "language_saved": "✅ Language saved: English",
    "language_save_failed": (
      "❌ Could not save the language. The users table is missing in Supabase. "
      "Run the SQL update and choose again."
    ),
    "welcome": (
      "🏛 <b>{shop}</b>\n\n"
      "Welcome! Your role: <b>{role}</b>\n"
      "Use the menu below."
    ),
    "role_admin": "Admin",
    "role_client": "Customer",
    "help_admin": (
      "⚙️ <b>Admin help</b>\n\n"
      "• Add products, stock in, manage items\n"
      "• Approve or reject new orders\n"
      "• In room 480: code (#TATU-42 or 42) or the customer's QR\n"
      "• Stats and history\n"
      "• Open the catalog via the client menu"
    ),
    "help_client": (
      "ℹ️ <b>Help</b>\n\n"
      "• Pick a product from the catalog\n"
      "• Add it to the cart or place a quick order\n"
      "• My Orders shows the pickup card and QR\n"
      "• Where to pick up — Building C, room 480\n"
      "• Change Language — Uzbek / Russian / English"
    ),
    "client_menu_opened": (
      "🛍 Client menu opened.\n"
      "Back to admin: «⚙️ Admin menyu»."
    ),
    "admin_menu_opened": "⚙️ Admin menu opened.",
    "no_permission": "⛔ No permission.",
    "use_menu": "ℹ️ Use the menu buttons.",
    "cancelled": "❌ Cancelled.",
    "order_cancelled": "❌ Order cancelled.",
    "ordering_busy": (
      "⏳ An order is still in progress.\n"
      "Send a phone number or quantity, or tap «{cancel}»."
    ),
    "catalog_title": "🛍 <b>Catalog</b>",
    "catalog_empty": "Nothing is for sale right now.",
    "catalog_pick": "Choose a product:",
    "catalog_body": "🛍 <b>Catalog</b>\n\nChoose a product:",
    "product_unavailable": "This product is unavailable.",
    "product_missing": "Product not found.",
    "product_link_missing": (
      "❌ This product was not found or is not for sale.\n"
      "Choose another product from the catalog."
    ),
    "product_link_opened": "🛍 Product opened from a QR / link:",
    "added_toast": "Added to cart ✅",
    "added_hint": (
      "✅ Added to cart: <b>{name}</b> × 1\n"
      "Add more, or check out from «{cart}»."
    ),
    "added_named": "✅ Added to cart: <b>{name}</b> × {qty}",
    "order_line": (
      "⚡️ <b>Order:</b> {name} × {qty}\n"
      "💰 {price}\n\n"
      "📞 Send your phone number or tap the button:"
    ),
    "stock_left": (
      "🛒 <b>{name}</b>\n"
      "In stock: <b>{qty}</b>\n\n"
      "How many should be added? Enter a number:"
    ),
    "buy_qty_prompt": (
      "⚡️ <b>Quick order</b>\n"
      "Product: <b>{name}</b>\n"
      "In stock: <b>{qty}</b>\n\n"
      "How many do you need? Enter a number:"
    ),
    "bad_qty": "❌ Enter a whole number greater than zero:",
    "not_enough_stock": (
      "❌ Only <b>{qty}</b> left in stock.\n"
      "Enter a smaller quantity:"
    ),
    "ask_phone": (
      "📞 Send your phone number or tap «{share}»\n"
      "(example: +998901234567):"
    ),
    "cart_cleared_toast": "Cart cleared.",
    "cart_empty_short": "🛒 Your cart is empty.",
    "cart_empty_alert": "Your cart is empty.",
    "checkout_intro": (
      "✅ Order total: <b>{total}</b>\n"
      "🛍 {count} products\n\n"
      "📞 Send your phone number or tap «{share}»:"
    ),
    "restart_error": "Something went wrong. Please start again.",
    "stock_short": "❌ Not enough stock ({qty} left).",
    "cart_empty_long": "🛒 Your cart is empty. Add a product from the catalog first.",
    "order_failed_error": "❌ Could not create the order: {error}",
    "order_failed_stock": "❌ Could not create the order. Check stock and try again.",
    "order_created": (
      "✅ <b>Order created!</b>\n\n"
      "🆔 Number: <b>#{order_id}</b>\n"
      "🛍 Lines: <b>{rows}</b>\n"
      "💰 Total: <b>{total}</b>\n"
      "📞 Phone: <b>{phone}</b>\n"
      "⏳ Status: <b>Waiting for payment</b>"
    ),
    "pay_finish": "💳 Finish payment with {label}:",
    "invoice_not_opened": "The invoice did not open. Try again:",
    "choose_payment": "💳 Choose a payment method:",
    "payments_off": "⚠️ Online payment is temporarily off. Wait for an admin to confirm.",
    "invoice_saved_failed": (
      "⚠️ The order was saved, but the payment window did not open.\n{error}"
    ),
    "phone_missing": "❌ Phone number was not received. Send it again:",
    "phone_bad": "❌ That phone number is invalid. Send it again:",
    "phone_bad_share": (
      "❌ That phone number is invalid. Send it again\n"
      "or tap «{share}»:"
    ),
    "qty_hint": "🔢 Type the quantity as a number:",
    "phone_hint": "📞 Send a phone number or tap «{share}»:",
    "cart_title": "🛒 <b>Cart</b>",
    "cart_empty_hint": "Your cart is empty. Open the catalog to add a product.",
    "cart_total": "\n💰 Total: <b>{total}</b>",
    "pickup_short": "TUIT, Building C, Room 480 (Mon-Fri 09:00-17:00)",
    "pickup_address": "TUIT, Building C, Room 480",
    "pickup_hours": "Mon-Fri 09:00-17:00",
    "pickup_guide": (
      "📍 <b>Where do I pick up?</b>\n\n"
      "TUIT, Building C, Room 480 (Mon-Fri 09:00-17:00)\n"
      "4th floor, door 480.\n\n"
      "Show the staff the QR from your paid order card.\n"
      "📞 {contact} ({phone})"
    ),
    "status_pending": "⏳ Waiting for payment",
    "status_paid": "🔘 Ready (pick up from room 480)",
    "status_approved": "🔘 Ready (pick up from room 480)",
    "status_delivered": "🎓 Delivered",
    "status_rejected": "❌ Cancelled",
    "no_orders": "📦 You have no orders yet.",
    "no_active": "📦 There is no order ready for pickup right now.",
    "history_title": "🗂 <b>Earlier orders</b>",
    "slip_id": "🆔 <b>Order ID:</b> <code>{code}</code>",
    "slip_product": "🛍 <b>Product:</b> {name} ({qty})",
    "slip_status": "🔘 <b>Status:</b> {status}",
    "slip_sum": "💰 <b>Total:</b> {total}",
    "slip_address": "📍 <b>Address:</b> {address}",
    "slip_hours": "🕒 <b>Hours:</b> {hours}",
    "slip_contact": "📞 <b>Contact:</b> {contact} ({phone})",
    "product_fallback": "Product",
    "qr_caption": (
      "🏷 <b>Pickup code</b> {code}\n"
      "Room 480 staff scan this QR."
    ),
    "qr_paid_only": "QR is only for a paid order.",
    "your_claim_code": "This is your pickup code. Show it to the room 480 staff.",
    "claim_staff_only": "This code is only for room 480 staff.",
    "staff_only": "⛔ Only room 480 staff can do this.",
    "order_not_found": "Order not found.",
    "already_delivered": "ℹ️ {code} was already handed over.",
    "not_paid_yet": "This order is not paid yet. Check payment before handing it over.",
    "delivered_ok": "✅ {code} handed over.",
    "delivered_notice": (
      "🎉 Your order ({code}) was handed over! "
      "Thank you for choosing TATU Brand Shop 🎓"
    ),
    "staff_slip": (
      "🆔 <b>Order:</b> <code>{code}</code>\n"
      "👤 <b>Customer:</b> {name}\n"
      "📞 <b>Phone:</b> {phone}\n"
      "💰 <b>Amount:</b> {total}\n"
      "🔘 <b>Status:</b> {status}\n\n"
      "🛍 <b>Items:</b>\n{goods}"
    ),
    "stock_line": "• {name} × {qty} ({left} in stock)",
    "pay_provider_off": "⚠️ This payment method is not set up. Choose another one.",
    "pay_min": (
      "❌ Minimum payment via {label} is {amount}.\n"
      "The order is saved — choose another method or add a product."
    ),
    "pay_window_failed": (
      "❌ The {label} window did not open. The order is saved — "
      "try the button below.\n"
      "<code>{detail}</code>"
    ),
    "pay_intro": "💳 Order #{order_id} — {label}:",
    "pre_checkout_fail": "Payment could not be checked right now. Try again.",
    "pay_unknown_order": "❌ Payment was received, but the order was not found.",
    "pay_db_fail": (
      "⚠️ Payment was received, but order #{order_id} could not be updated.\n"
      "Reason: {reason}\n"
      "🧾 {label} ID: <code>{charge}</code>\n"
      "Please contact an admin."
    ),
    "pay_ok": (
      "✅ <b>Payment confirmed</b>\n\n"
      "🆔 Order: <b>#{order_id}</b>\n"
      "💰 Total: <b>{total}</b>\n"
      "🧾 {label} ID: <code>{charge}</code>\n\n"
      "{items}\n\n"
      "Pick up at TUIT, Building C, Room 480. The card and QR are below."
    ),
    "admin_new_order": (
      "🔔 <b>New order #{order_id}</b>\n"
      "👤 {name}\n"
      "📞 {phone}\n"
      "🛍 {rows} lines\n"
      "💰 {total}\n"
      "💳 Payment: waiting\n\n"
      "Approve via «📋 Yangi buyurtmalar»"
    ),
    "admin_pay_db_fail": (
      "🚨 Payment went through, database error!\n"
      "Order #{order_id}\n"
      "👤 {name}\n"
      "📞 {phone}\n"
      "💰 {total}\n"
      "{reason}\n"
      "🧾 {label}: <code>{charge}</code>"
    ),
    "admin_paid": (
      "💳 <b>Paid order #{order_id}</b>\n"
      "👤 {name}\n"
      "📞 {phone}\n"
      "💰 {total}\n"
      "🧾 {label}: <code>{charge}</code>\n\n"
      "{items}"
    ),
    "err_bad_payload": "Invalid payment data.",
    "err_order_missing": "Order not found.",
    "err_not_owner": "This payment does not belong to your order.",
    "err_amount_changed": "The amount changed. Please try again.",
    "err_currency": "This currency is not supported.",
    "err_already_paid": "This order is already paid.",
    "err_not_payable": "Payment is not accepted for this order.",
    "err_bad_total": "The order total is invalid.",
    "err_no_items": "This order has no products.",
    "err_not_for_sale": "«{name}» is not for sale.",
  },
}
