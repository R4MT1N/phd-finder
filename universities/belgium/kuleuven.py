from typing import List
from lib import *


class KULeuven(University):
    Name = 'KU Leuven'
    Auto_Soup = False
    Vacancy_Link = 'https://icts-p-fii-toep-component-filter2.cloud.icts.kuleuven.be/api/projects/Jobsite_phd/search?112=%5B%22Research%20Areas%20Science,%20Engineering%20and%20Technology%22%5D&115=%5B%22Full-time%22%5D&136=%5B%22Computer%20Science%22%5D&lang=en&page=0'
    Country_Name = 'Belgium'
    Rank_USN = 342
    Rank_QSN = 124
    Rank_USN_CS = 123

    def _extract_job_block(self):
        try:
            self.json_data = post_request(self.Vacancy_Link, data={"_locale": "en", "environment": "production", "release": ""}).json()['hits']
            return self.json_data
        except:
            return None

    def _extract_jobs(self):
        return self.json_data

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job['_source']['posting']['title'])
            link = join_urls('https://www.kuleuven.be/personeel/jobsite/jobs/', job['_id'])
            end_at = read_date(job['_source']['applyBefore'], '%Y%m%d')
            self.add_position(link, title, end_at)
