from lib import *


class Radboud(University):
    Name = 'Radboud University'
    Vacancy_Link = "https://www.ru.nl/en/working-at/job-opportunities/job-opportunities/Scientific/job-type/Promotieplaatsen/provider/828"
    Country_Name = 'Netherlands'
    Rank_USN = 106
    Rank_QSN = 222
    Rank_USN_CS = 248
    Auto_Soup = True

    def _extract_job_block(self):
        return self.soup_data.select_one('div.overview--list ul')

    def _extract_jobs(self):
        return self.soup_data.select('div.overview--list ul > li')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job.select_one('h2.card__title span.link__text').text)
            link = join_urls(self.Vacancy_Link, job.select_one('h2.card__title a').attrs['href'])
            job_details = BeautifulSoup(get_request(link).content, 'html.parser')
            end_at = read_date(clean_text(job_details.select('div.definitionlist__item time')[-1].attrs['datetime']), '%Y-%m-%dT%H:%M:%SZ')
            self.save_position(link, title, end_at)
