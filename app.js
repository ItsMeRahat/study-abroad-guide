var $=function(s){return document.querySelector(s)},qa=function(s){return[].slice.call(document.querySelectorAll(s))},DATA_VERSION="20261104d";
var CC=[],CACHE={},D=null,code="se",U={},S=[],R={},META={},CUR="SEK",FX=13,FXN="",MON=0,scope="top",city="all",all=false,done={};
function esc(t){return String(t==null?"":t).replace(/&/g,"&amp;").replace(/</g,"&lt;")}
function lookup(o,p){return p.split(".").reduce(function(a,k){return a&&a[k]},o)}
function fill(){if(!D)return;qa("[data-f]").forEach(function(e){var v=lookup(D.facts,e.dataset.f);if(v==null)return;e.textContent=typeof v=="number"&&!/year/.test(e.dataset.f)?v.toLocaleString("en-US"):v})}
function links(){qa("a[data-u]").forEach(function(a){if(U[a.dataset.u]){a.href=U[a.dataset.u];a.target="_blank";a.rel="noopener"}})}
var LB={ug_entry:"Entry: UG",pg_entry:"Entry: PG",english:"English (UG | PG)",courses:"Courses (UG | PG)",apply:"Application window",fees:"Tuition fees (UG | PG)",funds:"Funds transfer",scholarship:"Scholarships (UG | PG)"};
function sname(u){return u.name.replace(/\s*\(.*?\)/g,"").replace(/^The /,"")}
function plink(u){var L=(D.facts.links)||{};if(u.programmes_url)return u.programmes_url;return(L.programme_search||u.website).replace("{name}",encodeURIComponent(sname(u)))}
function mono(n){var w=sname({name:n.split(",")[0]}).split(/[\s,]+/).filter(function(x){return/^[A-ZÅÄÖØÆ]/.test(x)&&!/^(of|the|in|and|for)$/i.test(x)});return(w.length>1?w[0][0]+w[1][0]:(w[0]||n).slice(0,2)).toUpperCase()}
function cbase(u){return String(u.city||"").replace(/\s*\(.*?\)/g,"").trim()||"Other"}
function card(u){var rows="";
if(u.profile)rows=Object.keys(LB).filter(function(k){return u.profile[k]}).map(function(k){return"<dt>"+LB[k]+"</dt><dd>"+esc(u.profile[k])+"</dd>"}).join("");
rows+="<dt>City</dt><dd>"+esc(u.city||"See website")+"</dd>";
if(u.focus)rows+="<dt>Known for</dt><dd>"+esc(u.focus)+"</dd>";
if(u.admissions_email)rows+='<dt>Admissions email</dt><dd><a href="mailto:'+esc(u.admissions_email.toLowerCase())+'">'+esc(u.admissions_email.toLowerCase())+"</a></dd>";
if(u.phone)rows+='<dt>Phone</dt><dd><a href="tel:'+esc(u.phone.replace(/[^+\d]/g,""))+'">'+esc(u.phone)+"</a></dd>";
var tag=u.top10?'<span class="tag">'+esc(u.rank_label||("Top 10 · #"+u.top10_rank))+"</span>":(u.new?'<span class="tag">New</span>':(u.not_listed?'<span class="tag">Not on official list</span>':""));
var info=u.profile?'<p class="src">'+esc(u.profile_source)+"</p>":'<div class="note">'+esc(META.gen_note)+"</div>";
var mk=u.top10?'<span class="mk top">'+u.top10_rank+"</span>":'<span class="mk">'+esc(mono(u.name))+"</span>";
return'<details><summary>'+mk+'<span class="ti">'+tag+"<b>"+esc(u.name)+"</b><small>"+esc(u.city)+(u.focus?" · "+esc(u.focus):"")+'</small></span><span class="pm" aria-hidden="true"></span></summary><div class="bd"><dl>'+rows+"</dl>"+info+'<div class="acts"><a class="btn" href="'+esc(plink(u))+'" target="_blank" rel="noopener">'+esc(META.prog_btn||"Programmes and fees")+'</a><a class="site" href="'+esc(u.website)+'" target="_blank" rel="noopener">'+esc(u.website.replace(/^https?:\/\/(www\.)?/,"").replace(/\/$/,""))+"</a></div></div></details>"}
function hay(u){return[u.name,u.city,u.focus,u.profile?u.profile.courses:""].join(" ").toLowerCase()}
function pool(){return D.universities.universities.filter(function(u){return scope=="top"?!!u.top10:!u.top10})}
function chips(){var el=$("#chips");if(scope=="top"){el.hidden=true;return}
var m={};pool().forEach(function(u){var c=cbase(u);m[c]=(m[c]||0)+1});
var ks=Object.keys(m).sort(function(a,b){return m[b]-m[a]||a.localeCompare(b,"sv")});
if(city!="all"&&!m[city])city="all";
el.innerHTML='<button data-c="all">All<em>'+pool().length+"</em></button>"+ks.map(function(k){return'<button data-c="'+esc(k)+'">'+esc(k)+"<em>"+m[k]+"</em></button>"}).join("");
el.hidden=false;
qa("#chips button").forEach(function(b){b.onclick=function(){city=b.dataset.c;draw()}})}
function draw(){var q=$("#q").value.trim().toLowerCase(),so=$("#so").value;
chips();
var L=pool().filter(function(u){return(scope=="top"||city=="all"||cbase(u)==city)&&(!q||hay(u).indexOf(q)>-1)});
if(so=="az")L.sort(function(a,b){return a.name.localeCompare(b.name,"sv")});
else if(so=="city")L.sort(function(a,b){return cbase(a).localeCompare(cbase(b),"sv")||a.name.localeCompare(b.name,"sv")});
else if(scope=="top")L.sort(function(a,b){return a.top10_rank-b.top10_rank});
$("#ul").innerHTML=L.length?L.map(card).join(""):'<div class="empty">No universities match your search.</div>';
$("#cnt").textContent=L.length+" of "+pool().length+" shown";
all=false;$("#exp").textContent="Open all";$("#exp").hidden=!L.length;
qa("#chips button").forEach(function(b){b.setAttribute("aria-pressed",b.dataset.c==city)});
links()}
function unisHtml(){return'<h2>'+esc(META.uni_title)+'</h2><div class="stats"><div class="stat"><b id="s1">0</b><span>'+esc(META.top_label)+'</span></div><div class="stat"><b id="s2">0</b><span>Others</span></div><div class="stat"><b id="s3">0</b><span>Total</span></div></div><div class="seg" id="scope"><button aria-pressed="true" data-s="top">'+esc(META.top_label)+'</button><button aria-pressed="false" data-s="rest">Others <span id="nall">0</span></button></div><div class="tools"><input type="search" id="q" placeholder="Search name, city or subject" aria-label="Search universities"><select id="so" aria-label="Sort"><option value="rank">Ranked order</option><option value="az">A to Z</option><option value="city">By city</option></select></div><div class="chips" id="chips" hidden></div><div class="bar2"><span id="cnt"></span><button class="ghost" id="exp">Open all</button></div><div id="ul"></div><div class="note" id="unote"></div>'}
function wireUnis(){var L=D.universities.universities,f=D.facts,nt=L.filter(function(u){return u.top10}).length;
$("#s1").textContent=nt;$("#s2").textContent=L.length-nt;$("#s3").textContent=L.length;$("#nall").textContent=L.length-nt;
scope=nt?"top":"rest";city="all";
$("#scope button").forEach(function(b){b.setAttribute("aria-pressed",b.dataset.s==scope)});
$("#so").value=nt?"rank":"az";
$("#unote").innerHTML=esc(META.list_note||("The official list names "+L.length+" institutions."))+(f.institutions&&f.institutions.stated_on_page&&f.institutions.stated_on_page!=L.length?" (its introduction says "+f.institutions.stated_on_page+")":"")+" "+esc(META.rank_note||"")+' Source: <a href="'+esc(META.portal_url)+'" target="_blank" rel="noopener">'+esc(META.portal)+"</a>.";
qa("#scope button").forEach(function(b){b.onclick=function(){scope=b.dataset.s;city="all";$("#so").value=scope=="top"?"rank":"az";qa("#scope button").forEach(function(x){x.setAttribute("aria-pressed",x==b)});draw()}});
$("#q").oninput=draw;$("#so").onchange=draw;
$("#exp").onclick=function(){all=!all;qa("#ul details").forEach(function(d){d.open=all});this.textContent=all?"Close all":"Open all"};
draw()}
function req(l){$("#req").innerHTML=R[l].map(function(r){return"<dt>"+r[0]+"</dt><dd>"+r[1]+"</dd>"}).join("");qa("#lvl button").forEach(function(b){b.setAttribute("aria-pressed",b.dataset.l==l)})}
function calc(){var el=$("#mo");if(!el)return;var M=D.facts.maintenance||{},per=+(M.monthly||0);if(!per&&M.annual)per=+M.annual/12;var n=Math.max(1,Math.min(48,+el.value||1)),t=n*per;
if(!per){$("#tot").textContent="Cost data not verified";$("#bdt").textContent="BDT estimate unavailable";$("#fxn").textContent="Add an official monthly or annual living-cost figure before using this estimate.";return}
$("#tot").textContent=CUR+" "+t.toLocaleString("en-US");
$("#bdt").textContent="≈ BDT "+Math.round(t*FX).toLocaleString("en-US");
$("#fxn").textContent="Per month ≈ BDT "+Math.round(per*FX).toLocaleString("en-US")+". "+FXN+" This is the mid-market rate; your bank’s rate will differ."}
function liveFx(c){var c1=c,u=["https://open.er-api.com/v6/latest/"+CUR,"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/"+CUR.toLowerCase()+".json"],k=CUR.toLowerCase();
function ok(r){return r&&r>0&&r<10000}
fetch(u[0]).then(function(r){return r.json()}).then(function(j){var r=j.rates&&j.rates.BDT;if(!ok(r))throw 0;return r}).catch(function(){return fetch(u[1]).then(function(r){return r.json()}).then(function(j){var r=j[k]&&j[k].bdt;if(!ok(r))throw 0;return r})}).then(function(r){if(code!=c1)return;FX=r;FXN="Live rate today: 1 "+CUR+" = "+r.toFixed(2)+" BDT.";calc()}).catch(function(){})}
function steps(){var el=$("#st");if(!el)return;
try{done=JSON.parse(localStorage.getItem("steps-"+code)||"{}")}catch(e){done={}}
el.innerHTML=S.map(function(s,i){return'<li><label><input type="checkbox" data-i="'+i+'"'+(done[i]?" checked":"")+'><span>'+s+"</span></label></li>"}).join("");
function prog(){$("#pb").style.width=qa("#st input:checked").length/S.length*100+"%"}
qa("#st input").forEach(function(c){c.onchange=function(){done[c.dataset.i]=c.checked;try{localStorage.setItem("steps-"+code,JSON.stringify(done))}catch(e){}prog()}});prog()}
function wire(){
if($("#lvl")){qa("#lvl button").forEach(function(b){b.onclick=function(){req(b.dataset.l)}});req("ug")}
if($("#tl"))$("#tl").innerHTML=D.facts.dates.rows.map(function(r){return"<li><time>"+esc(r.date)+"</time><span>"+esc(r.event)+"</span></li>"}).join("");
steps();
if($("#mo"))$("#mo").oninput=calc;
fill();links();wireUnis()}
function show(id,push){var P=META.tabs;if(!P.some(function(p){return p[0]==id}))id="overview";
qa("main>section").forEach(function(s){s.classList.toggle("on",s.id==id)});
qa("#tabs button").forEach(function(b){var on=b.dataset.t==id;b.setAttribute("aria-selected",on);if(on&&b.scrollIntoView)b.scrollIntoView({inline:"center",block:"nearest"})});
if(push)try{history.replaceState(null,"","#"+code+"-"+id)}catch(e){location.hash=code+"-"+id}
window.scrollTo(0,0)}
function load(c){if(CACHE[c])return Promise.resolve(CACHE[c]);
if(window.__DATA__&&window.__DATA__.c&&window.__DATA__.c[c]){CACHE[c]=window.__DATA__.c[c];return Promise.resolve(CACHE[c])}
var e=CC.filter(function(x){return x.code==c})[0],dir="data/"+(e.dir?e.dir+"/":"");
return Promise.all(["facts","universities","content"].map(function(n){return fetch(dir+n+".json?v="+DATA_VERSION,{cache:"no-store"}).then(function(r){if(!r.ok)throw 0;return r.json()})})).then(function(a){CACHE[c]={facts:a[0],universities:a[1],content:a[2]};return CACHE[c]})}
function setCountry(c,id){load(c).then(function(d){
code=c;D=d;var C=d.content;META=C.meta;META.tabs=C.tabs;U=C.links;S=C.steps;R=C.req;CUR=META.currency;
try{localStorage.setItem("cc",c)}catch(e){}
$("#cc").value=c;document.title=META.title;
$("#ht").textContent=META.title;$("#hs").textContent=META.sub;
$("#tabs").innerHTML="";META.tabs.forEach(function(p){var b=document.createElement("button");b.textContent=p[1];b.setAttribute("role","tab");b.dataset.t=p[0];b.onclick=function(){show(p[0],1)};$("#tabs").appendChild(b)});
$("#main").innerHTML=META.tabs.map(function(p){var h;if(p[0]=="unis"){h=unisHtml()}else{var body=C.sections[p[0]].html;if(p[0]=="overview"&&d.facts.population!=null){var pop=Number(d.facts.population).toLocaleString("en-US")+(d.facts.population_reference_date?" ("+d.facts.population_reference_date+" estimate)":(d.facts.population_year?" ("+d.facts.population_year+" estimate)":""));body=body.replace(/<dt>Population<\/dt>\s*<dd>[\s\S]*?<\/dd>/i,"<dt>Population</dt><dd>"+esc(pop)+"</dd>")}h="<h2>"+C.sections[p[0]].title+"</h2>"+body}return'<section id="'+p[0]+'">'+h+"</section>"}).join("");
var f=d.facts;MON=f.maintenance.monthly||0;FX=(f.fx&&f.fx[CUR+"_BDT"])||13;FXN=f.fx?"Rate: 1 "+CUR+" = "+FX.toFixed(2)+" BDT (stored "+f.fx.date+", refreshed daily).":"";
$("#caution").innerHTML=META.caution;
$("#dstat").textContent="Data checked "+f.last_checked+" · Confirm with official links";
wire();calc();liveFx(c);show(id||"overview",1)}).catch(function(e){console.error("Country guide load/render error:",e);$("#main").innerHTML='<div class="note warn">This country guide could not be opened. Please reload the page. If the problem continues, contact the site owner.</div>'})}
function boot(cs){CC=cs;$("#cc").innerHTML=CC.map(function(x){return'<option value="'+esc(x.code)+'">'+esc(x.flag+" "+x.name)+"</option>"}).join("");
$("#cc").onchange=function(){setCountry(this.value,"overview")};
var h=location.hash.slice(1).split("-"),c=null,id=null;
if(h.length>1){c=h[0];id=h[1]}else if(h[0]){if(CC.some(function(x){return x.code==h[0]}))c=h[0];else id=h[0]}
if(!c||!CC.some(function(x){return x.code==c})){try{c=localStorage.getItem("cc")}catch(e){}}
if(!c||!CC.some(function(x){return x.code==c}))c=CC[0].code;
setCountry(c,id)}
window.onhashchange=function(){var h=location.hash.slice(1).split("-");if(h.length>1&&h[0]!=code&&CC.some(function(x){return x.code==h[0]}))setCountry(h[0],h[1]);else if(D)show(h[h.length-1])};
document.addEventListener("DOMContentLoaded",function(){
(window.__DATA__&&window.__DATA__.countries?Promise.resolve(window.__DATA__.countries):fetch("data/countries.json?v="+DATA_VERSION,{cache:"no-store"}).then(function(r){return r.json()})).then(boot).catch(function(){$("#main").innerHTML='<div class="note warn">Could not load the data files. Open this page from GitHub Pages, run <code>python -m http.server</code> in the project folder, or use standalone.html.</div>'});
});
