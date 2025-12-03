from ruamel.yaml import YAML
from pathlib import Path
yaml = YAML()
docs = yaml.load_all(open('configs/systems/jr_purtec_catalog.yaml','r',encoding='utf-8'))
for d in docs:
    sid = d.get('system_id')
    if sid and sid.upper().startswith('SYSTEM_R1'):
        p = d.get('polyol',{})
        print('system_id=', sid)
        print('oh number raw=', p.get('oh_number_mgKOH_per_g'), type(p.get('oh_number_mgKOH_per_g')))
        break
print('done')
