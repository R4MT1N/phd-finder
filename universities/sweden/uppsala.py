from lib import *

class Uppsala(University):
    Name = 'Uppsala University'
    Vacancy_Link = 'https://www.jobb.uu.se/?languageId=1&locationFilter=&positionType=doktorand&sortValue=published'
    Country_Name = 'Sweden'
    Rank_USN = 127
    Rank_QSN = 105
    Rank_USN_CS = 410
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('ul.loaded-content')

    def _extract_jobs(self):
        return self.soup_data.select('ul.loaded-content li')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            if row.select('a p')[0].text.strip() != 'Department of Information Technology':
                continue

            title = row.select_one('a h2').text
            link = join_urls(self.Vacancy_Link, row.select_one('a').attrs['href'])
            expire_at = read_date(row.select('a p')[1].text.split(':')[1].strip(), "%Y-%m-%d")
            published_at = read_date(row.select_one('a span').text, "%Y-%m-%d")
            self.save_position(link, title, expire_at, published_at)
