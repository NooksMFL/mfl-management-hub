"""Formation recommendations using measured ratings, never invented secondary OVRs."""
import json
import math
import re

ALIASES = {'DM':'CDM','AM':'CAM','LCB':'CB','RCB':'CB','LCM':'CM','RCM':'CM','LDM':'CDM','RDM':'CDM','LCAM':'CAM','RCAM':'CAM','LST':'ST','RST':'ST'}

def canonical(position):
    position=str(position).upper().strip()
    return ALIASES.get(position,position)

def numeric(value):
    if isinstance(value,bool):return None
    try:
        value=float(value)
        return value if math.isfinite(value) and 0<=value<=100 else None
    except (ValueError,TypeError):return None

def positions(value):
    if isinstance(value,list):
        return list(dict.fromkeys(canonical(v.get('position') or v.get('name')) if isinstance(v,dict) else canonical(v) for v in value))
    return list(dict.fromkeys(canonical(p) for p in re.findall(r'[A-Z]+',str(value or '').upper())))

def explicit_ratings(value):
    """Accept explicit maps/lists; do not infer a formula from attributes."""
    if isinstance(value,str):
        try:value=json.loads(value)
        except (ValueError,TypeError):return {}
    if isinstance(value,dict):
        pairs=value.items()
    elif isinstance(value,list):
        pairs=[(r.get('position') or r.get('name'),r.get('rating',r.get('overall',r.get('ovr')))) for r in value if isinstance(r,dict)]
    else:return {}
    result={}
    for key,value in pairs:
        if isinstance(value,dict):value=value.get('rating',value.get('overall',value.get('ovr')))
        rating=numeric(value)
        if key and rating is not None:result[canonical(key)]=rating
    return result

def payload_ratings(player):
    result={}
    for source in (player.get('metadata') or {},player):
        if not isinstance(source,dict):continue
        for key in ('positionRatings','position_ratings','ratingsByPosition','positions'):
            result.update(explicit_ratings(source.get(key)))
    return result

def rating_at(player,position):
    position=canonical(position)
    manual=explicit_ratings(player.get('manual_position_ratings'))
    if position in manual:return manual[position],'Entered rating'
    explicit=explicit_ratings(player.get('position_ratings'))
    if position in explicit:return explicit[position],'Supplied position rating'
    listed=positions(player.get('position'))
    # Existing cache has base OVR only. First-listed-position fallback is visible.
    if listed and position==listed[0]:
        rating=numeric(player.get('current_ovr',player.get('overall')))
        if rating is not None:return rating,'First-position OVR fallback'
    return None,'Unverified position rating'


def shape(*rows):return [(role,x,y) for y,row in rows for role,x in row]
BACK=[('LB',13),('LCB',38),('RCB',63),('RB',88)]
GK=(93,[('GK',50)])
FORMATIONS={
 '4-1-3-2':shape(GK,(75,BACK),(57,[('CDM',50)]),(38,[('LM',18),('CM',50),('RM',82)]),(15,[('LST',34),('RST',67)])),
 '4-3-3':shape(GK,(75,BACK),(49,[('LCM',20),('CM',50),('RCM',80)]),(16,[('LW',18),('ST',50),('RW',82)])),
 '4-3-3 D':shape(GK,(75,BACK),(57,[('CDM',50)]),(38,[('LCM',32),('RCM',68)]),(15,[('LW',18),('ST',50),('RW',82)])),
 '4-2-3-1':shape(GK,(75,BACK),(56,[('LDM',33),('RDM',67)]),(34,[('LM',18),('CAM',50),('RM',82)]),(13,[('ST',50)])),
 '4-3-2-1 narrow':shape(GK,(76,BACK),(61,[('CDM',50)]),(46,[('LCM',30),('RCM',70)]),(29,[('LCAM',33),('RCAM',67)]),(12,[('ST',50)])),
 '4-1-2-1-2':shape(GK,(76,BACK),(60,[('CDM',50)]),(44,[('LCM',28),('RCM',72)]),(29,[('CAM',50)]),(12,[('LST',34),('RST',67)])),
 '4-4-2':shape(GK,(75,BACK),(45,[('LM',15),('LCM',38),('RCM',63),('RM',88)]),(16,[('LST',34),('RST',67)])),
 '4-1-4-1':shape(GK,(75,BACK),(58,[('CDM',50)]),(36,[('LM',15),('LCM',38),('RCM',63),('RM',88)]),(13,[('ST',50)])),
}


def assignment(costs):
    """Rectangular Hungarian algorithm; each player used at most once."""
    n=len(costs);m=len(costs[0]);u=[0]*(n+1);v=[0]*(m+1);matched=[0]*(m+1);way=[0]*(m+1)
    for i in range(1,n+1):
        matched[0]=i;j0=0;minimum=[float('inf')]*(m+1);used=[False]*(m+1)
        while True:
            used[j0]=True;i0=matched[j0];delta=float('inf');j1=0
            for j in range(1,m+1):
                if not used[j]:
                    cur=costs[i0-1][j-1]-u[i0]-v[j]
                    if cur<minimum[j]:minimum[j]=cur;way[j]=j0
                    if minimum[j]<delta:delta=minimum[j];j1=j
            for j in range(m+1):
                if used[j]:u[matched[j]]+=delta;v[j]-=delta
                else:minimum[j]-=delta
            j0=j1
            if not matched[j0]:break
        while j0:
            j1=way[j0];matched[j0]=matched[j1];j0=j1
            if not j0:break
    return {matched[j]-1:j-1 for j in range(1,m+1) if matched[j]}


def recommend(players):
    from squad_builder import has_current_club
    unique={str(p['player_id']):p for p in players if has_current_club(p.get('club'))}
    players=sorted(unique.values(),key=lambda p:int(p['player_id']))
    results=[]
    for formation,slots in FORMATIONS.items():
        costs=[]
        for role,_,_ in slots:
            row=[]
            for p in players:
                rating,source=rating_at(p,role)
                row.append(-(10000+rating) if rating is not None else 1000000)
            costs.append(row+[0]*11)
        assigned=assignment(costs);lineup={};total=0;fallbacks=0
        for i,j in assigned.items():
            if j<len(players) and costs[i][j]<0:
                p=players[j];role=slots[i][0];rating,source=rating_at(p,role)
                lineup[role]=str(p['player_id']);total+=rating;fallbacks+=source=='First-position OVR fallback'
        results.append({'formation':formation,'lineup':lineup,'filled':len(lineup),'average':total/11 if len(lineup)==11 else None,
                        'known_average':total/len(lineup) if lineup else None,'total':total,'fallbacks':fallbacks,
                        'missing':[role for role,_,_ in slots if role not in lineup]})
    return sorted(results,key=lambda r:(-r['filled'],-r['total'],r['fallbacks'],r['formation']))
