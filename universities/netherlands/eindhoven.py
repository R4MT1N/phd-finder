from lib import *
from models import CUniversity


class Eindhoven(CUniversity):
    Name = 'Eindhoven University of Technology'
    Auto_Soup = False
    Vacancy_Link = 'https://jobs.tue.nl/en/vacancies.html'
    Country_Name = 'Netherlands'
    Rank_USN = 342
    Rank_QSN = 124
    Rank_USN_CS = 123

    def _extract_jobs(self):
        content = post_request(self.Vacancy_Link,
                               data={'p_category_code_arr': ['6047-461661', '6048-461676'], 'p_format': 'AJAX'}).content
        self.page_soup = BeautifulSoup(content, 'html.parser')
        return self.page_soup.select('div.jobpost')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job.select_one('h2').attrs['title'])
            link = job.select_one('h2 a').attrs['href']
            expire_at = read_date(job.select_one('span.job_date').text, '%d %B %Y')
            self.save_position(link, title, expire_at)
