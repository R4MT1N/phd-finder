from lib import *


class Groningen(University):
    Name = 'University of Groningen'
    Vacancy_Link = 'https://www.rug.nl/about-ug/work-with-us/job-opportunities/?cat=phd&&_x_tr_tl=en&_x_tr_hl=en&_x_tr_pto=wapp'
    Country_Name = 'Netherlands'
    Rank_USN = 88
    Rank_QSN = 139
    Rank_USN_CS = 415
    Auto_Soup = True

    def _extract_job_block(self):
        self.page_soup = BeautifulSoup(get_request(self.Vacancy_Link, headers={'Accept-Language': 'en-US,en;q=0.7'}).content, 'html.parser')
        return self.page_soup.select_one('div.rug-background-alternating--inverse')

    def _extract_jobs(self):
        return self.page_soup.select('div.rug-background-alternating--inverse > div')

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            dept = clean_text(job.select('div.rug-layout .rug-layout__item')[1].text)

            if dept != 'Faculty of Science and Engineering':
                continue

            title = clean_text(job.select_one('div.rug-mb-s a').text)
            link = join_urls(self.Vacancy_Link, job.select_one('div.rug-mb-s a').attrs['href'])
            end_at = read_date(clean_text(job.select('div.rug-layout .rug-layout__item')[5].text), '%B %d, %Y')
            self.add_position(link, title, end_at)
