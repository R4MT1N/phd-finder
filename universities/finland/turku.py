from lib import *
from models import CUniversity


class Turku(CUniversity):
    Name = 'University of Turku'
    Auto_Soup = False
    Vacancy_Link = 'https://ats.talentadore.com/positions/3VMfJS4/json?v=2&display_language=en&tags=&notTags=&busi[%E2%80%A6]nits=&display_description=job_ad&categories=tags_and_extras'
    Country_Name = 'Finland'
    Rank_USN = 300
    Rank_QSN = 315
    Rank_USN_CS = 300

    def _extract_jobs(self):
        return get_request(self.Vacancy_Link).json()['jobs']

    def fetch_positions(self):
        for job in self._extract_jobs():
            for category in job['categories']:
                if category['domain'] == 'staff-group' and category['term'] == "Teaching and research staff":
                    break
            else:
                continue

            title = clean_text(job['name'])
            link = job['link']
            end_at = read_date(job['due_date'], '%Y-%m-%dT%H:%M:%SZ')
            self.save_position(link, title, end_at)
