from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import requests
from bs4 import BeautifulSoup

from models import University as MUniversity, Position as MPosition, Country as MCountry


class Position:
    def __init__(self, university, link, title, end_date=None, start_date=None):
        self.university: University = university
        self.link = link
        self.title = title
        self.end_date = end_date
        self.start_date = start_date

    def save_if_new(self) -> bool:
        model, is_created = MPosition.get_or_create(link=self.link, end_date=self.end_date,
                                                    university=self.university.db_model,
                                                    defaults={'start_date': self.start_date, 'title': self.title})
        return is_created

    def __str__(self):
        return f"{self.university.Name}: {self.title}, expires at {self.end_date}, more info in {self.link}"


class University(ABC):
    Country_Name = None
    Auto_Soup = False
    Name = None
    Rank_USN = None
    Rank_USN_CS = None
    Rank_QSN = None
    Vacancy_Link = None

    def __init__(self):
        self.soup_data: BeautifulSoup = self._fetch_and_render_link(self.Vacancy_Link) if self.Auto_Soup else None
        self.json_data = None
        self.total_new_positions = 0

        MCountry.get_or_create(name=self.Country_Name)
        self.db_model = self.create_db_record()
        self._check_source_validity()

    def create_db_record(self):
        return MUniversity.get_or_create(name=self.Name,
                                         defaults={'usn_rank': self.Rank_USN,
                                                   'usn_cs_rank': self.Rank_USN_CS,
                                                   'qsn_rank': self.Rank_QSN,
                                                   'country_id': self.Country_Name,
                                                   'vacancy_link': self.Vacancy_Link})[0]

    @staticmethod
    def _fetch_and_render_link(link=None) -> BeautifulSoup:
        content = requests.get(link).content
        return BeautifulSoup(content, 'html.parser')

    @abstractmethod
    def _extract_job_block(self):
        pass

    @abstractmethod
    def _extract_jobs(self):
        pass

    @abstractmethod
    def fetch_positions(self) -> List[Position]:
        pass

    def _check_job_availability(self):
        if len(self._extract_jobs()) == 0:
            print(f'No position were found in "{self.Name}".')

    def _check_source_validity(self):
        try:
            assert self._extract_job_block() is not None
        except AssertionError:
            raise Exception(f'Page validation failed for "{self.Name}".')

    def save_position(self, link, title, expire_date=None, start_date=None):
        if Position(self, link, title, expire_date, start_date).save_if_new():
            self.total_new_positions += 1