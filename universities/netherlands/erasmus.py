from lib import *
from models import CUniversity


class Erasmus(CUniversity):
    Name = 'Erasmus University Rotterdam'
    Vacancy_Link = "https://www.eur.nl/en/vacancies/overview?f[0]=organisation%3A3179&f[1]=type%3A2955"
    Country_Name = 'Netherlands'
    Rank_USN = 65
    Rank_QSN = 176
    Rank_USN_CS = 520
    Auto_Soup = True

    def _extract_jobs(self):
        job_block = self.soup_data.select_one('ul.list--view')
        return job_block.select('li.list__item--margin')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job.select_one('h3.teaser__title a').text)
            link = job.select_one('h3.teaser__title a').attrs['href']
            end_at = read_date(clean_text(job.select('li.list__item--meta')[1].text), '%A %d %b %Y')
            start_at = read_date(clean_text(job.select('li.list__item--meta')[0].text), '%A %d %b %Y')
            self.save_position(link, title, end_at, start_at)
