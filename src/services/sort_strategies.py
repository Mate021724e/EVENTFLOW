from src.storage.interfaces import IEventSortStrategy


class SortByDateAscStrategy(IEventSortStrategy):
    def sort(self, events: list) -> list:
        return sorted(events, key=lambda e: e.start_dt)

    def get_name(self) -> str:
        return "Date ascending"


class SortByDateDescStrategy(IEventSortStrategy):
    def sort(self, events: list) -> list:
        return sorted(events, key=lambda e: e.start_dt, reverse=True)

    def get_name(self) -> str:
        return "Date descending"


class SortByPopularityStrategy(IEventSortStrategy):
    def sort(self, events: list) -> list:
        return sorted(events, key=lambda e: e.registered_count, reverse=True)

    def get_name(self) -> str:
        return "Popularity (most registered)"


class SortByPriceAscStrategy(IEventSortStrategy):
    def sort(self, events: list) -> list:
        return sorted(events, key=lambda e: e.price)

    def get_name(self) -> str:
        return "Price ascending"


class SortByPriceDescStrategy(IEventSortStrategy):
    def sort(self, events: list) -> list:
        return sorted(events, key=lambda e: e.price, reverse=True)

    def get_name(self) -> str:
        return "Price descending"


class SortByTitleStrategy(IEventSortStrategy):
    def sort(self, events: list) -> list:
        return sorted(events, key=lambda e: e.title.lower())

    def get_name(self) -> str:
        return "Title alphabetical"


class SortBySpotsLeftStrategy(IEventSortStrategy):
    def sort(self, events: list) -> list:
        return sorted(events, key=lambda e: e.spots_left(), reverse=True)

    def get_name(self) -> str:
        return "Spots left (most available)"
