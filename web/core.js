// Pure analytical functions shared by the dashboard and its parity tests.
export const YEARS = [2017, 2021, 2025];
export const PAGE_NAMES = ['Overview','Indicators','Cluster Atlas','Party Landscape','Party Portrait','Change','Volt','District Explorer','Methodology'];
export const SLUGS = ['overview','indicators','cluster-atlas','party-landscape','party-portrait','change','volt','district-explorer','methodology'];
export const mean = values => { const v = values.filter(Number.isFinite); return v.length ? v.reduce((a,b)=>a+b,0)/v.length : null; };
export const median = values => {const v=values.filter(Number.isFinite).toSorted((a,b)=>a-b), n=v.length; return n ? (v[Math.floor((n-1)/2)]+v[Math.floor(n/2)])/2 : null;};
export const clamp = (v,a,b)=>Math.max(a,Math.min(b,v));
export const safe = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function vote(d, year, party){return d.votes[YEARS.indexOf(+year)]?.[party] ?? null;}
export function turnout(d, year){return d.turnout[YEARS.indexOf(+year)] ?? null;}
export function comparable(ds,party,start,end){return ds.filter(d=>YEARS.filter(y=>y>=start&&y<=end).every(y=>Number.isFinite(vote(d,y,party))));}
export function change(d, party, start, end){const a=vote(d,start,party),b=vote(d,end,party);return Number.isFinite(a)&&Number.isFinite(b)?b-a:null;}
export function highSupport(ds, party, year){const threshold=median(ds.map(d=>vote(d,year,party)));return {threshold, districts:ds.filter(d=>Number.isFinite(vote(d,year,party))&&vote(d,year,party)>=threshold)};}
export function portrait(ds,features,party,year){const selected=highSupport(ds,party,year);return {...selected, profile:features.map((f,i)=>(mean(selected.districts.map(d=>d.features[i]))-f.mean)/(f.sd||1))};}
export function profileZ(d, feature, i){const v=d.features[i];return ((feature.transform==='log1p'?Math.log1p(v):v)-feature.modelMean)/(feature.modelSD||1);}
export function percentile(ds, district, i){const valid=ds.filter(d=>Number.isFinite(d.features[i]));return valid.filter(d=>d.features[i]<=district.features[i]).length/valid.length*100;}
export function peers(ds,district){return ds.filter(d=>d.id!==district.id).map(d=>({district:d,distance:Math.hypot(...d.pca.map((v,i)=>v-district.pca[i]))})).sort((a,b)=>a.distance-b.distance||a.district.id.localeCompare(b.district.id)).slice(0,5);}
export function voltNational(data,year){const states=Object.values(data.volt[year]);const votes=states.reduce((s,d)=>s+d.votes,0),valid=states.reduce((s,d)=>s+d.valid,0);return {votes,valid,share:votes/valid*100};}
export function colourBetween(a,b,t){const rgb=c=>[1,3,5].map(i=>parseInt(c.slice(i,i+2),16));const x=rgb(a),y=rgb(b);return '#'+x.map((v,i)=>Math.round(v+(y[i]-v)*clamp(t,0,1)).toString(16).padStart(2,'0')).join('');}
export function indicatorColour(value, anchors){const a=[...anchors].sort((a,b)=>a.value-b.value);if(value<=a[0].value)return a[0].color;if(value>=a.at(-1).value)return a.at(-1).color;const high=a.findIndex(x=>x.value>=value),lo=a[high-1],hi=a[high];return colourBetween(lo.color,hi.color,(value-lo.value)/(hi.value-lo.value||1));}
export const PALETTES = [ ['#E5E7EB','#D0D0D0','#8C9199','#4B4F55','#171717'], ['#FDECEE','#F8B7BD','#F07580','#E83A49','#E3000F'], ['#E8F5EB','#B9DFBF','#7BCB8A','#3AB553','#1AA037'], ['#FFFDE6','#FFF8A6','#FFF36A','#FBE52D','#F2D400'], ['#F6E7EF','#E8BDD3','#D88DB4','#CA5B95','#BE3075'], ['#E5F5FC','#B5E2F4','#79CDEB','#36B4E3','#009EE0'] ];
export function partyRange(ds,p){const values=ds.flatMap(d=>YEARS.map(y=>vote(d,y,p))).filter(Number.isFinite);return [Math.min(...values),Math.max(...values)];}
export function supportColour(value,range,p,centred=false){if(!Number.isFinite(value))return '#e4ebef';const t=(value-range[0])/(range[1]-range[0]||1);const band=centred?(t<.125?0:t<.375?1:t<.625?2:t<.875?3:4):clamp(Math.floor(t*5),0,4);return PALETTES[p][band];}
export const CHANGE_COLOURS=['#C95D55','#EBAEA9','#F0F2F3','#A8D5C9','#238A78'];
export function changeColour(value,limit){if(!Number.isFinite(value))return '#dce2e6';return CHANGE_COLOURS[value< -limit*.5?0:value< -.5?1:value<=.5?2:value<=limit*.5?3:4];}
