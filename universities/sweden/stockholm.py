from lib import *
from models import CUniversity


class Stockholm(CUniversity):
    Name = 'Stockholm University'
    Vacancy_Link = 'https://web103.reachmee.com/ext/I007/927/main?site=13&validator=da57c1f2e2ddea2946680e7e5adb241d&lang=UK&ref='
    Country_Name = 'Sweden'
    Rank_USN = 127
    Rank_QSN = 118
    Rank_USN_CS = 474
    Auto_Soup = True

    def _extract_jobs(self):
        job_block = self.soup_data.select_one('#jobsTable')
        return job_block.select('tbody tr')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            dept = clean_text(row.select_one('td:nth-child(2)').text)

            if dept != 'Department of Computer and Systems Sciences':
                continue

            title = clean_text(row.select_one('td:nth-child(1) a').text)
            link = row.select_one('td:nth-child(1) a').attrs['href']
            expire_at = read_date(clean_text(row.select_one('td:nth-child(3) span:nth-child(2)').text), "%Y-%m-%d")
            self.save_position(link, title, expire_at)
