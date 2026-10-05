import json
import pytest
from reconcile import load,run

def test_sample_and_repeat(tmp_path):
 r=run('data/source.csv','data/target.csv',tmp_path)
 assert r['missing_in_target']==['A3'] and r['extra_in_target']==['A5']
 assert r['changed'][0]['order_id']=='A2'
 assert len(r['source_issues'])==3 and not r['passed']
 assert r==run('data/source.csv','data/target.csv',tmp_path)

def test_clean_pass_and_html_escape(tmp_path):
 p=tmp_path/'input.csv';p.write_text('order_id,amount,status\n<script>,1.00,paid\n')
 assert run(p,p,tmp_path/'report')['passed']
 q=tmp_path/'empty.csv';q.write_text('order_id,amount,status\n')
 run(p,q,tmp_path/'report')
 assert '&lt;script&gt;' in (tmp_path/'report/report.html').read_text()

def test_bad_schema(tmp_path):
 p=tmp_path/'x.csv';p.write_text('foo\nbar\n')
 with pytest.raises(ValueError):load(p)

def test_nonfinite_and_precision(tmp_path):
 p=tmp_path/'x.csv';p.write_text('order_id,amount,status\nA,NaN,paid\nB,1.001,paid\nC,Infinity,paid\n')
 valid,issues,n=load(p);assert not valid and len(issues)==3
