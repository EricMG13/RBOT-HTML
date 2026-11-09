/* Presentation views. No analytical execution. */
const DISPLAY_MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
// 31 December 2024 for a valid YYYY-MM-DD calendar date; anything else is returned unchanged. Never the OS locale.
function displayDate(iso) {
  const m=typeof iso==='string'&&/^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if(!m) return iso;
  const [year,month,day]=[Number(m[1]),Number(m[2]),Number(m[3])],check=new Date(Date.UTC(2000,month-1,day));
  check.setUTCFullYear(year);
  if(year<1||month<1||month>12||check.getUTCFullYear()!==year||check.getUTCMonth()!==month-1||check.getUTCDate()!==day) return iso;
  return `${day} ${DISPLAY_MONTHS[month-1]} ${year}`;
}
function installDestinations() {
  const title = h => h.replace(/^Chart data: /,'').replace(/^T[\w.]+(?:\s*[–/]\s*(?:T[\w.]+|\d+))*\s*[—–]\s*/,'').replace(/^./,s=>s.toUpperCase());
  for (const [id,out] of Object.entries(data)) {
    if(modules[id]) continue;
    const sections=[];
    const audit=[];
    for(const s of out.sections.filter(s=>s.blocks.length)) {
      if(/^(Request|Calculations|Next module)/.test(s.heading)) {audit.push('='+s.heading);continue;}
      sections.push(['s'+s.line,title(s.heading),['='+s.heading]]);
    }
        const first=out.summary?out.sections.find(s=>s.heading==='Reader summary'):out.firstHeading&&out.sections.find(s=>s.heading.startsWith(out.firstHeading));
    const rank=s=>s[0]==='s'+first?.line?-1:s[1]==='Sources'?1:0;
    sections.sort((a,b)=>rank(a)-rank(b));
    sections.push(['audit','Technical audit',audit]);
    modules[id]={name:moduleNames[out.module],subtitle:out.scope,first:first?'s'+first.line:sections[0][0],sections};
  }
  const destinations={
    'W-Library':['Issuer library',[['cases','Issuer cases',[]]]],
    'W-Overview':['Overview',[['overview','Overview',[]]]],
    'W-Calendar':['Event calendar',[['unavailable','Calendar availability',[]]]],
    'W-Reports':['Reports',[['list','Reports',[]]]],
    'W-Evidence':['Evidence library',[['sources','Retained outputs',[]]]],
    'W-Forecast':['Forecast',[['forecast','Forecast',[]]]],
    'CP-OS':['Run activity',[['activity','Run activity',[]]]]
  };
  for(const [id,[name,sections]] of Object.entries(destinations)) {
    modules[id]={name,sections,first:sections[0][0]};
    moduleNames[id]=name;
    data[id]={sections:[]};
  }
}

const moduleEntry=(module,context)=>contexts[context]?.modules[module];
const defaultOutput=(module,context)=>moduleEntry(module,context)?.default??null;
function resolveOutput(module,context,file) {
  const entry=moduleEntry(module,context);
  return entry?.outputs.find(id=>data[id].source===file)||entry?.default||null;
}
const NO_OUTPUT='No output found';
function availability(module,context) {
  const entry=moduleEntry(module,context);
  return entry?.outputs.length?'Output available':NO_OUTPUT;
}
const contextModules=context=>Object.keys(contexts[context].modules).filter(id=>contexts[context].modules[id].outputs.length);
// One issuer is one issuerKey, whatever names its runs were recorded under; an unrecorded issuer (null) equals nothing.
const sameIssuer=(a,b)=>a!=null&&a===b;
const issuerReports=context=>window.DESIGN_WORKSPACE.reports.filter(r=>!context||sameIssuer(r.issuerKey,contexts[context]?.issuerKey));
const reportsBuiltFrom=context=>window.DESIGN_WORKSPACE.reports.filter(r=>r.builtFrom.some(b=>b.run===context));
const reportsUsing=output=>window.DESIGN_WORKSPACE.reports.filter(r=>r.builtFrom.some(b=>b.source===output));
// A run's published models: those recorded for its folder and those built from a file it holds.
const publishedModels=()=>window.DESIGN_WORKSPACE.models;
const byModelId=(a,b)=>b.id.localeCompare(a.id);
// One order for the Model select, the section pager and the default: the default model first, then the rest by folder name, latest first.
// A model of another issuer (or of none recorded) is never a run's own, whatever run it names; no run context holds none.
const runModels=context=>{const run=contexts[context];if(!run)return [];const held=publishedModels().filter(m=>sameIssuer(m.issuerKey,run.issuerKey)&&(m.runId===run.folder||m.sources.some(s=>s.run===context))).sort(byModelId),first=modelOrder(held)[0];return first?[first,...held.filter(m=>m!==first)]:held;};
// A model links only to a run whose Forecast page lists it (runModels); with no such run it is shown unlinked.
const modelRun=model=>Object.keys(contexts).find(key=>runModels(key).includes(model))||null;
// A model opens under the run it was published for (its runId), never under a run that only supplied files; with no such run listing it, modelRun's choice stands.
const modelOwnRun=model=>Object.keys(contexts).find(key=>contexts[key].folder===model.runId&&runModels(key).includes(model))||modelRun(model);
// Not superseded by another listed model; one that records a predecessor comes first, then the later folder name.
const modelOrder=models=>[...models].sort((a,b)=>(models.some(m=>m.previous===a.id)-models.some(m=>m.previous===b.id))||((b.previous!=null)-(a.previous!=null))||byModelId(a,b));
function modelRelationship(model,models) {
  const successor=models.find(m=>m.previous===model.id);
  return model.previous?`supersedes ${model.previous}`:successor?`superseded by ${successor.id}`:'relationship not recorded';
}
const tracedRun=report=>report.builtFrom.find(b=>b.run)?.run||null;
const reportName=report=>report.build?`Build ${report.build} · ${report.label.trim()}`:report.label.trim();
const byBuild=(a,b)=>(b.build||0)-(a.build||0)||a.label.trim().localeCompare(b.label.trim());
// A frame has no error event for a page that never arrives, so a missing load within the timeout is the failure.
const frameTimeout=()=>Number.isFinite(window.DESIGN_FRAME_TIMEOUT_MS)?window.DESIGN_FRAME_TIMEOUT_MS:6000;
function watchFrame(frame,status,loadingText,failedText,link) {
  let timer=null;
  const loaded=()=>{clearTimeout(timer);status.hidden=true;};
  const wait=()=>{clearTimeout(timer);status.hidden=false;status.textContent=loadingText;timer=setTimeout(fail,frameTimeout());};
  function fail() {
    const retry=document.createElement('button');
    retry.type='button';retry.className='text-button frame-retry';retry.textContent='Retry';
    retry.addEventListener('click',()=>{frame.setAttribute('src',frame.getAttribute('src'));wait();});
    status.textContent=failedText+' ';
    if(link)status.append(link(),' ');
    status.append(retry);
  }
  frame.addEventListener('load',loaded);
  wait();
  return loaded;
}
const isReportRoute=(module,section)=>module==='W-Reports'&&window.DESIGN_WORKSPACE.reports.some(r=>r.id===section);
function firstSection(module,context) {
  const output=defaultOutput(module,context);
  return output?REPORT_PARTS[0][0]:navigationSections(module,context)[0][0];
}
const plural=(n,word)=>`${n} ${word}${n===1?'':'s'}`;
// The saved-output selector, the "Used in" link and the parse flag a module's head carries.
function headTools(module,context,output) {
  const files=moduleEntry(module,context)?.outputs||[],out=output&&data[output];
  const meta=!out?'':files.length>1?`<label class="output-meta output-select">Saved output <select id="output-select">${files.map(id=>`<option value="${esc(data[id].source)}" ${id===output?'selected':''}>${esc(data[id].label)}</option>`).join('')}</select></label>`:`<span class="output-meta">Saved output${out.label===module?'':` · ${esc(out.label)}`}</span>`;
  const used=output?reportsUsing(output):[];
  const usedIn=used.length===1?`<a class="output-meta" href="${routeHref('W-Reports',used[0].id)}">Used in ${esc(reportName(used[0]))}</a>`:used.length?`<a class="output-meta" href="${routeHref('W-Reports','list')}">Used in ${used.length} deliverables</a>`:'';
  const flag=out?.parseError?`<span class="output-meta">Shown unstructured: ${esc(out.parseError)}</span>`:'';
  return {meta,usedIn,flag};
}
function moduleHead({module,context,output}) {
  if(output&&isAnalytical(module))return ''; // The module report draws its own head.
  const {meta,usedIn,flag}=headTools(module,context,output);
  return `<div class="module-title"><h2 ${module.startsWith('W-')?'':`title="${esc(module)}"`}>${esc(moduleNames[module])}</h2>${meta}${usedIn}${flag}</div>`;
}
function fixtureTable(module,line) {
  const table=data[module].sections.flatMap(s=>s.blocks).find(b=>b.type==='table'&&b.line===line);
  if(!table)throw new Error(`Missing visual table ${module}:${line}`);
  return table;
}
function chartNumber(value) {
  const clean=plain(value).trim().replace(/,/g,'');
  if(!/^(?:[-+]?\d+(?:\.\d+)?|\(\d+(?:\.\d+)?\))(?:%|x)?$/.test(clean))return null;
  const number=Number(clean.replace(/[()%x]/g,''))*(clean.startsWith('(')?-1:1);
  return Number.isFinite(number)?number:null;
}
function chartIntro(id,v) {
  const label=[v.unit,data[id].period].filter(Boolean).join(' · ');
  return `<div class="section-heading"><h2>${esc(v.title)}</h2>${label?`<span>${esc(label)}</span>`:''}</div>${v.quote?`<p class="chart-reading">${rich(v.quote.text.replace(/\n/g,' '))}</p>${sourceFooter(`${id}:${v.quote.line}`)}`:''}`;
}
const evidenceHref=(id,line)=>routeHref(data[id].module,current?.output===id?current.section:modules[id].first,`${id}:${line}`,data[id].run);
function comparisonChart(module,v,selection=0,chips=false) {
  const table=fixtureTable(module,v.table),selected=table.rows[v.rows?.[selection]??0];
  const selectable=['paired','peers'].includes(v.kind)&&!['CP-4C','CP-2A'].includes(data[module].module);
  const rows=selectable?[selected]:(v.rows||table.rows.map((_,i)=>i)).map(i=>table.rows[i]);
  const points=v.kind==='peers'?v.columns.map(c=>({label:table.headers[c],value:selected.cells[c],row:selected,series:0})):rows.flatMap(row=>(v.columns||[v.column]).map((c,i)=>({label:plain(row.cells[0]),series:i,value:row.cells[c],row,column:c})));
  const max=Math.max(1,...points.map(p=>Math.abs(chartNumber(p.value)??0)));
  const hasNegative=points.some(p=>(chartNumber(p.value)??0)<0);
  return `${chartIntro(module,v)}${selectable&&!v.fixed?`<label class="metric-control">Measure <select id="chart-metric">${v.rows.map((idx,i)=>`<option value="${i}" ${i===selection?'selected':''}>${esc(plain(table.rows[idx].cells[0]))}</option>`).join('')}</select></label>`:''}<div class="horizontal-chart ${hasNegative?'diverging':''}">${points.map((p,i)=>{
    const n=chartNumber(p.value),width=n===null?0:Math.abs(n)/max*100;
    const key=`${module}:${p.row.line}`,cells=`<span class="chart-label">${i&&points[i-1].label===p.label?`<span class="sr-only">${esc(p.label)}</span>`:esc(p.label)}${v.columns&&v.kind!=='peers'?`<small>${esc(table.headers[p.column])}</small>`:''}</span><span class="track ${n===null?'missing':''}">${hasNegative?`<span class="zero-rule"></span><i class="series-${p.series} ${n<0?'negative':''}" style="left:${n<0?50-width/2:50}%;width:${width/2}%"></i>`:`<i class="series-${p.series}" style="width:${width}%"></i>`}</span><strong>${/[\p{L}\p{N}]/u.test(String(p.value??''))?esc(p.value):'Not available'}</strong>`;
    // With chips the row is a group: the button opens the row, each chip opens its own source (a chip cannot sit inside a button).
    return chips?`<div class="chart-row" role="group"><button class="chart-open" data-evidence="${esc(key)}">${cells}</button>${chipsMarkup(key)}</div>`:`<button class="chart-row" data-evidence="${esc(key)}">${cells}</button>`;
  }).join('')}</div><p class="matrix-note">Missing values have no bar.</p>`;
}
// A label of two or more words breaks at the space nearest its middle (ties: the earlier one).
function axisLines(label) {
  const spaces=[...label.matchAll(/ /g)].map(m=>m.index);
  if(!spaces.length)return [label];
  const at=spaces.reduce((best,i)=>Math.abs(i-label.length/2)<Math.abs(best-label.length/2)?i:best);
  return [label.slice(0,at),label.slice(at+1)];
}
function bridgeChart(module,v) {
  const table=fixtureTable(module,v.table),rows=(v.rows||table.rows.map((_,i)=>i)).map(i=>table.rows[i]);
  let running=0;
  const points=rows.map((row,i)=>{
    const amount=chartNumber(row.cells[v.amount]);
    if(amount===null)throw new Error('Non-numeric bridge input');
    const isTotal=i===0||(v.kind==='waterfall'&&i===rows.length-1);
    const start=isTotal?0:running;
    running=isTotal?amount:running+amount;
    if(v.total!==undefined&&Math.abs(running-chartNumber(row.cells[v.total]))>.001)throw new Error('Retained bridge does not reconcile');
    return {row,start,end:running,total:isTotal,amount};
  });
  if(v.total!==undefined) {
    const row=rows.at(-1),closing=chartNumber(row.cells[v.total]);
    points.push({row,start:0,end:closing,total:true,amount:closing,display:row.cells[v.total],label:'Issuer As Defined EBITDA'});
  }
  const max=Math.max(...points.map(p=>Math.max(p.start,p.end)))*1.16;
  const width=660,height=210,step=width/points.length,y=n=>height-n/max*height;
  return `${chartIntro(module,v)}<div class="vector-chart"><svg viewBox="-5 -12 680 270" role="group" aria-label="${esc(v.title)}. Select a movement to inspect its source."><line x1="0" y1="210" x2="660" y2="210" class="axis"/>${points.map((p,i)=>`<a class="plot-point" href="${evidenceHref(module,p.row.line)}" data-evidence="${esc(`${module}:${p.row.line}`)}" aria-label="${esc(p.label||plain(p.row.cells[0]))}, ${esc(p.display??p.row.cells[v.amount])} ${esc(v.unit)}. View source"><title>${esc(p.label||plain(p.row.cells[0]))}: ${esc(p.display??p.row.cells[v.amount])}</title><rect class="${p.total?'total':p.amount<0?'outflow':'movement'}" x="${i*step+10}" y="${y(Math.max(p.start,p.end))}" width="${step-20}" height="${Math.max(1,Math.abs(y(p.end)-y(p.start)))}"/><text x="${i*step+step/2}" y="${y(Math.max(p.start,p.end))-8}" text-anchor="middle">${esc(p.display??p.row.cells[v.amount])}</text><text class="axis-label" x="${i*step+step/2}" y="232" text-anchor="middle">${axisLines(p.label||plain(p.row.cells[0])).map((line,at)=>`<tspan x="${i*step+step/2}" dy="${at?'1.2em':0}">${esc(line)}</tspan>`).join('')}</text>${i<points.length-1?`<line class="connector" x1="${i*step+step-10}" y1="${y(p.end)}" x2="${(i+1)*step+10}" y2="${y(p.end)}"/>`:''}</a>`).join('')}</svg></div><div class="bridge-key">${points.map((p,i)=>`<span>${sourceLink(`${module}:${p.row.line}`,p.label||plain(p.row.cells[0]))}${classTag(evidence.get(`${module}:${p.row.line}`),'row-classification')}</span>`).join('')}</div>`;
}
function pathChart(module,v) {
  const table=fixtureTable(module,v.table),series=['Reference','Downside','Upside'];
  const values=table.rows.map(r=>chartNumber(r.cells[v.column]));
  if(values.some(n=>n===null))throw new Error('Missing conditional path value');
  const max=Math.max(...values)*1.13, y=n=>200-n/max*175;
  return `${chartIntro(module,v)}<div class="chart-legend path-legend">${series.map((s,i)=>`<span><i class="path-key-${i}"></i>${s}</span>`).join('')}<span>Dashed paths · conditional scenarios</span></div><div class="vector-chart"><svg viewBox="0 0 670 250" role="group" aria-label="Closing cash across FY2025 to FY2027. Select a point to inspect its exact source.">${[0,2000,4000,6000].map(n=>`<line class="gridline" x1="65" x2="600" y1="${y(n)}" y2="${y(n)}"/><text class="axis-label" x="55" y="${y(n)+4}" text-anchor="end">${n.toLocaleString('en-US')}</text>`).join('')}${series.map((name,i)=>{
    const rows=table.rows.filter(r=>r.cells[0].startsWith(name+' / '));
    return `<polyline class="path-${i}" fill="none" stroke-dasharray="${['5 4','2 4','9 4'][i]}" points="${rows.map((r,j)=>`${90+j*235},${y(chartNumber(r.cells[v.column]))}`).join(' ')}"/>${rows.map((r,j)=>`<a class="plot-point" href="${evidenceHref(module,r.line)}" data-evidence="${esc(`${module}:${r.line}`)}" aria-label="${esc(r.cells[0])}, closing cash ${esc(r.cells[v.column])} ${esc(v.unit)}. View source"><title>${esc(r.cells[0])}: ${esc(r.cells[v.column])} ${esc(v.unit)}</title><circle class="point-hit" cx="${90+j*235}" cy="${y(chartNumber(r.cells[v.column]))}" r="12"/><circle class="point-${i}" cx="${90+j*235}" cy="${y(chartNumber(r.cells[v.column]))}" r="4"/></a>`).join('')}`;
  }).join('')}${['2025','2026','2027'].map((year,i)=>`<text class="axis-label" x="${90+i*235}" y="230" text-anchor="middle">FY${year}</text>`).join('')}</svg></div><div class="path-readout">${series.map(name=>{const r=table.rows.find(r=>r.cells[0]===name+' / 2027');return `<div><span>${name} · FY2027</span><strong>${esc(r.cells[v.column])}</strong>${sourceFooter(`${module}:${r.line}`)}</div>`;}).join('')}</div>`;
}
function hedgeChart(module,v) {
  const table=fixtureTable(module,v.table),start=Date.UTC(2023,2,31),end=Date.UTC(2027,8,30),position=date=>(Date.parse(date)-start)/(end-start)*100;
  return `${chartIntro(module,v)}<div class="hedge-axis"><span style="left:0">Mar 2023</span><span style="left:${position('2024-09-30')}%">Sep 2024 base</span><span style="left:100%">Sep 2027</span></div><div class="hedge-chart">${table.rows.map(row=>{
    const dates=row.cells[2].match(/\d{4}-\d{2}-\d{2}/g),dated=dates?.length===2,forward=dated&&dates[0]>'2024-09-30';
    return `<button class="hedge-row" data-evidence="${esc(`${module}:${row.line}`)}"><span>${esc(row.cells[0])}<small>${esc(row.cells[1])} ${row.cells[0]==='FX forwards'?'':'USDm'}</small></span><span class="hedge-lane"><i class="base-rule" style="left:${position('2024-09-30')}%"></i>${dated?`<i class="hedge-span ${forward?'future':''}" style="left:${position(dates[0])}%;width:${position(dates[1])-position(dates[0])}%"></i>`:'<span class="duration-only">Duration only · ≤12 months</span>'}</span><span class="hedge-dates">${dated?esc(dates.join(' → ')):esc(row.cells[2])}<small>${forward?'Forward starting at base date':dated?'Active at base date':'No exact expiry supplied'}</small></span></button>`;
  }).join('')}</div>`;
}
function qualitativeVisual(module,v) {
  const table=fixtureTable(module,v.table);
  if(v.kind==='debate')return `${chartIntro(module,v)}<div class="debates">${table.rows.map(r=>`<section class="debate"><header><h3>${rich(r.cells[0])}</h3><span class="grade unknown">${rich(r.cells[3])}</span></header><div class="arguments"><div><h4>Bull position</h4><p>${rich(r.cells[1])}</p></div><div><h4>Bear position</h4><p>${rich(r.cells[2])}</p></div></div><p class="resolution">${rich(r.cells[4])}</p>${sourceFooter(`${module}:${r.line}`)}</section>`).join('')}</div>`;
  if(v.kind==='agencies')return `${chartIntro(module,v)}<div class="agency-pair">${table.rows.map(r=>`<section><h3>${esc(r.cells[0])}</h3><p class="rating">${rich(r.cells[1])}</p><h4>Proposed issue</h4><p>${rich(r.cells[2])}</p><p class="matrix-note">${rich(r.cells[3])}</p>${sourceFooter(`${module}:${r.line}`)}</section>`).join('')}</div>`;
  return `${chartIntro(module,v)}<div class="qual-matrix">${table.rows.map(row=>`<section><h3>${rich(row.cells[v.columns[0]])}</h3><div>${v.columns.slice(1).map(c=>`<div><h4>${esc(table.headers[c])}</h4><p>${rich(row.cells[c])}</p></div>`).join('')}${sourceFooter(`${module}:${row.line}`)}</div></section>`).join('')}</div>`;
}
const CHART_RENDERERS={paired:comparisonChart,peers:comparisonChart,bars:comparisonChart,bridge:bridgeChart,waterfall:bridgeChart,paths:pathChart,hedges:hedgeChart};
const visualMarkup=(module,v)=>(CHART_RENDERERS[v.kind]||qualitativeVisual)(module,v);
const readerChart=(id,chart,chips=false)=>comparisonChart(id,{kind:'bars',...chart},0,chips);
function readerCharts(id,section) {
  const lines=new Set(sectionData(id,section).flatMap(s=>s.blocks).map(b=>b.line));
  return (data[id].charts||[]).filter(c=>lines.has(c.table)).map(c=>readerChart(id,c)).join('');
}

// ---- The module report: six parts in one scroll. Python resolves every citation into window.CREDIT_OS_DATA.chips;
// nothing below infers a page, a class or a date.
const REPORT_PARTS=[['head','Module'],['bottom-line','Bottom line'],['numbers','Key numbers'],['findings','Findings'],['limits','Limits & monitoring'],['audit','Evidence & audit']];
const EMPTY_PART={'bottom-line':'No bottom line in this handoff.',numbers:'No chart data or key-number table in this handoff.',findings:'No findings table in this handoff.',limits:'No gap, limit or monitoring section in this handoff.'};
const SHORT_CODES={'CP-1':'C1','CP-1A':'A','CP-0':'C0','CP-2':'C2'};
const shortCode=module=>SHORT_CODES[module]||String(module).replace(/^CP-/,'');
// What a chip draws, from the chip dict as the library build emits it. An upstream chip with no module names register codes of the row's own module.
function chipView(chip,rowModule) {
  if(chip.kind==='issuer_page') {
    const pages=chip.page_end!=null&&chip.page_end!==chip.page?`p.${chip.page}–${chip.page_end}`:`p.${chip.page}`;
    return {label:pages,av:chip.source,avClass:'',dot:'',cls:''};
  }
  if(chip.kind==='upstream') {
    const codes=chip.codes.join(' · ');
    return {label:chip.module?`${chip.module} · ${codes}`:codes,av:chip.module||rowModule?shortCode(chip.module||rowModule):'?',avClass:'q',dot:'up',cls:''};
  }
  return {label:chip.label||'no page',av:'?',avClass:'gap',dot:'gap',cls:'gap'};
}
const chipSet=chips=>chips.length?`<span class="chips">${chips.join('')}</span>`:'';
// The "handoff row" chip comes from the evidence key itself; the others from the chips map, by index.
function chipsMarkup(key) {
  const item=evidence.get(key),found=window.CREDIT_OS_DATA?.chips?.[key]||[];
  const row=item?`<button type="button" class="chip" data-evidence="${esc(key)}" aria-label="Handoff row, line ${item.line}"><span class="av cp">${esc(shortCode(item.module))}</span>L${item.line}<span class="dot row"></span></button>`:'';
  return chipSet([row,...found.map((chip,index)=>{
    const view=chipView(chip,item?.module);
    return `<button type="button" class="chip ${view.cls}" data-chip="${esc(key)}" data-index="${index}" ${chip.reason?`title="${esc(chip.reason)}"`:''}><span class="av ${view.avClass}">${esc(view.av)}</span>${esc(view.label)}<span class="dot ${view.dot}"></span></button>`;
  })].filter(Boolean));
}
const MISSING_CELL=/^(|[—–-]|Not supplied)$/i;
const cellView=(cell,numeric)=>{
  const text=plain(cell??'').trim();
  if(MISSING_CELL.test(text))return `<td${numeric?' class="num"':''}><span class="na" title="${esc(text||'Empty in the handoff')}">n.a.</span></td>`;
  return `<td${numeric?' class="num"':''}>${rich(text)}</td>`;
};
const isFindingsTable=b=>b.type==='table'&&b.headers[0]==='Finding'&&b.headers[1]==='Creditor impact';
// The first reader table of the findings-and-analysis sections with two or more numeric columns, capped at 8 rows and 6 columns (5 handoff columns and the Source column).
function keyNumbers(id) {
  // The analysis group is the first group that is neither limits nor evidence, whatever the module names it.
  const reader=(sectionGroups(id).find(([group])=>group!=='Limits & monitoring'&&group!=='Evidence & audit')?.[1]||[]).flatMap(([sectionId])=>sectionData(id,sectionId));
  for(const section of reader) {
    if(section.heading.startsWith('Chart data'))continue;
    for(const block of section.blocks) {
      if(block.type!=='table'||isFindingsTable(block)||block.headers[0]==='Bottom line')continue;
      const numeric=block.headers.map((_,c)=>c>0&&block.rows.some(r=>chartNumber(r.cells[c]??'')!==null));
      if(numeric.filter(Boolean).length<2)continue;
      const short=block.headers.map((_,c)=>c===0||numeric[c]||block.rows.every(r=>(r.cells[c]??'').length<=24));
      const columns=block.headers.map((_,c)=>c).filter(c=>short[c]).slice(0,5),rows=block.rows.slice(0,8);
      return `<div class="table-card"><table><caption class="sr-only">${esc(plain(section.heading))}</caption><thead><tr>${columns.map(c=>`<th scope="col"${numeric[c]?' class="num"':''}>${esc(block.headers[c])}</th>`).join('')}<th scope="col">Source</th></tr></thead><tbody>${rows.map(row=>`<tr>${columns.map(c=>cellView(row.cells[c],numeric[c])).join('')}<td>${chipsMarkup(`${id}:${row.line}`)}</td></tr>`).join('')}</tbody></table>${block.rows.length>rows.length?`<p class="table-more">${block.rows.length-rows.length} more rows are under Evidence &amp; audit.</p>`:''}</div>`;
    }
  }
  return '';
}
const LEGEND='<div class="legend"><span>Chip dot: <i class="dot"></i> issuer page · <i class="dot row"></i> handoff row · <i class="dot up"></i> upstream module · <i class="dot gap"></i> gap</span></div>';
function reportHead(id) {
  const out=data[id],{module,run:context}=out,ctx=contexts[context];
  const {meta,usedIn,flag}=headTools(module,context,id);
  // No catalogue field says "accepted"; a run shows a checklist only when one is recorded (none is today), and that is not acceptance.
  const record=window.DESIGN_CATALOGUE.real.find(r=>r.id===ctx.folder);
  const acceptance=record?.checklist?'Acceptance checklist recorded':'Candidate · not accepted';
  const count=out.sections.filter(s=>s.blocks.length).length;
  return `<div class="module-head" id="head"><div><h2 title="${esc(module)}">${esc(moduleNames[module])}</h2><div class="sub"><span>${esc(module)}</span><span>·</span><span>Current methodology</span><span>·</span><span>Handoff <code>${esc(out.source.split('/').pop())}</code> · ${plural(count,'section')}</span></div></div><div class="head-tools"><span class="badge badge-gray">${acceptance}</span>${meta}${usedIn}${flag}<a class="btn" href="${esc(out.href)}" download>${icon('download')}Handoff</a></div></div>`;
}
function reportBand(id) {
  const {summary,call,source}=data[id],quoted=summary?{text:summary.bottomLine,line:summary.line}:call;
  if(!quoted)return `<p class="part-empty" id="bottom-line">${EMPTY_PART['bottom-line']}</p>`;
  const facts=summary?`<dl><span class="row"><dt>Confidence</dt><dd>${esc(summary.confidence)}</dd></span><span class="row"><dt>Main limitation</dt><dd>${rich(summary.limitation)}</dd></span></dl>`:'';
  return `<div class="band" id="bottom-line"><p>${rich(quoted.text.replace(/\n/g,' '))}</p>${facts}<div class="src"><span class="badge on-navy">Quoted from the handoff</span><button type="button" class="band-link" data-evidence="${esc(`${id}:${quoted.line}`)}">${esc(source.split('/').pop())} · line ${quoted.line}</button></div></div>`;
}
function reportNumbers(id) {
  const charts=(data[id].charts||[]).map(c=>`<div class="panel-card">${readerChart(id,c,true)}${LEGEND}</div>`).join(''),table=keyNumbers(id);
  return `<section class="part" id="numbers"><h3>Key numbers</h3>${charts||table?charts+table:`<p class="part-empty">${EMPTY_PART.numbers}</p>`}</section>`;
}
function reportFindings(id) {
  const articles=data[id].sections.flatMap(s=>s.blocks).filter(isFindingsTable).flatMap(block=>{
    const confidence=block.headers.indexOf('Confidence');
    return block.rows.map(row=>`<article class="finding"><div><h4>${rich(row.cells[0])}</h4><p class="impact"><b>Creditor impact</b>${rich(row.cells[1])}</p></div><aside>${confidence<0?'':`<span class="conf">Confidence<span class="pill">${esc(plain(row.cells[confidence]??''))}</span></span>`}${chipsMarkup(`${id}:${row.line}`)}</aside></article>`);
  });
  return `<section class="part" id="findings"><h3>Findings</h3>${articles.join('')||`<p class="part-empty">${EMPTY_PART.findings}</p>`}</section>`;
}
function limitsGroup(id) {return sectionGroups(id).find(([group])=>group==='Limits & monitoring')?.[1]||[];}
function reportLimits(id) {
  const line=(key,html)=>`<p>${html} ${chipsMarkup(key)}</p>`;
  const cards=limitsGroup(id).map(([sectionId,label])=>`<div><h4>${esc(label)}</h4>${sectionData(id,sectionId).flatMap(s=>s.blocks).flatMap(block=>block.type==='table'?block.rows.map(row=>line(`${id}:${row.line}`,`<strong>${rich(row.cells[0])}</strong> ${row.cells.slice(1).map(rich).join(' · ')}`)):[line(`${id}:${block.line}`,rich(block.text.replace(/\n/g,' ')))]).join('')}</div>`);
  return `<section class="part" id="limits"><h3>Limits &amp; monitoring</h3>${cards.length?`<div class="limits">${cards.join('')}</div>`:`<p class="part-empty">${EMPTY_PART.limits}</p>`}</section>`;
}
// Every section the parts above do not print in full, as a line-numbered list; a section's content is drawn when it is opened (screen.js).
function reportAudit(id) {
  const shown=new Set(limitsGroup(id).map(s=>s[0])),rest=modules[id].sections.filter(s=>!shown.has(s[0]));
  return `<details class="audit" id="audit"><summary>${icon('chevron-right')}Evidence &amp; audit<span>${plural(rest.length,'section')} · unchanged from the handoff</span></summary><ul class="audit-list">${rest.map(([sectionId,label])=>{
    const first=sectionData(id,sectionId)[0];
    return `<li><button type="button" class="audit-open" data-audit="${esc(sectionId)}" aria-expanded="false" aria-controls="audit-${esc(sectionId)}">${esc(label)}${first?`<span>L${first.line}</span>`:''}</button><div class="audit-body" id="audit-${esc(sectionId)}" hidden></div></li>`;
  }).join('')}</ul></details>`;
}
const moduleReport=id=>reportHead(id)+reportBand(id)+reportNumbers(id)+reportFindings(id)+reportLimits(id)+reportAudit(id);
function galleryVisual(module,section) {
  const out=data[module],v=out.visual;
  if(!v||!sectionData(module,section).some(s=>s.blocks.some(b=>b.line===v.table)))return '';
  return `<div id="module-visual">${visualMarkup(module,v)}</div>${visualCoversTable(module,fixtureTable(module,v.table))?'':'<div class="section-heading compact"><h2>Complete findings & exact data</h2><span>Retained output</span></div>'}`;
}
function visualCoversTable(module,block) {
  const {visual:v,summary}=data[module];
  if(block.type==='table'&&summary&&block.rows[0]?.line===summary.line)return true; // The band holds this row.
  return block.type==='table'&&v?.table===block.line&&(['agencies','debate'].includes(v.kind)||(v.kind==='matrix'&&new Set(v.columns).size===block.headers.length));
}
function comparisonView() {
  const id=pins['CP-8'],run=data[id].run,compare=data[id].compare,recheck=data[compare.recheck];
  const parts=heading=>sectionData(id,'comparison').find(s=>s.heading.startsWith(heading)).blocks;
  const tableOf=heading=>parts(heading).find(b=>b.type==='table'),notes=heading=>parts(heading).filter(b=>b.type==='text').map(b=>narrativeMarkup(id,b)).join('');
  const reportLink=reportId=>`<a class="text-action" href="${routeHref('W-Reports',reportId,null,run)}">${esc(reportName(window.DESIGN_WORKSPACE.reports.find(r=>r.id===reportId)))}${icon('arrow-right')}</a>`;
  const field=(table,row,i)=>`<div class="record-field"><h4>${esc(table.headers[i])}</h4><div>${rich(row.cells[i])}</div></div>`;
  const quoted=(blocks,pattern)=>blocks.filter(b=>b.type==='text').map(b=>b.text.replace(/\n/g,' ').match(pattern)?.[0]).find(Boolean);
  const heading=(title,count)=>`<div class="section-heading compact"><h2>${esc(title)}</h2><span>${count}</span></div>`;
  const changes=tableOf('All five report sections'),material=tableOf('Material analytical changes'),regressions=tableOf('Unresolved regressions');
  const recheckFindings=recheck.sections.find(s=>s.heading==='Findings').blocks,recheckRows=recheckFindings.find(b=>b.type==='table').rows;
  const recheckHref=routeHref('CP-8',modules[recheck.id].first,null,run,recheck.source);
  return `<div class="comparison-pair"><div><span>Prior</span>${reportLink(compare.prior)}</div><div><span>Current</span>${reportLink(compare.current)}</div><p>${esc(quoted(data[id].sections.find(s=>s.heading==='Request').blocks,/“Current” means[^.]+\./))}</p></div>${notes('Findings')}
  ${heading('All five report sections','Prior → current')}${changes.rows.map(row=>{
    const word=plain(row.cells[1]).match(/^(Unchanged|Revised)/)[1];
    return `<section class="debate change-row"><header><h3>${rich(row.cells[0])}</h3><span class="grade ${word==='Unchanged'?'unknown':'neutral'}">${word}</span></header>${[1,2,3].map(i=>field(changes,row,i)).join('')}${sourceFooter(`${id}:${row.line}`)}</section>`;
  }).join('')}
  ${heading('Material analytical changes','Prior and current deliverable')}${material.rows.map(row=>`<section class="debate"><header><h3>${rich(row.cells[0])}</h3></header><div class="arguments">${[1,2].map(i=>`<div><h4>${esc(material.headers[i])}</h4><p>${rich(row.cells[i])}</p></div>`).join('')}</div>${field(material,row,3)}${field(material,row,4)}${sourceFooter(`${id}:${row.line}`)}</section>`).join('')}
  ${heading('Unresolved regressions to repair','Requested from CP-2')}<div class="recheck"><p>${esc(quoted(recheckFindings,/RC-1\/2\/3 are closed[^.]+\./))}</p><a class="text-action" href="${recheckHref}">Read the recheck${icon('arrow-right')}</a>${reportLink(compare.repaired)}</div>${regressions.rows.map(row=>{
    const after=recheckRows.find(r=>plain(r.cells[0]).startsWith(plain(row.cells[0]).split(' ')[0]));
    return `<section class="debate regression-row"><header><h3>${rich(row.cells[0])}</h3><span class="grade neutral">${esc(plain(after.cells[2]))}</span></header>${field(regressions,row,1)}${field(regressions,row,2)}<div class="record-field"><h4>Recheck · ${esc(recheckFindings.find(b=>b.type==='table').headers[1])}</h4><div>${rich(after.cells[1])}</div></div>${sourceFooter(`${id}:${row.line}`)}</section>`;
  }).join('')}${notes('Unresolved regressions')}`;
}
function routeHref(module,section,key=null,context=current?.context,file=lastFile.get(`${context}:${module}`),chip=null) {
  const params=new URLSearchParams();
  if(context)params.set('c',context);
  if(file&&`${contexts[context].folder}/${file}`!==defaultOutput(module,context))params.set('o',file);
  if(key)params.set('e',key);
  if(key&&chip!==null)params.set('chip',String(chip));
  // A report id is a folder name: encoded, it can hold quotes, angle brackets, ? or # and still route back.
  return `#${encodeURIComponent(module)}/${encodeURIComponent(section)}${params.size?'?'+params:''}`;
}
function sectionGroups(id) {
  const result=new Map(),module=data[id].module;
  for(const section of modules[id].sections) {
    const [sectionId,label,prefixes]=section,heading=prefixes.join(' ');
    let group='Findings & analysis';
    if(sectionId==='audit'||/^(Sources|Scope &|Evidence &|Definitions & periods|Source register)/.test(label))group='Evidence & audit';
    else if(/gap|limit|monitor|follow-up|readiness/i.test(label))group='Limits & monitoring';
    else if(module==='CP-2E')group=heading.includes('T2G.')?'ESG & credit effects':heading.includes('T2F.')?'Rates, FX & hedges':'Credit conclusion';
    else if(module==='CP-1D')group=heading.includes('T1E.')?'Debt & obligations':'Earnings quality';
    else if(module==='CP-5')group=heading.includes('T5B.')?'Evidence lineage':'Validation & remediation';
    if(!result.has(group))result.set(group,[]);
    result.get(group).push(section);
  }
  return [...result];
}
function outlineMarkup(id) {
  const module=data[id].module||id;
  return `<nav class="section-outline" aria-label="On this page"><ol>${REPORT_PARTS.map(([part,label])=>`<li><a class="section-item" href="${routeHref(module,part)}" ${current.section===part?'aria-current="location"':''}>${esc(label)}</a></li>`).join('')}</ol></nav>`;
}
function unavailableView(module) {
  const ctx=contexts[current.context];
  const others=Object.entries(contexts).filter(([key,run])=>key!==current.context&&sameIssuer(run.issuerKey,ctx.issuerKey)&&run.modules[module]?.outputs.length);
  return `<div class="missing-state"><div class="empty-symbol">${icon('file-text')}</div><h2>${NO_OUTPUT}</h2></div>${others.length?`<div class="available-case"><h3>Other ${esc(ctx.issuer)} runs with this module</h3>${others.map(([key,run])=>`<p><a class="text-action" href="${routeHref(module,firstSection(module,key),null,key)}">${esc(run.run)}${icon('arrow-right')}</a></p>`).join('')}</div>`:''}`;
}
function outputChooser(module) {
  const ctx=contexts[current.context],files=moduleEntry(module,current.context).outputs;
  return `<div class="missing-state"><div class="empty-symbol">${icon('file-text')}</div><h2>Choose a saved output</h2><p>${files.length} versions of this analysis. Choose one to read.</p></div><div class="output-choices">${files.map(id=>`<a class="text-action" href="${routeHref(module,modules[id].first,null,current.context,data[id].source)}">${esc(data[id].label)}${icon('arrow-right')}</a>`).join('')}</div>`;
}
// Events come from the run's own CP-1A event table (calendar.js eventTable); no dates are inferred from other runs.
// The CP-1A output holding that table, default output first, or null.
function eventsOutput(context) {
  const entry=moduleEntry('CP-1A',context);
  return entry?[entry.default,...entry.outputs].find(id=>id&&eventTable(data[id].sections))||null:null;
}
const hedgesOutput=context=>{const entry=moduleEntry('CP-2E',context);return entry?.default||entry?.outputs[0]||null;};
// The first run that has the module's calendar source (route fallback when no run is chosen).
const calendarRun=module=>Object.keys(contexts).find(context=>module==='CP-1A'?eventsOutput(context):hedgesOutput(context));
function calendarSections(context) {
  const sections=[];
  if(eventsOutput(context))sections.push(['tdg','Issuer events',[]]);
  if(hedgesOutput(context))sections.push(['hedges','Hedge schedule',[]]);
  return sections.length?sections:[['unavailable','Calendar availability',[]]];
}
function forecastSections(context) {
  const models=runModels(context);
  return models.length?models.map(m=>[m.id,m.id,[]]):[['none','Forecast availability',[]]];
}
// The run's issuer reports, then any other report built from this run's files (parseRoute sends such a report to this run).
function runReports(context) {
  const own=issuerReports(context);
  return [...own,...(context?reportsBuiltFrom(context).filter(r=>!own.includes(r)):[])];
}
function reportSections(context) {
  const reports=runReports(context);
  return reports.length?[['list','Reports',[]],...reports.map(r=>[r.id,reportName(r),[]])]:[['none','Report availability',[]]];
}
function navigationSections(module,context,output=defaultOutput(module,context)) {
  if(module==='W-Calendar')return calendarSections(context);
  if(module==='W-Evidence')return [['sources','Retained outputs',[]]];
  if(module==='W-Reports')return reportSections(context);
  if(module==='W-Forecast')return forecastSections(context);
  if(isAnalytical(module)&&output)return REPORT_PARTS.map(([part,label])=>[part,label,[]]);
  if(Object.hasOwn(modules,module))return modules[module].sections;
  return [['status',moduleEntry(module,context)?.outputs.length?'Choose a saved output':availability(module,context),[]]];
}
function moduleLink(id,label){return `<a class="text-action" href="${routeHref(id,lastSection.get(current?.context+':'+id)||firstSection(id,current?.context))}">${esc(label||moduleNames[id])}${icon('arrow-right')}</a>`;}
// Rows repeat the same two actions, so each is an icon; its accessible name and tooltip still say what it does.
const iconAction=(action,target,href,name,download=false)=>`<a class="icon-action" href="${esc(href)}" ${download?'download':''} aria-label="${esc(`${action}: ${target}`)}" title="${action}">${icon(name)}</a>`;
// A module with no name keeps its code alone.
const nameThenCode=code=>moduleNames[code]&&moduleNames[code]!==code?`${moduleNames[code]} · ${code}`:code;
function sourceInventory(context) {
  const identity=f=>`<details><summary>File identity</summary><p>${esc(f.file)}</p><p class="hash">SHA-256 ${f.sha256}</p></details>`;
  const rows=Object.entries(contexts[context].modules).flatMap(([module,entry])=>[
    ...entry.outputs.map(id=>{const out=data[id];return `<section><div><h3>${esc(nameThenCode(module))}</h3><p>${esc(out.label)}</p>${out.scope==='Retained module output'?'':`<span class="badge badge-gray">${esc(out.scope)}</span>`}</div><div>${iconAction('Open output',`${module} ${moduleNames[module]}, ${out.label}`,routeHref(module,modules[id].first,null,context,out.source),'arrow-right')}${iconAction('Download original handoff',`${module} ${moduleNames[module]}, ${out.label}`,out.href,'download',true)}</div>${identity(out)}</section>`;}),
    ...entry.inputs.map(id=>{const f=store.inputs[id];return `<section><div><h3>${esc(nameThenCode(module))}</h3><p>${esc(f.source)}</p><span class="badge badge-gray">Input</span></div><div>${iconAction('Download original file',`${module} ${moduleNames[module]}, ${f.source}`,f.href,'download',true)}</div>${identity(f)}</section>`;})
  ]);
  if(!rows.length)return `<div class="missing-state"><div class="empty-symbol">${icon('file-text')}</div><h2>No retained files for this run</h2><p>No module outputs or inputs were found in this run’s folder.</p></div><a class="text-action switch-case" href="#W-Library/cases">Choose another case</a>`;
  return `<div class="source-inventory">${rows.join('')}</div>`;
}
const badge=(kind,text)=>`<span class="badge badge-${kind}">${esc(text)}</span>`;
// The acceptance state a report declares, as the badge and muted qualification text every report listing shows.
const QUALIFICATIONS=['unrun','partial','qualified','blocked'];
function reportAcceptance(report) {
  const candidate=report.mode==='candidate';
  const state=report.mode==='accepted'?'Accepted':candidate?'Candidate · not accepted':'Acceptance not recorded';
  const qualification=report.qualification==='unrun'?'Analytical qualification: not run':QUALIFICATIONS.includes(report.qualification)?`Analytical qualification: ${report.qualification}`:'Analytical qualification not recorded';
  return {state,qualification,html:`<span class="acceptance">${badge('gray',state)} <span class="muted">${esc(qualification)}</span></span>`};
}
function forecastEmpty(context) {
  const ctx=contexts[context],others=publishedModels().filter(m=>sameIssuer(m.issuerKey,ctx.issuerKey)).sort(byModelId);
  const row=m=>{const run=modelOwnRun(m);return `<li class="report-row">${run?`<a class="text-action" href="${routeHref('W-Forecast',m.id,null,run)}">${esc(m.id)}${icon('arrow-right')}</a>`:`<span>${esc(m.id)}</span>`} ${reportAcceptance(m).html}</li>`;};
  return `<div class="missing-state"><div class="empty-symbol">${icon('file-text')}</div><h2>No forecast model was published from this run’s files</h2></div>${others.length?`<section class="forecast-other"><h2>Other ${esc(ctx.issuerHeading)} models</h2><ol class="report-list">${others.map(row).join('')}</ol></section>`:''}`;
}
// A percent or multiple cell's title: the value in its display unit at four decimals, half away from zero, "≈ " when rounding changed it.
function ratioTitle(exact,kind) {
  const found=/^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(exact);
  if(!found||Math.abs(Number(found[4]||0))>400)return exact;
  const frac=found[3]||'',shift=Number(found[4]||0)+(kind==='percent'?2:0);
  const digits=BigInt(found[2]+frac),scale=frac.length-shift;
  let units,exactly=true;
  if(scale<=4)units=digits*10n**BigInt(4-scale);
  else{const divisor=10n**BigInt(scale-4);units=digits/divisor;const rest=digits%divisor;exactly=rest===0n;if(rest*2n>=divisor)units+=1n;}
  const negative=found[1]==='-'&&units!==0n,text=units.toString().padStart(5,'0');
  return `${exactly?'':'≈ '}${negative?'-':''}${text.slice(0,-4)}.${text.slice(-4)}${kind==='percent'?'%':'x'}`;
}
// One cell's title: the exact amount (ratios in their display unit), else the reason it has no value.
const cellTitle=(cell,kind)=>cell.exact!=null?(kind==='percent'||kind==='multiple'?ratioTitle(cell.exact,kind):cell.exact):cell.reason;
// "Not available" lines: one per row and reason, naming the periods; a repeated column label takes its group's name.
function notAvailableLines(c) {
  const counts=new Map();
  for(const col of c.columns)counts.set(col.label,(counts.get(col.label)||0)+1);
  const period=col=>counts.get(col.label)>1?`${col.label} ${col.group.replace(/\s*\([^()]*\)$/,'')}`:col.label;
  const lines=[];
  for(const row of c.rows){
    const pairs=new Map();
    row.cells.forEach((cell,i)=>{
      if(cell.status!=='na')return;
      const list=pairs.get(cell.reason)||pairs.set(cell.reason,[]).get(cell.reason);
      list.push(period(c.columns[i]));
    });
    for(const [reason,periods] of pairs)lines.push(`Not available: ${row.label} — ${periods.join(', ')}${reason==null?'':`: ${reason}`}`);
  }
  return lines;
}
// The calculation record as a line-item by period grid. The store formatted every cell; this only places it.
function cashflowSection(model) {
  const c=model.cashflow;
  if(!c)return '<section class="forecast-cashflow"><h2>Cash flow model</h2><p>This model has no readable calculation record.</p></section>';
  const groups=[];
  for(const col of c.columns){const last=groups[groups.length-1];if(last&&last.name===col.group)last.span++;else groups.push({name:col.group,span:1});}
  // The first column of each group carries a rule; the Base case and Downside columns sit on a quiet ground.
  const scenario=name=>/^(Base case|Downside)/.test(name),starts=c.columns.map((col,i)=>i===0||c.columns[i-1].group!==col.group);
  const colClass=i=>[starts[i]?'group-start':'',scenario(c.columns[i].group)?'scenario':''].filter(Boolean).join(' '),attr=cls=>cls?` class="${cls}"`:'';
  const head=`<tr><th scope="col" rowspan="2">Line item</th>${groups.map(g=>{const at=c.columns.findIndex(col=>col.group===g.name);return `<th scope="colgroup" colspan="${g.span}"${attr(colClass(at))}>${esc(g.name)}</th>`;}).join('')}</tr><tr>${c.columns.map((col,i)=>`<th scope="col"${attr(colClass(i))}${col.start==null||col.end==null?'':` title="${esc(`${displayDate(col.start)} to ${displayDate(col.end)}`)}"`}>${col.ytd&&col.label.endsWith(' (YTD)')?`${esc(col.label.slice(0,-6))} <span class="col-sub">(YTD)</span>`:esc(col.label)}</th>`).join('')}</tr>`;
  const td=(cell,kind,i)=>{
    const title=cellTitle(cell,kind),label=cell.status==='na'?`n.a.${cell.reason==null?'':`: ${cell.reason}`}`:cell.status==='nm'?'n.m.: not modelled in the calculation record':null;
    return `<td${attr(colClass(i))}${title==null?'':` title="${esc(title)}"`}${label==null?'':` aria-label="${esc(label)}"`}>${esc(cell.display)}</td>`;
  };
  let band=null,body='';
  for(const row of c.rows){
    if(row.band!==band){band=row.band;body+=`<tr class="band-row"><th scope="colgroup" colspan="${c.columns.length+1}">${esc(band)}</th></tr>`;}
    body+=`<tr${row.total?' class="total-row"':''}><th scope="row">${esc(row.label)}</th>${row.cells.map((cell,i)=>td(cell,row.kind,i)).join('')}</tr>`;
  }
  const na=notAvailableLines(c),first=c.columns[0],last=c.columns[c.columns.length-1];
  const caption=[c.units==null?'Units not recorded':c.units,...first?[`${first.label} to ${last.label}`]:[],'history as retained in the handoffs; forecasts are conditional illustrations from the calculation record'].join(' · ');
  return `<section class="forecast-cashflow"><h2 id="cashflow-heading">Cash flow model</h2><p class="forecast-caption">${esc(caption)}</p><div class="table-scroll" role="region" aria-labelledby="cashflow-heading" tabindex="0"><table class="cashflow"><thead>${head}</thead><tbody>${body}</tbody></table></div>${c.notes.length?`<ul class="cashflow-notes">${c.notes.map(line=>`<li>${esc(line)}</li>`).join('')}</ul>`:''}${na.length?`<details class="cashflow-na"><summary>Why cells show n.a. (${na.length} lines)</summary><ul>${na.map(line=>`<li>${esc(line)}</li>`).join('')}</ul></details>`:''}</section>`;
}
// The roles a delivery's sources are declared under; an unknown role shows its own token.
const SOURCE_ROLES={annual:'Annual handoff',quarter:'Quarterly handoff',forecast:'Forecast handoff',forecast_exact:'Forecast calculations',current_synthesis:'Current synthesis'};
const sourceFile=s=>(s.output||s.path||'').split('/').at(-1);
// A fact, not a judgement: sources whose file names carry different attempt numbers.
function attemptNote(sources) {
  const named=[...new Set(sources.map(sourceFile).filter(f=>/-attempt-\d+/.test(f)))];
  const attempt=f=>/-attempt-(\d+)/.exec(f)[1];
  if(new Set(named.map(attempt)).size<2)return '';
  return `<p class="forecast-attempts">${esc(`These files come from different attempts: ${named.map(f=>`${f} (attempt ${attempt(f)})`).join(', ')}`)}</p>`;
}
function forecastView(context,id) {
  const models=runModels(context);
  if(!models.length)return forecastEmpty(context);
  const model=models.find(m=>m.id===id)||models[0];
  const acceptance=reportAcceptance(model);
  const select=`<label for="model-select">Model</label><select id="model-select">${models.map(m=>`<option value="${esc(m.id)}" ${m.id===model.id?'selected':''}>${esc(`${m.id} · ${modelRelationship(m,models)}`)}</option>`).join('')}</select>`;
  const why=`<section class="forecast-why"><h2>Why this model was built</h2>${model.scope==null?'':`<p class="forecast-scope">${esc(model.scope)}</p>`}${model.inputContract==null?'':`<p class="forecast-input">${esc(`Input contract: ${model.inputContract}`)}</p>`}${model.revisionNote==null?'':`<p class="forecast-revision">${esc(`Revision note: ${model.revisionNote}`)}</p>`}</section>`;
  const forecast=model.sources.find(s=>s.role==='forecast'),register=model.register;
  const full=forecast?.output?`<a class="text-action" href="${routeHref(data[forecast.output].module,modules[forecast.output].first,null,forecast.run,data[forecast.output].source)}">Open the full forward credit model output${icon('arrow-right')}</a>`:'';
  const assumptions=`<section class="forecast-assumptions"><h2>Assumptions and their rationale</h2>${register?`<h3>${esc(register.heading)}</h3>${register.intro==null?'':`<p class="register-intro">${esc(register.intro)}</p>`}${register.headers.length?`<div class="table-scroll"><table><thead><tr>${register.headers.map(c=>`<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${register.rows.map(r=>`<tr>${r.map(c=>`<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:''}${full}`:'<p>This model’s forecast handoff has no assumption register.</p>'}</section>`;
  const source=s=>s.output?`<a href="${routeHref(data[s.output].module,modules[s.output].first,null,s.run,data[s.output].source)}">${esc(s.output.split('/').at(-1))}</a>`:`<span title="${esc(s.path)}">${esc(sourceFile(s))}</span>`;
  // The run is the folder the delivery declares the file under, so every source names one the same way.
  const run=s=>{const id=/^runs\/([^/]+)\//.exec(s.path||'')?.[1];return id?`<span class="code">${esc(id)}</span>`:'<span class="muted">Not recorded</span>';};
  const status=s=>s.sha256===null?badge('attention','Invalid path or hash'):s.changed?badge('attention','Changed since publication'):badge('gray','Matches publication');
  const built=`<section class="forecast-built"><h2>Built from</h2><div class="table-scroll"><table><thead><tr><th scope="col">Role</th><th scope="col">Run</th><th scope="col">Source</th><th scope="col">SHA-256 prefix</th><th scope="col">Status</th></tr></thead><tbody>${model.sources.map(s=>`<tr><th scope="row">${esc(Object.hasOwn(SOURCE_ROLES,s.role)?SOURCE_ROLES[s.role]:s.role)}</th><td>${run(s)}</td><td>${source(s)}</td><td>${s.sha256===null?'':esc(s.sha256.slice(0,12))}</td><td>${status(s)}</td></tr>`).join('')}</tbody></table></div>${attemptNote(model.sources)}</section>`;
  return `<div class="forecast"><div class="report-tools forecast-tools">${select}${acceptance.html}<a href="${esc(model.download)}" download>Download original HTML</a></div>${cashflowSection(model)}${assumptions}${model.cashflow?`<section class="forecast-limits"><h2>Model limitations</h2><ul>${model.cashflow.limits.map(l=>`<li>${esc(l)}</li>`).join('')}</ul></section>`:''}${why}${built}<details class="model-original"><summary>Published model (original HTML)</summary><div class="frame-host"><p class="frame-status" role="status" hidden></p><iframe id="model-preview" data-download="${esc(model.download)}" data-src="${esc(model.href)}" title="${esc(model.id)} · published model" sandbox="allow-scripts allow-downloads" referrerpolicy="no-referrer"></iframe></div></details></div>`;
}
// The Library screen. The served catalogue (window.DESIGN_CATALOGUE) is screened and sorted by LibraryLogic (screening.js); this places it. Nothing here calculates, converts or rescales a value.
const METRIC_NAMES={revenue:'Revenue',ebitda:'EBITDA',leverage:'Leverage',net_leverage:'Net leverage',coverage:'Interest coverage',cash:'Closing cash',undrawn:'Undrawn facilities',cashflow:'Cash flow measure'};
const LIBRARY_COLUMNS=[['name','Issuer / run'],[null,'Sector'],['date','Evidence date'],['leverage','Leverage'],['coverage','Coverage'],['completion','Completeness'],['net_leverage','Net leverage'],['rating','Rating'],[null,'Deliverable']];
const TERM_LABELS={size_m:'Size',tenor_years:'Tenor',talk_spread_bps_low:'Spread talk, low',talk_spread_bps_high:'Spread talk, high',talk_oid_low:'OID talk, low',talk_oid_high:'OID talk, high',floor_pct:'Floor',coupon_pct:'Coupon',margin_bps:'Margin',bid:'Bid',ask:'Ask',price:'Price',yield_pct:'Yield',spread_bps:'Spread'};
const CLASSIFICATIONS={investment_grade:'Investment grade',high_yield:'High yield'},RATING_SCOPES={issuer:'Issuer',facility:'Facility'};
// Coverage group names as the screen says them; the first four hold no figure, so their hidden rows have none recorded.
const COVERAGE_NAMES={classification:'Classification',currency:'Currency',rating:'Rating',limitation:'Accepted limitations',leverage:'Leverage',net_leverage:'Net leverage',coverage:'Interest coverage',cash:'Cash',undrawn:'Undrawn facilities',talk:'Spread talk',margin:'Margin',coupon:'Coupon',price:'Price',yield:'Yield'};
const LIBRARY_GROUPS={metric:['basis','period','leverageMin','leverageMax','coverageMin','coverageMax','netLeverageMin','netLeverageMax','cashMin','cashMax','undrawnMin','undrawnMax'],rating:['classification','currency','ratingBelow','ratingAbove','ratingScope'],deal:['talkMin','talkMax','marginMin','marginMax','couponMin','couponMax','priceMin','priceMax','yieldMin','yieldMax'],limit:['limitation']};
const catalogueRuns=()=>window.DESIGN_CATALOGUE?.real||[];
// A date that is not a real calendar day is shown as served, never as another day.
function libraryDate(value) {
  if(!value)return '—';
  const day=new Date(`${value}T12:00:00Z`);
  return Number.isNaN(day.getTime())||day.toISOString().slice(0,10)!==value?String(value):day.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'});
}
// Only a same-origin path is linked; a record cannot send the reader elsewhere.
const libraryPath=href=>/^\/[^/\\]/.test(href??'');
// A value as served: grouping and its own decimals only; no value is missing-as-zero.
function libraryMetric(metric) {
  if(LibraryLogic.numberOf(metric)===null)return '—';
  if(metric.unit==='x')return `${metric.value}×`;
  const decimals=(String(metric.value).split('.')[1]||'').length;
  if(decimals>20)return String(metric.value); // beyond what the formatter takes: shown exactly as served
  return Number(metric.value).toLocaleString('en-GB',{minimumFractionDigits:decimals,maximumFractionDigits:decimals});
}
// A catalogue row joins the store by folder: a match opens that run's Overview; no match keeps the row without the link.
const libraryRunKey=run=>Object.keys(contexts).find(key=>contexts[key].folder===run.id)??null;
const primaryArtifact=run=>run.artifacts.find(a=>a.available&&a.state!=='superseded');
// A pinned report or published model the store holds opens inside the app; any other file opens in its own tab.
function libraryArtifactLink(artifact,key,text,cls,aria='') {
  const pinned=`${artifact.href}&embedded=1`,report=window.DESIGN_WORKSPACE.reports.find(r=>r.href===pinned);
  const model=window.DESIGN_WORKSPACE.models.find(m=>m.href===pinned),owner=model&&modelOwnRun(model);
  const inApp=report?routeHref('W-Reports',report.id,null,key&&sameIssuer(report.issuerKey,contexts[key].issuerKey)?key:tracedRun(report)):owner?routeHref('W-Forecast',model.id,null,owner):null;
  const href=inApp??(libraryPath(artifact.href)?artifact.href:null);
  if(!href)return `<span>${esc(text)}</span>`;
  return `<a class="${cls}" href="${esc(href)}" ${inApp?'':'target="_blank" rel="noopener"'} ${aria?`aria-label="${esc(aria)}"`:''}>${esc(text)}${inApp?'':' ↗'}</a>`;
}
const libraryOpenText=artifact=>artifact.kind==='model'?'Open model':artifact.relationship==='related'?'Related report':'Open report';
function libraryRows() {
  const runs=catalogueRuns(),f={...libraryFilters};
  // Search also reads the issuer name and terms the store recorded for the joined run, appended to the title the search reads; counts, hidden rows and the list all see the same text.
  const shadows=runs.map(run=>{const held=contexts[libraryRunKey(run)];return {...run,title:[run.title,held?.issuer,...(held?.issuerTerms||[])].filter(Boolean).join(' ')};});
  const original=new Map(runs.map(run=>[run.id,run])),back=list=>list.map(run=>original.get(run.id));
  const coverage=LibraryLogic.coverage(shadows,f);
  if(!Object.hasOwn(coverage,libraryState.hidden))libraryState.hidden='';
  const entries=LibraryLogic.screened(shadows,f),skipped=new Set(entries.filter(e=>e.notScreened).map(e=>e.run.id));
  const matching=back(libraryState.hidden?LibraryLogic.hiddenBy(shadows,f,libraryState.hidden):entries.map(e=>e.run)); // "Show them" lists exactly the logic's hidden rows
  const rows=libraryState.sortKey?LibraryLogic.sortRuns(matching,libraryState.sortKey,libraryState.direction,f):matching;
  if(!rows.some(r=>r.id===libraryState.selected))libraryState.selected=rows[0]?.id??'';
  const unscreened=f.runs==='any'?0:LibraryLogic.filterRuns(shadows,{...f,runs:'any'}).length-entries.length; // rows Any run would add under these filters
  return {runs,rows,skipped,coverage,unscreened,hidden:libraryState.hidden};
}
// Runs grouped by issuer, case-insensitively, in order of first appearance.
const issuerGroups=runs=>[...runs.reduce((m,r)=>m.set(LibraryLogic.issuerKey(r.issuer),[...(m.get(LibraryLogic.issuerKey(r.issuer))||[]),r]),new Map()).values()];
const libraryCount=({runs,rows,hidden})=>hidden?`${plural(rows.length,'run')} hidden by ${COVERAGE_NAMES[hidden]} · not matching these filters`:`${rows.length} of ${plural(runs.length,'run')} · ${plural(issuerGroups(rows).length,'issuer')}`;
function libraryCoverage({runs,coverage,unscreened}) {
  const lines=Object.entries(coverage).map(([group,{recorded,hidden}])=>`<p data-library-coverage="${group}">${esc(`${COVERAGE_NAMES[group]} recorded for ${recorded} of ${plural(runs.length,'run')}`)}${hidden?` · ${hidden} hidden · <button class="tertiary-action" type="button" data-library-hidden="${group}">Show them</button>`:''}</p>`);
  if(unscreened)lines.push(`<p>${esc(`${plural(unscreened,'run')} not screened by the Latest run rule · choose Any run to show them`)}</p>`);
  return lines.join('');
}
const libraryCell=(primary,secondary,cls='')=>`<td><span class="cell-primary${cls}">${esc(primary)}</span><span class="cell-secondary">${esc(secondary)}</span></td>`;
const libraryMetricCell=(run,key)=>libraryCell(libraryMetric(run.metrics[key]),run.metrics[key]?.basis||'Not available',run.metrics[key]?'':' missing');
function libraryCompletion(run) {
  if(run.completion===null)return libraryCell('Not assessed','Checklist required');
  const done=run.checkpoints?`${run.checkpoints.done}/${run.checkpoints.total} requirements`:'';
  return `<td><span class="cell-primary">${esc(run.completion)}%</span><span class="progress-track" aria-hidden="true"><i style="width:${esc(Number(run.completion))}%"></i></span><span class="cell-secondary">${esc(done)}</span></td>`;
}
const libraryRatingText=r=>[r.agency||'Agency not recorded',RATING_SCOPES[r.scope]||'Scope not recorded',libraryDate(r.date)].join(' · ');
function libraryRatingCell(run) {
  const lowest=LibraryLogic.lowestRating(run,libraryFilters.ratingScope);
  return lowest?libraryCell(lowest.label,libraryRatingText(lowest)):libraryCell('—','Not recorded',' missing');
}
function libraryRow(run,selected,skipped) {
  const key=libraryRunKey(run),artifact=primaryArtifact(run),tags=[CLASSIFICATIONS[run.classification],run.private_side===true&&'Private-side',skipped&&'No report · not screened'].filter(Boolean).join(' · ');
  const identity=`<td><button class="library-run-name" type="button" data-library-select="${esc(run.id)}" aria-expanded="${selected}" aria-controls="run-detail" aria-label="${esc(`View ${run.name}: ${run.title}`)}">${esc(run.name)}<span class="ticker">${esc(run.issuer)}</span></button><span class="cell-secondary">${esc(run.title)}</span>${tags?`<span class="cell-secondary">${esc(tags)}</span>`:''}${key?`<a class="run-link" href="${routeHref('W-Overview','overview',null,key)}" aria-label="${esc(`Open run: ${run.name}, ${run.id}`)}">Open run</a>`:''}</td>`;
  const deliverable=artifact?`<td>${libraryArtifactLink(artifact,key,libraryOpenText(artifact),'report-link',`${libraryOpenText(artifact)}: ${run.name}, ${artifact.label}`)}<span class="cell-secondary">Candidate HTML</span></td>`:libraryCell('Handoffs only','No report');
  return `<tr${selected?' class="selected"':''}>${identity}<td>${esc(run.sector)}</td>${libraryCell(libraryDate(run.date),run.period)}${libraryMetricCell(run,'leverage')}${libraryMetricCell(run,'coverage')}${libraryCompletion(run)}${libraryMetricCell(run,'net_leverage')}${libraryRatingCell(run)}${deliverable}</tr>`;
}
function libraryResults({runs,rows,skipped,hidden}) {
  if(!runs.length)return window.DESIGN_APP?.problem?`<div class="library-empty"><h2>The library could not read this workspace</h2><p>Nothing can be listed until its data file loads. Rebuild the data file and open this page again.</p></div>`:`<div class="library-empty"><h2>No runs in this workspace yet</h2><p>The data file holds no retained runs.</p></div>`;
  if(!rows.length)return '<div class="library-empty"><h2>No runs match these filters</h2><p>Try a wider range or include unavailable values. Workflow completeness is not assessed for retained runs.</p><button id="library-empty-reset" class="primary-action" type="button">Reset filters</button></div>';
  const sort=key=>libraryState.sortKey===key?libraryState.direction==='asc'?'ascending':'descending':'none';
  const head=LIBRARY_COLUMNS.map(([key,label])=>key?`<th scope="col" aria-sort="${sort(key)}"><button type="button" data-library-sort="${key}">${label} <span aria-hidden="true">↕</span></button></th>`:`<th scope="col">${label}</th>`).join('');
  const heading=hidden?`<div class="hidden-head"><h2 id="library-hidden-title" tabindex="-1">${esc(`Hidden by ${COVERAGE_NAMES[hidden]}: ${['classification','currency','rating','limitation'].includes(hidden)?'not':'no figure'} recorded`)}</h2><button type="button" class="secondary-action" data-library-back>Back to results</button></div>`:'';
  return `${heading}<div class="table-scroll" role="region" aria-label="Issuer runs table; scroll horizontally for all columns" tabindex="0"><table class="library-table"><caption class="sr-only">Issuer runs, credit metrics, completeness and report availability</caption><thead><tr>${head}</tr></thead><tbody>${rows.map(r=>libraryRow(r,r.id===libraryState.selected,skipped.has(r.id))).join('')}</tbody></table></div><p class="hint">Dates refer to evidence, not execution. Ratios keep their original definitions.</p>`;
}
function libraryNav() {
  const runs=catalogueRuns(),f=libraryFilters,reports=runs.filter(LibraryLogic.hasReport).length,issuers=issuerGroups(runs);
  const choice=(attrs,active,label,count,mark='')=>`<button type="button" class="nav-choice${active?' active':''}" ${attrs} aria-pressed="${active}">${mark}<span>${esc(label)}</span><span class="count">${count}</span></button>`;
  return `${choice('data-library-nav="all"',!f.issuer&&!f.availability,'All runs',runs.length)}${choice('data-library-nav="reports"',f.availability==='report',`Reports available`,reports)}<p class="eyebrow">Issuers · ${issuers.length}</p>${issuers.map(mine=>{
    const id=mine[0].issuer,names=new Set(mine.map(r=>r.name));
    return choice(`data-library-issuer="${esc(id)}" aria-label="${esc(`Filter ${names.size===1?mine[0].name:id}`)}"`,LibraryLogic.issuerKey(f.issuer)===LibraryLogic.issuerKey(id),names.size===1?mine[0].name:id,mine.length,`<span class="monogram">${esc(id.slice(0,3))}</span>`);
  }).join('')}`;
}
function librarySources(run) {
  const sources=window.DESIGN_CATALOGUE?.sources||{};
  const ids=[...new Set([run.identity_source,run.sector_source,run.classification_source,run.private_side_source,...Object.values(run.metrics).map(m=>m?.source),...run.ratings.map(r=>r.source),...libraryTerms(run).map(([,m])=>m.source)].filter(Boolean))];
  const block=id=>{
    const s=Object.hasOwn(sources,id)?sources[id]:null;
    if(!s)return `<div id="source-${esc(id)}" tabindex="-1"><p>${esc(id)} · source record not served</p></div>`;
    const quote=String(s.quote);
    return `<div id="source-${esc(id)}" tabindex="-1"><p>${esc(`${s.path} · line ${s.line}`)}</p><blockquote>${esc(quote.length>1500?`${quote.slice(0,1500)}… [full capture in linked file]`:quote)}</blockquote>${libraryPath(s.href)?`<a href="${esc(s.href)}" target="_blank" rel="noopener">Open retained source ↗</a>`:''}</div>`;
  };
  return `<details class="source-details" id="metric-sources"><summary>Sources &amp; definitions · ${ids.length} references</summary>${ids.map(block).join('')}</details>`;
}
// The pinned line opens in the evidence inspector when the joined run holds that file as a module output and the evidence map has the line; otherwise the Sources & definitions entry.
function librarySourceAction(run,id) {
  const sources=window.DESIGN_CATALOGUE?.sources||{},source=id&&Object.hasOwn(sources,id)?sources[id]:null,key=libraryRunKey(run);
  const output=source&&key?String(source.path).replace(/^runs\//,''):'',line=`${output}:${source?.line}`;
  if(Object.hasOwn(data,output)&&data[output].run===key&&evidence.has(line))return `<a class="tertiary-action" href="${routeHref(data[output].module,modules[output].first,line,key,data[output].source)}">View source ↗</a>`;
  return id?`<button class="tertiary-action" type="button" data-library-source="${esc(id)}">View source ↗</button>`:'';
}
// Every facility term and quote term as served: [field, Metric].
const libraryTerms=run=>(run.facilities||[]).flatMap(f=>[f.terms,...(f.quotes||[]).map(q=>q.terms)]).flatMap(terms=>Object.entries(terms||{}));
function libraryMetricItem(run,name,metric) {
  return `<div class="metric-item"><span class="metric-label">${esc(name)}</span><span class="metric-value">${esc(libraryMetric(metric))}${metric&&metric.unit!=='x'&&LibraryLogic.numberOf(metric)!==null?`<small>${esc(metric.unit)}</small>`:''}</span><p>${esc(metric?`${metric.period} · ${metric.basis}`:'Not established for this case.')}</p>${metric?.provenance==='user'?'<p>Entered by the user · shown as entered</p>':''}${librarySourceAction(run,metric?.source)}</div>`;
}
const libraryTermItems=(run,terms)=>Object.entries(terms||{}).map(([field,metric])=>libraryMetricItem(run,TERM_LABELS[field]||field,metric)).join('');
const libraryFacilities=run=>run.facilities?.length?`<h3>Facilities &amp; quotes as entered</h3>${run.facilities.map(f=>`<section class="facility"><h4>${esc(f.facility_id)}</h4><div class="metric-grid">${libraryTermItems(run,f.terms)}</div>${(f.quotes||[]).map(q=>`<h5>${esc(`Quote · ${q.kind}`)}</h5><div class="metric-grid">${libraryTermItems(run,q.terms)}</div>`).join('')}</section>`).join('')}`:'';
function libraryDetail({rows}) {
  const run=rows.find(r=>r.id===libraryState.selected);
  if(!run)return '';
  const key=libraryRunKey(run),artifact=primaryArtifact(run);
  const open=[key?`<a class="secondary-action" href="${routeHref('W-Overview','overview',null,key)}">Open run</a>`:'',artifact?libraryArtifactLink(artifact,key,libraryOpenText(artifact),'primary-action'):libraryPath(run.handoff_href)?`<a class="primary-action" href="${esc(run.handoff_href)}" target="_blank" rel="noopener">Open primary handoff ↗</a>`:''].join('');
  const done=run.completion===null?['Workflow completeness · Not assessed','A verified checklist for this workflow has not been supplied. Available files and checked ratios do not establish end-to-end completion.']:[`Workflow completeness · ${run.completion}%`,run.checkpoints?`${run.checkpoints.done} of ${run.checkpoints.total} required checkpoints completed. This is workflow progress, not a credit score.`:'This is workflow progress, not a credit score.'];
  const artifacts=run.artifacts.length?run.artifacts.map(a=>`<li>${a.available?libraryArtifactLink(a,key,a.label,''):`<span>${esc(a.label)} · Unavailable</span>`}<small>${esc(a.issue||(a.state==='superseded'?'Retained failed attempt':`${a.relationship==='related'?'Related annual report · ':''}Candidate · file hashes checked at build`))}</small></li>`).join(''):'<li>No final deliverable has been indexed for this case.</li>';
  return `<div class="detail-head"><div><p class="eyebrow">Selected run</p><h2>${esc(run.name)}</h2><p class="cell-secondary">${esc(`${run.id} / ${run.title}`)}</p></div><div class="detail-actions">${open}</div></div><div class="detail-layout"><div><p>${esc(run.summary)}</p><h3>Scope &amp; open questions</h3><ul class="gap-list">${run.gaps.map(g=>`<li>${esc(g)}</li>`).join('')}</ul><h3>Classification &amp; currency</h3>${[['Classification',CLASSIFICATIONS[run.classification],run.classification_source],...(run.private_side===true?[['Private-side','Yes',run.private_side_source]]:[]),['Currency',run.currency]].map(([name,value,source])=>`<p>${esc(`${name} · ${value||'Not stated'}`)} ${librarySourceAction(run,source)}</p>`).join('')}${run.ratings.length?`<h3>Dated ratings</h3>${run.ratings.map(r=>`<p>${esc(`${r.label} · ${libraryRatingText(r)}`)} ${librarySourceAction(run,r.source)}</p>`).join('')}`:''}<div class="completion-box"><strong>${esc(done[0])}</strong>${esc(done[1])}</div></div><div><div class="metric-grid">${Object.entries(METRIC_NAMES).map(([k,n])=>libraryMetricItem(run,n,run.metrics[k])).join('')}</div>${libraryFacilities(run)}<h3>Deliverables &amp; revision history</h3><ul class="artifact-list">${artifacts}</ul>${librarySources(run)}</div></div>`;
}
// Options of every select the screen sends to LibraryLogic, as [value, text]. The Library query accepts only these values.
function libraryChoices() {
  const runs=catalogueRuns(),values=pick=>[...new Set(runs.flatMap(pick).filter(Boolean))].sort().map(v=>[v,v]);
  return {sector:values(r=>r.sector),workflow:values(r=>r.workflow),issuer:issuerGroups(runs).map(g=>g[0].issuer).filter(Boolean).sort().map(v=>[v,v]),basis:values(r=>r.metrics.leverage?.basis),period:values(r=>r.period_kind),currency:values(r=>r.currency),limitation:values(r=>r.gaps||[]),
    completion:[['75','75% or above'],['50','50% or above'],['100','100% complete'],['unassessed','Not assessed']],availability:[['report','Report available'],['handoff','No report available']],
    runs:[['latest','Latest run per issuer'],['any','Any run']],classification:[...Object.entries(CLASSIFICATIONS),['not_stated','Not stated']],
    ratingBelow:LibraryLogic.scale.map(r=>[r,r.replace('/',' / ')]),ratingAbove:LibraryLogic.scale.map(r=>[r,r.replace('/',' / ')]),ratingScope:[['issuer','Issuer ratings'],['any','Any rating']]};
}
const libraryActive=group=>LIBRARY_GROUPS[group].filter(k=>libraryFilters[k]&&libraryFilters[k]!==LIBRARY_DEFAULTS[k]).length;
function libraryPanel() {
  const f=libraryFilters,choices=libraryChoices();
  const select=(key,label,any)=>`<label>${label}<select id="library-${key}" data-library-filter="${key}">${(any?[['',any],...choices[key]]:choices[key]).map(([v,t])=>`<option value="${esc(v)}" ${f[key]===v?'selected':''}>${esc(t)}</option>`).join('')}</select></label>`;
  const number=(key,label,hint)=>`<label>${label}<input id="library-${key}" data-library-filter="${key}" type="number" step="any" placeholder="${hint}" value="${esc(f[key])}"></label>`;
  const pair=(key,label,unit)=>['Min','Max'].map(end=>number(`${key}${end}`,`${label}, ${end==='Min'?'minimum':'maximum'}${unit?` (${unit})`:''}`,`No ${end==='Min'?'minimum':'maximum'}`)).join('');
  const group=(name,title,body,hint='')=>{const n=libraryActive(name);return `<details id="${name}-filters" ${n?'open':''}><summary>${title} <span id="${name}-filter-count">${n?`· ${n} active`:''}</span></summary><div class="library-filters">${body}</div>${hint}</details>`;};
  return `<header class="block-head"><h2>Screening criteria</h2><span class="hint">Combined filters</span></header><div class="search-row"><label class="library-search"><span class="sr-only">Search issuer, run or sector</span>${icon('search')}<input id="library-query" data-library-filter="search" type="search" value="${esc(f.search)}" placeholder="Search issuer, run or sector…" autocomplete="off" aria-controls="library-results"></label><button id="library-clear" class="tertiary-action" type="button">Reset filters</button></div><div class="library-filters">${select('runs','Runs')}${select('sector','Sector','All sectors')}${select('workflow','Workflow','All workflows')}${select('completion','Completeness','Any completeness')}${select('availability','Deliverables','All runs')}</div>`
    +group('rating','Classification, rating &amp; currency',`${select('classification','Classification','Any')}${select('currency','Currency','Any')}${select('ratingBelow','Rating at or below','Any')}${select('ratingAbove','Rating at or above','Any')}${select('ratingScope','Rating scope')}`)
    +group('metric','Credit metrics &amp; period',`${select('basis','Leverage basis','All bases · definitions differ')}${select('period','Financial period','All period types')}${pair('leverage','Leverage','x')}${pair('coverage','Coverage','x')}${pair('netLeverage','Net leverage','x')}${pair('cash','Cash','as reported unit')}${pair('undrawn','Undrawn facilities','as reported unit')}`,'<p class="hint">Numeric filters exclude unavailable values. Select a leverage basis to keep definitions consistent; coverage definitions remain visible on each row.</p>')
    +group('deal','Facilities &amp; quotes',`${pair('talk','Spread talk','bps')}${pair('margin','Margin','bps')}${pair('coupon','Coupon','%')}${pair('price','Price')}${pair('yield','Yield','%')}`,'<p class="hint">Matched within one facility: talk and bid–ask by overlap, single values inside the range. Values are shown as entered.</p>')
    +group('limit','Accepted limitations',select('limitation','Accepted limitation','Any'));
}
// A panel rebuild shows an unreadable number box empty, so its stored 'invalid' bound is dropped to keep the filter and the control in agreement.
const clearInvalidBounds=()=>Object.keys(libraryFilters).forEach(k=>{if(libraryFilters[k]==='invalid')libraryFilters[k]='';});
function libraryView() {
  clearInvalidBounds();
  const view=libraryRows();
  return `<div class="library-screen"><nav id="library-nav" class="library-nav" aria-label="Issuers">${libraryNav()}</nav><div class="library-main"><form id="library-filters" class="library-panel" role="search" aria-label="Screen issuer runs">${libraryPanel()}</form><section class="library-results-panel" aria-label="Run results"><p id="library-count" role="status" aria-live="polite">${libraryCount(view)}</p><div id="library-coverage" class="library-coverage" role="status" aria-live="polite">${libraryCoverage(view)}</div><div id="library-results">${libraryResults(view)}</div></section><section id="run-detail" class="run-detail" aria-label="Selected run details" tabindex="-1" ${view.rows.some(r=>r.id===libraryState.selected)?'':'hidden'}>${libraryDetail(view)}</section></div></div>`;
}
// Re-places the results from the current filters; the panel itself is only rebuilt on a reset so typing keeps its focus.
function updateLibrary(panel=false) {
  if(panel)clearInvalidBounds();
  const view=libraryRows();
  if(panel)$('library-filters').innerHTML=libraryPanel();
  $('library-nav').innerHTML=libraryNav();
  $('library-count').textContent=libraryCount(view);
  $('library-results').innerHTML=libraryResults(view);
  $('run-detail').innerHTML=libraryDetail(view);
  $('run-detail').hidden=!view.rows.some(r=>r.id===libraryState.selected);
  $('library-coverage').innerHTML=libraryCoverage(view);
  for(const group of Object.keys(LIBRARY_GROUPS))$(`${group}-filter-count`).textContent=libraryActive(group)?`· ${libraryActive(group)} active`:'';
  writeLibraryHash();
}
function reportList(context) {
  const ctx=contexts[context],all=window.DESIGN_WORKSPACE.reports,built=reportsBuiltFrom(context),others=ctx?issuerReports(context).filter(r=>!built.includes(r)):[];
  const rest=all.filter(r=>!built.includes(r)&&!others.includes(r));
  const none='No report was built from this run’s files';
  const row=r=>`<li class="report-row">${ctx&&!sameIssuer(r.issuerKey,ctx.issuerKey)&&!r.label.trim().startsWith(r.issuer)?`<span class="report-issuer">${esc(r.issuer)} · </span>`:''}<a class="text-action" href="${routeHref('W-Reports',r.id,null,ctx&&sameIssuer(r.issuerKey,ctx.issuerKey)?context:tracedRun(r))}">${esc(reportName(r))}${icon('arrow-right')}</a><span class="code">${esc(r.id)}</span>${r.status?`<span class="badge badge-gray">${esc(r.status)}</span>`:''} ${reportAcceptance(r).html}</li>`;
  const list=(cls,title,reports)=>reports.length?`<section class="${cls}"><h2>${esc(title)}</h2><ol class="report-list">${[...reports].sort(byBuild).map(row).join('')}</ol></section>`:'';
  if(!ctx)return `<p class="intro">${plural(all.length,'deliverable')} in this workspace.</p>${list('report-other','All deliverables',all)}${all.length?'':`<div class="missing-state"><h2>No deliverables yet</h2><p>A run writes its report here when it finishes.</p></div>`}`;
  const heading=!built.length&&!others.length?`<div class="missing-state"><div class="empty-symbol">${icon('file-text')}</div><h2>${none}</h2></div><a class="text-action" href="#W-Library/cases">Choose another case</a>`:`<p class="intro">${built.length?`${plural(built.length,'report')} built from ${esc(ctx.run)}’s files.`:`${none}.`}</p>`;
  return `${heading}${list('report-built','Built from this run',built)}${list('report-other',`Other ${ctx.issuer} reports`,others)}${list('report-rest','Other issuers’ reports',rest)}`;
}
function reportView(report,context) {
  const ctx=contexts[context],rows=report.builtFrom.map(b=>{
    if(!b.run)return `<tr><th scope="row">${esc(b.module)}</th><td>No matching run file</td><td>${esc(b.source)}</td><td>${b.sha256.slice(0,12)}</td></tr>`;
    const href=b.output?routeHref(b.module,modules[b.source].first,null,b.run,data[b.source].source):routeHref('W-Evidence','sources',null,b.run);
    return `<tr><th scope="row">${esc(b.module)}</th><td>${esc(contexts[b.run].run)}</td><td><a href="${href}">${esc(b.source.split('/').at(-1))}</a></td><td>${b.sha256.slice(0,12)}</td></tr>`;
  }).join('');
  const handoffs=new Set(report.builtFrom.map(b=>b.module)).size,unmatched=new Set(report.builtFrom.filter(b=>!b.run).map(b=>b.module)).size;
  const files=report.files.length?`<details class="built-from"><summary>Files in this deliverable · ${report.files.length}</summary><ul>${report.files.map(f=>`<li><a href="${esc(f.href)}" download>${esc(f.name)}</a></li>`).join('')}</ul></details>`:'';
  const status=[report.status,ctx?'':'No matching run'].filter(Boolean).join(' · ');
  return `<div class="report-tools"><label for="report-select">Report</label><select id="report-select">${[...runReports(context)].sort(byBuild).map(r=>`<option value="${esc(r.id)}" ${r.id===report.id?'selected':''}>${esc(reportName(r))}</option>`).join('')}</select>${status?`<span>${esc(status)}</span><i class="tool-sep" aria-hidden="true"></i>`:''}${reportAcceptance(report).html}<a href="${esc(report.download)}" download>Download original HTML</a><a href="${routeHref('W-Reports','list')}">All reports</a><a href="#W-Library/cases">Return to library</a></div><details class="built-from"><summary>Built from ${handoffs} handoffs · ${unmatched?`${unmatched} with no matching run file`:'byte-identical by SHA-256'}</summary><div class="table-scroll"><table><thead><tr><th scope="col">Module</th><th scope="col">Run</th><th scope="col">File</th><th scope="col">SHA-256 prefix</th></tr></thead><tbody>${rows}</tbody></table></div></details>${files}<div class="frame-host"><p class="frame-status" role="status">Loading report…</p><iframe id="report-preview" title="${esc(reportName(report))} · ${esc(report.issuer)} report" sandbox="allow-scripts allow-downloads" referrerpolicy="no-referrer" src="${esc(report.href)}"></iframe></div>`;
}
// Modules most likely to state the run's overall credit view come first.
const CALL_ORDER=['CP-6','CP-2','CP-3','CP-2D','CP-1','CP-0'];
function firstFinding(id) {
  const sections=data[id].sections,start=sections.findIndex(s=>s.heading==='Findings');
  if(start<0)return null;
  for(const [at,section] of sections.slice(start).entries()) {
    if(at&&section.level<=sections[start].level)break;
    const block=section.blocks.find(b=>b.type==='text');
    if(block)return {text:block.text,line:block.line};
  }
  return null;
}
function moduleSummary(id) {
  const {summary,call}=data[id];
  if(summary)return {kind:'summary',text:summary.bottomLine,line:summary.line,confidence:summary.confidence,limitation:summary.limitation};
  if(call)return {kind:'call',text:call.text,line:call.line};
  const finding=firstFinding(id);
  return finding&&{kind:'finding',...finding};
}
function leadModule(context,available) {
  const order=[...new Set([...CALL_ORDER,...groups.flatMap(g=>g[1].map(item=>item[0]))])].filter(id=>available.includes(id));
  for(const module of order) {
    const id=defaultOutput(module,context),summary=id&&moduleSummary(id);
    // A first finding is one paragraph of a module's work, so it never stands as the run's bottom line.
    if(summary&&summary.kind!=='finding')return {module,id,summary};
  }
  return null;
}
function summaryLead(lead) {
  if(lead) {
    const {module,id,summary}=lead;
    return `<section class="summary-lead"><p class="summary-owner">${esc(moduleNames[module])}</p><p class="call-quote">${rich(summary.text.replace(/\n/g,' '))}</p>${summary.kind==='summary'?readerFacts(summary):''}${sourceFooter(`${id}:${summary.line}`)}</section>`;
  }
  return '<section class="summary-lead empty"><p>No bottom line is stored for this run. Read the findings below.</p></section>';
}
function summaryCharts(available,context) {
  const charts=available.map(module=>defaultOutput(module,context)).filter(Boolean).flatMap(id=>{
    const visual=data[id].visual;
    if(CHART_RENDERERS[visual?.kind])return [visualMarkup(id,{...visual,fixed:true})];
    return (data[id].charts||[]).map(chart=>readerChart(id,chart));
  }).slice(0,4);
  return charts.length?`<div class="summary-charts">${charts.map(chart=>`<div class="summary-chart">${chart}</div>`).join('')}</div>`:'';
}
function summaryCard(module,context) {
  const id=defaultOutput(module,context),summary=id&&moduleSummary(id);
  const body=!id?`<p class="summary-note">${plural(moduleEntry(module,context).outputs.length,'saved output')}. Choose one to read its findings.</p>`:summary?`<div class="summary-text">${rich(summary.text.replace(/\n/g,' '))}</div>${summary.kind==='summary'?`<span class="badge badge-gray">Confidence: ${esc(summary.confidence)}</span>`:''}${sourceLink(`${id}:${summary.line}`)}`:'<p class="summary-note">No written findings in this output.</p>';
  return `<article class="summary-card" data-module="${esc(module)}" ${id?`data-output="${esc(id)}"`:''}><h3>${moduleLink(module)}</h3>${body}</article>`;
}
function summaryView(context) {
  const available=contextModules(context),built=reportsBuiltFrom(context),lead=leadModule(context,available),led=lead?.module;
  const questions=groups.map(([title,items])=>[title,items.filter(([id])=>available.includes(id)&&id!==led)]).filter(([,items])=>items.length);
  return `${summaryLead(lead)}${summaryCharts(available,context)}<div class="question-map">${questions.map(([title,items])=>`<section><h2>${esc(title)}</h2><div>${items.map(([id])=>summaryCard(id,context)).join('')}</div></section>`).join('')}</div>${built.length?`<section class="summary-deliverables"><h2>Deliverables from this run</h2>${built.map(r=>`<div class="deliverable"><a class="text-action" href="${routeHref('W-Reports',r.id,null,context)}">${esc(reportName(r))}${icon('arrow-right')}</a>${reportAcceptance(r).html}</div>`).join('')}</section>`:''}`;
}
// Read-only: the folders the library does not show (with the reason) and the issues found when it was built.
function activityView(activity) {
  if(!activity)return '<div class="missing-state"><div class="empty-symbol">'+icon('file-text')+'</div><h2>Run activity could not be read</h2><p>The data file did not supply it, so nothing is claimed about excluded runs or issues. Rebuild the data file and open this page again.</p></div>';
  const excluded=activity.excluded,issues=activity.issues;
  if(!excluded.length&&!issues.length)return '<div class="missing-state"><div class="empty-symbol">'+icon('file-text')+'</div><h2>Nothing to report</h2><p>Every run folder in this workspace is shown in the library, and building it raised no issues.</p></div>';
  return `<p class="intro">Read when the library was built. It lists run folders that are not shown and any issues found; it changes nothing.</p>${excluded.length?`<section class="activity-excluded"><h2>Run folders not shown</h2><ol class="report-list">${excluded.map(([folder,reason])=>`<li class="report-row"><span class="code">${esc(folder)}</span><span>${esc(reason)}</span></li>`).join('')}</ol></section>`:''}${issues.length?`<section class="activity-issues"><h2>Issues</h2><ul class="report-list">${issues.map(i=>`<li class="report-row">${esc(i)}</li>`).join('')}</ul></section>`:''}`;
}
function workspaceView(module,section) {
  const context=current?.context,ctx=contexts[context],available=ctx?contextModules(context):[];
  if(module==='W-Library')return libraryView();
  if(module==='W-Overview')return summaryView(context);
  if(module==='W-Calendar') {
    const events=eventsOutput(context),hedges=hedgesOutput(context),showHedges=hedges&&(section==='hedges'||!events);
    if(!events&&!hedges)return `<div class="missing-state"><h2>No calendar retained for this run</h2><p>No dates are inferred from other cases.</p></div>${moduleLink('W-Evidence','Review available evidence')}<a class="text-action switch-case" href="#W-Library/cases">Choose another case</a>`;
    const hedgeView=hedges&&(data[hedges].visual?.kind==='hedges'?hedgeChart(hedges,data[hedges].visual):`<div class="missing-state"><h2>No hedge schedule view for this output</h2><p>The retained CP-2E output is available in its module.</p></div>`);
    return `${showHedges?hedgeView:eventTimeline(events,eventTable(data[events].sections))}${moduleLink(showHedges?'CP-2E':'CP-1A','Open owning module')}`;
  }
  if(module==='W-Evidence')return `<p class="intro">Source PDFs aren’t included; page references point to the originals.</p>${sourceInventory(context)}`;
  if(module==='W-Reports') {
    const report=window.DESIGN_WORKSPACE.reports.find(r=>r.id===section);
    return report?reportView(report,context):reportList(context);
  }
  if(module==='W-Forecast')return forecastView(context,section);
  if(module==='CP-OS')return activityView(window.DESIGN_ACTIVITY);
  return '';
}
function updateWorkspaceChrome(module) {
  const ctx=contexts[current.context],isHome=!ctx||appDestinations.has(module);
  const moduleId=ctx&&(lastSection.get(current.context+':module')||ctx.first),period=current.output?data[current.output].period:ctx?.period;
  const title=isHome?(module==='W-Library'?'Issuer library':moduleNames[module]):ctx.title;
  document.querySelector('.issuer').innerHTML=`<div class="issuer-title"><h1 title="${esc(title)}">${esc(title)}</h1>${isHome?'':`<div class="issuer-meta"><span class="code">${esc(ctx.run)}</span><a href="#W-Library/cases">Change case</a></div>`}</div>${module==='W-Library'?`<div class="page-actions"><a class="secondary-action" href="#W-Reports/list">${icon('files')}All reports</a></div>`:''}${isHome?'':`<div class="scope">${icon('calendar-days')}<strong>${esc(period)}</strong></div>`}`;
  document.querySelector('.workspace-tabs').hidden=isHome;
  if(!isHome)document.querySelector('.workspace-tabs').innerHTML=[['W-Overview','Overview','layout-grid'],[moduleId,'Modules','layers'],['W-Calendar','Calendar','calendar-days'],['W-Forecast','Forecast','chart-no-axes-combined'],['W-Reports','Reports','files'],['W-Evidence','Evidence','folder-open']].map(([id,label,img])=>{
    const sections=navigationSections(id,current.context,resolveOutput(id,current.context,lastFile.get(`${current.context}:${id}`))),remembered=lastSection.get(current.context+':'+id),section=sections.some(s=>s[0]===remembered)?remembered:sections[0][0];
    return `<a href="${routeHref(id,section)}" ${(label==='Modules'?isAnalytical(module):id===module)?'aria-current="page"':''}>${icon(img)}${label}</a>`;
  }).join('');
  const report=isReportRoute(module,current.section);
  $('workbench').classList.toggle('report-workspace',report);
  $('workbench').classList.toggle('library-workspace',isHome);
  // The navigator is resident only where its modules are the subject; elsewhere it opens from the Modules button.
  $('workbench').classList.toggle('tools-workspace',!isHome&&!report&&module!=='W-Overview'&&!isAnalytical(module));
  $('content').classList.toggle('report-content',report);
  // The rail shows where you are, and its run-level links keep the selected run.
  const rail=label=>document.querySelector(`.rail [data-place="${label}"]`);
  const place={'W-Library':'Issuer library','W-Reports':'Reports','CP-OS':'Run activity'}[module];
  document.querySelectorAll('.rail a[data-place]').forEach(link=>{
    const here=link.dataset.place===place;
    link.classList.toggle('rail-active',here);
    if(here)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');
  });
  rail('Reports').hidden=!window.DESIGN_WORKSPACE.reports.length&&!Object.keys(contexts).length;
  if(ctx) {
    rail('Reports').href=routeHref('W-Reports','list');
  }
  const app=window.DESIGN_APP||{};
  $('app-problem').hidden=!app.problem;
  $('app-problem').textContent=app.problem?`The workspace could not be read: ${app.problem}`:'';
}
