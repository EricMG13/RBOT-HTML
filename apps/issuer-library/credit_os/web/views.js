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
// ---- Names, not codes. A module code or a methodology step id is replaced by what it identifies; only register references (C9, G1, D1, GAP-001) stay.
// A module's own name wins; a code standing in for its own label takes its parent's name when it has one.
const moduleLabel=code=>{
  const own=moduleNames[code];
  return (own!==code&&own)||moduleNames[aliases[code]]||own||(code==='CP-MEMO'?'Credit memo':null);
};
const moduleTitle=code=>moduleLabel(code)??'Unnamed module';
// "<Module name> handoff" for a file named after its module (…/CP-1.md, …--CP-1.md); any other file keeps its name.
// A second saved output (…--CP-0-a.md) keeps its distinguishing suffix: "Source readiness handoff (a)".
const handoffName=(code,suffix)=>`${moduleTitle(code)} handoff${suffix?` (${suffix.slice(1)})`:''}`;
function handoffLabel(file) {
  const found=/(?:^|[/-])(CP-[A-Z0-9]+)(-[a-z0-9]+)?\.md$/.exec(file);
  return found?handoffName(found[1],found[2]):file;
}
// A module code, its register id (CP-2A-GAP-005, CP-3B-MON-001), its handoff file (…CP-0-a.md) or its runbook file (CP-4_RUNBOOK.md).
const MODULE_REF=/\bCP-(?<owner>[A-Z0-9]+)-(?<reg>[A-Z]+)-(?<zeros>0*)(?<num>\d+)\b|\bCP-(?<book>[A-Z0-9]+)_RUNBOOK\.md\b|\b(?<file>CP-[A-Z0-9]+)(?<suffix>-[a-z0-9]+)?\.md\b|\bCP-[A-Z0-9]+\b/g;
// A step id carries its dot and has the METHOD_CODE shape: T4.10, T1D.1, T4.D1, T2G.* (a family), T2E.3.r01 (a sub-row). A bare T2 is ordinary text.
const DASH='(?:\\s+—\\s+|\\s+(?=[A-Z]))'; // a real heading is "T2.12 Gaps ledger" or "T2.12 — Gaps ledger"; with no dash a capital must follow
const STEP='T\\d+[A-Z]?\\.(?:[A-Z]?\\d+|\\*)(?:\\.[a-z]+\\d+)?',ID=`\\b${STEP}(?![A-Za-z0-9])`;
const STEP_ID=new RegExp(`^${STEP}$`),STEP_ANY=new RegExp(ID,'g'),STEP_LEAD=new RegExp(`^\\s*${ID}\\s+—\\s+`);
const STEP_RUN=new RegExp(`${ID}(?:\\s*(?:,\\s*and|[–/,;]|and|through)\\s*${ID})*`,'g');
const STEP_HEADING=new RegExp(`^(${STEP})${DASH}(.+)$`),STEP_ROW=new RegExp(`^(${STEP})(?:${DASH}(.+))?$`);
// A step's title is the one its own output gives it: a heading "T1D.1 — Add-Back Register", or a step-table row ["T4.1","Peer universe",…]. A longer second cell is a description, not a title.
const stepTitleCache=new Map();
function stepTitles(output) {
  if(stepTitleCache.has(output))return stepTitleCache.get(output);
  const titles=new Map(),note=(id,title)=>{if(!titles.has(id)&&title&&plain(title).length<=80)titles.set(id,plain(title));};
  for(const section of data[output]?.sections??[]) {
    const heading=STEP_HEADING.exec(section.heading);
    if(heading)note(heading[1],heading[2]);
    for(const block of section.blocks)if(block.type==='table')for(const row of block.rows) {
      const cell=STEP_ROW.exec(plain(row.cells[0]).trim());
      if(cell)note(cell[1],cell[2]??row.cells[1]);
    }
  }
  stepTitleCache.set(output,titles);
  return titles;
}
// A step id in prose or a cell becomes its title (in quotes inside a sentence, bare when the id is the whole text); a range's dash reads "to";
// a run of ids with no title reads "method steps" ("a method step" for one); an id leading its own title is dropped; no title found: "a method step".
function stepText(text,output) {
  const titles=stepTitles(output),whole=text.trim();
  const lead=STEP_LEAD.exec(text);
  const body=lead?text.slice(lead[0].length):text;
  return body.replace(STEP_RUN,run=>{
    const ids=run.match(STEP_ANY),quoted=run===whole?t=>t:t=>`“${t}”`;
    if(!ids.some(id=>titles.has(id)))return ids.length>1?'method steps':'a method step';
    return run.replace(/\s*–\s*/g,' to ').replace(STEP_ANY,id=>titles.has(id)?quoted(titles.get(id)):'a method step');
  });
}
// CP-<x>-GAP-<n> is "Gap <n>" on module x's own page and "<Name of x> gap <n>" elsewhere; a code with no known name is "unnamed module".
// A name already written before its own parenthesised code ("Liquidity (CP-2D)") is not said twice: the parenthetical is dropped.
const NAME_THEN_CODE=/\s*\((CP-[A-Z0-9]+)\)/g;
const dropRepeat=(text,lead='')=>text.replace(NAME_THEN_CODE,(whole,code,at)=>{const name=moduleLabel(code)?.toLowerCase(),before=(lead+text.slice(0,at)).toLowerCase();return name&&before.endsWith(name)&&!/[\p{L}\p{N}]$/u.test(before.slice(0,-name.length))?'':whole;});
function namedText(text,output=current?.output,lead='') {
  // A stored source file name of the run is shown exactly as stored, even when it holds a code.
  const ev=contexts[data[output]?.run??current?.context]?.evidence||{};
  const file=[...(ev.sources||[]),...(ev.unused||[]),...(ev.unrecorded||[])].map(f=>f.name).filter(Boolean).sort((a,b)=>b.length-a.length).find(name=>text.includes(name));
  if(file!==undefined){const at=text.indexOf(file);return namedText(text.slice(0,at),output,lead)+file+namedText(text.slice(at+file.length),output);}
  return stepText(dropRepeat(text,lead).replace(/\bGap (?=CP-[A-Z0-9]+-GAP-)/g,'').replace(MODULE_REF,(code,...rest)=>{
    const {owner,reg,zeros,num,book,file,suffix}=rest.at(-1),name=id=>moduleLabel(id)??'unnamed module';
    if(book!==undefined)return `${name(`CP-${book}`)} runbook`;
    if(file!==undefined)return handoffName(file,suffix);
    if(owner===undefined)return name(code);
    const own=[`CP-${owner}`,aliases[`CP-${owner}`]].includes(current?.module);
    if(reg==='GAP')return own?`Gap ${num}`:`${name(`CP-${owner}`)} gap ${num}`;
    return own?`${reg}-${zeros}${num}`:`${name(`CP-${owner}`)} ${reg}-${zeros}${num}`;
  }),output);
}
function installDestinations() {
  const title = h => h.replace(/^Chart data: /,'').replace(/^T[\w.]+(?:\s*[–/]\s*(?:T[\w.]+|\d+))*\s*[—–]\s*/,'').replace(/^./,s=>s.toUpperCase());
  for (const [id,out] of Object.entries(data)) {
    if(modules[id]) continue;
    const sections=[];
    const audit=[];
    for(const s of out.sections.filter(s=>s.blocks.length)) {
      if((isNewFormat(out.sections)?/^(Request|Next module)/:/^(Request|Calculations|Next module)/).test(s.heading)) {audit.push('='+s.heading);continue;}
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
    'W-Report':['Report history',[['history','Report history',[]]]],
    'W-Overview':['Overview',[['overview','Overview',[]]]],
    'W-Changes':['Changes',[['changes','Changes',[]]]],
    'W-Evidence':['Evidence',[['sources','Evidence',[]]]],
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
// A run's published models: those recorded for its folder and those built from a file it holds.
const publishedModels=()=>window.DESIGN_WORKSPACE.models;
const byModelId=(a,b)=>b.id.localeCompare(a.id);
// One order for the Model select, the section pager and the default: the default model first, then the rest by folder name, latest first.
// A model of another issuer (or of none recorded) is never a run's own, whatever run it names; no run context holds none.
const runModels=context=>{const run=contexts[context];if(!run)return [];const held=publishedModels().filter(m=>sameIssuer(m.issuerKey,run.issuerKey)&&(m.runId===run.folder||m.runFolder===run.folder||m.sources.some(s=>s.run===context))).sort(byModelId),first=modelOrder(held)[0];return first?[first,...held.filter(m=>m!==first)]:held;};
// A model links only to a run whose Forecast page lists it (runModels); with no such run it is shown unlinked.
const modelRun=model=>Object.keys(contexts).find(key=>runModels(key).includes(model))||null;
// A model opens under the run it was published for (its runId), never under a run that only supplied files; with no such run listing it, modelRun's choice stands.
const modelOwnRun=model=>Object.keys(contexts).find(key=>(contexts[key].folder===model.runId||contexts[key].folder===model.runFolder)&&runModels(key).includes(model))||modelRun(model);
// Not superseded by another listed model; one that records a predecessor comes first, then the later folder name.
const modelOrder=models=>[...models].sort((a,b)=>(models.some(m=>m.previous===a.id)-models.some(m=>m.previous===b.id))||((b.previous!=null)-(a.previous!=null))||byModelId(a,b));
// The relationship a delivery records with another, or null when it records none. The other delivery is named by name(id): its picker label when it is listed, its id when not.
function modelRelationship(model,models,name) {
  const successor=models.find(m=>m.previous===model.id);
  return model.previous?`supersedes ${name(model.previous)}`:successor?`superseded by ${name(successor.id)}`:null;
}
// A delivery in the Model select reads "<run date> · <pathway>" from its own run, then its run folder, then its delivery id. Two deliveries that
// read alike each add the first eight characters of the delivery id, or the whole id when those still tie; a relationship is added only when one is recorded.
function modelOptionLabels(models) {
  const base=models.map(m=>{const ctx=Object.values(contexts).find(run=>sameIssuer(m.issuerKey,run.issuerKey)&&(run.folder===m.runFolder||run.folder===m.runId));return ctx?`${runName(ctx)}`:m.runFolder||m.id;});
  const tagged=models.map((m,i)=>base.filter(text=>text===base[i]).length>1?`${base[i]} · ${m.id.slice(0,8)}`:base[i]);
  const names=models.map((m,i)=>tagged.filter(text=>text===tagged[i]).length>1&&tagged[i]!==base[i]?`${base[i]} · ${m.id}`:tagged[i]);
  const listed=id=>{const at=models.findIndex(m=>m.id===id);return at<0?id:names[at];};
  return models.map((m,i)=>{const relationship=modelRelationship(m,models,listed);return `${names[i]}${relationship==null?'':` · ${relationship}`}`;});
}
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
function firstSection(module,context) {
  const output=defaultOutput(module,context);
  return output?REPORT_PARTS[0][0]:navigationSections(module,context)[0][0];
}
const plural=(n,word)=>`${n} ${word}${n===1?'':'s'}`;
// The saved-output selector, the "Used in" link and the parse flag a module's head carries.
function headTools(module,context,output) {
  const files=moduleEntry(module,context)?.outputs||[],out=output&&data[output];
  const meta=!out?'':files.length>1?`<label class="output-meta output-select">Saved output <select id="output-select">${files.map(id=>`<option value="${esc(data[id].source)}" ${id===output?'selected':''}>${esc(data[id].label)}</option>`).join('')}</select></label>`:out.label===module?'':`<span class="output-meta">Saved output · ${esc(out.label)}</span>`;
  const flag=out?.parseError?`<span class="output-meta">Shown unstructured: ${esc(out.parseError)}</span>`:'';
  return {meta,flag};
}
function moduleHead({module,context,output}) {
  if(output&&isAnalytical(module))return ''; // The module report draws its own head.
  const {meta,flag}=headTools(module,context,output);
  return `<div class="module-title"><h2>${esc(moduleNames[module])}</h2>${meta}${flag}</div>`;
}
function fixtureTable(module,line) {
  const table=data[module].sections.flatMap(s=>s.blocks).find(b=>b.type==='table'&&b.line===line);
  if(!table)throw new Error(`Missing visual table ${module}:${line}`);
  return table;
}
function chartIntro(id,v) {
  const label=[v.unit,data[id].period].filter(Boolean).join(' · ');
  return `<div class="section-heading"><h2>${esc(v.title)}</h2>${label?`<span>${esc(label)}</span>`:''}</div>${v.quote?`<p class="chart-reading">${rich(v.quote.text.replace(/\n/g,' '))}</p>${sourceFooter(`${id}:${v.quote.line}`)}`:''}`;
}
const evidenceHref=(id,line)=>routeHref(data[id].module,current?.output===id?current.section:modules[id].first,`${id}:${line}`,data[id].run);
function comparisonChart(module,v,selection=0,chips=false,note=true) {
  const table=fixtureTable(module,v.table),selected=table.rows[v.rows?.[selection]??0];
  const selectable=['paired','peers'].includes(v.kind)&&!['CP-4C','CP-2A'].includes(data[module].module);
  const rows=selectable?[selected]:(v.rows||table.rows.map((_,i)=>i)).map(i=>table.rows[i]);
  const points=v.kind==='peers'?v.columns.map(c=>({label:table.headers[c],value:selected.cells[c],row:selected,series:0})):rows.flatMap(row=>(v.columns||[v.column]).map((c,i)=>({label:plain(row.cells[0]),series:i,value:row.cells[c],row,column:c})));
  const max=Math.max(1,...points.map(p=>Math.abs(chartNumber(p.value)??0)));
  const hasNegative=points.some(p=>(chartNumber(p.value)??0)<0);
  return `${chartIntro(module,v)}${selectable&&!v.fixed?`<label class="metric-control">Measure <select id="chart-metric">${v.rows.map((idx,i)=>`<option value="${i}" ${i===selection?'selected':''}>${esc(plain(table.rows[idx].cells[0]))}</option>`).join('')}</select></label>`:''}<div class="horizontal-chart ${hasNegative?'diverging':''}">${points.map((p,i)=>{
    const n=chartNumber(p.value),width=n===null?0:Math.abs(n)/max*100;
    const key=`${module}:${p.row.line}`,cells=`<span class="chart-label">${i&&points[i-1].label===p.label?`<span class="sr-only">${esc(p.label)}</span>`:esc(p.label)}${v.columns&&v.kind!=='peers'?`<small>${esc(table.headers[p.column])}</small>`:''}</span><span class="track ${n===null?'missing':''}">${hasNegative?`<span class="zero-rule"></span>${n===null?'':`<i class="series-${p.series} ${n<0?'negative':''}" style="left:${n<0?50-width/2:50}%;width:${width/2}%"></i>`}`:n===null?'':`<i class="series-${p.series}" style="width:${width}%"></i>`}</span>${n===null?`<strong${/[\p{L}\p{N}]/u.test(String(p.value??''))?` title="${esc(p.value)}"`:''}>n.a.</strong>`:`<strong>${esc(p.value)}</strong>`}`;
    // With chips the row is a group: the button opens the row, each chip opens its own source (a chip cannot sit inside a button).
    return chips?`<div class="chart-row" role="group"><button class="chart-open" data-evidence="${esc(key)}">${cells}</button>${chipsMarkup(key)}</div>`:`<button class="chart-row" data-evidence="${esc(key)}">${cells}</button>`;
  }).join('')}</div>${note?'<p class="matrix-note">Missing values have no bar.</p>':''}`;
}
// A step label wraps word-wise to what one step can hold (the 14px monospace axis label advances 8.4 viewBox units a character, less a gap
// between neighbours), in at most three lines. A word is cut only when it alone is wider than a line; the ellipsis marks a cut word or text
// left after the third line (the last line then drops whole words to make room for it). The title and key carry the full text.
// A map node reuses it with its own character advance (12px proportional type, MAP_CHAR).
// Labels start at AXIS_Y and drop 1.2em a line (up to 14px type on a narrow screen), so the viewBox runs to AXIS_BOTTOM to hold three lines and their descenders
// at either size. A wide bridge is drawn at no less than WIDE_SCALE of its viewBox, whatever its container: a narrow card scrolls it sideways.
const AXIS_CHAR=8.4,AXIS_LINES=3,WIDE_STEPS=7,WIDE_STEP=142,AXIS_Y=226,BRIDGE_HEIGHT=282,WIDE_SCALE=.75;
function axisLines(label,step,char=AXIS_CHAR,hard=false,most=AXIS_LINES) {
  const room=Math.max(4,Math.floor((step-6)/char)),lines=[];
  for(const long of label.split(' ').filter(Boolean)){
    // `hard` (map nodes): a word wider than a line breaks across lines, whole, before any ellipsis; the bridge cuts it with an ellipsis; 'keep' (map edge labels) leaves it whole on its own line.
    let word=long;
    while(hard===true&&word.length>room){lines.push(word.slice(0,room));word=word.slice(room);}
    const w=word.length>room&&hard!=='keep'?`${word.slice(0,room-1)}\u2026`:word,last=lines.length-1;
    if(last>=0&&lines[last].length+1+w.length<=room&&!lines[last].endsWith('\u2026'))lines[last]+=` ${w}`;
    else lines.push(w);
  }
  if(lines.length<=most)return lines.length?lines:[label];
  const kept=lines.slice(0,most),end=kept[most-1].split(' ');
  while(end.length>1&&end.join(' ').length+1>room)end.pop();
  const tail=end.join(' ');
  kept[most-1]=tail.endsWith('\u2026')?tail:tail.length+1>room&&hard!=='keep'?`${tail.slice(0,room-1)}\u2026`:`${tail}\u2026`;
  return kept;
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
  // The scale covers every running start and end, so a position that dips below zero (repay before refinancing) stays inside the frame; the axis is the zero rule.
  const high=Math.max(0,...points.map(p=>Math.max(p.start,p.end)))*1.16,low=Math.min(0,...points.map(p=>Math.min(p.start,p.end)));
  const wide=points.length>=WIDE_STEPS,width=wide?points.length*WIDE_STEP:660,height=210,step=width/points.length,y=n=>height-(n-low)/((high-low)||1)*height;
  return `${chartIntro(module,v)}<div class="vector-chart${wide?' bridge-wide':''}"${wide?` role="region" tabindex="0" aria-label="${esc(v.title)}; scroll horizontally for every step"`:''}><svg${wide?` style="min-width:${Math.round((width+20)*WIDE_SCALE)}px"`:''} viewBox="-5 -12 ${width+20} ${BRIDGE_HEIGHT}" role="group" aria-label="${esc(v.title)}. Select a movement to inspect its source."><line x1="0" y1="${y(0)}" x2="${width}" y2="${y(0)}" class="axis"/>${points.map((p,i)=>`<a class="plot-point" href="${evidenceHref(module,p.row.line)}" data-evidence="${esc(`${module}:${p.row.line}`)}" aria-label="${esc(p.label||plain(p.row.cells[0]))}, ${esc(p.display??p.row.cells[v.amount])} ${esc(v.unit)}. View source"><title>${esc(p.label||plain(p.row.cells[0]))}: ${esc(p.display??p.row.cells[v.amount])}</title><rect class="${p.total?'total':p.amount<0?'outflow':'movement'}" x="${i*step+10}" y="${y(Math.max(p.start,p.end))}" width="${step-20}" height="${Math.max(1,Math.abs(y(p.end)-y(p.start)))}"/><text x="${i*step+step/2}" y="${y(Math.max(p.start,p.end))-8}" text-anchor="middle">${esc(p.display??p.row.cells[v.amount])}</text><text class="axis-label" x="${i*step+step/2}" y="${AXIS_Y}" text-anchor="middle">${axisLines(p.label||plain(p.row.cells[0]),step).map((line,at)=>`<tspan x="${i*step+step/2}" dy="${at?'1.2em':0}">${esc(line)}</tspan>`).join('')}</text>${i<points.length-1?`<line class="connector" x1="${i*step+step-10}" y1="${y(p.end)}" x2="${(i+1)*step+10}" y2="${y(p.end)}"/>`:''}</a>`).join('')}</svg></div><div class="bridge-key">${points.map((p,i)=>`<span>${sourceLink(`${module}:${p.row.line}`,p.label||plain(p.row.cells[0]))}${classTag(evidence.get(`${module}:${p.row.line}`),'row-classification')}</span>`).join('')}</div>`;
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
// The axis runs from the earliest date in the table (or 18 months before the run's as-of, if earlier) to the latest (or 36 months after, if later); the base rule is the as-of. Only YYYY-MM-DD strings already in the table's date columns are read (every column if none is headed as a date).
function hedgeChart(module,v) {
  const table=fixtureTable(module,v.table),asOf=contexts[data[module].run]?.asOf;
  if(!/^\d{4}-\d{2}-\d{2}$/.test(asOf||''))throw new Error(`Missing as-of date for ${module}`);
  // Dates are read only from the columns whose header names a date; a table with no such header falls back to every cell.
  const dateColumns=table.headers.flatMap((h,i)=>/date|expiry|maturity|period|tenor/i.test(h)?[i]:[]),rowDates=row=>(dateColumns.length?dateColumns.map(i=>row.cells[i]??''):row.cells).join(' ').match(/\d{4}-\d{2}-\d{2}/g)||[],base=Date.parse(asOf),[y,m,d]=asOf.split('-').map(Number);
  const times=table.rows.flatMap(rowDates).map(Date.parse),shift=n=>Date.UTC(y,m-1+n,Math.min(d,new Date(Date.UTC(y,m+n,0)).getUTCDate())),start=Math.min(shift(-18),...times),end=Math.max(shift(36),...times);
  const position=time=>(time-start)/(end-start)*100,label=time=>new Date(time).toLocaleString('en-US',{month:'short',year:'numeric',timeZone:'UTC'});
  const unitColumn=table.headers.findIndex(h=>/unit/i.test(h));
  return `${chartIntro(module,v)}<div class="hedge-axis"><span style="left:0">${label(start)}</span><span style="left:${position(base)}%">${label(base)} base</span><span style="left:100%">${label(end)}</span></div><div class="hedge-chart">${table.rows.map(row=>{
    const dates=rowDates(row),dated=dates.length===2,forward=dated&&Date.parse(dates[0])>base,unit=unitColumn>=0?row.cells[unitColumn]||'':'';
    return `<button class="hedge-row" data-evidence="${esc(`${module}:${row.line}`)}"><span>${esc(row.cells[0])}<small>${esc(`${row.cells[1]} ${unit}`.trim())}</small></span><span class="hedge-lane"><i class="base-rule" style="left:${position(base)}%"></i>${dated?`<i class="hedge-span ${forward?'future':''}" style="left:${position(Date.parse(dates[0]))}%;width:${position(Date.parse(dates[1]))-position(Date.parse(dates[0]))}%"></i>`:'<span class="duration-only">Duration only · ≤12 months</span>'}</span><span class="hedge-dates">${dated?esc(dates.join(' → ')):esc(row.cells[2])}<small>${forward?'Forward starting at base date':dated?'Active at base date':'No exact expiry supplied'}</small></span></button>`;
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
// The accessible table form of a reader chart: the handoff's own table, every cell as written and a chip per row, behind a disclosure.
function chartTableForm(id,chart) {
  const table=fixtureTable(id,chart.table),columns=table.headers.map((_,c)=>c);
  return `<details class="chart-table"><summary>Table form</summary>${sourceTable(id,chart.title,table,columns.map(c=>numericColumn(table,c)),columns,table.rows)}</div></details>`;
}
// A drawing that states none (a chart, lane or map the store holds as a gap) keeps its section's table as the same fold: every cell as the module wrote it, a Source button per row.
const gapTableForm=(id,title,table)=>chartTableForm(id,{title,table});
// ---- Structure views (a "Chart data:" row table that is not by period or step): drawn from the stated numbers only. A value that is
// not a number is n.a. with its stated reason as the title; it is never a zero position. Nothing is computed for display: headroom and
// cumulative leverage are shown as stated, and the geometry uses the stated numbers.
const roundPct=n=>Math.round(n*100)/100;
const shown=cell=>/^Not supplied:/.test(cell)?`<span title="${esc(cell)}">n.a.</span>`:esc(cell);
const stated=(cell,suffix='')=>chartNumber(cell)===null?shown(cell):`${esc(cell)}${suffix}`;
// A track runs from the zero baseline (or the lowest stated value) to just past the highest: `at` is a stated number's position in percent.
function trackScale(numbers) {
  const known=numbers.filter(n=>n!==null),low=Math.min(0,...known),high=Math.max(0,...known),end=high+((high-low)||1)*.1;
  return n=>roundPct((n-low)/(end-low)*100);
}
function structureOpen(id,row,inner,label,chips) {
  const key=`${id}:${row.line}`,button=`<button class="chart-open" data-evidence="${esc(key)}" aria-label="${esc(`${label}. View source`)}">${inner}</button>`;
  return chips?`${button}${chipsMarkup(key)}`:button;
}
// A facility's series is its ranking and security together: one per distinct pair in order of first appearance. A row with no stated ranking, or a
// Secured value that is neither Yes nor No, is neutral and the legend says which of the two is not stated.
const stackRank=(row,v)=>{const rank=String(row.cells[v.rank]??'').trim();return !rank||/^Not supplied:/.test(rank)?'':rank;};
function stackPair(row,v) {
  const rank=stackRank(row,v),secured=String(row.cells[v.secured]??'').trim().toLowerCase();
  return !rank||!['yes','no'].includes(secured)?null:{rank,secured:secured==='yes'};
}
// Four fills, then the same four with a hatch: eight styles that differ by more than colour. A ninth distinct pair repeats the first style; the legend
// and each facility's own line state the ranking and security in words, so nothing rests on the swatch alone.
const stackClass=i=>`series-${i%4}${i%8>=4?' hatch':''}`;
function stackChart(id,v,chips=false) {
  const table=fixtureTable(id,v.table),amounts=table.rows.map(r=>chartNumber(r.cells[v.amount])),total=amounts.reduce((sum,n)=>sum+(n>0?n:0),0);
  const pairs=table.rows.map(r=>stackPair(r,v)),names=[];
  for(const p of pairs)if(p&&!names.includes(`${p.rank}|${p.secured}`))names.push(`${p.rank}|${p.secured}`);
  const series=pairs.map(p=>p?stackClass(names.indexOf(`${p.rank}|${p.secured}`)):'stack-neutral');
  const unstated=[...new Set(pairs.flatMap((p,i)=>{const rank=stackRank(table.rows[i],v);return p?[]:[rank?`Rank ${esc(rank)} \u00b7 security not stated`:'Ranking not stated'];}))];
  const legend=[...names.map((n,i)=>{const[rank,secured]=n.split('|');return `<span><i class="${stackClass(i)}"></i>Rank ${esc(rank)} \u00b7 ${secured==='true'?'secured':'unsecured'}</span>`;}),...unstated.map(t=>`<span><i class="stack-neutral"></i>${t}</span>`)].join('');
  const bar=table.rows.map((row,i)=>amounts[i]>0?`<a class="stack-seg ${series[i]}" href="${evidenceHref(id,row.line)}" data-evidence="${esc(`${id}:${row.line}`)}" style="width:${roundPct(amounts[i]/total*100)}%" aria-label="${esc(`${row.cells[v.label]}, ${row.cells[v.amount]} ${v.unit}. View source`)}" title="${esc(row.cells[v.label])}: ${esc(row.cells[v.amount])}"></a>`:'').join('');
  const key=table.rows.map((row,i)=>`<li><i class="swatch ${series[i]}"></i><span>${sourceLink(`${id}:${row.line}`,row.cells[v.label])}<small>Rank ${esc(row.cells[v.rank])} · Secured ${esc(row.cells[v.secured])} · Amount ${stated(row.cells[v.amount])} · Cumulative leverage ${stated(row.cells[v.leverage],'x')}</small></span>${chips?chipsMarkup(`${id}:${row.line}`):''}</li>`).join('');
  return `${chartIntro(id,v)}<div class="chart-legend stack-legend">${legend}</div><div class="stack-bar" role="group" aria-label="${esc(v.title)} in stated rank order. Select a facility to inspect its source.">${bar}</div>${amounts.includes(null)?'<p class="matrix-note">A facility with no stated amount has no segment.</p>':''}<ol class="stack-key">${key}</ol>`;
}
function bulletChart(id,v,chips=false) {
  const table=fixtureTable(id,v.table);
  return `${chartIntro(id,v)}<div class="bullet-chart">${table.rows.map(row=>{
    const cells=row.cells,threshold=chartNumber(cells[v.threshold]),current=chartNumber(cells[v.current]),direction=cells[v.direction],at=trackScale([threshold,current]);
    const label=v.label.map(c=>plain(cells[c])).join(' · '),unit=v.unit?'':cells[cells.length-2];
    const pass=threshold===null?'':/below/.test(direction)?`<i class="pass" style="left:0%;width:${at(threshold)}%"></i>`:`<i class="pass" style="left:${at(threshold)}%;width:${roundPct(100-at(threshold))}%"></i>`;
    const track=`<span class="bullet-track">${pass}${threshold===null?'':`<i class="tick" style="left:${at(threshold)}%"></i>`}${current===null?'':`<i class="marker" style="left:${at(current)}%"></i>`}</span>`;
    const text=`<span class="structure-text">Threshold ${stated(cells[v.threshold])} · Current ${stated(cells[v.current])}${v.headroom===null?'':` · Headroom ${shown(cells[v.headroom])}`} · ${esc(direction)}</span>`;
    const inner=`<span class="chart-label">${esc(label)}${unit?`<small>${esc(unit)}</small>`:''}</span>${track}${text}`;
    return `<div class="bullet-row" role="group" aria-label="${esc(label)}">${structureOpen(id,row,inner,`${label}: threshold ${cells[v.threshold]}, current ${cells[v.current]}, ${direction}`,chips)}</div>`;
  }).join('')}</div>`;
}
function limitsChart(id,v,chips=false) {
  const table=fixtureTable(id,v.table);
  return `${chartIntro(id,v)}<div class="limits-chart"><div class="chart-legend"><span><i class="series-0"></i>Current exposure</span><span><i class="series-1"></i>Proposed exposure</span><span><i class="limit-key"></i>Limit</span></div>${table.rows.map(row=>{
    const cells=row.cells,[current,proposed,limit]=[v.current,v.proposed,v.limit].map(c=>chartNumber(cells[c])),at=trackScale([current,proposed,limit]),zero=at(0);
    const bar=(n,series)=>n===null?'':`<i class="series-${series}" style="${n<0?`margin-left:${at(n)}%;`:zero?`margin-left:${zero}%;`:''}width:${roundPct(Math.abs(at(n)-zero))}%"></i>`;
    const track=`<span class="limit-track">${bar(current,0)}${bar(proposed,1)}${limit===null?'':`<i class="tick" style="left:${at(limit)}%"></i>`}</span>`;
    const text=`<span class="structure-text">Current ${stated(cells[v.current])} · Proposed ${stated(cells[v.proposed])} · Limit ${stated(cells[v.limit])}</span>`;
    const inner=`<span class="chart-label">${esc(plain(cells[v.label]))}${v.unit?'':`<small>${esc(cells[cells.length-2])}</small>`}</span>${track}${text}`;
    return `<div class="limit-row" role="group" aria-label="${esc(plain(cells[v.label]))}">${structureOpen(id,row,inner,`${plain(cells[v.label])}: current ${cells[v.current]}, proposed ${cells[v.proposed]}, limit ${cells[v.limit]}`,chips)}</div>`;
  }).join('')}</div>`;
}
// ---- Comparison views: only stated numbers are placed. A change between two stated values is never worked out or written; the two points show it.
const unitOf=row=>row.cells[row.cells.length-2];
// Prior and current results are the period-column chart (kind grouped, `sub` periods under each label); this is the dumbbell, one scale per unit.
function dumbbellChart(id,v,chips=false) {
  const table=fixtureTable(id,v.table),pair=row=>[v.prior,v.current].map(c=>chartNumber(row.cells[c]));
  const scales=new Map([...new Set(table.rows.map(unitOf))].map(unit=>[unit,trackScale(table.rows.filter(r=>unitOf(r)===unit).flatMap(pair))]));
  const legend=`<div class="chart-legend"><span><i class="series-0"></i>${esc(table.headers[v.prior])}</span><span><i class="series-1"></i>${esc(table.headers[v.current])}</span></div>`;
  return `${chartIntro(id,v)}${legend}<div class="dumbbell-chart">${table.rows.map(row=>{
    const cells=row.cells,[prior,current]=pair(row),at=scales.get(unitOf(row)),label=plain(cells[v.label]);
    const link=prior===null||current===null?'':`<i class="dumbbell-link" style="left:${Math.min(at(prior),at(current))}%;width:${roundPct(Math.abs(at(current)-at(prior)))}%"></i>`;
    const dot=(n,series)=>n===null?'':`<i class="dumbbell-dot series-${series}" style="left:${at(n)}%"></i>`;
    const text=`<span class="structure-text">Prior ${shown(cells[v.periods[0]])} ${stated(cells[v.prior])} · Current ${shown(cells[v.periods[1]])} ${stated(cells[v.current])} · ${esc(unitOf(row))}</span>`;
    const inner=`<span class="chart-label">${esc(label)}</span><span class="dumbbell-track">${link}${dot(prior,0)}${dot(current,1)}</span>${text}`;
    return `<div class="dumbbell-row" role="group" aria-label="${esc(label)}">${structureOpen(id,row,inner,`${label}: prior ${cells[v.prior]}, current ${cells[v.current]}`,chips)}</div>`;
  }).join('')}</div>`;
}
// A peer range strip per metric (each on its own scale: a metric has its own unit). The band is drawn only for a stated low that does not exceed the stated high.
function rangeChart(id,v,chips=false) {
  const table=fixtureTable(id,v.table);
  const legend=`<div class="chart-legend"><span><i class="range-key"></i>Peer low to high</span><span><i class="limit-key"></i>Peer median</span><span><i class="series-0"></i>Issuer</span></div>`;
  return `${chartIntro(id,v)}${legend}<div class="range-chart">${table.rows.map(row=>{
    const cells=row.cells,[issuer,low,median,high]=[v.issuer,v.low,v.median,v.high].map(c=>chartNumber(cells[c])),at=trackScale([issuer,low,median,high]),label=plain(cells[v.label]);
    const band=low===null||high===null||low>high?'':`<i class="range-band" style="left:${at(low)}%;width:${roundPct(at(high)-at(low))}%"></i>`;
    const track=`<span class="range-track">${band}${median===null?'':`<i class="tick" style="left:${at(median)}%"></i>`}${issuer===null?'':`<i class="marker" style="left:${at(issuer)}%"></i>`}</span>`;
    const text=`<span class="structure-text">Issuer ${stated(cells[v.issuer])} · Peer low ${stated(cells[v.low])} · Peer median ${stated(cells[v.median])} · Peer high ${stated(cells[v.high])} · Peers ${shown(cells[v.count])} · ${esc(unitOf(row))}</span>`;
    return `<div class="range-row" role="group" aria-label="${esc(label)}">${structureOpen(id,row,`<span class="chart-label">${esc(label)}</span>${track}${text}`,`${label}: issuer ${cells[v.issuer]}, peer range ${cells[v.low]} to ${cells[v.high]}`,chips)}</div>`;
  }).join('')}</div>`;
}
// Yield against maturity: x is the stated maturity date (a real YYYY-MM-DD, first to last placed), y the stated yield on a panel per unit. An instrument with no such date or yield has no point and is still listed.
const isoDate=cell=>/^\d{4}-\d{2}-\d{2}$/.test(cell)&&!Number.isNaN(Date.parse(cell))&&new Date(Date.parse(cell)).toISOString().slice(0,10)===cell;
function scatterChart(id,v,chips=false) {
  const table=fixtureTable(id,v.table),placed=row=>isoDate(row.cells[v.date])&&chartNumber(row.cells[v.yield])!==null,rows=table.rows.filter(placed);
  const dated=rows.map(r=>r.cells[v.date]).sort(),[first,last]=[Date.parse(dated[0]),Date.parse(dated.at(-1))];
  const x=time=>last===first?345:roundPct(60+(time-first)/(last-first)*570);
  const panels=[...new Set(rows.map(unitOf))].map(unit=>{
    const own=rows.filter(r=>unitOf(r)===unit),values=own.map(r=>chartNumber(r.cells[v.yield])),low=Math.min(...values),high=Math.max(...values),pad=(high-low)*.1||.5,y=n=>roundPct(180-(n-low+pad)/(high-low+2*pad)*160);
    const points=own.map(row=>{
      const cx=x(Date.parse(row.cells[v.date])),cy=y(chartNumber(row.cells[v.yield])),name=plain(row.cells[v.label]),said=`${name}, matures ${row.cells[v.date]}, yield ${row.cells[v.yield]} ${unit}`;
      return `<a class="plot-point" href="${evidenceHref(id,row.line)}" data-evidence="${esc(`${id}:${row.line}`)}" aria-label="${esc(said)}. View source"><title>${esc(said)}</title><circle class="point-hit" cx="${cx}" cy="${cy}" r="12"/><circle class="scatter-dot" cx="${cx}" cy="${cy}" r="5"/><text x="${cx}" y="${cy-10}" text-anchor="middle">${esc(row.cells[v.yield])}</text></a>`;
    }).join('');
    return `<p class="matrix-note">Yield, ${esc(unit)}</p><div class="vector-chart"><svg viewBox="0 0 680 220" role="group" aria-label="${esc(`${v.title}, yield in ${unit}. Select a point to inspect its source.`)}"><line class="axis" x1="60" x2="630" y1="190" y2="190"/>${points}<text class="axis-label" x="60" y="210" text-anchor="start">${esc(dated[0])}</text><text class="axis-label" x="630" y="210" text-anchor="end">${esc(dated.at(-1))}</text></svg></div>`;
  }).join('');
  const key=table.rows.map(row=>`<li><span>${sourceLink(`${id}:${row.line}`,row.cells[v.label])}<small>Maturity ${shown(row.cells[v.date])} · Yield ${stated(row.cells[v.yield])} ${esc(unitOf(row))} · Spread ${shown(row.cells[v.spread])} · Quoted ${shown(row.cells[v.quoted])} · ${esc(row.cells[v.source])}</small></span>${chips?chipsMarkup(`${id}:${row.line}`):''}</li>`).join('');
  return `${chartIntro(id,v)}${panels}${rows.length<table.rows.length?'<p class="matrix-note">An instrument with no stated maturity date or yield has no point.</p>':''}<ol class="stack-key">${key}</ol>`;
}
// One column of a column chart from a stated value: a bar from the zero rule, or n.a. with its stated reason. `tag` and `attrs` let a column be a link.
function columnOf(value,i,zero,pct,tag='span',attrs='') {
  const n=chartNumber(value);
  if(n===null)return `<${tag} class="col missing"${attrs}><strong style="bottom:${zero}%"${/[\p{L}\p{N}]/u.test(String(value??''))?` title="${esc(value)}"`:''}>n.a.</strong></${tag}>`;
  const height=pct(Math.abs(n)),bottom=n<0?Math.round((zero-height)*100)/100:zero;
  return `<${tag} class="col"${attrs}><i class="series-${i}${n<0?' negative':''}" style="bottom:${bottom}%;height:${height}%"></i><strong${n<0?' class="below"':''} style="bottom:${n<0?bottom:Math.round((bottom+height)*100)/100}%">${esc(value)}</strong></${tag}>`;
}
// Recovery by class (the owner's table has a row per class and scenario): classes along the axis in first-stated order, a column per scenario
// from a zero baseline on one scale. Claim and Recovery % are shown as stated; no percentage or shortfall is worked out here.
function recoveryChart(id,v,chips=false,note=true) {
  const table=fixtureTable(id,v.table),classes=[...new Set(table.rows.map(r=>r.cells[v.label]))],scenarios=[...new Set(table.rows.map(r=>r.cells[v.scenario]))];
  const numbers=table.rows.map(r=>chartNumber(r.cells[v.recovery])??0),top=Math.max(0,...numbers),low=Math.min(0,...numbers),span=top-low||1,pct=n=>Math.round(n/span*10000)/100,zero=pct(-low);
  const legend=`<div class="chart-legend">${scenarios.map((s,i)=>`<span><i class="series-${i%3}"></i>${esc(s)}</span>`).join('')}</div>`;
  const groups=classes.map(name=>{
    const rows=table.rows.filter(r=>r.cells[v.label]===name);
    const cols=scenarios.map((scenario,i)=>{
      const row=rows.find(r=>r.cells[v.scenario]===scenario);
      if(!row)return `<span class="col missing" title="No row for ${esc(scenario)}"><strong style="bottom:${zero}%">not stated</strong></span>`;
      const said=`${plain(name)}, ${scenario}: recovery ${chartNumber(row.cells[v.recovery])===null?'n.a.':row.cells[v.recovery]} ${unitOf(row)}. View source`;
      return columnOf(row.cells[v.recovery],i%3,zero,pct,'a',` href="${evidenceHref(id,row.line)}" data-evidence="${esc(`${id}:${row.line}`)}" aria-label="${esc(said)}"`);
    }).join('');
    const facts=rows.map(r=>`<small>${esc(r.cells[v.scenario])}: claim ${stated(r.cells[v.claim])} ${esc(unitOf(r))} · recovery ${stated(r.cells[v.recovery])} · ${stated(r.cells[v.percent],'%')}</small>`).join('');
    return `<div class="recovery-group" role="group" aria-label="${esc(plain(name))}"><span class="plot"><span class="zero-rule" style="bottom:${zero}%"></span>${cols}</span><span class="chart-label">${esc(plain(name))}${facts}</span>${chips?rows.map(r=>chipsMarkup(`${id}:${r.line}`)).join(''):''}</div>`;
  }).join('');
  return `${chartIntro(id,v)}<div class="column-chart" style="--periods:${classes.length}">${legend}<div class="periods">${groups}</div></div>${note?'<p class="matrix-note">Missing values have no bar.</p>':''}`;
}
const READER_FIGURES={recovery:recoveryChart,waterfall:bridgeChart,stack:stackChart,bullet:bulletChart,limits:limitsChart,dumbbell:dumbbellChart,range:rangeChart,scatter:scatterChart};
// A reader chart is a "Chart data:" table whose first column is Period, so it is drawn over time: periods along the x axis in table order,
// one column per series from a zero baseline (owner, 2026-11-10). Each period is one button (its handoff row) with its chips under it.
// A step table (store.py: kind "waterfall") is a bridge: opening, stated changes and closing, drawn by bridgeChart; the row tables (kinds stack, bullet, limits) are below.
function readerChart(id,chart,chips=false,note=true) {
  if(READER_FIGURES[chart.kind])return `${READER_FIGURES[chart.kind](id,chart,chips,note)}${chartTableForm(id,chart)}`;
  const table=fixtureTable(id,chart.table),series=chart.columns||[chart.column],rows=(chart.rows||table.rows.map((_,i)=>i)).map(i=>table.rows[i]);
  const numbers=rows.flatMap(row=>series.map(c=>chartNumber(row.cells[c])??0));
  const top=Math.max(0,...numbers),low=Math.min(0,...numbers),span=top-low||1,pct=n=>Math.round(n/span*10000)/100,zero=pct(-low);
  const legend=`<div class="chart-legend">${series.map((c,i)=>`<span><i class="series-${i}"></i>${esc(table.headers[c])}</span>`).join('')}</div>`;
  const periods=rows.map(row=>{
    const key=`${id}:${row.line}`,period=plain(row.cells[0]);
    const cols=series.map((c,i)=>columnOf(row.cells[c],i,zero,pct)).join('');
    const said=series.map(c=>`${table.headers[c]} ${chartNumber(row.cells[c])===null?'n.a.':plain(row.cells[c])}`).join(', ');
    const inner=`<span class="plot"><span class="zero-rule" style="bottom:${zero}%"></span>${cols}</span><span class="chart-label">${esc(period)}${chart.sub?`<small>${chart.sub.map(c=>shown(row.cells[c])).join(' → ')}</small>`:''}</span>`;
    const label=`aria-label="${esc(`${period}: ${said}. View source`)}"`;
    return chips?`<div class="chart-row" role="group" aria-label="${esc(period)}"><button class="chart-open" data-evidence="${esc(key)}" ${label}>${inner}</button>${chipsMarkup(key)}</div>`:`<button class="chart-row" data-evidence="${esc(key)}" ${label}>${inner}</button>`;
  }).join('');
  return `${chartIntro(id,chart)}<div class="column-chart" style="--periods:${rows.length}">${legend}<div class="periods">${periods}</div></div>${note?'<p class="matrix-note">Missing values have no bar.</p>':''}${chartTableForm(id,chart)}`;
}
function readerCharts(id,section) {
  const lines=new Set(sectionData(id,section).flatMap(s=>s.blocks).map(b=>b.line));
  return (data[id].charts||[]).filter(c=>lines.has(c.table)).map(c=>readerChart(id,c)).join('');
}

// ---- The module report: nine parts in one scroll, those the handoff has. Python resolves every citation into window.CREDIT_OS_DATA.chips
// and places every section (data[id].placement, parallel to data[id].sections); nothing below infers a page, a class, a date or a placement.
const REPORT_PARTS=[['head','Module'],['bottom-line','Bottom line'],['numbers','Key numbers'],['findings','Findings'],['analysis','Analysis'],['limits','Limits & monitoring'],['reference','Statements and registers'],['calculations','Calculations'],['audit','Evidence & audit']];
const HANDOFF_TEXT=['handoff-text','Full handoff text'];
// A leading method code (R36) is dropped from a displayed heading or caption.
const METHOD_CODE=/^(?:[A-Z][A-Z0-9]*\.[A-Z]?\d+(?:\s+—\s+|\s+(?=[A-Z]))|[a-z0-9]+(?:\.[a-z0-9_]+)+\s+—\s+)/;
const headingView=(heading,tag,cls='')=>`<${tag}${cls?` class="${cls}"`:''}>${rich(heading.replace(METHOD_CODE,''))}</${tag}>`;
// The sections the store placed here that have something to draw, in handoff order.
const drawn=(id,where)=>data[id].sections.filter((section,i)=>data[id].placement[i]===where&&section.blocks.length);
const DRAWN_PLACEMENTS=['view','reference','calculations','limits'];
// The routable section anchors of an output: the sections a part draws (audit and consumed sections open from the audit list instead).
const drawnAnchors=id=>{
  const {rest,drawings}=isNewFormat(data[id].sections)?newFormatSplit(id):{rest:DRAWN_PLACEMENTS.flatMap(where=>drawn(id,where)),drawings:[]};
  return new Set([...rest,...drawings].map(section=>`s-${section.line}`));
};
// What a chip draws, from the chip dict as the library build emits it. An upstream chip with no module names register codes of the row's own module.
// Only an issuer-page chip has an avatar (its source key); a module is named in the label, never coded.
function chipView(chip,rowModule) {
  if(chip.kind==='issuer_page') {
    const pages=chip.page_end!=null&&chip.page_end!==chip.page?`p.${chip.page}–${chip.page_end}`:`p.${chip.page}`;
    const verified=chip.quote_found===true;
    return {label:pages,av:chip.avatar||chip.source,avClass:'',dot:'',cls:verified?'verified':'',title:verified?'Quote found on page':null};
  }
  if(chip.kind==='upstream') {
    const codes=chip.codes.join(' · ');
    const module=chip.module||rowModule;
    return {label:module?`${moduleTitle(module)} · ${codes}`:codes,av:'',avClass:'',dot:'up',cls:''};
  }
  return {label:chip.label||'no page',av:'?',avClass:'gap',dot:'gap',cls:'gap'};
}
const chipSet=chips=>chips.length?`<span class="chips">${chips.join('')}</span>`:'';
// A gap chip that is not a plain "Not supplied" is a citation with no page: it is counted, not drawn.
const unresolvedGap=chip=>chip.kind==='gap'&&chip.label!=='Not supplied';
const gapCount=n=>`${n} unresolved citation${n===1?'':'s'}`;
// The "Row" chip comes from the evidence key itself; the others from the chips map, by index (the index counts every chip of the key).
function chipsMarkup(key,counted=true) {
  const item=evidence.get(key),found=window.CREDIT_OS_DATA?.chips?.[key]||[];
  const row=item?window.Components.traceRow(key,`Table row, line ${item.line}`):'';
  const gaps=found.filter(unresolvedGap).length;
  const count=counted&&gaps?`<button type="button" class="chip-count" data-gaps="${esc(key)}">${gapCount(gaps)}</button>`:'';
  return chipSet([row,...found.map((chip,index)=>{
    if(unresolvedGap(chip))return '';
    const view=chipView(chip,item?.module),title=view.title||chip.reason;
    return `<button type="button" class="chip ${view.cls}" data-chip="${esc(key)}" data-index="${index}" ${title?`title="${esc(namedText(title,item?.output))}"`:''}>${view.av?`<span class="av ${view.avClass}">${esc(view.av)}</span>`:''}${esc(view.label)}<span class="dot ${view.dot}"></span></button>`;
  }),count].filter(Boolean));
}
const isFindingsTable=b=>b.type==='table'&&b.headers[0]==='Finding'&&b.headers[1]==='Creditor impact';
// The first table of the reference sections with two or more numeric columns, capped at 8 rows and 6 columns (5 handoff columns and the Source column).
function keyNumbersChoice(id) {
  for(const section of drawn(id,'reference')) {
    for(const block of section.blocks) {
      if(block.type!=='table'||isFindingsTable(block)||block.headers[0]==='Bottom line')continue;
      const numeric=block.headers.map((_,c)=>numericColumn(block,c));
      if(numeric.filter(Boolean).length<2)continue;
      const short=block.headers.map((_,c)=>c===0||numeric[c]||block.rows.every(r=>(r.cells[c]??'').length<=24));
      return {section,block,numeric,columns:block.headers.map((_,c)=>c).filter(c=>short[c]).slice(0,5),rows:block.rows.slice(0,8)};
    }
  }
  return null;
}
// A column whose cells are all bare step ids names nothing the reader can use: it is not drawn.
const stepColumn=(block,c)=>block.rows.length>0&&block.rows.every(r=>STEP_ID.test(plain(r.cells[c]??'').trim()));
const sourceTable=(id,caption,block,numeric,allColumns,rows)=>{
  const columns=allColumns.filter(c=>!stepColumn(block,c));
  return `<div class="table-card"><table><caption class="sr-only">${esc(plain(caption).replace(METHOD_CODE,''))}</caption><thead><tr>${columns.map(c=>`<th scope="col"${numeric[c]?' class="num"':''}>${esc(block.headers[c])}</th>`).join('')}<th scope="col">Source</th></tr></thead><tbody>${rows.map(row=>`<tr>${columns.map(c=>cellView(row.cells[c],numeric[c])).join('')}<td>${chipsMarkup(`${id}:${row.line}`)}</td></tr>`).join('')}</tbody></table>`;
};
function keyNumbers(id) {
  const pick=keyNumbersChoice(id);
  if(!pick)return '';
  const {section,block,numeric,columns,rows}=pick;
  return `${sourceTable(id,section.heading,block,numeric,columns,rows)}${block.rows.length>rows.length?`<p class="table-more">${block.rows.length-rows.length} more rows are under Statements and registers.</p>`:''}</div>`;
}
// The front matter's committee_status, verbatim; none declared draws nothing. The title says whose word it is.
const declaredBadge=declared=>declared==null?'':`<span class="badge badge-gray" title="Status the module declares in its handoff">${esc(declared)}</span>`;
const LEGEND='<div class="legend"><span>Chip dot: <i class="dot"></i> issuer page · <i class="dot row"></i> this table row · <i class="dot up"></i> another module · <i class="dot gap"></i> gap</span></div>';
// No catalogue field says "accepted"; a run shows a checklist only when one is recorded (none is today), and that is not acceptance.
function runAcceptanceText(context) {
  const record=window.DESIGN_CATALOGUE.real.find(r=>r.id===contexts[context].folder);
  return record?.checklist?'Acceptance checklist recorded':'Candidate · not accepted';
}
// The score Python computed from the module's confidence inputs table (the store's `confidence`), or why there is none; an output with no such table draws nothing.
const confidenceText=c=>!c?'':`<span class="output-meta" title="Computed from the inputs the module states">${c.missing!=null?`Confidence not computed: ${esc(c.missing)}`:`Confidence ${esc(c.value)} · ${esc(c.band)}`}</span>`;
function reportHead(id) {
  const out=data[id],{module,run:context}=out;
  const {meta,flag}=headTools(module,context,id);
  const acceptance=runAcceptanceText(context);
  const declared=declaredBadge(out.state.declared);
  const notAssessable=isNewFormat(out.sections)&&blocked(out.sections,out.state)?badge('gray','Not assessable'):'';
  const group=groups.find(([,items])=>items.some(item=>item[0]===module))?.[0];
  // A bottom line: the earlier format's Reader summary or call; the new format's Bottom line passage. With one, the name is the eyebrow and the bottom line the headline.
  const hasBottom=isNewFormat(out.sections)?Boolean(readerPassages(out.sections).bottom):Boolean(out.summary||out.call);
  return `<div class="module-head${hasBottom?' has-bottom-line':''}" id="head"><div class="head-title">${group?`<span class="head-group">${esc(group)}</span>`:''}<h2>${esc(moduleNames[module])}</h2></div><div class="head-tools">${notAssessable}<span class="badge badge-gray">${acceptance}</span>${declared}${meta}${flag}${confidenceText(out.confidence)}<a class="btn" href="${esc(out.href)}" download>${icon('download')}Handoff</a></div></div>`;
}
function reportBand(id) {
  const {summary,call,source}=data[id],quoted=summary?{text:summary.bottomLine,line:summary.line}:call;
  if(!quoted)return '';
  const facts=summary?`<dl><span class="row"><dt>Confidence</dt><dd>${esc(summary.confidence)}</dd></span><span class="row"><dt>Main limitation</dt><dd>${rich(summary.limitation)}</dd></span></dl>`:'';
  return `<div class="band" id="bottom-line"><p>${rich(quoted.text.replace(/\n/g,' '))}</p>${facts}<div class="src"><span class="badge badge-gray">Quoted from the handoff</span><button type="button" class="band-link" data-evidence="${esc(`${id}:${quoted.line}`)}" title="${esc(`${handoffLabel(source)}, line ${quoted.line}`)}">View source</button></div></div>`;
}
// One chip-dot legend per set of charts, under the last card.
// A card sits under a module's h3, so its chart title is an h4 there. ponytail: retagged here, where cards are made; chartIntro writes the h2 for a chart that stands alone, and threading a level through every chart kind would touch eight call sites.
const cardTitle=chart=>chart.replace(/<div class="section-heading"><h2>(.*?)<\/h2>/s,'<div class="section-heading"><h4>$1</h4>');
// The index of the last period chart: the waterfall is not a column chart, so "Missing values have no bar" prints under the last one that is.
const lastPeriodChart=charts=>charts.findLastIndex(c=>!c.kind||c.kind==='grouped'||c.kind==='recovery');
const chartCards=charts=>charts.map((chart,at)=>`<div class="panel-card">${cardTitle(chart)}${at===charts.length-1?LEGEND:''}</div>`).join('');
function reportNumbers(id) {
  // The "Missing values have no bar" note prints once for the part, under its last chart, as on the run report.
  const charts=reportChartCards(id),table=keyNumbers(id);
  return charts||table?`<section class="part" id="numbers"><h3>Key numbers</h3>${charts+table}</section>`:'';
}
// Finding rows are the store's: summary.findings, the Reader summary's second table (null summary, none).
const findingRows=id=>data[id].summary?.findings??[];
function findingArticle(id,row) {
  return `<article class="finding"><h4>${rich(row.finding)}</h4><p class="impact"><b>Creditor impact</b>${rich(row.impact)}</p><p class="finding-line"><span class="conf">Confidence ${esc(plain(row.confidence))}</span>${basisButton(`${id}:${row.line}`,[],`Basis for finding: ${plain(row.finding)}`)}</p></article>`;
}
function reportFindings(id) {
  const articles=findingRows(id).map(row=>findingArticle(id,row));
  return articles.length?`<section class="part" id="findings"><h3>Findings</h3>${articles.join('')}</section>`:'';
}
// Sections drawn whole, in the order given. Heading tags are relative to the shallowest section (R33a), one step per level, capped at h6; the part heading stays the only h3.
function readingSections(id,sections,base=4) {
  const top=Math.min(...sections.map(section=>section.level));
  return sections.map(section=>{
    const tag='h'+Math.min(6,base+(section.level-top||0));
    return `<div class="analysis-section" id="s-${section.line}">${headingView(section.heading,tag)}${section.blocks.map(block=>{
      if(block.type==='table')return `${sourceTable(id,section.heading,block,block.headers.map((_,c)=>numericColumn(block,c)),block.headers.map((_,c)=>c),block.rows)}</div>`;
      return `<p class="analysis-text">${paragraphView(block.text,`${id}:${block.line}`,{earlier:true,chips:bodyContext(id,false).chips(`${id}:${block.line}`)}).html}</p>`;
    }).join('')}</div>`;
  }).join('');
}
function reportAnalysis(id) {
  const sections=drawn(id,'view');
  return sections.length?`<section class="part" id="analysis"><h3>Analysis</h3>${readingSections(id,sections)}</section>`:'';
}
// A closed part: nothing is cut, it opens to the whole sections (a hash route or a chip into it opens it, screen.js).
// The summary is a row: its title, then a detail (it may be empty) drawn at the right.
function fold(anchor,title,detail,body) {
  return `<details class="fold" id="${anchor}"><summary>${icon('chevron-right')}<span class="fold-title">${esc(title)}</span>${detail?` <span class="fold-detail">${esc(detail)}</span>`:''}</summary>${body}</details>`;
}
function reportReference(id) {
  const sections=drawn(id,'reference');
  if(!sections.length)return '';
  const tables=sections.flatMap(section=>section.blocks).filter(block=>block.type==='table');
  return fold('reference','Statements and registers',`${plural(tables.length,'table')} · ${plural(tables.reduce((n,block)=>n+block.rows.length,0),'row')}`,readingSections(id,sections));
}
function reportCalculations(id) {
  const sections=drawn(id,'calculations');
  return sections.length?fold('calculations','Calculations',`${data[id].words.calculations} words`,readingSections(id,sections)):'';
}
function reportLimits(id) {
  const row=(key,label,html)=>`<p>${html} ${basisButton(key,[],`Basis for row: ${plain(label)}`)}</p>`;
  const cards=drawn(id,'limits').map(section=>`<div id="s-${section.line}">${headingView(section.heading,'h4')}${section.blocks.flatMap(block=>block.type==='table'?block.rows.map(r=>row(`${id}:${r.line}`,r.cells[0],`<strong>${rich(r.cells[0])}</strong> ${r.cells.slice(1).map(rich).join(' · ')}`)):[`<p>${paragraphView(block.text,`${id}:${block.line}`,{earlier:true,chips:bodyContext(id,false).chips(`${id}:${block.line}`)}).html}</p>`]).join('')}</div>`);
  return cards.length?`<section class="part" id="limits"><h3>Limits &amp; monitoring</h3><div class="limits">${cards.join('')}</div></section>`:'';
}
// The sections no part draws, as a line-numbered list; a section's content is drawn when it is opened (screen.js). An entry is listed when a section it holds
// is placed audit or consumed; the `audit` entry is always listed, for the original-output block it opens with.
function reportAudit(id) {
  const out=data[id],kept=['audit','consumed'];
  const listed=modules[id].sections.filter(([sectionId])=>sectionId==='audit'||sectionData(id,sectionId).some(section=>kept.includes(out.placement[out.sections.indexOf(section)])));
  return `<details class="audit" id="audit"><summary>${icon('chevron-right')}<span class="fold-title">Evidence &amp; audit</span> <span class="fold-detail">${plural(out.sections.length,'section')} · unchanged from the handoff</span></summary><ul class="audit-list">${listed.map(([sectionId,label])=>{
    const first=sectionData(id,sectionId)[0];
    return `<li><button type="button" class="audit-open" data-audit="${esc(sectionId)}" aria-expanded="false" aria-controls="audit-${esc(sectionId)}">${esc(label)}${first?`<span>L${first.line}</span>`:''}</button><div class="audit-body" id="audit-${esc(sectionId)}" hidden></div></li>`;
  }).join('')}</ul></details>`;
}
// A module that reaches no conclusion (established false) keeps its head, band, findings and limits; the reading and reference parts fold under one closed disclosure.
function reportParts(id) {
  if(isNewFormat(data[id].sections))return newFormatParts(id);
  const out=data[id],folded=out.state.established===false,label=anchor=>anchor==='maps'?'Maps':anchor==='timeline'?'Timeline':REPORT_PARTS.find(part=>part[0]===anchor)[1];
  const analysis=reportAnalysis(id),reference=reportReference(id),calculations=reportCalculations(id),limits=reportLimits(id);
  const {view,reference:referenceWords,calculations:calculationWords}=out.words;
  const parts=[['head',reportHead(id)],['bottom-line',reportBand(id)]];
  if(folded)parts.push(['findings',reportFindings(id)],['limits',limits],['maps',reportMaps(id)],['timeline',reportTimeline(id)],[HANDOFF_TEXT[0],analysis+reference+calculations?fold('handoff-text','Full handoff text',`${view+referenceWords+calculationWords} words`,analysis+reference+calculations):'']);
  else parts.push(['numbers',reportNumbers(id)],['findings',reportFindings(id)],['analysis',analysis],['limits',limits],['reference',reference],['calculations',calculations],['maps',reportMaps(id)],['timeline',reportTimeline(id)]);
  parts.push(['audit',reportAudit(id)]);
  return parts.filter(([,html])=>html).map(([anchor,html])=>[anchor,anchor===HANDOFF_TEXT[0]?HANDOFF_TEXT[1]:label(anchor),html]);
}
// ---- The module page of a new-format handoff (ruling H1, H4; library redesign, Task 4). The page draws sections by role (Shapes.sectionRole): the four passages as
// components (Bottom line, Key findings beside What would change the view, Limitations with the gap signal), the module's `finding` and `drawing` sections in handoff
// order, and nothing else. Sources, Calculations, Gaps, registers, method notes and the sections written for other modules are the Evidence page's (or drawn nowhere).
const passageSections=id=>Object.values(readerPassages(data[id].sections)).filter(Boolean);
// A finding section has something to draw when it holds a prose block that is not a note, or a table with a row and a column the reader sees.
const drawsSomething=section=>section.blocks.some(block=>block.type==='table'?block.rows.length>0&&window.Shapes.hiddenColumns(block.headers,'records').length<block.headers.length:window.Shapes.blockRole(block.text)!=='note');
// Ruling 2026-11-12, decisions 1 and 2. A chart, map or timeline is drawn once, in its panel: the `Chart data:`, `Map:` or `Events:` section the store drew is `drawings`
// (its numbers are the drawing's Table form, its prose the caption). A drawing section the store could not draw has no drawing, so it stays in the body with the
// findings. A section that is not a passage, finding or drawing (its role says Evidence or nowhere) is in neither list.
function newFormatSplit(id) {
  const held=new Set(passageSections(id)),drawnTables=new Set([...(data[id].charts||[]),...(data[id].chartGaps||[]),...(data[id].maps||[]),...(data[id].events||[])].map(drawing=>drawing.table));
  const split={rest:[],drawings:[]};
  for(const {section,role} of window.Evidence.classify(data[id].sections,data[id].placement)) {
    if(held.has(section)||!section.blocks.length)continue;
    if(role==='drawing'&&section.blocks.some(block=>block.type==='table'&&drawnTables.has(block.line)))split.drawings.push(section);
    else if(['finding','drawing','passage'].includes(role)&&drawsSomething(section))split.rest.push(section);
  }
  return split;
}
// The section that holds a drawing's table. On a new-format page it gives the drawing its route (s-<line>) and its caption: the section's prose, in order.
const drawingSection=(id,table)=>isNewFormat(data[id].sections)?data[id].sections.find(section=>section.blocks.some(block=>block.type==='table'&&block.line===table)):undefined;
const drawingAnchor=(id,table)=>{const section=drawingSection(id,table);return section?` id="s-${section.line}"`:'';};
function drawingCaption(id,table) {
  const section=drawingSection(id,table);
  return section?.blocks.some(block=>block.type==='text')?`<div class="drawing-caption">${sectionBodyHtml(section,bodyContext(id,false))}</div>`:'';
}
// The module's own charts, one card each; the Key numbers part of an earlier-format page draws the same cards.
const reportChartCards=id=>chartCards((data[id].charts||[]).map((c,at,all)=>readerChart(id,c,true,at===lastPeriodChart(all))));
// A new-format page's cards: a chart with no numbers (store `chartGaps`) is a card saying why, in table-line order with the charts; each card has its section route and caption.
function newFormatChartCards(id) {
  const charts=data[id].charts||[],last=lastPeriodChart(charts);
  const cards=[...charts.map((chart,at)=>({table:chart.table,html:readerChart(id,chart,true,at===last)})),...(data[id].chartGaps||[]).map(gap=>({table:gap.table,gap}))].sort((a,b)=>a.table-b.table);
  const lastChart=cards.findLastIndex(card=>!card.gap);
  return cards.map((card,at)=>{
    const body=card.gap?`<div class="section-heading"><h4>${esc(card.gap.title)}</h4></div><p class="lane-gap">${NOT_ESTABLISHED}<small>${esc(card.gap.gap)}</small></p>${gapTableForm(id,card.gap.title,card.table)}`:cardTitle(card.html);
    return `<div class="panel-card"${drawingAnchor(id,card.table)}>${body}${drawingCaption(id,card.table)}${at===lastChart?LEGEND:''}</div>`;
  }).join('');
}
// An output with Events lanes draws them; an earlier-format one that has an event table and no lane draws that table as a timeline.
function reportTimeline(id) {
  const html=eventLanesView(data[id].run,{only:id,compact:true,tag:'h3',title:'Timeline'});
  if(html)return `<section class="part" id="timeline">${html}</section>`;
  const table=eventTable(data[id].sections);
  return table?`<section class="part" id="timeline">${eventTimeline(id,table,'h3')}</section>`:'';
}
// What a paragraph's drawing needs of the page: its output, the chips the build holds for a key, and the table caption without a method code.
const bodyContext=(id,tables)=>({id,tables,chips:key=>(window.CREDIT_OS_DATA?.chips?.[key]||[]).length,chipList:key=>window.CREDIT_OS_DATA?.chips?.[key]||[],caption:heading=>plain(heading).replace(METHOD_CODE,'')});
// The handoff's own heading levels: its H2 sections are h3 (the page's h2 is the module), their H3 children h4, capped at h6.
const newFormatTag=section=>'h'+Math.min(6,3+section.level-2);
// A finding section of the module page: its prose as written (a method or status note is Evidence's) and each table as record cards until its own component lands.
const findingSection=(id,section)=>{
  const ctx={...bodyContext(id,true),skip:block=>block.type==='text'&&window.Shapes.blockRole(block.text)==='note',table:(block,at)=>window.Components.recordCards(block,{key:row=>`${id}:${row.line}`,caption:plain(at.heading).replace(METHOD_CODE,'')})};
  return `<div class="analysis-section" id="s-${section.line}">${headingView(section.heading,newFormatTag(section))}${sectionBodyHtml(section,ctx)}</div>`;
};
const passageTexts=section=>(section?section.blocks.filter(block=>block.type==='text').map(block=>({text:block.text,line:block.line})):[]);
// The gaps the module records: the rows of the tables of its Gaps sections, counted as the Evidence page lists them.
const recordedGaps=id=>window.Evidence.classify(data[id].sections,data[id].placement).filter(({role})=>role==='gaps').reduce((total,{section})=>total+section.blocks.filter(block=>block.type==='table'&&window.Evidence.tableView(block)).reduce((rows,block)=>rows+block.rows.length,0),0);
const tableRows=section=>section.blocks.filter(block=>block.type==='table').reduce((rows,block)=>rows+block.rows.length,0);
// The line of the first section that holds one of a drawing's tables: where in the handoff the drawing stood.
const drawingLine=(id,drawings)=>Math.min(...(drawings||[]).map(drawing=>drawingSection(id,drawing.table)?.line??Infinity));
// A part is [anchor, label, html, count?]; `count` is the number of listed items the rail shows beside the label.
function newFormatParts(id) {
  const out=data[id],passages=readerPassages(out.sections),texts=Object.fromEntries(Object.entries(passages).map(([key,section])=>[key,passageTexts(section)]));
  const controls=key=>passageControls(texts[key],bodyContext(id,false));
  const parts=[['head','Module',reportHead(id)]];
  // The Findings heading above the passages stays in the page for headings and screen readers (sr-only).
  const findings=out.sections.find(section=>section.level===2&&section.heading==='Findings');
  const verdict=window.Components.verdictPanel(texts.bottom,controls('bottom').trace,controls('bottom').figure);
  if(verdict)parts.push(['bottom-line','Bottom line',`<section class="part" id="bottom-line">${findings&&!findings.blocks.length?`<h3 class="sr-only">${rich(findings.heading)}</h3>`:''}${verdict}</section>`]);
  const feed=window.Components.findingsFeed(texts.key,controls('key').trace,controls('key').figure);
  const change=window.Components.callout('What would change the view',texts.contrary,controls('contrary').trace,controls('contrary').figure);
  if(feed||change) {
    const both=Boolean(feed&&change);
    parts.push(['key-findings',feed?'Key findings':'What would change the view',`<section class="part key-row g24" id="key-findings">${feed?`<div class="${both?'c14':'c24'}"><div class="rd-card"><h4 class="rd-h">Key findings</h4>${feed}</div></div>`:''}${change?`<div class="${both?'c10':'c24'}" id="contrary-evidence">${change}</div>`:''}</section>`,texts.key.length]);
  }
  // Charts, timeline and maps keep their renderers; each stands where its section stood in the handoff, among the finding sections.
  const body=[],charts=newFormatChartCards(id),maps=reportMaps(id),timeline=reportTimeline(id);
  if(charts)body.push([drawingLine(id,[...(out.charts||[]),...(out.chartGaps||[])]),['charts','Charts',`<section class="part" id="charts"><h3>Charts</h3>${charts}</section>`]]);
  if(timeline)body.push([drawingLine(id,out.events),['timeline','Timeline',timeline]]);
  if(maps)body.push([drawingLine(id,out.maps),['maps','Maps',maps]]);
  for(const section of newFormatSplit(id).rest) {
    const rows=tableRows(section);
    body.push([section.line,[`s-${section.line}`,plain(section.heading.replace(METHOD_CODE,'')),`<section class="part">${findingSection(id,section)}</section>`,...(rows?[rows]:[])]]);
  }
  parts.push(...body.sort((a,b)=>(a[0]<b[0]?-1:a[0]>b[0]?1:0)).map(([,part])=>part));
  const limits=window.Components.limitationsBlock(texts.limits,recordedGaps(id),window.Evidence.href('gaps',out.module,out.run),controls('limits').trace,controls('limits').figure);
  if(limits)parts.push(['limitations','Limitations',`<section class="part" id="limitations"><div class="rd-card"><h4 class="rd-h">Limitations</h4>${limits}</div></section>`,texts.limits.length]);
  return parts;
}
// The module page: the head, then (new format) the section rail beside the parts. An earlier-format page is its parts in a row, as it always was.
const railItems=id=>reportOutline(id).filter(([anchor])=>anchor!=='head').map(([anchor,label,,count])=>({id:anchor,label,count,href:routeHref(data[id].module,anchor,null,data[id].run)}));
function moduleReport(id) {
  const parts=reportParts(id);
  if(!isNewFormat(data[id].sections)||parts.length<2)return parts.map(part=>part[2]).join('');
  return `${parts[0][2]}<div class="g24 module-grid"><div class="c5 module-rail">${window.Components.sectionRail(railItems(id))}</div><div class="c19 module-main">${parts.slice(1).map(part=>part[2]).join('')}</div></div>`;
}
// What the outline and the section list show: each present part's anchor and label (and its count, where the page shows one). Presence depends on the data only, so it is built once per output.
const outlineCache=new Map();
function reportOutline(id) {
  if(!outlineCache.has(id))outlineCache.set(id,reportParts(id).map(([anchor,label,,count])=>(count===undefined?[anchor,label,[]]:[anchor,label,[],count])));
  return outlineCache.get(id);
}
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
  // A compared deliverable is named by its build folder: the delivered report is retired, so there is nothing in the app to open.
  const reportLink=reportId=>`<span class="code">${esc(reportId)}</span>`;
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
// The Evidence page's trace view of one module of the run: routeHref encodes the run (`c`) once; the module (`m`) is encoded the same way (URLSearchParams), which parseRoute reads back.
function traceHref(moduleId,context=current?.context) {
  const base=routeHref('W-Evidence','trace',null,context,null),module=new URLSearchParams({m:moduleId});
  return `${base}${base.includes('?')?'&':'?'}${module}`;
}
// The drawer's last element: the way from one traced item to the whole trace of its module in the Evidence page.
function drawerFoot(moduleId,context=current?.context) {
  return `<div class="drawer-foot"><a class="text-action" href="${esc(traceHref(moduleId,context))}">Open in Evidence${icon('arrow-right')}</a></div>`;
}
function outlineMarkup(id) {
  if(isNewFormat(data[id].sections))return ''; // the page's own section rail is its outline
  const module=data[id].module||id;
  return `<nav class="section-outline" aria-label="On this page"><p class="outline-heading" aria-hidden="true">On this page</p><ol>${reportOutline(id).map(([part,label])=>`<li><a class="section-item" href="${routeHref(module,part)}" ${current.section===part?'aria-current="location"':''}>${esc(label)}</a></li>`).join('')}</ol></nav>`;
}
function unavailableView(module) {
  const ctx=contexts[current.context];
  const others=Object.entries(contexts).filter(([key,run])=>key!==current.context&&sameIssuer(run.issuerKey,ctx.issuerKey)&&run.modules[module]?.outputs.length);
  return `<div class="missing-state"><div class="empty-symbol">${icon('file-text')}</div><h2>${NO_OUTPUT}</h2></div>${others.length?`<div class="available-case"><h3>Other ${esc(ctx.issuer)} runs with this module</h3>${others.map(([key,run])=>`<p><a class="text-action" href="${routeHref(module,firstSection(module,key),null,key)}">${esc(runName(run))}${icon('arrow-right')}</a></p>`).join('')}</div>`:''}`;
}
function outputChooser(module) {
  const ctx=contexts[current.context],files=moduleEntry(module,current.context).outputs;
  return `<div class="missing-state"><div class="empty-symbol">${icon('file-text')}</div><h2>Choose a saved output</h2><p>${files.length} versions of this analysis. Choose one to read.</p></div><div class="output-choices">${files.map(id=>`<a class="text-action" href="${routeHref(module,modules[id].first,null,current.context,data[id].source)}">${esc(data[id].label)}${icon('arrow-right')}</a>`).join('')}</div>`;
}
// ---- Calendar lanes: one lane per module output that carries an `Events: <lane>` table (store.py event lanes), on one shared date axis.
// A lane is named by the table's heading, so no module code is shown. `gap` is the stated reason when the module supplied no dated event.
function eventLanes(context) {
  return Object.values(contexts[context]?.modules||{}).flatMap(entry=>{
    const id=entry.default||entry.outputs[0];
    return (data[id]?.events||[]).map(lane=>({...lane,id}));
  });
}
// A day is a point; a month, quarter or year is drawn across its whole span (calendar.js eventSpan), never on a day the source does not state.
// `compact` is the lanes alone, without the intro and the event table. Scenario events have an outline.
// Where each kind of chart table is drawn besides its module page. The views that draw them and the chart index both read this table.
// Overview charts and maps are the visuals catalogue's own placement (docs/visualisations/catalogue.csv, window.DESIGN_WORKSPACE.visuals) for a module that is not blocked.
const onOverview=out=>{const code=aliases[out.module]??out.module;return window.DESIGN_WORKSPACE.visuals.some(visual=>visual.module===code&&/\bOverview\b/.test(visual.placement))&&!blocked(out.sections,out.state);};
// A lane is not drawn on the Overview: its dated rows feed the Overview's nearest dates (overviewDates), which is what 'Overview' means for a lane.
const PLACEMENT=[['chart','Overview',onOverview],['map','Overview',onOverview],['lane','Overview',()=>true]];
const placed=(kind,where,out,name)=>PLACEMENT.some(([k,w,test])=>k===kind&&w===where&&test(out,name));
const LANE_ROW=20,LANE_BASE=4; // a lane row is one marker (16 px) and its gap; the lane's floor is 28 px
function eventLanesView(context,{compact=false,only=null,tag='h2',title='Event lanes'}={}) {
  // `only` is one output's own lanes, whichever saved output it is; otherwise the run's lanes (each module's default output).
  const lanes=(only?(data[only]?.events||[]).map(lane=>({...lane,id:only})):eventLanes(context)).map(lane=>({...lane,events:lane.gap!==null?[]:fixtureTable(lane.id,lane.table).rows.map(row=>({row,span:eventSpan(row.cells[0],row.cells[1])}))}));
  if(!lanes.length)return '';
  const scenario=row=>/^Scenario — /.test(row.cells[4]),day=n=>new Date(n*86400000).toISOString().slice(0,10);
  const axis=eventAxis(lanes.flatMap(lane=>lane.events.flatMap(({span})=>span?[span]:[])));
  const link=(lane,row)=>`href="${evidenceHref(lane.id,row.line)}" data-evidence="${esc(`${lane.id}:${row.line}`)}"`;
  // Each lane's drawn events get a number in date order, continuing across lanes (the key names them), and a level: a marker that would overlap one already drawn goes up, never sideways.
  let count=0;
  const drawn=lanes.map(lane=>{
    const items=lane.events.filter(e=>e.span).map(e=>({...e,...eventPlace(e.span,axis)})),start=count+1;
    [...items.keys()].sort((a,b)=>items[a].span.from-items[b].span.from||items[b].span.to-items[a].span.to||a-b).forEach(i=>{items[i].no=++count;items[i].chip=Math.max(16,7*String(count).length+4);}); // the chip grows with its digits (11 px mono, 7 px a digit and 4 px padding)
    const levels=eventStack(items);
    items.forEach((item,i)=>{item.level=levels[i];item.anchored=eventRoom(item)[2];}); // a thin span at the right end keeps its number inside the track: it is drawn from its right edge
    return {lane,items,start,height:Math.max(28,2*LANE_BASE+(Math.max(-1,...levels)+1)*LANE_ROW)};
  });
  const marker=(lane,{row,span,left,width,no,level,anchored})=>{
    const [date,precision,,event]=row.cells;
    return `<a class="lane-event ${span.point?'point':'span'}${anchored?' anchored':''}${scenario(row)?' scenario':''}" ${link(lane,row)} aria-label="${esc(`Event ${no}: ${lane.lane}: ${event}${scenario(row)?' (Scenario event)':''}, ${date} (${precision}). View source`)}" style="${anchored?`right:${Math.round((100-left-width)*100)/100}%`:`left:${left}%`}${span.point?'':`;width:${width}%`};bottom:${LANE_BASE+level*LANE_ROW}px"><span class="lane-no">${no}</span></a>`;
  };
  const own=Boolean(only)&&isNewFormat(data[only].sections); // a new-format module page: each lane is its section's route and caption, its events a Table form
  const rows=drawn.map(({lane,items,height})=>`<div class="lane-row"${own?drawingAnchor(lane.id,lane.table):''}><span class="lane-name">${esc(lane.lane)}</span>${lane.gap!==null?`<span class="lane-gap">Not established for this run<small>${esc(lane.gap)}</small></span>`:`<span class="lane-track" style="height:${height}px">${items.map(item=>marker(lane,item)).join('')}</span>`}</div>${own?drawingCaption(lane.id,lane.table)+(lane.gap!==null?gapTableForm(lane.id,lane.lane,lane.table):''):''}`).join('');
  const key=drawn.filter(({items})=>items.length).map(({lane,items,start})=>`<p class="lane-key-name">${esc(lane.lane)}</p><ol class="lane-key" start="${start}">${[...items].sort((a,b)=>a.no-b.no).map(({row})=>`<li><span class="lane-key-date">${esc(row.cells[0])}</span> ${rich(row.cells[3])}${scenario(row)?' (Scenario event)':''}</li>`).join('')}</ol>`).join('');
  const asOf=contexts[context]?.asOf,asOfAt=eventAsOf(axis,asOf);
  const ticks=eventTicks(axis);
  const scale=axis?`<span class="lane-scale">${asOfAt===null?'':`<span class="lane-asof-label${asOfAt>50?' end':''}" style="left:${asOfAt}%">As of ${esc(displayDate(asOf))}</span>`}${ticks.map(t=>`<span class="lane-tick" style="left:${t.left}%"></span>`).join('')}${ticks.filter(t=>t.label).map(t=>`<span class="lane-tick-label" style="left:${t.left}%">${esc(t.label)}</span>`).join('')}</span>`:'';
  const overlay=axis?`<div class="lane-overlay" aria-hidden="true"><span></span><span>${ticks.map(t=>`<i class="lane-grid" style="left:${t.left}%"></i>`).join('')}${asOfAt===null?'':`<i class="lane-asof" style="left:${asOfAt}%"></i>`}</span></div>`:'';
  const body=lanes.flatMap(lane=>lane.events.map(({row})=>{
    const [date,precision,published,event,status,source,relevance]=row.cells;
    return `<tr><td>${esc(lane.lane)}</td><td>${esc(date)}</td><td>${esc(precision)}</td><td>${esc(published)}</td><td><a class="event-link" ${link(lane,row)}>${rich(event)}</a></td><td>${rich(status)}</td><td>${rich(source)}</td><td>${rich(relevance)}</td></tr>`;
  })).join('');
  const head=['Lane','Event date','Date precision','Published','Event','Status','Source','Credit relevance'].map(h=>`<th scope="col">${h}</th>`).join('');
  const eventTableHtml=`<table class="event-table"><caption>All events, by lane</caption><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  const intro=compact?'':'<p class="intro">Each lane is one module’s dated events on a shared date axis. A day is a point; a month, quarter or year is drawn across its whole span, not on a day the source does not state. A dashed outline is a Scenario event.</p>';
  return `<div class="event-lanes${compact?' compact':''}"><div class="section-heading"><${tag}>${esc(title)}</${tag}><span>Dated events by module</span></div>${intro}<div class="lane-scroll" role="region" tabindex="0" aria-label="Event lanes; scroll horizontally on a narrow screen"><div class="lane-plot">${axis?`<div class="lane-axis"><span></span>${scale}</div>`:''}<div role="group" aria-label="Event lanes on a shared date axis">${rows}</div>${overlay}</div></div>${key?`<div class="lane-keys" role="group" aria-label="Key to the numbered events"><p class="lane-range">Axis from ${day(axis.start)} to ${day(axis.end)}</p>${key}</div>`:''}${body?(compact?own?`<details class="chart-table"><summary>Table form</summary>${eventTableHtml}</details>`:'':eventTableHtml):''}</div>`;
}
// ---- Maps: one layered left-to-right SVG for every node/edge map (store.py `maps`), the edge table beneath as its accessible form.
// A layer is the longest path from a node with no incoming edge. An edge that would close a loop is cut by first-seen row order and still drawn, below the nodes.
// Nothing is weighted: the edge type is a word label and a line style, and the only coordinates are the layout's.
function mapLayers(edges,nodes=[]) {
  const into=new Map(),out=new Map(),layer=new Map(),names=[];
  const reaches=(from,to,seen=new Set())=>from===to||(!seen.has(from)&&seen.add(from)&&(out.get(from)||[]).some(next=>reaches(next,to,seen)));
  const cut=edges.map(({from,to})=>{
    for(const name of [from,to])if(!names.includes(name))names.push(name);
    if(reaches(to,from))return true;
    out.set(from,[...(out.get(from)||[]),to]);into.set(to,[...(into.get(to)||[]),from]);
    return false;
  });
  for(const name of nodes)if(!names.includes(name))names.push(name);
  const depth=name=>{if(!layer.has(name))layer.set(name,Math.max(-1,...(into.get(name)||[]).map(depth))+1);return layer.get(name);};
  names.forEach(depth);
  return {names,layer:new Map(names.map(name=>[name,layer.get(name)])),cut};
}
const MAP_HEAD=['From','Relationship','Edge type','To','Evidence'],MAP_DASH=['','7 4','2 4','9 3 2 3','12 5 2 5'],BOX={w:150,h:54,gx:120,gy:22,pad:12},MAP_CHAR=6.6,MAP_T=Array.from({length:39},(_,i)=>(i+1)/40).sort((a,b)=>Math.abs(a-.5)-Math.abs(b-.5)),LABEL_CHAR=6.6,LABEL_STEP=15,LABEL_MARGIN=20,LABEL_STEPS=24,LABEL_WRAP=106,LABEL_LINES=2,LABEL_LINE=13;
function mapDiagram(id,map,rows) {
  const edges=rows.map(({cells:[from,,type,to]})=>({from,type,to})),{names,layer,cut}=mapLayers(edges),{w,h,gy,pad}=BOX;
  // The column gap holds the longest label of an edge drawn between columns (a cut edge's label sits below the nodes), never under BOX.gx, so a map of short labels stays compact.
  // A label wraps on whole words to at most two lines (LABEL_WRAP holds 15 characters; one longer word keeps its own line), so the gap follows the longest line.
  const wrap=edges.map(e=>axisLines(e.type,LABEL_WRAP,LABEL_CHAR,'keep',LABEL_LINES)),wide=wrap.map(ls=>Math.max(...ls.map(l=>l.length))*LABEL_CHAR);
  const gx=Math.max(BOX.gx,Math.ceil(Math.max(0,...wide.filter((_,i)=>!cut[i]))+LABEL_MARGIN));
  const slot=new Map(),filled=[],types=[...new Set(edges.map(edge=>edge.type))];
  for(const name of names){const l=layer.get(name);slot.set(name,filled[l]??0);filled[l]=(filled[l]??0)+1;}
  const at=name=>({x:pad+layer.get(name)*(w+gx),y:pad+slot.get(name)*(h+gy)});
  const width=pad*2+filled.length*(w+gx)-gx,loops=cut.filter(Boolean).length,base=pad*2+Math.max(...filled)*(h+gy)-gy+(loops?46:0);
  const path=({from,to},back)=>{
    const a=at(from),b=at(to),mid=(a.x+b.x+w)/2;
    if(!back)return {d:`M${a.x+w} ${a.y+h/2}C${mid} ${a.y+h/2} ${mid} ${b.y+h/2} ${b.x} ${b.y+h/2}`,c:[[a.x+w,a.y+h/2],[mid,a.y+h/2],[mid,b.y+h/2],[b.x,b.y+h/2]]};
    const low=Math.max(a.y,b.y)+h+34,x1=a.x+w/2+(from===to?-30:0),x2=b.x+w/2+(from===to?30:0);
    return {d:`M${x1} ${a.y+h}C${x1} ${low} ${x2} ${low} ${x2} ${b.y+h}`,c:[[x1,a.y+h],[x1,low],[x2,low],[x2,b.y+h]]};
  };
  const bezier=(c,t)=>[0,1].map(k=>(1-t)**3*c[0][k]+3*(1-t)**2*t*c[1][k]+3*(1-t)*t*t*c[2][k]+t**3*c[3][k]);
  const boxes=names.map(name=>({...at(name),w,h})),placed=[],paths=edges.map((edge,i)=>path(edge,cut[i]));
  const near=paths.map(p=>Array.from({length:61},(_,k)=>bezier(p.c,k/60)));
  const gap=(pts,x,y)=>Math.min(...pts.map(([px,py])=>Math.hypot(px-x,py-y)));
  // A label is a box: its longest line wide, 12px tall a line (13px apart), centred on its spot. It tries a spot on its own line, then moves up or down by whole steps,
  // to the first clear spot (no placed label, no node) that is not nearer another edge than its own. Where another edge crosses its middle it tries nearer its source end
  // (t .25) or its target end (t .75) first, alternating by edge, so crossing labels are not stacked at the shared middle. Room is made, not borrowed: a spot below the drawing grows its height.
  const span=(y,n)=>[y-9-(n-1)*LABEL_LINE/2,y+3+(n-1)*LABEL_LINE/2];
  const clear=(x,y,lw,n)=>{const [top,bot]=span(y,n);return placed.every(o=>Math.abs(o.x-x)>=(o.w+lw)/2||top>=o.bot+2||o.top>=bot+2)&&boxes.every(b=>x+lw/2<=b.x-2||x-lw/2>=b.x+b.w+2||bot<=b.y-2||top>=b.y+b.h+2);};
  const spot=(i,lw,n)=>{
    const c=paths[i].c,steps=[0];for(let k=1;k<=LABEL_STEPS;k++)steps.push(-k,k);
    const [mx,my]=bezier(c,.5),crossed=near.some((pts,k)=>k!==i&&gap(pts,mx,my)<LABEL_STEP*2),pref=i%2?.75:.25,ts=crossed?[...MAP_T].sort((p,q)=>Math.abs(p-pref)-Math.abs(q-pref)):MAP_T;
    for(const own of [true,false])for(const dy of steps)for(const t of ts){
      const [x,y]=bezier(c,t),at=y-4+dy*LABEL_STEP;
      if(at-(n-1)*LABEL_LINE/2>=10&&clear(x,at,lw,n)&&(!own||near.every((pts,k)=>k===i||gap(pts,x,at-4)>=gap(near[i],x,at-4))))return {x,y:at};
    }
    // ponytail: LABEL_STEPS (24 steps, 360px) is the bound; past it the label sits at the line's midpoint, over its neighbours, rather than grow the drawing without end.
    const [x,y]=bezier(c,.5);return {x,y:y-4};
  };
  const drawn=edges.map((edge,i)=>{
    const p=paths[i],dash=MAP_DASH[types.indexOf(edge.type)%MAP_DASH.length],lines=wrap[i],lw=wide[i],q=spot(i,lw,lines.length),[top,bot]=span(q.y,lines.length),y0=q.y-(lines.length-1)*LABEL_LINE/2;
    placed.push({...q,w:lw,top,bot});
    return `<path class="map-edge${cut[i]?' cut':''}" d="${p.d}" marker-end="url(#map-arrow-${id.replace(/\W/g,'-')}-${map.table})"${dash?` stroke-dasharray="${dash}"`:''}/><text class="map-edge-label" x="${Math.round(q.x*10)/10}" y="${Math.round(y0*10)/10}" text-anchor="middle">${lines.map((line,k)=>`<tspan x="${Math.round(q.x*10)/10}" dy="${k?LABEL_LINE:0}">${esc(line)}</tspan>`).join('')}${lines.join(' ')===edge.type?'':`<title>${esc(edge.type)}</title>`}</text>`;
  }).join('');
  const height=Math.ceil(Math.max(base,...placed.map(o=>o.bot+3)));
  const nodes=names.map(name=>{const p=at(name),lines=axisLines(name,w-10,MAP_CHAR,true);return `<g class="map-node"><title>${esc(name)}</title><rect x="${p.x}" y="${p.y}" width="${w}" height="${h}" rx="4"/><text x="${p.x+8}" y="${p.y+h/2+4-7*(lines.length-1)}">${lines.map((line,i)=>`<tspan x="${p.x+8}" dy="${i?14:0}">${esc(line)}</tspan>`).join('')}</text></g>`;}).join('');
  const label=`${map.name}: ${names.length} nodes, ${edges.length} edges`;
  const marker=`<defs><marker id="map-arrow-${id.replace(/\W/g,'-')}-${map.table}" viewBox="0 0 8 8" refX="8" refY="4" markerWidth="8" markerHeight="8" orient="auto"><path class="map-arrow" d="M0 0L8 4L0 8z"/></marker></defs>`;
  const note=loops?`<p class="map-note">${loops} edge${loops===1?'':'s'} would close a loop: drawn below the nodes, in the order the handoff states them.</p>`:'';
  return `<div class="map-scroll" role="region" aria-label="${esc(label)}. The edge table follows; scroll horizontally if the drawing is wider than its card" tabindex="0"><svg role="img" aria-label="${esc(label)}. The edge table follows." width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${marker}${drawn}${nodes}</svg></div>${note}`;
}
// A map with only a stated gap is drawn as its reason, never as an empty diagram.
// `own` is the module page's: the map card carries its section route and caption there; the Overview draws the card alone.
function mapsView(id,tag='h2',keep=()=>true,own=false) {
  return (data[id]?.maps||[]).filter(keep).map(map=>{
    const title=`<${tag}>${esc(map.name[0].toUpperCase()+map.name.slice(1))}</${tag}>`;
    const anchor=own?drawingAnchor(id,map.table):'',caption=own?drawingCaption(id,map.table):'';
    if(map.gap!==null)return `<div class="map-card"${anchor}>${title}<p class="lane-gap">Not established for this run<small>${esc(map.gap)}</small></p>${own&&isNewFormat(data[id].sections)?gapTableForm(id,map.name,map.table):''}${caption}</div>`;
    const rows=fixtureTable(id,map.table).rows,link=row=>`<a class="event-link" href="${evidenceHref(id,row.line)}" data-evidence="${esc(`${id}:${row.line}`)}">${rich(row.cells[1])}</a>`;
    const body=rows.map(row=>`<tr><td>${rich(row.cells[0])}</td><td>${link(row)}</td><td>${esc(row.cells[2])}</td><td>${rich(row.cells[3])}</td><td>${rich(row.cells[4])}</td></tr>`).join('');
    return `<div class="map-card"${anchor}>${title}${mapDiagram(id,map,rows)}<table class="map-table"><caption>Edges of the map, as stated</caption><thead><tr>${MAP_HEAD.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table>${caption}</div>`;
  }).join('');
}
// Maps on a module page.
const reportMaps=id=>data[id]?.maps?.length?`<section class="part" id="maps"><h3>Maps</h3>${mapsView(id,'h4',()=>true,true)}</section>`:'';
// ---- Chart index (CP-MODEL-V02): one row per `Chart data:`, `Map:` or `Events:` table the run's handoffs hold, in the state the build gave it. It lists and links; nothing is drawn or recomputed here.
const CHART_HEADING=/^(Chart data|Map|Events): /;
const NOT_STATED='Not stated',NOT_ESTABLISHED='Not established for this run';
const raised=text=>text.charAt(0).toUpperCase()+text.slice(1);
const shownIn=(out,kind,name)=>[`${moduleTitle(out.module)} page`,...PLACEMENT.filter(([k,,test])=>k===kind&&test(out,name)).map(([,where])=>where)];
// The part of the module page that holds a chart, map or lane table: charts (earlier format: Key numbers), maps, and for a lane the routable s-<line>
// section that holds its table, else the page's Timeline part. Every one is an anchor of reportParts, so the link never lands on the page head.
function tableForm(id,kind,section) {
  if(kind==='map')return 'maps';
  if(kind==='chart')return isNewFormat(data[id].sections)?'charts':'numbers';
  return drawnAnchors(id).has(`s-${section.line}`)?`s-${section.line}`:'timeline';
}
function chartRows(context) {
  const ids=Object.values(contexts[context]?.modules||{}).map(entry=>entry.default||entry.outputs[0]).filter(id=>id&&data[id]);
  return ids.flatMap(id=>{
    const out=data[id];
    const held=new Map([...(out.charts||[]).map(c=>[c.table,{kind:'chart',title:c.title,unit:c.unit,gap:null}]),...(out.chartGaps||[]).map(c=>[c.table,{kind:'chart',...c}]),...(out.maps||[]).map(m=>[m.table,{kind:'map',title:`${raised(m.name)} map`,name:m.name,gap:m.gap}]),...(out.events||[]).map(l=>[l.table,{kind:'lane',title:`${l.lane} events`,gap:l.gap}])]);
    return out.sections.filter(section=>CHART_HEADING.test(section.heading)).flatMap(section=>{
      const table=section.blocks.find(b=>b.type==='table');
      if(!table)return [];
      const kind=section.heading.startsWith('Map')?'map':section.heading.startsWith('Events')?'lane':'chart',name=section.heading.replace(CHART_HEADING,''),here=held.get(table.line);
      const title=here?.title||(kind==='map'?`${raised(name)} map`:kind==='lane'?`${name} events`:raised(name));
      const sentBack=!here&&out.issue?.split('; ').find(problem=>problem.startsWith(section.heading));
      const unsupplied=table.rows[0]?.cells.find(cell=>/^Not supplied:/.test(cell))?.replace(/^Not supplied:\s*/,'');
      const hidden=kind==='chart'&&out.state.established===false;
      const drawn=Boolean(here)&&here.gap===null&&!hidden,basis=[...new Set(table.rows.map(row=>row.cells.at(-1)))].join('; ');
      const state=hidden?NOT_ESTABLISHED:drawn?'Drawn':sentBack?'Sent back':NOT_ESTABLISHED;
      const limitation=hidden?(out.summary?.limitation||'Module not assessable'):drawn?(kind==='chart'&&/^Basis/.test(table.headers.at(-1))&&basis)||NOT_STATED:sentBack||here?.gap||unsupplied||NOT_STATED;
      const unit=drawn&&kind==='chart'?(here.unit===''?'Stated per row':here.unit??NOT_STATED):NOT_STATED;
      const period=drawn&&kind==='chart'&&table.headers[0]==='Period'?[...new Set([table.rows[0].cells[0],table.rows.at(-1).cells[0]])].map(plain).join(' to '):NOT_STATED;
      const line=table.rows[0]?.line,key=`${id}:${line}`;
      const form=!drawn?null:routeHref(out.module,tableForm(id,kind,section),null,out.run,out.source);
      return [{key,title,owner:moduleTitle(out.module),state,limitation,unit,period,where:drawn?shownIn(out,kind,here.name).join(', '):'Not drawn',form,source:evidence.has(key)?evidenceHref(id,line):null,line}];
    });
  });
}
function chartIndex(context) {
  if(!contexts[context])return '';
  const rows=chartRows(context),open='<section class="run-section chart-index" id="run-charts"><h2>Chart index</h2>';
  if(!rows.length)return `${open}<p class="intro">No chart, map or calendar lane table is held in this run’s handoffs.</p></section>`;
  const head=['Chart','Module','State','Limitation','Unit','Period','Shown in','Table form','Source'];
  const body=rows.map(row=>`<tr data-chart="${esc(row.key)}"><th scope="row">${esc(row.title)}</th><td>${esc(row.owner)}</td><td>${esc(row.state)}</td><td class="index-limit">${esc(row.limitation)}</td><td>${esc(row.unit)}</td><td>${esc(row.period)}</td><td>${esc(row.where)}</td><td>${row.form?`<a href="${esc(row.form)}">Table form</a>`:'Not drawn'}</td><td>${row.source?`<a href="${esc(row.source)}">Line ${row.line}</a>`:NOT_STATED}</td></tr>`).join('');
  return `${open}<p class="intro">Every chart, map and calendar lane in this run’s handoffs, as the handoff states it. A chart drawn in several places is one row. This index lists them; it recalculates nothing.</p><div class="table-scroll" role="region" aria-label="Chart index" tabindex="0"><table class="index-table"><thead><tr>${head.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div></section>`;
}
// ---- The run label (decision 12 of the 2026-11-11 reader ruling): every run page says which run it shows, and where the issuer's other runs are.
// H7: a run is "Earlier format" when any of its handoffs (every saved output of every module, not only the defaults) has no Bottom line first under Findings.
const earlierFormat=run=>earlierFormatRun(Object.values(run.modules).flatMap(entry=>entry.outputs).filter(id=>data[id]).map(id=>data[id].sections));
const EARLIER_FORMAT_BADGE='<span class="badge badge-gray earlier-format">Earlier format</span>';
// A run whose module methods have changed since it ran is listed and marked (owner, 2026-11-11); the store's own list decides.
const EARLIER_METHODS_BADGE='<span class="badge badge-gray earlier-methods">Earlier methods</span>';
const earlierMethods=run=>(run.methodChanges||[]).length>0;
const runDate=run=>run.asOf?displayDate(run.asOf):'Not recorded';
const runPathway=run=>pathwayTitle(run.pathway)||'Not recorded';
// A findings page names a run by its date and pathway in words, never by its code (the Evidence page's to show).
const runName=run=>`${runDate(run)} · ${runPathway(run)}`;
// The header's meta line under the issuer title: the ticker and sector the catalogue holds for this run and the number of the issuer's runs it holds (the runs
// the store joins to the same issuer, this one included). A part the catalogue lacks is left out; with none the line is not drawn.
function issuerMeta(context) {
  const ctx=contexts[context],row=catalogueRuns().find(run=>run.id===ctx?.folder);
  if(!row)return '';
  return [row.issuer,row.sector,plural(issuerRuns(context).length,'run')].filter(Boolean).join(' · ');
}
// The runs of the context's issuer as Report history lists them, latest as-of date first: the count in the meta line, the rows of the history and the run a new run starts from all read this.
function issuerRuns(context) {
  const ctx=contexts[context];
  return ctx?historyRows(Object.values(contexts).filter(run=>run===ctx||sameIssuer(run.issuerKey,ctx.issuerKey))):[];
}
// The start page opened on the issuer's latest run (decision of PR 52); '' when the issuer has no run in the library.
function startRunHref(context) {
  const latest=issuerRuns(context)[0];
  return latest?'/?from='+encodeURIComponent(latest.folder):'';
}
// "Start a run on this issuer", for the run header on every run tab. Only a library served over http has the start page.
function startRunLink(context) {
  const href=startRunHref(context);
  return servedOverHttp()&&href?`<a class="start-run primary-action" href="${esc(href)}">${icon('plus')}Start a run on this issuer</a>`:'';
}
// "Showing run: 31 March 2025 · Credit snapshot" (and the run code on the Evidence page), the Earlier format badge where it holds, the link to the issuer's Report history and, where the run records one, the run it replaces.
function runLabel(module,context) {
  const ctx=contexts[context];
  if(!ctx)return '';
  const here=['W-Forecast','W-Evidence','W-Changes'].includes(module)?module:'W-Overview';
  const revisions=(ctx.revisions||[]).map(r=>r.run&&contexts[r.run]?`<a href="${esc(routeHref(here,navigationSections(here,r.run)[0][0],null,r.run,null))}">${esc(`${r.word} ${runDate(contexts[r.run])}`)}</a>`:`<span>${esc(`${r.word} ${r.id}`)}</span>`);
  // The run code is the Evidence page's to show; every other page names the run by its date and pathway.
  const code=module==='W-Evidence'?` · <span class="code">${esc(ctx.run)}</span>`:'';
  return `<p class="context-run">Showing run: <strong>${esc(runDate(ctx))}</strong> · ${esc(runPathway(ctx))}${code}${earlierFormat(ctx)?` ${EARLIER_FORMAT_BADGE}`:''}${earlierMethods(ctx)?` ${EARLIER_METHODS_BADGE}`:''}</p><a class="text-action" href="${esc(routeHref('W-Report','history',null,context))}">All runs of this issuer</a>${revisions.length?`<p class="context-revision">${revisions.join(' · ')}</p>`:''}`;
}
// ---- Report history (decision 4): one row per run of the issuer, latest as-of date first. Each row opens that run's Overview.
const SOURCE_NOT_RECORDED='Not recorded';
function historyView(context) {
  const ctx=contexts[context],keyOf=new Map(Object.entries(contexts).map(([key,run])=>[run,key])),runs=issuerRuns(context);
  const row=run=>{
    const key=keyOf.get(run),codes=runModuleCodes(run),label=`${runDate(run)}, ${runPathway(run)}, ${run.run}`;
    const notAssessable=codes.filter(code=>{const id=run.modules[code].default;return id&&blocked(data[id].sections,data[id].state);}).length;
    const modulesRun=codes.length?`<ul class="history-modules">${codes.map(code=>`<li>${esc(moduleTitle(code))}</li>`).join('')}</ul>`:SOURCE_NOT_RECORDED;
    const status=`Completed${notAssessable?` · ${notAssessable} not assessable`:''}`;
    return `<tr${key===context?' aria-current="true" class="selected-run"':''}><th scope="row"><a href="${esc(routeHref('W-Overview','overview',null,key))}" aria-label="${esc(`Open run: ${label}`)}">${esc(runDate(run))}</a><small class="code">${esc(run.run)}</small>${key===context?' <span class="badge badge-gray">Showing</span>':''}</th><td>${esc(runPathway(run))}</td><td>${modulesRun}</td><td>${esc(status)}${earlierFormat(run)?` ${EARLIER_FORMAT_BADGE}`:''}${earlierMethods(run)?` ${EARLIER_METHODS_BADGE}`:''}</td></tr>`;
  };
  return `<div class="table-scroll" role="region" aria-label="Report history" tabindex="0"><table class="history-table"><caption>Runs of ${esc(ctx.issuer||ctx.title)}, latest as-of date first</caption><thead><tr>${['Date','Pathway','Modules run','Status'].map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${runs.map(row).join('')}</tbody></table></div>`;
}
function forecastSections(context) {
  const models=runModels(context);
  return models.length?models.map(m=>[m.id,m.id,[]]):[['none','Forecast availability',[]]];
}
function navigationSections(module,context,output=defaultOutput(module,context)) {
  if(module==='W-Evidence')return [['sources','Evidence',[]]];
  if(module==='W-Forecast'||module===MODEL_ENTRY[0])return forecastSections(context);
  if(isAnalytical(module)&&output)return reportOutline(output);
  if(Object.hasOwn(modules,module))return modules[module].sections;
  return [['status',moduleEntry(module,context)?.outputs.length?'Choose a saved output':availability(module,context),[]]];
}
// ---- The Modules navigator (ruling decision 5): flat and always open, only the modules this run holds, under plain group headings. Each entry is the plain
// name only. The open entry carries its page outline directly under it.
const MODEL_ENTRY=['CP-MODEL','Cash flow model'];
function navigatorGroups(context) {
  if(!contexts[context])return []; // the library page has no run, so no module list
  const ran=new Set(contextModules(context)),named=groups.map(([title,items])=>[title,items.filter(([id])=>ran.has(id))]).filter(([,items])=>items.length);
  return runModels(context).length?[...named,['Delivered model',[MODEL_ENTRY]]]:named;
}
// The section titles a navigator entry is searched by: the model's, or those of the module's default output.
const entrySections=(id,context)=>{const output=defaultOutput(id,context);return id===MODEL_ENTRY[0]?navigationSections(id,context):output?modules[output].sections:[];};
function navigatorEntry(id,name,module,context,query) {
  const output=defaultOutput(id,context),sections=entrySections(id,context);
  const hit=query&&sections.find(s=>s[1].toLowerCase().includes(query));
  const open=id===module,notAssessable=output&&blocked(data[output].sections,data[output].state);
  const outline=open&&current.output&&isAnalytical(id)?outlineMarkup(current.output):'';
  return `<li><a href="${routeHref(id,hit?.[0]||lastSection.get(context+':'+id)||firstSection(id,context))}" class="module-item${open?' selected':''}"${open?' aria-current="page"':''}><span class="module-label">${esc(name)}</span>${notAssessable?badge('gray','Not assessable'):''}${hit?`<small>${esc(hit[1])}</small>`:''}</a>${outline}</li>`;
}
// The entries that match `query` (name, code, aliases, section titles; lower case), as markup and a count.
function navigatorView(module,query) {
  const context=current.context;
  let count=0;
  const html=navigatorGroups(context).map(([title,items])=>{
    const shown=items.filter(([id,name])=>{
      const sections=entrySections(id,context);
      return `${id} ${Object.keys(aliases).filter(k=>aliases[k]===id).join(' ')} ${name} ${sections.map(s=>s[1]).join(' ')}`.toLowerCase().includes(query);
    });
    count+=shown.length;
    return shown.length?`<div class="nav-group"><h2 class="nav-heading">${esc(title)}</h2><ul class="module-list">${shown.map(([id,name])=>navigatorEntry(id,name,module,context,query)).join('')}</ul></div>`:'';
  }).join('')+(count?'':'<p class="empty">No match. Try another name or topic.</p>');
  return {html,count};
}
const moduleHref=id=>routeHref(id,lastSection.get(current?.context+':'+id)||firstSection(id,current?.context));
function moduleLink(id,label){return `<a class="text-action" href="${moduleHref(id)}">${esc(label||moduleNames[id])}${icon('arrow-right')}</a>`;}
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
function cashflowTable(c,rows=c.rows) {
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
  for(const row of rows){
    if(row.band!==band){band=row.band;body+=`<tr class="band-row"><th scope="colgroup" colspan="${c.columns.length+1}">${esc(band)}</th></tr>`;}
    body+=`<tr${row.total?' class="total-row"':''}><th scope="row">${esc(row.label)}</th>${row.cells.map((cell,i)=>td(cell,row.kind,i)).join('')}</tr>`;
  }
  return `<table class="cashflow"><thead>${head}</thead><tbody>${body}</tbody></table>`;
}
function cashflowSection(model) {
  const c=model.cashflow;
  if(!c)return '<section class="forecast-cashflow"><h2>Cash flow model</h2><p>This model has no readable calculation record.</p></section>';
  // The store's placeholder when no downside was computed is the one Downside-case column that is not a forecast year.
  const periods=c.columns.filter(col=>!(col.group==='Downside case'&&!/^FY\d+E$/.test(col.label)));
  const na=notAvailableLines(c),first=periods[0],last=periods[periods.length-1];
  const caption=[c.units==null?'Units not recorded':c.units,...first?[`${first.label} to ${last.label}`]:[],'history as retained in the handoffs; forecasts are conditional illustrations from the calculation record'].join(' · ');
  // A line with no figure in any column (the store's `empty`) is folded; its cells stay reachable, and a heading goes with the lines under it.
  const shown=c.rows.filter(row=>!row.empty),folded=c.rows.filter(row=>row.empty);
  const empty=folded.length?`<details class="cashflow-empty"><summary>Lines with no figure in this run (${folded.length})</summary><div class="table-scroll" role="region" aria-label="Lines with no figure in this run" tabindex="0">${cashflowTable(c,folded)}</div></details>`:'';
  const other=c.other?`<details class="cashflow-other"><summary>${esc(`Other forecast cases: ${[...new Set(c.other.columns.map(col=>col.group))].join(', ')}`)}</summary><div class="table-scroll" role="region" aria-label="Other forecast cases" tabindex="0">${cashflowTable(c.other)}</div></details>`:'';
  return `<section class="forecast-cashflow"><h2 id="cashflow-heading">Cash flow model</h2><p class="forecast-caption">${esc(caption)}</p><div class="table-scroll" role="region" aria-labelledby="cashflow-heading" tabindex="0">${cashflowTable(c,shown)}</div>${empty}${c.notes.length?`<ul class="cashflow-notes">${c.notes.map(line=>`<li>${esc(line)}</li>`).join('')}</ul>`:''}${other}${na.length?`<details class="cashflow-na"><summary>Why cells show n.a. (${na.length} lines)</summary><ul>${na.map(line=>`<li>${esc(line)}</li>`).join('')}</ul></details>`:''}</section>`;
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
  const optionLabels=modelOptionLabels(models);
  const select=`<label for="model-select">Model</label><select id="model-select">${models.map((m,i)=>`<option value="${esc(m.id)}" ${m.id===model.id?'selected':''}>${esc(optionLabels[i])}</option>`).join('')}</select>`;
  const why=`<section class="forecast-why"><h2>Why this model was built</h2>${model.scope==null?'':`<p class="forecast-scope">${esc(model.scope)}</p>`}${model.inputContract==null?'':`<p class="forecast-input">${esc(`Input contract: ${model.inputContract}`)}</p>`}${model.revisionNote==null?'':`<p class="forecast-revision">${esc(`Revision note: ${model.revisionNote}`)}</p>`}</section>`;
  const forecast=model.sources.find(s=>s.role==='forecast'),register=model.register;
  // The link opens the module that wrote the forecast handoff: CP-2G's forward model, or CP-1 for a layer-1 forecast.
  const fullName=forecast?.output&&(data[forecast.output].module==='CP-2G'?'the full forward credit model output':`the ${data[forecast.output].module} output the forecast was built from`);
  const full=forecast?.output?`<a class="text-action" href="${routeHref(data[forecast.output].module,modules[forecast.output].first,null,forecast.run,data[forecast.output].source)}">Open ${fullName}${icon('arrow-right')}</a>`:'';
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
const LIBRARY_COLUMNS=[['name','Issuer'],[null,'Run'],[null,'Sector'],['date','Evidence date'],['leverage','Leverage'],['net_leverage','Net leverage'],['coverage','Coverage'],['rating','Rating'],['completion','Completeness'],[null,'Open']];
const TERM_LABELS={size_m:'Size',tenor_years:'Tenor',talk_spread_bps_low:'Spread talk, low',talk_spread_bps_high:'Spread talk, high',talk_oid_low:'OID talk, low',talk_oid_high:'OID talk, high',floor_pct:'Floor',coupon_pct:'Coupon',margin_bps:'Margin',bid:'Bid',ask:'Ask',price:'Price',yield_pct:'Yield',spread_bps:'Spread'};
const CLASSIFICATIONS={investment_grade:'Investment grade',high_yield:'High yield'},RATING_SCOPES={issuer:'Issuer',facility:'Facility'};
// Coverage group names as the screen says them; the first four hold no figure, so their hidden rows have none recorded.
const COVERAGE_NAMES={classification:'Classification',currency:'Currency',rating:'Rating',limitation:'Accepted limitations',leverage:'Leverage',net_leverage:'Net leverage',coverage:'Interest coverage',cash:'Cash',undrawn:'Undrawn facilities',talk:'Spread talk',margin:'Margin',coupon:'Coupon',price:'Price',yield:'Yield'};
const LIBRARY_GROUPS={metric:['basis','period','leverageMin','leverageMax','coverageMin','coverageMax','netLeverageMin','netLeverageMax','cashMin','cashMax','undrawnMin','undrawnMax'],rating:['classification','currency','ratingBelow','ratingAbove','ratingScope'],deal:['talkMin','talkMax','marginMin','marginMax','couponMin','couponMax','priceMin','priceMax','yieldMin','yieldMax'],limit:['limitation']};
const catalogueRuns=()=>window.DESIGN_CATALOGUE?.real||[];
// A date that is not a real calendar day is shown as served, never as another day.
function libraryDate(value) {
  if(!value)return 'n.a.';
  const day=new Date(`${value}T12:00:00Z`);
  return Number.isNaN(day.getTime())||day.toISOString().slice(0,10)!==value?String(value):day.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'});
}
// Only a file of this workspace is linked, in the one form the library build writes: a retained file beside the library (../…).
// No scheme, no root, no further climbing, plain or percent-encoded: a record cannot send the reader elsewhere.
const libraryPath=href=>{
  const rest=/^\.\.\/([\w.~%\/-]+)$/.exec(href??'')?.[1];
  return !!rest&&!/%(2e|2f|5c)/i.test(rest)&&rest.split('/').every(part=>part&&part!=='.'&&part!=='..');
};
// A value as served: grouping and its own decimals only; no value is missing-as-zero.
function libraryMetric(metric) {
  if(LibraryLogic.numberOf(metric)===null)return 'n.a.';
  if(metric.unit==='x')return `${metric.value}×`;
  const decimals=(String(metric.value).split('.')[1]||'').length;
  if(decimals>20)return String(metric.value); // beyond what the formatter takes: shown exactly as served
  return Number(metric.value).toLocaleString('en-GB',{minimumFractionDigits:decimals,maximumFractionDigits:decimals});
}
// A catalogue row joins the store by folder: a match opens that run's Overview; no match keeps the row without the link.
const libraryRunKey=run=>Object.keys(contexts).find(key=>contexts[key].folder===run.id)??null;
const primaryArtifact=run=>run.artifacts.find(a=>a.kind==='model'&&a.available&&a.state!=='superseded');
// A published model the store holds opens inside the app (its Forecast page); any other model file opens in its own tab. The delivered report is retired
// (decision 1 of the reader ruling): a report artifact is named, never linked.
function libraryArtifactLink(artifact,key,text,cls,aria='') {
  // The build writes one address for a file wherever it is named, so the catalogue's artifact and the store's model match by it.
  const model=window.DESIGN_WORKSPACE.models.find(m=>m.href===artifact.href),owner=model&&modelOwnRun(model);
  const inApp=owner?routeHref('W-Forecast',model.id,null,owner):null;
  const href=inApp??(artifact.kind==='model'&&libraryPath(artifact.href)?artifact.href:null);
  if(!href)return `<span>${esc(text)}</span>`;
  return `<a class="${cls}" href="${esc(href)}" ${inApp?'':'target="_blank" rel="noopener"'} ${aria?`aria-label="${esc(aria)}"`:''}>${esc(text)}${inApp?'':' ↗'}</a>`;
}
// What a deliverable is called: the model the store holds at its address, else the label as catalogued; a label that is only the delivery folder's hash is "Delivered report".
function libraryArtifactName(artifact) {
  const model=window.DESIGN_WORKSPACE.models.find(m=>m.href===artifact.href);
  return model?model.id:/^[0-9a-f]{64}$/.test(artifact.label)?'Delivered report':artifact.label;
}
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
// One item per column (owner, 2026-11-10). What a row no longer carries (ticker, workflow, period, each ratio's basis, a rating's agency and date, the checklist line) is in the selected-run panel; a ratio's basis and a rating's detail are also the cell's title.
const libraryMetricCell=(run,key)=>{
  const metric=run.metrics[key];
  return `<td${metric?'':' class="missing"'} title="${esc(metric?.basis||'Not available')}">${esc(libraryMetric(metric))}</td>`;
};
const libraryRatingText=r=>[r.agency||'Agency not recorded',RATING_SCOPES[r.scope]||'Scope not recorded',libraryDate(r.date)].join(' · ');
function libraryRatingCell(run) {
  const lowest=LibraryLogic.lowestRating(run,libraryFilters.ratingScope);
  return lowest?`<td title="${esc(libraryRatingText(lowest))}">${esc(lowest.label)}</td>`:'<td class="missing" title="No rating recorded">n.a.</td>';
}
// The name selects the row (its panel is below the table); the run id opens the run when the store holds it.
function libraryRow(run,selected,skipped) {
  const key=libraryRunKey(run),artifact=primaryArtifact(run);
  const name=`<td><button class="library-run-name" type="button" data-library-select="${esc(run.id)}" aria-expanded="${selected}" aria-controls="run-detail" aria-label="${esc(`View ${run.name}: ${run.title}`)}">${esc(run.name)}</button></td>`;
  const id=`<td class="run-id" title="${esc(run.id)}">${key?`<a href="${routeHref('W-Overview','overview',null,key)}" aria-label="${esc(`Open run: ${run.name}, ${run.id}`)}">${esc(run.id)}</a>`:esc(run.id)}</td>`;
  const label=`${run.name}, ${run.id}`,links=key?[`<a class="report-link" href="${routeHref('W-Overview','overview',null,key)}" aria-label="${esc(`Open run: ${label}`)}">Open run</a>`,`<a class="report-link" href="${routeHref('W-Report','history',null,key)}" aria-label="${esc(`Report history: ${label}`)}">History</a>`]:[];
  if(artifact)links.push(libraryArtifactLink(artifact,key,'Open model','report-link',`Open model: ${run.name}, ${artifact.label}`));
  const deliverable=links.length?links.join(' · '):skipped?'Not screened':'Handoffs only';
  return `<tr${selected?' class="selected"':''}>${name}${id}<td>${esc(run.sector)}</td><td>${esc(libraryDate(run.date))}</td>${libraryMetricCell(run,'leverage')}${libraryMetricCell(run,'net_leverage')}${libraryMetricCell(run,'coverage')}${libraryRatingCell(run)}<td>${esc(run.completion===null?'Not assessed':`${run.completion}%`)}</td><td>${deliverable}</td></tr>`;
}
function libraryResults({runs,rows,skipped,hidden}) {
  if(!runs.length)return window.DESIGN_APP?.problem?`<div class="library-empty"><h2>The library could not read this workspace</h2><p>Nothing can be listed until its data file loads. Rebuild the data file and open this page again.</p></div>`:`<div class="library-empty"><h2>No runs in this workspace yet</h2><p>The data file holds no retained runs.</p></div>`;
  if(!rows.length)return '<div class="library-empty"><h2>No runs match these filters</h2><p>Try a wider range or include unavailable values. Workflow completeness is not assessed for retained runs.</p><button id="library-empty-reset" class="primary-action" type="button">Reset filters</button></div>';
  const sort=key=>libraryState.sortKey===key?libraryState.direction==='asc'?'ascending':'descending':'none';
  const head=LIBRARY_COLUMNS.map(([key,label])=>key?`<th scope="col" aria-sort="${sort(key)}"><button type="button" data-library-sort="${key}">${label} <span aria-hidden="true">${{ascending:'↑',descending:'↓',none:'↕'}[sort(key)]}</span></button></th>`:`<th scope="col">${label}</th>`).join('');
  const heading=hidden?`<div class="hidden-head"><h2 id="library-hidden-title" tabindex="-1">${esc(`Hidden by ${COVERAGE_NAMES[hidden]}: ${['classification','currency','rating','limitation'].includes(hidden)?'not':'no figure'} recorded`)}</h2><button type="button" class="secondary-action" data-library-back>Back to results</button></div>`:'';
  return `${heading}<div class="table-scroll" role="region" aria-label="Issuer runs table; scroll horizontally for all columns" tabindex="0"><table class="library-table"><caption class="sr-only">Issuer runs, credit metrics, completeness and report availability</caption><thead><tr>${head}</tr></thead><tbody>${rows.map(r=>libraryRow(r,r.id===libraryState.selected,skipped.has(r.id))).join('')}</tbody></table></div><p class="hint">Dates refer to evidence, not execution. Ratios keep their original definitions.</p>`;
}
function librarySources(run) {
  const sources=window.DESIGN_CATALOGUE?.sources||{};
  const ids=[...new Set([run.identity_source,run.sector_source,run.classification_source,run.private_side_source,...Object.values(run.metrics).map(m=>m?.source),...run.ratings.map(r=>r.source),...libraryTerms(run).map(([,m])=>m.source)].filter(Boolean))];
  const block=id=>{
    const s=Object.hasOwn(sources,id)?sources[id]:null;
    if(!s)return `<div id="source-${esc(id)}" tabindex="-1"><p>${esc(id)} · source record not served</p></div>`;
    const quote=String(s.quote);
    return `<div id="source-${esc(id)}" tabindex="-1"><p>${esc(`${handoffLabel(s.path)} · line ${s.line}`)}</p><blockquote>${esc(quote.length>1500?`${quote.slice(0,1500)}… [full capture in linked file]`:quote)}</blockquote>${libraryPath(s.href)?`<a href="${esc(s.href)}" target="_blank" rel="noopener">Open retained source ↗</a>`:''}</div>`;
  };
  return `<details class="source-details" id="metric-sources"><summary>Sources &amp; definitions · ${ids.length} references</summary>${ids.map(block).join('')}</details>`;
}
// The pinned line opens in the evidence inspector when the joined run holds that file as a module output and the evidence map has the line; otherwise the Sources & definitions entry.
function librarySourceAction(run,id) {
  const sources=window.DESIGN_CATALOGUE?.sources||{},source=id&&Object.hasOwn(sources,id)?sources[id]:null,key=libraryRunKey(run);
  const output=source&&key?String(source.path).replace(/^runs\//,''):'',line=`${output}:${source?.line}`;
  if(Object.hasOwn(data,output)&&data[output].run===key&&evidence.has(line))return `<a class="tertiary-action" href="${routeHref(data[output].module,modules[output].first,line,key,data[output].source)}">View source</a>`;
  return id?`<button class="tertiary-action" type="button" data-library-source="${esc(id)}">View source</button>`:'';
}
// Every facility term and quote term as served: [field, Metric].
const libraryTerms=run=>(run.facilities||[]).flatMap(f=>[f.terms,...(f.quotes||[]).map(q=>q.terms)]).flatMap(terms=>Object.entries(terms||{}));
function libraryMetricItem(run,name,metric) {
  return `<div class="metric-item"><span class="metric-label">${esc(name)}</span><span class="metric-value">${esc(libraryMetric(metric))}${metric&&metric.unit!=='x'&&LibraryLogic.numberOf(metric)!==null?`<small>${esc(metric.unit)}</small>`:''}</span><p>${esc(metric?`${metric.period} · ${metric.basis}`:'Not established for this run.')}</p>${metric?.provenance==='user'?'<p>Entered by the user · shown as entered</p>':''}${librarySourceAction(run,metric?.source)}</div>`;
}
// The run's measures as cards; those it does not establish are named in one line under them.
function libraryMetrics(run) {
  const names=Object.entries(METRIC_NAMES),held=names.filter(([key])=>run.metrics[key]),absent=names.filter(([key])=>!run.metrics[key]).map(([,name])=>name);
  return `${held.length?`<div class="metric-grid">${held.map(([key,name])=>libraryMetricItem(run,name,run.metrics[key])).join('')}</div>`:''}${absent.length?`<p class="metric-absent">${esc(`Not established for this run: ${absent.join(', ')}.`)}</p>`:''}`;
}
const libraryTermItems=(run,terms)=>Object.entries(terms||{}).map(([field,metric])=>libraryMetricItem(run,TERM_LABELS[field]||field,metric)).join('');
const libraryFacilities=run=>run.facilities?.length?`<h3>Facilities &amp; quotes as entered</h3>${run.facilities.map(f=>`<section class="facility"><h4>${esc(f.facility_id)}</h4><div class="metric-grid">${libraryTermItems(run,f.terms)}</div>${(f.quotes||[]).map(q=>`<h5>${esc(`Quote · ${q.kind}`)}</h5><div class="metric-grid">${libraryTermItems(run,q.terms)}</div>`).join('')}</section>`).join('')}`:'';
function libraryDetail({rows}) {
  const run=rows.find(r=>r.id===libraryState.selected);
  if(!run)return '';
  const key=libraryRunKey(run),artifact=primaryArtifact(run);
  const open=[key?`<a class="secondary-action" href="${routeHref('W-Overview','overview',null,key)}">Open run</a><a class="secondary-action" href="${routeHref('W-Report','history',null,key)}">History</a>`:'',artifact?libraryArtifactLink(artifact,key,'Open model','primary-action'):libraryPath(run.handoff_href)?`<a class="primary-action" href="${esc(run.handoff_href)}" target="_blank" rel="noopener">Open primary handoff ↗</a>`:''].join('');
  const done=run.completion===null?['Workflow completeness · Not assessed','A verified checklist for this workflow has not been supplied. Available files and checked ratios do not establish end-to-end completion.']:[`Workflow completeness · ${run.completion}%`,run.checkpoints?`${run.checkpoints.done} of ${run.checkpoints.total} required checkpoints completed. This is workflow progress, not a credit score.`:'This is workflow progress, not a credit score.'];
  const artifacts=run.artifacts.length?run.artifacts.map(a=>`<li>${a.available?libraryArtifactLink(a,key,libraryArtifactName(a),''):`<span>${esc(libraryArtifactName(a))} · Unavailable</span>`}<small>${esc(a.issue||(a.state==='superseded'?'Retained failed attempt':`${a.relationship==='related'?'Related annual report · ':''}${reportAcceptance({mode:a.state}).state}`))}</small></li>`).join(''):'<li>No final deliverable has been indexed for this run.</li>';
  return `<div class="detail-head"><div><h2>${esc(run.name)}</h2><p class="cell-secondary">${esc(`${run.issuer} · ${run.id} / ${run.title}`)}</p><p class="cell-secondary">${esc(['Evidence date',libraryDate(run.date),run.period].filter(Boolean).join(' · '))}</p></div><div class="detail-actions">${artifact?`<span class="badge badge-gray">${esc(reportAcceptance({mode:artifact.state}).state)}</span>`:''}${open}</div></div><div class="detail-layout"><div><p>${esc(run.summary)}</p><h3>Scope &amp; open questions</h3><ul class="gap-list">${run.gaps.map(g=>`<li>${esc(g)}</li>`).join('')}</ul><h3>Classification &amp; currency</h3>${[['Classification',CLASSIFICATIONS[run.classification],run.classification_source],...(run.private_side===true?[['Private-side','Yes',run.private_side_source]]:[]),['Currency',run.currency]].map(([name,value,source])=>`<p>${esc(`${name} · ${value||'Not stated'}`)} ${librarySourceAction(run,source)}</p>`).join('')}${run.ratings.length?`<h3>Dated ratings</h3>${run.ratings.map(r=>`<p>${esc(`${r.label} · ${libraryRatingText(r)}`)} ${librarySourceAction(run,r.source)}</p>`).join('')}`:''}<div class="completion-box"><strong>${esc(done[0])}</strong>${esc(done[1])}</div></div><div>${libraryMetrics(run)}${libraryFacilities(run)}<h3>Deliverables &amp; revision history</h3><ul class="artifact-list">${artifacts}</ul>${librarySources(run)}</div></div>`;
}
// Options of every select the screen sends to LibraryLogic, as [value, text]. The Library query accepts only these values.
function libraryChoices() {
  const runs=catalogueRuns(),values=pick=>[...new Set(runs.flatMap(pick).filter(Boolean))].sort().map(v=>[v,v]);
  return {sector:values(r=>r.sector),workflow:values(r=>r.workflow),issuer:issuerGroups(runs).filter(g=>g[0].issuer).map(g=>[g[0].issuer,new Set(g.map(r=>r.name)).size===1?g[0].name:g[0].issuer]).sort((a,b)=>a[1].localeCompare(b[1])),basis:values(r=>r.metrics.leverage?.basis),period:values(r=>r.period_kind),currency:values(r=>r.currency),limitation:values(r=>r.gaps||[]),
    // No run records a completeness until a checklist is supplied; a filter that nothing can match is not offered, by the screen or the address.
    completion:runs.some(run=>run.completion!=null)?[['75','75% or above'],['50','50% or above'],['100','100% complete'],['unassessed','Not assessed']]:[],availability:[['report','Report available'],['handoff','No report available']],
    runs:[['latest','Latest run per issuer'],['any','Any run']],classification:[...Object.entries(CLASSIFICATIONS),['not_stated','Not stated']],
    ratingBelow:LibraryLogic.scale.map(r=>[r,r.replace('/',' / ')]),ratingAbove:LibraryLogic.scale.map(r=>[r,r.replace('/',' / ')]),ratingScope:[['issuer','Issuer ratings'],['any','Any rating']]};
}
// Anything Reset filters would undo: a filter off its default, or a sort.
const libraryFiltered=()=>!!libraryState.sortKey||Object.keys(LIBRARY_DEFAULTS).some(key=>libraryFilters[key]!==LIBRARY_DEFAULTS[key]);
const libraryActive=group=>LIBRARY_GROUPS[group].filter(k=>libraryFilters[k]&&libraryFilters[k]!==LIBRARY_DEFAULTS[k]).length;
function libraryPanel() {
  const f=libraryFilters,choices=libraryChoices();
  const chosen=(key,v)=>key==='issuer'?!!v&&LibraryLogic.issuerKey(f.issuer)===LibraryLogic.issuerKey(v):f[key]===v; // an issuer from the address matches in any case
  const select=(key,label,any)=>`<label>${label}<select id="library-${key}" data-library-filter="${key}">${(any?[['',any],...choices[key]]:choices[key]).map(([v,t])=>`<option value="${esc(v)}" ${chosen(key,v)?'selected':''}>${esc(t)}</option>`).join('')}</select></label>`;
  const number=(key,label,hint)=>`<label>${label}<input id="library-${key}" data-library-filter="${key}" type="number" step="any" placeholder="${hint}" value="${esc(f[key])}"></label>`;
  const pair=(key,label,unit)=>['Min','Max'].map(end=>number(`${key}${end}`,`${label}, ${end==='Min'?'minimum':'maximum'}${unit?` (${unit})`:''}`,`No ${end==='Min'?'minimum':'maximum'}`)).join('');
  const group=(name,title,body,hint='')=>{const n=libraryActive(name);return `<details id="${name}-filters" ${n?'open':''}><summary>${title} <span id="${name}-filter-count">${n?`· ${n} active`:''}</span></summary><div class="library-filters">${body}</div>${hint}</details>`;};
  return `<div class="search-row"><label class="library-search"><span class="sr-only">Search issuer, run or sector</span>${icon('search')}<input id="library-query" data-library-filter="search" type="search" value="${esc(f.search)}" placeholder="Search issuer, run or sector…" autocomplete="off" aria-controls="library-results"></label><button id="library-clear" class="tertiary-action" type="button"${libraryFiltered()?'':' hidden'}>Reset filters</button></div><div class="library-filters">${select('runs','Runs')}${select('issuer','Issuer','All issuers')}${select('sector','Sector','All sectors')}${select('workflow','Workflow','All workflows')}${choices.completion.length?select('completion','Completeness','Any completeness'):''}${select('availability','Deliverables','All runs')}</div>`
    +group('rating','Classification, rating &amp; currency',`${select('classification','Classification','Any')}${select('currency','Currency','Any')}${select('ratingBelow','Rating at or below','Any')}${select('ratingAbove','Rating at or above','Any')}${select('ratingScope','Rating scope')}`)
    +group('metric','Credit metrics &amp; period',`${select('basis','Leverage basis','All bases · definitions differ')}${select('period','Financial period','All period types')}${pair('leverage','Leverage','x')}${pair('coverage','Coverage','x')}${pair('netLeverage','Net leverage','x')}${pair('cash','Cash','as reported unit')}${pair('undrawn','Undrawn facilities','as reported unit')}`,'<p class="hint">Numeric filters exclude unavailable values. Select a leverage basis to keep definitions consistent; the definition of each ratio is listed for the selected run.</p>')
    +group('deal','Facilities &amp; quotes',`${pair('talk','Spread talk','bps')}${pair('margin','Margin','bps')}${pair('coupon','Coupon','%')}${pair('price','Price')}${pair('yield','Yield','%')}`,'<p class="hint">Matched within one facility: talk and bid–ask by overlap, single values inside the range. Values are shown as entered.</p>')
    +group('limit','Accepted limitations',select('limitation','Accepted limitation','Any'));
}
// A panel rebuild shows an unreadable number box empty, so its stored 'invalid' bound is dropped to keep the filter and the control in agreement.
const clearInvalidBounds=()=>Object.keys(libraryFilters).forEach(k=>{if(libraryFilters[k]==='invalid')libraryFilters[k]='';});
// Read when the library was built: the run folders it does not show, with the reason, and the issues the build found. Closed by default; it changes nothing.
function libraryNotShown(activity) {
  if(!activity)return '<p class="intro">The build’s list of folders not shown and its issues could not be read; nothing is claimed about them.</p>';
  const {excluded,issues}=activity;
  if(!excluded.length&&!issues.length)return '';
  const folders=excluded.length?`<h3>Run folders not shown</h3><ol class="report-list">${excluded.map(([folder,reason])=>`<li class="report-row"><span class="code">${esc(folder)}</span><span>${esc(reason)}</span></li>`).join('')}</ol>`:'';
  const found=issues.length?`<h3>Issues</h3><ul class="report-list">${issues.map(i=>`<li class="report-row">${esc(i)}</li>`).join('')}</ul>`:'';
  return `<details class="library-not-shown"><summary>Not shown (${excluded.length} folders, ${issues.length} issues)</summary>${folders}${found}</details>`;
}
function libraryView() {
  clearInvalidBounds();
  const view=libraryRows();
  return `<div class="library-main"><form id="library-filters" class="library-panel" role="search" aria-label="Screen issuer runs">${libraryPanel()}</form><section class="library-results-panel" aria-label="Run results"><p id="library-count" role="status" aria-live="polite">${libraryCount(view)}</p><div id="library-coverage" class="library-coverage" role="status" aria-live="polite">${libraryCoverage(view)}</div><div id="library-results">${libraryResults(view)}</div></section><section id="run-detail" class="run-detail" aria-label="Selected run details" tabindex="-1" ${view.rows.some(r=>r.id===libraryState.selected)?'':'hidden'}>${libraryDetail(view)}</section></div>${libraryNotShown(window.DESIGN_ACTIVITY)}`;
}
// Re-places the results from the current filters; the panel itself is only rebuilt on a reset so typing keeps its focus.
function updateLibrary(panel=false) {
  if(panel)clearInvalidBounds();
  const view=libraryRows();
  if(panel)$('library-filters').innerHTML=libraryPanel();
  $('library-count').textContent=libraryCount(view);
  $('library-results').innerHTML=libraryResults(view);
  $('run-detail').innerHTML=libraryDetail(view);
  $('run-detail').hidden=!view.rows.some(r=>r.id===libraryState.selected);
  $('library-coverage').innerHTML=libraryCoverage(view);
  $('library-clear').hidden=!libraryFiltered();
  // What was redrawn is named as the route's own draw names it.
  for(const id of ['library-results','run-detail','library-coverage',...(panel?['library-filters']:[])])nameCodes($(id));
  for(const group of Object.keys(LIBRARY_GROUPS))$(`${group}-filter-count`).textContent=libraryActive(group)?`· ${libraryActive(group)} active`:'';
  writeLibraryHash();
}
// ---- The run report: the run's landing page. Every sentence is a handoff cell verbatim; the counts, the state and the words come from
// Python (data[id].state, data[id].words). The page makes no judgement of its own.
const NO_SUMMARY='No reader summary';
// Every module that has an output in the run, in reading-group order: [group title, [{module, id, out}]]. A module with saved outputs but no
// default has id and out null and the number of its outputs in choices: the page does not pick one for it.
function runGroups(context) {
  const item=module=>{
    const id=defaultOutput(module,context);
    return id?{module,id,out:data[id],choices:0}:{module,id:null,out:null,choices:(moduleEntry(module,context)?.outputs||[]).length};
  };
  return groups.map(([title,items])=>[title,items.map(([module])=>item(module)).filter(item=>item.id||item.choices)]).filter(([,items])=>items.length);
}
const stateWord=established=>established===true?'Reaches a conclusion':established===false?'Not assessable':NO_SUMMARY;
// ---- The Overview (ruling H5): selection and ordering of the handoffs' own passages, text unchanged. Nothing is written, counted or
// judged here; a passage the handoff lacks is named as missing, never replaced by other text (H7).
// CP-L10 leads only a short snapshot (amendment 2026-11-11 to H5): CP-2 and CP-6 do not run in it.
const LEAD_MODULES=['CP-6','CP-2','CP-L10'];
const NO_LEAD='No credit view module completed in this run.';
const EARLIER_NO_LEAD='This run is in the earlier format: its handoffs carry no reader passages for Overview to select.';
// The one place a handoff paragraph is drawn (Overview and, later, the module page), so figures can become clickable in one function.
// The one place a handoff's prose is drawn (Overview and the module page): a list item loses its "- " marker, the Basis line is not printed, and its
// figures (or one Basis button) open the inspector. `tables` false draws prose only (Overview).
function passageHtml(section,id,tables=true) {
  return section?sectionBodyHtml(section,bodyContext(id,tables)):'';
}
// The run's modules in the order CP-OS ran them, each with its default output and that output's reader passages.
function overviewEntries(context) {
  return runModuleCodes(contexts[context]).map(module=>{
    const id=defaultOutput(module,context);
    if(!id)return {module,id:null,out:null,passages:null,choices:(moduleEntry(module,context)?.outputs||[]).length};
    const out=data[id];
    return {module,id,out,passages:readerPassages(out.sections),choices:0};
  });
}
const notAssessable=entry=>Boolean(entry.out)&&blocked(entry.out.sections,entry.out.state);
const NOT_ASSESSABLE_BADGE='<span class="badge badge-gray">Not assessable</span>';
function overviewLead(entries,earlier) {
  const lead=LEAD_MODULES.map(code=>entries.find(entry=>entry.module===code)).find(entry=>entry?.passages?.bottom&&!notAssessable(entry));
  if(!lead)return {lead:null,html:`<section class="overview-part" id="overview-lead"><h2 class="kicker">Credit view</h2><p class="intro">${earlier?EARLIER_NO_LEAD:NO_LEAD}</p></section>`};
  const key=lead.passages.key?`<div class="reading-findings"><h3>Key findings</h3>${passageHtml(lead.passages.key,lead.id,false)}</div>`:'';
  return {lead,html:`<section class="overview-part" id="overview-lead"><h2 class="kicker">Credit view</h2><p class="lead-source kicker">Written by ${moduleLink(lead.module)}</p><div class="reading-headline"><h3 class="sr-only">Bottom line</h3>${passageHtml(lead.passages.bottom,lead.id,false)}</div>${key}</section>`};
}
function overviewBottomLines(entries,lead) {
  const rows=entries.filter(entry=>entry!==lead).map(entry=>{
    if(!entry.out)return `<div class="bottom-entry"><h3>${moduleLink(entry.module)}</h3><p class="intro">${entry.choices} saved outputs, none chosen. <a class="text-action" href="#${encodeURIComponent(entry.module)}?${new URLSearchParams({c:current.context})}">Choose one</a></p></div>`;
    const body=entry.passages.bottom?passageHtml(entry.passages.bottom,entry.id,false):'<p class="intro">No bottom line in this handoff.</p>';
    return `<div class="bottom-entry" data-module="${esc(entry.module)}"><h3>${moduleLink(entry.module)}${notAssessable(entry)?` ${NOT_ASSESSABLE_BADGE}`:''}</h3>${body}</div>`;
  });
  return rows.length?`<section class="overview-part" id="overview-bottom-lines"><h2>Bottom line by module</h2>${rows.join('')}</section>`:'';
}
// Every Limitations item of every module, first occurrence kept (verbatim) when the normalised text repeats.
function overviewLimitations(entries) {
  const seen=new Set(),items=[];
  for(const entry of entries)for(const block of (entry.passages?.limits?.blocks||[]).filter(b=>b.type==='text')) {
    const key=normaliseLimitation(block.text);
    if(key!==''&&seen.has(key))continue;
    seen.add(key);
    const ref=`${entry.id}:${block.line}`,{html}=paragraphView(block.text,ref,{chips:bodyContext(entry.id,false).chips(ref)});
    items.push(`<li class="limit-item">${html}<small class="limit-module">${moduleLink(entry.module)}</small></li>`);
  }
  return `<section class="overview-part" id="overview-limitations"><h2>Limitations</h2>${items.length?`<div class="reading-limits"><ul class="passage-list">${items.join('')}</ul></div>`:'<p class="intro">No handoff in this run states limitations.</p>'}</section>`;
}
// The drawn charts and maps of the modules the visuals catalogue places on Overview (PLACEMENT); a blocked module draws none. Lanes are the dates section.
function overviewCharts(entries,context) {
  let noted=false;
  const html=entries.filter(entry=>entry.out).map(({id,out})=>{
    if(!placed('chart','Overview',out))return '';
    const charts=out.charts||[];
    const cards=chartCards(charts.map((chart,at)=>readerChart(id,chart,true,!noted&&at===lastPeriodChart(charts))));
    noted=noted||lastPeriodChart(charts)>=0;
    return `<div class="overview-charts" data-module="${esc(out.module)}">${cards}${mapsView(id,'h3',map=>map.gap===null&&placed('map','Overview',out,map.name))}</div>`;
  }).filter(html=>/class="(panel-card|map-card)"/.test(html));
  // The link goes to the chart index on this run's Forecast page: the index is a section of that page, reached by its route (it has no route of its own).
  const index=`<a class="chart-index-link" href="${routeHref('W-Forecast','run-charts',null,context)}">Chart index</a>`;
  return html.length?`<section class="overview-part" id="overview-charts"><h2>Key charts</h2>${index}${html.join('')}</section>`:'';
}
// Nearest dates: the next five items in all (reader.js nearestDates), day-dated and period-dated in one nearest-first list, from every module's event lanes.
// A period-dated item (month, quarter or year) is sorted by its period end and shown with that date text as written. The sentence when none is drawn names its cause.
const runHoldsEventTable=context=>runModuleCodes(contexts[context]).some(module=>{const id=defaultOutput(module,context);return Boolean(id)&&Boolean(eventTable(data[id].sections));});
function overviewDates(context) {
  const asOf=contexts[context].asOf;
  const head='<section class="overview-part" id="overview-dates"><h2>Nearest dates</h2>';
  if(!asOf)return `${head}<p class="intro">This run records no as-of date, so no nearest dates are selected.</p></section>`;
  const lanes=eventLanes(context);
  if(!lanes.length)return `${head}<p class="intro">${runHoldsEventTable(context)?'This run’s handoffs hold an event table but no dated lane, so no nearest dates are selected.':'No event timeline in this run’s handoffs.'}</p></section>`;
  const items=lanes.filter(lane=>lane.gap===null).flatMap(lane=>fixtureTable(lane.id,lane.table).rows.map(row=>({date:row.cells[0],text:row.cells[3],module:data[lane.id].module,line:row.line})));
  const next=nearestDates(items,asOf);
  if(!next.length)return `${head}<p class="intro">No dated item on or after ${esc(asOf)} in this run’s handoffs.</p></section>`;
  const caption=`The next ${next.length} dated item${next.length===1?'':'s'} on or after ${asOf}`;
  const table=scrollRegion(caption,`<table class="dates-table"><caption>${esc(caption)}</caption><thead><tr>${['Date','Event','Module'].map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${next.map(item=>`<tr><th scope="row">${esc(item.date)}</th><td>${rich(item.text)}</td><td>${moduleLink(item.module)}</td></tr>`).join('')}</tbody></table>`);
  return `${head}${table}</section>`;
}
function runReport(context) {
  const entries=overviewEntries(context);
  // A run that holds no module output has nothing to select from: it says so and keeps the way to its sources.
  if(!entries.length)return `<div class="missing-state"><h2>No module output retained for this run</h2><p>The Overview is selected from module handoffs, and this run holds none.</p></div><p class="run-inventory"><a class="text-action" href="${routeHref('W-Evidence','sources',null,context)}">Evidence${icon('arrow-right')}</a></p>`;
  const {lead,html}=overviewLead(entries,earlierFormat(contexts[context]));
  // Two columns at wide windows (screen.css): the reading in the main column, the charts and dates in the aside; the document order is the part order.
  return `<div class="overview-main">${html+overviewBottomLines(entries,lead)+overviewLimitations(entries)}</div><aside class="overview-aside" aria-label="Charts and dates">${overviewCharts(entries,context)+overviewDates(context)}</aside>`;
}
// Run activity (ruling decision 10): only what is in progress and the queue. A finished run is reached from the library; the folders the
// library does not show and the build's issues are on the library page.
function activityView(live) {
  const top=liveActivityView(live);
  if(!live||typeof live!=='object'||Array.isArray(live)||!Array.isArray(live.runs))return '<div class="missing-state activity-empty"><div class="empty-symbol">'+icon('file-text')+'</div><h2>Run activity could not be read</h2><p>No live run data was supplied, so nothing is claimed about runs in progress or waiting.</p></div>';
  if(!top.includes('<section'))return top+'<div class="missing-state activity-empty"><div class="empty-symbol">'+icon('file-text')+'</div><h2>No run in progress</h2><p>No run is running or waiting. Finished runs are in the Issuer library.</p><a class="primary-action" href="#W-Library/cases">Issuer library</a></div>';
  return top;
}
// Live runs from _engine/activity.js (window.RUN_ACTIVITY). Every field may be missing and the whole object may be malformed:
// then nothing live is shown. Each value passes through esc. Only runs that are running or queued are drawn.
const ACTIVITY_RELOAD_MS=30000;
// Statuses of runs that have ended: not drawn here (decision 10); the list stays so a test can check it against the run start service's statuses.
const ENDED_STATUSES=['finished','failed','capped','rejected','interrupted'];
// Only strings and finite numbers reach the page; any other value in a field renders as empty text.
function liveText(value) {return esc(typeof value==='string'||(typeof value==='number'&&Number.isFinite(value))?value:'');}
const LIVE_STATUSES=['queued','running','finished','failed','capped','rejected','interrupted']; // read only by tests/test_context_form.py, which holds it to the run start service's statuses
const servedOverHttp=()=>typeof window!=='undefined'&&/^https?:$/.test(window.location?.protocol); // a page with no location (the node tests) is not served
const MODULE_STATES=['done','running','waiting'];
// What a run's head and a waiting row say about it: each part that has text, joined with " · ".
function liveRunLine(run,extra=[]) {
  const part=(value,html)=>liveText(value)?html:'';
  return [part(run.submitted_by,`<span class="run-by">submitted by ${liveText(run.submitted_by)}</span>`),part(run.started_at,`<span class="run-time">started ${liveText(run.started_at)}</span>`),part(run.folder,`<span class="code">${liveText(run.folder)}</span>`),...extra].filter(Boolean).join(' · ');
}
function liveRunProgress(modules) {
  if(!modules.length)return '';
  const done=modules.filter(m=>m[1]==='done').length;
  const badges=modules.map(([name,state])=>{const kind=MODULE_STATES.includes(state)?state:'waiting';return `<span class="chip chip-${kind}">${liveText(name)}<span class="run-vh">, ${kind}</span></span>`;}).join('');
  return `<div class="run-progress"><progress max="${modules.length}" value="${done}" aria-label="Modules done"></progress><span class="run-done">${done} of ${modules.length} done</span></div><div class="run-mods">${badges}</div>`;
}
function liveRunFiles(run) {
  const files=Array.isArray(run.files)?run.files:[];
  const has=typeof run.id==='string'&&run.id||typeof run.id==='number'&&Number.isFinite(run.id),tag=has?` data-run="${liveText(run.id)}"`:'';
  return files.length?`<details class="run-files"${tag}><summary>${files.length} file${files.length===1?'':'s'} read</summary><ul>${files.map(f=>`<li>${liveText(f)}</li>`).join('')}</ul></details>`:'';
}
// The reason a run is not progressing and the name warning, as spans: the card and the waiting row both show them.
function liveRunNotes(run) {
  return [run.reason&&liveText(run.reason)?`<span class="run-reason">${liveText(run.reason)}</span>`:'',run.name_differs?'<span class="run-note">issuer name differs from earlier runs</span>':''].filter(Boolean);
}
function liveRunCard(run) {
  const modules=Array.isArray(run.modules)?run.modules.filter(Array.isArray):[];
  const line=liveRunLine(run),pathway=liveText(run.pathway);
  const notes=liveRunNotes(run).join(' · ');
  const list=liveRunFiles(run);
  const badge=run.stalled?'<span class="run-badge run-badge-stalled">Running · stalled</span>':'<span class="run-badge run-badge-running">Running</span>';
  return `<li class="run-card live-run live-running"><div class="run-head"><div class="run-who"><strong>${liveText(run.issuer_name||run.folder||run.id)}</strong>${line?`<p>${line}</p>`:''}</div><div class="run-marks">${pathway?`<span class="run-tag">${pathway}</span>`:''}${badge}</div></div>${liveRunProgress(modules)}${list||notes?`<div class="run-foot">${list}${notes?`<span class="run-foot-notes">${notes}</span>`:''}</div>`:''}</li>`;
}
function liveWaitingRow(run) {
  const extra=[...liveRunNotes(run),...(run.stalled?['<span class="run-stalled">stalled</span>']:[])];
  const line=liveRunLine({submitted_by:run.submitted_by,folder:run.folder},extra);
  return `<tr class="live-run live-queued"><th scope="row"><span class="run-name">${liveText(run.issuer_name||run.folder||run.id)}</span>${line?`<span class="run-sub">${line}</span>`:''}${liveRunFiles(run)}</th><td>${liveText(run.pathway)}</td></tr>`;
}
function liveActivityView(live) {
  if(!live||typeof live!=='object'||Array.isArray(live)||!Array.isArray(live.runs))return '';
  const runs=live.runs.filter(r=>r&&typeof r==='object'&&!Array.isArray(r));
  const running=runs.filter(r=>r.status==='running'),waiting=runs.filter(r=>r.status==='queued');
  const held=live.held&&liveText(live.held)?`<p class="run-held" role="note">${liveText(live.held)}</p>`:'';
  const runningHtml=running.length?`<section class="activity-running"><h2>Running</h2><ul class="run-cards">${running.map(liveRunCard).join('')}</ul></section>`:'';
  const table=waiting.length?`<div class="run-table-wrap"><table class="run-table"><caption class="run-vh">Waiting runs</caption><thead><tr><th scope="col">Issuer</th><th scope="col">Pathway</th></tr></thead><tbody>${waiting.map(liveWaitingRow).join('')}</tbody></table></div>`:'';
  const waitingHtml=waiting.length||held?`<section class="activity-waiting"><h2>Waiting</h2>${held}${table}</section>`:'';
  const stamp=`<p class="run-updated">Updated <span class="run-updated-at">${liveText(live.updated)}</span></p>`;
  const counts=`<dl class="run-tally"><div><dt>Running</dt><dd>${running.length}</dd></div><div><dt>Waiting</dt><dd>${waiting.length}</dd></div></dl>`;
  const cols=runningHtml&&waitingHtml?'':' one';
  return `<div class="run-activity-head">${stamp}${counts}</div>${runningHtml||waitingHtml?`<div class="activity-cols${cols}">${runningHtml}${waitingHtml}</div>`:''}`;
}
// The Run activity view re-loads activity.js every 30 s while it is showing; no other view schedules anything.
function nextActivityReload(route) {return route&&route.module==='CP-OS'?ACTIVITY_RELOAD_MS:null;}
// Adds a fresh copy of the script and removes the previous one. A missing file only logs in the browser; the page carries on.
function swapActivityScript(doc,now) {
  const previous=doc.head.querySelector('script[data-run-activity]');
  const script=doc.createElement('script');
  script.src='../activity.js?t='+now;script.setAttribute('data-run-activity','');
  doc.head.append(script);
  if(previous)previous.remove();
}
// A wide table scrolls inside its own focusable region, never the page (the region pattern of the library and chart index tables).
const scrollRegion=(label,table)=>`<div class="table-scroll" role="region" aria-label="${esc(label)}" tabindex="0">${table}</div>`;
// ---- Evidence (ruling decisions 9, 10; library redesign task 3): evidence.js draws a governance summary and the tabs; this gathers what the library holds for the run.
// A file named after a module is labelled by its module; any other file keeps its name. The hash beside it is the file's own.
const hashLabel=name=>{
  const sent=/^instructions\/(CP-[A-Z0-9]+)(-[a-z0-9]+)?\.md$/.exec(name);
  return sent?`${moduleTitle(sent[1])} instructions${sent[2]?` (${sent[2].slice(1)})`:''}`:handoffLabel(name);
};
// A module code in a method-change line ("CP-0: src/…/cp0.md changed") is named; a code inside a file path (…/CP-1.md) is part of the path and stays.
const CODE_NOT_IN_PATH=/(?<![\w/.-])CP-[A-Z0-9]+(?![\w-]|\.md)/g;
function evidenceView(context) {
  const run=contexts[context];
  // A hash row named like a stored source file keeps that name; any other module-named file is labelled by its module.
  const stored=new Set([...(run?.evidence?.sources||[]),...(run?.evidence?.unused||[]),...(run?.evidence?.unrecorded||[])].map(f=>f.name));
  const modules=Object.entries(run?.modules||{}).map(([id,entry])=>({id,outputs:entry.outputs.map(output=>data[output]).filter(Boolean).map(output=>({id:output.id,sections:output.sections,placement:output.placement}))}));
  return window.Evidence.view({
    run:{context,code:run?.run,evidence:run?.evidence,methodChanges:run?.methodChanges||[],steps:run?.record?.steps||[]},
    modules,chips:window.CREDIT_OS_DATA?.chips||{},
    deps:{moduleTitle,hashLabel:name=>stored.has(name)?name:hashLabel(name),methodChange:line=>line.replace(CODE_NOT_IN_PATH,moduleTitle)}
  },{tab:current?.tab,module:current?.evidenceModule});
}
// ---- Changes (decision M8 of the 2026-11-11 module-presets ruling): changes.js draws the run's comparison pack and CP-8's handoff. Nothing is worked out here:
// this gathers what the library holds, the runs of this issuer and pathway (earliest first) with their quoted figures, packs and lead-module bottom lines.
function changesView(context) {
  const ctx=contexts[context],keyOf=new Map(Object.entries(contexts).map(([key,run])=>[run,key]));
  const sections=run=>{const id=run.modules['CP-8']?.default;return id&&data[id]?data[id].sections:null;};
  const runs=historyRows(Object.values(contexts).filter(run=>run===ctx||(sameIssuer(run.issuerKey,ctx.issuerKey)&&run.pathway===ctx.pathway))).reverse().map(run=>{
    const key=keyOf.get(run),lead=run.changes?.lead&&run.modules[run.changes.lead]?.default,out=lead&&data[lead];
    return {key,href:routeHref('W-Changes','changes',null,key),asOf:run.asOf,runId:run.folder,current:run===ctx,bottom:out?ChangesView.leadBottom(out.sections,out.summary):null,
      metrics:window.DESIGN_CATALOGUE.real.find(r=>r.id===run.folder)?.metrics||{},changes:run.changes||null};
  });
  return ChangesView.changesHtml({changes:ctx.changes||null,cp8:sections(ctx),pathway:runPathway(ctx),fmtDate:displayDate,runs});
}
function workspaceView(module,section) {
  const context=current?.context,ctx=contexts[context],available=ctx?contextModules(context):[];
  if(module==='W-Library')return libraryView();
  if(module==='W-Overview')return runReport(context);
  if(module==='W-Changes')return changesView(context);
  if(module==='W-Report')return historyView(context);
  if(module==='W-Evidence')return evidenceView(context);
  if(module==='W-Forecast')return forecastView(context,section)+chartIndex(context);
  if(module==='CP-OS')return activityView(window.RUN_ACTIVITY);
  return '';
}
// The issuer's header chips: the run's period, its pathway in words and, only when the store lists method changes since the run, an amber chip to Evidence's run record.
// The sliding pill sits under the active tab; it is measured, so it is placed again when the tabs are drawn, the window resizes or the fonts load.
const placeTabsPill=()=>{const tabs=document.querySelector('.workspace-tabs');if(tabs&&!tabs.hidden)window.Components.placePill(tabs);};
function headerChipMarkup(ctx,context) {
  const changed=earlierMethods(ctx)?{text:'Methods changed since this run',tone:'amber',href:routeHref('W-Evidence','record',null,context,null)}:null;
  return window.Components.headerChips([{text:ctx.period},{text:pathwayTitle(ctx.pathway)},changed]);
}
function updateWorkspaceChrome(module) {
  const ctx=contexts[current.context],isHome=!ctx||appDestinations.has(module);
  const moduleId=ctx&&(lastSection.get(current.context+':module')||ctx.first);
  const title=isHome?(module==='W-Library'?'Issuer library':moduleNames[module]):ctx.title;
  const header=document.querySelector('.issuer'),meta=isHome?'':issuerMeta(current.context);
  header.classList.toggle('run-header',!isHome);
  const startRun=isHome?'':startRunLink(current.context),chips=isHome?'':headerChipMarkup(ctx,current.context);
  header.innerHTML=isHome?`<div class="issuer-title"><h1 title="${esc(title)}">${esc(title)}</h1></div>`:`<a class="issuer-back" href="#W-Library/cases"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>Issuer library</a><div class="issuer-row${startRun?' has-start-link':''}"><div class="issuer-title"><h1 title="${esc(title)}">${esc(title)}</h1>${meta?`<p class="issuer-meta">${esc(meta)}</p>`:''}${chips}</div>${startRun?`<div class="issuer-side">${startRun}</div>`:''}</div>`;
  document.querySelector('.workspace-tabs').hidden=isHome;
  $('context-bar').hidden=isHome||module==='W-Report';
  if(!isHome)$('context-bar').innerHTML=runLabel(module,current.context);
  if(!isHome)document.querySelector('.workspace-tabs').innerHTML=[['W-Report','Report'],['W-Overview','Overview'],['W-Changes','Changes'],[moduleId,'Modules'],['W-Forecast','Forecast'],['W-Evidence','Evidence']].map(([id,label])=>{
    const sections=navigationSections(id,current.context,resolveOutput(id,current.context,lastFile.get(`${current.context}:${id}`))),remembered=lastSection.get(current.context+':'+id),section=sections.some(s=>s[0]===remembered)?remembered:sections[0][0];
    return `<a href="${routeHref(id,section)}" ${(label==='Modules'?isAnalytical(module):id===module)?'aria-current="page"':''}>${label}</a>`;
  }).join('');
  placeTabsPill();
  $('workbench').classList.toggle('library-workspace',isHome);
  // The Overview is a page of selected passages: no module navigator beside it and no Browse modules button above it.
  $('workbench').classList.toggle('overview-workspace',!isHome&&module==='W-Overview');
  // The navigator is resident only where its modules are the subject; elsewhere it opens from the Modules button.
  $('workbench').classList.toggle('tools-workspace',!isHome&&module!=='W-Overview'&&!isAnalytical(module));
  // The rail shows where you are, and its run-level links keep the selected run.
  const rail=label=>document.querySelector(`.rail [data-place="${label}"]`);
  const place={'W-Library':'Issuer library','CP-OS':'Run activity'}[module];
  document.querySelectorAll('.rail a[data-place]:not([data-place="Start a run"])').forEach(link=>{
    const here=link.dataset.place===place;
    link.classList.toggle('rail-active',here);
    if(here)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');
  });
  rail('Start a run').hidden=!servedOverHttp(); // the start page exists only when the service serves the library
  const app=window.DESIGN_APP||{};
  $('app-problem').hidden=!app.problem;
  $('app-problem').textContent=app.problem?`The workspace could not be read: ${app.problem}`:'';
}
