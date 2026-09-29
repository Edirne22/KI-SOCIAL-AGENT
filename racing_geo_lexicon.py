"""Canonical MotoGP race geography aliases (German/Turkish/English).

Seeded from the official 2027 MotoGP calendar. Geography normalization is
language knowledge, not a claim that an event happened in a particular year.
"""
RACE_GEO = {
"Thailand":{"tr":["Tayland"],"en":["Thailand"],"circuits":["Buriram","Chang International Circuit"]},
"Katar":{"tr":["Katar"],"en":["Qatar"],"circuits":["Lusail","Lusail International Circuit"]},
"Brasilien":{"tr":["Brezilya"],"en":["Brazil"],"circuits":["Goiania","Goiânia"]},
"Argentinien":{"tr":["Arjantin"],"en":["Argentina"],"circuits":["Buenos Aires"]},
"USA":{"tr":["ABD","Amerika Birleşik Devletleri"],"en":["USA","United States"],"circuits":["Austin","Circuit of the Americas"]},
"Spanien":{"tr":["İspanya","Ispanya"],"en":["Spain"],"circuits":["Jerez","MotorLand Aragón","Aragon"]},
"Frankreich":{"tr":["Fransa"],"en":["France"],"circuits":["Le Mans"]},
"Italien":{"tr":["İtalya","Italya"],"en":["Italy"],"circuits":["Mugello","Misano"]},
"Katalonien":{"tr":["Katalonya"],"en":["Catalonia","Catalunya"],"circuits":["Barcelona","Circuit de Barcelona-Catalunya"]},
"Niederlande":{"tr":["Hollanda"],"en":["Netherlands"],"circuits":["Assen","TT Circuit Assen"]},
"Deutschland":{"tr":["Almanya"],"en":["Germany"],"circuits":["Sachsenring"]},
"Tschechien":{"tr":["Çekya","Cekya"],"en":["Czechia","Czech Republic"],"circuits":["Brno"]},
"Großbritannien":{"tr":["Büyük Britanya","Buyuk Britanya","İngiltere","Ingiltere"],"en":["Great Britain","UK"],"circuits":["Silverstone"]},
"Österreich":{"tr":["Avusturya"],"en":["Austria"],"circuits":["Spielberg","Red Bull Ring"]},
"San Marino":{"tr":["San Marino"],"en":["San Marino"],"circuits":["Misano"]},
"Aragon":{"tr":["Aragon"],"en":["Aragon"],"circuits":["MotorLand","MotorLand Aragón"]},
"Portugal":{"tr":["Portekiz"],"en":["Portugal"],"circuits":["Portimao","Portimão"]},
"Japan":{"tr":["Japonya"],"en":["Japan"],"circuits":["Motegi","Mobility Resort Motegi"]},
"Malaysia":{"tr":["Malezya"],"en":["Malaysia"],"circuits":["Sepang"]},
"Indonesien":{"tr":["Endonezya"],"en":["Indonesia"],"circuits":["Mandalika"]},
"Australien":{"tr":["Avustralya"],"en":["Australia"],"circuits":["Adelaide","Adelaide Street Circuit"]},
"Valencia":{"tr":["Valensiya"],"en":["Valencia"],"circuits":["Cheste","Circuit Ricardo Tormo"]},
}
def aliases_for(german):
 row=RACE_GEO.get(german,{})
 return [german]+list(row.get("tr",[]))+list(row.get("en",[]))+list(row.get("circuits",[]))
