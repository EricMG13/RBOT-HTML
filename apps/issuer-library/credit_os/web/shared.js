'use strict';
// Moved from Credit OS actions.js: the page title. The run watcher that set a title prefix is not part of
// the static pages, so the title is the module name alone.
let titleBase='';
function applyTitle(){if(titleBase)document.title=`${titleBase} · Credit OS`;}
