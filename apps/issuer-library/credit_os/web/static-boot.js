'use strict';
// The screens read the workspace store, so they load once it has been built. The data file (data.js)
// sets window.CREDIT_OS_DATA = {catalogue, workspace, activity}; nothing is requested from a server, so the page
// opens from file://. Data that is missing or cannot be read still opens the app with the problem stated.
(async()=>{
  let catalogue={},store={runs:{},outputs:{},inputs:{},pins:{},handoffs:{},reports:[],models:[],visuals:[],issues:[]},problem='',activity={excluded:[],issues:[]};
  try{
    const data=window.CREDIT_OS_DATA;
    if(!data||!data.catalogue||!data.workspace||!data.activity)throw new Error('The data file did not load (window.CREDIT_OS_DATA is not set).');
    catalogue=data.catalogue;store=hydrate(data.workspace);activity=data.activity;
  }catch(error){problem=error.message;console.error('Credit OS data could not be read',error);}
  window.DESIGN_DATA={runs:store.runs,outputs:store.outputs,inputs:store.inputs,pins:store.pins};
  window.DESIGN_WORKSPACE={reports:store.reports,models:store.models,visuals:store.visuals};
  window.DESIGN_CATALOGUE={real:catalogue.real||[],sources:catalogue.sources||{}};
  window.DESIGN_ACTIVITY=activity;
  window.DESIGN_APP={workspace:catalogue.workspace||'',policy_locked:!!catalogue.policy_locked,issues:problem?catalogue.issues||[]:store.issues,problem};
  for(const name of ['calendar.js','views.js','shared.js','screen.js'])await new Promise((resolve,reject)=>{
    const script=document.createElement('script');
    script.src=name;script.onload=resolve;script.onerror=()=>reject(new Error(`${name} did not load`));
    document.head.append(script);
  });
})();
