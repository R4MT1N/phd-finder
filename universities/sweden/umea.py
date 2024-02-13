from lib import *
from models import CUniversity


class Umea(CUniversity):
    Name = 'Umea University'
    Vacancy_Link = 'https://www.umu.se/en/work-with-us/open-positions/listajobb?JobbSidId=3770980&JobbBlockId=3771058&pk=1&org=8304&X-Requested-With=XMLHttpRequest'
    Country_Name = 'Sweden'
    Rank_USN = 366
    Rank_QSN = 465
    Rank_USN_CS = None
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('.jobblista')

    def _extract_jobs(self):
        return self.soup_data.select('.jobblista .jobb')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            title = clean_text(row.select_one('.jobbRow a.jobbTitle').text)
            link = join_urls(self.Vacancy_Link, row.select_one('.jobbRow a.jobbTitle').attrs['href'])
            expire_at = read_date(clean_text(row.select_one('.jobbRow .applybydate').text), "%Y-%m-%d")
            self.save_position(link, title, expire_at)
