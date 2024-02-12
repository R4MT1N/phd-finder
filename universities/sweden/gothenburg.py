from typing import List
from lib import *


class Gothenburg(University):
    Name = 'University of Gothenburg'
    Vacancy_Link = 'https://www.gu.se/en/work-at-the-university-of-gothenburg/vacancies'
    Country_Name = 'Sweden'
    Rank_USN = 146
    Rank_QSN = 187
    Rank_USN_CS = 584
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('table.table--vacancies')

    def _extract_jobs(self):
        return self.soup_data.select('table.table--vacancies tbody tr')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            title = clean_text(row.select_one('td:nth-child(1) a').text)

            if (not any(term.lower() in title.lower() for term in ['PhD', 'Doctorate', 'Doctoral'])) or 'postdoctoral' in title.lower():
                continue

            link = row.select_one('td:nth-child(1) a').attrs['href']
            expire_at = read_date(clean_text(row.select_one('td:nth-child(4) div:nth-child(2)').text), "%Y-%m-%d")
            self.save_position(link, title, expire_at)
