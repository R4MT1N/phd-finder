from lib import *
from models import CUniversity


class Hannover(CUniversity):
    Name = 'University of Hannover'
    Vacancy_Link = 'https://www.uni-hannover.de/en/universitaet/stellenangebote-arbeit-an-der-uni/jobboerse'
    Country_Name = 'Germany'
    Rank_USN = 487
    Rank_QSN = 481
    Rank_USN_CS = 550

    def _extract_job_block(self):
        try:
            content = post_request(self.Vacancy_Link, data={'luhjobs[__referrer][@extension]': 'Luhjobs',
                                                            'luhjobs[__referrer][@controller]': 'Search',
                                                            'luhjobs[__referrer][@action]': 'index',
                                                            'luhjobs[__referrer][arguments]': 'YToxOntzOjY6InNlYXJjaCI7YTo0OntzOjQ6InRleHQiO3M6MDoiIjtzOjU6InR5cGVzIjthOjE6e2k6MDtzOjE6IjciO31zOjEyOiJpbnN0aXR1dGlvbnMiO2E6MTp7aTowO3M6MjoiMTMiO31zOjE0OiJkZWdyZWVyZXF1aXJlZCI7czoxOiIwIjt9fQ==6eee82abdcad91ddef2bef267b0a6006b8dcc11a',
                                                            'luhjobs[__referrer][@request]': '{"@extension":"Luhjobs","@controller":"Search","@action":"index"}b91485920cdd2a5fd6e0f2ed061f22022ad80985',
                                                            'luhjobs[__trustedProperties]': '{"search":{"text":1,"types":[1,1,1,1,1,1,1,1],"institutions":[1,1,1,1,1,1,1,1,1,1,1],"degreerequired":1}}4dee803633408e84c74e9c62c52abefb3e786111',
                                                            'luhjobs[search][types][]': '7',
                                                            'luhjobs[search][types][]': '11',
                                                            'luhjobs[search][institutions][]': '13',
                                                            'luhjobs[search][degreerequired]': '1'}).content

            return BeautifulSoup(content, 'html.parser').select_one('div.luhjobs')
        except:
            return None

    def _extract_jobs(self):
        job_block = self._extract_job_block()
        return job_block.select('div.js-searchresults div.c-jobsitem')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job.select_one('div.c-jobsitem__name a').text)
            link = join_urls(self.Vacancy_Link, job.select_one('div.c-jobsitem__name a').attrs['href'])
            expire_at = read_date(
                clean_text(clean_text(''.join(job.select_one('div.c-jobsitem__deadline').findAll(text=True, recursive=False)))), "%d.%m.%Y")
            self.save_position(link, title, expire_at)
