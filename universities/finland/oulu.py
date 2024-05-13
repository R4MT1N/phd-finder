from lib import *
from models import CUniversity


# Luxembourg University does not announce the position deadlines, which is weird!
# I'm not sure how it is going to work, but I will complete the code for this university in future

class Oulu(CUniversity):
    Name = 'University of Oulu'
    Vacancy_Link = 'https://oulunyliopisto.varbi.com/en/'
    Country_Name = 'Finland'
    Rank_USN = 447
    Rank_QSN = 313
    Rank_USN_CS = 227
    Auto_Soup = True

    def _extract_jobs(self):
        job_block = self.soup_data.select_one('#table-position')
        return job_block.select('tbody tr')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            if "Faculty of Information Technology" not in row.select_one('.pos-subcompany').text:
                continue

            link = row.select_one('.pos-ends a').attrs['href']
            title = row.select_one('.pos-title').text
            expire_at = read_date(clean_text(row.select_one('.pos-ends').text), "%Y-%m-%d")

            self.save_position(link, title, expire_at)
