from lib import *


class Chalmers(University):
    Name = 'Chalmers University of Technology'
    Vacancy_Link = 'https://web103.reachmee.com/ext/I003/304/main?site=5&validator=a72aeedd63ec10de71e46f8d91d0d57c&lang=UK&ref='
    Country_Name = 'Sweden'
    Rank_USN = 112
    Rank_QSN = 85
    Rank_USN_CS = 328
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('#jobsTable')

    def _extract_jobs(self):
        return self.soup_data.select('#jobsTable tbody tr')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            dept = clean_text(row.select_one('td:nth-child(4)').text)
            job_type = clean_text(row.select_one('td:nth-child(5)').text)

            if dept != 'Computer Science and Engineering' or job_type != 'PhD Student Positions':
                continue

            title = clean_text(row.select_one('td:nth-child(2) a').text)
            link = row.select_one('td:nth-child(2) a').attrs['href']
            expire_at = read_date(clean_text(row.select_one('td:nth-child(3) span:nth-child(2)').text), "%Y-%m-%d")
            self.add_position(link, title, expire_at)
