from typing import Any, Self, override, Callable, DefaultDict
from enum import Enum
from abc import ABC, abstractmethod
import json
from dataclasses import dataclass
import re
from collections import Counter, defaultdict


import logging

from numpy import average
"""
ZARZĄDZANIE KOLEKCJĄ SAMOCHODÓW
Zaimplementuj klasę Car. Klasa posiada pola składowe model, price, color, mileage oraz kolekcję napisów components reprezentująca 
wyposażenie samochodu. Dla klasy przygotuj podstawowe metody ułatwiające korzystanie z klasy. Przygotuj również logikę, która 
pozwoli walidować pola składowe klasy. Model musi składać się tylko i wyłącznie z dużych liter oraz białych znaków. 
Kolor przyjmuje wartości typu wyliczeniowego Color (przygotuj przykładowe wartości dla typu wyliczeniowego). 
Pole milleage oraz price mogą przyjmować wartości tylko nieujemne. Kolekcja components może składać się z napisów, które zawierają 
tylko i wyłącznie duże litery i białe znaki. Możesz zastosować wzorzec projektowy builder.
Następnie zaimplementuj klasę Cars, której polem składowym jest kolekcja obiektów klasy Car o nazwie cars. Dla klasy przygotuj 
konstruktor, który jako argument przyjmuje nazwę pliku w formacie JSON przechowującego dane o przykładowych samochodach. 
Przykładowa postać pliku została przedstawiona poniżej. Dane z pliku należy pobrać do kolekcji znajdującej się w klasie Cars.
"""

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)-8s] - %(asctime)s - %(message)s'
)

class CarColor(Enum):
    GREEN = 'Green'
    BLACK = 'Black'
    WHITE = 'White'
    RED = 'Red'

# -------------------------------------------------------------------------
# 1. Data loading
# -------------------------------------------------------------------------
class FileRead(ABC):

    @abstractmethod
    def read(self, file_name: str, key: str) -> list[dict[str, Any]]:
        pass

class JsonFileReader(FileRead):
    
    @override
    def read(self, file_name: str, key: str) -> list[dict[str, Any]]:
        with open(file_name, 'r', encoding='UTF-8') as json_file:
            data_from_file = json.load(json_file)
            if key not in data_from_file:
                raise AttributeError(f'Not found key {key} in file : {file_name}')

            return data_from_file[key]

# -------------------------------------------------------------------------
# 2. Validation
# -------------------------------------------------------------------------
class Validator(ABC):

    @abstractmethod
    def validate(self, data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        pass


@dataclass
class CarValidator(Validator):
    model_regex: str = r'^[A-Z\s]+$'
    collection_regex: str = r'^[A-Z\s]+$'

    @override
    def validate(self, data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        errors: dict[str, Any] = {}
        
        if "model" not in data:
            errors |= {'model': ['not found']}
        elif not re.match(self.model_regex, data["model"]):
            errors |= {'model': [f'{data["model"]} does not match regex: {self.model_regex}']}

        if "price" not in data:
            errors |= {'price': [f'not found for model: {data["model"]}']}
        elif not isinstance(data['price'], int):
            errors |= {f'price': [f'price for model {data["model"]} is not a number: "{data["price"]}"']}
        elif int(data["price"]) <= 0:
            errors |= {'price': [f'price for model {data["model"]} must be greater than 0']}

        if "color" not in data:
            errors |= {'color': [f'not found for model: {data["model"]}']}
        elif data["color"] not in {color.name for color in CarColor}:
            errors |= {'color': [f'not found color: {data["color"]} for model: {data["model"]}']}

        if "mileage" not in data:
            errors |= {'mileage': [f'not found for model: {data["model"]}']}
        elif not isinstance(data['mileage'], int):
            errors |= {f'mileage': [f'mileage for model {data["model"]} is not a number: "{data["price"]}"']}
        elif int(data["mileage"]) <= 0:
            errors |= {'mileage': [f'mileage for model {data["model"]} must be greater than 0']}

        if "components" not in data:
            errors['components'] = [f'not found for model: {data["model"]}']
        elif not all(isinstance(comp, str) and re.match(self.collection_regex, comp) for comp in data["components"]):
            errors['components'] = [f'Invalid components for model {data["model"]}: {data["components"]}'\
                ' does not match to regex {self.model_regex}']

        return len(errors) == 0 , errors

# -------------------------------------------------------------------------
# 3. Conversion
# -------------------------------------------------------------------------

@dataclass
class Car:
    model: str
    price: int
    color: CarColor
    mileage: int
    components: list[str]

    def __str__(self) -> str:
        return f'Car(model: {self.model}, price: {self.price}, color: {self.color.name}, mileage: {self.mileage})'
    
    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            model=data["model"],
            price=data["price"],
            color=CarColor[data["color"]],  
            mileage=data["mileage"],
            components=data["components"]
        )

# -------------------------------------------------------------------------
# 4. Cars collection loading
# -------------------------------------------------------------------------
@dataclass
class CarsFileReader:
    car_validator: CarValidator
    stop_loading_if_error: bool = True

    def get_cars(self, file_name: str, key: str) -> list[Car]:
        json_file_read = JsonFileReader()
        cars_data = json_file_read.read(file_name=file_name, key=key)
        cars = []

        for car in cars_data:
            is_valid, errors = self.car_validator.validate(car)

            if not is_valid:
                for field_name, error in errors.items():
                    logging.warning(f'{field_name} - {error}')
            
                if self.stop_loading_if_error:
                    raise ValueError(f'Validation error: {errors}')

            if is_valid:
                cars.append(Car.from_dict(car))

        return cars

# -------------------------------------------------------------------------
# 5. Cars service
# -------------------------------------------------------------------------
@dataclass
class CarsService:
    cars: list[Car]

# Metoda, która zwraca nową kolekcję elementów Car posortowaną według podanego jako argument metody kryterium. 
# Metoda powinna mieć możliwość sortowania po nazwie modelu, kolorze, cenie oraz przebiegu. Dodatkowo należy określić 
# czy sortowanie ma odbywać się malejąco czy rosnąco.
    def get_sorted_cars(self, fn_sorted: Callable[[Car], Any], descending: bool = False) -> list[Car]:
        return sorted(self.cars, key=fn_sorted, reverse=descending)


# Metoda zwraca kolekcję elementów typu Car, które posiadają przebieg o wartości większej niż wartość podana jako 
# argument metody.
    def get_cars_mileage_than(self, mileage:int) -> list[Car]:
        if not isinstance(mileage, int) or mileage < 0:
            raise ValueError(f'Incorrect value mileage: "{mileage}" - should be integer greater or equal than 0')
        return [car for car in self.cars if car.mileage > mileage]
        
# Metoda zwraca mapę, której kluczem jest kolor, natomiast wartością ilość samochodów, które posiadają taki kolor. 
# Mapa powinna być posortowana malejąco po wartościach.
    def get_count_cars_by_color(self, descending: bool = True) -> dict[str, int]:
        count_cars_with_colors = Counter(car.color.name for car in self.cars)
        # count_cars_with_colors = Counter()
        # for car in self.cars:
        #     count_cars_with_colors[car.color.name] += 1    
        return dict(sorted(count_cars_with_colors.items(), key=lambda item: item[1], reverse=descending))

# Metoda zwraca mapę, której kluczem jest nazwa modelu samochodu, natomiast wartością obiekt klasy Car, który reprezentuje 
# najdroższy samochód o tej nazwie modelu. Mapa powinna być posortowana kluczami malejąco.
    def get_model_cars_most_expensive(self, descending: bool = True ) -> dict[str,list[Car]]:
        model_cars_most_expensive = defaultdict(list)
        for car in self.cars:
            if not model_cars_most_expensive[car.model]:
                model_cars_most_expensive[car.model].append(car)
            else:
                max_price = model_cars_most_expensive[car.model][0].price
                if  car.price > max_price:
                    model_cars_most_expensive[car.model] = [car]
                elif car.price == max_price:
                    model_cars_most_expensive[car.model].append(car)
        return dict(sorted(model_cars_most_expensive.items(), key=lambda item:item[0], reverse=descending))

# Metoda wypisuje statystykę samochodów w zestawieniu. W statystyce powinny znajdować się wartość średnia, wartość najmniejsza, 
# wartość największa dla pól opisujących cenę oraz przebieg samochodów.
    def get_statistic_price_mileage(self) -> dict[str, dict[str, float]]:
        if not self.cars:
            return {'price': {'avg': 0, 'min': 0, 'max': 0}, 'mileage': {'avg': 0, 'min': 0, 'max': 0}}

        prices = [car.price for car in self.cars]
        milleages = [car.mileage for car in self.cars]
        return {
            'price': {
                'avg': sum(prices)/len(prices),
                'min': min(prices),
                'max': max(prices) 
            },
            'mileage': {
                'avg': sum(milleages)/len(milleages),
                'min': min(milleages),
                'max': max(milleages)  
            }
        }

# Metoda zwraca samochód, którego cena jest największa. W przypadku kiedy więcej niż jeden samochód posiada największą cenę 
# należy zwrócić kolekcję tych samochodów.
    def get_cars_most_expensive(self) -> list[Car]:
        max_price = max(car.price for car in self.cars)
        return [car for car in self.cars if car.price == max_price]

# Metoda zwraca kolekcję samochodów, w której każdy samochód posiada posortowaną alfabetycznie kolekcję komponentów.
    def get_sorted_collection(self, descending:bool = False) -> list[Car]:
        for car in self.cars:
            car.components.sort(reverse=descending)
        return self.cars

# Metoda zwraca mapę, której kluczem jest nazwa komponentu, natomiast wartością jest kolekcja samochodów, 
# które posiadają ten komponent. Pary w mapie powinny być posortowane malejąco po ilości elementów w kolekcji reprezentującej 
# wartość pary.
    def get_componets_with_car(self, descending: bool = False) -> dict[str, list[Car]]:
        components_with_cars = defaultdict(list)

    # Zbieramy samochody dla każdego komponentu
        for car in self.cars:
            for component in car.components:
                components_with_cars[component].append(car)

    # Sortujemy mapę po liczbie samochodów dla każdego komponentu
        sorted_components = dict(
            sorted(components_with_cars.items(), key=lambda item: len(item[1]), reverse=descending)
        )

    # Zwracamy posortowaną mapę komponentów
        return sorted_components

# Metoda zwraca kolekcję samochodów, których cena znajduje się w przedziale cenowym <a, b>. Wartości a oraz b przekazywane są
# jako argument metody. Kolekcja powinna być posortowana alfabetycznie według nazw samochodów.
    def get_cars_price_between(self, price_from: int, price_to: int) -> list[Car]:
        if price_from > price_to:
            raise ValueError('Invalid price_from and price_to')

        return sorted(
            [car for car in self.cars if price_from <= car.price <= price_to], 
            key=lambda car: car.model  
        )
   

def main() -> None:
    FILE_NAME = 'cars.json'
    MODEL_REGEX: str = r'^[A-Z\s]+$'
    COLLECTION_REGEX: str = r'^[A-Z\s]+$'

    validator=  CarValidator(
        model_regex= MODEL_REGEX,
        collection_regex=COLLECTION_REGEX
    )

    cars_reader = CarsFileReader(car_validator=validator, stop_loading_if_error=False)
    cars = cars_reader.get_cars(file_name=FILE_NAME, key='cars')
   
    cars_service = CarsService(cars=cars)

    print('-----cars sorted by price-------')
    cars_sorted_price = cars_service.get_sorted_cars(fn_sorted=lambda car:car.price,descending=True)
    for car in cars_sorted_price:
        print(car)
    
    print('-----cars sorted by color-------')
    cars_sorted_by_color = cars_service.get_sorted_cars(fn_sorted=lambda car: car.color.name)
    for car in cars_sorted_by_color:
        print(car) 

    print('-----cars mileage grater than-------')
    MILEAGE = 2400
    cars_mileage_grater_than = cars_service.get_cars_mileage_than(mileage=MILEAGE)
    for car in cars_mileage_grater_than:
        print(car) 
    
    print('-----cars counted by color-------')
    cars_counted_by_color = cars_service.get_count_cars_by_color()
    for car in cars_counted_by_color.items():
        print(car) 

    print('-----cars model most expensive-------')  
    model_cars_most_expensive = cars_service.get_model_cars_most_expensive()
    for car in model_cars_most_expensive.items():
        print(car)

    print('-----cars statistics (price/mileage-------')  
    cars_statistics = cars_service.get_statistic_price_mileage()
    for car in cars_statistics.items():
        print(car)

    print('-----cars most expansive-------')  
    cars_most_expansive = cars_service.get_cars_most_expensive()
    for car in cars_most_expansive:
        print(car)

    print('-----componets with cars-------')  
    components_car = cars_service.get_componets_with_car()
    for component, cars_list in components_car.items():
        print(f'{component}: {len(cars_list)} cars')
        for car in cars_list:
            print(f"  {car}")

    print('-----cars price betwwen-------')
    PRICE_MIN, PRICE_MAX = 100, 200
    cars_price_between = cars_service.get_cars_price_between(price_from=PRICE_MIN, price_to=PRICE_MAX)
    for car in cars_price_between:
        print(car)
    
    
    

if __name__ == '__main__':
    main()