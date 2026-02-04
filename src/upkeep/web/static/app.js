"use strict";(()=>{function pe(){let t=localStorage.getItem("theme")||"system";X(t),window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change",()=>{(localStorage.getItem("theme")||"system")==="system"&&X("system")})}function ge(){let t=localStorage.getItem("theme")||"system",e;t==="light"?e="dark":t==="dark"?e="system":e="light",X(e),localStorage.setItem("theme",e)}function X(t){let e=t;t==="system"&&(e=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"),document.documentElement.setAttribute("data-theme",e);let o=document.getElementById("theme-icon");o&&(t==="light"?o.textContent="\u2600\uFE0F":t==="dark"?o.textContent="\u{1F319}":o.textContent="\u{1F5A5}\uFE0F")}function u(t,e="info",o=3e3){let n=document.createElement("div");n.className=`toast ${e}`,n.textContent=t;let s=document.getElementById("toast-container");if(!s){console.error("Toast container not found");return}s.appendChild(n),setTimeout(()=>n.classList.add("show"),10),setTimeout(()=>{n.classList.remove("show"),setTimeout(()=>n.remove(),300)},o)}var j=!1,q=null,z=null;function fe(t,e,o){let n=document.getElementById("progress-overlay"),s=document.getElementById("progress-title"),r=document.getElementById("progress-percent"),i=document.getElementById("progress-current"),a=document.getElementById("progress-bar");if(!n||!s||!r||!i||!a){console.error("Progress overlay elements not found");return}s.textContent=t,r.textContent="0%",i.textContent="0";let c=document.getElementById("progress-remaining");c&&(c.textContent="--"),a.style.width="0%",n.classList.add("active"),j=!0,q=o,z=Date.now(),document.addEventListener("keydown",ye)}function he(t,e,o=""){if(!j)return;let n=Math.round(t/e*100),s=document.getElementById("progress-percent"),r=document.getElementById("progress-current"),i=document.getElementById("progress-bar"),a=document.getElementById("progress-remaining"),c=document.getElementById("progress-message");if(!s||!r||!i)return;let m=parseInt(s.textContent||"0");if(A(s,m,n,200,0,"%"),r.textContent=String(t),i.style.width=n+"%",t>0&&z&&a){let l=(Date.now()-z)/1e3,d=t/l,p=(e-t)/d;if(p<60)a.textContent=Math.round(p)+"s";else{let f=Math.floor(p/60),T=Math.round(p%60);a.textContent=`${f}m ${T}s`}}o&&c&&(c.textContent=o)}function Z(){let t=document.getElementById("progress-overlay");t&&t.classList.remove("active"),j=!1,q=null,z=null,document.removeEventListener("keydown",ye)}function Xe(){q&&q(),Z(),u("Operation cancelled","warning")}function ye(t){t.key==="Escape"&&j&&Xe()}function A(t,e,o,n=300,s=1,r=""){let i=performance.now(),a=o-e;function c(m){let l=m-i,d=Math.min(l/n,1),g=1-Math.pow(1-d,3),p=e+a*g;t.textContent=p.toFixed(s)+r,d<1&&requestAnimationFrame(c)}requestAnimationFrame(c)}async function ve(){let t=document.getElementById("reload-scripts-btn"),e=document.getElementById("reload-scripts-status");if(!(!t||!e)){t.disabled=!0,t.textContent="\u23F3 Reloading...",e.textContent="Copying updated scripts to system location...",e.style.color="var(--text-secondary)";try{let o=await fetch("/api/system/reload-scripts",{method:"POST",headers:{"Content-Type":"application/json"}});if(!o.ok){let s=await o.json();throw new Error(s.detail||"Failed to reload scripts")}let n=await o.json();t.textContent="\u2713 Reloaded",e.textContent=n.message||"Scripts reloaded successfully. Changes will take effect immediately.",e.style.color="var(--success)",u("Scripts reloaded successfully","success"),setTimeout(()=>{t.disabled=!1,t.textContent="\u{1F504} Reload Scripts",e.textContent=""},3e3)}catch(o){let n=o instanceof Error?o.message:"Unknown error";t.textContent="\u2717 Failed",e.textContent=`Error: ${n}`,e.style.color="var(--danger)",u(`Failed to reload scripts: ${n}`,"error"),setTimeout(()=>{t.disabled=!1,t.textContent="\u{1F504} Reload Scripts"},5e3)}}}function ee(t){document.querySelectorAll(".tab-content").forEach(n=>n.classList.remove("active")),document.querySelectorAll(".tabs button").forEach(n=>n.classList.remove("active"));let e=document.getElementById(t);if(e&&e.classList.add("active"),document.querySelectorAll(".tabs button").forEach(n=>{n.textContent?.toLowerCase().includes(t)&&n.classList.add("active")}),t==="dashboard"){let n=window.loadSystemInfo;n&&n()}else if(t==="maintenance"){let n=window.loadOperations;n&&n()}else if(t==="schedule"){let n=window.onScheduleTabShow;n&&n()}}var $={cpu:null,memory:null,disk:null},Ze=null;async function U(){try{let e=await(await fetch("/api/system/info")).json();e.system&&e.system.username&&(Ze=e.system.username,window._currentUsername=e.system.username);let o=ne(e.cpu.history),n=ne(e.memory.history),s=ne(e.disk.history),r=document.getElementById("system-metrics");if(!r)return;if($.cpu===null)r.innerHTML=`
        <div class="metric-card">
          <h3>CPU Usage</h3>
          <div class="value" id="cpu-value">${e.cpu.percent.toFixed(1)}%</div>
          ${H(o,e.cpu.history)}
          <div class="sparkline-container">
            <canvas id="cpu-sparkline" class="sparkline" width="80" height="24"></canvas>
          </div>
          <div class="subvalue">${e.cpu.count} cores</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${B(e.cpu.percent)}" id="cpu-bar"
                 style="width: ${e.cpu.percent}%"></div>
          </div>
        </div>
        <div class="metric-card">
          <h3>Memory</h3>
          <div class="value" id="memory-value">${e.memory.percent.toFixed(1)}%</div>
          ${H(n,e.memory.history)}
          <div class="sparkline-container">
            <canvas id="memory-sparkline" class="sparkline" width="80" height="24"></canvas>
          </div>
          <div class="subvalue">${e.memory.available_gb.toFixed(1)} GB available</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${B(e.memory.percent)}" id="memory-bar"
                 style="width: ${e.memory.percent}%"></div>
          </div>
        </div>
        <div class="metric-card">
          <h3>Disk Space</h3>
          <div class="value" id="disk-value">${e.disk.percent.toFixed(1)}%</div>
          ${H(s,e.disk.history)}
          <div class="sparkline-container">
            <canvas id="disk-sparkline" class="sparkline" width="80" height="24"></canvas>
          </div>
          <div class="subvalue">${e.disk.free_gb.toFixed(1)} GB free of ${e.disk.total_gb.toFixed(1)} GB</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${B(e.disk.percent)}" id="disk-bar"
                 style="width: ${e.disk.percent}%"></div>
          </div>
        </div>
        ${e.network?`
        <div class="metric-card">
          <h3>Network</h3>
          <div class="value" id="network-value">
            \u2193 ${e.network.download_mbps.toFixed(2)} MB/s
          </div>
          <div class="subvalue" style="margin-top: 0.25rem;">
            \u2191 ${e.network.upload_mbps.toFixed(2)} MB/s
          </div>
          <div class="subvalue" style="font-size: 0.75rem; margin-top: 0.5rem;">
            Total: \u2193${e.network.total_recv_gb} GB / \u2191${e.network.total_sent_gb} GB
          </div>
        </div>
        `:""}
        ${e.swap&&e.swap.total_gb>0?`
        <div class="metric-card">
          <h3>Swap</h3>
          <div class="value" id="swap-value">${e.swap.percent.toFixed(1)}%</div>
          <div class="subvalue">${e.swap.used_gb} GB used of ${e.swap.total_gb} GB</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${B(e.swap.percent)}" id="swap-bar"
                 style="width: ${e.swap.percent}%"></div>
          </div>
          ${e.swap.percent>50?'<div class="warning">\u26A0\uFE0F High swap usage indicates memory pressure</div>':""}
        </div>
        `:""}
      `,console.log("First load - Memory bar HTML rendered"),setTimeout(()=>{let l=document.getElementById("memory-bar");l?console.log("Memory bar found after first load:",{width:l.style.width,className:l.className,computedWidth:window.getComputedStyle(l).width,parent:l.parentElement}):console.error("Memory bar NOT found after first load!")},100);else{let l=document.getElementById("cpu-value"),d=document.getElementById("memory-value"),g=document.getElementById("disk-value");l&&$.cpu!==null&&A(l,$.cpu,e.cpu.percent,300,1,"%"),d&&$.memory!==null&&A(d,$.memory,e.memory.percent,300,1,"%"),g&&$.disk!==null&&A(g,$.disk,e.disk.percent,300,1,"%");let p=document.getElementById("cpu-bar"),f=document.getElementById("memory-bar"),T=document.getElementById("disk-bar");f?console.log(`Memory bar found: width=${e.memory.percent}%, element:`,f):console.error("Memory bar element not found!"),p&&(p.style.width=e.cpu.percent+"%",p.className=`progress-bar-fill ${B(e.cpu.percent)}`),f&&(f.style.width=e.memory.percent+"%",f.className=`progress-bar-fill ${B(e.memory.percent)}`),T&&(T.style.width=e.disk.percent+"%",T.className=`progress-bar-fill ${B(e.disk.percent)}`);let h=document.querySelector(".metric-card:nth-child(1)"),b=document.querySelector(".metric-card:nth-child(2)"),v=document.querySelector(".metric-card:nth-child(3)");if(h){let y=h.querySelector(".trend");y&&y.remove();let x=h.querySelector(".value");x&&x.insertAdjacentHTML("afterend",H(o,e.cpu.history))}if(b){let y=b.querySelector(".trend");y&&y.remove();let x=b.querySelector(".value");x&&x.insertAdjacentHTML("afterend",H(n,e.memory.history))}if(v){let y=v.querySelector(".trend");y&&y.remove();let x=v.querySelector(".value");x&&x.insertAdjacentHTML("afterend",H(s,e.disk.history))}}$.cpu=e.cpu.percent,$.memory=e.memory.percent,$.disk=e.disk.percent,fetch("/api/system/sparkline").then(l=>l.json()).then(l=>{console.log("Sparkline data received:",l),l&&l.cpu&&l.cpu.length>=2?(te("cpu-sparkline",l.cpu,"#ff6961"),te("memory-sparkline",l.memory,"#0a84ff"),te("disk-sparkline",l.disk,"#ff9500")):console.warn("Sparkline data insufficient:",l)}).catch(l=>console.error("Error loading sparkline data:",l));let a=document.getElementById("system-info");a&&(a.innerHTML=`
        <dl class="info-item">
          <dt>Total Memory</dt>
          <dd>${e.memory.total_gb.toFixed(1)} GB</dd>
        </dl>
        <dl class="info-item">
          <dt>Used Memory</dt>
          <dd>${e.memory.used_gb.toFixed(1)} GB</dd>
        </dl>
        <dl class="info-item">
          <dt>Total Disk</dt>
          <dd>${e.disk.total_gb.toFixed(1)} GB</dd>
        </dl>
        <dl class="info-item">
          <dt>Used Disk</dt>
          <dd>${e.disk.used_gb.toFixed(1)} GB</dd>
        </dl>
      `);let c=e.disk.percent>80?`<div class="warning">\u26A0\uFE0F Disk usage is high (${e.disk.percent.toFixed(1)}%). Consider running cleanup operations.</div>`:"",m=e.memory.percent>80?`<div class="warning">\u26A0\uFE0F Memory usage is high (${e.memory.percent.toFixed(1)}%).</div>`:"";await et(c,m)}catch(t){let e=document.getElementById("system-metrics");e&&(e.innerHTML=`<div class="error">Error loading system info: ${t.message}</div>`)}}async function W(){let t=document.getElementById("health-score");if(t)try{let o=await(await fetch("/api/system/health")).json(),n="";o.issues&&o.issues.length>0&&(n=`
        <div class="health-issues" style="margin-top: 1rem; text-align: left;">
          <h4 style="margin-bottom: 0.5rem;">Issues Detected:</h4>
          ${o.issues.map(s=>`
            <div class="warning" style="margin-bottom: 0.5rem;">
              ${s.includes("Critical")?"\u{1F534}":"\u26A0\uFE0F"} ${s}
            </div>
          `).join("")}
        </div>
      `),t.innerHTML=`
      <div class="health-score-value ${o.overall}">
        ${o.score}
      </div>
      <div class="health-status">${o.overall.toUpperCase()}</div>
      ${n}
    `}catch(e){t.innerHTML=`<div class="error">Error loading health score: ${e.message}</div>`}}async function G(){let t=document.getElementById("top-processes");if(t)try{let o=await(await fetch("/api/system/processes?limit=3")).json(),n='<div class="process-section">';n+='<h3 style="font-size: 0.875rem; margin-bottom: 0.5rem; color: var(--text-secondary);">Top CPU Consumers</h3>',n+='<div class="process-list">',o.top_cpu.forEach((s,r)=>{n+=`
        <div class="process-item">
          <div class="process-rank">${r+1}</div>
          <div class="process-name">${s.name}</div>
          <div class="process-value">${s.cpu_percent}%</div>
        </div>
      `}),n+="</div></div>",n+='<div class="process-section" style="margin-top: 1.5rem;">',n+='<h3 style="font-size: 0.875rem; margin-bottom: 0.5rem; color: var(--text-secondary);">Top Memory Consumers</h3>',n+='<div class="process-list">',o.top_memory.forEach((s,r)=>{n+=`
        <div class="process-item">
          <div class="process-rank">${r+1}</div>
          <div class="process-name">${s.name}</div>
          <div class="process-value">${s.memory_mb.toFixed(0)} MB</div>
        </div>
      `}),n+="</div></div>",t.innerHTML=n}catch(e){t.innerHTML=`<div class="error">Error loading processes: ${e.message}</div>`}}async function et(t="",e=""){let o=document.getElementById("maintenance-status");if(o)try{let s=await(await fetch("/api/maintenance/last-run")).json(),r;if(s.status==="never")r="<strong>Never</strong>";else{let i=s.global_last_run||"Unknown",a=s.global_last_run_relative||"";r=`<strong>${i}</strong> <span style="color: var(--text-secondary);">(${a})</span>`}o.innerHTML=`
      <p>Last maintenance run: ${r}</p>
      <p style="margin-top: 0.5rem;">Recommendation: <strong>Run maintenance weekly</strong></p>
      ${t}
      ${e}
      ${!t&&!e?'<div class="success">\u2713 System is running smoothly</div>':""}
    `}catch{o.innerHTML=`
      <p>Last maintenance run: <strong>Never</strong> <span style="color: var(--text-secondary);">(check logs)</span></p>
      <p style="margin-top: 0.5rem;">Recommendation: <strong>Run maintenance weekly</strong></p>
      ${t}
      ${e}
      ${!t&&!e?'<div class="success">\u2713 System is running smoothly</div>':""}
    `}}function te(t,e,o="#0a84ff"){let n=document.getElementById(t);if(!n){console.warn(`Canvas not found: ${t}`);return}if(!e||e.length<2){console.warn(`Insufficient data for ${t}: ${e?e.length:0} points`);return}let s=n.getContext("2d");if(!s)return;let r=n.width,i=n.height;s.clearRect(0,0,r,i);let a=Math.min(...e),m=Math.max(...e)-a||1;s.beginPath(),s.strokeStyle=o,s.lineWidth=1.5,s.lineJoin="round",e.forEach((l,d)=>{let g=d/(e.length-1)*r,p=i-(l-a)/m*i;d===0?s.moveTo(g,p):s.lineTo(g,p)}),s.stroke()}function ne(t){if(!t||t.length<2)return"neutral";let e=t[t.length-1],o=t[t.length-2],n=e-o;return Math.abs(n)<.5?"neutral":n>0?"up":"down"}function H(t,e){if(!e||e.length<2)return"";let o=e[e.length-1],n=e[e.length-2],s=Math.abs(o-n).toFixed(1);return`<span class="trend ${t}">${{up:"\u2191",down:"\u2193",neutral:"\u2022"}[t]} ${s}%</span>`}function B(t){return t>90?"danger":t>75?"warning":""}function O(t){if(t<60)return`${t.toFixed(0)}s`;if(t<3600){let e=Math.floor(t/60),o=Math.round(t%60);return`${e}m ${o}s`}else{let e=Math.floor(t/3600),o=Math.floor(t%3600/60);return`${e}h ${o}m`}}function E(t){let e=document.createElement("div");return e.textContent=t,e.innerHTML}var be="upkeep-operation-times";function oe(){try{let t=localStorage.getItem(be);return t?JSON.parse(t):{}}catch(t){return console.error("Failed to load operation times:",t),{}}}function tt(t){try{localStorage.setItem(be,JSON.stringify(t))}catch(e){console.error("Failed to save operation times:",e)}}function Ee(t,e){let o=oe(),n=o[t]||{runs:[],average:0};n.runs.push(Math.round(e)),n.runs.length>5&&(n.runs=n.runs.slice(-5));let s=n.runs.reduce((r,i)=>r+i,0)/n.runs.length;n.average=Math.round(s*100)/100,o[t]=n,tt(o)}function K(t){let o=oe()[t];return!o||o.runs.length===0?30:o.average}function se(t){let o=oe()[t];if(!o||o.runs.length===0)return null;let n=[...o.runs].sort((i,a)=>i-a),s=Math.floor(n.length/2);if(n.length%2===0){let i=n[s-1],a=n[s];return typeof i!="number"||typeof a!="number"?null:(i+a)/2}let r=n[s];return typeof r=="number"?r:null}function we(t){let e=se(t);if(e===null)return null;if(e<60)return`${Math.round(e)}s`;if(e<3600){let o=Math.floor(e/60),n=Math.round(e%60);return n>0?`${o}m ${n}s`:`${o}m`}else{let o=Math.floor(e/3600),n=Math.round(e%3600/60);return n>0?`${o}h ${n}m`:`${o}h`}}function Te(t,e,o){let n=0;for(let s of t)n+=K(s);if(e){let s=K(e),i=1-Math.max(0,Math.min(1,o));n+=s*i}return Math.round(n)}var re=!1,_=0,F=[],C=0,R=0,M=0,L=0,xe=[],P=null,D=null,S=null,ae=[],$e={};async function Se(){try{let t=Date.now(),o=await(await fetch(`/api/maintenance/operations?_=${t}`)).json();if(!o.operations||o.operations.length===0){let a=document.getElementById("operations-list");a&&(a.innerHTML='<div class="error">No operations available</div>');return}F=o.operations,F.sort((a,c)=>a.category===c.category?a.name.localeCompare(c.name):a.category.localeCompare(c.category));let n={};try{n=(await(await fetch("/api/maintenance/last-run")).json()).operations||{},$e=n}catch(a){console.warn("Could not fetch per-operation history:",a)}J().catch(()=>{});let s=F.map(a=>{let c=n[a.id],m=c?.typical_display||we(a.id),l=m?` | \u23F1\uFE0F Typically <strong>${m}</strong>`:"",d="";if(c&&c.last_run_relative){let p=c.success?"\u2713":"\u2717",f=c.success?"var(--success-color)":"var(--error-color)";d=`<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem;">
          \u{1F4C5} Last run: <strong>${c.last_run_relative}</strong> <span style="color: ${f}">${p}</span>${l}
        </div>`}else d=`<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem;">
          \u{1F4C5} Last run: <strong>Never run</strong>${l||(l||' | \u23F1\uFE0F Typically <strong>\u2014</strong> <span style="opacity:0.7;">(first run)</span>')}
        </div>`;let g="";if(a.why||a.what||a.when_to_run&&a.when_to_run.length>0){let p=Array.isArray(a.when_to_run)&&a.when_to_run.length>0,f=!!a.why?.context,T=Array.isArray(a.why?.problems)&&a.why.problems.length>0,h=Array.isArray(a.what?.outcomes)&&a.what.outcomes.length>0,b=!!a.what?.timeline;if(p||f||T||h||b){let y=p?`
              <div class="operation-when">
                <h5>\u{1F4C5} When to Run This</h5>
                <ul>
                  ${a.when_to_run.map(k=>`<li>${E(String(k))}</li>`).join("")}
                </ul>
              </div>
            `:"",x=f?`<p class="operation-context">${E(String(a.why.context))}</p>`:"",N=T?a.why.problems.map(k=>`<li><strong>${E(String(k.symptom))}</strong><br>${E(String(k.description))}</li>`).join(""):"",Qe=h?a.what.outcomes.map(k=>`<li>${k.type==="positive"?"\u2705":k.type==="warning"?"\u26A0\uFE0F":k.type==="temporary"?"\u23F1\uFE0F":"\u2139\uFE0F"} ${E(String(k.description))}</li>`).join(""):"",Ye=b?`<p class="operation-timeline"><strong>\u23F1\uFE0F How Long:</strong> ${E(String(a.what.timeline))}</p>`:"";g=`
            <details class="operation-details">
              <summary>\u2139\uFE0F Why run this & What to expect</summary>
              <div class="operation-details-content">
                ${y}
                ${x}
                ${T?`<div class="operation-why"><h5>\u{1F50D} Problems This Solves</h5><ul>${N}</ul></div>`:""}
                ${h||b?`<div class="operation-what"><h5>\u2728 What Happens After Running</h5>${h?`<ul>${Qe}</ul>`:""}${Ye}</div>`:""}
              </div>
            </details>
          `}}return`
        <div class="operation-item" data-operation-id="${a.id}">
          <input type="checkbox" id="op-${a.id}" value="${a.id}"
                 ${a.recommended?"checked":""}>
          <div class="operation-info">
            <h4>
              ${a.name}
              ${a.recommended?'<span class="badge recommended">Recommended</span>':'<span class="badge optional">Optional</span>'}
            </h4>
            <p>${a.description}</p>
            ${g}
            ${d}
          </div>
        </div>
      `}).join(""),r=document.getElementById("operations-list");r&&(r.innerHTML=s);let i=F.filter(a=>a.recommended).length;u(`Loaded ${F.length} operations (${i} recommended)`,"success",2e3);try{let c=await(await fetch("/api/maintenance/last-run")).json();if(document.querySelectorAll(".info-banner").forEach(l=>l.remove()),c.success&&c.status==="completed"){let l=document.createElement("div");l.className="info-banner",l.style.cssText="padding: 0.75rem; background: var(--success-bg); color: var(--success-color); border-radius: 6px; margin-bottom: 1rem; font-size: 0.875rem;";let d=c.global_last_run_relative||"Recently";l.innerHTML=`\u{1F4C5} Last maintenance run: <strong>${d}</strong>`,r?.insertAdjacentElement("beforebegin",l)}else if(c.status==="never"){let l=document.createElement("div");l.className="info-banner",l.style.cssText="padding: 0.75rem; background: var(--warning-bg); color: var(--warning-color); border-radius: 6px; margin-bottom: 1rem; font-size: 0.875rem;",l.innerHTML="\u2139\uFE0F Maintenance has never been run",r?.insertAdjacentElement("beforebegin",l)}}catch(a){console.warn("Could not fetch last run info:",a)}}catch(t){console.error("Error loading operations:",t);let e=document.getElementById("operations-list");e&&(e.innerHTML=`<div class="error">Error loading operations: ${t.message}</div>`),u("Failed to load operations","error")}}function ke(){let t=document.querySelectorAll('#operations-list input[type="checkbox"]');t.forEach(e=>e.checked=!0),u(`Selected all ${t.length} operations`,"info",2e3)}function Ie(){document.querySelectorAll('#operations-list input[type="checkbox"]').forEach(e=>e.checked=!1),u("Deselected all operations","info",2e3)}function Me(t){if(console.log("Applying template:",t),document.querySelectorAll('#operations-list input[type="checkbox"]').forEach(o=>o.checked=!1),t.operations&&t.operations.length>0){let o=0;t.operations.forEach(n=>{let s=document.getElementById(`op-${n}`);s?(s.checked=!0,o++):console.warn(`Operation not found: ${n}`)}),u(`Applied "${t.name}" - ${o} operations selected`,"success",3e3)}else u(`Applied "${t.name}"`,"info",2e3)}async function Be(){console.log("=== runSelectedOperations CALLED ===");let t=document.querySelectorAll('#operations-list input[type="checkbox"]:checked');console.log("Found checked checkboxes:",t.length);let e=Array.from(t).map(l=>l.value);if(console.log("Selected operations:",e),ae=e,e.length===0){console.log("No operations selected"),alert("No operations selected");return}_++;let o=_;console.log("Operation invocation ID:",o),re=!0;let n=document.getElementById("run-btn");n&&(n.disabled=!0);let s=document.getElementById("select-all-btn"),r=document.getElementById("deselect-all-btn");s&&(s.disabled=!0,s.setAttribute("aria-disabled","true"),s.title="Selection locked while operations are running"),r&&(r.disabled=!0,r.setAttribute("aria-disabled","true"),r.title="Selection locked while operations are running");let i=document.getElementById("skip-btn"),a=document.getElementById("cancel-btn");i&&(i.style.display="inline-block"),a&&(a.style.display="inline-block"),console.log("Showing Skip/Cancel buttons for invocation",o);let c=document.getElementById("progress-container");c&&(c.style.display="block"),M=0,L=e.length,xe=[],R=Date.now(),ie(),st(),rt();let m=document.getElementById("progress-text");m&&(m.style.display="block",m.textContent=`Connecting to server...
`,m.scrollIntoView({behavior:"smooth",block:"nearest"}));try{let l=await fetch("/api/maintenance/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({operation_ids:e})});if(!l.ok){let f=await l.json();throw new Error(f.detail||"Failed to start operations")}let d=l.body?.getReader();if(!d)throw new Error("Failed to get response reader");let g=new TextDecoder,p="";for(;;){let{done:f,value:T}=await d.read();if(f)break;p+=g.decode(T,{stream:!0});let h=p.split(`
`);p=h.pop()||"";for(let b of h)if(b.startsWith("data: ")){let v=b.slice(6);try{let y=JSON.parse(v);nt(y)}catch(y){console.error("Error parsing SSE data:",y)}}}}catch(l){m&&(m.textContent+=`

Error: ${l.message}
`),console.error("Error running operations:",l)}finally{o===_?(console.log("Cleaning up invocation",o,"(current)"),n&&(n.disabled=!1),i&&(i.style.display="none"),a&&(a.style.display="none"),re=!1,He(),_e(),R=0,c&&(c.style.display="none"),s&&(s.disabled=!1,s.removeAttribute("aria-disabled"),s.title=""),r&&(r.disabled=!1,r.removeAttribute("aria-disabled"),r.title="")):console.log("Skipping cleanup for invocation",o,"(superseded by",_,")")}}async function Le(){if(confirm("Skip the current operation?"))try{let t=await fetch("/api/maintenance/skip",{method:"POST"});if(!t.ok)throw new Error(`HTTP ${t.status}`);let e=await t.json(),o=document.getElementById("progress-text");if(o){let n=e.message||"Skipped by user";o.textContent+=`

\u23ED\uFE0F ${n}
`}u("Operation skipped","info",2e3)}catch(t){console.error("Error skipping operation:",t),alert("Error skipping operation: "+t.message)}}async function Ce(){if(confirm("Cancel all running operations?"))try{let e=await(await fetch("/api/maintenance/cancel",{method:"POST"})).json(),o=document.getElementById("progress-text");o&&(o.textContent+=`

\u26A0\uFE0F ${e.message}
`),_++,re=!1;let n=document.getElementById("run-btn"),s=document.getElementById("skip-btn"),r=document.getElementById("cancel-btn");n&&(n.disabled=!1),s&&(s.style.display="none"),r&&(r.style.display="none"),He(),_e(),R=0;let i=document.getElementById("progress-container");i&&(i.style.display="none");let a=document.getElementById("select-all-btn"),c=document.getElementById("deselect-all-btn");a&&(a.disabled=!1,a.removeAttribute("aria-disabled"),a.title=""),c&&(c.disabled=!1,c.removeAttribute("aria-disabled"),c.title=""),console.log("Operations cancelled, incremented invocation ID to",_)}catch(t){console.error("Error cancelling operations:",t),alert("Error cancelling operations: "+t.message)}}function nt(t){let e=document.getElementById("progress-text");if(e){switch(t.type){case"start":e.textContent+=`
${t.message}
`,e.textContent+=`${"=".repeat(60)}

`;let o=document.getElementById("inline-progress-actions");o&&(o.style.display="none",o.innerHTML=""),setTimeout(()=>{window.scrollTo({top:document.body.scrollHeight,behavior:"smooth"})},50);break;case"operation_start":e.textContent+=`
[${t.progress}] Starting: ${t.operation_name}
`,e.textContent+=`${"-".repeat(60)}
`,C=Date.now(),S=t.operation_id||null,M++,ie();break;case"output":e.textContent+=`${t.line}
`,e.scrollTop=e.scrollHeight;break;case"operation_complete":let n=t.success?"\u2713 Success":"\u2717 Failed";if(e.textContent+=`
${n} (exit code: ${t.returncode})
`,C>0&&S){let r=Date.now()-C,i=r/1e3;t.success&&Ee(S,i),xe.push(r),ie()}S=null;break;case"operation_skipped":e.textContent+=`
\u23ED\uFE0F  Skipped by user
`;break;case"operation_error":e.textContent+=`
Error: ${t.message}
`;break;case"summary":e.textContent+=`
${"=".repeat(60)}
`,e.textContent+=`
Summary:
`,e.textContent+=`  Total operations: ${t.total}
`,e.textContent+=`  Successful: ${t.successful}
`,e.textContent+=`  Failed: ${t.failed}
`;break;case"complete":e.textContent+=`
${t.message}
`,e.textContent+=`${"=".repeat(60)}
`,at();let s=document.getElementById("inline-progress-actions");if(s){s.innerHTML="",s.style.display="flex";let r=document.createElement("button");r.className="primary",r.id="copy-output-btn",r.innerHTML="\u{1F4CB} Copy Output to Clipboard",r.onclick=()=>le(),s.appendChild(r),setTimeout(()=>{r.scrollIntoView({behavior:"smooth",block:"nearest"})},100)}break;case"cancelled":e.textContent+=`
${t.message}
`;break;case"error":e.textContent+=`
Error: ${t.message}
`;break}e.scrollTop=e.scrollHeight}}async function le(){let t=document.getElementById("progress-text"),e=document.getElementById("copy-output-btn");if(!(!t||!e))try{await navigator.clipboard.writeText(t.textContent||"");let o=e.innerHTML;e.innerHTML="\u2713 Copied to Clipboard!",e.className="primary success-flash",setTimeout(()=>{e.innerHTML=o,e.className="primary"},2e3)}catch(o){console.error("Failed to copy to clipboard:",o);let n=e.innerHTML;e.innerHTML="\u2717 Copy Failed",e.className="danger",setTimeout(()=>{e.innerHTML=n,e.className="primary"},2e3)}}function ot(){if(R>0){let t=Date.now()-R,e=document.getElementById("total-elapsed");e&&(e.textContent=O(t/1e3))}}function st(){P&&clearInterval(P),P=window.setInterval(()=>{if(C>0){let t=Date.now()-C,e=document.getElementById("current-op-timer");if(e){let o=O(t/1e3);if(S){let n=$e?.[S]?.typical_seconds,s=typeof n=="number"?n:se(S);if(s!==null&&typeof s=="number"&&!Number.isNaN(s)){let r=O(s);e.textContent=`${o} / Typically ${r}`,e.setAttribute("title","Typical runtime (median of recent runs)")}else e.textContent=`${o} / Typically \u2014`,e.setAttribute("title","No historical runtime yet (first run)")}else e.textContent=o}}ot()},1e3)}function He(){P&&(clearInterval(P),P=null)}function ie(){let t=L>0?Math.round(M/L*100):0;console.log("updateProgress:",{currentOperationIndex:M,totalOperations:L,percent:t});let e=document.getElementById("maintenance-progress-bar"),o=document.getElementById("maintenance-progress-percent");e?(e.style.width=t+"%",console.log("Set maintenance-progress-bar width to:",t+"%")):console.error("maintenance-progress-bar element not found!"),o?(o.textContent=t+"%",console.log("Set maintenance-progress-percent text to:",t+"%")):console.error("maintenance-progress-percent element not found!");let n=document.getElementById("progress-label");n&&(n.textContent=`Operation ${M} of ${L}`);let s=document.getElementById("ops-progress");s&&(s.textContent=`${M}/${L}`);let r=document.getElementById("est-remaining");if(r)if(M>=L)r.textContent="Complete";else if(ae.length>0){let i=ae.slice(M),a=S&&C>0?Math.min((Date.now()-C)/(K(S)*1e3),.99):0,c=Te(i,S,a);r.textContent=O(c)}else r.textContent="Calculating..."}function rt(){D&&clearInterval(D),D=window.setInterval(async()=>{try{let e=await(await fetch("/api/maintenance/queue")).json(),o=document.getElementById("queue-status");if(e.queued_count>0){o&&(o.style.display="flex");let n=document.getElementById("queue-count");n&&(n.textContent=String(e.queued_count))}else o&&(o.style.display="none");e.current_operation&&console.log("Current operation:",e.current_operation)}catch(t){console.error("Error polling queue status:",t)}},2e3)}function _e(){D&&(clearInterval(D),D=null)}async function at(){try{let e=await(await fetch("/api/maintenance/last-run")).json();if(document.querySelectorAll(".info-banner").forEach(n=>{e.global_last_run_relative&&(n.innerHTML=`\u{1F4C5} Last maintenance run: <strong>${e.global_last_run_relative}</strong>`,n.style.background="var(--success-bg)",n.style.color="var(--success-color)")}),e.operations)for(let[n,s]of Object.entries(e.operations)){let r=document.querySelector(`[data-operation-id="${n}"]`);if(r){let i=r.querySelector(".operation-info > div:last-child");if(i&&s.last_run_relative){let a=s.success?"\u2713":"\u2717",c=s.success?"var(--success-color)":"var(--error-color)",m=s.typical_display||"",l=m?` | \u23F1\uFE0F Typically <strong>${m}</strong>`:"";i.innerHTML=`
              \u{1F4C5} Last run: <strong>${s.last_run_relative}</strong> <span style="color: ${c}">${a}</span>${l}
            `}}}}catch(t){console.error("Error refreshing timestamp:",t)}}var it={quick:["browser-cache","trim-caches"],weekly:["brew-update","mas-update","disk-verify","browser-cache","trim-caches","trim-logs","spotlight-status"],full:["brew-update","mas-update","disk-verify","browser-cache","dev-cache","trim-caches","trim-logs","smart-check","spotlight-status","dns-flush"]};function Pe(){let t=document.getElementById("wizard-modal");t&&t.classList.add("active")}function V(){let t=document.getElementById("wizard-modal");t&&t.classList.remove("active")}async function De(t){if(V(),t==="custom"){u("Select operations below","info",2e3);return}let e=it[t]||[];document.querySelectorAll('#operations-list input[type="checkbox"]').forEach(r=>{let i=r;i.checked=e.includes(i.value)}),u(`\u2728 Selected: ${{quick:"Quick Clean",weekly:"Weekly Routine",full:"Full Checkup"}[t]} (${e.length} operations)`,"success",3e3);let n=document.getElementById("operations-list");n&&n.scrollIntoView({behavior:"smooth"});let s=document.getElementById("wizard-prompt");s&&(s.style.display="none")}function lt(t){let e=t;if(!e)return!1;let o=(e.tagName||"").toLowerCase();return o==="input"||o==="textarea"||o==="select"||e.isContentEditable}async function J(){let t=document.getElementById("doctor-panel"),e=document.getElementById("doctor-results");if(!(!t||!e))try{let n=await(await fetch("/api/maintenance/doctor")).json();if(!n.success){t.style.display="block",e.innerHTML='<div style="color: var(--danger);">Doctor check failed.</div>';return}let s=n.issues||[];if(s.length===0){t.style.display="none",e.innerHTML="";return}t.style.display="block";let r=s.map(i=>{let a=i.severity==="error"?"var(--danger)":i.severity==="warning"?"var(--warning)":"var(--text-secondary)",c=Array.isArray(i.affects_operations)&&i.affects_operations.length?`<div style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.25rem;">Affects: ${i.affects_operations.join(", ")}</div>`:"",m=i.fix_action?`<button class="secondary" style="white-space: nowrap;" onclick="fixDoctorIssue('${i.fix_action}')">${i.fix_label||"Fix"}</button>`:"";return`
        <div style="display:flex; justify-content: space-between; gap: 1rem; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 10px; background: var(--bg-secondary);">
          <div>
            <div style="font-weight: 600; color: ${a};">${E(i.title||"Issue")}</div>
            <div style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 0.15rem;">${E(i.detail||"")}</div>
            ${c}
          </div>
          <div style="display:flex; align-items:center; gap: 0.5rem;">
            ${m}
          </div>
        </div>
      `}).join("");e.innerHTML=`<div style="display:grid; gap: 0.75rem;">${r}</div>`}catch{t.style.display="block",e.innerHTML='<div style="color: var(--danger);">Doctor check failed.</div>'}}async function Ae(t){try{let e=await fetch("/api/maintenance/doctor/fix",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:t})}),o=await e.json();if(!e.ok||!o.success)throw new Error(o.detail||o.error||"Failed");u(o.message||"Fix started","success",4e3),setTimeout(()=>J().catch(()=>{}),1500)}catch(e){u(e?.message||"Fix failed","error",5e3)}}function ce(){let t=document.getElementById("shortcuts-modal");t&&t.classList.remove("active")}function ct(){let t=document.getElementById("shortcuts-modal");t&&t.classList.add("active")}function Oe(){document.addEventListener("keydown",t=>{if(!lt(t.target)){if(t.key==="?"||t.key==="/"&&t.shiftKey){t.preventDefault(),ct();return}if(t.key==="/"&&!t.metaKey&&!t.ctrlKey&&!t.altKey){let e=document.getElementById("operation-search");e&&(t.preventDefault(),e.focus());return}if(t.key==="Escape"){ce(),V();let e=window.closeScheduleModal;e&&e()}}})}var w=new Set;async function de(){let e=document.getElementById("path-input")?.value||"/Users",o=document.getElementById("storage-results"),n=document.getElementById("analyze-btn-text");if(!(!o||!n)){o.innerHTML='<div class="loading"><div class="spinner"></div> Analyzing storage...</div>',n.innerHTML='<div class="spinner"></div>',w.clear(),Re(e);try{let s=await fetch(`/api/storage/analyze?path=${encodeURIComponent(e)}`);if(!s.ok){let d=`Server error: ${s.status}`;try{d=(await s.json()).detail||d}catch{}n.textContent="Analyze",o.innerHTML=`<div class="error">${d}</div>`,u(d,"error");return}let r=await s.json();if(n.textContent="Analyze",!r.success){let d=r.error||"Unknown error occurred";o.innerHTML=`<div class="error">${d}</div>`,u(d,"error");return}u(`Analyzed: ${r.file_count} files, ${r.total_size_gb.toFixed(2)} GB`,"success"),o.innerHTML=`
      <h3 style="margin-top: 2rem;">Results for ${r.root_path}</h3>
      <div class="metric-grid" style="margin-top: 1rem;">
        <div class="metric-card">
          <h3>Total Size</h3>
          <div class="value">${r.total_size_gb.toFixed(2)} GB</div>
        </div>
        <div class="metric-card">
          <h3>Files</h3>
          <div class="value">${r.file_count.toLocaleString()}</div>
        </div>
        <div class="metric-card">
          <h3>Directories</h3>
          <div class="value">${r.dir_count.toLocaleString()}</div>
        </div>
      </div>
      <h3 style="margin-top: 2rem;">Largest Items</h3>
      <p style="color: #6e6e73; margin-top: 0.5rem;">Select items to delete</p>
      <div class="file-list">
        ${r.largest_entries.map((d,g)=>{let p=d.path.split("/").pop();return`
          <div class="file-item">
            <input type="checkbox" id="file-${g}" data-path="${d.path.replace(/"/g,"&quot;").replace(/'/g,"&#39;")}">
            <div class="file-info">
              <strong>${p}</strong><br>
              <small style="color: #6e6e73;">${d.path}</small>
            </div>
            <div class="file-size">
              <strong>${d.size_gb.toFixed(2)} GB</strong><br>
              <small style="color: #6e6e73;">${d.is_dir?"Directory":"File"}</small>
            </div>
          </div>
        `}).join("")}
      </div>
      <div class="button-group">
        <button class="primary" id="trash-btn">
          \u{1F5D1}\uFE0F Move to Trash (<span id="selected-count">0</span>)
        </button>
        <button class="danger" id="permanent-delete-btn">
          \u26A0\uFE0F Permanently Delete (<span id="selected-count-permanent">0</span>)
        </button>
        <button class="secondary" id="select-all-btn">Select All</button>
        <button class="secondary" id="deselect-all-btn">Deselect All</button>
      </div>
    `,console.log("=== ATTACHING EVENT LISTENERS ===");let i=document.getElementById("trash-btn"),a=document.getElementById("permanent-delete-btn"),c=document.getElementById("select-all-btn"),m=document.getElementById("deselect-all-btn");console.log("Trash button found:",i),console.log("Permanent button found:",a),i&&(i.addEventListener("click",()=>{console.log("TRASH BUTTON CLICKED!"),Fe("trash")}),console.log("\u2713 Trash button listener attached")),a&&(a.addEventListener("click",()=>{console.log("PERMANENT DELETE BUTTON CLICKED!"),Fe("permanent")}),console.log("\u2713 Permanent button listener attached")),c&&(c.addEventListener("click",ut),console.log("\u2713 Select all button listener attached")),m&&(m.addEventListener("click",mt),console.log("\u2713 Deselect all button listener attached"));let l=document.querySelectorAll('#storage-results input[type="checkbox"]');console.log("Found checkboxes:",l.length),l.forEach((d,g)=>{d.addEventListener("change",()=>{console.log(`Checkbox ${g} changed, path:`,d.dataset.path),d.dataset.path&&dt(d.dataset.path)})}),console.log("\u2713 All checkbox listeners attached")}catch(s){let r=s.message||"Failed to analyze storage";o.innerHTML=`<div class="error">Error: ${r}</div>`,n.textContent="Analyze",u(r,"error")}}}function dt(t){console.log("toggleFileSelection called with:",t),console.log("selectedFiles before:",Array.from(w)),w.has(t)?(w.delete(t),console.log("Removed path")):(w.add(t),console.log("Added path")),console.log("selectedFiles after:",Array.from(w)),Q()}function Q(){let t=w.size,e=document.getElementById("selected-count"),o=document.getElementById("selected-count-permanent");e&&(e.textContent=String(t)),o&&(o.textContent=String(t))}function ut(){document.querySelectorAll('#storage-results input[type="checkbox"]').forEach(e=>{e.checked=!0,e.dataset.path&&w.add(e.dataset.path)}),Q()}function mt(){document.querySelectorAll('#storage-results input[type="checkbox"]').forEach(e=>{e.checked=!1}),w.clear(),Q()}async function Fe(t="trash"){if(console.log("=== deleteSelected CALLED ==="),console.log("Mode:",t),console.log("selectedFiles.size:",w.size),console.log("selectedFiles contents:",Array.from(w)),w.size===0){console.log("No files selected, showing toast"),u("No files selected","warning");return}let e;t==="permanent"?e=`\u26A0\uFE0F PERMANENTLY DELETE ${w.size} item(s)?

This CANNOT be undone! Files will be deleted forever.

Consider using "Move to Trash" instead (recoverable).`:e=`Move ${w.size} item(s) to Trash?

You can recover them from macOS Trash if needed.`,console.log("Showing confirmation dialog");let o=confirm(e);if(console.log("User confirmed:",o),!o){console.log("User cancelled");return}console.log("Proceeding with delete...");let n=w.size,s=0,r=0,i=[],a=!1,c=document.getElementById("trash-btn"),m=document.getElementById("permanent-delete-btn");c&&(c.disabled=!0),m&&(m.disabled=!0),fe(t==="permanent"?"\u26A0\uFE0F Permanently Deleting Files...":"\u{1F5D1}\uFE0F Moving Files to Trash...",n,()=>{a=!0});let d=0;for(let f of w){if(a)break;d++;let T=f.split("/").pop();he(d,n,`Processing: ${T}`);try{let h=await fetch(`/api/storage/delete?path=${encodeURIComponent(f)}&mode=${t}`,{method:"DELETE"});if(!h.ok){let v=await h.json().catch(()=>({detail:"Unknown error"}));throw new Error(v.detail||`HTTP ${h.status}`)}let b=await h.json();b.success?s++:(r++,i.push({path:f,error:b.error||"Unknown error"}),console.error(`Failed to ${t==="permanent"?"delete":"move to trash"} ${f}:`,b.error))}catch(h){r++,i.push({path:f,error:h.message}),console.error(`Error processing ${f}:`,h)}}Z(),c&&(c.disabled=!1),m&&(m.disabled=!1),w.clear(),Q();let g=t==="permanent"?"deleted":"moved to Trash",p=t==="permanent"?"delete":"move";a?u(`\u26A0\uFE0F Operation cancelled. Processed ${s+r}/${n} items.`,"warning",4e3):s>0&&r===0?(u(`\u2705 Successfully ${g} ${s} item(s)`,"success",4e3),t==="trash"&&u("\u{1F4A1} Tip: You can recover files from macOS Trash","info",3e3)):s>0&&r>0?(u(`\u26A0\uFE0F ${g.charAt(0).toUpperCase()+g.slice(1)} ${s}, failed to ${p} ${r} item(s)`,"warning",6e3),console.error("Failed operations:",i)):(u(`\u274C Failed to ${p} all ${r} item(s)`,"error",6e3),console.error("Failed operations:",i)),u("Refreshing view...","info",2e3),await de()}function Re(t){let e=document.getElementById("breadcrumbs");if(!e)return;let o=t.split("/").filter(r=>r);if(o.length===0){e.innerHTML=`<span class="breadcrumb" onclick="setPath('/')">Root</span>`;return}let n=`<span class="breadcrumb" onclick="setPath('/')">\u{1F3E0} Root</span>`,s="";o.forEach((r,i)=>{s+="/"+r;let a=s;n+=' <span class="breadcrumb-separator">/</span> ',n+=`<span class="breadcrumb" onclick="setPath('${a}')">${r}</span>`}),e.innerHTML=n}function pt(t){let e=document.getElementById("path-input");e&&(e.value=t,Re(t),u(`Path set to: ${t}`,"info",2e3))}function Ne(t){pt(t)}function qe(){return window._currentUsername||"username"}async function gt(){try{console.log("Loading schedule templates...");let t=await fetch("/api/schedules/templates");if(!t.ok)throw new Error(`HTTP ${t.status}: ${t.statusText}`);let e=await t.json();console.log("Templates loaded:",e);let o=document.getElementById("templates-list");if(!o)return;if(!e.templates||e.templates.length===0){o.innerHTML='<p style="color: var(--text-secondary);">No templates available</p>';return}o.innerHTML=e.templates.map(n=>{let s=JSON.stringify(n).replace(/'/g,"\\'");return`
        <div class="template-card ${n.recommended?"recommended":""}"
             onclick='applyScheduleTemplate(${s})'>
          <div class="template-icon">${n.icon}</div>
          <div class="template-name">${E(n.name)}</div>
          <div class="template-desc">${E(n.description)}</div>
          ${n.recommended?'<span class="template-badge">RECOMMENDED</span>':""}
        </div>
      `}).join("")}catch(t){console.error("Failed to load templates:",t);let e=document.getElementById("templates-list");e&&(e.innerHTML=`<p style="color: var(--danger);">Error loading templates: ${t.message}</p>`),u("Failed to load templates: "+t.message,"error")}}async function I(){try{let e=await(await fetch("/api/schedules")).json(),o=document.getElementById("schedules-list");if(!o)return;if(!e.success||!e.schedules||e.schedules.length===0){o.innerHTML=`
        <div style="text-align: center; padding: 3rem; color: var(--text-secondary);">
          <div style="font-size: 3rem; margin-bottom: 1rem;">\u{1F4C5}</div>
          <p>No schedules yet</p>
          <p style="font-size: 0.875rem;">Click "New Schedule" or use a template to get started</p>
        </div>
      `;return}o.innerHTML=e.schedules.map(n=>{let s=n.next_run?ze(n.next_run):"Not scheduled",r=n.last_run?ze(n.last_run):"Never",i=n.enabled?"enabled":"disabled",a=n.enabled?"\u25CF Enabled":"\u25CB Disabled";return`
        <div class="schedule-card ${n.enabled?"":"disabled"}">
          <div class="schedule-header">
            <div>
              <div class="schedule-title">${E(n.name)}</div>
              ${n.description?`<div class="schedule-desc">${E(n.description)}</div>`:""}
            </div>
            <div class="schedule-actions">
              <button class="secondary" onclick="openScheduleModal('${n.id}')" title="Edit">
                \u270F\uFE0F
              </button>
              <button class="secondary" onclick="toggleScheduleEnabled('${n.id}', ${!n.enabled})"
                      title="${n.enabled?"Disable":"Enable"}">
                ${n.enabled?"\u23F8\uFE0F":"\u25B6\uFE0F"}
              </button>
              <button class="warning" onclick="runScheduleNow('${n.id}')" title="Run now">
                \u25B6\uFE0F Run
              </button>
              <button class="danger" onclick="deleteSchedule('${n.id}')" title="Delete schedule">
                \u{1F5D1}\uFE0F Delete
              </button>
            </div>
          </div>
          <div class="schedule-info">
            <div class="schedule-info-item">
              <div class="schedule-info-label">Status</div>
              <div class="schedule-info-value">
                <span class="schedule-status ${i}">${a}</span>
              </div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Frequency</div>
              <div class="schedule-info-value">${yt(n)}</div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Time</div>
              <div class="schedule-info-value">${n.time_of_day}</div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Next Run</div>
              <div class="schedule-info-value">
                <span class="next-run-badge">\u23F0 ${s}</span>
              </div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Last Run</div>
              <div class="schedule-info-value">${r}</div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Operations</div>
              <div class="schedule-info-value">${n.operations?.length??n.operation_ids?.length??0} selected</div>
            </div>
          </div>
          ${n.message?`
            <div class="conflict-warning">
              <div class="conflict-warning-text">\u26A0\uFE0F ${E(n.message)}</div>
            </div>
          `:""}
        </div>
      `}).join("")}catch(t){console.error("Failed to load schedules:",t),u("Failed to load schedules","error")}}async function je(){let e=document.getElementById("schedule-id")?.value||"",n=document.getElementById("schedule-name")?.value||"",r=document.getElementById("schedule-description")?.value||"",a=document.getElementById("schedule-frequency")?.value||"",m=document.getElementById("schedule-time")?.value||"",d=document.getElementById("schedule-enabled")?.checked||!1,p=document.getElementById("schedule-notify")?.checked??!0,T=document.getElementById("schedule-wake")?.checked??!1,h=Array.from(document.querySelectorAll('input[name="operations"]:checked')).map(v=>v.value);if(!n||h.length===0||!m){u("Please fill in all required fields","error");return}let b={name:n,description:r,operations:h,frequency:a,time_of_day:m+":00",enabled:d,notify:p,wake_mac:T};if(a==="weekly"){let v=Array.from(document.querySelectorAll('input[name="days"]:checked')).map(y=>y.value);if(v.length===0){u("Please select at least one day of the week","error");return}b.days_of_week=v}else if(a==="monthly"){let v=document.getElementById("schedule-day"),y=parseInt(v?.value||"0");if(!y||y<1||y>28){u("Please enter a day between 1 and 28","error");return}b.day_of_month=y}try{let v=e?`/api/schedules/${e}`:"/api/schedules",x=await fetch(v,{method:e?"PUT":"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}),N=await x.json();if(!x.ok||!N.success)throw new Error(N.error||"Failed to save schedule");u(e?"Schedule updated!":"Schedule created!","success"),Y(),I()}catch(v){console.error("Failed to save schedule:",v),u(v.message,"error")}}async function Ue(t){if(confirm("Delete this schedule? This will unregister it from launchd."))try{let e=await fetch(`/api/schedules/${t}`,{method:"DELETE"}),o=await e.json();if(!e.ok||!o.success)throw new Error(o.error||"Failed to delete schedule");u("Schedule deleted","success"),I()}catch(e){console.error("Failed to delete schedule:",e),u(e.message,"error")}}async function We(t,e){try{let o=await fetch(`/api/schedules/${t}/enabled`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({enabled:e})}),n=await o.json();if(!o.ok||!n.success)throw new Error(n.error||"Failed to toggle schedule");u(e?"Schedule enabled":"Schedule disabled","success"),I()}catch(o){console.error("Failed to toggle schedule:",o),u(o.message,"error")}}async function Ge(t){if(confirm("Run this schedule now? This will execute all operations immediately."))try{let e=await fetch(`/api/schedules/${t}/run-now`,{method:"POST"}),o=await e.json();if(!e.ok||!o.success)throw new Error(o.message||"Failed to run schedule");u("Schedule running...","success"),setTimeout(()=>I(),2e3),setTimeout(()=>I(),7e3)}catch(e){console.error("Failed to run schedule:",e),u(e.message,"error")}}function me(t=null){let e=document.getElementById("schedule-modal"),o=document.getElementById("schedule-modal-title"),n=document.getElementById("schedule-form");if(!e||!o)return Promise.resolve();n&&n.reset();let s=document.getElementById("schedule-id");return s&&(s.value=t||""),o.textContent=t?"Edit Schedule":"Create Schedule",ft(),t?ht(t):(e.classList.add("active"),Promise.resolve())}function Y(){let t=document.getElementById("schedule-modal");t&&t.classList.remove("active")}async function ft(){try{let e=await(await fetch("/api/maintenance/operations")).json(),o=document.getElementById("schedule-operations");if(!o)return;o.innerHTML=e.operations.map(n=>`
      <label class="operation-checkbox">
        <input type="checkbox" name="operations" value="${n.id}">
        <div class="operation-checkbox-label">
          <div class="operation-checkbox-name">${E(n.name)}</div>
          <div class="operation-checkbox-desc">${E(n.description||"")}</div>
        </div>
      </label>
    `).join("")}catch(t){console.error("Failed to load operations:",t)}}async function ht(t){try{let o=await(await fetch(`/api/schedules/${t}`)).json();if(!o.success){u("Schedule not found","error"),Y();return}let n=o.schedule,s=document.getElementById("schedule-name"),r=document.getElementById("schedule-description"),i=document.getElementById("schedule-frequency"),a=document.getElementById("schedule-time"),c=document.getElementById("schedule-enabled"),m=document.getElementById("schedule-notify"),l=document.getElementById("schedule-wake");if(s&&(s.value=n.name||""),r&&(r.value=n.description||""),i&&n.frequency&&(i.value=n.frequency),a&&n.time_of_day&&(a.value=n.time_of_day.substring(0,5)),c&&(c.checked=n.enabled),m&&(m.checked=n.notify??!0),l&&(l.checked=n.wake_mac??!1),(n.operations||[]).forEach(g=>{let p=document.querySelector(`input[name="operations"][value="${g}"]`);p&&(p.checked=!0)}),Ke(),n.frequency==="weekly"&&n.days_of_week&&n.days_of_week.forEach(g=>{let p=document.querySelector(`input[name="days"][value="${g}"]`);p&&(p.checked=!0)}),n.frequency==="monthly"&&n.day_of_month){let g=document.getElementById("schedule-day");g&&(g.value=String(n.day_of_month))}let d=document.getElementById("schedule-modal");d&&d.classList.add("active")}catch(e){console.error("Failed to load schedule:",e),u("Failed to load schedule","error")}}function Ke(){let e=document.getElementById("schedule-frequency")?.value||"",o=document.getElementById("days-selector"),n=document.getElementById("day-selector");o&&(o.style.display=e==="weekly"?"block":"none"),n&&(n.style.display=e==="monthly"?"block":"none")}function Ve(t){me(),setTimeout(()=>{let e=document.getElementById("schedule-name"),o=document.getElementById("schedule-description"),n=document.getElementById("schedule-frequency"),s=document.getElementById("schedule-time");if(e&&(e.value=t.name),o&&(o.value=t.description),n&&(n.value=t.frequency),s&&(s.value=t.time_of_day.substring(0,5)),t.operations.forEach(r=>{let i=document.querySelector(`input[name="operations"][value="${r}"]`);i&&(i.checked=!0)}),Ke(),t.days_of_week&&t.days_of_week.forEach(r=>{let i=document.querySelector(`input[name="days"][value="${r}"]`);i&&(i.checked=!0)}),t.day_of_month){let r=document.getElementById("schedule-day");r&&(r.value=t.day_of_month)}},100)}var ue=null;function Je(){gt(),I(),ue&&window.clearInterval(ue),ue=window.setInterval(()=>{let t=document.getElementById("schedule");t&&t.classList.contains("active")&&I()},1e4)}function yt(t){return t.frequency==="daily"?"Daily":t.frequency==="weekly"?`Weekly (${t.days_of_week?.map(o=>o.substring(0,3).toUpperCase()).join(", ")||"No days"})`:t.frequency==="monthly"?`Monthly (Day ${t.day_of_month})`:t.frequency||"Unknown"}function ze(t){try{let e=new Date(t),o=new Date,n=e.getTime()-o.getTime(),s=Math.floor(n/(1e3*60*60*24)),r=Math.floor(n/(1e3*60*60));return n<0?e.toLocaleString():s===0&&r<24?`in ${r}h`:s<7?`in ${s}d`:e.toLocaleDateString()}catch{return t}}console.log("\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557");console.log("\u2551   UPKEEP - SCRIPT LOADING            \u2551");console.log("\u255A\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255D");window.switchTab=ee;window.showTab=ee;window.toggleTheme=ge;window.reloadScripts=ve;window.loadSystemInfo=U;window.loadHealthScore=W;window.loadTopProcesses=G;window.loadOperations=Se;window.runDoctor=J;window.fixDoctorIssue=Ae;window.runSelectedOperations=Be;window.cancelOperations=Ce;window.skipCurrentOperation=Le;window.applyTemplate=Me;window.selectAllOperations=ke;window.deselectAllOperations=Ie;window.copyOutputToClipboard=le;window.showQuickStartWizard=Pe;window.closeWizard=V;window.selectWizardOption=De;window.closeShortcuts=ce;window.analyzeStorage=de;window.setPath=Ne;window.getUsername=qe;window.onScheduleTabShow=Je;window.openScheduleModal=me;window.closeScheduleModal=Y;window.loadSchedules=I;window.saveSchedule=je;window.deleteSchedule=Ue;window.toggleScheduleEnabled=We;window.runScheduleNow=Ge;window.applyScheduleTemplate=Ve;window.showToast=u;document.addEventListener("DOMContentLoaded",()=>{console.log("\u2713 DOM Content Loaded"),Oe(),pe(),console.log("\u2713 Theme initialized"),U(),W(),G(),console.log("\u2713 Initial dashboard data loading"),setInterval(()=>{let t=document.getElementById("dashboard");t&&t.classList.contains("active")&&(U(),W())},5e3),console.log("\u2713 Periodic updates configured (5s interval)"),setInterval(()=>{let t=document.getElementById("dashboard");t&&t.classList.contains("active")&&G()},1e4),console.log("\u2713 Process refresh configured (10s interval)"),console.log("\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557"),console.log("\u2551   UPKEEP - READY                     \u2551"),console.log("\u255A\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255D")});})();
//# sourceMappingURL=app.js.map
