from dataclasses import dataclass
from re import L
from typing import Tuple,List
import time
import traceback

@dataclass
class matching:
    keywords: Tuple[str, ...]
    match_keywords : str

nations = [
    matching(("commonwealth","英联邦",),"commonwealth"),
    matching(("europe","欧洲",),"europe"),
    matching(("france","法国",),"france"),
    matching(("germany","德国",),"germany:"),
    matching(("italy","意大利",),"italy"),
    matching(("japan","日本",),"japan"),
    matching(("pan_america","泛美",),"pan_america"),
    matching(("pan_asia","泛亚",),"pan_asia"),
    matching(("uk","英国","United_Kingdom"),"United_Kingdom"),
    matching(("usa","美国",),"usa"),
    matching(("ussr","苏联",),"ussr"),
    matching(("netherlands","荷兰",),"netherlands"),
    matching(("spain","西班牙",),"spain"),
]

shiptypes = [
    matching(("Cruiser","巡洋舰","巡洋","CA"),"Cruiser"),
    matching(("Battleship","战列舰","战列","BB"),"Battleship"),
    matching(("Destroyer","驱逐舰","驱逐","DD"),"Destroyer"),
    matching(("Submarine","潜艇","SS"),"Submarine"),
    matching(("Auxiliary","辅助舰艇","DD"),"Auxiliary"),
    matching(("AirCarrier","航空母舰","航母","CV"),"AirCarrier"),
]

levels = [
    matching(("1","1级","一级","一"),"1"),
    matching(("2","2级","二级","二"),"2"),
    matching(("3","3级","三级","三"),"3"),
    matching(("4","4级","四级","四"),"4"),
    matching(("4","4级","四级","四"),"4"),
    matching(("5","5级","五级","五"),"5"),
    matching(("6","6级","六级","六"),"6"),
    matching(("7","7级","七级","七"),"7"),
    matching(("8","8级","八级","八"),"8"),
    matching(("9","9级","九级","九"),"9"),
    matching(("10","10级","十级","十"),"10"),
    matching(("11","11级","十一级","十一"),"11"),
]

servers = [
    matching(("asia","亚服","asian"),"asia"),
    matching(("eu","欧服","europe"),"eu"),
    matching(("na","美服","NorthAmerican"),"na"),
    matching(("ru","俄服","Russia"),"ru"),
    matching(("cn","国服","china"),"cn"),
]

pr_select = [
    {
        "value": 0,
        "name": "还需努力",
        "englishName": "Bad",
        "color": "#FE0E00"
    },
    {
        "value": 750,
        "name": "低于平均",
        "englishName": "Below Average",
        "color": "#FE7903"
    },
    {
        "value": 1100,
        "name": "平均水平",
        "englishName": "Average",
        "color": "#FFC71F"
    },
    {
        "value": 1350,
        "name": "好",
        "englishName": "Good",
        "color": "#44B300"
    },
    {
        "value": 1550,
        "name": "很好",
        "englishName": "Very Good",
        "color": "#318000"
    },
    {
        "value": 1750,
        "name": "非常好",
        "englishName": "Great",
        "color": "#02C9B3"
    },
    {
        "value": 2100,
        "name": "大佬水平",
        "englishName": "Unicum",
        "color": "#D042F3"
    },
    {
        "value": 2450,
        "name": "神佬水平",
        "englishName": "Super Unicum",
        "color": "#A00DC5"
    }
]

async def set_infoparams(List):
    try:
        result = {
            "guild":List['clanInfo']['tag'],
            "userName":List['userName'],
            "karma":List['karma'],
            "serverName":List['serverName'],
            "newDamage":List['dwpDataVO']['damage'],
            "newWins":round(List['dwpDataVO']['wins'],2),
            "newPr":List['dwpDataVO']['pr'],
            "prValue":f"{List['pr']['value']} {List['pr']['name']}",
            "time":time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(List['lastDateTime'])),
            "battles":List['pvp']['battles'],
            "wins":List['pvp']['wins'],
            "damage":List['pvp']['damage'],
            "xp":List['pvp']['xp'],
            "kd":List['pvp']['kd'],
            "hit":List['pvp']['hit'],
            "bb_battles":List['type']['Battleship']['battles'],
            "bb_pr":List['type']['Battleship']['pr']['value'],
            "bb_wins":List['type']['Battleship']['wins'],
            "bb_damage":List['type']['Battleship']['damage'],
            "bb_hit":List['type']['Battleship']['hit'],
            "ca_battles":List['type']['Cruiser']['battles'],
            "ca_pr":List['type']['Cruiser']['pr']['value'],
            "ca_wins":List['type']['Cruiser']['wins'],
            "ca_damage":List['type']['Cruiser']['damage'],
            "ca_hit":List['type']['Cruiser']['hit'],
            "dd_battles":List['type']['Destroyer']['battles'],
            "dd_pr":List['type']['Destroyer']['pr']['value'],
            "dd_wins":List['type']['Destroyer']['wins'],
            "dd_damage":List['type']['Destroyer']['damage'],
            "dd_hit":List['type']['Destroyer']['hit'], 
            "cv_battles":List['type']['AirCarrier']['battles'],
            "cv_pr":List['type']['AirCarrier']['pr']['value'],
            "cv_wins":List['type']['AirCarrier']['wins'],
            "cv_damage":List['type']['AirCarrier']['damage'],
            "cv_hit":List['type']['AirCarrier']['hit'],      
            "solo_battles":List['pvpSolo']['battles'],
            "solo_wins":List['pvpSolo']['wins'],
            "solo_xp":List['pvpSolo']['xp'],
            "solo_damage":List['pvpSolo']['damage'],
            "solo_kd":List['pvpSolo']['kd'],
            "solo_hit":List['pvpSolo']['hit'],
            "div2_battles":List['pvpTwo']['battles'],
            "div2_wins":List['pvpTwo']['wins'],
            "div2_xp":List['pvpTwo']['xp'],
            "div2_damage":List['pvpTwo']['damage'],
            "div2_kd":List['pvpTwo']['kd'],
            "div2_hit":List['pvpTwo']['hit'],
            "div3_battles":List['pvpThree']['battles'],
            "div3_wins":List['pvpThree']['wins'],
            "div3_xp":List['pvpThree']['xp'],
            "div3_damage":List['pvpThree']['damage'],
            "div3_kd":List['pvpThree']['kd'],
            "div3_hit":List['pvpThree']['hit'],
            "lv1":List['battleCountAll']['1'],
            "lv2":List['battleCountAll']['2'],
            "lv3":List['battleCountAll']['3'],
            "lv4":List['battleCountAll']['4'],
            "lv5":List['battleCountAll']['5'],
            "lv6":List['battleCountAll']['6'],
            "lv7":List['battleCountAll']['7'],
            "lv8":List['battleCountAll']['8'],
            "lv9":List['battleCountAll']['9'],
            "lv10":List['battleCountAll']['10'],
            "prValueColor":List['pr']['color'],
        }
        return result
    except Exception:
        traceback.print_exc()

async def set_recentparams(List):
    try:   
        historyData = await set_historyData(List['recentList'])
        result = {
            "guild":List['clanInfo']['tag'],
            "userName":List['userName'],
            "serverName":List['serverName'],
            "prValue":f"{List['data']['pr']['value']} {List['data']['pr']['name']}",
            "reTime":time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(List['recordTime'])),
            "battles":List['data']['battles'],
            "wins":List['data']['wins'],
            "damage":List['data']['damage'],
            "xp":List['data']['xp'],
            "kd":List['data']['kd'],
            "hit":List['data']['hit'],
            "historyData":historyData,
            "prValueColor":List['data']['pr']['color'],
        }
        return result
    except Exception:
        traceback.print_exc()

async def select_prvalue_and_color(pr:int):
    for select in pr_select :
        if pr > select['value']:
            describe = select['name']
            color = select['color']
    return describe,color

async def set_historyData(List):
    historyData = ''
    for ship in List:
        historyData += r'<tr>'
        historyData += r'<td class="blueColor">'+f"{ship['shipInfo']['nameCn']}"+r'</td>'
        historyData += r'<td class="blueColor">'+f"{ship['shipInfo']['level']}"+r'</td>'
        historyData += r'<td class="blueColor">'+f"{ship['battles']}"+r'</td>'
        historyData += r'<td class="blueColor">'+f"{ship['pr']['value']}"+r'</td>'
        historyData += r'<td class="blueColor">'+f"{ship['xp']}"+r'</td>'
        historyData += r'<td class="blueColor">'+f"{ship['wins']}%"+r'</td>'
        historyData += r'<td class="blueColor">'+f"{ship['damage']}"+r'</td>'
        historyData += r'<td class="blueColor">'+f"{ship['hit']}%"+r'</td>'
        historyData += r'</tr>'
    return historyData
