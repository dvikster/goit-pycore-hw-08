import pickle
from collections import UserDict
import re
from datetime import datetime, timedelta

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if re.fullmatch(r'\d{10}', value):
            super().__init__(value)
        else:
            raise ValueError("Phone number must contain exactly 10 digits.")

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                self.phones.remove(phone)
                return f"Phone {phone_number} removed."
        return f"Phone {phone_number} not found."

    def edit_phone(self, old_phone, new_phone):
        for phone in self.phones:
            if phone.value == old_phone:
                phone.value = new_phone
                return f"Phone {old_phone} changed to {new_phone}."
        return f"Phone {old_phone} not found."

    def add_birthday(self, birthday_date):
        self.birthday = Birthday(birthday_date)

    def days_to_birthday(self):
        if not self.birthday:
            return None
        today = datetime.today().date()
        next_birthday = self.birthday.value.replace(year=today.year)
        if next_birthday < today:
            next_birthday = next_birthday.replace(year=today.year + 1)
        return (next_birthday - today).days

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        birthday = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{birthday}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record
        return f"Record for {record.name.value} added."

    def find(self, name):
        return self.data.get(name, "Contact not found.")

    def delete(self, name):
        if name in self.data:
            del self.data[name]
            return f"Record for {name} deleted."
        return "Contact not found."

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                days_until_birthday = record.days_to_birthday()
                if days_until_birthday is not None and 0 <= days_until_birthday <= 7:
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": record.birthday,
                        "congratulation_date": (today + timedelta(days=days_until_birthday)).strftime("%d.%m.%Y")
                    })
        return upcoming_birthdays

# Серіалізація та десеріалізація з pickle
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

# Декоратор для обробки помилок
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return str(e)
    return inner

# Функції обробки команд
def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        return "Please provide both name and phone number."

    name, phone = args[0], args[1]
    record = book.find(name)

    if record == "Contact not found.":
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    else:
        message = "Contact updated."

    if phone:
        record.add_phone(phone)

    return message

@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        return "Please provide both name and birthday date in the format DD.MM.YYYY."
    
    name, birthday = args[0], args[1]
    record = book.find(name)
    if record == "Contact not found.":
        return "Contact not found."

    if record.birthday:
        record.add_birthday(birthday)
        return f"Birthday for {name} updated."
    else:
        record.add_birthday(birthday)
        return f"Birthday for {name} added."

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record == "Contact not found.":
        return record
    return f"{name}'s birthday: {record.birthday}" if record.birthday else f"{name} has no birthday set."

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    return "\n".join(f"{item['name']} - {item['congratulation_date']}" for item in upcoming)

@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        return "Please provide name, old phone number, and new phone number."
    
    name, old_phone, new_phone = args[0], args[1], args[2]
    record = book.find(name)
    if record == "Contact not found.":
        return record
    return record.edit_phone(old_phone, new_phone)

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record == "Contact not found.":
        return record
    return f"{name}'s phones: {', '.join(p.value for p in record.phones)}"

@input_error
def show_all(args, book: AddressBook):
    return "\n".join(str(record) for record in book.data.values()) if book.data else "No contacts added yet"

# Головна функція бота
def main():
    book = load_data()  # Завантажуємо дані з файлу при запуску
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ").strip()
        if not user_input:
            print("Error: Please enter a command.")
            continue

        command, *args = parse_input(user_input)
        
        if command in ["close", "exit"]:
            save_data(book)  # Зберігаємо дані перед виходом
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(*args, book))
        elif command == "change":
            print(change_contact(*args, book))
        elif command == "phone":
            print(show_phone(*args, book))
        elif command == "all":
            print(show_all(*args, book))
        elif command == "add-birthday":
            print(add_birthday(*args, book))
        elif command == "show-birthday":
            print(show_birthday(*args, book))
        elif command == "birthdays":
            print(birthdays(*args, book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()

