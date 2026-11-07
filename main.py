# ============================================================
# Система заказов «Пиццерия»
# ООП (инкапсуляция, наследование, полиморфизм) + JSON + валидация
# ============================================================
import hashlib
import json
import os

DATA_FILE = "data.json"
ADMIN_CODE = "admin2024"  # секретный код для регистрации администратора
SIZE_MULTIPLIERS = {"S": 0.8, "M": 1.0, "L": 1.3}
STATUSES = ["Новый", "Готовится", "Доставляется", "Выполнен"]


# ============================================================
# Валидация ввода
# ============================================================
def input_text(prompt, min_length=1):
    """Строка без пробелов по краям, не короче min_length символов."""
    while True:
        value = input(prompt).strip()
        if len(value) >= min_length:
            return value
        if min_length == 1:
            print("Ошибка: строка не может быть пустой.")
        else:
            print(f"Ошибка: минимум {min_length} символа(ов).")


def input_number(prompt, cast=int, min_value=None, max_value=None):
    """Число нужного типа (int/float) в заданном диапазоне."""
    while True:
        try:
            value = cast(input(prompt))
        except ValueError:
            print("Ошибка: введите число.")
            continue
        if min_value is not None and value < min_value:
            print(f"Ошибка: значение не может быть меньше {min_value}.")
        elif max_value is not None and value > max_value:
            print(f"Ошибка: значение не может быть больше {max_value}.")
        else:
            return value


def money(value):
    return f"{value:.0f} ₸"


# ============================================================
# Товары: базовый класс Product -> Pizza, Drink
# ============================================================
class Product:
    HAS_SIZES = False

    def __init__(self, name, price):
        self._name = name
        self._price = price

    @property
    def name(self):
        return self._name

    def get_price(self, size=None):
        """Цена за единицу. В наследниках переопределяется (полиморфизм)."""
        return self._price

    def get_info(self):
        return f"{self._name} — {money(self._price)}"

    def to_dict(self):
        return {"type": "product", "name": self._name, "price": self._price}


class Pizza(Product):
    HAS_SIZES = True

    def get_price(self, size="M"):
        return round(self._price * SIZE_MULTIPLIERS[size])

    def get_info(self):
        prices = " / ".join(f"{s} {self.get_price(s)}" for s in SIZE_MULTIPLIERS)
        return f"Пицца «{self._name}»: {prices} ₸"

    def to_dict(self):
        return {"type": "pizza", "name": self._name, "price": self._price}


class Drink(Product):
    def __init__(self, name, price, volume):
        super().__init__(name, price)
        self._volume = volume

    def get_info(self):
        return f"Напиток «{self._name}» {self._volume} л — {money(self._price)}"

    def to_dict(self):
        return {"type": "drink", "name": self._name,
                "price": self._price, "volume": self._volume}


def product_from_dict(data):
    if data["type"] == "pizza":
        return Pizza(data["name"], data["price"])
    if data["type"] == "drink":
        return Drink(data["name"], data["price"], data["volume"])
    return Product(data["name"], data["price"])


# ============================================================
# Пользователи: базовый класс User -> Client, Admin
# ============================================================
class User:
    ROLE_TITLE = "Пользователь"

    def __init__(self, login, password_hash):
        self._login = login
        self.__password_hash = password_hash  # приватное поле

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def check_password(self, password):
        return self.__password_hash == self.hash_password(password)

    @property
    def login(self):
        return self._login

    def get_info(self):
        return f"Логин: {self._login}\nРоль: {self.ROLE_TITLE}"

    def to_dict(self):
        return {"login": self._login, "password_hash": self.__password_hash}

    def run_menu(self, shop):
        raise NotImplementedError("Меню определяется в дочернем классе")


class Client(User):
    ROLE_TITLE = "Клиент"

    def __init__(self, login, password_hash, balance=0.0, cart=None):
        super().__init__(login, password_hash)
        self._balance = balance
        self._cart = cart if cart is not None else []

    # --- баланс ---
    def get_balance(self):
        return self._balance

    def top_up(self, amount):
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self._balance += amount

    def pay(self, amount):
        if amount > self._balance:
            raise ValueError("Недостаточно средств на балансе")
        self._balance -= amount

    # --- корзина ---
    def get_cart(self):
        return self._cart

    def add_to_cart(self, name, size, price, qty):
        self._cart.append({"name": name, "size": size, "price": price, "qty": qty})

    def cart_total(self):
        return sum(item["price"] * item["qty"] for item in self._cart)

    def clear_cart(self):
        self._cart.clear()

    def get_info(self):
        return (super().get_info()
                + f"\nБаланс: {money(self._balance)}"
                + f"\nПозиций в корзине: {len(self._cart)}")

    def to_dict(self):
        data = super().to_dict()
        data.update({"role": "client", "balance": self._balance, "cart": self._cart})
        return data

    # --- меню клиента ---
    def run_menu(self, shop):
        while True:
            print(f"\n--- Меню клиента ({self._login}) ---")
            print("1. Заказать еду")
            print("2. Баланс и история заказов")
            print("3. Показать информацию о профиле")
            print("4. Выйти из аккаунта")
            choice = input_number("Выбор: ", int, 1, 4)

            if choice == 1:
                self._order_menu(shop)
            elif choice == 2:
                self._balance_menu(shop)
            elif choice == 3:
                print("\n" + self.get_info())
            else:
                print("Вы вышли из аккаунта.")
                break

    def _order_menu(self, shop):
        while True:
            print("\n-- Заказ --")
            print("1. Показать меню")
            print("2. Добавить в корзину")
            print("3. Показать корзину")
            print("4. Очистить корзину")
            print("5. Оформить заказ")
            print("0. Назад")
            choice = input_number("Выбор: ", int, 0, 5)

            if choice == 1:
                shop.show_menu()
            elif choice == 2:
                self._add_item(shop)
            elif choice == 3:
                self._show_cart()
            elif choice == 4:
                self.clear_cart()
                shop.save()
                print("Корзина очищена.")
            elif choice == 5:
                self._checkout(shop)
            else:
                break

    def _add_item(self, shop):
        if not shop.products:
            print("Меню пока пустое.")
            return
        shop.show_menu()
        index = input_number("Номер позиции: ", int, 1, len(shop.products)) - 1
        product = shop.products[index]

        size = None
        if product.HAS_SIZES:
            print("Размер: 1 — S, 2 — M, 3 — L")
            size = ["S", "M", "L"][input_number("Выбор размера: ", int, 1, 3) - 1]

        qty = input_number("Количество (1-10): ", int, 1, 10)
        self.add_to_cart(product.name, size, product.get_price(size), qty)
        shop.save()
        print("Добавлено в корзину.")

    def _show_cart(self):
        if not self._cart:
            print("Корзина пуста.")
            return
        print("\nКорзина:")
        for i, item in enumerate(self._cart, start=1):
            size = f" ({item['size']})" if item["size"] else ""
            print(f"{i}. {item['name']}{size} x{item['qty']} = {money(item['price'] * item['qty'])}")
        print(f"Итого: {money(self.cart_total())}")

    def _checkout(self, shop):
        if not self._cart:
            print("Корзина пуста — нечего оформлять.")
            return
        total = self.cart_total()
        try:
            self.pay(total)
        except ValueError as error:
            print(f"Ошибка: {error}. К оплате {money(total)}, на балансе {money(self._balance)}.")
            return
        order = {
            "id": shop.next_order_id(),
            "client": self._login,
            "items": [dict(item) for item in self._cart],
            "total": total,
            "status": STATUSES[0],
        }
        shop.orders.append(order)
        self.clear_cart()
        shop.save()
        print(f"Заказ №{order['id']} оформлен! Списано {money(total)}.")

    def _balance_menu(self, shop):
        while True:
            print(f"\n-- Баланс: {money(self._balance)} --")
            print("1. Пополнить баланс")
            print("2. История заказов")
            print("0. Назад")
            choice = input_number("Выбор: ", int, 0, 2)

            if choice == 1:
                amount = input_number("Сумма пополнения: ", float, 1)
                try:
                    self.top_up(amount)
                    shop.save()
                    print(f"Баланс пополнен. Сейчас: {money(self._balance)}")
                except ValueError as error:
                    print(f"Ошибка: {error}.")
            elif choice == 2:
                my_orders = [o for o in shop.orders if o["client"] == self._login]
                if not my_orders:
                    print("У вас пока нет заказов.")
                for order in my_orders:
                    print(format_order(order))
            else:
                break


class Admin(User):
    ROLE_TITLE = "Администратор"

    def to_dict(self):
        data = super().to_dict()
        data["role"] = "admin"
        return data

    # --- меню администратора ---
    def run_menu(self, shop):
        while True:
            print(f"\n--- Меню администратора ({self._login}) ---")
            print("1. Управление меню и заказами")
            print("2. Статистика")
            print("3. Показать информацию о профиле")
            print("4. Выйти из аккаунта")
            choice = input_number("Выбор: ", int, 1, 4)

            if choice == 1:
                self._manage_menu(shop)
            elif choice == 2:
                self._show_stats(shop)
            elif choice == 3:
                print("\n" + self.get_info())
            else:
                print("Вы вышли из аккаунта.")
                break

    def _manage_menu(self, shop):
        while True:
            print("\n-- Управление --")
            print("1. Показать меню")
            print("2. Добавить товар")
            print("3. Удалить товар")
            print("4. Все заказы")
            print("5. Изменить статус заказа")
            print("0. Назад")
            choice = input_number("Выбор: ", int, 0, 5)

            if choice == 1:
                shop.show_menu()
            elif choice == 2:
                self._add_product(shop)
            elif choice == 3:
                self._delete_product(shop)
            elif choice == 4:
                if not shop.orders:
                    print("Заказов пока нет.")
                for order in shop.orders:
                    print(format_order(order))
            elif choice == 5:
                self._change_status(shop)
            else:
                break

    def _add_product(self, shop):
        print("Тип: 1 — пицца, 2 — напиток")
        kind = input_number("Выбор: ", int, 1, 2)
        name = input_text("Название: ")
        if any(p.name.lower() == name.lower() for p in shop.products):
            print("Ошибка: товар с таким названием уже есть.")
            return
        price = input_number("Базовая цена (₸): ", float, 1)
        if kind == 1:
            shop.products.append(Pizza(name, price))
        else:
            volume = input_number("Объём (л): ", float, 0.05)
            shop.products.append(Drink(name, price, volume))
        shop.save()
        print("Товар добавлен.")

    def _delete_product(self, shop):
        if not shop.products:
            print("Меню пустое.")
            return
        shop.show_menu()
        index = input_number("Номер товара для удаления: ", int, 1, len(shop.products)) - 1
        removed = shop.products.pop(index)
        shop.save()
        print(f"Товар «{removed.name}» удалён.")

    def _change_status(self, shop):
        if not shop.orders:
            print("Заказов пока нет.")
            return
        order_id = input_number("Номер заказа: ", int, 1)
        order = next((o for o in shop.orders if o["id"] == order_id), None)
        if order is None:
            print("Заказ не найден.")
            return
        for i, status in enumerate(STATUSES, start=1):
            print(f"{i}. {status}")
        new_status = STATUSES[input_number("Новый статус: ", int, 1, len(STATUSES)) - 1]
        order["status"] = new_status
        shop.save()
        print(f"Статус заказа №{order_id} изменён на «{new_status}».")

    def _show_stats(self, shop):
        revenue = sum(o["total"] for o in shop.orders)
        clients = sum(1 for u in shop.users.values() if isinstance(u, Client))
        print("\n-- Статистика --")
        print(f"Клиентов: {clients}")
        print(f"Заказов: {len(shop.orders)}")
        print(f"Выручка: {money(revenue)}")
        for status in STATUSES:
            count = sum(1 for o in shop.orders if o["status"] == status)
            print(f"  {status}: {count}")


def user_from_dict(data):
    if data["role"] == "admin":
        return Admin(data["login"], data["password_hash"])
    return Client(data["login"], data["password_hash"],
                  data.get("balance", 0.0), data.get("cart", []))


def format_order(order):
    lines = [f"Заказ №{order['id']} | клиент: {order['client']} | статус: {order['status']}"]
    for item in order["items"]:
        size = f" ({item['size']})" if item["size"] else ""
        lines.append(f"   {item['name']}{size} x{item['qty']} = {money(item['price'] * item['qty'])}")
    lines.append(f"   Итого: {money(order['total'])}")
    return "\n".join(lines)


# ============================================================
# Магазин: хранение данных и работа с JSON
# ============================================================
class Shop:
    def __init__(self):
        self.users = {}     # {логин: объект User}
        self.products = []  # список Product
        self.orders = []    # список словарей-заказов
        self.load()

    def _create_defaults(self):
        self.users = {"admin": Admin("admin", User.hash_password("admin123"))}
        self.products = [
            Pizza("Маргарита", 3000),
            Pizza("Пепперони", 3500),
            Pizza("Четыре сыра", 4000),
            Drink("Кола", 700, 0.5),
            Drink("Сок яблочный", 600, 0.33),
        ]
        self.orders = []

    def load(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            users = {u["login"]: user_from_dict(u) for u in data["users"]}
            products = [product_from_dict(p) for p in data["products"]]
            orders = data["orders"]
        except FileNotFoundError:
            print("Файл данных не найден — создан новый (админ: admin / admin123).")
            self._create_defaults()
            self.save()
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            print(f"Файл данных повреждён ({error}). Создаём новый, старый сохранён как .bak")
            try:
                os.replace(DATA_FILE, DATA_FILE + ".bak")
            except OSError:
                pass
            self._create_defaults()
            self.save()
        else:
            self.users, self.products, self.orders = users, products, orders

    def save(self):
        data = {
            "users": [u.to_dict() for u in self.users.values()],
            "products": [p.to_dict() for p in self.products],
            "orders": self.orders,
        }
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except OSError as error:
            print(f"Не удалось сохранить данные: {error}")

    def next_order_id(self):
        return max((o["id"] for o in self.orders), default=0) + 1

    def show_menu(self):
        print("\nМеню:")
        for i, product in enumerate(self.products, start=1):
            print(f"{i}. {product.get_info()}")  # полиморфизм: у каждого типа свой вывод


# ============================================================
# Регистрация и вход
# ============================================================
def register(shop):
    print("\n-- Регистрация --")
    login = input_text("Логин (мин. 3 символа): ", 3)
    if login in shop.users:
        print("Ошибка: такой логин уже занят.")
        return
    password = input_text("Пароль (мин. 4 символа): ", 4)

    print("Роль: 1 — клиент, 2 — администратор")
    role = input_number("Выбор: ", int, 1, 2)
    password_hash = User.hash_password(password)

    if role == 2:
        code = input_text("Код администратора: ")
        if code != ADMIN_CODE:
            print("Неверный код. Регистрация отменена.")
            return
        shop.users[login] = Admin(login, password_hash)
    else:
        shop.users[login] = Client(login, password_hash)

    shop.save()
    print("Регистрация прошла успешно!")


def login(shop):
    print("\n-- Вход --")
    login_name = input_text("Логин: ")
    password = input_text("Пароль: ")
    user = shop.users.get(login_name)
    if user is not None and user.check_password(password):
        print(f"Добро пожаловать, {login_name}!")
        return user
    print("Неверный логин или пароль.")
    return None


# ============================================================
# Главный цикл
# ============================================================
def main():
    shop = Shop()
    while True:
        print("\n=== Пиццерия ===")
        print("1. Регистрация")
        print("2. Вход")
        print("3. Завершить программу")
        choice = input_number("Выбор: ", int, 1, 3)

        if choice == 1:
            register(shop)
        elif choice == 2:
            user = login(shop)
            if user is not None:
                user.run_menu(shop)  # полиморфизм: меню зависит от типа пользователя
        else:
            shop.save()
            print("Данные сохранены. До свидания!")
            break


if __name__ == "__main__":
    main()
