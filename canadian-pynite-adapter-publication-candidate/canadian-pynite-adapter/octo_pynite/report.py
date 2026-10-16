"""Offline review report: complete member rows, signed demands, support reactions."""
import html,json,csv
from pathlib import Path

def write_report(data,result,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    rows=[]
    for mid,cases in result['members'].items():
        for cid,r in cases.items():
            d=r['demand'];checks=r.get('wood_checks',{}).get('comparisons',[])
            ratios='; '.join(f"{v['check']} {v['ratio']:.3f}" for v in checks)
            vals=[mid,cid,r['limit_state'],d['axial_min_kN'],d['axial_max_kN'],d['Fy_min_kN'],d['Fy_max_kN'],d['Fz_min_kN'],d['Fz_max_kN'],d['My_min_kNm'],d['My_max_kNm'],d['Mz_min_kNm'],d['Mz_max_kNm'],1000*d['dy_min_m'],1000*d['dy_max_m'],1000*d['dz_min_m'],1000*d['dz_max_m'],ratios,r['design_status'],r.get('design_reason','')]
            rows.append(vals)
    headers=['Member','Case','Limit state','N min kN','N max kN','Vy min kN','Vy max kN','Vz min kN','Vz max kN','My min kNm','My max kNm','Mz min kNm','Mz max kNm','dy min mm','dy max mm','dz min mm','dz max mm','Demand / resistance','Check status','Qualification']
    with path.with_suffix('.csv').open('w') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(rows)
    def table(head,body):return '<table><thead><tr>'+''.join('<th>'+html.escape(str(v))+'</th>' for v in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(f'{v:.5g}' if isinstance(v,float) else str(v))+'</td>' for v in row)+'</tr>' for row in body)+'</tbody></table>'
    reactionrows=[[c,n,*r.values()] for c,nodes in result['support_reactions'].items() for n,r in nodes.items()]
    points={n['id']:(n['xyz'][0]-.5*n['xyz'][1],-n['xyz'][2]-.35*n['xyz'][1]) for n in data['nodes']}
    xs=[p[0] for p in points.values()];ys=[p[1] for p in points.values()];scale=min(850/max(max(xs)-min(xs),1),350/max(max(ys)-min(ys),1))
    xy={k:(40+(x-min(xs))*scale,40+(y-min(ys))*scale) for k,(x,y) in points.items()}
    graphic='<svg width="950" height="440" viewBox="0 0 950 440" role="img" aria-label="Axonometric connectivity view">'
    for m in data['members']:
        x,y=xy[m['i']];xx,yy=xy[m['j']]
        graphic+=f'<line x1="{x}" y1="{y}" x2="{xx}" y2="{yy}" stroke="#176a85" stroke-width="4"/><text x="{(x+xx)/2+5}" y="{(y+yy)/2-5}">{html.escape(m["id"])}</text>'
    for n in data['nodes']:
        x,y=xy[n['id']];color='#c44' if any(n['supports']) else '#333'
        graphic+=f'<circle cx="{x}" cy="{y}" r="5" fill="{color}"/><text x="{x+7}" y="{y+15}">{html.escape(n["id"])}</text>'
    graphic+='</svg>'
    body='<h1>Canadian PyNite adapter: review results</h1><p><strong>Development calculation. Not construction approval or complete Canadian code compliance.</strong></p><p>Input SHA256: '+result['input_sha256']+'</p><p>'+html.escape(result['scope'])+'</p><h2>Explicit connectivity</h2><p>Axonometric view; red nodes have one or more restraints. Member IDs match every result below. No hidden member or unlabelled foundation result.</p>'+graphic+'<h2>All member results</h2><p>Local member axes. Positive axial force is compression. Separate extrema are not simultaneous interaction demands. Deflections are absolute local displacements.</p>'+table(headers,rows)+'<h2>Foundation / support reactions</h2><p>Global signed kN and kNm; ULS and SLS remain separate. These are reactions, not soil-bearing acceptance.</p>'+table(['Case','Node','FX','FY','FZ','MX','MY','MZ'],reactionrows)+'<h2>Global equilibrium</h2>'+table(['Case','Balanced','Force/moment residual about origin'],[[c,r['balanced'],r['residual_about_origin']] for c,r in result['equilibrium'].items()])
    path.write_text('<!doctype html><meta charset="utf-8"><title>Canadian adapter review</title><style>body{font:15px Arial;margin:30px;color:#17242c}table{border-collapse:collapse;margin:20px 0;font-size:12px}th,td{border:1px solid #bbc;padding:7px}th{background:#e3edf2}svg{border:1px solid #ccd}h2{margin-top:35px}</style>'+body)
