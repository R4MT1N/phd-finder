from typing import List
from lib import *


class Utrecht(University):
    Name = 'Utrecht University'
    Vacancy_Link = 'https://www.uu.nl/en/organisation/working-at-utrecht-university/jobs'
    Country_Name = 'Netherlands'
    Rank_USN = 44
    Rank_QSN = 107
    Rank_USN_CS = 230
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('div.item-list ul.overview-list')

    def _extract_jobs(self):
        return self.soup_data.select('div.item-list ul.overview-list > li')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            level = clean_text(job.select_one('div.list-item__main div.position').text)
            dept = clean_text(job.select('div.list-item__bottom dl.meta dd.meta__content')[0].text)

            if level != 'PhD' or dept != 'Department of Information and Computing Sciences':
                continue

            title = clean_text(job.select_one('h3.list-item__title > a').text)
            link = join_urls(self.Vacancy_Link, job.select_one('h3.list-item__title > a').attrs['href'])
            expire_at = read_date(job.select('div.list-item__bottom dl.meta dd.meta__content')[1].text, '%d %B %Y')
            self.add_position(link, title, expire_at)
