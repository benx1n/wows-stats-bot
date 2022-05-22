from .models import matching

nations = [
    matching(("commonwealth","英联邦",),"commonwealth"),
    matching(("europe","欧洲",),"europe"),
    matching(("france","法国",),"france"),
    matching(("germany","德国",),"germany:"),
    matching(("italy","意大利",),"italy"),
    matching(("japan","日本",),"japan"),
    matching(("pan_america","泛美",),"pan_america"),
    matching(("pan_asia","泛亚",),"pan_asia"),
    matching(("uk","英国",),"uk"),
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