from lib import *
from models import CUniversity


# Luxembourg University does not announce the position deadlines, which is weird!
# I'm not sure how it is going to work, but I will complete the code for this university in future

class Bergen(CUniversity):
    Name = 'University of Bergen'
    Vacancy_Link = 'https://www.uib.no/en/about/84777/vacant-positions-uib'
    Country_Name = 'Norway'
    Rank_USN = 199
    Rank_QSN = 281
    Rank_USN_CS = 400
    Auto_Soup = True

    def _extract_jobs(self):
        job_block = self.soup_data.select_one('ul.uib-vacancies')
        return job_block.select('li')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            if "Department of Informatics" not in row.select_one('p'):
                continue

            link = row.select_one('h3 a').attrs['href']
            title = row.select_one('h3 a').text
            expire_at = read_date(clean_text(row.select_one('p').text.split("deadline:")[1]), "%A, %B %d, %Y")

            self.save_position(link, title, expire_at)
