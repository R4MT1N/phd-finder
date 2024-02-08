from typing import List
from lib import *

class Lund(University):
    Name = 'Lund University'
    Vacancy_Link = 'https://www.lunduniversity.lu.se/vacancies'
    Country_Name = 'Sweden'
    Rank_USN = 112
    Rank_QSN = 85
    Rank_USN_CS = 328
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('table.vacancies-list__table')

    def _extract_jobs(self):
        return self.soup_data.select('table.vacancies-list__table tbody tr')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            if row.attrs['data-job-category'] != 'D' or row.attrs['data-job-department'] != 'faculty_of_science':
                continue

            title = row.attrs['data-job-title']
            link = row.select_one('td h2 a').attrs['href']
            expire_at = read_date(row.attrs['data-job-ends'], "%Y-%m-%d")
            published_at = read_date(row.attrs['data-job-published'], "%Y-%m-%d")
            self.add_position(link, title, expire_at, published_at)
