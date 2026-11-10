/* Presentation only: use the retained report's renderer, citations and evidence controls. */
(() => {
  document.body.classList.add('library-report');
  document.title='Issuer report';
  document.querySelectorAll('.brand-mark').forEach(mark=>mark.replaceChildren());
  document.querySelectorAll('.logo-block').forEach(block=>block.remove());
  const content=document.getElementById('inspector-content');
  if(!content)return;
  let trigger=null;
  const dismiss=document.createElement('button');dismiss.type='button';dismiss.className='inspector-dismiss';dismiss.textContent='Close evidence';
  function close(){document.body.classList.remove('evidence-open');if(trigger?.isConnected)trigger.focus();}
  dismiss.addEventListener('click',close);
  document.querySelector('#inspector .insp-head').prepend(dismiss);
  document.addEventListener('click',event=>{if(!event.target.closest('#inspector'))trigger=event.target.closest('button,a')||trigger;},true);
  function classify(){
    document.querySelectorAll('.page-head>.eyebrow').forEach(label=>label.remove());
    document.querySelectorAll('.fig').forEach(item=>item.classList.toggle('narrative',!item.closest('.fig-cell')&&item.textContent.trim().split(/\s+/).length>=6));
  }
  function update(){
    const selected=!content.textContent.startsWith('Select a figure or source');
    const wasOpen=document.body.classList.contains('evidence-open');
    document.body.classList.toggle('evidence-open',selected);
    if(selected&&!wasOpen)content.focus({preventScroll:true});
  }
  new MutationObserver(classify).observe(document.getElementById('view-root'),{childList:true,subtree:true});
  new MutationObserver(update).observe(content,{childList:true,subtree:true});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&document.body.classList.contains('evidence-open'))close();});
  classify();update();
})();
/* Presentation adaptation of copied reports; original downloads are untouched. */
(() => {
  const navigator=document.querySelector('.navigator'),destinations=document.getElementById('rail-dests');
  if(navigator&&destinations) {
    navigator.prepend(destinations);
    destinations.querySelectorAll('.rail-btn').forEach(button=>{
      const label=document.createElement('span');
      label.textContent=button.getAttribute('aria-label')||button.getAttribute('title')||'';
      button.append(label);
    });
  }
  const scope=document.getElementById('delivery-scope-banner'),call=document.getElementById('call-root');
  if(scope) {
    const details=document.createElement('details'),summary=document.createElement('summary');
    details.className='delivery-disclosure';
    summary.textContent='Delivery scope · assessment pending';
    scope.before(details);details.append(summary,scope);
    // These retained snapshots contain an Assessment pending placeholder. Keep it
    // inspectable with the delivery boundary instead of duplicating the workspace.
    if(call)details.append(call);
    document.getElementById('outline')?.addEventListener('click',event=>{
      if(event.target.closest('button')?.textContent==='The call')details.open=true;
    },true);
  }
  const payload=JSON.parse(document.getElementById('report-data').textContent);
  const title=()=>{
    const heading=document.querySelector('.page-head h1');
    if(heading?.textContent===payload.run.issuer_name)heading.textContent=payload.report.pathway.title;
  };
  new MutationObserver(title).observe(document.getElementById('view-root'),{childList:true,subtree:true});
  title();
})();
/* Reader text, titles and accessible labels show module names. The inspector keeps exact codes and the original download is untouched. */
(() => {
  const MODULE_NAMES={"CP-0":"Source readiness","CP-1A":"Business & governance","CP-DR":"Research questions","CP-1":"Financial foundation","CP-1B":"Earnings changes","CP-L10":"Financial change screen","CP-1D":"Earnings quality","CP-1C":"Peer benchmark","CP-2D":"Liquidity","CP-3C":"Refinancing & LME","CP-2":"Fundamental credit","CP-2A":"Downside","CP-2G":"Forward credit model","CP-2E":"Rates, FX & hedging","CP-2H":"Ratings & triggers","CP-4":"Legal & covenants","CP-4A":"Covenant capacity","CP-4B":"Structural priority","CP-4D":"Intercreditor control","CP-4C":"Recovery & fulcrum","CP-3":"Security selection","CP-3D":"Market-implied risk","CP-6":"Committee decision","CP-5":"Evidence validation","CP-8":"Deliverable comparison","CP-MODEL":"Published model","CP-OS":"Run activity","CP-MEMO":"Credit memo","CP-PARSE":"Source readiness","CP-2C":"Business & governance","CP-1E":"Earnings quality","CP-2B":"Downside","CP-2F":"Rates, FX & hedging","CP-3A":"Security selection","CP-3B":"Security selection","CP-5A":"Evidence validation","CP-6A":"Committee decision","CP-L20":"Financial change screen","CP-L23":"Financial change screen","CP-L30":"Financial change screen","CP-L40":"Financial change screen"};
  // CP-<x>-GAP-<n> reads "<Name of x> gap <n>"; a code with no known name reads "unnamed module".
  const CODE=/\bCP-([A-Z0-9]+)-GAP-0*(\d+)\b|\bCP-[A-Z0-9]+\b(?![-.][A-Za-z0-9])/g;
  const named=text=>text.replace(CODE,(code,owner,gap)=>owner===undefined?MODULE_NAMES[code]||'unnamed module':`${MODULE_NAMES[`CP-${owner}`]||'unnamed module'} gap ${gap}`);
  function nameCodes(root) {
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),nodes=[];
    while(walker.nextNode())nodes.push(walker.currentNode);
    for(const node of nodes)if(named(node.data)!==node.data)node.data=named(node.data);
    for(const element of root.querySelectorAll('[title],[aria-label]'))for(const attribute of ['title','aria-label']) {
      const value=element.getAttribute(attribute);
      if(value&&named(value)!==value)element.setAttribute(attribute,named(value));
    }
  }
  // The navigator lists a module under the name the workspace uses for it; the report's own title becomes the link's title.
  function nameLinks(root) {
    for(const link of root.querySelectorAll('.module-link')) {
      const name=MODULE_NAMES[(link.getAttribute('href')||'').slice(1)],own=link.querySelector('.title')?.firstChild;
      if(name&&own?.nodeType===Node.TEXT_NODE&&own.data!==name){link.title=own.data;own.data=name;}
    }
  }
  // Only child changes are observed, so rewriting text here cannot trigger another pass. The banners sit outside the view and carry handoff text too.
  for(const root of document.querySelectorAll('.navigator,#view-root,#call-root,.banner')) {
    new MutationObserver(()=>{nameCodes(root);nameLinks(root);}).observe(root,{childList:true,subtree:true});
    nameCodes(root);nameLinks(root);
  }
})();
