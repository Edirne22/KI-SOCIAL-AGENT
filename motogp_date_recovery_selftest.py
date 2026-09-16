import motogp_content_agency_v2 as a
from motogp_date_recovery_patch import install
install(a)
def check(title,url,expected):
 d=a.article_date({'title':title,'url':url});got=d.date().isoformat() if d else None
 if got!=expected:raise AssertionError(f'{title}: {got} != {expected}')
def main():
 check('GP14 Race News SAN MARINO 11 - 13 Sep 2026 11 - 13 Sep 2026 Title sponsor','https://www.motogp.com/en/en/news/grand-prix/san-marino','2026-09-13')
 check('GP1 Race News THAILAND 27 Feb - 1 Mar 2026 27 Feb - 1 Mar 2026 Title sponsor','https://www.motogp.com/en/en/news/grand-prix/thailand','2026-03-01')
 check('GP13 Race News ARAGON 28 - 30 Aug 2026','https://www.motogp.com/en/en/news/grand-prix/aragon','2026-08-30')
 check('Official Communications','https://www.motogp.com/en/news/official-communications',None)
 check('11 - 13 Sep 2026','https://example.com/news/grand-prix/test',None)
 print('MOTOGP DATE RECOVERY SELFTEST: PASS')
if __name__=='__main__':main()
