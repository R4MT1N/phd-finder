from lib import *
from models import CUniversity

class Linkoping(CUniversity):
    Name = 'Linkoping University'
    Vacancy_Link = 'https://liu.se/en/work-at-liu/vacancies'
    Country_Name = 'Sweden'
    Rank_USN = 330
    Rank_QSN = 268
    Rank_USN_CS = 247
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('#jobListingsTable')

    def _extract_jobs(self):
        return self.soup_data.select('#jobListingsTable tbody tr')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            dept = clean_text(row.select_one('td:nth-child(6)').text)
            job_type = clean_text(row.select_one('td:nth-child(8)').text)

            if 'Department of Computer and Information Science' not in dept or job_type != 'PhD students':
                continue

            title = clean_text(row.select_one('td:nth-child(1)').text)
            link = row.select_one('td:nth-child(9)').text
            expire_at = read_date(clean_text(row.select_one('td:nth-child(2)').text), "%Y-%m-%d")
            self.save_position(link, title, expire_at)
