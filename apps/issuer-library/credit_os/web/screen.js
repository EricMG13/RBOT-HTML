'use strict';
// The app's screens over the workspace store. Curated visuals apply only to pinned outputs.
const store=window.DESIGN_DATA,data=store.outputs,contexts=store.runs,pins=store.pins;
// Curated section maps apply only to the exact output they were written for.
const modules = {
  [pins['CP-1']]: {name:'Financial foundation', subtitle:'Reported financials, cash generation and funding', first:'performance', sections:[
    ['performance','Performance',['T4.10']], ['interpretation','Financial interpretation',['Financial read-through']],
    ['statements','Income & equity statements',['T4.4']], ['cash','Cash generation',['T4.5']],
    ['balance','Balance sheet',['T4.6']], ['segments','Segments',['T4.16']],
    ['ebitda','EBITDA definitions & bridges',['Additional issuer bridges','T4.17']],
    ['debt','Debt & maturities',['T4.18']], ['definitions','Definitions & periods',['T4.11','T4.8']],
    ['scope','Scope & reporting basis',['Request','Sources','T4.1']], ['gaps','Gaps & limitations',['Gaps']],
    ['audit','Technical audit',['T4.9','T4.15','Calculations','Next module']]]},
  [pins['CP-1A']]: {name:'Business & governance', subtitle:'Operating model, transactions and issuer behaviour', first:'events', sections:[
    ['business','Business & operating model',['Company, business']], ['ownership','Ownership & control',['Ownership and control']],
    ['transactions','Transactions & capital allocation',['Transaction and capital']], ['events','Events & timeline',['Timeline and governance']],
    ['governance','Governance & financial policy',['Governance topics']], ['conflicts','Conflicting evidence & implications',['Conflicts and credit']],
    ['gaps','Gaps & limitations',['Gaps','Consumer readiness']], ['basis','Evidence & financial backdrop',['Sources','Source register','CP-1 fact']],
    ['audit','Technical audit',['Request','Calculations','Next module']]]},
  [pins['CP-2']]: {name:'Fundamental credit', subtitle:'Integrated assessment, downside mechanisms and monitoring', first:'assessment', sections:[
    ['assessment','Integrated assessment',['Integrated fundamental']], ['business','Business & competitive position',['Fundamental view','Competitive and external']],
    ['risks','Strengths, weaknesses & risks',['Ranked strengths']], ['profile','Financial profile',['Financial profile']],
    ['outlook','Outlook & downside chain',['Outlook and issuer']], ['factors','Six-factor matrix & monitoring',['Six-factor']],
    ['gaps','Gaps & limitations',['Gaps']], ['basis','Evidence & definitions',['Sources','Evidence rows','Calculations']],
    ['audit','Technical audit',['Request','Next module']]]},
  [pins['CP-8']]: {name:'Changes since the last run', subtitle:'What changed between deliverables, and why?', first:'comparison', sections:[
    ['comparison','Changes since the last run',['Findings','All five report sections','Material analytical changes','Unresolved regressions']],
    ['gaps','Gaps & limitations',['Gaps']],['sources','Sources',['Sources']],['audit','Technical audit',['Request','Calculations','Next module']]]}
};
const groups = [
  ['Business and evidence',[['CP-0','Source readiness'],['CP-1A','Business & governance'],['CP-DR','Research questions']]],
  ['Financial performance',[['CP-1','Financial foundation'],['CP-1B','Earnings changes'],['CP-L10','Short credit snapshot'],['CP-1D','Earnings quality'],['CP-1C','Peer benchmark']]],
  ['Liquidity and refinancing',[['CP-2D','Liquidity'],['CP-3C','Refinancing & LME']]],
  ['Outlook and downside',[['CP-2','Fundamental credit'],['CP-2A','Downside'],['CP-2G','Forward credit model'],['CP-2E','Rates, FX & hedging'],['CP-2H','Ratings & triggers']]],
  ['Capital structure and legal',[['CP-4','Legal & covenants'],['CP-4A','Covenant capacity'],['CP-4B','Structural priority'],['CP-4D','Intercreditor control'],['CP-4C','Recovery & fulcrum']]],
  ['Relative value',[['CP-3','Security selection'],['CP-3D','Market-implied risk']]],
  ['Decision and review',[['CP-6','Committee decision'],['CP-5','Evidence validation'],['CP-8','Changes since the last run']]]
];
// A module the reading groups do not name still gets a place, as an unnamed module.
const unnamed=[...new Set(Object.values(data).map(output=>output.module))].filter(id=>id!=='CP-MODEL'&&!groups.some(group=>group[1].some(item=>item[0]===id))).sort();
if(unnamed.length)groups.push(['Other modules',unnamed.map(id=>[id,'Unnamed module'])]);
const moduleNames = {...Object.fromEntries(groups.flatMap(g=>g[1])),[MODEL_ENTRY[0]]:MODEL_ENTRY[1]}; // the delivered model is a Modules entry (decision 5) that no reading group names
delete modules.undefined; // A pin this workspace does not hold.
const isAnalytical = id => !id.startsWith('W-')&&id!=='CP-OS';
const $ = id => document.getElementById(id);
const esc = escapeHtml, plain = plainText, rich = richText; // reader.js: the page and the node tests draw prose and tables with the same code
const icon = name => `<img src="icons/${name}.svg" alt="">`;
const matchesHeading = (heading,prefix) => prefix.startsWith('=') ? heading===prefix.slice(1) : heading.startsWith(prefix) && (!/^T\d+\.\d+$/.test(prefix) || !/\d/.test(heading.charAt(prefix.length)));
const evidence = new Map();
const lastSection = new Map(), lastFile = new Map();
const readingPositions = new Map();
// Screening state, kept while the reader is on another screen. Filter names are LibraryLogic's.
const LIBRARY_DEFAULTS = {search:'',sector:'',workflow:'',completion:'',availability:'',basis:'',period:'',leverageMin:'',leverageMax:'',coverageMin:'',coverageMax:'',issuer:'',runs:'latest',classification:'',currency:'',ratingBelow:'',ratingAbove:'',ratingScope:'issuer',netLeverageMin:'',netLeverageMax:'',cashMin:'',cashMax:'',undrawnMin:'',undrawnMax:'',talkMin:'',talkMax:'',marginMin:'',marginMax:'',couponMin:'',couponMax:'',priceMin:'',priceMax:'',yieldMin:'',yieldMax:'',limitation:''};
const libraryFilters = {...LIBRARY_DEFAULTS};
const libraryState = {selected:'',sortKey:'',direction:'asc',hidden:''};
let current = null, returnTrigger = null, returnScroll = 0, returnContentScroll = 0;
installDestinations();
const appDestinations=new Set(['W-Library','CP-OS']); // These need no selected run.
const aliases = {'CP-2F':'CP-2E','CP-2C':'CP-1A','CP-1E':'CP-1D','CP-5A':'CP-5','CP-6A':'CP-6'};
for(const visual of window.DESIGN_WORKSPACE.visuals)for(const alias of String(visual.aliases||'').split(/[;,\s]+/).filter(Boolean))aliases[alias]??=visual.module;
// Every page shows names (views.js namedText). Text and the title and aria-label attributes only, so downloads, links and the retained files are untouched.
// Register references (F, K, C, S plus digits) are not codes of this kind: they stay, as a quiet mark.
const REFERENCE=/\b[FKCS]\d{1,4}\b/g;
function nameCodes(root,output=current?.output,marks=true) {
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),nodes=[];
  while(walker.nextNode())nodes.push(walker.currentNode);
  for(const node of nodes) {
    const parent=node.parentElement;
    if(parent.closest('.ref,.excerpt'))continue; // a source excerpt is the issuer's own text, quoted as it is; a register reference keeps its mark
    const named=namedText(node.data,output,node.previousSibling?.textContent??'');
    if(named!==node.data)node.data=named;
    // A chart, a select or a chip cannot hold the mark, so these keep the reference as text.
    const found=marks?[...node.data.matchAll(REFERENCE)]:[];
    if(!found.length||parent.closest('svg,option,.chip'))continue;
    const fragment=document.createDocumentFragment();
    let at=0;
    for(const mark of found) {
      fragment.append(node.data.slice(at,mark.index),Object.assign(document.createElement('small'),{className:'ref',textContent:mark[0]}));
      at=mark.index+mark[0].length;
    }
    fragment.append(node.data.slice(at));
    node.replaceWith(fragment);
  }
  for(const element of root.querySelectorAll('[title],[aria-label]'))for(const attribute of ['title','aria-label']) {
    const value=element.getAttribute(attribute),named=value&&namedText(value,output);
    if(named&&named!==value)element.setAttribute(attribute,named);
  }
}

for (const [id, output] of Object.entries(data)) {
  const located={module:output.module,output:id,run:output.run};
  for (const section of output.sections) for (const block of section.blocks) {
    if (block.type === 'table') for (const row of block.rows) {
      const priorText=section.blocks.slice(0,section.blocks.indexOf(block)).filter(b=>b.type==='text').at(-1)?.text;
      const basis=priorText||output.basis?.text;
      evidence.set(`${id}:${row.line}`, {...located,line:row.line,title:plain(row.cells[0]), fields:block.headers.map((label,i)=>[label,row.cells[i]]),section:section.heading,basis});
    }
    else evidence.set(`${id}:${block.line}`, {...located,line:block.line,title:section.heading,fields:[['Retained finding',block.text]],section:section.heading,text:block.text});
  }
  // Unknown nonempty sections remain visible rather than being silently omitted.
  const known = modules[id].sections.flatMap(s=>s[2]);
  const unknown = output.sections.filter(s=>s.blocks.length && !known.some(p=>matchesHeading(s.heading,p)));
  if (unknown.length) modules[id].sections.push(['additional','Additional findings',unknown.map(s=>'='+s.heading)]);
}
for(const definition of Object.values(modules)) {
  const seen=new Set();
  for(const section of definition.sections) {
    if(seen.has(section[1]))section[1]=section[1]==='Gaps'?'Module-wide gaps':`${section[1]} · ${section[0]}`;
    seen.add(section[1]);
  }
}

function sectionData(outputId, id) {
  const definition = modules[outputId].sections.find(s=>s[0]===id);
  return data[outputId].sections.filter(s=>definition[2].some(p=>matchesHeading(s.heading,p)));
}
function findRow(module, prefix, label) {
  for (const s of data[module].sections.filter(s=>matchesHeading(s.heading,prefix))) for (const b of s.blocks.filter(b=>b.type==='table')) {
    const row=b.rows.find(r=>plain(r.cells[0])===label);
    if(row) return {table:b,row,key:`${module}:${row.line}`};
  }
  throw new Error(`Missing pinned fixture: ${module} / ${label}`);
}
function sourceLink(key, label='View source') {
  return `<button class="source-link" data-evidence="${esc(key)}">${icon('file-text')}${esc(label)}</button>`;
}
const PROVENANCE='Documentary Fact|Management Language|Analyst Interpretation|Insufficient Information';
// A class counts only where the handoff declares it; mid-sentence mentions and verdicts never do.
function declaredClasses(value) {
  const cell=value.trim(),found=[];
  const opening=cell.match(new RegExp(`^(${PROVENANCE})[.:]\\s`));
  if(opening)found.push(opening[1]);
  const graded=cell.replace(/\*\*/g,'').match(new RegExp(`^.{1,30} — (${PROVENANCE})$`));
  if(graded)found.push(graded[1]);
  for(const bold of cell.matchAll(/\*\*(.+?)\*\*/g)) {
    if(bold[0]===cell)continue;
    const label=bold[1].trim(),after=cell[bold.index+bold[0].length];
    const match=label.match(new RegExp(`^(${PROVENANCE})[.:]$`))||(after===':'?label.match(new RegExp(`^(${PROVENANCE})$`)):null)||label.match(new RegExp(`^(${PROVENANCE});`))||label.match(new RegExp(`— (${PROVENANCE})`));
    if(match)found.push(match[1]);
  }
  return found;
}
function classification(item) {
  const classes=item.fields.flatMap(([label,value])=>{
    const declared=/classification|category|provenance|evidence (class|type)/i.test(label)?plain(value).trim().match(new RegExp(`^(${PROVENANCE})`)):null;
    return [...(declared?[declared[1]]:[]),...declaredClasses(value)];
  });
  return [...new Set(classes)].join(' · ') || 'Not classified';
}
// Lists show a class only when the handoff declared one; the inspector still says Not classified.
const classTag=(item,cls)=>{const c=classification(item);return c==='Not classified'?'':`<span class="${cls}">${esc(c)}</span>`;};
function sourceFooter(key) {
  const item=evidence.get(key);
  return `<div class="source-footer">${sourceLink(key)}${classTag(item,'badge badge-gray')}</div>`;
}
function tableMarkup(module, block) {
  const financial=block.financial||block.headers.some(h=>/^(FY\d{4}|Sep 30|Own FY)/.test(h))||block.rows.some(r=>r.cells.slice(1).filter(c=>chartNumber(c)!==null).length>=2);
  if(!financial) return `<div class="records">${block.rows.map(row=>{
    const key=`${module}:${row.line}`;
    return `<section class="record"><h3>${rich(row.cells[0])}</h3>${block.headers.slice(1).map((h,i)=>`<div class="record-field"><h4>${esc(h)}</h4><div>${rich(row.cells[i+1])}</div></div>`).join('')}${sourceFooter(key)}</section>`;
  }).join('')}</div>`;
  return `<div class="table-scroll" tabindex="0" role="region" aria-label="Exact source values"><table><thead><tr>${block.headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${block.rows.map(row=>`<tr><th scope="row">${sourceLink(`${module}:${row.line}`,plain(row.cells[0]))}${classTag(evidence.get(`${module}:${row.line}`),'row-classification')}</th>${row.cells.slice(1).map(c=>`<td>${rich(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function sectionsMarkup(module, sections, omitPresentedTable=false) {
  return sections.map(section=>{
    const blocks=section.blocks.filter(block=>!omitPresentedTable||!visualCoversTable(module,block));
    if(!blocks.length)return '';
    return `<section class="source-section"><h2>${esc(section.heading.replace(/^T[\d.\w–]+(?: and T[\d.]+)? — /,''))}</h2>${blocks.map(block=>block.type==='table'?tableMarkup(module,block):narrativeMarkup(module,block)).join('')}</section>`;
  }).join('');
}
function narrativeMarkup(module,block) {
  const text=block.text.replace(/\n/g,' ');
  return `<section class="finding"><div class="prose">${rich(text)}</div>${sourceFooter(`${module}:${block.line}`)}</section>`;
}
function trendChart(module, metric) {
  const {table,row,key}=findRow(module,'T4.10',metric),unit=data[module].basis.unit;
  const points=[3,2,1].map(i=>({label:table.headers[i],exact:row.cells[i],n:Number(row.cells[i].replace(/,/g,''))}));
  const max=Math.max(...points.map(p=>p.n));
  return `<div class="chart-head"><h3>${esc(metric)}</h3><span>${esc(unit)} · ${esc(row.cells[4])}</span></div><div class="bars" role="group" aria-label="${esc(metric)} by financial year">${points.map(p=>`<button class="bar-column" data-evidence="${esc(key)}" aria-label="${esc(p.label)} ${esc(metric)} ${esc(p.exact)} ${esc(unit)}. View source"><span class="bar-value">${esc(p.exact)}</span><span class="bar" style="height:${Math.max(2,p.n/max*142)}px"></span><span class="bar-period">${esc(p.label)}</span></button>`).join('')}</div>${sourceFooter(key)}`;
}
function performanceView() {
  const id=pins['CP-1'],{table}=findRow(id,'T4.10','Net sales');
  const retainedNotes=sectionData(id,'performance').flatMap(s=>s.blocks.filter(b=>b.type==='text')).map(b=>narrativeMarkup(id,b)).join('');
  return `<div class="section-heading"><h2>Performance</h2><span>${esc(table.headers[3])}–${esc(table.headers[1])}</span></div>${trendChart(id,'Net sales')}<div class="section-heading compact"><h3>Exact financial measures</h3></div>${tableMarkup(id,table)}${retainedNotes}`;
}
function eventTimeline(id,table,tag='h2') {
  const rowMarkup=row=>{
    const order=eventOrder(row.cells[0]),precision=order===null?'No year stated':order[1]===0?'Year only':'';
    const details=table.headers.slice(1).map((header,i)=>row.cells[i+1]?`<div class="event-detail"><strong>${esc(header)}</strong> ${rich(row.cells[i+1])}</div>`:'').join('');
    return `<li><div class="event-date"><strong>${esc(row.cells[0])}</strong>${precision?`<span>${precision}</span>`:''}</div><div class="event-body">${details}${sourceFooter(`${id}:${row.line}`)}</div></li>`;
  };
  return `<div class="section-heading"><${tag}>Issuer events</${tag}><span>Historical record</span></div><p class="intro">Events are ordered by the first year and month named in each date cell; rows with no year follow. Row text is shown as retained.</p><ol class="timeline">${orderEvents(table.rows).map(rowMarkup).join('')}</ol>`;
}
function businessVisual() {
  const row=findRow(pins['CP-1A'],'Company, business','End markets / concentration');
  // Read the mix from the retained cell; a change in the handoff surfaces as a failed view.
  const [,mix,reading]=plain(row.row.cells[1]).match(/(FY2024 sales were[^.]+\.) (.+)$/);
  const parts=[...mix.matchAll(/(\d+)% ([^,.]+?)(?=,|\.)/g)].map(m=>[m[2].replace(/^and /,''),Number(m[1])]),max=Math.max(...parts.map(p=>p[1]));
  return `<div class="section-heading"><h2>Revenue exposure</h2><span>FY2024 · approximate</span></div><div class="mix-bars">${parts.map(([label,n])=>`<div><span>${esc(label)}</span><button data-evidence="${esc(row.key)}" aria-label="${esc(label)} approximately ${n} percent, view source"><i style="width:${n/max*100}%"></i></button><strong>≈${n}%</strong></div>`).join('')}</div><p class="chart-reading">${esc(reading)}</p>${sourceFooter(row.key)}`;
}
function factorMatrix() {
  const id=pins['CP-2'],table=sectionData(id,'factors')[0].blocks.find(b=>b.type==='table');
  return `<div class="section-heading"><h2>Six-factor view</h2><span>Qualitative · no composite score</span></div><div class="factor-matrix">${table.rows.map(row=>{
    const grade=plain(row.cells[1]).split(' — ')[0], cls=grade==='Weak'?'adverse':grade==='Not Assessable'?'unknown':'neutral';
    return `<div class="factor"><div><h3>${esc(row.cells[0])}</h3>${sourceLink(`${id}:${row.line}`,'Evidence & rationale')}</div><span class="grade ${cls}">${esc(grade)}</span><p>${rich(row.cells[2])}</p></div>`;
  }).join('')}</div><p class="matrix-note">“Not Assessable” is an evidence limitation, not an adverse grade.</p>`;
}
function downside() {
  const id=pins['CP-2'],block=sectionData(id,'factors')[0].blocks.find(b=>b.text?.startsWith('**Primary downside path:**'));
  return `<div class="downside"><p>${rich(block.text)}</p></div>${sourceFooter(`${id}:${block.line}`)}`;
}
function assessment() {
  const id=pins['CP-2'];
  return `${factorMatrix()}${downside()}${sectionsMarkup(id,sectionData(id,'assessment'))}`;
}
const readerFacts=({confidence,limitation})=>`<dl class="summary-facts"><div><dt>Confidence</dt><dd>${esc(confidence)}</dd></div><div><dt>Main limitation</dt><dd>${rich(limitation)}</dd></div></dl>`;
function callBand(id,section) {
  const {summary,call}=data[id];
  if(section!==modules[id].first||!(summary||call))return '';
  const {text,line}=summary?{text:summary.bottomLine,line:summary.line}:call;
  return `<div class="analysis-call"><p class="call-quote">${rich(text.replace(/\n/g,' '))}</p>${summary?readerFacts(summary):''}</div>${sourceFooter(`${id}:${line}`)}`;
}
// An analytical output is one module report whatever the section: the section only names the part scrolled to.
function renderContent(id,section) {
  if(!isAnalytical(id))return workspaceView(id,section);
  return moduleReport(id);
}
// One named section as the library has always drawn it; the report's Evidence & audit list opens these.
function sectionView(id,section) {
  const band=callBand(id,section);
  if(id===pins['CP-1']&&section==='performance')return band+performanceView();
  if(id===pins['CP-1A']&&section==='events'){const table=eventTable(sectionData(id,section));if(table)return band+eventTimeline(id,table);}
  if(id===pins['CP-2']&&section==='assessment')return band+assessment();
  if(id===pins['CP-8']&&section==='comparison')return band+comparisonView();
  let visual=band+(id===pins['CP-1A']&&section==='business'?businessVisual():id===pins['CP-1']&&section==='cash'?trendChart(id,'Net cash provided by operating activities'):id===pins['CP-2']&&section==='outlook'?downside():'');
  visual+=galleryVisual(id,section)+readerCharts(id,section);
  if(section==='audit')visual+=`<div class="audit-intro"><h2>Original output & technical audit</h2><p>The retained output is available alongside its designed presentation. Analytical acceptance has not been verified by this library.</p><a href="${esc(data[id].href)}" download>Download original handoff</a><p class="hash">SHA-256 ${data[id].sha256}</p></div>`;
  return visual+sectionsMarkup(id,sectionData(id,section),true);
}
function renderSearch(query) {
  if(!query){$('search-results').replaceChildren();return;}
  const context=current.context,has=(...parts)=>parts.join(' ').toLowerCase().includes(query);
  // Default outputs first, so the first hit opens what the module itself opens.
  const isDefault=id=>defaultOutput(data[id].module,context)===id;
  const outputs=Object.keys(data).filter(id=>data[id].run===context).sort((a,b)=>isDefault(b)-isDefault(a));
  const code=id=>data[id].label===data[id].module?moduleNames[data[id].module]:`${moduleNames[data[id].module]} · ${data[id].label}`;
  const sectionOf=(id,heading)=>modules[id].sections.find(s=>s[2].some(p=>matchesHeading(heading,p)))?.[0];
  const href=(id,section,key=null)=>routeHref(data[id].module,section,key,context,data[id].source);
  const hit=(kind,owner,label,target)=>`<a class="search-hit" href="${esc(target)}" aria-label="${esc(`${kind}: ${owner} ${label}`)}"><span class="code">${esc(owner)}</span><span>${esc(label)}</span></a>`;
  const group=(title,total,hits)=>total?`<div class="search-group"><p>${title}${hits.length<total?` · ${hits.length} of ${total}`:''}</p>${hits.join('')}</div>`:'';
  // A row's title can be a bare row number; name the cell that matched unless it is a whole paragraph.
  const itemLabel=item=>{
    const title=plain(item.title),cell=item.fields.map(field=>plain(field[1]??'')).find(value=>has(value));
    return has(title)||!cell||cell.length>80?title:`${title} · ${cell}`;
  };
  const figures=outputs.flatMap(id=>{
    const tables=data[id].sections.filter(s=>s.blocks.some(b=>b.type==='table')),visual=data[id].visual;
    const plotted=visual&&tables.find(s=>s.blocks.some(b=>b.line===visual.table));
    return [...(plotted?[[id,visual.title,plotted.heading]]:[]),...tables.map(s=>[id,plain(s.heading.replace(METHOD_CODE,'')),s.heading])];
  }).filter(([id,label])=>has(label,data[id].module));
  const files=[
    ...outputs.filter(id=>has(data[id].source,data[id].label)).map(id=>hit('Source',code(id),handoffLabel(data[id].source),href(id,modules[id].first))),
    ...Object.values(store.inputs).filter(input=>input.run===context&&has(input.source)).map(input=>hit('Source',moduleNames[input.module]||input.module,input.source,routeHref('W-Evidence','sources',null,context))),
  ];
  const items=[...evidence.entries()].filter(([,item])=>item.run===context&&has(item.title,...item.fields.map(field=>field[1]))).sort((a,b)=>outputs.indexOf(a[1].output)-outputs.indexOf(b[1].output));
  $('search-results').innerHTML=group('Figures',figures.length,figures.slice(0,6).map(([id,label,heading])=>hit('Figure',code(id),label,href(id,sectionOf(id,heading)))))
    +group('Sources',files.length+items.length,[...files.slice(0,4),...items.slice(0,4).map(([key,item])=>hit('Reference',code(item.output),itemLabel(item),href(item.output,sectionOf(item.output,item.section),key)))]);
  nameCodes($('search-results'),null,false); // hits come from several outputs, so no step title is borrowed from the open one (a step id reads "a method step"); register references stay as they are
}
function renderNavigator(module) {
  const query=$('module-search').value.trim().toLowerCase(),{html,count}=navigatorView(module,query);
  // Flat and always open (decision 5): the list is the run's modules, the open one with its page outline under it.
  $('module-list').innerHTML=html;
  nameCodes($('module-list'));
  document.querySelector('.nav-filter').innerHTML=`${query?'Matches':'Modules'} <span>${count}</span>`;
  $('module-search-clear').hidden=!$('module-search').value;
  renderSearch(query);
}
function parseRoute() {
  const [path,query='']=location.hash.slice(1).split('?');
  const [encodedModule,encodedSection]=path.split('/');
  // routeHref encodes each segment once. A module escape that cannot be decoded is read as typed (an unknown module
  // opens the library); a section escape that cannot be decoded names no section, so the module opens its default.
  let requestedModule=encodedModule,requestedSection=encodedSection;
  try{requestedModule=decodeURIComponent(encodedModule);}catch(error){if(!(error instanceof URIError))throw error;}
  try{if(encodedSection!==undefined)requestedSection=decodeURIComponent(encodedSection);}catch(error){if(!(error instanceof URIError))throw error;requestedSection=null;}
  // The Calendar and Reports pages are retired (decisions 1 and 12 of the reader ruling): their old hashes open the run's Report history, or the library when no run is known.
  if(requestedModule==='W-Calendar'||requestedModule==='W-Reports'){requestedModule='W-Report';requestedSection='history';}
  const resolved=!Object.hasOwn(moduleNames,requestedModule)&&Object.hasOwn(aliases,requestedModule)?aliases[requestedModule]:requestedModule;
  let module=Object.hasOwn(moduleNames,resolved)?resolved:'W-Library';
  const params=new URLSearchParams(query);
  let fallback=data[pins[module]]?.run;
  const requestedContext=params.get('c');
  let context=Object.hasOwn(contexts,requestedContext)?requestedContext:fallback||current?.context||Object.keys(contexts)[0]||null;
  if(!context&&!appDestinations.has(module))module='W-Library';
  const output=resolveOutput(module,context,params.get('o'));
  const sections=navigationSections(module,context,output),first=output&&isAnalytical(module)?REPORT_PARTS[0][0]:modules[module]?.first;
  // A report page also routes to one drawn section, as s-<line>; any other name opens the head.
  const anchored=Boolean(output&&isAnalytical(module))&&drawnAnchors(output).has(requestedSection);
  // The Forecast page draws its chart index after the models: that one name scrolls to it. It draws the model the Forecast tab
  // would open (the remembered section while it is a section of this run, else the first) and leaves what is remembered alone.
  const part=module==='W-Forecast'&&requestedSection==='run-charts'?requestedSection:null;
  const remembered=part&&lastSection.get(context+':W-Forecast');
  const selected=anchored?[requestedSection,plain(data[output].sections.find(s=>`s-${s.line}`===requestedSection).heading.replace(METHOD_CODE,'')),[]]:sections.find(s=>s[0]===requestedSection)||sections.find(s=>s[0]===remembered)||sections.find(s=>s[0]===first)||sections[0];
  const e=params.get('e'),key=e&&(e.includes(':')?e:`${output}:${e}`),item=evidence.get(key);
  const permitted=item&&item.run===context&&(item.output===output||module==='W-Overview');
  const file=output&&output!==defaultOutput(module,context)?data[output].source:null;
  // A chip index names one of the key's chips, and `gaps` its unresolved citations; one that is not there opens the row alone.
  const keyChips=window.CREDIT_OS_DATA?.chips?.[key]||[],requestedChip=params.get('chip')??'';
  // `p` opens a paragraph's or row's Basis; `f<n>` its n-th figure (reader.js paragraphView).
  const chip=/^\d+$/.test(requestedChip)&&Number(requestedChip)<keyChips.length?Number(requestedChip):requestedChip==='gaps'&&keyChips.some(unresolvedGap)?'gaps':/^(p|f\d+)$/.test(requestedChip)?requestedChip:null;
  // The Evidence page's tab is its route section and its module filter the `m` parameter, read the way `c` is; evidence.js owns both.
  const evidencePage=module==='W-Evidence'?window.Evidence.parseHash(location.hash,Object.keys(contexts[context]?.modules||{})):null;
  return {module,output,file,section:selected[0],label:selected[1],context,evidence:permitted?key:null,chip:permitted?chip:null,part,tab:evidencePage?.tab??null,evidenceModule:evidencePage?.module??null};
}
function go(module,section,key=null,file,chip=null) {location.hash=file===undefined?routeHref(module,section,key,current?.context,undefined,chip):routeHref(module,section,key,current?.context,file,chip);}
// The source-page part of the inspector for the chip that opened it. The excerpt, flags and reasons are the build's; nothing is judged here.
function chipSection(chip,output) {
  const hash=chip.hash_matches_inventory===true?'<span class="badge badge-gray">Matches publication</span>':chip.hash_matches_inventory===false?'<span class="badge badge-attention">Changed since inventory</span>':'';
  const quote=chip.quote_found===true?'<span class="badge badge-gray">Quote found on page</span>':chip.quote_found===false?'<span class="badge badge-attention">Quote not found</span>':'';
  const reason=chip.reason?`<p class="small chip-reason">${esc(chip.reason)}</p>`:'';
  if(chip.kind!=='issuer_page') {
    const what=chip.kind==='upstream'?`Upstream · ${esc([chip.module,...chip.codes].filter(Boolean).join(' · '))}`:`Citation gap · ${esc(chip.label||'no page')}`;
    return `<div class="chip-source"><h3>${what}</h3>${reason}</div>`;
  }
  const pages=chip.page_end!=null&&chip.page_end!==chip.page?`${chip.page}–${chip.page_end}`:chip.page;
  let excerpt='';
  if(chip.excerpt) {
    // The build says what it matched (`match`, at `match_at` in the excerpt); the page marks that and judges nothing.
    const at=chip.match?(Number.isInteger(chip.match_at)?chip.match_at:chip.excerpt.indexOf(chip.match)):-1,marked=at>=0&&chip.excerpt.startsWith(chip.match,at);
    excerpt=`<div class="excerpt">${marked?`${esc(chip.excerpt.slice(0,at))}<mark>${esc(chip.match)}</mark>${esc(chip.excerpt.slice(at+chip.match.length))}`:esc(chip.excerpt)}</div>`;
  }
  // The output's href points into runs/<run>/...; the retained source text sits beside the handoff's folder tree in the same run.
  const root=output.href.split('/').slice(0,-output.source.split('/').length).join('/');
  // A source text the build could not read (no hash match result, no excerpt) has no file to open; the reason stands instead.
  const absent=chip.hash_matches_inventory===null&&!chip.excerpt;
  const open=chip.file&&!absent?`<a class="btn" href="${esc(`${root}/source-text/${encodeURIComponent(chip.file)}`)}">${icon('file-text')}Open source file</a>`:'';
  return `<div class="chip-source"><h3>Source page · ${esc(chip.file||chip.source)} p.${esc(pages)}</h3><div class="chip-flags">${hash}${quote}</div>${chip.file&&chip.source?`<p class="small chip-key">Cited as ${esc(chip.source)}</p>`:''}${reason}${excerpt}${chip.sha256?`<p class="hash">SHA-256 ${esc(chip.sha256)}</p>`:''}<p>${open}</p></div>`;
}
// One resolved Basis item of a new-format paragraph in words (reader.js inspectorItemHtml); `deps` is built once per paragraph. `used` collects the chips an item took.
function basisItemHtml(item,deps,used) {
  if(item.kind==='source') item.chips.forEach(c=>used.add(c));
  return inspectorItemHtml(item,deps);
}
// The figure an `f<n>` control opened the inspector from, drawn first in the inspector (the large value under its eyebrow); none for a paragraph's or a chip's control.
function inspectorFigure(item,output,mode) {
  if(typeof mode!=='string'||!mode.startsWith('f')||item.text===undefined)return '';
  const span=figureSpans(paragraphBody(item.text,!isNewFormat(output.sections)).body)[Number(mode.slice(1))];
  return span?`<p class="inspector-figure"><span class="kicker">Figure</span> <strong>${esc(span.text)}</strong></p>`:'';
}
// The inspector part for a paragraph's Basis control (`p`) or one of its figures (`f<n>`), or for a table row's control: the Basis items
// in words with the chips each resolved to, then every other chip the build holds for the key. An earlier-format paragraph shows its citations as written.
function paragraphBasisHtml(key,item,output,mode,chips) {
  chips=uniqueChips(chips);
  const earlier=!isNewFormat(output.sections),used=new Set();
  let items='';
  if(item.text!==undefined) {
    // reader.js draws the list (the same code the node tests read): an upstream-handoff item shows its written name; nameCodes names the rest, citations of an earlier-format page included.
    const deps={chipSection:c=>chipSection(c,output),moduleHref,icon};
    const ev=contexts[output.run]?.evidence||{},files=[...(ev.sources||[]),...(ev.unused||[]),...(ev.unrecorded||[])].map(f=>f.name);
    items=inspectorBasisBlock(item.text,earlier,{sections:output.sections,chips,files,ran:code=>defaultOutput(code,output.run)},it=>basisItemHtml(it,deps,used));
  }
  const rest=chips.filter(c=>!used.has(c));
  return `${items}${rest.length?`<h3 class="citations-heading">${items?'Other citations':'Citations'}</h3>${rest.map(c=>chipSection(c,output)).join('')}`:''}`;
}
function showInspector(key,chipIndex=null) {
  const item=evidence.get(key), output=data[item.output], keyChips=window.CREDIT_OS_DATA?.chips?.[key]||[];
  const paragraph=typeof chipIndex==='string'&&chipIndex!=='gaps';
  const chipHtml=paragraph?paragraphBasisHtml(key,item,output,chipIndex,keyChips):chipIndex==='gaps'?keyChips.filter(unresolvedGap).map(c=>chipSection(c,output)).join(''):chipIndex===null?'':chipSection(keyChips[chipIndex],output);
  // A paragraph shows its wording without its Basis line or citations; they are listed below it.
  const figure=paragraph?inspectorFigure(item,output,chipIndex):'';
  const fields=paragraph&&item.text!==undefined?[['Paragraph',paragraphBody(item.text,!isNewFormat(output.sections)).body]]:item.fields;
  $('inspector').hidden=false;
  $('inspector').innerHTML=`<div class="inspector-bar"><p class="drawer-title">Trace</p><span>Esc</span><button type="button" id="back-analysis" class="drawer-close" aria-label="Close the trace and go back to the analysis">${window.Components.icon('x')}</button></div><div class="inspector-body"><h2${figure?' class="sr-only"':' class="kicker"'}>Evidence inspector</h2>${figure}<h3>${esc(item.title)}</h3><div class="evidence-context">${esc(moduleTitle(item.module))}${output.label===item.module?'':` · ${esc(output.label)}`} · Line ${item.line}</div><span class="badge badge-gray classification">${esc(classification(item))}</span><div class="evidence-fields">${fields.map(([label,value])=>`<div><h4>${esc(label)}</h4><div>${rich(value)}</div></div>`).join('')}</div>${item.basis?`<div class="evidence-basis"><h3>Basis & context</h3><p class="inspector-card">${rich(item.basis)}</p></div>`:''}${chipHtml}<div class="source-location"><h3>Source location</h3><div class="inspector-card"><p>${esc(item.section)}</p><a href="${esc(output.href)}" download>${icon('file-text')}Download retained handoff</a><p class="small">${esc(handoffLabel(output.file))}<br>${esc(output.case)} · saved output</p></div></div><div class="inspector-note"><strong>Reading boundary</strong><p>Retained fields from this historical run, with module codes and method step ids shown as names. Source and PDF locators remain attributed to the original handoff. The library does not authenticate the underlying PDFs.</p></div></div>${drawerFoot(item.module)}`;
  nameCodes($('inspector'),item.output,false); // the inspector keeps register references as they are
  document.querySelectorAll('[data-evidence]').forEach(el=>el.classList.toggle('source-selected',el.dataset.evidence===key));
  document.querySelectorAll('.chip,.trace-row').forEach(el=>{
    const pressed=el.dataset.chip===key?Number(el.dataset.index)===chipIndex:el.dataset.evidence===key&&chipIndex===null;
    if(pressed)el.setAttribute('aria-pressed','true');else el.removeAttribute('aria-pressed');
  });
  document.querySelectorAll('[data-paragraph]').forEach(el=>{
    const mode=el.dataset.figure===undefined?'p':`f${el.dataset.figure}`;
    if(el.dataset.paragraph===key&&mode===chipIndex)el.setAttribute('aria-pressed','true');else el.removeAttribute('aria-pressed');
  });
  if(returnTrigger) {
    $('back-analysis').focus({preventScroll:true});
  }
}
function moduleBody({module,context,output}) {
  try {
    if(module===MODEL_ENTRY[0])return forecastView(context,current.section);
    if(output||!isAnalytical(module))return renderContent(output||module,current.section);
    return moduleEntry(module,context)?.outputs.length?outputChooser(module):unavailableView(module);
  } catch(error) {
    // Documented fail-open: logged, and the reader keeps the new header and the original file.
    console.error(error);
    return `<div class="missing-state"><div class="empty-symbol">${icon('file-text')}</div><h2>Couldn’t present this output</h2><p>The screen could not render this view. The saved file is unchanged.</p>${output?`<a class="text-action" href="${esc(data[output].href)}" download>Download the original handoff</a>`:''}</div>`;
  }
}
let cancelModelFrame=null;
// A number box with text it cannot read is 'invalid', which excludes every run rather than being ignored.
function readLibraryFilters() {
  const before=JSON.stringify(libraryFilters);
  $('library-filters').querySelectorAll('[data-library-filter]').forEach(control=>{libraryFilters[control.dataset.libraryFilter]=control.validity?.badInput?'invalid':control.value;});
  if(JSON.stringify(libraryFilters)!==before)updateLibrary(); // a change event after the input event adds nothing and must not swallow the click that blurred the box
}
// The Library route keeps its filter state in the query. Only a known key with a valid value is applied (a select key one of its options, a number key a finite number, search up to 200 characters); anything else is dropped.
const LIBRARY_QUERY_KEYS=[...Object.keys(LIBRARY_DEFAULTS),'sort','dir'];
const libraryNumber=value=>/^-?(\d+(\.\d+)?|\.\d+)([eE][-+]?\d+)?$/.test(value)&&Number.isFinite(Number(value));
function readLibraryHash() {
  const query=location.hash.split('?')[1];
  if(!query)return false;
  const choices=libraryChoices(),before=JSON.stringify([libraryFilters,libraryState]);
  for(const [key,value] of new URLSearchParams(query)) {
    if(key==='sort'){if(LIBRARY_COLUMNS.some(([column])=>column===value))libraryState.sortKey=value;}
    else if(key==='dir'){if(value==='asc'||value==='desc')libraryState.direction=value;}
    else if(!Object.hasOwn(LIBRARY_DEFAULTS,key))continue;
    else if(key==='search'){if(value.length<=200)libraryFilters.search=value;}
    else if(Object.hasOwn(choices,key)){if(choices[key].some(([option])=>option===value||key==='issuer'&&LibraryLogic.issuerKey(option)===LibraryLogic.issuerKey(value)))libraryFilters[key]=value;}
    else if(libraryNumber(value))libraryFilters[key]=value;
  }
  return before!==JSON.stringify([libraryFilters,libraryState]);
}
// Written with replaceState so typing does not re-render the route; defaults are left out.
function writeLibraryHash() {
  const [path,query='']=location.hash.slice(1).split('?'),params=new URLSearchParams(query);
  for(const key of LIBRARY_QUERY_KEYS)params.delete(key);
  for(const [key,value] of Object.entries(libraryFilters))if(value!==LIBRARY_DEFAULTS[key]&&value!=='invalid')params.set(key,value);
  if(libraryState.sortKey){params.set('sort',libraryState.sortKey);params.set('dir',libraryState.direction);}
  const hash=`#${path}${params.size?`?${params}`:''}`;
  if(hash!==location.hash)history.replaceState(null,'',hash);
}
function resetLibrary() {
  Object.assign(libraryFilters,LIBRARY_DEFAULTS);
  Object.assign(libraryState,{selected:'',sortKey:'',direction:'asc',hidden:''});
  updateLibrary(true);
}
// Clicks inside the Library screen; true when one was handled.
function libraryClick(target) {
  const choose=target.closest('[data-library-select]'),sort=target.closest('[data-library-sort]'),source=target.closest('[data-library-source]'),hide=target.closest('[data-library-hidden]'),back=target.closest('[data-library-back]');
  if(choose) {
    libraryState.selected=choose.dataset.librarySelect;updateLibrary();
    $('run-detail').focus({preventScroll:true});$('run-detail').scrollIntoView({block:'start'});
  } else if(sort) {
    const key=sort.dataset.librarySort;
    libraryState.direction=libraryState.sortKey===key&&libraryState.direction==='asc'?'desc':'asc';libraryState.sortKey=key;
    updateLibrary();$('library-results').querySelector(`[data-library-sort="${key}"]`).focus();
  } else if(hide) {
    libraryState.hidden=hide.dataset.libraryHidden;updateLibrary();$('library-hidden-title').focus();
  } else if(back) {
    const group=libraryState.hidden;libraryState.hidden='';updateLibrary();
    $('library-coverage').querySelector(`[data-library-hidden="${group}"]`)?.focus();
  } else if(source) {
    $('metric-sources').open=true;
    const block=$(`source-${source.dataset.librarySource}`);block.focus({preventScroll:true});block.scrollIntoView({block:'center'});
  } else if(target.closest('#library-clear,#library-empty-reset')) {
    resetLibrary();$('library-query').focus();
  } else return false;
  return true;
}
// An Evidence & audit item opens its section in place, drawn the first time it is opened.
function openAuditSection(button) {
  const body=$(button.getAttribute('aria-controls')),open=body.hidden;
  if(open&&!body.dataset.drawn) {
    try {body.innerHTML=sectionView(current.output,button.dataset.audit);if(!keepsCodes(current))nameCodes(body);body.dataset.drawn='1';}
    catch(error) {
      // Documented fail-open, as in moduleBody: logged, and the item says it could not be drawn; the saved file is unchanged.
      console.error(error);
      body.innerHTML='<p class="small">Couldn’t present this item. The saved file is unchanged.</p>';
    }
  }
  body.hidden=!open;
  button.setAttribute('aria-expanded',String(open));
}
function showNavigator(open) {
  $('navigator').classList.toggle('mobile-open',open);
  $('module-toggle').setAttribute('aria-expanded',String(open));
}
function focusSearch() {
  if(current.module!=='W-Library'&&(appDestinations.has(current.module)||!contexts[current.context])){location.hash='W-Library/cases';renderRoute();}
  if(current.module==='W-Library'){$('library-query').focus();return;}
  showNavigator(true);
  $('module-search').focus();
}
// The module or destination name (with the run code on the Evidence page only).
function contextPrefix({module,context}) {
  const ctx=contexts[context];
  // The run code is the Evidence page's to show.
  return ctx&&!appDestinations.has(module)?`<span class="section-context">${module==='W-Evidence'?`${esc(ctx.run)} · `:''}${esc(moduleNames[module])}</span>`:'';
}
// No page shows a module code (owner ruling 2026-11-12). The Evidence page lists issuer source file names and hashes, which identify files:
// it is drawn with its module names already (views.js) and is never rewritten; every other page is named here.
const keepsCodes=route=>route.module==='W-Evidence';
const reportPage=route=>Boolean(route?.output&&isAnalytical(route.module));
// The reading position of a page: a module report is one page whatever part is scrolled to.
const positionKey=route=>`${route.context}:${route.output||route.module}:${reportPage(route)?'report':route.section}`;
// Scroll the canvas to one of the report's parts or sections; the head is the top. Unknown names never reach here: parseRoute maps them to the head.
// Every closed <details> that is or holds the target is opened first, so a route into a folded part shows what it names.
function scrollToPart(part) {
  const content=$('content'),target=part==='head'?null:$(part);
  if(target)openFolds(target);
  content.scrollTop=target?Math.max(0,content.scrollTop+target.getBoundingClientRect().top-content.getBoundingClientRect().top-10):0;
}
function openFolds(target) {
  for(let fold=target.closest('details');fold;fold=fold.parentElement?.closest('details'))fold.open=true;
}
// The section rail (a new-format module page): the item of the part at the top of the canvas is the current one. A part is current while it crosses the top
// 30% of the canvas, the first one in page order when several do; the last part is current once it is wholly in view, since a short last part never reaches the top.
function markRail(rail,part) {
  for(const link of rail.querySelectorAll('a.rail-item')) {
    const on=link.dataset.part===part;
    link.classList.toggle('on',on);
    if(on)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');
  }
}
let railObservers=[];
function watchRail() {
  for(const observer of railObservers)observer.disconnect();
  railObservers=[];
  const content=$('content'),rail=content.querySelector('.sec-rail');
  // Without IntersectionObserver the rail stays a list of working links; nothing is marked.
  if(!rail||typeof IntersectionObserver==='undefined')return;
  const parts=[...rail.querySelectorAll('a.rail-item')].map(link=>document.getElementById(link.dataset.part)).filter(Boolean);
  if(!parts.length)return;
  const crossing=new Set();
  let atEnd=false;
  const show=()=>{const shown=atEnd?parts.at(-1):parts.find(part=>crossing.has(part));if(shown)markRail(rail,shown.id);};
  railObservers.push(new IntersectionObserver(entries=>{for(const entry of entries)(entry.isIntersecting?crossing.add(entry.target):crossing.delete(entry.target));show();},{root:content,rootMargin:'0px 0px -70% 0px'}));
  railObservers.push(new IntersectionObserver(entries=>{atEnd=entries.at(-1).intersectionRatio>=0.99;show();},{root:content,threshold:[0,0.99,1]}));
  for(const part of parts)railObservers[0].observe(part);
  railObservers[1].observe(parts.at(-1));
}
function renderRoute() {
  const next=parseRoute(), previous=current;
  // Moving between the parts of one report scrolls; it draws nothing again.
  const sameReport=reportPage(next)&&reportPage(previous)&&next.module===previous.module&&next.output===previous.output&&next.context===previous.context;
  const changed=!current||next.module!==current.module||next.output!==current.output||(next.section!==current.section&&!sameReport)||next.context!==current.context||next.tab!==current.tab||next.evidenceModule!==current.evidenceModule;
  const partMove=sameReport&&next.section!==previous.section;
  const focused=document.activeElement,focusId=focused?.id,focusHref=focused?.getAttribute('href'),hashed=next.module==='W-Library'&&readLibraryHash();
  if(changed&&previous)readingPositions.set(positionKey(previous),$('content').scrollTop);
  current=next; if(!reportPage(next))lastSection.set(next.context+':'+next.module,next.section);
  if(next.file)lastFile.set(`${next.context}:${next.module}`,next.file);else lastFile.delete(`${next.context}:${next.module}`);
  if(isAnalytical(next.module))lastSection.set(next.context+':module',next.module);
  if(changed) {
    const sections=navigationSections(next.module,next.context,next.output),index=sections.findIndex(s=>s[0]===next.section);
    $('module-head').innerHTML=moduleHead(next);
    // A page with one section already says its name in the heading above.
    const only=sections.length===1&&!isAnalytical(next.module);
    // The pager names what it steps through on the page where the sections are models.
    const pagerNoun={'W-Forecast':'model',[MODEL_ENTRY[0]]:'model'}[next.module]||'section';
    const report=reportPage(next);
    // A module report has no heading above this one but the issuer's h1, so there it is an h2; elsewhere it sits under the page's h2.
    const level=report?'h2':'h3';
    const title=`<${level} id="section-title" tabindex="-1" ${only||report||(isAnalytical(next.module)&&!next.output)?'class="sr-only"':''}>${esc(report||next.module===MODEL_ENTRY[0]?moduleNames[next.module]:sections[index][1])}</${level}>`;
    // The bar sticks at narrow widths, so it names the run and the module (or destination) it belongs to.
    $('section-nav').innerHTML=contextPrefix(next)+(only||report||(isAnalytical(next.module)&&!next.output)?title:`${title}<span>${index+1} / ${sections.length}</span><button id="previous-section" ${index===0?'disabled':''} aria-label="Previous ${pagerNoun}">${icon('arrow-left')}</button><button id="next-section" ${index===sections.length-1?'disabled':''} aria-label="Next ${pagerNoun}">${icon('arrow-right')}</button>`);
    nameCodes($('section-nav'));
    updateWorkspaceChrome(next.module);
    nameCodes($('context-bar'));
    $('content').innerHTML=moduleBody(next);
    watchRail();
    // watchFrame returns the callback that stops its timer; the previous model's timer must not fire against a detached element.
    if(cancelModelFrame)cancelModelFrame();
    cancelModelFrame=null;
    const modelFrame=$('model-preview');
    // The published model loads only when its disclosure is first opened: the frame gets its address and its watch then.
    const disclosure=$('content').querySelector('details.model-original');
    if(modelFrame&&disclosure){
      const openModel=()=>{
        if(!disclosure.open||modelFrame.getAttribute('src'))return;
        modelFrame.setAttribute('src',modelFrame.dataset.src);
        cancelModelFrame=watchFrame(modelFrame,disclosure.querySelector('.frame-status'),'Loading model…','The model did not load.',()=>{const link=document.createElement('a');link.setAttribute('href',modelFrame.dataset.download);link.download='';link.textContent='Download original HTML';return link;});
      };
      disclosure.addEventListener('toggle',openModel);
    }
    if(!keepsCodes(next)){nameCodes($('module-head'));nameCodes($('content'));}
    $('content').scrollTop=readingPositions.get(positionKey(next))||0;
    if(reportPage(next)&&next.section!=='head')scrollToPart(next.section);
    if(next.part)scrollToPart(next.part);
    showNavigator(false);
    // Search hits drive moves between analytical modules, so the query is kept there and dropped elsewhere.
    if(previous&&previous.module!==next.module&&!isAnalytical(next.module))$('module-search').value='';
    renderNavigator(next.module);
    titleBase=moduleNames[next.module];applyTitle();
    if(previous) {
      const library=appDestinations.has(next.module)||!contexts[next.context];
      const restored=!library&&focusId&&$(focusId);
      const link=window.innerWidth>720&&focused?.classList.contains('section-item')&&focusHref&&[...$('module-list').querySelectorAll('.section-item')].find(el=>el.getAttribute('href')===focusHref);
      const destination=(next.module==='W-Forecast'||next.module===MODEL_ENTRY[0])&&$('model-select')?$('model-select'):library?$('canvas'):$('section-title');
      (restored&&!restored.disabled?restored:link||destination).focus({preventScroll:true});
      if(previous.module!==next.module||previous.context!==next.context)$('navigator').scrollTop=0;
    }
  } else if(next.part)scrollToPart(next.part);
  if(partMove) {
    scrollToPart(next.section);
    renderNavigator(next.module);
    const link=focused?.classList.contains('section-item')&&[...$('module-list').querySelectorAll('.section-item')].find(el=>el.getAttribute('href')===focusHref);
    if(link)link.focus({preventScroll:true});
  }
  if(next.evidence) {
    // A route to a row inside a folded part (a link, a reload) opens the part holding its trigger; Esc then returns to that trigger.
    const opener=`.chip[data-evidence="${CSS.escape(next.evidence)}"],.trace-row[data-evidence="${CSS.escape(next.evidence)}"],[data-paragraph="${CSS.escape(next.evidence)}"]`;
    const trigger=reportPage(next)||next.module==='W-Overview'?($(next.section)||$('content')).querySelector(opener)||$('content').querySelector(opener):null;
    if(trigger) {
      openFolds(trigger);
      if(!returnTrigger?.isConnected){returnTrigger=trigger;returnContentScroll=$('content').scrollTop;}
    }
    showInspector(next.evidence,next.chip);
  }
  else {
    $('inspector').hidden=true;
    document.querySelectorAll('.source-selected').forEach(el=>el.classList.remove('source-selected'));
    document.querySelectorAll('.chip[aria-pressed],.trace-row[aria-pressed],[data-paragraph][aria-pressed]').forEach(el=>el.removeAttribute('aria-pressed'));
    if(previous?.evidence&&!changed) {
      $('content').scrollTop=returnContentScroll;
      if(window.innerWidth<=1050) window.scrollTo(0,returnScroll);
      if(returnTrigger?.isConnected)returnTrigger.focus({preventScroll:true});else $('canvas').focus({preventScroll:true});
    }
  }
  if(hashed&&!changed)updateLibrary(true);
  if(next.module==='W-Library')writeLibraryHash();
  const named=contexts[next.context]&&!appDestinations.has(next.module)?`${contexts[next.context].title}, ${runName(contexts[next.context])}, `:'';
  $('announcement').textContent=`${named}${moduleNames[next.module]}, ${namedText(next.label)}${next.evidence?', evidence open':''}`;
}
document.addEventListener('change',event=>{
  if(event.target.matches('[data-library-filter]'))readLibraryFilters();
  if(event.target.id==='model-select')go(current.module,event.target.value);
  if(event.target.id==='output-select')go(current.module,current.section,null,event.target.value);
  if(event.target.id==='chart-metric') {
    $('module-visual').innerHTML=comparisonChart(current.output,data[current.output].visual,Number(event.target.value));
    nameCodes($('module-visual'));
    $('chart-metric').focus({preventScroll:true});
  }
});
document.addEventListener('click',event=>{
  if(event.target.closest('#rail-search')){focusSearch();return;}
  if(window.Evidence.handleClick(event.target))return;
  if(window.Components.handleClick(event.target))return;
  const searchHit=event.target.closest('.search-hit');
  if(searchHit){returnTrigger=$('module-search');showNavigator(false);if(searchHit.hash===location.hash)$('canvas').focus();}
  if(libraryClick(event.target))return;
  if(event.target.closest('.skip')){event.preventDefault();if(current.evidence){returnTrigger=$('canvas');go(current.module,current.section);}else $('canvas').focus();return;}
  const chip=event.target.closest('[data-chip]');
  if(chip){event.preventDefault();returnTrigger=chip;returnScroll=window.scrollY;returnContentScroll=$('content').scrollTop;go(current.module,current.section,chip.dataset.chip,undefined,Number(chip.dataset.index));return;}
  const paragraph=event.target.closest('[data-paragraph]');
  if(paragraph){event.preventDefault();returnTrigger=paragraph;returnScroll=window.scrollY;returnContentScroll=$('content').scrollTop;go(current.module,current.section,paragraph.dataset.paragraph,undefined,paragraph.dataset.figure===undefined?'p':`f${paragraph.dataset.figure}`);return;}
  const gaps=event.target.closest('[data-gaps]');
  if(gaps){event.preventDefault();returnTrigger=gaps;returnScroll=window.scrollY;returnContentScroll=$('content').scrollTop;go(current.module,current.section,gaps.dataset.gaps,undefined,'gaps');return;}
  const audit=event.target.closest('.audit-open');
  if(audit){openAuditSection(audit);return;}
  const part=event.target.closest('a.section-item,a.rail-item');
  if(part&&reportPage(current)&&part.hash===location.hash){event.preventDefault();scrollToPart(current.section);return;}
  const source=event.target.closest('[data-evidence]');
  if(source){event.preventDefault();returnTrigger=source;returnScroll=window.scrollY;returnContentScroll=$('content').scrollTop;go(current.module,current.section,source.dataset.evidence);return;}
  if(event.target.closest('#back-analysis,#drawer-backdrop'))go(current.module,current.section);
  const moduleLink=event.target.closest('.module-item');
  if(moduleLink){$('module-search').value='';if(moduleLink.hash===location.hash)renderNavigator(current.module);}
  const step=event.target.closest('#next-section')?1:event.target.closest('#previous-section')?-1:0;
  if(step){const sections=navigationSections(current.module,current.context),index=sections.findIndex(s=>s[0]===current.section);if(sections[index+step])go(current.module,sections[index+step][0]);}
});
document.addEventListener('input',event=>{if(event.target.matches('input[data-library-filter]'))readLibraryFilters();if(event.target.id==='ev-q')window.Evidence.handleSearch(event.target);});
document.addEventListener('submit',event=>{if(event.target.id==='library-filters')event.preventDefault();});
$('module-search').addEventListener('input',()=>renderNavigator(current.module));
$('module-search-clear').addEventListener('click',()=>{$('module-search').value='';renderNavigator(current.module);$('module-search').focus();});
$('module-toggle').addEventListener('click',()=>showNavigator(!$('navigator').classList.contains('mobile-open')));
document.addEventListener('keydown',event=>{
  const target=event.target,unmodified=!event.metaKey&&!event.ctrlKey&&!event.altKey;
  if(event.key==='/'&&unmodified&&!/^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)){event.preventDefault();focusSearch();return;}
  // A node or an edge of a pathway is a role=button group: Enter and Space choose it, as a click does.
  if((event.key==='Enter'||event.key===' ')&&unmodified&&target.matches?.('[data-map-pick]')){event.preventDefault();window.Components.handleClick(target);return;}
  const step={ArrowRight:1,ArrowDown:1,ArrowLeft:-1,ArrowUp:-1}[event.key];
  if(step&&unmodified) {
    const mark=target.closest?.('[data-evidence]:not(.chip)'),chart=mark?.closest('.bars,.mix-bars,.horizontal-chart,.hedge-chart,.vector-chart');
    if(!chart)return;
    const marks=[...chart.querySelectorAll('[data-evidence]:not(.chip)')],next=marks[marks.indexOf(mark)+step];
    if(next){next.focus();event.preventDefault();}
    return;
  }
  if(event.key!=='Escape')return;
  // One layer at a time: the search text, then the inspector, then the narrow-screen navigator.
  if(target.matches?.('#module-search,#library-query')&&target.value){event.preventDefault();target.value='';target.dispatchEvent(new Event('input',{bubbles:true}));return;}
  if(current.evidence){event.preventDefault();go(current.module,current.section);return;}
  if($('navigator').classList.contains('mobile-open')){showNavigator(false);$('module-toggle').focus();}
});
window.addEventListener('hashchange',renderRoute);
window.addEventListener('resize',placeTabsPill);
document.fonts?.ready.then(placeTabsPill);
// The rail opens 100 ms after the pointer comes within 16 px of its right edge and closes 300 ms after it leaves; touch has no proximity.
(()=>{
  const rail=document.querySelector('.rail');let openTimer=null,closeTimer=null;
  const coarse=window.matchMedia?.('(hover: none), (pointer: coarse)')||{matches:false}; // no matchMedia (test DOMs): treat as a fine pointer
  const inZone=x=>x<=rail.getBoundingClientRect().right+16;
  document.addEventListener('pointermove',event=>{
    if(coarse.matches||event.pointerType!=='mouse')return;
    const near=inZone(event.clientX),isOpen=rail.classList.contains('rail-open');
    if(near){
      clearTimeout(closeTimer);closeTimer=null;
      if(!isOpen&&!openTimer)openTimer=setTimeout(()=>{openTimer=null;rail.classList.add('rail-open');},100);
    }else{
      clearTimeout(openTimer);openTimer=null;
      if(isOpen&&!closeTimer)closeTimer=setTimeout(()=>{closeTimer=null;rail.classList.remove('rail-open');},300);
    }
  });
  // Leaving the window, or the open rail itself for an embedded frame (a pointer inside a frame sends the page nothing), starts the close delay.
  const leave=()=>{
    clearTimeout(openTimer);openTimer=null;
    if(rail.classList.contains('rail-open')&&!closeTimer)closeTimer=setTimeout(()=>{closeTimer=null;rail.classList.remove('rail-open');},300);
  };
  document.documentElement.addEventListener('pointerleave',leave);
  rail.addEventListener('pointerleave',leave);
})();
// Live run activity: re-load activity.js every 30 s while Run activity is the view showing, and once at once when the view is entered. The script
// calls onRunActivity, which re-renders that view through the same moduleBody path as a route change, only when it is still the one showing
// and only when the runs or the held note changed. A re-render keeps the lists the reader opened and the control that had focus.
let activityTimer=null;
let activityShowing=false;
function syncActivityTimer() {
  const wait=nextActivityReload(current);
  if(wait===null){clearTimeout(activityTimer);activityTimer=null;activityShowing=false;return;}
  if(!activityShowing){activityShowing=true;swapActivityScript(document,Date.now());}
  if(activityTimer!==null)return;
  activityTimer=setTimeout(()=>{activityTimer=null;if(nextActivityReload(current)===null)return;swapActivityScript(document,Date.now());syncActivityTimer();},wait);
}
let lastActivity=null;
// Which runs have an opened file list, and which run's control (link, list or its summary) has focus. A run is named by its data-run attribute.
function recordActivityView(root,active) {
  const runs=root.querySelectorAll?.('[data-run]')??[];
  const open=[...runs].filter(el=>el.tagName==='DETAILS'&&el.open).map(el=>el.getAttribute('data-run'));
  const owner=active&&(active.getAttribute?.('data-run')!==null&&active.getAttribute?.('data-run')!==undefined?active:active.parentElement);
  const run=owner?.getAttribute?.('data-run');
  const focus=active&&root.contains?.(active)&&run!==null&&run!==undefined?{run,tag:active.tagName}:null;
  return {open,focus};
}
function restoreActivityView(root,kept) {
  const runs=[...(root.querySelectorAll?.('[data-run]')??[])];
  for(const el of runs)if(el.tagName==='DETAILS'&&kept.open.includes(el.getAttribute('data-run')))el.open=true;
  if(!kept.focus)return;
  const {run,tag}=kept.focus;
  const target=tag==='SUMMARY'?runs.find(el=>el.tagName==='DETAILS'&&el.getAttribute('data-run')===run)?.querySelector('summary'):runs.find(el=>el.tagName===tag&&el.getAttribute('data-run')===run);
  target?.focus?.();
}
window.onRunActivity=()=>{
  if(nextActivityReload(current)===null)return;
  const content=$('content'),live=window.RUN_ACTIVITY,top=content.scrollTop;
  const seen=JSON.stringify([live?.runs,live?.held,live?.cap]);
  if(seen===lastActivity){ // same runs: leave the page as the reader has it; only the snapshot's own time moves
    const stamp=content.querySelector?.('.run-updated-at');
    if(stamp&&typeof live?.updated==='string')stamp.textContent=live.updated;
    return;
  }
  lastActivity=seen;
  const kept=recordActivityView(content,document.activeElement);
  content.innerHTML=moduleBody(current);
  if(!keepsCodes(current))nameCodes(content);
  restoreActivityView(content,kept);
  content.scrollTop=top;
};
window.addEventListener('hashchange',syncActivityTimer);
renderRoute();
syncActivityTimer();
