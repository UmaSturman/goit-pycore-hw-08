import pickle
from collections import UserDict
from datetime import datetime, date, timedelta


# ── Поля ──────────────────────────────────────────────────────────────────────

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value or not value.strip():
            raise ValueError("Name cannot be empty.")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError(f"Phone '{value}' must be exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    FORMAT = "%d.%m.%Y"

    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, self.FORMAT).date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime(self.FORMAT)


# ── Record ────────────────────────────────────────────────────────────────────

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        found = self.find_phone(phone)
        if not found:
            raise ValueError(f"Phone {phone} not found.")
        self.phones.remove(found)

    def edit_phone(self, old, new):
        found = self.find_phone(old)
        if not found:
            raise ValueError(f"Phone {old} not found.")
        self.phones[self.phones.index(found)] = Phone(new)

    def find_phone(self, phone):
        return next((p for p in self.phones if p.value == phone), None)

    def add_birthday(self, value):
        self.birthday = Birthday(value)

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones) or "no phones"
        bday = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{bday}"


# ── AddressBook ───────────────────────────────────────────────────────────────

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name not in self.data:
            raise KeyError(f"Record '{name}' not found.")
        del self.data[name]

    def get_upcoming_birthdays(self, days=7):
        today = date.today()
        result = []
        for record in self.data.values():
            if not record.birthday:
                continue
            bday = record.birthday.value.replace(year=today.year)
            if bday < today:
                bday = bday.replace(year=today.year + 1)
            if 0 <= (bday - today).days <= days:
                shift = {5: 2, 6: 1}.get(bday.weekday(), 0)
                congrat = bday + timedelta(days=shift)
                result.append({"name": record.name.value,
                                "congratulation_date": congrat.strftime("%d.%m.%Y")})
        return result


# ── Збереження та завантаження (pickle) ───────────────────────────────────────

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено


# ── Декоратор ─────────────────────────────────────────────────────────────────

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (KeyError, ValueError) as e:
            return str(e)
        except IndexError:
            return "Enter the argument for the command."
    return inner


# ── Обробники команд ──────────────────────────────────────────────────────────

@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        msg = "Contact added."
    else:
        msg = "Contact updated."
    record.add_phone(phone)
    return msg

@input_error
def change_contact(args, book):
    name, old, new = args
    record = book.find(name)
    if not record:
        raise KeyError(f"Contact '{name}' not found.")
    record.edit_phone(old, new)
    return "Contact updated."

@input_error
def show_phone(args, book):
    record = book.find(args[0])
    if not record:
        raise KeyError(f"Contact '{args[0]}' not found.")
    return str(record)

@input_error
def add_birthday(args, book):
    name, bday = args
    record = book.find(name)
    if not record:
        raise KeyError(f"Contact '{name}' not found.")
    record.add_birthday(bday)
    return f"Birthday {bday} added to {name}."

@input_error
def show_birthday(args, book):
    record = book.find(args[0])
    if not record:
        raise KeyError(f"Contact '{args[0]}' not found.")
    return f"{args[0]}'s birthday: {record.birthday}" if record.birthday else f"{args[0]} has no birthday set."

@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    return "\n".join(f"{u['name']}: {u['congratulation_date']}" for u in upcoming)

def show_all(book):
    return "\n".join(str(r) for r in book.data.values()) or "No contacts."


# ── CLI ───────────────────────────────────────────────────────────────────────

COMMANDS = {
    "add":          add_contact,
    "change":       change_contact,
    "phone":        show_phone,
    "add-birthday": add_birthday,
    "show-birthday":show_birthday,
    "birthdays":    birthdays,
}

def parse_input(user_input):
    parts = user_input.strip().split()
    return (parts[0].lower(), parts[1:]) if parts else ("", [])

def main():
    book = load_data()  # Завантаження даних при запуску
    print("Welcome to the assistant bot!")
    while True:
        command, args = parse_input(input("Enter a command: "))
        if command in ("exit", "close"):
            save_data(book)  # Збереження даних перед виходом
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "all":
            print(show_all(book))
        elif command in COMMANDS:
            print(COMMANDS[command](args, book))
        elif command:
            print("Invalid command.")

if __name__ == "__main__":
    main()