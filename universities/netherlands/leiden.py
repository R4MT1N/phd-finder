from typing import List
from lib import *


class Leiden(University):
    Name = 'Leiden University'
    Vacancy_Link = 'https://www.universiteitleiden.nl/en/vacancies?pageNumber=1&functioncategory=phd-function&faculty=science&facultyinstitute=leiden-institute-of-advanced-computer-science'
    Country_Name = 'Netherlands'
    Rank_USN = 74
    Rank_QSN = 126
    Rank_USN_CS = 227
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('#content ul')

    def _extract_jobs(self):
        return self.soup_data.select('#content ul li')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job.select_one('a div strong').text)
            link = join_urls(self.Vacancy_Link, job.select_one('a').attrs['href'])
            pos_details = BeautifulSoup(get_request(link).content, 'html.parser')
            end_at = read_date(clean_text(pos_details.select('.facts dd')[-1].find(text=True)), '%d %B %Y')
            start_at = read_date(clean_text(pos_details.select('.facts dd')[-2].find(text=True)), '%d %B %Y')
            self.add_position(link, title, end_at, start_at)
