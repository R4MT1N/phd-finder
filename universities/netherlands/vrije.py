from lib import *
from models import CUniversity


class Vrije(CUniversity):
    Name = 'Vrije Universiteit Amsterdam'
    Vacancy_Link = "https://workingat.vu.nl/vacancies?o=0&n=10&of=18&f=653&of=35&f=36&of=38&f=42#vacancy-overview"
    Country_Name = 'Netherlands'
    Rank_USN = 802
    Rank_QSN = 207
    Rank_USN_CS = 247
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('ul.vacancy-list')

    def _extract_jobs(self):
        return self.soup_data.select('ul.vacancy-list > li')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job.select_one('div.vacancy-item-titles h3').text)
            link = job.select_one('a.vacancy-item').attrs['href']
            end_at = read_date(job.select_one('li.end-date div.date-metadata').attrs['data-utc'], '%Y-%m-%dT%H:%M:%S')
            self.save_position(link, title, end_at)
