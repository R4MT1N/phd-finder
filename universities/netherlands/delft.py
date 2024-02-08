from typing import List
from lib import *


class Delft(University):
    Name = 'Delft University of Technology'
    Vacancy_Link = 'https://emea3.recruitmentplatform.com/fo/rest/jobs?firstResult=0&maxResults=100&sortBy=DPOSTINGEND&sortOrder=desc'
    Country_Name = 'Netherlands'
    Rank_USN = 169
    Rank_QSN = 47
    Rank_USN_CS = 65

    def _extract_job_block(self):
        try:
            return post_request(self.Vacancy_Link,
                                headers={'Username': 'QEZFK026203F3VBQBLO6G68W9:guest:FO', 'Password': 'guest'},
                                json={"searchCriteria": {"criteria": [{"key": "LOV25", "values": ["11383"]},
                                                                       {"key": "LOV27", "values": ["11422"]},
                                                                       {"key": "LOV28", "values": ["11564"]},
                                                                       {"key": "Resultsperpage",
                                                                        "values": ["100"]}]}}).json()['jobs']
        except:
            return None

    def _extract_jobs(self):
        return self._extract_job_block()

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job['jobFields']['jobTitle'])
            link = job['jobFields']['applicationUrl']
            expire_at = read_timestamp(job['jobFields']['DPOSTINGEND'] // 1000)
            self.add_position(link, title, expire_at)
