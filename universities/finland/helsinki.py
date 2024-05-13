from lib import *
import json
from models import CUniversity


class Helsinki(CUniversity):
    Name = 'University of Helsinki'
    Auto_Soup = False
    Vacancy_Link = 'https://www.helsinki.fi/en/ajax_get_jobs/en/null/2/Faculty%20of%20Science/0'
    Country_Name = 'Finland'
    Rank_USN = 222
    Rank_QSN = 115
    Rank_USN_CS = 300

    def _extract_jobs(self):
        return json.loads(get_request(self.Vacancy_Link).json()[0]['data'])

    def fetch_positions(self):
        for job in self._extract_jobs():
            title = clean_text(job['title'])
            link = job['url']
            end_at = read_date(job['date'], '%d.%m.%Y')
            self.save_position(link, title, end_at)
