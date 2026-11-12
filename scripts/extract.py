import json,zipfile,pathlib,collections,csv,hashlib
P=pathlib.Path('data'); out=pathlib.Path('web')
v=json.loads((P/'version.json').read_text(encoding='utf-8-sig'))
z=zipfile.ZipFile(P/'verified.jar')
raw={n.removeprefix('data/minecraft/recipe/').removesuffix('.json'):json.loads(z.read(n)) for n in z.namelist() if n.startswith('data/minecraft/recipe/') and n.endswith('.json')}
tags={n.removeprefix('data/minecraft/tags/item/').removesuffix('.json'):json.loads(z.read(n)) for n in z.namelist() if n.startswith('data/minecraft/tags/item/') and n.endswith('.json')}
def short(s): return s.removeprefix('minecraft:')
missing=set()
def expand(x,seen=()):
    if isinstance(x,list): return sorted(set(i for a in x for i in expand(a,seen)))
    if isinstance(x,dict): return expand(x.get('item',x.get('tag','')),seen) if 'item' in x else expand('#'+short(x['tag']),seen) if 'tag' in x else []
    if not isinstance(x,str) or not x: return []
    if x.startswith('#'):
        k=short(x[1:])
        if k in seen:return []
        if k not in tags: missing.add(k);return []
        return sorted(set(i for a in tags[k]['values'] for i in expand(a if isinstance(a,str) else a['id'],(*seen,k))))
    return [short(x)]
recipes=[]; special=[]
for id,r in sorted(raw.items()):
    t=short(r['type']);result=r.get('result',r.get('output')); groups=[]
    if isinstance(result,str): result={'id':result,'count':r.get('count',1)}
    if not isinstance(result,dict) or not result.get('id',result.get('item')):
        special.append({'id':id,'type':t,'raw':r});continue
    if t=='brewing':
        inp=r['input']; pot=short(inp['potion_contents']['potions'])
        groups=[{'options':[short(inp['item'])+'@'+pot],'count':1,'source':inp},{'options':expand(r['reagent']),'count':1,'source':r['reagent']}]
        result=dict(result);result['id']=short(result['id'])+'@'+short(result['components']['minecraft:potion_contents']['potion'])
    elif t=='crafting_transmute':
        groups=[{'options':expand(r[k]),'count':1,'source':r[k]} for k in ['input','material']]
    elif t=='crafting_decorated_pot':
        groups=[{'options':expand(r[k]),'count':1,'source':r[k],'role':k} for k in ['back','front','left','right']]
    elif isinstance(r.get('pattern'),list):
        counts=collections.Counter(''.join(r['pattern']));counts.pop(' ',None)
        groups=[{'options':expand(r['key'][k]),'count':n,'symbol':k,'source':r['key'][k]} for k,n in counts.items()]
    elif 'ingredients' in r:
        for x in r['ingredients']:
            op=expand(x)
            found=next((g for g in groups if g['options']==op),None)
            if found: found['count']+=1
            else: groups.append({'options':op,'count':1,'source':x})
    elif 'ingredient' in r: groups=[{'options':expand(r['ingredient']),'count':1,'source':r['ingredient']}]
    elif t.startswith('smithing'):
        groups=[{'options':expand(r[k]),'count':1,'source':r[k],'role':k} for k in ['template','base','addition'] if k in r]
    else: special.append({'id':id,'type':t,'raw':r});continue
    for g in groups:g['choiceMode']='per_unit'
    recipes.append({'id':id,'type':t,'output':short(result.get('id',result.get('item'))),'count':result.get('count',1),'groups':groups,'pattern':r.get('pattern'),'time':r.get('cookingtime'),'experience':r.get('experience'),'raw':r})
items=sorted({r['output'] for r in recipes}|{i for r in recipes for g in r['groups'] for i in g['options']})
outputs={r['output'] for r in recipes}
# Primary naturally collected materials break reversible storage / dye / wool cycles.
natural=set('coal diamond emerald lapis_lazuli redstone raw_iron raw_copper raw_gold gold_nugget iron_nugget bone bone_meal wheat slime_ball honey_bottle honeycomb string white_wool snowball clay_ball melon_slice dried_kelp nether_wart amethyst_shard quartz glowstone_dust flint leather rabbit_hide bamboo sugar_cane brown_mushroom red_mushroom sand red_sand gravel dirt cobblestone cobbled_deepslate blackstone netherrack end_stone basalt calcite tuff mud moss_block pale_moss_block stone sandstone red_sandstone obsidian ice packed_ice blue_ice pumpkin melon resin_clump egg milk_bucket water_bucket lava_bucket'.split())
natural.discard('dried_kelp')
natural|={i for i in items if i.endswith(('_log','_stem','_hyphae','_smithing_template')) and not i.startswith('stripped_')}
roots=(set(items)-outputs)|(natural&set(items))
levels={i:1 for i in roots}
for _ in range(len(items)):
    changed=False
    for r in recipes:
        ls=[min((levels.get(i,10**6) for i in g['options']),default=10**6) for g in r['groups']]
        l=1+max(ls,default=10**6)
        if l<levels.get(r['output'],10**6): levels[r['output']]=l;changed=True
    if not changed:break
lang=json.loads(z.read('assets/minecraft/lang/en_us.json'))
zh=json.loads((P/'zh_cn.json').read_text(encoding='utf-8-sig')) if (P/'zh_cn.json').exists() else {}
def name(i,l):
    if '@' in i:
        base,pot=i.split('@'); simple=pot.removeprefix('long_').removeprefix('strong_')
        return l.get('item.minecraft.'+base+'.effect.'+simple,base+' / '+pot)+(' · '+pot if pot!=simple else '')
    if i.endswith('_smithing_template'):
        return l.get('item.minecraft.'+i+'.new',l.get('item.minecraft.'+i,i))
    return l.get('item.minecraft.'+i,l.get('block.minecraft.'+i,i))
nodes={i:{'name':name(i,zh),'en':name(i,lang),'level':levels.get(i),'root':i in roots,'external':i not in outputs} for i in items}
stats={'version':'26.3','checked':'2026-11-12','recipes':len(recipes),'recipeFiles':len(raw),'special':len(special),'items':len(items),'roots':len(roots),'unresolved':[i for i in items if i not in levels],'levels':dict(sorted(collections.Counter(levels.values()).items())),'types':dict(collections.Counter(short(r['type']) for r in raw.values())),'missingTags':sorted(missing),'sha1':v['downloads']['client']['sha1']}
data={'meta':stats,'nodes':nodes,'recipes':recipes,'special':special}
(P/'data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(out/'recipes-26.3.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'graph-26.3.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
with (out/'catalog-26.3.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['recipe_id','type','output','中文名','output_count','level','input_AND_groups_OR_options'])
    for r in recipes:w.writerow([r['id'],r['type'],r['output'],nodes[r['output']]['name'],r['count'],levels.get(r['output']),json.dumps(r['groups'],ensure_ascii=False)])
print(json.dumps(stats,ensure_ascii=False,indent=2))
