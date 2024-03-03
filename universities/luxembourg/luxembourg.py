from lib import *
from models import CUniversity


# Luxembourg University does not announce the position deadlines, which is weird!
# I'm not sure how it is going to work, but I will complete the code for this university in future

class Luxembourg(CUniversity):
    Name = 'University of Luxembourg'
    Vacancy_Link = 'https://emea3.recruitmentplatform.com/syndicated/lay/jsoutputinitrapido.cfm?ID=QMUFK026203F3VBQB7V7VV4S8&LG=UK&mask=karriereseiten&mtbrwchk=nok&browserchk=no&JobAdLG=UK&LOV52=11696&SUBDEPT2=27&LOV53=11737&keywords=&Resultsperpage=100&srcsubmit=Search&statlog=1&page1=index.html&component=lay9999_lst400a&rapido=false&1707809426383'
    Country_Name = 'Luxembourg'
    Rank_USN = 570
    Rank_QSN = 381
    Rank_USN_CS = 196
    Auto_Soup = True

    def _extract_jobs(self):
        job_block = self.soup_data.select_one('#jobsTable')
        return job_block.select('tbody tr')

    def fetch_positions(self):
        rows = self._extract_jobs()

        for row in rows:
            dept = clean_text(row.select_one('td:nth-child(4)').text)
            job_type = clean_text(row.select_one('td:nth-child(5)').text)

            if dept != 'Computer Science and Engineering' or job_type != 'PhD Student Positions':
                continue

            title = clean_text(row.select_one('td:nth-child(2) a').text)
            link = row.select_one('td:nth-child(2) a').attrs['href']
            expire_at = read_date(clean_text(row.select_one('td:nth-child(3) span:nth-child(2)').text), "%Y-%m-%d")
            self.save_position(link, title, expire_at)
