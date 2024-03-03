from lib import *
from models import CUniversity


class Amsterdam(CUniversity):
    Name = 'University of Amsterdam'
    Vacancy_Link = 'https://vacatures.uva.nl/UvA/search/?createNewAlert=false&q=&optionsFacetsDD_department=Master&optionsFacetsDD_shifttype=PhD+position&optionsFacetsDD_facility=Faculty+of++Science&locale=en_GB'
    Country_Name = 'Netherlands'
    Rank_USN = 39
    Rank_QSN = 53
    Rank_USN_CS = 108

    def _extract_jobs(self):
        s = Session()
        jobs = []
        start_item = 0
        while True:
            s.get(self.Vacancy_Link)
            content = s.get(
                f'https://vacatures.uva.nl/UvA/tile-search-results/?q=&sortColumn=referencedate&sortDirection=desc&optionsFacetsDD_department=Master&optionsFacetsDD_shifttype=PhD+position&optionsFacetsDD_facility=Faculty+of++Science&startrow={start_item}').content
            temp_jobs = BeautifulSoup(content, 'html.parser').select('li.job-tile')
            jobs += temp_jobs
            start_item += 10
            if len(temp_jobs) < 10:
                break
        return jobs

    def fetch_positions(self):
        jobs = self._extract_jobs()

        for job in jobs:
            title = clean_text(job.select_one('a.jobTitle-link').text)
            link = join_urls(self.Vacancy_Link, job.select_one('a.jobTitle-link').attrs['href'])
            pos_soup = BeautifulSoup(get_request(link).content, 'html.parser')
            end_date = read_date(pos_soup.select_one('meta[itemprop=validThrough]').attrs['content'],
                                 "%a %b %d %H:%M:%S UTC %Y")
            start_at = read_date(pos_soup.select_one('meta[itemprop=datePosted]').attrs['content'],
                                 "%a %b %d %H:%M:%S UTC %Y")
            self.save_position(link, title, end_date, start_at)
