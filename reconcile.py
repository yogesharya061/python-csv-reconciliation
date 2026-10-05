"""Validate and reconcile CSV deliveries without modifying the originals."""
import argparse,csv,hashlib,html,json,os,tempfile
from decimal import Decimal,InvalidOperation
from pathlib import Path
REQUIRED={'order_id','amount','status'}

def load(path):
 valid={};issues=[];seen=set();total=0
 with open(path,newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  if not REQUIRED.issubset(reader.fieldnames or []):raise ValueError('Missing columns: '+str(REQUIRED-set(reader.fieldnames or [])))
  if len(set(reader.fieldnames))!=len(reader.fieldnames):raise ValueError('Duplicate column names')
  for line,row in enumerate(reader,2):
   total+=1;key=(row.get('order_id') or '').strip();reason=None
   try:
    amount=Decimal(row.get('amount') or '')
    if not amount.is_finite() or amount<0 or amount!=amount.quantize(Decimal('.01')):raise InvalidOperation
   except (InvalidOperation,ValueError):reason='invalid_amount'
   status=(row.get('status') or '').strip()
   if status not in {'paid','refunded','pending'}:reason='invalid_status'
   if not key:reason='missing_key'
   if key in seen:reason='duplicate_key'
   if key:seen.add(key)
   if reason:issues.append({'line':line,'order_id':key,'reason':reason});continue
   valid[key]={'amount':str(amount.quantize(Decimal('.01'))),'status':status}
 return valid,issues,total

def atomic_write(path,text):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf8') as f:f.write(text)
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)

def run(source,target,out):
 s,si,sn=load(source);t,ti,tn=load(target)
 missing=sorted(s.keys()-t.keys());extra=sorted(t.keys()-s.keys())
 changed=[{'order_id':k,'source':s[k],'target':t[k]} for k in sorted(s.keys()&t.keys()) if s[k]!=t[k]]
 fingerprint=hashlib.sha256(Path(source).read_bytes()+b'\0'+Path(target).read_bytes()).hexdigest()
 report={'input_sha256':fingerprint,'source_rows':sn,'target_rows':tn,'source_valid_unique':len(s),'target_valid_unique':len(t),'source_issues':si,'target_issues':ti,'missing_in_target':missing,'extra_in_target':extra,'changed':changed,'source_valid_total':str(sum((Decimal(v['amount']) for v in s.values()),Decimal(0))),'target_valid_total':str(sum((Decimal(v['amount']) for v in t.values()),Decimal(0)))}
 report['passed']=not any([si,ti,missing,extra,changed])
 out=Path(out);atomic_write(out/'report.json',json.dumps(report,indent=2))
 issue_count=len(si)+len(ti)+len(missing)+len(extra)+len(changed)
 markup="""<!doctype html><html lang="en"><meta charset="utf-8"><title>Data delivery check</title>
 <style>body{font:17px system-ui;background:#f3f6fa;color:#192b41;margin:45px auto;max-width:950px}header,section{background:white;padding:28px;border-radius:12px;margin:18px 0}h1{margin:0;color:#123f5a}pre{white-space:pre-wrap;overflow-wrap:anywhere}strong{color:#b34325}</style>
 <header><p>PORTFOLIO DEMO · SYNTHETIC DATA</p><h1>Data delivery check</h1><p>CSV validation and source-to-target reconciliation</p></header>"""
 markup+=f'<section><h2>{"PASS" if report["passed"] else "REVIEW REQUIRED"}</h2><p><strong>{issue_count} findings</strong> · Source: {sn} rows · Target: {tn} rows</p><p>Missing: {len(missing)} · Extra: {len(extra)} · Changed: {len(changed)}</p></section>'
 markup+='<section><h2>Audit details</h2><pre>'+html.escape(json.dumps(report,indent=2))+'</pre></section></html>'
 atomic_write(out/'report.html',markup);return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',default='data/source.csv');p.add_argument('--target',default='data/target.csv');p.add_argument('--out',default='output');a=p.parse_args()
 try:r=run(a.source,a.target,a.out)
 except (ValueError,OSError) as e:p.exit(1,str(e)+'\n')
 print(json.dumps({'passed':r['passed'],'report':str(Path(a.out)/'report.html')}))
 raise SystemExit(0 if r['passed'] else 2)
