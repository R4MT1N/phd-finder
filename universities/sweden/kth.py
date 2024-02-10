import json
from lib import *


class KTH(University):
    Vacancy_Link = "https://www.kth.se/lediga-jobb?l=en"
    Name = 'KTH Royal Institute of Technology'
    Country_Name = 'Sweden'
    Rank_QSN = 73
    Rank_USN = 240
    Rank_USN_CS = 96
    Auto_Soup = True

    def _extract_job_block(self):
        try:
            job_data = clean_text(self.soup_data.select_one('div.main > div.row > script').string.split('=')[1].strip(' ;'), True).strip('"')
            return json.loads(job_data)['jobData']
        except:
            return None

    def _extract_jobs(self):
        job_block = self._extract_job_block()
        return job_block.get('data', [])

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            for category in job['relationships']['categories']['data']:
                if category['type'] == 'job-category' and category['id'] == '1449':
                    break
            else:
                continue

            title = clean_text(job['attributes']['translations']['texts']['title'])
            link = job['links']['apply']
            expire_at = read_date(job['attributes']['dates']['deadline'].split('T')[0], "%Y-%m-%d")
            published_at = read_date(job['attributes']['dates']['published'].split('T')[0], "%Y-%m-%d")
            self.add_position(link, title, expire_at, published_at)
