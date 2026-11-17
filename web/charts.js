// Small, local SVG charts: no external scripts, map tiles, keys or telemetry.
import {safe, clamp} from './core.js';
const n=(x,d=1)=>Number.isFinite(x)?x.toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d}):'—';
const tip=t=>`data-tip="${safe(t)}"`;
const tx=(x,y,text,cls='',extra='')=>`<text x="${x}" y="${y}" class="${cls}" ${extra}>${safe(text)}</text>`;
const line=(x1,y1,x2,y2,cls='grid-line')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="${cls}"/>`;
function size(host){return {w:Math.max(260,host.clientWidth),h:Math.max(160,host.clientHeight)};}
function svg(host,w,h,html,label){host.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${safe(label)}">${html}</svg>`;}
function ticks(min,max,count=5){if(min===max)max=min+1;const span=max-min;const raw=span/count,power=10**Math.floor(Math.log10(raw));const step=[1,2,2.5,5,10].map(x=>x*power).find(x=>x>=raw)||power*10;const result=[];for(let t=Math.ceil(min/step)*step;t<=max+step*.001;t+=step)result.push(+t.toFixed(8));return result;}
function wrappedLabel(x,y,label,width){const words=String(label).replaceAll('-','- ').split(' '),rows=[''];for(const word of words){const separator=rows.at(-1)&&!rows.at(-1).endsWith('-')?' ':'';if((rows.at(-1)+separator+word).length>width/6.5&&rows.at(-1))rows.push(word);else rows[rows.length-1]+=separator+word;}return `<text x="${x}" y="${y-(rows.length-1)*6}" text-anchor="end" class="axis-label">${rows.map((r,i)=>`<tspan x="${x}" dy="${i?13:0}">${safe(r)}</tspan>`).join('')}</text>`;}
export function legend(items, id=''){return `<div class="legend" aria-label="Chart legend">${items.map((s,i)=>id?`<button type="button" class="legend-item" data-legend="${safe(id)}" data-series="${i}" aria-pressed="true" title="Show or hide ${safe(s.name)}"><span class="dot" style="background:${s.color}"></span>${safe(s.name)}</button>`:`<span class="legend-item"><span class="dot" style="background:${s.color}"></span>${safe(s.name)}</span>`).join('')}</div>`;}

export function bars(host,rows,opts={}){
  const {w,h}=size(host), left=opts.left?Math.max(Math.min(145,w*.42),Math.min(opts.left,w*.45)):Math.min(210,w*.42),right=opts.right??76,top=12,bottom=28;
  let min=Math.min(0,...rows.flatMap(r=>[r.value,r.secondary??0])),max=Math.max(0,...rows.flatMap(r=>[r.value,r.secondary??0]));
  if(opts.domain)[min,max]=opts.domain;else {const pad=(max-min||1)*.08;if(min<0)min-=pad;if(max>0)max+=pad;}
  if(min===max)max=min+1;
  const x=v=>left+(v-min)/(max-min)*(w-left-right),rowH=(h-top-bottom)/Math.max(rows.length,1), y=i=>top+rowH*(i+.5);
  let html=ticks(min,max,opts.ticks||5).map(t=>line(x(t),top,x(t),h-bottom)+tx(x(t),h-6,opts.tick?opts.tick(t):n(t,opts.decimals??0),'axis-label','text-anchor="middle"')).join('');
  html+=line(x(0),top,x(0),h-bottom,'zero-line');
  rows.forEach((r,i)=>{
    const group = r.click ? `data-action="${safe(r.click)}" data-value="${safe(r.id)}" tabindex="0" role="button" aria-label="${safe(r.label)}"` : '';
    const bh=Math.min(opts.paired?13:22,rowH*(opts.paired?.25:.52)), posY=y(i)-(opts.paired?bh+1:bh/2);
    html+=`<g ${group} ${tip(r.tooltip||r.label+': '+(r.display??n(r.value)))}>${wrappedLabel(left-10,y(i)+4,r.label,left-20)}`;
    if(Number.isFinite(r.secondary)){
      const sy=opts.paired?y(i)+1:y(i)-bh/2;
      html+=`<rect x="${Math.min(x(0),x(r.secondary))}" y="${sy}" width="${Math.max(.8,Math.abs(x(r.secondary)-x(0)))}" height="${bh}" fill="${r.secondaryColor||'#a8bbc5'}"/>`;
      html+=tx(x(r.secondary)+(r.secondary<0?-7:7),sy+bh*.8,r.secondaryDisplay??n(r.secondary),'value-label',`text-anchor="${r.secondary<0?'end':'start'}"`);
    }
    html+=`<rect x="${Math.min(x(0),x(r.value))}" y="${posY}" width="${Math.max(.8,Math.abs(x(r.value)-x(0)))}" height="${bh}" fill="${r.color||'#7357e8'}"/>`;
    html+=tx(x(r.value)+(r.value<0?-7:7),posY+bh*.8,r.display??n(r.value),'value-label',`text-anchor="${r.value<0?'end':'start'}"`)+`</g>`;
  });
  if(!rows.length)html+=tx(w/2,h/2,'No comparable data','axis-label','text-anchor="middle"');
  svg(host,w,h,html,opts.label||'Horizontal bar chart');
}

export function lines(host,series,years,opts={}){
  const {w,h}=size(host),left=44,right=40,top=26,bottom=34;
  const values=series.flatMap(s=>s.values).filter(Number.isFinite);
  let min=opts.zero?0:Math.max(0,Math.floor((Math.min(...values)-3)/5)*5),max=Math.ceil((Math.max(...values)+3)/5)*5;
  if(!values.length){svg(host,w,h,tx(w/2,h/2,'No data','axis-label'),'No data');return;}
  const x=i=>left+(w-left-right)*(years.length===1?.5:i/(years.length-1)),y=v=>h-bottom-(v-min)/(max-min)*(h-top-bottom);
  let html=ticks(min,max,4).map(t=>line(left,y(t),w-right,y(t))+tx(left-8,y(t)+4,t+'%','axis-label','text-anchor="end"')).join('');
  html+=years.map((t,i)=>tx(x(i),h-9,t,'axis-label','text-anchor="middle"')).join('');
  const labels=years.map((_,i)=>series.map((s,j)=>({series:j,y:y(s.values[i])})).filter(p=>Number.isFinite(p.y)).sort((a,b)=>a.y-b.y));
  labels.forEach(column=>{column.forEach((p,i)=>{p.labelY=Math.max(top-10,p.y-12,i?column[i-1].labelY+13:0);});const overflow=column.at(-1)?.labelY-(h-bottom-3);if(overflow>0)column.forEach(p=>p.labelY-=overflow);});
  series.forEach((s,j)=>{
    const points=s.values.map((v,i)=>Number.isFinite(v)?`${x(i)},${y(v)}`:null).filter(Boolean);
    html+=`<g class="series series-${j}"><polyline points="${points.join(' ')}" fill="none" stroke="${s.color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`;
    s.values.forEach((v,i)=>{if(!Number.isFinite(v))return;html+=`<circle cx="${x(i)}" cy="${y(v)}" r="4.5" fill="${s.color}" ${tip(`${s.name} · ${years[i]}: ${n(v)}%`)} />`;if(opts.labels!==false){const p=labels[i].find(p=>p.series===j);html+=tx(x(i),p.labelY,n(v)+'%','value-label','text-anchor="middle"');}});
    html+='</g>';
  });
  svg(host,w,h,html,opts.label||'Election trend line chart');
}

export function stacked(host,rows,series,opts={}){
  const {w,h}=size(host),left=opts.left??Math.min(196,w*.34),right=18,top=8,bottom=30;
  const max=opts.percent?100:Math.max(1,...rows.map(r=>r.values.reduce((a,b)=>a+b,0)))*1.04;
  const x=v=>left+v/max*(w-left-right),rh=(h-top-bottom)/Math.max(rows.length,1);
  let html=ticks(0,max,opts.ticks||4).map(t=>line(x(t),top,x(t),h-bottom)+tx(x(t),h-7,t+(opts.percent?'%':''),'axis-label','text-anchor="middle"')).join('');
  rows.forEach((r,i)=>{
    const y=top+rh*(i+.5),bh=Math.min(22,rh*.64);let sum=0;
    html+=wrappedLabel(left-10,y+4,r.label,left-18);
    r.values.forEach((v,j)=>{const width=x(sum+v)-x(sum);html+=`<g class="series series-${j}" ${tip(`${r.label} · ${series[j].name}: ${n(v)}${opts.percent?'%':' districts'}`)}><rect x="${x(sum)}" y="${y-bh/2}" width="${Math.max(0,width)}" height="${bh}" fill="${series[j].color}" stroke="white" stroke-width="1.4"/>`;
      if(opts.labels&&width>34)html+=tx(x(sum)+width/2,y+4,n(v)+'%','stack-label','text-anchor="middle"');html+='</g>';sum+=v;});
  });
  svg(host,w,h,html,opts.label||'Stacked bar chart');
}

export function scatter(host,points,selected,peerIds){
  const {w,h}=size(host),left=40,right=18,top=12,bottom=36;
  const xmin=Math.min(...points.map(d=>d.pca[0]))-.5,xmax=Math.max(...points.map(d=>d.pca[0]))+.5;
  const ymin=Math.min(...points.map(d=>d.pca[1]))-.5,ymax=Math.max(...points.map(d=>d.pca[1]))+.5;
  const x=v=>left+(v-xmin)/(xmax-xmin)*(w-left-right),y=v=>h-bottom-(v-ymin)/(ymax-ymin)*(h-top-bottom);
  let html=ticks(xmin,xmax,4).map(t=>line(x(t),top,x(t),h-bottom)+tx(x(t),h-bottom+18,n(t,0),'axis-label','text-anchor="middle"')).join('');
  html+=ticks(ymin,ymax,4).map(t=>line(left,y(t),w-right,y(t))+tx(left-8,y(t)+4,n(t,0),'axis-label','text-anchor="end"')).join('');
  html+=tx(w/2,h-2,'PC1','axis-title','text-anchor="middle"')+`<text transform="translate(12 ${h/2}) rotate(-90)" class="axis-title" text-anchor="middle">PC2</text>`;
  const sorted=[...points].sort((a,b)=>(a.id===selected.id?2:peerIds.includes(a.id)?1:0)-(b.id===selected.id?2:peerIds.includes(b.id)?1:0));
  sorted.forEach(d=>{const chosen=d.id===selected.id,peer=peerIds.includes(d.id);html+=`<circle cx="${x(d.pca[0])}" cy="${y(d.pca[1])}" r="${chosen?12:peer?7:4.5}" fill="${chosen?selected.color:peer?'#1593b5':'#e0e9ed'}" fill-opacity="${chosen?.9:peer?.85:.8}" stroke="${chosen?'#5635c8':'white'}" stroke-width="${chosen?1.5:.4}" data-action="district" data-value="${d.id}" ${tip(`${d.name} [${d.id}]\nPC1 ${n(d.pca[0],2)} · PC2 ${n(d.pca[1],2)}${chosen?'\nSelected district':peer?'\nStructural peer':''}`)}/>`;});
  svg(host,w,h,html,'PC1–PC2 structural neighbourhood. Select a point to inspect its district.');
}

export function map(host,paths,fill,descriptions,opts={}){
  host.innerHTML=`<div class="map-controls" aria-label="Map zoom"><button data-map-zoom="in" aria-label="Zoom in on map">+</button><button data-map-zoom="out" aria-label="Zoom out on map">−</button><button data-map-zoom="reset" aria-label="Fit map">⌂</button></div><svg class="germany-map" viewBox="0 0 400 550" role="group" aria-label="${safe(opts.label||'Interactive map of Germany')}">${Object.entries(paths).map(([id,path])=>`<path d="${path}" fill="${fill(id)}" fill-rule="evenodd" stroke="#8596a1" stroke-width="${opts.stateMap?.9:.65}" vector-effect="non-scaling-stroke" tabindex="0" role="button" aria-label="${safe(descriptions(id))}" data-action="${opts.stateMap?'state-map':'map-district'}" data-value="${id}" ${tip(descriptions(id))}><title>${safe(descriptions(id))}</title></path>`).join('')}</svg>`;
}
