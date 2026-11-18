import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as C from '../core.js';
const data=JSON.parse(readFileSync(new URL('../data/snapshot.json',import.meta.url)));
const geometry=JSON.parse(readFileSync(new URL('../data/geometry.json',import.meta.url)));
const close=(actual,expected,tolerance=1e-8)=>assert.ok(Math.abs(actual-expected)<tolerance,`${actual} != ${expected}`);
const party=id=>data.parties.findIndex(p=>p.party_group_id==='party_group_'+id);

test('all nine pages include Volt and stable shareable slugs',()=>{
  assert.equal(C.PAGE_NAMES.length,9);assert.equal(C.SLUGS.length,9);
  assert.equal(C.PAGE_NAMES[C.SLUGS.indexOf('volt')],'Volt');
  assert.equal(new Set(C.SLUGS).size,9);
});
test('separate district edition shares styling and excludes the Volt route',()=>{
  const full=C.reportPages(),districts=C.reportPages(false);
  assert.equal(full.length,9);assert.equal(districts.length,8);
  assert.ok(full.some(p=>p.slug==='volt'));
  assert.ok(!districts.some(p=>p.slug==='volt'));
  assert.deepEqual(districts,full.filter(p=>p.slug!=='volt'));
  const entry=readFileSync(new URL('../dashboard/index.html',import.meta.url),'utf8');
  assert.match(entry,/data-edition="districts"/);
  assert.match(entry,/href="\.\.\/styles\.css"/);
  assert.match(entry,/src="\.\.\/app\.js\?edition=3"/);
});
test('complete validated coverage and string geographic keys',()=>{
  assert.equal(data.districts.length,400);assert.equal(Object.keys(geometry.districts).length,400);
  assert.equal(data.states.length,16);assert.equal(Object.keys(geometry.states).length,16);
  assert.equal(data.features.length,14);assert.equal(data.features.filter(f=>f.included_in_clustering==='True').length,11);
  for(const d of data.districts){assert.match(d.id,/^\d{5}$/);assert.ok(geometry.districts[d.id].startsWith('M'));assert.equal(d.features.length,14);assert.ok(d.features.every(Number.isFinite));assert.ok(d.votes.flat().every(v=>v===null||Number.isFinite(v)));assert.equal(d.pca.length,4);}
  for(const d of data.states)assert.ok(geometry.states[d.state_code].endsWith('Z'));
});
test('cluster counts match Power BI',()=>{
  assert.deepEqual(data.clusters.map(c=>data.districts.filter(d=>d.cluster===c.cluster_id).length),[64,234,67,35]);
});
test('mean district turnout is not the weighted national turnout',()=>{
  close(C.mean(data.districts.map(d=>C.turnout(d,2017))),75.84825);
  close(C.mean(data.districts.map(d=>C.turnout(d,2025))),82.36075);
});
test('district vote-share trends match Power BI',()=>{
  close(C.mean(data.districts.map(d=>C.vote(d,2021,party('spd')))),25.6635);
  close(C.mean(data.districts.map(d=>C.vote(d,2025,party('spd')))),15.69625);
  close(C.mean(data.districts.map(d=>C.vote(d,2025,party('cdu_csu')))),29.42975);
});
test('all-district gains and losses reconcile with published findings',()=>{
  for(const id of ['afd','spd','fdp']){
    const p=party(id),ds=C.comparable(data.districts,p,2021,2025);
    assert.equal(ds.length,400);
    assert.equal(ds.filter(d=>id==='afd'?C.change(d,p,2021,2025)>0:C.change(d,p,2021,2025)<0).length,400);
  }
  assert.equal(data.districts.filter(d=>C.change(d,party('cdu_csu'),2021,2025)>0).length,380);
});
test('all comparable periods exclude missing intermediate observations',()=>{
  const complete={votes:[[1],[2],[3]]},missingMiddle={votes:[[1],[null],[3]]};
  assert.equal(C.comparable([complete,missingMiddle],0,2017,2025).length,1);
  assert.equal(C.change(missingMiddle,0,2017,2025),2);
  // GRÜNE were not on the Saarland ballot in 2021. Missing is not zero.
  const greens=party('greens');
  assert.equal(data.districts.filter(d=>C.vote(d,2021,greens)===null).length,6);
  assert.equal(C.comparable(data.districts,greens,2017,2025).length,394);
});
test('Berlin peers match the Power BI five-neighbour table',()=>{
  const berlin=data.districts.find(d=>d.id==='11000'),result=C.peers(data.districts,berlin);
  assert.deepEqual(result.map(x=>x.district.id),['05913','04011','05113','05114','09761']);
  assert.deepEqual(result.map(x=>+x.distance.toFixed(2)),[1.04,1.18,1.29,1.36,1.53]);
  assert.ok(!result.some(x=>x.district.id===berlin.id));
});
test('Explorer percentile includes ties and selected district',()=>{
  const berlin=data.districts.find(d=>d.id==='11000'),i=data.features.findIndex(f=>f.feature_id==='population_density');
  close(C.percentile(data.districts,berlin,i),99.75);
});
test('model profiles agree with exported cluster z scores for all eleven inputs',()=>{
  for(const cluster of data.clusters){const ds=data.districts.filter(d=>d.cluster===cluster.cluster_id);for(const [i,f] of data.features.entries()){if(f.included_in_clustering!=='True')continue;close(C.mean(ds.map(d=>C.profileZ(d,f,i))),cluster.z[f.feature_id],1e-7);}}
});
test('Portrait uses national median, includes ties and raw-scale differences',()=>{
  const result=C.portrait(data.districts,data.features,party('cdu_csu'),2025);
  assert.ok(result.districts.every(d=>C.vote(d,2025,0)>=result.threshold));
  assert.ok(result.districts.length>=200);
  const i=data.features.findIndex(f=>f.feature_id==='population_density'),f=data.features[i];
  close(result.profile[i],(C.mean(result.districts.map(d=>d.features[i]))-f.mean)/f.sd);
});
test('Volt uses sum of votes / sum of valid second votes, not state means',()=>{
  const a=C.voltNational(data,2021),b=C.voltNational(data,2025);
  assert.equal(a.votes,164300);assert.equal(b.votes,355262);assert.equal(b.votes-a.votes,190962);
  close(b.share,0.7155397620020918);assert.equal(b.share.toFixed(2),'0.72');
  assert.notEqual(b.share,C.mean(Object.values(data.volt[2025]).map(x=>x.votes/x.valid*100)));
});
test('colour bands and neutral pp interval match DAX',()=>{
  assert.equal(C.changeColour(-.5,22),'#F0F2F3');assert.equal(C.changeColour(.5,22),'#F0F2F3');
  assert.equal(C.changeColour(-12,22),'#C95D55');assert.equal(C.changeColour(12,22),'#238A78');
  assert.equal(C.supportColour(50,[0,50],0),'#171717');
  assert.equal(C.supportColour(null,[0,50],0),'#e4ebef');
  assert.equal(C.indicatorColour(5,[{value:0,color:'#000000'},{value:10,color:'#ffffff'}]),'#808080');
});
test('all rendering inputs escape HTML',()=>{assert.equal(C.safe('<script>"x" & \'y\'</script>'),'&lt;script&gt;&quot;x&quot; &amp; &#39;y&#39;&lt;/script&gt;');});
