from lib import *


class Lulea(University):
    Name = 'Lulea University of Technology'
    Vacancy_Link = 'https://www.ltu.se/appresource/4.49015fe118adb9b38ad1b0e4/12.49015fe118adb9b38ad1b05b/jobs'
    Country_Name = 'Sweden'
    Rank_USN = 710
    Rank_QSN = None
    Rank_USN_CS = 265
    Auto_Soup = True

    def _extract_job_block(self):
        try:
            return get_request(self.Vacancy_Link).json()['data']
        except:
            return None

    def _extract_jobs(self):
        job_block: dict = self._extract_job_block()
        return job_block.get('jobs', [])

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job['title'])

            if (not any(term.lower() in title.lower() for term in ['PhD', 'Doctorate', 'Doctoral'])) or 'postdoctoral' in title.lower():
                continue

            link = job['link']
            expire_at = read_date(clean_text(job['expirationDate']), "%Y-%m-%d")
            self.add_position(link, title, expire_at)
