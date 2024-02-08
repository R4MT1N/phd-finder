from typing import List
from lib import *


class Twente(University):
    Name = 'University of Twente'
    Vacancy_Link = "https://utwentecareers.nl/en/vacancies/?type=WP&category=PR&page=1&faculty=EEMCS"
    Country_Name = 'Netherlands'
    Rank_USN = 400
    Rank_QSN = 210
    Rank_USN_CS = 186
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('ul.vacancies__results__list')

    def _extract_jobs(self):
        return self.soup_data.select('ul.vacancies__results__list > li')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job.select_one('b.vacancies__results__vacancy__title').text)
            link = job.select_one('a.vacancies__results__vacancy').attrs['href']
            end_at = read_date(clean_text(job.select('span.vacancies__results__vacancy__date')[1].find(text=True, recursive=False)), '%d %b %Y')
            start_at = read_date(clean_text(job.select('span.vacancies__results__vacancy__date')[0].find(text=True, recursive=False)), '%d %b %Y')
            self.add_position(link, title, end_at, start_at)
