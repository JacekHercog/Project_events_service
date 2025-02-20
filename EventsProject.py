"""
1. Klasa Wydarzenie posiada pola składowe opisujące nazwę wydarzenia (str) oraz datę wydarzenia (str).
Przygotuj plik tekstowy, w którym umieścisz w osobnych wierszach informacje o nazwie wydarzenia, a po 
średniku o dacie wydarzenia. Następnie pobierz z pliku wydarzenia do listy i uporządkuj je według daty 
wystąpienia od najwcześniejszego do najpóźniejszego. Wynik sortowania zapisz do nowego pliku tekstowego 
o dowolnej nazwie. Dodatkowo zwróć informację na temat daty, dla której wystąpiło najwięcej wydarzeń.
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, Self, override
from datetime import datetime
import re
from collections import Counter

# -------------------------------------------------------------------------
# 1. Data loading
# -------------------------------------------------------------------------

class FileRead(ABC):

    @abstractmethod
    def read(cls, file_name: str) -> list[str]:
        pass

@dataclass
class TextFileReader(FileRead):

    @override
    def read(cls, file_name: str) -> list[str]:
        with open(file_name, 'r', encoding='UTF-8') as f:
            return [line.strip() for line in f.readlines()]

# -------------------------------------------------------------------------
# 2. Data writing
# -------------------------------------------------------------------------

class FileWrite(ABC):

    @abstractmethod
    def write(cls, file_name: str, data: list[str]) -> None:
        pass

@dataclass
class TextFileWriter(FileWrite):

    @override
    def write(cls, file_name: str, data: list[str]) -> None:
        with open(file_name, 'w', encoding='UTF-8') as f:
            f.writelines(line + '\n' for line in data)

# -------------------------------------------------------------------------
# 3. Validation
# -------------------------------------------------------------------------

class Validator(ABC):
    @abstractmethod    
    def validate(self, line_str: str) -> tuple[bool, dict[str, Any]]:
        pass

@dataclass
class EventValidator(Validator):
    event_name_regex: str
    date_format: str
    separator: str = ';'
    allow_past_dates: bool = False

    @override
    def validate(self, line_str: str) -> tuple[bool, dict[str, Any]]:
        errors: dict[str, Any] = {}

        parts = line_str.split(self.separator)
        if len(parts) != 2:
            errors['format'] = [f'Invalid format, expected "event_name{self.separator}date"']
        else:
            event_name, date_str = parts[0].strip(), parts[1].strip()

            # Validation of event_name
            if not event_name:
                errors['event_name'] = ['Empty event name']
            elif not re.match(self.event_name_regex, event_name):
                errors['event_name'] = [f'"{event_name}" does not match regex: {self.event_name_regex}']
            
            # Validation of date
            if not date_str:
                errors['date'] = ['Empty date']
            else:
                try:
                    event_date = datetime.strptime(date_str, self.date_format)
                    if not self.allow_past_dates and event_date < datetime.now():
                        errors['date'] = [f'Date {date_str} is in the past']
                except ValueError:
                    errors['date'] = [f'"{date_str}" not in the format: {self.date_format}']

        return len(errors) == 0, errors

# -------------------------------------------------------------------------
# 4. Conversion
# -------------------------------------------------------------------------   

@dataclass
class Event:
    event_name: str
    date: datetime

    def __str__(self) -> str:
        return f'Event(event_name: {self.event_name}, date: {self.date})'

    def __repr__(self) -> str:
        return f'REPR -  {str(self.__str__())}'

    @classmethod
    def from_str(cls, data: str, date_format: str, separator: str = ';') -> Self:
        event_name, date_str = data.split(separator)
        date = datetime.strptime(date_str, date_format)
        return cls(event_name, date)

# -------------------------------------------------------------------------
# 5. Events collection loading
# -------------------------------------------------------------------------

@dataclass
class EventsFileReader:
    read_file: FileRead
    event_validator: EventValidator
    stop_loading_if_error: bool = True

    def get_events(self, file_name) -> list[Event]:
        event_data = self.read_file.read(file_name)
        events = []

        for event in event_data:
            is_valid, errors = self.event_validator.validate(event)
            if is_valid:
                events.append(Event.from_str(event, self.event_validator.date_format))
            elif self.stop_loading_if_error:
                raise ValueError(f'Validation error: {errors}')
        
        return sorted(events, key=lambda event: event.date)

# -------------------------------------------------------------------------
# 6. Event service
# -------------------------------------------------------------------------

@dataclass
class EventService:
    events: list[Event]
    file_writer: FileWrite

    def save_sorted_events(self, file_name: str, date_format: str) -> None:
        sorted_data = [f'{event.event_name};{event.date.strftime(date_format)}' for event in self.events]
        self.file_writer.write(file_name, sorted_data)

    def get_most_common_date(self, date_format: str) -> tuple[list[str], int]:

        if not self.events:
            raise ValueError('Events are not found ')
            
        date_counts = Counter(event.date.strftime(date_format) for event in self.events)
        max_count = max(date_counts.values(), default=0)

        most_common_dates = [date for date, count in date_counts.items() if count == max_count]
        return most_common_dates, max_count

# -------------------------------------------------------------------------
# 7. Main function
# -------------------------------------------------------------------------

def main() -> None:
    FILE_NAME = 'events.txt'
    OUTPUT_FILE = 'sorted_events.txt'
    DATE_FORMAT = '%d-%m-%Y'

    validator = EventValidator(
        event_name_regex=r"^[A-Za-z0-9 ĄąĆćĘęŁłŃńÓóŚśŹźŻż,.?!-]+$",
        date_format=DATE_FORMAT,
        allow_past_dates=False
    )

    read_file = TextFileReader()
    event_loader = EventsFileReader(read_file, validator)
    try:
        events = event_loader.get_events(FILE_NAME)
    except ValueError as e:
        print(f"Error loading events: {e}")
        return

    file_writer = TextFileWriter()
    event_service = EventService(events, file_writer)
    event_service.save_sorted_events(OUTPUT_FILE, DATE_FORMAT)

    most_common_date = event_service.get_most_common_date(DATE_FORMAT)
    print(f'Most common date: {most_common_date}')

if __name__ == '__main__':
    main()

