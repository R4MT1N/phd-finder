from typing import List
from lib import *


class Maastricht(University):
    Name = 'Maastricht University'
    Vacancy_Link = "https://vacancies.maastrichtuniversity.nl/search/?createNewAlert=false&q=&optionsFacetsDD_facility=Faculty+of+Science+%26+Engineering&optionsFacetsDD_dept=Academic&optionsFacetsDD_city=&optionsFacetsDD_customfield1=&optionsFacetsDD_customfield2="
    Country_Name = 'Netherlands'
    Rank_USN = 186
    Rank_QSN = 256
    Rank_USN_CS = 562
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('#searchresults')

    def _extract_jobs(self):
        return self.soup_data.select('#searchresults tbody tr')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job.select_one('td.colTitle a').text)
            link = join_urls(self.Vacancy_Link, job.select_one('td.colTitle a').attrs['href'])
            end_at = read_date(clean_text(job.select_one('span.jobShifttype').text), '%d-%m-%Y')
            self.add_position(link, title, end_at)
