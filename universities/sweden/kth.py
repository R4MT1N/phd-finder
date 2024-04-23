import json
from lib import *
from models import CUniversity


class KTH(CUniversity):
    Vacancy_Link = "https://www.kth.se/lediga-jobb?l=en"
    Name = 'KTH Royal Institute of Technology'
    Country_Name = 'Sweden'
    Rank_QSN = 73
    Rank_USN = 240
    Rank_USN_CS = 96
    Auto_Soup = True

    def _extract_jobs(self):
        job_data = clean_text(self.soup_data.select_one('div.kth-content > div.row > script').string.split('=')[1].strip(' ;'), True).strip('"')
        job_block = json.loads(job_data)['jobData']
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
            link = job['links']['apply'] or job['links']['ad-rendered']
            expire_at = read_date(job['attributes']['dates']['deadline'].split('T')[0], "%Y-%m-%d")
            published_at = read_date(job['attributes']['dates']['published'].split('T')[0], "%Y-%m-%d")
            self.save_position(link, title, expire_at, published_at)
