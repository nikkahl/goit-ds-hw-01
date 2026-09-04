import os
import pickle
import re
from collections import UserDict
from datetime import datetime, timedelta
from dataclasses import dataclass, field, InitVar
from typing import List, Optional


@dataclass
class Field:
    value: str

    def __str__(self):
        return str(self.value)


@dataclass
class Name(Field):
    pass


@dataclass
class Phone(Field):
    def __post_init__(self):
        if not isinstance(self.value, str) or len(self.value) != 10 or not self.value.isdigit():
            raise ValueError("Phone number must contain exactly 10 digits")


@dataclass
class Email(Field):
    EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    def __post_init__(self):
        if not isinstance(self.value, str) or not re.match(self.EMAIL_PATTERN, self.value):
            raise ValueError("Invalid email format")


@dataclass
class Birthday(Field):
    date_obj: datetime.date = field(init=False)

    def __post_init__(self):
        try:
            self.date_obj = datetime.strptime(self.value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format, use DD.MM.YYYY")


@dataclass
class Record:
    name_val: InitVar[str]
    name: Name = field(init=False)
    phones: List[Phone] = field(default_factory=list)
    birthday: Optional[Birthday] = None
    email: Optional[Email] = None

    def __post_init__(self, name_val):
        self.name = Name(name_val)

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        phone_obj = self.find_phone(phone_number)
        if phone_obj:
            self.phones.remove(phone_obj)
        else:
            raise ValueError(f"Phone {phone_number} not found in the record")

    def edit_phone(self, old_phone, new_phone):
        phone_obj = self.find_phone(old_phone)
        if not phone_obj:
            raise ValueError(f"Old phone {old_phone} not found in the record")

        index = self.phones.index(phone_obj)
        self.phones[index] = Phone(new_phone)

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, birthday_str):
        self.birthday = Birthday(birthday_str)

    def add_email(self, email_str):
        self.email = Email(email_str)

    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones) if self.phones else "no phones"
        birthday_str = self.birthday.value if self.birthday else "not set"
        email_str = self.email.value if self.email else "not set"
        return (f"Contact name: {self.name.value}, phones: {phones_str}, "
                f"birthday: {birthday_str}, email: {email_str}")


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming = []
        for record in self.data.values():
            if not record.birthday:
                continue

            b_date_this_year = record.birthday.date_obj.replace(year=today.year)

            if b_date_this_year < today:
                b_date_this_year = b_date_this_year.replace(year=today.year + 1)
            delta_days = (b_date_this_year - today).days

            if 0 <= delta_days <= 7:
                if b_date_this_year.weekday() == 5:
                    b_date_this_year += timedelta(days=2)
                elif b_date_this_year.weekday() == 6:
                    b_date_this_year += timedelta(days=1)

                upcoming.append({
                    "name": record.name.value,
                    "birthday": b_date_this_year.strftime("%d.%m.%Y")
                })

        return upcoming


DEFAULT_DATA_FILE = os.environ.get("DATA_FILE", "addressbook.pkl")


def save_data(book, filename=DEFAULT_DATA_FILE):
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename=DEFAULT_DATA_FILE):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Not enough arguments provided"
        except KeyError:
            return "Contact not found"
    return inner


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Please provide name and phone")
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated"

    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added"

    record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise ValueError("Please provide name, old phone, and new phone")
    name, old_phone, new_phone = args
    record = book.find(name)

    if record is None:
        raise KeyError

    record.edit_phone(old_phone, new_phone)
    return "Contact updated"


@input_error
def show_phone(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Please provide a name")
    name = args[0]
    record = book.find(name)

    if record is None:
        raise KeyError

    return f"{name}'s phones: {'; '.join(p.value for p in record.phones)}"


@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "Address book is empty"
    return '\n'.join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Please provide name and birthday (DD.MM.YYYY)")
    name, birthday = args
    record = book.find(name)

    if record is None:
        raise KeyError

    record.add_birthday(birthday)
    return "Birthday added"


@input_error
def show_birthday(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Please provide a name")
    name = args[0]
    record = book.find(name)

    if record is None:
        raise KeyError

    if record.birthday:
        return f"{name}'s birthday is {record.birthday.value}"
    else:
        return f"{name} does not have a birthday set"


@input_error
def add_email(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Please provide name and email")
    name, email = args
    record = book.find(name)

    if record is None:
        raise KeyError

    record.add_email(email)
    return "Email added"


@input_error
def show_email(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Please provide a name")
    name = args[0]
    record = book.find(name)

    if record is None:
        raise KeyError

    if record.email:
        return f"{name}'s email is {record.email.value}"
    else:
        return f"{name} does not have an email set"


@input_error
def birthdays(book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next 7 days"

    result = "Upcoming birthdays:\n"
    for item in upcoming:
        result += f"- {item['name']}: {item['birthday']}\n"
    return result.strip()


@input_error
def delete_contact(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Please provide a name")
    name = args[0]
    book.delete(name)
    return f"Contact {name} deleted"


def print_help():
    print(
        "Available commands:\n"
        "  hello                                 - greet the bot\n"
        "  add <name> <phone>                     - add contact or phone to existing one\n"
        "  change <name> <old_phone> <new_phone>  - change a phone number\n"
        "  phone <name>                           - show phones of a contact\n"
        "  all                                    - show all contacts\n"
        "  add-birthday <name> <DD.MM.YYYY>        - add birthday to contact\n"
        "  show-birthday <name>                   - show birthday of a contact\n"
        "  add-email <name> <email>               - add email to contact\n"
        "  show-email <name>                      - show email of a contact\n"
        "  birthdays                              - show birthdays in next 7 days\n"
        "  delete <name>                          - delete a contact\n"
        "  help                                   - show this message\n"
        "  close / exit                           - save and exit"
    )


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    print("Type 'help' to see the list of available commands.")

    while True:
        user_input = input("Enter a command: ")
        if not user_input.strip():
            continue

        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "help":
            print_help()

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "add-email":
            print(add_email(args, book))

        elif command == "show-email":
            print(show_email(args, book))

        elif command == "birthdays":
            print(birthdays(book))

        elif command == "delete":
            print(delete_contact(args, book))

        else:
            print("Invalid command. Type 'help' to see available commands.")


if __name__ == "__main__":
    main()