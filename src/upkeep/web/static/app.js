"use strict";(()=>{function pn(){let e=localStorage.getItem("theme")||"system";He(e),window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change",()=>{(localStorage.getItem("theme")||"system")==="system"&&He("system")})}function fn(){let e=localStorage.getItem("theme")||"system",t;e==="light"?t="dark":e==="dark"?t="system":t="light",He(t),localStorage.setItem("theme",t)}function He(e){let t=e;e==="system"&&(t=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"),document.documentElement.setAttribute("data-theme",t);let n=document.getElementById("theme-icon");n&&(e==="light"?n.textContent="\u2600\uFE0F":e==="dark"?n.textContent="\u{1F319}":n.textContent="\u{1F5A5}\uFE0F")}function h(e,t="info",n=3e3){let r=document.createElement("div");r.className=`toast ${t}`,r.textContent=e;let o=document.getElementById("toast-container");if(!o){console.error("Toast container not found");return}o.appendChild(r),setTimeout(()=>r.classList.add("show"),10),setTimeout(()=>{r.classList.remove("show"),setTimeout(()=>r.remove(),300)},n)}var qe=!1,ze=null,De=null;function mn(e,t,n){let r=document.getElementById("progress-overlay"),o=document.getElementById("progress-title"),s=document.getElementById("progress-percent"),i=document.getElementById("progress-current"),a=document.getElementById("progress-bar");if(!r||!o||!s||!i||!a){console.error("Progress overlay elements not found");return}o.textContent=e,s.textContent="0%",i.textContent="0";let c=document.getElementById("progress-remaining");c&&(c.textContent="--"),a.style.width="0%",r.classList.add("active"),qe=!0,ze=n,De=Date.now(),document.addEventListener("keydown",gn)}function hn(e,t,n=""){if(!qe)return;let r=Math.round(e/t*100),o=document.getElementById("progress-percent"),s=document.getElementById("progress-current"),i=document.getElementById("progress-bar"),a=document.getElementById("progress-remaining"),c=document.getElementById("progress-message");if(!o||!s||!i)return;let p=parseInt(o.textContent||"0");if(fe(o,p,r,200,0,"%"),s.textContent=String(e),i.style.width=r+"%",e>0&&De&&a){let u=(Date.now()-De)/1e3,d=e/u,f=(t-e)/d;if(f<60)a.textContent=Math.round(f)+"s";else{let m=Math.floor(f/60),y=Math.round(f%60);a.textContent=`${m}m ${y}s`}}n&&c&&(c.textContent=n)}function St(){let e=document.getElementById("progress-overlay");e&&e.classList.remove("active"),qe=!1,ze=null,De=null,document.removeEventListener("keydown",gn)}function xs(){ze&&ze(),St(),h("Operation cancelled","warning")}function gn(e){e.key==="Escape"&&qe&&xs()}function fe(e,t,n,r=300,o=1,s=""){let i=performance.now(),a=n-t;function c(p){let u=p-i,d=Math.min(u/r,1),l=1-Math.pow(1-d,3),f=t+a*l;e.textContent=f.toFixed(o)+s,d<1&&requestAnimationFrame(c)}requestAnimationFrame(c)}async function yn(){let e=document.getElementById("reload-scripts-btn"),t=document.getElementById("reload-scripts-status");if(!(!e||!t)){e.disabled=!0,e.textContent="\u23F3 Reloading...",t.textContent="Copying updated scripts to system location...",t.style.color="var(--text-secondary)";try{let n=await fetch("/api/system/reload-scripts",{method:"POST",headers:{"Content-Type":"application/json"}});if(!n.ok){let o=await n.json();throw new Error(o.detail||"Failed to reload scripts")}let r=await n.json();e.textContent="\u2713 Reloaded",t.textContent=r.message||"Scripts reloaded successfully. Changes will take effect immediately.",t.style.color="var(--success)",h("Scripts reloaded successfully","success"),setTimeout(()=>{e.disabled=!1,e.textContent="\u{1F504} Reload Scripts",t.textContent=""},3e3)}catch(n){let r=n instanceof Error?n.message:"Unknown error";e.textContent="\u2717 Failed",t.textContent=`Error: ${r}`,t.style.color="var(--danger)",h(`Failed to reload scripts: ${r}`,"error"),setTimeout(()=>{e.disabled=!1,e.textContent="\u{1F504} Reload Scripts"},5e3)}}}var Be=null,Ae=null;function vn(e){He(e),localStorage.setItem("theme",e),xn(e),h(`Theme set to ${e}`,"success",2e3)}function xn(e){let t=document.getElementById("theme-selector");t&&t.querySelectorAll(".theme-option").forEach(n=>{n.getAttribute("data-theme")===e?n.classList.add("active"):n.classList.remove("active")})}function wn(e){if(localStorage.setItem("autoRefresh",String(e)),e){let t=parseInt(localStorage.getItem("refreshInterval")||"10",10);Tt(t),h("Auto-refresh enabled","success",2e3)}else En(),h("Auto-refresh disabled","info",2e3)}function bn(e){localStorage.setItem("refreshInterval",String(e));let t=document.getElementById("interval-selector");t&&t.querySelectorAll(".interval-option").forEach(r=>{parseInt(r.getAttribute("data-interval")||"0",10)===e?r.classList.add("active"):r.classList.remove("active")}),localStorage.getItem("autoRefresh")!=="false"&&Tt(e),h(`Refresh interval set to ${e}s`,"success",2e3)}function Tt(e){En();let t=e*1e3;Be=setInterval(()=>{let r=document.getElementById("dashboard");if(r&&r.classList.contains("active")){let o=window.loadSystemInfo,s=window.loadHealthScore;o&&o(),s&&s()}},t);let n=Math.max(t*2,1e4);Ae=setInterval(()=>{let r=document.getElementById("dashboard");if(r&&r.classList.contains("active")){let o=window.loadTopProcesses;o&&o()}},n)}function En(){Be&&(clearInterval(Be),Be=null),Ae&&(clearInterval(Ae),Ae=null)}function kn(e){localStorage.setItem("defaultPreviewMode",String(e)),h(e?"Preview mode enabled by default":"Preview mode disabled","info",2e3)}function _n(e){localStorage.setItem("requireConfirmation",String(e)),h(e?"Confirmations enabled":"Confirmations disabled","info",2e3)}function Sn(){let e=localStorage.getItem("theme")||"system";xn(e);let t=localStorage.getItem("autoRefresh")!=="false",n=document.getElementById("auto-refresh-toggle");n&&(n.checked=t);let r=parseInt(localStorage.getItem("refreshInterval")||"10",10),o=document.getElementById("interval-selector");o&&o.querySelectorAll(".interval-option").forEach(p=>{parseInt(p.getAttribute("data-interval")||"0",10)===r?p.classList.add("active"):p.classList.remove("active")});let s=localStorage.getItem("defaultPreviewMode")==="true",i=document.getElementById("preview-mode-toggle");i&&(i.checked=s);let a=localStorage.getItem("requireConfirmation")!=="false",c=document.getElementById("confirm-toggle");c&&(c.checked=a),ws(),t&&Tt(r)}async function ws(){let e=document.getElementById("app-version"),t=document.getElementById("ops-count"),n=document.getElementById("schedules-count"),r=document.querySelector('meta[name="app-version"]');e&&r&&(e.textContent=r.getAttribute("content")||"--");try{let o=await fetch("/api/maintenance/operations");if(o.ok&&t){let s=await o.json();t.textContent=String(s.operations?.length||0)}}catch{}try{let o=await fetch("/api/schedules");if(o.ok&&n){let s=await o.json();n.textContent=String(s.schedules?.length||0)}}catch{}}function Tn(){let e=new KeyboardEvent("keydown",{key:"?"});document.dispatchEvent(e)}function $t(e){document.querySelectorAll(".tab-content").forEach(r=>r.classList.remove("active")),document.querySelectorAll(".tabs button").forEach(r=>r.classList.remove("active"));let t=document.getElementById(e);if(t&&t.classList.add("active"),document.querySelectorAll(".tabs button").forEach(r=>{r.textContent?.toLowerCase().includes(e)&&r.classList.add("active")}),e==="dashboard"){let r=window.loadSystemInfo;r&&r()}else if(e==="maintenance"){let r=window.loadOperations;r&&r()}else if(e==="schedule"){let r=window.onScheduleTabShow;r&&r()}}var H={cpu:null,memory:null,disk:null},bs=null;async function Lt(e,t=3,n=1e3){let r=null;for(let o=0;o<=t;o++)try{let s=await fetch(e);if(!s.ok)throw new Error(`HTTP ${s.status}: ${s.statusText}`);return s}catch(s){r=s,o<t&&await new Promise(i=>setTimeout(i,n*Math.pow(2,o)))}throw r||new Error("Fetch failed after retries")}async function Pe(){try{let t=await(await Lt("/api/system/info")).json();t.system&&t.system.username&&(bs=t.system.username,window._currentUsername=t.system.username);let n=Mt(t.cpu.history),r=Mt(t.memory.history),o=Mt(t.disk.history),s=document.getElementById("system-metrics");if(!s)return;if(H.cpu===null)s.innerHTML=`
        <div class="metric-card">
          <h3>CPU Usage</h3>
          <div class="value" id="cpu-value">${t.cpu.percent.toFixed(1)}%</div>
          ${te(n,t.cpu.history)}
          <div class="sparkline-container">
            <canvas id="cpu-sparkline" class="sparkline" width="80" height="24"></canvas>
          </div>
          <div class="subvalue">${t.cpu.count} cores</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${X(t.cpu.percent)}" id="cpu-bar"
                 style="width: ${t.cpu.percent}%"></div>
          </div>
        </div>
        <div class="metric-card">
          <h3>Memory</h3>
          <div class="value" id="memory-value">${t.memory.percent.toFixed(1)}%</div>
          ${te(r,t.memory.history)}
          <div class="sparkline-container">
            <canvas id="memory-sparkline" class="sparkline" width="80" height="24"></canvas>
          </div>
          <div class="subvalue">${t.memory.available_gb.toFixed(1)} GB available</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${X(t.memory.percent)}" id="memory-bar"
                 style="width: ${t.memory.percent}%"></div>
          </div>
        </div>
        <div class="metric-card">
          <h3>Disk Space</h3>
          <div class="value" id="disk-value">${t.disk.percent.toFixed(1)}%</div>
          ${te(o,t.disk.history)}
          <div class="sparkline-container">
            <canvas id="disk-sparkline" class="sparkline" width="80" height="24"></canvas>
          </div>
          <div class="subvalue">${t.disk.free_gb.toFixed(1)} GB free of ${t.disk.total_gb.toFixed(1)} GB</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${X(t.disk.percent)}" id="disk-bar"
                 style="width: ${t.disk.percent}%"></div>
          </div>
        </div>
        ${t.network?`
        <div class="metric-card">
          <h3>Network</h3>
          <div class="value" id="network-value">
            \u2193 ${t.network.download_mbps.toFixed(2)} MB/s
          </div>
          <div class="subvalue" style="margin-top: 0.25rem;">
            \u2191 ${t.network.upload_mbps.toFixed(2)} MB/s
          </div>
          <div class="subvalue" style="font-size: 0.75rem; margin-top: 0.5rem;">
            Total: \u2193${t.network.total_recv_gb} GB / \u2191${t.network.total_sent_gb} GB
          </div>
        </div>
        `:""}
        ${t.swap&&t.swap.total_gb>0?`
        <div class="metric-card">
          <h3>Swap</h3>
          <div class="value" id="swap-value">${t.swap.percent.toFixed(1)}%</div>
          <div class="subvalue">${t.swap.used_gb} GB used of ${t.swap.total_gb} GB</div>
          <div class="progress-bar">
            <div class="progress-bar-fill ${X(t.swap.percent)}" id="swap-bar"
                 style="width: ${t.swap.percent}%"></div>
          </div>
          ${t.swap.percent>50?'<div class="warning">\u26A0\uFE0F High swap usage indicates memory pressure</div>':""}
        </div>
        `:""}
      `,console.log("First load - Memory bar HTML rendered"),setTimeout(()=>{let u=document.getElementById("memory-bar");u?console.log("Memory bar found after first load:",{width:u.style.width,className:u.className,computedWidth:window.getComputedStyle(u).width,parent:u.parentElement}):console.error("Memory bar NOT found after first load!")},100);else{let u=document.getElementById("cpu-value"),d=document.getElementById("memory-value"),l=document.getElementById("disk-value");u&&H.cpu!==null&&fe(u,H.cpu,t.cpu.percent,300,1,"%"),d&&H.memory!==null&&fe(d,H.memory,t.memory.percent,300,1,"%"),l&&H.disk!==null&&fe(l,H.disk,t.disk.percent,300,1,"%");let f=document.getElementById("cpu-bar"),m=document.getElementById("memory-bar"),y=document.getElementById("disk-bar");m?console.log(`Memory bar found: width=${t.memory.percent}%, element:`,m):console.error("Memory bar element not found!"),f&&(f.style.width=t.cpu.percent+"%",f.className=`progress-bar-fill ${X(t.cpu.percent)}`),m&&(m.style.width=t.memory.percent+"%",m.className=`progress-bar-fill ${X(t.memory.percent)}`),y&&(y.style.width=t.disk.percent+"%",y.className=`progress-bar-fill ${X(t.disk.percent)}`);let v=document.querySelector(".metric-card:nth-child(1)"),w=document.querySelector(".metric-card:nth-child(2)"),g=document.querySelector(".metric-card:nth-child(3)");if(v){let x=v.querySelector(".trend");x&&x.remove();let b=v.querySelector(".value");b&&b.insertAdjacentHTML("afterend",te(n,t.cpu.history))}if(w){let x=w.querySelector(".trend");x&&x.remove();let b=w.querySelector(".value");b&&b.insertAdjacentHTML("afterend",te(r,t.memory.history))}if(g){let x=g.querySelector(".trend");x&&x.remove();let b=g.querySelector(".value");b&&b.insertAdjacentHTML("afterend",te(o,t.disk.history))}}H.cpu=t.cpu.percent,H.memory=t.memory.percent,H.disk=t.disk.percent,fetch("/api/system/sparkline").then(u=>u.json()).then(u=>{console.log("Sparkline data received:",u),u&&u.cpu&&u.cpu.length>=2?(It("cpu-sparkline",u.cpu,"#ff6961"),It("memory-sparkline",u.memory,"#0a84ff"),It("disk-sparkline",u.disk,"#ff9500")):console.warn("Sparkline data insufficient:",u)}).catch(u=>console.error("Error loading sparkline data:",u));let a=document.getElementById("system-info");a&&(a.innerHTML=`
        <dl class="info-item">
          <dt>Total Memory</dt>
          <dd>${t.memory.total_gb.toFixed(1)} GB</dd>
        </dl>
        <dl class="info-item">
          <dt>Used Memory</dt>
          <dd>${t.memory.used_gb.toFixed(1)} GB</dd>
        </dl>
        <dl class="info-item">
          <dt>Total Disk</dt>
          <dd>${t.disk.total_gb.toFixed(1)} GB</dd>
        </dl>
        <dl class="info-item">
          <dt>Used Disk</dt>
          <dd>${t.disk.used_gb.toFixed(1)} GB</dd>
        </dl>
      `);let c=t.disk.percent>80?`<div class="warning">\u26A0\uFE0F Disk usage is high (${t.disk.percent.toFixed(1)}%). Consider running cleanup operations.</div>`:"",p=t.memory.percent>80?`<div class="warning">\u26A0\uFE0F Memory usage is high (${t.memory.percent.toFixed(1)}%).</div>`:"";await _s(c,p)}catch(e){let t=document.getElementById("system-metrics");t&&(t.innerHTML=`<div class="error">Error loading system info: ${e.message}</div>`)}}function Es(e,t){switch(t){case"excellent":return"#32d74b";case"good":return"#0a84ff";case"fair":return"#ff9500";case"poor":return"#ff3b30";default:return e>=90?"#32d74b":e>=70?"#0a84ff":e>=50?"#ff9500":"#ff3b30"}}function ks(e,t){let p=150+240*e/100,u=_t=>(_t-90)*Math.PI/180,d=90+84*Math.cos(u(150)),l=90+84*Math.sin(u(150)),f=90+84*Math.cos(u(390)),m=90+84*Math.sin(u(390)),y=90+84*Math.cos(u(p)),v=90+84*Math.sin(u(p)),w=1,g=p-150>180?1:0,x=Es(e,t),b=`M ${d} ${l} A 84 84 0 ${w} 1 ${f} ${m}`,$=e>0?`M ${d} ${l} A 84 84 0 ${g} 1 ${y} ${v}`:"",q=t==="excellent"?"\u2728":t==="good"?"\u{1F44D}":t==="fair"?"\u26A0\uFE0F":"\u{1F534}";return`
    <svg width="180" height="180" viewBox="0 0 180 180" class="health-gauge-svg">
      <!-- Background track -->
      <path
        d="${b}"
        fill="none"
        stroke="var(--border-light)"
        stroke-width="12"
        stroke-linecap="round"
      />
      <!-- Score arc with gradient -->
      <defs>
        <linearGradient id="healthGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:${x};stop-opacity:0.7" />
          <stop offset="100%" style="stop-color:${x};stop-opacity:1" />
        </linearGradient>
      </defs>
      ${e>0?`
      <path
        d="${$}"
        fill="none"
        stroke="url(#healthGradient)"
        stroke-width="12"
        stroke-linecap="round"
        class="health-gauge-arc"
      />
      `:""}
      <!-- Center score text -->
      <text x="90" y="80" text-anchor="middle" class="health-gauge-score" fill="${x}">
        ${e}
      </text>
      <text x="90" y="110" text-anchor="middle" class="health-gauge-label">
        ${t.toUpperCase()}
      </text>
      <text x="90" y="135" text-anchor="middle" class="health-gauge-emoji">
        ${q}
      </text>
    </svg>
  `}async function Oe(){let e=document.getElementById("health-score");if(e)try{let n=await(await Lt("/api/system/health")).json(),r=ks(n.score,n.overall),o="";n.issues&&n.issues.length>0?o=`
        <div class="health-issues">
          <h4>Issues Detected:</h4>
          <ul class="health-issues-list">
            ${n.issues.map(s=>`
              <li class="${s.includes("Critical")?"critical":"warning"}">
                ${s.includes("Critical")?"\u{1F534}":"\u26A0\uFE0F"} ${s}
              </li>
            `).join("")}
          </ul>
        </div>
      `:o=`
        <div class="health-all-clear">
          <span class="health-check-icon">\u2713</span>
          All systems healthy
        </div>
      `,e.innerHTML=`
      <div class="health-gauge-container">
        ${r}
      </div>
      ${o}
    `}catch(t){e.innerHTML=`<div class="error">Error loading health score: ${t.message}</div>`}}async function Ne(){let e=document.getElementById("top-processes");if(e)try{let n=await(await Lt("/api/system/processes?limit=3")).json(),r='<div class="process-section">';r+='<h3 style="font-size: 0.875rem; margin-bottom: 0.5rem; color: var(--text-secondary);">Top CPU Consumers</h3>',r+='<div class="process-list">',n.top_cpu.forEach((o,s)=>{r+=`
        <div class="process-item">
          <div class="process-rank">${s+1}</div>
          <div class="process-name">${o.name}</div>
          <div class="process-value">${o.cpu_percent}%</div>
        </div>
      `}),r+="</div></div>",r+='<div class="process-section" style="margin-top: 1.5rem;">',r+='<h3 style="font-size: 0.875rem; margin-bottom: 0.5rem; color: var(--text-secondary);">Top Memory Consumers</h3>',r+='<div class="process-list">',n.top_memory.forEach((o,s)=>{r+=`
        <div class="process-item">
          <div class="process-rank">${s+1}</div>
          <div class="process-name">${o.name}</div>
          <div class="process-value">${o.memory_mb.toFixed(0)} MB</div>
        </div>
      `}),r+="</div></div>",e.innerHTML=r}catch(t){e.innerHTML=`<div class="error">Error loading processes: ${t.message}</div>`}}async function _s(e="",t=""){let n=document.getElementById("maintenance-status");if(n)try{let o=await(await fetch("/api/maintenance/last-run")).json(),s;if(o.status==="never")s="<strong>Never</strong>";else{let i=o.global_last_run||"Unknown",a=o.global_last_run_relative||"";s=`<strong>${i}</strong> <span style="color: var(--text-secondary);">(${a})</span>`}n.innerHTML=`
      <p>Last maintenance run: ${s}</p>
      <p style="margin-top: 0.5rem;">Recommendation: <strong>Run maintenance weekly</strong></p>
      ${e}
      ${t}
      ${!e&&!t?'<div class="success">\u2713 System is running smoothly</div>':""}
    `}catch{n.innerHTML=`
      <p>Last maintenance run: <strong>Never</strong> <span style="color: var(--text-secondary);">(check logs)</span></p>
      <p style="margin-top: 0.5rem;">Recommendation: <strong>Run maintenance weekly</strong></p>
      ${e}
      ${t}
      ${!e&&!t?'<div class="success">\u2713 System is running smoothly</div>':""}
    `}}function It(e,t,n="#0a84ff"){let r=document.getElementById(e);if(!r){console.warn(`Canvas not found: ${e}`);return}if(!t||t.length<2){console.warn(`Insufficient data for ${e}: ${t?t.length:0} points`);return}let o=r.getContext("2d");if(!o)return;let s=r.width,i=r.height;o.clearRect(0,0,s,i);let a=Math.min(...t),p=Math.max(...t)-a||1;o.beginPath(),o.strokeStyle=n,o.lineWidth=1.5,o.lineJoin="round",t.forEach((u,d)=>{let l=d/(t.length-1)*s,f=i-(u-a)/p*i;d===0?o.moveTo(l,f):o.lineTo(l,f)}),o.stroke()}function Mt(e){if(!e||e.length<2)return"neutral";let t=e[e.length-1],n=e[e.length-2],r=t-n;return Math.abs(r)<.5?"neutral":r>0?"up":"down"}function te(e,t){if(!t||t.length<2)return"";let n=t[t.length-1],r=t[t.length-2],o=Math.abs(n-r).toFixed(1);return`<span class="trend ${e}">${{up:"\u2191",down:"\u2193",neutral:"\u2022"}[e]} ${o}%</span>`}function X(e){return e>90?"danger":e>75?"warning":""}async function $n(){let e=document.querySelector(".hero-card button"),t=e?.innerHTML;try{e&&(e.disabled=!0,e.innerHTML="\u{1F504} Scanning..."),h("Starting health check...","info");let n=await fetch("/api/maintenance/doctor");if(!n.ok)throw new Error("Health check failed");let r=await n.json();await Promise.all([Pe(),Oe(),Ne()]);let o=r.issues?.length??0;if(o===0)h("\u2705 Your Mac is healthy! No issues found.","success");else{h(`Found ${o} item${o>1?"s":""} to review. Check the Maintenance tab.`,"warning");let s=window.showTab;s&&setTimeout(()=>s("maintenance"),1500)}}catch(n){console.error("Health check error:",n),h("Health check encountered an error. Please try again.","error")}finally{e&&t&&(e.disabled=!1,e.innerHTML=t)}}function me(e){if(e<60)return`${e.toFixed(0)}s`;if(e<3600){let t=Math.floor(e/60),n=Math.round(e%60);return`${t}m ${n}s`}else{let t=Math.floor(e/3600),n=Math.floor(e%3600/60);return`${t}h ${n}m`}}function E(e){let t=document.createElement("div");return t.textContent=e,t.innerHTML}var In="upkeep-operation-times";function Ct(){try{let e=localStorage.getItem(In);return e?JSON.parse(e):{}}catch(e){return console.error("Failed to load operation times:",e),{}}}function Ss(e){try{localStorage.setItem(In,JSON.stringify(e))}catch(t){console.error("Failed to save operation times:",t)}}function Mn(e,t){let n=Ct(),r=n[e]||{runs:[],average:0};r.runs.push(Math.round(t)),r.runs.length>5&&(r.runs=r.runs.slice(-5));let o=r.runs.reduce((s,i)=>s+i,0)/r.runs.length;r.average=Math.round(o*100)/100,n[e]=r,Ss(n)}function Re(e){let n=Ct()[e];return!n||n.runs.length===0?30:n.average}function Bt(e){let n=Ct()[e];if(!n||n.runs.length===0)return null;let r=[...n.runs].sort((i,a)=>i-a),o=Math.floor(r.length/2);if(r.length%2===0){let i=r[o-1],a=r[o];return typeof i!="number"||typeof a!="number"?null:(i+a)/2}let s=r[o];return typeof s=="number"?s:null}function At(e){let t=Bt(e);if(t===null)return null;if(t<60)return`${Math.round(t)}s`;if(t<3600){let n=Math.floor(t/60),r=Math.round(t%60);return r>0?`${n}m ${r}s`:`${n}m`}else{let n=Math.floor(t/3600),r=Math.round(t%3600/60);return r>0?`${n}h ${r}m`:`${n}h`}}function Ln(e,t,n){let r=0;for(let o of e)r+=Re(o);if(t){let o=Re(t),i=1-Math.max(0,Math.min(1,n));r+=o*i}return Math.round(r)}var Ht=!1,ne=0,L=[],Y=0,he=0,U=0,K=0,Bn=[],re=null,oe=null,z=null,zt=[],An={},Ts=null,B=new Set,Cn=new Set(["Reports","Cleanup Operations","Cache Cleanup","Space Cleanup"]),Fe={"Update Operations":{icon:"\u{1F4E6}",order:1},"Disk / Filesystem":{icon:"\u{1F4BE}",order:2},System:{icon:"\u2699\uFE0F",order:3},"Cleanup Operations":{icon:"\u{1F9F9}",order:4},"Cache Cleanup":{icon:"\u{1F5D1}\uFE0F",order:5},"Space Cleanup":{icon:"\u{1F4C1}",order:6},Reports:{icon:"\u{1F4CA}",order:7}};function $s(){let e=localStorage.getItem("upkeep-collapsed-categories");if(e)try{B=new Set(JSON.parse(e))}catch{B=new Set(Cn)}else B=new Set(Cn)}function Is(){localStorage.setItem("upkeep-collapsed-categories",JSON.stringify([...B]))}async function Hn(){try{let e=Date.now(),n=await(await fetch(`/api/maintenance/operations?_=${e}`)).json();if(!n.operations||n.operations.length===0){let d=document.getElementById("operations-list");d&&(d.innerHTML='<div class="error">No operations available</div>');return}L=n.operations,L.sort((d,l)=>d.category===l.category?d.name.localeCompare(l.name):d.category.localeCompare(l.category));let r={};try{r=(await(await fetch("/api/maintenance/last-run")).json()).operations||{},An=r}catch(d){console.warn("Could not fetch per-operation history:",d)}Ve().catch(()=>{});let o="";L.map(d=>{let l=r[d.id],f=l?.typical_display||At(d.id),m=f?` | \u23F1\uFE0F Typically <strong>${f}</strong>`:"",y="";if(l&&l.last_run_relative){let w=l.success?"\u2713":"\u2717",g=l.success?"var(--success-color)":"var(--error-color)";y=`<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem;">
          \u{1F4C5} Last run: <strong>${l.last_run_relative}</strong> <span style="color: ${g}">${w}</span>${m}
        </div>`}else y=`<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem;">
          \u{1F4C5} Last run: <strong>Never run</strong>${m||(m||' | \u23F1\uFE0F Typically <strong>\u2014</strong> <span style="opacity:0.7;">(first run)</span>')}
        </div>`;let v="";if(d.why||d.what||d.when_to_run&&d.when_to_run.length>0){let w=Array.isArray(d.when_to_run)&&d.when_to_run.length>0,g=!!d.why?.context,x=Array.isArray(d.why?.problems)&&d.why.problems.length>0,b=Array.isArray(d.what?.outcomes)&&d.what.outcomes.length>0,$=!!d.what?.timeline;if(w||g||x||b||$){let _t=w?`
              <div class="operation-when">
                <h5>\u{1F4C5} When to Run This</h5>
                <ul>
                  ${d.when_to_run.map(P=>`<li>${E(String(P))}</li>`).join("")}
                </ul>
              </div>
            `:"",hs=g?`<p class="operation-context">${E(String(d.why.context))}</p>`:"",gs=x?d.why.problems.map(P=>`<li><strong>${E(String(P.symptom))}</strong><br>${E(String(P.description))}</li>`).join(""):"",ys=b?d.what.outcomes.map(P=>`<li>${P.type==="positive"?"\u2705":P.type==="warning"?"\u26A0\uFE0F":P.type==="temporary"?"\u23F1\uFE0F":"\u2139\uFE0F"} ${E(String(P.description))}</li>`).join(""):"",vs=$?`<p class="operation-timeline"><strong>\u23F1\uFE0F How Long:</strong> ${E(String(d.what.timeline))}</p>`:"";v=`
            <details class="operation-details">
              <summary>\u2139\uFE0F Why run this & What to expect</summary>
              <div class="operation-details-content">
                ${_t}
                ${hs}
                ${x?`<div class="operation-why"><h5>\u{1F50D} Problems This Solves</h5><ul>${gs}</ul></div>`:""}
                ${b||$?`<div class="operation-what"><h5>\u2728 What Happens After Running</h5>${b?`<ul>${ys}</ul>`:""}${vs}</div>`:""}
              </div>
            </details>
          `}}return`
        <div class="operation-item" data-operation-id="${d.id}" data-category="${d.category}">
          <input type="checkbox" id="op-${d.id}" value="${d.id}"
                 ${d.recommended?"checked":""}>
          <div class="operation-info">
            <h4>
              ${d.name}
              ${d.recommended?'<span class="badge recommended">Recommended</span>':'<span class="badge optional">Optional</span>'}
            </h4>
            <p>${d.description}</p>
            ${v}
            ${y}
          </div>
        </div>
      `}),$s();let s=[...new Set(L.map(d=>d.category))].sort((d,l)=>{let f=Fe[d]?.order??99,m=Fe[l]?.order??99;return f-m}),i=L.filter(d=>d.recommended),a=`
      <div class="category-filters" style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; align-items: center;">
        <button class="category-filter-btn active" data-category="" onclick="window.upkeepFilterByCategory(null)">
          All (${L.length})
        </button>
        ${s.map(d=>{let l=L.filter(m=>m.category===d).length,f=Fe[d]?.icon||"\u{1F4CB}";return`<button class="category-filter-btn" data-category="${d}" onclick="window.upkeepFilterByCategory('${d}')">
            ${f} ${d} (${l})
          </button>`}).join("")}
        <span style="flex-grow: 1;"></span>
        <button class="expand-collapse-btn" onclick="window.upkeepExpandAll()" title="Expand all categories">
          \u229E Expand
        </button>
        <button class="expand-collapse-btn" onclick="window.upkeepCollapseAll()" title="Collapse all categories">
          \u229F Collapse
        </button>
      </div>
    `,c=(d,l=!1)=>{let f=r[d.id],m=f?.typical_display||At(d.id),y=m?` | \u23F1\uFE0F Typically <strong>${m}</strong>`:"",v="";if(f&&f.last_run_relative){let g=f.success?"\u2713":"\u2717",x=f.success?"var(--success-color)":"var(--error-color)";v=`<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem;">
          \u{1F4C5} Last run: <strong>${f.last_run_relative}</strong> <span style="color: ${x}">${g}</span>${y}
        </div>`}else v=`<div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem;">
          \u{1F4C5} Last run: <strong>Never run</strong>${y||" | \u23F1\uFE0F Typically <strong>\u2014</strong> (first run)"}
        </div>`;let w="";if(d.why||d.what||d.when_to_run&&d.when_to_run.length>0){let g="";if(d.why){if(g+='<div class="operation-why">',g+="<h5>\u{1F914} Why run this?</h5>",d.why.context&&(g+=`<div class="operation-context">${E(d.why.context)}</div>`),d.why.problems&&d.why.problems.length>0){g+="<ul>";for(let x of d.why.problems)g+=`<li><strong>${E(x.symptom)}</strong> ${E(x.description)}</li>`;g+="</ul>"}g+="</div>"}if(d.what){if(g+='<div class="operation-what">',g+="<h5>\u{1F4CB} What to expect</h5>",d.what.outcomes&&d.what.outcomes.length>0){g+="<ul>";for(let x of d.what.outcomes){let b=x.type==="positive"?"\u2705":x.type==="warning"?"\u26A0\uFE0F":x.type==="temporary"?"\u23F3":x.type==="neutral"?"\u2796":"\u2139\uFE0F";g+=`<li>${b} ${E(x.description)}</li>`}g+="</ul>"}d.what.timeline&&(g+=`<div class="operation-timeline"><strong>\u23F1\uFE0F Timeline:</strong> ${E(d.what.timeline)}</div>`)}if(d.when_to_run&&d.when_to_run.length>0){g+='<div class="operation-when">',g+="<h5>\u{1F4C5} When to run</h5>",g+="<ul>";for(let x of d.when_to_run)g+=`<li>${E(x)}</li>`;g+="</ul>",g+="</div>"}w=`<details class="operation-details"><summary>\u2139\uFE0F Why run this & What to expect</summary><div class="operation-details-content">${g}</div></details>`}return`
        <div class="operation-item" data-operation-id="${d.id}" data-category="${d.category}" style="transition: all 0.2s ease;">
          <input type="checkbox" id="op-${d.id}" value="${d.id}" ${d.recommended?"checked":""}>
          <div class="operation-info">
            <h4>${d.name} ${d.recommended?'<span class="badge recommended">Recommended</span>':'<span class="badge optional">Optional</span>'}</h4>
            <p>${d.description}</p>
            ${w}
            ${v}
          </div>
        </div>
      `};o=a,i.length>0&&(o+=`
        <div class="category-header recommended-header" style="display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem; background: linear-gradient(135deg, var(--accent-color) 0%, #5856d6 100%); color: white; border-radius: 6px; margin: 0.5rem 0;">
          <span style="font-size: 1.1rem;">\u2B50</span>
          <strong>Recommended</strong>
          <span style="opacity: 0.8; font-size: 0.85rem;">(${i.length})</span>
        </div>
      `,i.forEach(d=>{o+=c(d,!0)}));for(let d of s){let l=L.filter(y=>y.category===d&&!y.recommended);if(l.length===0)continue;let f=Fe[d]?.icon||"\u{1F4CB}",m=B.has(d);o+=`
        <div class="category-header ${m?"collapsed":""}" data-category="${d}" 
             style="display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem; background: var(--bg-tertiary); border-radius: 6px; margin: 1rem 0 0.5rem; cursor: pointer; user-select: none;"
             onclick="window.upkeepToggleCategory('${d}')">
          <span class="collapse-icon" style="font-size: 0.75rem; transition: transform 0.2s;">${m?"\u25B6":"\u25BC"}</span>
          <span style="font-size: 1.1rem;">${f}</span>
          <strong>${d}</strong>
          <span style="color: var(--text-secondary); font-size: 0.85rem;">(${l.length})</span>
        </div>
      `,l.forEach(y=>{let v=m?"display: none; max-height: 0; opacity: 0;":"";o+=c(y).replace('style="transition:',`style="${v} transition:`)})}let p=document.getElementById("operations-list");p&&(p.innerHTML=o);let u=L.filter(d=>d.recommended).length;h(`Loaded ${L.length} operations (${u} recommended)`,"success",2e3);try{let l=await(await fetch("/api/maintenance/last-run")).json();if(document.querySelectorAll(".info-banner").forEach(m=>m.remove()),l.success&&l.status==="completed"){let m=document.createElement("div");m.className="info-banner",m.style.cssText="padding: 0.75rem; background: var(--success-bg); color: var(--success-color); border-radius: 6px; margin-bottom: 1rem; font-size: 0.875rem;";let y=l.global_last_run_relative||"Recently";m.innerHTML=`\u{1F4C5} Last maintenance run: <strong>${y}</strong>`,p?.insertAdjacentElement("beforebegin",m)}else if(l.status==="never"){let m=document.createElement("div");m.className="info-banner",m.style.cssText="padding: 0.75rem; background: var(--warning-bg); color: var(--warning-color); border-radius: 6px; margin-bottom: 1rem; font-size: 0.875rem;",m.innerHTML="\u2139\uFE0F Maintenance has never been run",p?.insertAdjacentElement("beforebegin",m)}}catch(d){console.warn("Could not fetch last run info:",d)}}catch(e){console.error("Error loading operations:",e);let t=document.getElementById("operations-list");t&&(t.innerHTML=`<div class="error">Error loading operations: ${e.message}</div>`),h("Failed to load operations","error")}}function zn(){let e=document.querySelectorAll('#operations-list input[type="checkbox"]');e.forEach(t=>t.checked=!0),h(`Selected all ${e.length} operations`,"info",2e3)}function Dn(){document.querySelectorAll('#operations-list input[type="checkbox"]').forEach(t=>t.checked=!1),h("Deselected all operations","info",2e3)}function qn(e){Ts=e,document.querySelectorAll(".category-filter-btn").forEach(n=>{n.classList.toggle("active",n.getAttribute("data-category")===e)}),document.querySelectorAll(".operation-item").forEach(n=>{let r=n.getAttribute("data-operation-id"),o=L.find(s=>s.id===r);if(o){let s=!e||o.category===e;n.style.display=s?"":"none"}}),document.querySelectorAll(".category-header").forEach(n=>{let r=n.getAttribute("data-category");n.style.display=!e||r===e?"":"none"}),h(`Showing ${e||"all"} operations`,"info",1500)}function Ue(e){B.has(e)?B.delete(e):B.add(e),Is();let t=document.querySelectorAll(`.operation-item[data-category="${e}"]`),n=B.has(e);t.forEach(o=>{n?(o.style.maxHeight="0",o.style.opacity="0",o.style.overflow="hidden",o.style.marginBottom="0",o.style.padding="0",setTimeout(()=>{o.style.display="none"},200)):(o.style.display="",o.style.overflow="hidden",setTimeout(()=>{o.style.maxHeight="500px",o.style.opacity="1",o.style.marginBottom="",o.style.padding=""},10))});let r=document.querySelector(`.category-header[data-category="${e}"]`);if(r){let o=r.querySelector(".collapse-icon");o&&(o.textContent=n?"\u25B6":"\u25BC"),r.classList.toggle("collapsed",n)}}function Pn(){[...new Set(L.map(t=>t.category))].forEach(t=>{B.has(t)&&Ue(t)}),h("All categories expanded","info",1500)}function On(){[...new Set(L.map(t=>t.category))].forEach(t=>{B.has(t)||Ue(t)}),h("All categories collapsed","info",1500)}function Nn(e){if(console.log("Applying template:",e),document.querySelectorAll('#operations-list input[type="checkbox"]').forEach(n=>n.checked=!1),e.operations&&e.operations.length>0){let n=0;e.operations.forEach(r=>{let o=document.getElementById(`op-${r}`);o?(o.checked=!0,n++):console.warn(`Operation not found: ${r}`)}),h(`Applied "${e.name}" - ${n} operations selected`,"success",3e3)}else h(`Applied "${e.name}"`,"info",2e3)}async function Rn(){console.log("=== runSelectedOperations CALLED ===");let e=document.querySelectorAll('#operations-list input[type="checkbox"]:checked');console.log("Found checked checkboxes:",e.length);let t=Array.from(e).map(u=>u.value);if(console.log("Selected operations:",t),zt=t,t.length===0){console.log("No operations selected"),alert("No operations selected");return}ne++;let n=ne;console.log("Operation invocation ID:",n),Ht=!0;let r=document.getElementById("run-btn");r&&(r.disabled=!0);let o=document.getElementById("select-all-btn"),s=document.getElementById("deselect-all-btn");o&&(o.disabled=!0,o.setAttribute("aria-disabled","true"),o.title="Selection locked while operations are running"),s&&(s.disabled=!0,s.setAttribute("aria-disabled","true"),s.title="Selection locked while operations are running");let i=document.getElementById("skip-btn"),a=document.getElementById("cancel-btn");i&&(i.style.display="inline-block"),a&&(a.style.display="inline-block"),console.log("Showing Skip/Cancel buttons for invocation",n);let c=document.getElementById("progress-container");c&&(c.style.display="block"),U=0,K=t.length,Bn=[],he=Date.now(),Dt(),Cs(),Bs();let p=document.getElementById("progress-text");p&&(p.style.display="block",p.textContent=`Connecting to server...
`,p.scrollIntoView({behavior:"smooth",block:"nearest"}));try{let u=await fetch("/api/maintenance/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({operation_ids:t})});if(!u.ok){let m=await u.json();throw new Error(m.detail||"Failed to start operations")}let d=u.body?.getReader();if(!d)throw new Error("Failed to get response reader");let l=new TextDecoder,f="";for(;;){let{done:m,value:y}=await d.read();if(m)break;f+=l.decode(y,{stream:!0});let v=f.split(`
`);f=v.pop()||"";for(let w of v)if(w.startsWith("data: ")){let g=w.slice(6);try{let x=JSON.parse(g);Ms(x)}catch(x){console.error("Error parsing SSE data:",x)}}}}catch(u){p&&(p.textContent+=`

Error: ${u.message}
`),console.error("Error running operations:",u)}finally{n===ne?(console.log("Cleaning up invocation",n,"(current)"),r&&(r.disabled=!1),i&&(i.style.display="none"),a&&(a.style.display="none"),Ht=!1,Gn(),Vn(),he=0,c&&(c.style.display="none"),o&&(o.disabled=!1,o.removeAttribute("aria-disabled"),o.title=""),s&&(s.disabled=!1,s.removeAttribute("aria-disabled"),s.title="")):console.log("Skipping cleanup for invocation",n,"(superseded by",ne,")")}}async function Fn(){if(confirm("Skip the current operation?"))try{let e=await fetch("/api/maintenance/skip",{method:"POST"});if(!e.ok)throw new Error(`HTTP ${e.status}`);let t=await e.json(),n=document.getElementById("progress-text");if(n){let r=t.message||"Skipped by user";n.textContent+=`

\u23ED\uFE0F ${r}
`}h("Operation skipped","info",2e3)}catch(e){console.error("Error skipping operation:",e),alert("Error skipping operation: "+e.message)}}async function Un(){if(confirm("Cancel all running operations?"))try{let t=await(await fetch("/api/maintenance/cancel",{method:"POST"})).json(),n=document.getElementById("progress-text");n&&(n.textContent+=`

\u26A0\uFE0F ${t.message}
`),ne++,Ht=!1;let r=document.getElementById("run-btn"),o=document.getElementById("skip-btn"),s=document.getElementById("cancel-btn");r&&(r.disabled=!1),o&&(o.style.display="none"),s&&(s.style.display="none"),Gn(),Vn(),he=0;let i=document.getElementById("progress-container");i&&(i.style.display="none");let a=document.getElementById("select-all-btn"),c=document.getElementById("deselect-all-btn");a&&(a.disabled=!1,a.removeAttribute("aria-disabled"),a.title=""),c&&(c.disabled=!1,c.removeAttribute("aria-disabled"),c.title=""),console.log("Operations cancelled, incremented invocation ID to",ne)}catch(e){console.error("Error cancelling operations:",e),alert("Error cancelling operations: "+e.message)}}function Ms(e){let t=document.getElementById("progress-text");if(t){switch(e.type){case"start":t.textContent+=`
${e.message}
`,t.textContent+=`${"=".repeat(60)}

`;let n=document.getElementById("inline-progress-actions");n&&(n.style.display="none",n.innerHTML=""),setTimeout(()=>{window.scrollTo({top:document.body.scrollHeight,behavior:"smooth"})},50);break;case"operation_start":t.textContent+=`
[${e.progress}] Starting: ${e.operation_name}
`,t.textContent+=`${"-".repeat(60)}
`,Y=Date.now(),z=e.operation_id||null,U++,Dt();break;case"output":t.textContent+=`${e.line}
`,t.scrollTop=t.scrollHeight;break;case"operation_complete":let r=e.success?"\u2713 Success":"\u2717 Failed";if(t.textContent+=`
${r} (exit code: ${e.returncode})
`,Y>0&&z){let s=Date.now()-Y,i=s/1e3;e.success&&Mn(z,i),Bn.push(s),Dt()}z=null;break;case"operation_skipped":t.textContent+=`
\u23ED\uFE0F  Skipped by user
`;break;case"operation_error":t.textContent+=`
Error: ${e.message}
`;break;case"summary":if(t.textContent+=`
${"=".repeat(60)}
`,t.textContent+=`
Summary:
`,t.textContent+=`  Total operations: ${e.total}
`,t.textContent+=`  Successful: ${e.successful}
`,t.textContent+=`  Failed: ${e.failed}
`,e.disk_before&&e.disk_after&&e.space_recovered_display){t.textContent+=`
\u{1F4CA} Disk Space:
`,t.textContent+=`  Before: ${e.disk_before.free_gb} GB free
`,t.textContent+=`  After:  ${e.disk_after.free_gb} GB free
`;let s=e.space_recovered_bytes||0;s>0?t.textContent+=`  \u2728 Space recovered: ${e.space_recovered_display}
`:s<0?t.textContent+=`  \u{1F4E5} Space used: ${e.space_recovered_display}
`:t.textContent+=`  \u2796 No change in disk space
`}break;case"complete":t.textContent+=`
${e.message}
`,t.textContent+=`${"=".repeat(60)}
`,As();let o=document.getElementById("inline-progress-actions");if(o){o.innerHTML="",o.style.display="flex";let s=document.createElement("button");s.className="primary",s.id="copy-output-btn",s.innerHTML="\u{1F4CB} Copy Output to Clipboard",s.onclick=()=>qt(),o.appendChild(s),setTimeout(()=>{s.scrollIntoView({behavior:"smooth",block:"nearest"})},100)}break;case"cancelled":t.textContent+=`
${e.message}
`;break;case"error":t.textContent+=`
Error: ${e.message}
`;break}t.scrollTop=t.scrollHeight}}async function qt(){let e=document.getElementById("progress-text"),t=document.getElementById("copy-output-btn");if(!(!e||!t))try{await navigator.clipboard.writeText(e.textContent||"");let n=t.innerHTML;t.innerHTML="\u2713 Copied to Clipboard!",t.className="primary success-flash",setTimeout(()=>{t.innerHTML=n,t.className="primary"},2e3)}catch(n){console.error("Failed to copy to clipboard:",n);let r=t.innerHTML;t.innerHTML="\u2717 Copy Failed",t.className="danger",setTimeout(()=>{t.innerHTML=r,t.className="primary"},2e3)}}function Ls(){if(he>0){let e=Date.now()-he,t=document.getElementById("total-elapsed");t&&(t.textContent=me(e/1e3))}}function Cs(){re&&clearInterval(re),re=window.setInterval(()=>{if(Y>0){let e=Date.now()-Y,t=document.getElementById("current-op-timer");if(t){let n=me(e/1e3);if(z){let r=An?.[z]?.typical_seconds,o=typeof r=="number"?r:Bt(z);if(o!==null&&typeof o=="number"&&!Number.isNaN(o)){let s=me(o);t.textContent=`${n} / Typically ${s}`,t.setAttribute("title","Typical runtime (median of recent runs)")}else t.textContent=`${n} / Typically \u2014`,t.setAttribute("title","No historical runtime yet (first run)")}else t.textContent=n}}Ls()},1e3)}function Gn(){re&&(clearInterval(re),re=null)}function Dt(){let e=K>0?Math.round(U/K*100):0;console.log("updateProgress:",{currentOperationIndex:U,totalOperations:K,percent:e});let t=document.getElementById("maintenance-progress-bar"),n=document.getElementById("maintenance-progress-percent");t?(t.style.width=e+"%",console.log("Set maintenance-progress-bar width to:",e+"%")):console.error("maintenance-progress-bar element not found!"),n?(n.textContent=e+"%",console.log("Set maintenance-progress-percent text to:",e+"%")):console.error("maintenance-progress-percent element not found!");let r=document.getElementById("progress-label");r&&(r.textContent=`Operation ${U} of ${K}`);let o=document.getElementById("ops-progress");o&&(o.textContent=`${U}/${K}`);let s=document.getElementById("est-remaining");if(s)if(U>=K)s.textContent="Complete";else if(zt.length>0){let i=zt.slice(U),a=z&&Y>0?Math.min((Date.now()-Y)/(Re(z)*1e3),.99):0,c=Ln(i,z,a);s.textContent=me(c)}else s.textContent="Calculating..."}function Bs(){oe&&clearInterval(oe),oe=window.setInterval(async()=>{try{let t=await(await fetch("/api/maintenance/queue")).json(),n=document.getElementById("queue-status");if(t.queued_count>0){n&&(n.style.display="flex");let r=document.getElementById("queue-count");r&&(r.textContent=String(t.queued_count))}else n&&(n.style.display="none");t.current_operation&&console.log("Current operation:",t.current_operation)}catch(e){console.error("Error polling queue status:",e)}},2e3)}function Vn(){oe&&(clearInterval(oe),oe=null)}async function As(){try{let t=await(await fetch("/api/maintenance/last-run")).json();if(document.querySelectorAll(".info-banner").forEach(r=>{t.global_last_run_relative&&(r.innerHTML=`\u{1F4C5} Last maintenance run: <strong>${t.global_last_run_relative}</strong>`,r.style.background="var(--success-bg)",r.style.color="var(--success-color)")}),t.operations)for(let[r,o]of Object.entries(t.operations)){let s=document.querySelector(`[data-operation-id="${r}"]`);if(s){let i=s.querySelector(".operation-info > div:last-child");if(i&&o.last_run_relative){let a=o.success?"\u2713":"\u2717",c=o.success?"var(--success-color)":"var(--error-color)",p=o.typical_display||"",u=p?` | \u23F1\uFE0F Typically <strong>${p}</strong>`:"";i.innerHTML=`
              \u{1F4C5} Last run: <strong>${o.last_run_relative}</strong> <span style="color: ${c}">${a}</span>${u}
            `}}}}catch(e){console.error("Error refreshing timestamp:",e)}}var Hs={quick:["browser-cache","trim-caches","trim-logs"],weekly:["brew-update","mas-update","disk-verify","browser-cache","trim-caches","trim-logs","periodic","spotlight-status"],full:["brew-update","mas-update","disk-verify","browser-cache","dev-cache","dev-tools-cache","trim-caches","trim-logs","smart-check","periodic","spotlight-status","dns-flush"],developer:["dev-cache","dev-tools-cache","browser-cache","trim-caches","brew-cleanup","dns-flush"],security:["macos-check","brew-update","mas-update","disk-verify","smart-check"]};function Wn(){let e=document.getElementById("wizard-modal");e&&e.classList.add("active")}function Ge(){let e=document.getElementById("wizard-modal");e&&e.classList.remove("active")}async function jn(e){if(Ge(),e==="custom"){h("Select operations below","info",2e3);return}let t=Hs[e]||[];document.querySelectorAll('#operations-list input[type="checkbox"]').forEach(s=>{let i=s;i.checked=t.includes(i.value)}),h(`\u2728 Selected: ${{quick:"Quick Clean",weekly:"Weekly Routine",full:"Full Checkup"}[e]} (${t.length} operations)`,"success",3e3);let r=document.getElementById("operations-list");r&&r.scrollIntoView({behavior:"smooth"});let o=document.getElementById("wizard-prompt");o&&(o.style.display="none")}function zs(e){let t=e;if(!t)return!1;let n=(t.tagName||"").toLowerCase();return n==="input"||n==="textarea"||n==="select"||t.isContentEditable}async function Ve(){let e=document.getElementById("doctor-panel"),t=document.getElementById("doctor-results");if(!(!e||!t))try{let r=await(await fetch("/api/maintenance/doctor")).json();if(!r.success){e.style.display="block",t.innerHTML='<div style="color: var(--danger);">Doctor check failed.</div>';return}let o=r.issues||[];if(o.length===0){e.style.display="none",t.innerHTML="";return}e.style.display="block";let s=o.map(i=>{let a=i.severity==="error"?"var(--danger)":i.severity==="warning"?"var(--warning)":"var(--text-secondary)",c=Array.isArray(i.affects_operations)&&i.affects_operations.length?`<div style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.25rem;">Affects: ${i.affects_operations.join(", ")}</div>`:"",p=i.fix_action?`<button class="secondary" style="white-space: nowrap;" onclick="fixDoctorIssue('${i.fix_action}')">${i.fix_label||"Fix"}</button>`:"";return`
        <div style="display:flex; justify-content: space-between; gap: 1rem; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 10px; background: var(--bg-secondary);">
          <div>
            <div style="font-weight: 600; color: ${a};">${E(i.title||"Issue")}</div>
            <div style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 0.15rem;">${E(i.detail||"")}</div>
            ${c}
          </div>
          <div style="display:flex; align-items:center; gap: 0.5rem;">
            ${p}
          </div>
        </div>
      `}).join("");t.innerHTML=`<div style="display:grid; gap: 0.75rem;">${s}</div>`}catch{e.style.display="block",t.innerHTML='<div style="color: var(--danger);">Doctor check failed.</div>'}}async function Xn(e){try{let t=await fetch("/api/maintenance/doctor/fix",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:e})}),n=await t.json();if(!t.ok||!n.success)throw new Error(n.detail||n.error||"Failed");h(n.message||"Fix started","success",4e3),setTimeout(()=>Ve().catch(()=>{}),1500)}catch(t){h(t?.message||"Fix failed","error",5e3)}}function Pt(){let e=document.getElementById("shortcuts-modal");e&&e.classList.remove("active")}function Ds(){let e=document.getElementById("shortcuts-modal");e&&e.classList.add("active")}function Kn(){document.addEventListener("keydown",e=>{if(!zs(e.target)){if(e.key==="?"||e.key==="/"&&e.shiftKey){e.preventDefault(),Ds();return}if(e.key==="/"&&!e.metaKey&&!e.ctrlKey&&!e.altKey){let t=document.getElementById("operation-search");t&&(e.preventDefault(),t.focus());return}if(e.key==="Escape"){Pt(),Ge();let t=window.closeScheduleModal;t&&t()}}})}function Yn(){let e=document.createElement("a");e.href="/api/maintenance/export-log",e.download="upkeep-log.txt",document.body.appendChild(e),e.click(),document.body.removeChild(e)}var S=new Set;async function Nt(){let t=document.getElementById("path-input")?.value||"/Users",n=document.getElementById("storage-results"),r=document.getElementById("analyze-btn-text");if(!(!n||!r)){n.innerHTML='<div class="loading"><div class="spinner"></div> Analyzing storage...</div>',r.innerHTML='<div class="spinner"></div>',S.clear(),Jn(t);try{let o=await fetch(`/api/storage/analyze?path=${encodeURIComponent(t)}`);if(!o.ok){let l=`Server error: ${o.status}`;try{l=(await o.json()).detail||l}catch{}r.textContent="Analyze",n.innerHTML=`<div class="error">${l}</div>`,h(l,"error");return}let s=await o.json();if(r.textContent="Analyze",!s.success){let l=s.error||"Unknown error occurred";n.innerHTML=`<div class="error">${l}</div>`,h(l,"error");return}h(`Analyzed: ${s.file_count} files, ${s.total_size_gb.toFixed(2)} GB`,"success");let i=Fs(s.category_sizes,s.total_size_bytes);n.innerHTML=`
      <h3 style="margin-top: 2rem;">Results for ${s.path||t}</h3>
      <div class="metric-grid" style="margin-top: 1rem;">
        <div class="metric-card">
          <h3>Total Size</h3>
          <div class="value">${s.total_size_gb.toFixed(2)} GB</div>
        </div>
        <div class="metric-card">
          <h3>Files</h3>
          <div class="value">${s.file_count.toLocaleString()}</div>
        </div>
        <div class="metric-card">
          <h3>Directories</h3>
          <div class="value">${s.dir_count.toLocaleString()}</div>
        </div>
      </div>
      ${i}
      <h3 style="margin-top: 2rem;">Largest Items</h3>
      <p style="color: var(--text-secondary); margin-top: 0.5rem;">Select items to delete</p>
      <div class="file-list">
        ${s.largest_entries.map((l,f)=>{let m=l.path.split("/").pop();return`
          <div class="file-item">
            <input type="checkbox" id="file-${f}" data-path="${l.path.replace(/"/g,"&quot;").replace(/'/g,"&#39;")}">
            <div class="file-info">
              <strong>${m}</strong><br>
              <small style="color: var(--text-secondary);">${l.path}</small>
            </div>
            <div class="file-size">
              <strong>${l.size_gb.toFixed(2)} GB</strong><br>
              <small style="color: var(--text-secondary);">${l.is_dir?"Directory":"File"}</small>
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
    `,console.log("=== ATTACHING EVENT LISTENERS ===");let a=document.getElementById("trash-btn"),c=document.getElementById("permanent-delete-btn"),p=document.getElementById("select-all-btn"),u=document.getElementById("deselect-all-btn");console.log("Trash button found:",a),console.log("Permanent button found:",c),a&&(a.addEventListener("click",()=>{console.log("TRASH BUTTON CLICKED!"),Qn("trash")}),console.log("\u2713 Trash button listener attached")),c&&(c.addEventListener("click",()=>{console.log("PERMANENT DELETE BUTTON CLICKED!"),Qn("permanent")}),console.log("\u2713 Permanent button listener attached")),p&&(p.addEventListener("click",Ps),console.log("\u2713 Select all button listener attached")),u&&(u.addEventListener("click",Os),console.log("\u2713 Deselect all button listener attached"));let d=document.querySelectorAll('#storage-results input[type="checkbox"]');console.log("Found checkboxes:",d.length),d.forEach((l,f)=>{l.addEventListener("change",()=>{console.log(`Checkbox ${f} changed, path:`,l.dataset.path),l.dataset.path&&qs(l.dataset.path)})}),console.log("\u2713 All checkbox listeners attached")}catch(o){let s=o.message||"Failed to analyze storage";n.innerHTML=`<div class="error">Error: ${s}</div>`,r.textContent="Analyze",h(s,"error")}}}function qs(e){console.log("toggleFileSelection called with:",e),console.log("selectedFiles before:",Array.from(S)),S.has(e)?(S.delete(e),console.log("Removed path")):(S.add(e),console.log("Added path")),console.log("selectedFiles after:",Array.from(S)),We()}function We(){let e=S.size,t=document.getElementById("selected-count"),n=document.getElementById("selected-count-permanent");t&&(t.textContent=String(e)),n&&(n.textContent=String(e))}function Ps(){document.querySelectorAll('#storage-results input[type="checkbox"]').forEach(t=>{t.checked=!0,t.dataset.path&&S.add(t.dataset.path)}),We()}function Os(){document.querySelectorAll('#storage-results input[type="checkbox"]').forEach(t=>{t.checked=!1}),S.clear(),We()}async function Qn(e="trash"){if(console.log("=== deleteSelected CALLED ==="),console.log("Mode:",e),console.log("selectedFiles.size:",S.size),console.log("selectedFiles contents:",Array.from(S)),S.size===0){console.log("No files selected, showing toast"),h("No files selected","warning");return}let t;e==="permanent"?t=`\u26A0\uFE0F PERMANENTLY DELETE ${S.size} item(s)?

This CANNOT be undone! Files will be deleted forever.

Consider using "Move to Trash" instead (recoverable).`:t=`Move ${S.size} item(s) to Trash?

You can recover them from macOS Trash if needed.`,console.log("Showing confirmation dialog");let n=confirm(t);if(console.log("User confirmed:",n),!n){console.log("User cancelled");return}console.log("Proceeding with delete...");let r=S.size,o=0,s=0,i=[],a=!1,c=document.getElementById("trash-btn"),p=document.getElementById("permanent-delete-btn");c&&(c.disabled=!0),p&&(p.disabled=!0),mn(e==="permanent"?"\u26A0\uFE0F Permanently Deleting Files...":"\u{1F5D1}\uFE0F Moving Files to Trash...",r,()=>{a=!0});let d=0;for(let m of S){if(a)break;d++;let y=m.split("/").pop();hn(d,r,`Processing: ${y}`);try{let v=await fetch(`/api/storage/delete?path=${encodeURIComponent(m)}&mode=${e}`,{method:"DELETE"});if(!v.ok){let g=await v.json().catch(()=>({detail:"Unknown error"}));throw new Error(g.detail||`HTTP ${v.status}`)}let w=await v.json();w.success?o++:(s++,i.push({path:m,error:w.error||"Unknown error"}),console.error(`Failed to ${e==="permanent"?"delete":"move to trash"} ${m}:`,w.error))}catch(v){s++,i.push({path:m,error:v.message}),console.error(`Error processing ${m}:`,v)}}St(),c&&(c.disabled=!1),p&&(p.disabled=!1),S.clear(),We();let l=e==="permanent"?"deleted":"moved to Trash",f=e==="permanent"?"delete":"move";a?h(`\u26A0\uFE0F Operation cancelled. Processed ${o+s}/${r} items.`,"warning",4e3):o>0&&s===0?(h(`\u2705 Successfully ${l} ${o} item(s)`,"success",4e3),e==="trash"&&h("\u{1F4A1} Tip: You can recover files from macOS Trash","info",3e3)):o>0&&s>0?(h(`\u26A0\uFE0F ${l.charAt(0).toUpperCase()+l.slice(1)} ${o}, failed to ${f} ${s} item(s)`,"warning",6e3),console.error("Failed operations:",i)):(h(`\u274C Failed to ${f} all ${s} item(s)`,"error",6e3),console.error("Failed operations:",i)),h("Refreshing view...","info",2e3),await Nt()}function Jn(e){let t=document.getElementById("breadcrumbs");if(!t)return;let n=e.split("/").filter(s=>s);if(n.length===0){t.innerHTML=`<span class="breadcrumb" onclick="setPath('/')">Root</span>`;return}let r=`<span class="breadcrumb" onclick="setPath('/')">\u{1F3E0} Root</span>`,o="";n.forEach((s,i)=>{o+="/"+s;let a=o;r+=' <span class="breadcrumb-separator">/</span> ',r+=`<span class="breadcrumb" onclick="setPath('${a}')">${s}</span>`}),t.innerHTML=r}function Ns(e){let t=document.getElementById("path-input");t&&(t.value=e,Jn(e),h(`Path set to: ${e}`,"info",2e3))}function Zn(e){Ns(e)}function er(){return window._currentUsername||"username"}var Rs={images:{icon:"\u{1F5BC}\uFE0F",color:"#ff6961",label:"Images"},videos:{icon:"\u{1F3AC}",color:"#779ecb",label:"Videos"},audio:{icon:"\u{1F3B5}",color:"#77dd77",label:"Audio"},documents:{icon:"\u{1F4C4}",color:"#fdfd96",label:"Documents"},archives:{icon:"\u{1F4E6}",color:"#c5a3ff",label:"Archives"},code:{icon:"\u{1F4BB}",color:"#ffb347",label:"Code"}};function Ot(e){if(e===0)return"0 B";let t=1024,n=["B","KB","MB","GB","TB"],r=Math.floor(Math.log(e)/Math.log(t));return parseFloat((e/Math.pow(t,r)).toFixed(2))+" "+n[r]}function Fs(e,t){if(!e||typeof e!="object")return"";let n=Object.entries(e).filter(([p,u])=>u>0).sort((p,u)=>u[1]-p[1]);if(n.length===0)return"";let r=n.reduce((p,[u,d])=>p+d,0),o=t||r,s=o>r?o-r:0,i=Math.max(...n.map(([p,u])=>u),s),a=n.map(([p,u])=>{let d=Rs[p]||{icon:"\u{1F4C1}",color:"#888",label:p},l=o>0?(u/o*100).toFixed(1):"0",f=i>0?u/i*100:0;return`
      <div class="category-bar-item">
        <div class="category-bar-label">
          <span class="category-icon">${d.icon}</span>
          <span class="category-name">${d.label}</span>
          <span class="category-size">${Ot(u)}</span>
          <span class="category-percent">${l}%</span>
        </div>
        <div class="category-bar-track">
          <div class="category-bar-fill" style="width: ${f}%; background: ${d.color};"></div>
        </div>
      </div>
    `}).join(""),c="";if(s>0&&o>0){let p=(s/o*100).toFixed(1),u=i>0?s/i*100:0;c=`
      <div class="category-bar-item">
        <div class="category-bar-label">
          <span class="category-icon">\u{1F4C1}</span>
          <span class="category-name">Other</span>
          <span class="category-size">${Ot(s)}</span>
          <span class="category-percent">${p}%</span>
        </div>
        <div class="category-bar-track">
          <div class="category-bar-fill" style="width: ${u}%; background: #888;"></div>
        </div>
      </div>
    `}return`
    <div class="category-breakdown">
      <h3 style="margin-top: 2rem;">\u{1F4CA} Storage by Category</h3>
      <p style="color: var(--text-secondary); margin-top: 0.5rem; margin-bottom: 1rem;">
        Breakdown of ${Ot(r)} categorized across ${n.length} file types
      </p>
      <div class="category-bars">
        ${a}
        ${c}
      </div>
    </div>
  `}async function Us(){try{console.log("Loading schedule templates...");let e=await fetch("/api/schedules/templates");if(!e.ok)throw new Error(`HTTP ${e.status}: ${e.statusText}`);let t=await e.json();console.log("Templates loaded:",t);let n=document.getElementById("templates-list");if(!n)return;if(!t.templates||t.templates.length===0){n.innerHTML='<p style="color: var(--text-secondary);">No templates available</p>';return}n.innerHTML=t.templates.map(r=>{let o=JSON.stringify(r).replace(/'/g,"\\'");return`
        <div class="template-card ${r.recommended?"recommended":""}"
             onclick='applyScheduleTemplate(${o})'>
          <div class="template-icon">${r.icon}</div>
          <div class="template-name">${E(r.name)}</div>
          <div class="template-desc">${E(r.description)}</div>
          ${r.recommended?'<span class="template-badge">RECOMMENDED</span>':""}
        </div>
      `}).join("")}catch(e){console.error("Failed to load templates:",e);let t=document.getElementById("templates-list");t&&(t.innerHTML=`<p style="color: var(--danger);">Error loading templates: ${e.message}</p>`),h("Failed to load templates: "+e.message,"error")}}async function O(){try{console.log("[Schedule] Loading schedules...");let e=await fetch("/api/schedules");console.log("[Schedule] Schedules response status:",e.status);let t=await e.json();console.log("[Schedule] Schedules data:",t);let n=document.getElementById("schedules-list");if(console.log("[Schedule] Container found:",!!n),!n)return;if(!t.success||!t.schedules||t.schedules.length===0){n.innerHTML=`
        <div style="text-align: center; padding: 3rem; color: var(--text-secondary);">
          <div style="font-size: 3rem; margin-bottom: 1rem;">\u{1F4C5}</div>
          <p>No schedules yet</p>
          <p style="font-size: 0.875rem;">Click "New Schedule" or use a template to get started</p>
        </div>
      `;return}n.innerHTML=t.schedules.map(r=>{let o=r.next_run?tr(r.next_run):"Not scheduled",s=r.last_run?tr(r.last_run):"Never",i=r.enabled?"enabled":"disabled",a=r.enabled?"\u25CF Enabled":"\u25CB Disabled";return`
        <div class="schedule-card ${r.enabled?"":"disabled"}">
          <div class="schedule-header">
            <div>
              <div class="schedule-title">${E(r.name)}</div>
              ${r.description?`<div class="schedule-desc">${E(r.description)}</div>`:""}
            </div>
            <div class="schedule-actions">
              <button class="secondary" onclick="openScheduleModal('${r.id}')" title="Edit">
                \u270F\uFE0F
              </button>
              <button class="secondary" onclick="toggleScheduleEnabled('${r.id}', ${!r.enabled})"
                      title="${r.enabled?"Disable":"Enable"}">
                ${r.enabled?"\u23F8\uFE0F":"\u25B6\uFE0F"}
              </button>
              <button class="warning" onclick="runScheduleNow('${r.id}')" title="Run now">
                \u25B6\uFE0F Run
              </button>
              <button class="danger" onclick="deleteSchedule('${r.id}')" title="Delete schedule">
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
              <div class="schedule-info-value">${Ws(r)}</div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Time</div>
              <div class="schedule-info-value">${r.time_of_day}</div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Next Run</div>
              <div class="schedule-info-value">
                <span class="next-run-badge">\u23F0 ${o}</span>
              </div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Last Run</div>
              <div class="schedule-info-value">${s}</div>
            </div>
            <div class="schedule-info-item">
              <div class="schedule-info-label">Operations</div>
              <div class="schedule-info-value">${r.operations?.length??r.operation_ids?.length??0} selected</div>
            </div>
          </div>
          ${r.message?`
            <div class="conflict-warning">
              <div class="conflict-warning-text">\u26A0\uFE0F ${E(r.message)}</div>
            </div>
          `:""}
        </div>
      `}).join("")}catch(e){console.error("Failed to load schedules:",e),h("Failed to load schedules","error")}}async function nr(){let t=document.getElementById("schedule-id")?.value||"",r=document.getElementById("schedule-name")?.value||"",s=document.getElementById("schedule-description")?.value||"",a=document.getElementById("schedule-frequency")?.value||"",p=document.getElementById("schedule-time")?.value||"",d=document.getElementById("schedule-enabled")?.checked||!1,f=document.getElementById("schedule-notify")?.checked??!0,y=document.getElementById("schedule-wake")?.checked??!1,v=Array.from(document.querySelectorAll('input[name="operations"]:checked')).map(g=>g.value);if(!r||v.length===0||!p){h("Please fill in all required fields","error");return}let w={name:r,description:s,operations:v,frequency:a,time_of_day:p+":00",enabled:d,notify:f,wake_mac:y};if(a==="weekly"){let g=Array.from(document.querySelectorAll('input[name="days"]:checked')).map(x=>x.value);if(g.length===0){h("Please select at least one day of the week","error");return}w.days_of_week=g}else if(a==="monthly"){let g=document.getElementById("schedule-day"),x=parseInt(g?.value||"0");if(!x||x<1||x>28){h("Please enter a day between 1 and 28","error");return}w.day_of_month=x}try{let g=t?`/api/schedules/${t}`:"/api/schedules",b=await fetch(g,{method:t?"PUT":"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(w)}),$=await b.json();if(!b.ok||!$.success)throw new Error($.error||"Failed to save schedule");h(t?"Schedule updated!":"Schedule created!","success"),je(),O()}catch(g){console.error("Failed to save schedule:",g),h(g.message,"error")}}async function rr(e){if(confirm("Delete this schedule? This will unregister it from launchd."))try{let t=await fetch(`/api/schedules/${e}`,{method:"DELETE"}),n=await t.json();if(!t.ok||!n.success)throw new Error(n.error||"Failed to delete schedule");h("Schedule deleted","success"),O()}catch(t){console.error("Failed to delete schedule:",t),h(t.message,"error")}}async function or(e,t){try{let n=await fetch(`/api/schedules/${e}/enabled`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({enabled:t})}),r=await n.json();if(!n.ok||!r.success)throw new Error(r.error||"Failed to toggle schedule");h(t?"Schedule enabled":"Schedule disabled","success"),O()}catch(n){console.error("Failed to toggle schedule:",n),h(n.message,"error")}}async function sr(e){if(confirm("Run this schedule now? This will execute all operations immediately."))try{let t=await fetch(`/api/schedules/${e}/run-now`,{method:"POST"}),n=await t.json();if(!t.ok||!n.success)throw new Error(n.message||"Failed to run schedule");h("Schedule running...","success"),setTimeout(()=>O(),2e3),setTimeout(()=>O(),7e3)}catch(t){console.error("Failed to run schedule:",t),h(t.message,"error")}}function Ft(e=null){let t=document.getElementById("schedule-modal"),n=document.getElementById("schedule-modal-title"),r=document.getElementById("schedule-form");if(!t||!n)return Promise.resolve();r&&r.reset();let o=document.getElementById("schedule-id");return o&&(o.value=e||""),n.textContent=e?"Edit Schedule":"Create Schedule",Gs(),e?Vs(e):(t.classList.add("active"),Promise.resolve())}function je(){let e=document.getElementById("schedule-modal");e&&e.classList.remove("active")}async function Gs(){try{let t=await(await fetch("/api/maintenance/operations")).json(),n=document.getElementById("schedule-operations");if(!n)return;n.innerHTML=t.operations.map(r=>`
      <label class="operation-checkbox">
        <input type="checkbox" name="operations" value="${r.id}">
        <div class="operation-checkbox-label">
          <div class="operation-checkbox-name">${E(r.name)}</div>
          <div class="operation-checkbox-desc">${E(r.description||"")}</div>
        </div>
      </label>
    `).join("")}catch(e){console.error("Failed to load operations:",e)}}async function Vs(e){try{let n=await(await fetch(`/api/schedules/${e}`)).json();if(!n.success){h("Schedule not found","error"),je();return}let r=n.schedule,o=document.getElementById("schedule-name"),s=document.getElementById("schedule-description"),i=document.getElementById("schedule-frequency"),a=document.getElementById("schedule-time"),c=document.getElementById("schedule-enabled"),p=document.getElementById("schedule-notify"),u=document.getElementById("schedule-wake");if(o&&(o.value=r.name||""),s&&(s.value=r.description||""),i&&r.frequency&&(i.value=r.frequency),a&&r.time_of_day&&(a.value=r.time_of_day.substring(0,5)),c&&(c.checked=r.enabled),p&&(p.checked=r.notify??!0),u&&(u.checked=r.wake_mac??!1),(r.operations||[]).forEach(l=>{let f=document.querySelector(`input[name="operations"][value="${l}"]`);f&&(f.checked=!0)}),ir(),r.frequency==="weekly"&&r.days_of_week&&r.days_of_week.forEach(l=>{let f=document.querySelector(`input[name="days"][value="${l}"]`);f&&(f.checked=!0)}),r.frequency==="monthly"&&r.day_of_month){let l=document.getElementById("schedule-day");l&&(l.value=String(r.day_of_month))}let d=document.getElementById("schedule-modal");d&&d.classList.add("active")}catch(t){console.error("Failed to load schedule:",t),h("Failed to load schedule","error")}}function ir(){let t=document.getElementById("schedule-frequency")?.value||"",n=document.getElementById("days-selector"),r=document.getElementById("day-selector");n&&(n.style.display=t==="weekly"?"block":"none"),r&&(r.style.display=t==="monthly"?"block":"none")}function ar(e){Ft(),setTimeout(()=>{let t=document.getElementById("schedule-name"),n=document.getElementById("schedule-description"),r=document.getElementById("schedule-frequency"),o=document.getElementById("schedule-time");if(t&&(t.value=e.name),n&&(n.value=e.description),r&&(r.value=e.frequency),o&&(o.value=e.time_of_day.substring(0,5)),e.operations.forEach(s=>{let i=document.querySelector(`input[name="operations"][value="${s}"]`);i&&(i.checked=!0)}),ir(),e.days_of_week&&e.days_of_week.forEach(s=>{let i=document.querySelector(`input[name="days"][value="${s}"]`);i&&(i.checked=!0)}),e.day_of_month){let s=document.getElementById("schedule-day");s&&(s.value=e.day_of_month)}},100)}var Rt=null;function lr(){console.log("[Schedule] Tab shown, loading data..."),Us(),O(),Rt&&window.clearInterval(Rt),Rt=window.setInterval(()=>{let e=document.getElementById("schedule");e&&e.classList.contains("active")&&O()},1e4)}function Ws(e){return e.frequency==="daily"?"Daily":e.frequency==="weekly"?`Weekly (${e.days_of_week?.map(n=>n.substring(0,3).toUpperCase()).join(", ")||"No days"})`:e.frequency==="monthly"?`Monthly (Day ${e.day_of_month})`:e.frequency||"Unknown"}function tr(e){try{let t=new Date(e),n=new Date,r=t.getTime()-n.getTime(),o=Math.floor(r/(1e3*60*60*24)),s=Math.floor(r/(1e3*60*60));return r<0?t.toLocaleString():o===0&&s<24?`in ${s}h`:o<7?`in ${o}d`:t.toLocaleDateString()}catch{return e}}var Xe=class{constructor(t){this.apps=[];let n=document.getElementById(t);if(!n)throw new Error(`Container ${t} not found`);this.container=n,this.container.innerHTML=`
            <div class="app-uninstaller">
                <div class="search-bar">
                    <input type="text" id="app-search" placeholder="Search installed applications..." />
                    <button id="refresh-apps" class="secondary">Refresh</button>
                </div>
                <div class="app-list-header">
                    <span>Name</span>
                    <span>Size</span>
                    <span>Action</span>
                </div>
                <div id="app-list-content" class="app-list-content">
                    <div class="loading">Loading apps...</div>
                </div>
            </div>
        `,this.searchInput=this.container.querySelector("#app-search"),this.appList=this.container.querySelector("#app-list-content"),this.searchInput.addEventListener("input",()=>this.filterApps()),this.container.querySelector("#refresh-apps")?.addEventListener("click",()=>this.loadApps()),this.loadApps()}async loadApps(){this.appList.innerHTML='<div class="loading">Scanning applications...</div>';try{let t=await fetch("/api/apps");if(!t.ok)throw new Error("Failed to load apps");let n=await t.json();n.success?(this.apps=n.apps,this.renderApps(this.apps)):this.appList.innerHTML=`<div class="error">${n.error||"Unknown error"}</div>`}catch(t){this.appList.innerHTML=`<div class="error">Error loading apps: ${t}</div>`}}filterApps(){let t=this.searchInput.value.toLowerCase(),n=this.apps.filter(r=>r.name.toLowerCase().includes(t)||r.bundle_id.toLowerCase().includes(t));this.renderApps(n)}renderApps(t){if(t.length===0){this.appList.innerHTML='<div class="empty">No applications found</div>';return}this.appList.innerHTML="",t.forEach(n=>{let r=document.createElement("div");r.className="app-row",r.innerHTML=`
                <div class="app-name">
                    <div class="name">${n.name}</div>
                    <div class="sub">${n.version} \u2022 ${n.path}</div>
                </div>
                <div class="app-size">${n.size_display}</div>
                <div class="app-actions">
                    <button class="danger" data-app="${n.name}">Uninstall</button>
                </div>
            `,r.querySelector("button")?.addEventListener("click",()=>this.confirmUninstall(n)),this.appList.appendChild(r)})}async confirmUninstall(t){if(confirm(`Are you sure you want to uninstall ${t.name}? This will move the app and its data to Trash.`))try{let n=this.appList.querySelector(`button[data-app="${t.name}"]`);n&&(n.disabled=!0,n.textContent="Uninstalling...");let r=await fetch(`/api/apps/${encodeURIComponent(t.name)}/uninstall?dry_run=false`,{method:"POST"});if(!r.ok)throw new Error("Uninstall failed");let o=await r.json();o.success?(h(`Uninstalled ${t.name}. recovered ${this.formatBytes(o.bytes_recovered)}`,"success"),this.apps=this.apps.filter(s=>s.name!==t.name),this.renderApps(this.apps)):(h(`Failed to uninstall ${t.name}`,"error"),n&&(n.disabled=!1,n.textContent="Uninstall"))}catch(n){h(`Error: ${n}`,"error"),this.loadApps()}}formatBytes(t){if(t===0)return"0 B";let n=1024,r=["B","KB","MB","GB","TB"],o=Math.floor(Math.log(t)/Math.log(n));return parseFloat((t/Math.pow(n,o)).toFixed(1))+" "+r[o]}};var se=class extends Map{constructor(t,n=Ks){if(super(),Object.defineProperties(this,{_intern:{value:new Map},_key:{value:n}}),t!=null)for(let[r,o]of t)this.set(r,o)}get(t){return super.get(cr(this,t))}has(t){return super.has(cr(this,t))}set(t,n){return super.set(js(this,t),n)}delete(t){return super.delete(Xs(this,t))}};function cr({_intern:e,_key:t},n){let r=t(n);return e.has(r)?e.get(r):n}function js({_intern:e,_key:t},n){let r=t(n);return e.has(r)?e.get(r):(e.set(r,n),n)}function Xs({_intern:e,_key:t},n){let r=t(n);return e.has(r)&&(n=e.get(r),e.delete(r)),n}function Ks(e){return e!==null&&typeof e=="object"?e.valueOf():e}var Ys={value:()=>{}};function dr(){for(var e=0,t=arguments.length,n={},r;e<t;++e){if(!(r=arguments[e]+"")||r in n||/[\s.]/.test(r))throw new Error("illegal type: "+r);n[r]=[]}return new Ke(n)}function Ke(e){this._=e}function Qs(e,t){return e.trim().split(/^|\s+/).map(function(n){var r="",o=n.indexOf(".");if(o>=0&&(r=n.slice(o+1),n=n.slice(0,o)),n&&!t.hasOwnProperty(n))throw new Error("unknown type: "+n);return{type:n,name:r}})}Ke.prototype=dr.prototype={constructor:Ke,on:function(e,t){var n=this._,r=Qs(e+"",n),o,s=-1,i=r.length;if(arguments.length<2){for(;++s<i;)if((o=(e=r[s]).type)&&(o=Js(n[o],e.name)))return o;return}if(t!=null&&typeof t!="function")throw new Error("invalid callback: "+t);for(;++s<i;)if(o=(e=r[s]).type)n[o]=ur(n[o],e.name,t);else if(t==null)for(o in n)n[o]=ur(n[o],e.name,null);return this},copy:function(){var e={},t=this._;for(var n in t)e[n]=t[n].slice();return new Ke(e)},call:function(e,t){if((o=arguments.length-2)>0)for(var n=new Array(o),r=0,o,s;r<o;++r)n[r]=arguments[r+2];if(!this._.hasOwnProperty(e))throw new Error("unknown type: "+e);for(s=this._[e],r=0,o=s.length;r<o;++r)s[r].value.apply(t,n)},apply:function(e,t,n){if(!this._.hasOwnProperty(e))throw new Error("unknown type: "+e);for(var r=this._[e],o=0,s=r.length;o<s;++o)r[o].value.apply(t,n)}};function Js(e,t){for(var n=0,r=e.length,o;n<r;++n)if((o=e[n]).name===t)return o.value}function ur(e,t,n){for(var r=0,o=e.length;r<o;++r)if(e[r].name===t){e[r]=Ys,e=e.slice(0,r).concat(e.slice(r+1));break}return n!=null&&e.push({name:t,value:n}),e}var Ut=dr;var Ye="http://www.w3.org/1999/xhtml",Gt={svg:"http://www.w3.org/2000/svg",xhtml:Ye,xlink:"http://www.w3.org/1999/xlink",xml:"http://www.w3.org/XML/1998/namespace",xmlns:"http://www.w3.org/2000/xmlns/"};function N(e){var t=e+="",n=t.indexOf(":");return n>=0&&(t=e.slice(0,n))!=="xmlns"&&(e=e.slice(n+1)),Gt.hasOwnProperty(t)?{space:Gt[t],local:e}:e}function Zs(e){return function(){var t=this.ownerDocument,n=this.namespaceURI;return n===Ye&&t.documentElement.namespaceURI===Ye?t.createElement(e):t.createElementNS(n,e)}}function ei(e){return function(){return this.ownerDocument.createElementNS(e.space,e.local)}}function Qe(e){var t=N(e);return(t.local?ei:Zs)(t)}function ti(){}function Q(e){return e==null?ti:function(){return this.querySelector(e)}}function pr(e){typeof e!="function"&&(e=Q(e));for(var t=this._groups,n=t.length,r=new Array(n),o=0;o<n;++o)for(var s=t[o],i=s.length,a=r[o]=new Array(i),c,p,u=0;u<i;++u)(c=s[u])&&(p=e.call(c,c.__data__,u,s))&&("__data__"in c&&(p.__data__=c.__data__),a[u]=p);return new k(r,this._parents)}function Vt(e){return e==null?[]:Array.isArray(e)?e:Array.from(e)}function ni(){return[]}function ge(e){return e==null?ni:function(){return this.querySelectorAll(e)}}function ri(e){return function(){return Vt(e.apply(this,arguments))}}function fr(e){typeof e=="function"?e=ri(e):e=ge(e);for(var t=this._groups,n=t.length,r=[],o=[],s=0;s<n;++s)for(var i=t[s],a=i.length,c,p=0;p<a;++p)(c=i[p])&&(r.push(e.call(c,c.__data__,p,i)),o.push(c));return new k(r,o)}function ye(e){return function(){return this.matches(e)}}function Je(e){return function(t){return t.matches(e)}}var oi=Array.prototype.find;function si(e){return function(){return oi.call(this.children,e)}}function ii(){return this.firstElementChild}function mr(e){return this.select(e==null?ii:si(typeof e=="function"?e:Je(e)))}var ai=Array.prototype.filter;function li(){return Array.from(this.children)}function ci(e){return function(){return ai.call(this.children,e)}}function hr(e){return this.selectAll(e==null?li:ci(typeof e=="function"?e:Je(e)))}function gr(e){typeof e!="function"&&(e=ye(e));for(var t=this._groups,n=t.length,r=new Array(n),o=0;o<n;++o)for(var s=t[o],i=s.length,a=r[o]=[],c,p=0;p<i;++p)(c=s[p])&&e.call(c,c.__data__,p,s)&&a.push(c);return new k(r,this._parents)}function Ze(e){return new Array(e.length)}function yr(){return new k(this._enter||this._groups.map(Ze),this._parents)}function ve(e,t){this.ownerDocument=e.ownerDocument,this.namespaceURI=e.namespaceURI,this._next=null,this._parent=e,this.__data__=t}ve.prototype={constructor:ve,appendChild:function(e){return this._parent.insertBefore(e,this._next)},insertBefore:function(e,t){return this._parent.insertBefore(e,t)},querySelector:function(e){return this._parent.querySelector(e)},querySelectorAll:function(e){return this._parent.querySelectorAll(e)}};function vr(e){return function(){return e}}function ui(e,t,n,r,o,s){for(var i=0,a,c=t.length,p=s.length;i<p;++i)(a=t[i])?(a.__data__=s[i],r[i]=a):n[i]=new ve(e,s[i]);for(;i<c;++i)(a=t[i])&&(o[i]=a)}function di(e,t,n,r,o,s,i){var a,c,p=new Map,u=t.length,d=s.length,l=new Array(u),f;for(a=0;a<u;++a)(c=t[a])&&(l[a]=f=i.call(c,c.__data__,a,t)+"",p.has(f)?o[a]=c:p.set(f,c));for(a=0;a<d;++a)f=i.call(e,s[a],a,s)+"",(c=p.get(f))?(r[a]=c,c.__data__=s[a],p.delete(f)):n[a]=new ve(e,s[a]);for(a=0;a<u;++a)(c=t[a])&&p.get(l[a])===c&&(o[a]=c)}function pi(e){return e.__data__}function xr(e,t){if(!arguments.length)return Array.from(this,pi);var n=t?di:ui,r=this._parents,o=this._groups;typeof e!="function"&&(e=vr(e));for(var s=o.length,i=new Array(s),a=new Array(s),c=new Array(s),p=0;p<s;++p){var u=r[p],d=o[p],l=d.length,f=fi(e.call(u,u&&u.__data__,p,r)),m=f.length,y=a[p]=new Array(m),v=i[p]=new Array(m),w=c[p]=new Array(l);n(u,d,y,v,w,f,t);for(var g=0,x=0,b,$;g<m;++g)if(b=y[g]){for(g>=x&&(x=g+1);!($=v[x])&&++x<m;);b._next=$||null}}return i=new k(i,r),i._enter=a,i._exit=c,i}function fi(e){return typeof e=="object"&&"length"in e?e:Array.from(e)}function wr(){return new k(this._exit||this._groups.map(Ze),this._parents)}function br(e,t,n){var r=this.enter(),o=this,s=this.exit();return typeof e=="function"?(r=e(r),r&&(r=r.selection())):r=r.append(e+""),t!=null&&(o=t(o),o&&(o=o.selection())),n==null?s.remove():n(s),r&&o?r.merge(o).order():o}function Er(e){for(var t=e.selection?e.selection():e,n=this._groups,r=t._groups,o=n.length,s=r.length,i=Math.min(o,s),a=new Array(o),c=0;c<i;++c)for(var p=n[c],u=r[c],d=p.length,l=a[c]=new Array(d),f,m=0;m<d;++m)(f=p[m]||u[m])&&(l[m]=f);for(;c<o;++c)a[c]=n[c];return new k(a,this._parents)}function kr(){for(var e=this._groups,t=-1,n=e.length;++t<n;)for(var r=e[t],o=r.length-1,s=r[o],i;--o>=0;)(i=r[o])&&(s&&i.compareDocumentPosition(s)^4&&s.parentNode.insertBefore(i,s),s=i);return this}function _r(e){e||(e=mi);function t(d,l){return d&&l?e(d.__data__,l.__data__):!d-!l}for(var n=this._groups,r=n.length,o=new Array(r),s=0;s<r;++s){for(var i=n[s],a=i.length,c=o[s]=new Array(a),p,u=0;u<a;++u)(p=i[u])&&(c[u]=p);c.sort(t)}return new k(o,this._parents).order()}function mi(e,t){return e<t?-1:e>t?1:e>=t?0:NaN}function Sr(){var e=arguments[0];return arguments[0]=this,e.apply(null,arguments),this}function Tr(){return Array.from(this)}function $r(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],o=0,s=r.length;o<s;++o){var i=r[o];if(i)return i}return null}function Ir(){let e=0;for(let t of this)++e;return e}function Mr(){return!this.node()}function Lr(e){for(var t=this._groups,n=0,r=t.length;n<r;++n)for(var o=t[n],s=0,i=o.length,a;s<i;++s)(a=o[s])&&e.call(a,a.__data__,s,o);return this}function hi(e){return function(){this.removeAttribute(e)}}function gi(e){return function(){this.removeAttributeNS(e.space,e.local)}}function yi(e,t){return function(){this.setAttribute(e,t)}}function vi(e,t){return function(){this.setAttributeNS(e.space,e.local,t)}}function xi(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttribute(e):this.setAttribute(e,n)}}function wi(e,t){return function(){var n=t.apply(this,arguments);n==null?this.removeAttributeNS(e.space,e.local):this.setAttributeNS(e.space,e.local,n)}}function Cr(e,t){var n=N(e);if(arguments.length<2){var r=this.node();return n.local?r.getAttributeNS(n.space,n.local):r.getAttribute(n)}return this.each((t==null?n.local?gi:hi:typeof t=="function"?n.local?wi:xi:n.local?vi:yi)(n,t))}function et(e){return e.ownerDocument&&e.ownerDocument.defaultView||e.document&&e||e.defaultView}function bi(e){return function(){this.style.removeProperty(e)}}function Ei(e,t,n){return function(){this.style.setProperty(e,t,n)}}function ki(e,t,n){return function(){var r=t.apply(this,arguments);r==null?this.style.removeProperty(e):this.style.setProperty(e,r,n)}}function Br(e,t,n){return arguments.length>1?this.each((t==null?bi:typeof t=="function"?ki:Ei)(e,t,n??"")):G(this.node(),e)}function G(e,t){return e.style.getPropertyValue(t)||et(e).getComputedStyle(e,null).getPropertyValue(t)}function _i(e){return function(){delete this[e]}}function Si(e,t){return function(){this[e]=t}}function Ti(e,t){return function(){var n=t.apply(this,arguments);n==null?delete this[e]:this[e]=n}}function Ar(e,t){return arguments.length>1?this.each((t==null?_i:typeof t=="function"?Ti:Si)(e,t)):this.node()[e]}function Hr(e){return e.trim().split(/^|\s+/)}function Wt(e){return e.classList||new zr(e)}function zr(e){this._node=e,this._names=Hr(e.getAttribute("class")||"")}zr.prototype={add:function(e){var t=this._names.indexOf(e);t<0&&(this._names.push(e),this._node.setAttribute("class",this._names.join(" ")))},remove:function(e){var t=this._names.indexOf(e);t>=0&&(this._names.splice(t,1),this._node.setAttribute("class",this._names.join(" ")))},contains:function(e){return this._names.indexOf(e)>=0}};function Dr(e,t){for(var n=Wt(e),r=-1,o=t.length;++r<o;)n.add(t[r])}function qr(e,t){for(var n=Wt(e),r=-1,o=t.length;++r<o;)n.remove(t[r])}function $i(e){return function(){Dr(this,e)}}function Ii(e){return function(){qr(this,e)}}function Mi(e,t){return function(){(t.apply(this,arguments)?Dr:qr)(this,e)}}function Pr(e,t){var n=Hr(e+"");if(arguments.length<2){for(var r=Wt(this.node()),o=-1,s=n.length;++o<s;)if(!r.contains(n[o]))return!1;return!0}return this.each((typeof t=="function"?Mi:t?$i:Ii)(n,t))}function Li(){this.textContent=""}function Ci(e){return function(){this.textContent=e}}function Bi(e){return function(){var t=e.apply(this,arguments);this.textContent=t??""}}function Or(e){return arguments.length?this.each(e==null?Li:(typeof e=="function"?Bi:Ci)(e)):this.node().textContent}function Ai(){this.innerHTML=""}function Hi(e){return function(){this.innerHTML=e}}function zi(e){return function(){var t=e.apply(this,arguments);this.innerHTML=t??""}}function Nr(e){return arguments.length?this.each(e==null?Ai:(typeof e=="function"?zi:Hi)(e)):this.node().innerHTML}function Di(){this.nextSibling&&this.parentNode.appendChild(this)}function Rr(){return this.each(Di)}function qi(){this.previousSibling&&this.parentNode.insertBefore(this,this.parentNode.firstChild)}function Fr(){return this.each(qi)}function Ur(e){var t=typeof e=="function"?e:Qe(e);return this.select(function(){return this.appendChild(t.apply(this,arguments))})}function Pi(){return null}function Gr(e,t){var n=typeof e=="function"?e:Qe(e),r=t==null?Pi:typeof t=="function"?t:Q(t);return this.select(function(){return this.insertBefore(n.apply(this,arguments),r.apply(this,arguments)||null)})}function Oi(){var e=this.parentNode;e&&e.removeChild(this)}function Vr(){return this.each(Oi)}function Ni(){var e=this.cloneNode(!1),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Ri(){var e=this.cloneNode(!0),t=this.parentNode;return t?t.insertBefore(e,this.nextSibling):e}function Wr(e){return this.select(e?Ri:Ni)}function jr(e){return arguments.length?this.property("__data__",e):this.node().__data__}function Fi(e){return function(t){e.call(this,t,this.__data__)}}function Ui(e){return e.trim().split(/^|\s+/).map(function(t){var n="",r=t.indexOf(".");return r>=0&&(n=t.slice(r+1),t=t.slice(0,r)),{type:t,name:n}})}function Gi(e){return function(){var t=this.__on;if(t){for(var n=0,r=-1,o=t.length,s;n<o;++n)s=t[n],(!e.type||s.type===e.type)&&s.name===e.name?this.removeEventListener(s.type,s.listener,s.options):t[++r]=s;++r?t.length=r:delete this.__on}}}function Vi(e,t,n){return function(){var r=this.__on,o,s=Fi(t);if(r){for(var i=0,a=r.length;i<a;++i)if((o=r[i]).type===e.type&&o.name===e.name){this.removeEventListener(o.type,o.listener,o.options),this.addEventListener(o.type,o.listener=s,o.options=n),o.value=t;return}}this.addEventListener(e.type,s,n),o={type:e.type,name:e.name,value:t,listener:s,options:n},r?r.push(o):this.__on=[o]}}function Xr(e,t,n){var r=Ui(e+""),o,s=r.length,i;if(arguments.length<2){var a=this.node().__on;if(a){for(var c=0,p=a.length,u;c<p;++c)for(o=0,u=a[c];o<s;++o)if((i=r[o]).type===u.type&&i.name===u.name)return u.value}return}for(a=t?Vi:Gi,o=0;o<s;++o)this.each(a(r[o],t,n));return this}function Kr(e,t,n){var r=et(e),o=r.CustomEvent;typeof o=="function"?o=new o(t,n):(o=r.document.createEvent("Event"),n?(o.initEvent(t,n.bubbles,n.cancelable),o.detail=n.detail):o.initEvent(t,!1,!1)),e.dispatchEvent(o)}function Wi(e,t){return function(){return Kr(this,e,t)}}function ji(e,t){return function(){return Kr(this,e,t.apply(this,arguments))}}function Yr(e,t){return this.each((typeof t=="function"?ji:Wi)(e,t))}function*Qr(){for(var e=this._groups,t=0,n=e.length;t<n;++t)for(var r=e[t],o=0,s=r.length,i;o<s;++o)(i=r[o])&&(yield i)}var jt=[null];function k(e,t){this._groups=e,this._parents=t}function Jr(){return new k([[document.documentElement]],jt)}function Xi(){return this}k.prototype=Jr.prototype={constructor:k,select:pr,selectAll:fr,selectChild:mr,selectChildren:hr,filter:gr,data:xr,enter:yr,exit:wr,join:br,merge:Er,selection:Xi,order:kr,sort:_r,call:Sr,nodes:Tr,node:$r,size:Ir,empty:Mr,each:Lr,attr:Cr,style:Br,property:Ar,classed:Pr,text:Or,html:Nr,raise:Rr,lower:Fr,append:Ur,insert:Gr,remove:Vr,clone:Wr,datum:jr,on:Xr,dispatch:Yr,[Symbol.iterator]:Qr};var R=Jr;function Xt(e){return typeof e=="string"?new k([[document.querySelector(e)]],[document.documentElement]):new k([[e]],jt)}function tt(e,t,n){e.prototype=t.prototype=n,n.constructor=e}function Kt(e,t){var n=Object.create(e.prototype);for(var r in t)n[r]=t[r];return n}function be(){}var xe=.7,ot=1/xe,ie="\\s*([+-]?\\d+)\\s*",we="\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*",D="\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*",Ki=/^#([0-9a-f]{3,8})$/,Yi=new RegExp(`^rgb\\(${ie},${ie},${ie}\\)$`),Qi=new RegExp(`^rgb\\(${D},${D},${D}\\)$`),Ji=new RegExp(`^rgba\\(${ie},${ie},${ie},${we}\\)$`),Zi=new RegExp(`^rgba\\(${D},${D},${D},${we}\\)$`),ea=new RegExp(`^hsl\\(${we},${D},${D}\\)$`),ta=new RegExp(`^hsla\\(${we},${D},${D},${we}\\)$`),Zr={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074};tt(be,V,{copy(e){return Object.assign(new this.constructor,this,e)},displayable(){return this.rgb().displayable()},hex:eo,formatHex:eo,formatHex8:na,formatHsl:ra,formatRgb:to,toString:to});function eo(){return this.rgb().formatHex()}function na(){return this.rgb().formatHex8()}function ra(){return ao(this).formatHsl()}function to(){return this.rgb().formatRgb()}function V(e){var t,n;return e=(e+"").trim().toLowerCase(),(t=Ki.exec(e))?(n=t[1].length,t=parseInt(t[1],16),n===6?no(t):n===3?new M(t>>8&15|t>>4&240,t>>4&15|t&240,(t&15)<<4|t&15,1):n===8?nt(t>>24&255,t>>16&255,t>>8&255,(t&255)/255):n===4?nt(t>>12&15|t>>8&240,t>>8&15|t>>4&240,t>>4&15|t&240,((t&15)<<4|t&15)/255):null):(t=Yi.exec(e))?new M(t[1],t[2],t[3],1):(t=Qi.exec(e))?new M(t[1]*255/100,t[2]*255/100,t[3]*255/100,1):(t=Ji.exec(e))?nt(t[1],t[2],t[3],t[4]):(t=Zi.exec(e))?nt(t[1]*255/100,t[2]*255/100,t[3]*255/100,t[4]):(t=ea.exec(e))?so(t[1],t[2]/100,t[3]/100,1):(t=ta.exec(e))?so(t[1],t[2]/100,t[3]/100,t[4]):Zr.hasOwnProperty(e)?no(Zr[e]):e==="transparent"?new M(NaN,NaN,NaN,0):null}function no(e){return new M(e>>16&255,e>>8&255,e&255,1)}function nt(e,t,n,r){return r<=0&&(e=t=n=NaN),new M(e,t,n,r)}function oa(e){return e instanceof be||(e=V(e)),e?(e=e.rgb(),new M(e.r,e.g,e.b,e.opacity)):new M}function ae(e,t,n,r){return arguments.length===1?oa(e):new M(e,t,n,r??1)}function M(e,t,n,r){this.r=+e,this.g=+t,this.b=+n,this.opacity=+r}tt(M,ae,Kt(be,{brighter(e){return e=e==null?ot:Math.pow(ot,e),new M(this.r*e,this.g*e,this.b*e,this.opacity)},darker(e){return e=e==null?xe:Math.pow(xe,e),new M(this.r*e,this.g*e,this.b*e,this.opacity)},rgb(){return this},clamp(){return new M(Z(this.r),Z(this.g),Z(this.b),st(this.opacity))},displayable(){return-.5<=this.r&&this.r<255.5&&-.5<=this.g&&this.g<255.5&&-.5<=this.b&&this.b<255.5&&0<=this.opacity&&this.opacity<=1},hex:ro,formatHex:ro,formatHex8:sa,formatRgb:oo,toString:oo}));function ro(){return`#${J(this.r)}${J(this.g)}${J(this.b)}`}function sa(){return`#${J(this.r)}${J(this.g)}${J(this.b)}${J((isNaN(this.opacity)?1:this.opacity)*255)}`}function oo(){let e=st(this.opacity);return`${e===1?"rgb(":"rgba("}${Z(this.r)}, ${Z(this.g)}, ${Z(this.b)}${e===1?")":`, ${e})`}`}function st(e){return isNaN(e)?1:Math.max(0,Math.min(1,e))}function Z(e){return Math.max(0,Math.min(255,Math.round(e)||0))}function J(e){return e=Z(e),(e<16?"0":"")+e.toString(16)}function so(e,t,n,r){return r<=0?e=t=n=NaN:n<=0||n>=1?e=t=NaN:t<=0&&(e=NaN),new A(e,t,n,r)}function ao(e){if(e instanceof A)return new A(e.h,e.s,e.l,e.opacity);if(e instanceof be||(e=V(e)),!e)return new A;if(e instanceof A)return e;e=e.rgb();var t=e.r/255,n=e.g/255,r=e.b/255,o=Math.min(t,n,r),s=Math.max(t,n,r),i=NaN,a=s-o,c=(s+o)/2;return a?(t===s?i=(n-r)/a+(n<r)*6:n===s?i=(r-t)/a+2:i=(t-n)/a+4,a/=c<.5?s+o:2-s-o,i*=60):a=c>0&&c<1?0:i,new A(i,a,c,e.opacity)}function lo(e,t,n,r){return arguments.length===1?ao(e):new A(e,t,n,r??1)}function A(e,t,n,r){this.h=+e,this.s=+t,this.l=+n,this.opacity=+r}tt(A,lo,Kt(be,{brighter(e){return e=e==null?ot:Math.pow(ot,e),new A(this.h,this.s,this.l*e,this.opacity)},darker(e){return e=e==null?xe:Math.pow(xe,e),new A(this.h,this.s,this.l*e,this.opacity)},rgb(){var e=this.h%360+(this.h<0)*360,t=isNaN(e)||isNaN(this.s)?0:this.s,n=this.l,r=n+(n<.5?n:1-n)*t,o=2*n-r;return new M(Yt(e>=240?e-240:e+120,o,r),Yt(e,o,r),Yt(e<120?e+240:e-120,o,r),this.opacity)},clamp(){return new A(io(this.h),rt(this.s),rt(this.l),st(this.opacity))},displayable(){return(0<=this.s&&this.s<=1||isNaN(this.s))&&0<=this.l&&this.l<=1&&0<=this.opacity&&this.opacity<=1},formatHsl(){let e=st(this.opacity);return`${e===1?"hsl(":"hsla("}${io(this.h)}, ${rt(this.s)*100}%, ${rt(this.l)*100}%${e===1?")":`, ${e})`}`}}));function io(e){return e=(e||0)%360,e<0?e+360:e}function rt(e){return Math.max(0,Math.min(1,e||0))}function Yt(e,t,n){return(e<60?t+(n-t)*e/60:e<180?n:e<240?t+(n-t)*(240-e)/60:t)*255}function Qt(e,t,n,r,o){var s=e*e,i=s*e;return((1-3*e+3*s-i)*t+(4-6*s+3*i)*n+(1+3*e+3*s-3*i)*r+i*o)/6}function co(e){var t=e.length-1;return function(n){var r=n<=0?n=0:n>=1?(n=1,t-1):Math.floor(n*t),o=e[r],s=e[r+1],i=r>0?e[r-1]:2*o-s,a=r<t-1?e[r+2]:2*s-o;return Qt((n-r/t)*t,i,o,s,a)}}function uo(e){var t=e.length;return function(n){var r=Math.floor(((n%=1)<0?++n:n)*t),o=e[(r+t-1)%t],s=e[r%t],i=e[(r+1)%t],a=e[(r+2)%t];return Qt((n-r/t)*t,o,s,i,a)}}var Jt=e=>()=>e;function ia(e,t){return function(n){return e+n*t}}function aa(e,t,n){return e=Math.pow(e,n),t=Math.pow(t,n)-e,n=1/n,function(r){return Math.pow(e+r*t,n)}}function po(e){return(e=+e)==1?it:function(t,n){return n-t?aa(t,n,e):Jt(isNaN(t)?n:t)}}function it(e,t){var n=t-e;return n?ia(e,n):Jt(isNaN(e)?t:e)}var at=function e(t){var n=po(t);function r(o,s){var i=n((o=ae(o)).r,(s=ae(s)).r),a=n(o.g,s.g),c=n(o.b,s.b),p=it(o.opacity,s.opacity);return function(u){return o.r=i(u),o.g=a(u),o.b=c(u),o.opacity=p(u),o+""}}return r.gamma=e,r}(1);function fo(e){return function(t){var n=t.length,r=new Array(n),o=new Array(n),s=new Array(n),i,a;for(i=0;i<n;++i)a=ae(t[i]),r[i]=a.r||0,o[i]=a.g||0,s[i]=a.b||0;return r=e(r),o=e(o),s=e(s),a.opacity=1,function(c){return a.r=r(c),a.g=o(c),a.b=s(c),a+""}}}var la=fo(co),ca=fo(uo);function C(e,t){return e=+e,t=+t,function(n){return e*(1-n)+t*n}}var en=/[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g,Zt=new RegExp(en.source,"g");function ua(e){return function(){return e}}function da(e){return function(t){return e(t)+""}}function tn(e,t){var n=en.lastIndex=Zt.lastIndex=0,r,o,s,i=-1,a=[],c=[];for(e=e+"",t=t+"";(r=en.exec(e))&&(o=Zt.exec(t));)(s=o.index)>n&&(s=t.slice(n,s),a[i]?a[i]+=s:a[++i]=s),(r=r[0])===(o=o[0])?a[i]?a[i]+=o:a[++i]=o:(a[++i]=null,c.push({i,x:C(r,o)})),n=Zt.lastIndex;return n<t.length&&(s=t.slice(n),a[i]?a[i]+=s:a[++i]=s),a.length<2?c[0]?da(c[0].x):ua(t):(t=c.length,function(p){for(var u=0,d;u<t;++u)a[(d=c[u]).i]=d.x(p);return a.join("")})}var mo=180/Math.PI,lt={translateX:0,translateY:0,rotate:0,skewX:0,scaleX:1,scaleY:1};function nn(e,t,n,r,o,s){var i,a,c;return(i=Math.sqrt(e*e+t*t))&&(e/=i,t/=i),(c=e*n+t*r)&&(n-=e*c,r-=t*c),(a=Math.sqrt(n*n+r*r))&&(n/=a,r/=a,c/=a),e*r<t*n&&(e=-e,t=-t,c=-c,i=-i),{translateX:o,translateY:s,rotate:Math.atan2(t,e)*mo,skewX:Math.atan(c)*mo,scaleX:i,scaleY:a}}var ct;function ho(e){let t=new(typeof DOMMatrix=="function"?DOMMatrix:WebKitCSSMatrix)(e+"");return t.isIdentity?lt:nn(t.a,t.b,t.c,t.d,t.e,t.f)}function go(e){return e==null?lt:(ct||(ct=document.createElementNS("http://www.w3.org/2000/svg","g")),ct.setAttribute("transform",e),(e=ct.transform.baseVal.consolidate())?(e=e.matrix,nn(e.a,e.b,e.c,e.d,e.e,e.f)):lt)}function yo(e,t,n,r){function o(p){return p.length?p.pop()+" ":""}function s(p,u,d,l,f,m){if(p!==d||u!==l){var y=f.push("translate(",null,t,null,n);m.push({i:y-4,x:C(p,d)},{i:y-2,x:C(u,l)})}else(d||l)&&f.push("translate("+d+t+l+n)}function i(p,u,d,l){p!==u?(p-u>180?u+=360:u-p>180&&(p+=360),l.push({i:d.push(o(d)+"rotate(",null,r)-2,x:C(p,u)})):u&&d.push(o(d)+"rotate("+u+r)}function a(p,u,d,l){p!==u?l.push({i:d.push(o(d)+"skewX(",null,r)-2,x:C(p,u)}):u&&d.push(o(d)+"skewX("+u+r)}function c(p,u,d,l,f,m){if(p!==d||u!==l){var y=f.push(o(f)+"scale(",null,",",null,")");m.push({i:y-4,x:C(p,d)},{i:y-2,x:C(u,l)})}else(d!==1||l!==1)&&f.push(o(f)+"scale("+d+","+l+")")}return function(p,u){var d=[],l=[];return p=e(p),u=e(u),s(p.translateX,p.translateY,u.translateX,u.translateY,d,l),i(p.rotate,u.rotate,d,l),a(p.skewX,u.skewX,d,l),c(p.scaleX,p.scaleY,u.scaleX,u.scaleY,d,l),p=u=null,function(f){for(var m=-1,y=l.length,v;++m<y;)d[(v=l[m]).i]=v.x(f);return d.join("")}}}var rn=yo(ho,"px, ","px)","deg)"),on=yo(go,", ",")",")");var le=0,ke=0,Ee=0,xo=1e3,ut,_e,dt=0,ee=0,pt=0,Se=typeof performance=="object"&&performance.now?performance:Date,wo=typeof window=="object"&&window.requestAnimationFrame?window.requestAnimationFrame.bind(window):function(e){setTimeout(e,17)};function $e(){return ee||(wo(pa),ee=Se.now()+pt)}function pa(){ee=0}function Te(){this._call=this._time=this._next=null}Te.prototype=ft.prototype={constructor:Te,restart:function(e,t,n){if(typeof e!="function")throw new TypeError("callback is not a function");n=(n==null?$e():+n)+(t==null?0:+t),!this._next&&_e!==this&&(_e?_e._next=this:ut=this,_e=this),this._call=e,this._time=n,sn()},stop:function(){this._call&&(this._call=null,this._time=1/0,sn())}};function ft(e,t,n){var r=new Te;return r.restart(e,t,n),r}function bo(){$e(),++le;for(var e=ut,t;e;)(t=ee-e._time)>=0&&e._call.call(void 0,t),e=e._next;--le}function vo(){ee=(dt=Se.now())+pt,le=ke=0;try{bo()}finally{le=0,ma(),ee=0}}function fa(){var e=Se.now(),t=e-dt;t>xo&&(pt-=t,dt=e)}function ma(){for(var e,t=ut,n,r=1/0;t;)t._call?(r>t._time&&(r=t._time),e=t,t=t._next):(n=t._next,t._next=null,t=e?e._next=n:ut=n);_e=e,sn(r)}function sn(e){if(!le){ke&&(ke=clearTimeout(ke));var t=e-ee;t>24?(e<1/0&&(ke=setTimeout(vo,e-Se.now()-pt)),Ee&&(Ee=clearInterval(Ee))):(Ee||(dt=Se.now(),Ee=setInterval(fa,xo)),le=1,wo(vo))}}function mt(e,t,n){var r=new Te;return t=t==null?0:+t,r.restart(o=>{r.stop(),e(o+t)},t,n),r}var ha=Ut("start","end","cancel","interrupt"),ga=[],_o=0,Eo=1,gt=2,ht=3,ko=4,yt=5,Ie=6;function W(e,t,n,r,o,s){var i=e.__transition;if(!i)e.__transition={};else if(n in i)return;ya(e,n,{name:t,index:r,group:o,on:ha,tween:ga,time:s.time,delay:s.delay,duration:s.duration,ease:s.ease,timer:null,state:_o})}function Me(e,t){var n=_(e,t);if(n.state>_o)throw new Error("too late; already scheduled");return n}function T(e,t){var n=_(e,t);if(n.state>ht)throw new Error("too late; already running");return n}function _(e,t){var n=e.__transition;if(!n||!(n=n[t]))throw new Error("transition not found");return n}function ya(e,t,n){var r=e.__transition,o;r[t]=n,n.timer=ft(s,0,n.time);function s(p){n.state=Eo,n.timer.restart(i,n.delay,n.time),n.delay<=p&&i(p-n.delay)}function i(p){var u,d,l,f;if(n.state!==Eo)return c();for(u in r)if(f=r[u],f.name===n.name){if(f.state===ht)return mt(i);f.state===ko?(f.state=Ie,f.timer.stop(),f.on.call("interrupt",e,e.__data__,f.index,f.group),delete r[u]):+u<t&&(f.state=Ie,f.timer.stop(),f.on.call("cancel",e,e.__data__,f.index,f.group),delete r[u])}if(mt(function(){n.state===ht&&(n.state=ko,n.timer.restart(a,n.delay,n.time),a(p))}),n.state=gt,n.on.call("start",e,e.__data__,n.index,n.group),n.state===gt){for(n.state=ht,o=new Array(l=n.tween.length),u=0,d=-1;u<l;++u)(f=n.tween[u].value.call(e,e.__data__,n.index,n.group))&&(o[++d]=f);o.length=d+1}}function a(p){for(var u=p<n.duration?n.ease.call(null,p/n.duration):(n.timer.restart(c),n.state=yt,1),d=-1,l=o.length;++d<l;)o[d].call(e,u);n.state===yt&&(n.on.call("end",e,e.__data__,n.index,n.group),c())}function c(){n.state=Ie,n.timer.stop(),delete r[t];for(var p in r)return;delete e.__transition}}function vt(e,t){var n=e.__transition,r,o,s=!0,i;if(n){t=t==null?null:t+"";for(i in n){if((r=n[i]).name!==t){s=!1;continue}o=r.state>gt&&r.state<yt,r.state=Ie,r.timer.stop(),r.on.call(o?"interrupt":"cancel",e,e.__data__,r.index,r.group),delete n[i]}s&&delete e.__transition}}function So(e){return this.each(function(){vt(this,e)})}function va(e,t){var n,r;return function(){var o=T(this,e),s=o.tween;if(s!==n){r=n=s;for(var i=0,a=r.length;i<a;++i)if(r[i].name===t){r=r.slice(),r.splice(i,1);break}}o.tween=r}}function xa(e,t,n){var r,o;if(typeof n!="function")throw new Error;return function(){var s=T(this,e),i=s.tween;if(i!==r){o=(r=i).slice();for(var a={name:t,value:n},c=0,p=o.length;c<p;++c)if(o[c].name===t){o[c]=a;break}c===p&&o.push(a)}s.tween=o}}function To(e,t){var n=this._id;if(e+="",arguments.length<2){for(var r=_(this.node(),n).tween,o=0,s=r.length,i;o<s;++o)if((i=r[o]).name===e)return i.value;return null}return this.each((t==null?va:xa)(n,e,t))}function ce(e,t,n){var r=e._id;return e.each(function(){var o=T(this,r);(o.value||(o.value={}))[t]=n.apply(this,arguments)}),function(o){return _(o,r).value[t]}}function xt(e,t){var n;return(typeof t=="number"?C:t instanceof V?at:(n=V(t))?(t=n,at):tn)(e,t)}function wa(e){return function(){this.removeAttribute(e)}}function ba(e){return function(){this.removeAttributeNS(e.space,e.local)}}function Ea(e,t,n){var r,o=n+"",s;return function(){var i=this.getAttribute(e);return i===o?null:i===r?s:s=t(r=i,n)}}function ka(e,t,n){var r,o=n+"",s;return function(){var i=this.getAttributeNS(e.space,e.local);return i===o?null:i===r?s:s=t(r=i,n)}}function _a(e,t,n){var r,o,s;return function(){var i,a=n(this),c;return a==null?void this.removeAttribute(e):(i=this.getAttribute(e),c=a+"",i===c?null:i===r&&c===o?s:(o=c,s=t(r=i,a)))}}function Sa(e,t,n){var r,o,s;return function(){var i,a=n(this),c;return a==null?void this.removeAttributeNS(e.space,e.local):(i=this.getAttributeNS(e.space,e.local),c=a+"",i===c?null:i===r&&c===o?s:(o=c,s=t(r=i,a)))}}function $o(e,t){var n=N(e),r=n==="transform"?on:xt;return this.attrTween(e,typeof t=="function"?(n.local?Sa:_a)(n,r,ce(this,"attr."+e,t)):t==null?(n.local?ba:wa)(n):(n.local?ka:Ea)(n,r,t))}function Ta(e,t){return function(n){this.setAttribute(e,t.call(this,n))}}function $a(e,t){return function(n){this.setAttributeNS(e.space,e.local,t.call(this,n))}}function Ia(e,t){var n,r;function o(){var s=t.apply(this,arguments);return s!==r&&(n=(r=s)&&$a(e,s)),n}return o._value=t,o}function Ma(e,t){var n,r;function o(){var s=t.apply(this,arguments);return s!==r&&(n=(r=s)&&Ta(e,s)),n}return o._value=t,o}function Io(e,t){var n="attr."+e;if(arguments.length<2)return(n=this.tween(n))&&n._value;if(t==null)return this.tween(n,null);if(typeof t!="function")throw new Error;var r=N(e);return this.tween(n,(r.local?Ia:Ma)(r,t))}function La(e,t){return function(){Me(this,e).delay=+t.apply(this,arguments)}}function Ca(e,t){return t=+t,function(){Me(this,e).delay=t}}function Mo(e){var t=this._id;return arguments.length?this.each((typeof e=="function"?La:Ca)(t,e)):_(this.node(),t).delay}function Ba(e,t){return function(){T(this,e).duration=+t.apply(this,arguments)}}function Aa(e,t){return t=+t,function(){T(this,e).duration=t}}function Lo(e){var t=this._id;return arguments.length?this.each((typeof e=="function"?Ba:Aa)(t,e)):_(this.node(),t).duration}function Ha(e,t){if(typeof t!="function")throw new Error;return function(){T(this,e).ease=t}}function Co(e){var t=this._id;return arguments.length?this.each(Ha(t,e)):_(this.node(),t).ease}function za(e,t){return function(){var n=t.apply(this,arguments);if(typeof n!="function")throw new Error;T(this,e).ease=n}}function Bo(e){if(typeof e!="function")throw new Error;return this.each(za(this._id,e))}function Ao(e){typeof e!="function"&&(e=ye(e));for(var t=this._groups,n=t.length,r=new Array(n),o=0;o<n;++o)for(var s=t[o],i=s.length,a=r[o]=[],c,p=0;p<i;++p)(c=s[p])&&e.call(c,c.__data__,p,s)&&a.push(c);return new I(r,this._parents,this._name,this._id)}function Ho(e){if(e._id!==this._id)throw new Error;for(var t=this._groups,n=e._groups,r=t.length,o=n.length,s=Math.min(r,o),i=new Array(r),a=0;a<s;++a)for(var c=t[a],p=n[a],u=c.length,d=i[a]=new Array(u),l,f=0;f<u;++f)(l=c[f]||p[f])&&(d[f]=l);for(;a<r;++a)i[a]=t[a];return new I(i,this._parents,this._name,this._id)}function Da(e){return(e+"").trim().split(/^|\s+/).every(function(t){var n=t.indexOf(".");return n>=0&&(t=t.slice(0,n)),!t||t==="start"})}function qa(e,t,n){var r,o,s=Da(t)?Me:T;return function(){var i=s(this,e),a=i.on;a!==r&&(o=(r=a).copy()).on(t,n),i.on=o}}function zo(e,t){var n=this._id;return arguments.length<2?_(this.node(),n).on.on(e):this.each(qa(n,e,t))}function Pa(e){return function(){var t=this.parentNode;for(var n in this.__transition)if(+n!==e)return;t&&t.removeChild(this)}}function Do(){return this.on("end.remove",Pa(this._id))}function qo(e){var t=this._name,n=this._id;typeof e!="function"&&(e=Q(e));for(var r=this._groups,o=r.length,s=new Array(o),i=0;i<o;++i)for(var a=r[i],c=a.length,p=s[i]=new Array(c),u,d,l=0;l<c;++l)(u=a[l])&&(d=e.call(u,u.__data__,l,a))&&("__data__"in u&&(d.__data__=u.__data__),p[l]=d,W(p[l],t,n,l,p,_(u,n)));return new I(s,this._parents,t,n)}function Po(e){var t=this._name,n=this._id;typeof e!="function"&&(e=ge(e));for(var r=this._groups,o=r.length,s=[],i=[],a=0;a<o;++a)for(var c=r[a],p=c.length,u,d=0;d<p;++d)if(u=c[d]){for(var l=e.call(u,u.__data__,d,c),f,m=_(u,n),y=0,v=l.length;y<v;++y)(f=l[y])&&W(f,t,n,y,l,m);s.push(l),i.push(u)}return new I(s,i,t,n)}var Oa=R.prototype.constructor;function Oo(){return new Oa(this._groups,this._parents)}function Na(e,t){var n,r,o;return function(){var s=G(this,e),i=(this.style.removeProperty(e),G(this,e));return s===i?null:s===n&&i===r?o:o=t(n=s,r=i)}}function No(e){return function(){this.style.removeProperty(e)}}function Ra(e,t,n){var r,o=n+"",s;return function(){var i=G(this,e);return i===o?null:i===r?s:s=t(r=i,n)}}function Fa(e,t,n){var r,o,s;return function(){var i=G(this,e),a=n(this),c=a+"";return a==null&&(c=a=(this.style.removeProperty(e),G(this,e))),i===c?null:i===r&&c===o?s:(o=c,s=t(r=i,a))}}function Ua(e,t){var n,r,o,s="style."+t,i="end."+s,a;return function(){var c=T(this,e),p=c.on,u=c.value[s]==null?a||(a=No(t)):void 0;(p!==n||o!==u)&&(r=(n=p).copy()).on(i,o=u),c.on=r}}function Ro(e,t,n){var r=(e+="")=="transform"?rn:xt;return t==null?this.styleTween(e,Na(e,r)).on("end.style."+e,No(e)):typeof t=="function"?this.styleTween(e,Fa(e,r,ce(this,"style."+e,t))).each(Ua(this._id,e)):this.styleTween(e,Ra(e,r,t),n).on("end.style."+e,null)}function Ga(e,t,n){return function(r){this.style.setProperty(e,t.call(this,r),n)}}function Va(e,t,n){var r,o;function s(){var i=t.apply(this,arguments);return i!==o&&(r=(o=i)&&Ga(e,i,n)),r}return s._value=t,s}function Fo(e,t,n){var r="style."+(e+="");if(arguments.length<2)return(r=this.tween(r))&&r._value;if(t==null)return this.tween(r,null);if(typeof t!="function")throw new Error;return this.tween(r,Va(e,t,n??""))}function Wa(e){return function(){this.textContent=e}}function ja(e){return function(){var t=e(this);this.textContent=t??""}}function Uo(e){return this.tween("text",typeof e=="function"?ja(ce(this,"text",e)):Wa(e==null?"":e+""))}function Xa(e){return function(t){this.textContent=e.call(this,t)}}function Ka(e){var t,n;function r(){var o=e.apply(this,arguments);return o!==n&&(t=(n=o)&&Xa(o)),t}return r._value=e,r}function Go(e){var t="text";if(arguments.length<1)return(t=this.tween(t))&&t._value;if(e==null)return this.tween(t,null);if(typeof e!="function")throw new Error;return this.tween(t,Ka(e))}function Vo(){for(var e=this._name,t=this._id,n=wt(),r=this._groups,o=r.length,s=0;s<o;++s)for(var i=r[s],a=i.length,c,p=0;p<a;++p)if(c=i[p]){var u=_(c,t);W(c,e,n,p,i,{time:u.time+u.delay+u.duration,delay:0,duration:u.duration,ease:u.ease})}return new I(r,this._parents,e,n)}function Wo(){var e,t,n=this,r=n._id,o=n.size();return new Promise(function(s,i){var a={value:i},c={value:function(){--o===0&&s()}};n.each(function(){var p=T(this,r),u=p.on;u!==e&&(t=(e=u).copy(),t._.cancel.push(a),t._.interrupt.push(a),t._.end.push(c)),p.on=t}),o===0&&s()})}var Ya=0;function I(e,t,n,r){this._groups=e,this._parents=t,this._name=n,this._id=r}function jo(e){return R().transition(e)}function wt(){return++Ya}var F=R.prototype;I.prototype=jo.prototype={constructor:I,select:qo,selectAll:Po,selectChild:F.selectChild,selectChildren:F.selectChildren,filter:Ao,merge:Ho,selection:Oo,transition:Vo,call:F.call,nodes:F.nodes,node:F.node,size:F.size,empty:F.empty,each:F.each,on:zo,attr:$o,attrTween:Io,style:Ro,styleTween:Fo,text:Uo,textTween:Go,remove:Do,tween:To,delay:Mo,duration:Lo,ease:Co,easeVarying:Bo,end:Wo,[Symbol.iterator]:F[Symbol.iterator]};function bt(e){return((e*=2)<=1?e*e*e:(e-=2)*e*e+2)/2}var Qa={time:null,delay:0,duration:250,ease:bt};function Ja(e,t){for(var n;!(n=e.__transition)||!(n=n[t]);)if(!(e=e.parentNode))throw new Error(`transition ${t} not found`);return n}function Xo(e){var t,n;e instanceof I?(t=e._id,e=e._name):(t=wt(),(n=Qa).time=$e(),e=e==null?null:e+"");for(var r=this._groups,o=r.length,s=0;s<o;++s)for(var i=r[s],a=i.length,c,p=0;p<a;++p)(c=i[p])&&W(c,e,t,p,i,n||Ja(c,t));return new I(r,this._parents,e,t)}R.prototype.interrupt=So;R.prototype.transition=Xo;var{abs:$f,max:If,min:Mf}=Math;function Ko(e){return[+e[0],+e[1]]}function Za(e){return[Ko(e[0]),Ko(e[1])]}var Lf={name:"x",handles:["w","e"].map(an),input:function(e,t){return e==null?null:[[+e[0],t[0][1]],[+e[1],t[1][1]]]},output:function(e){return e&&[e[0][0],e[1][0]]}},Cf={name:"y",handles:["n","s"].map(an),input:function(e,t){return e==null?null:[[t[0][0],+e[0]],[t[1][0],+e[1]]]},output:function(e){return e&&[e[0][1],e[1][1]]}},Bf={name:"xy",handles:["n","w","e","s","nw","ne","sw","se"].map(an),input:function(e){return e==null?null:Za(e)},output:function(e){return e}};function an(e){return{type:e}}function el(e){var t=0,n=e.children,r=n&&n.length;if(!r)t=1;else for(;--r>=0;)t+=n[r].value;e.value=t}function Yo(){return this.eachAfter(el)}function Qo(e,t){let n=-1;for(let r of this)e.call(t,r,++n,this);return this}function Jo(e,t){for(var n=this,r=[n],o,s,i=-1;n=r.pop();)if(e.call(t,n,++i,this),o=n.children)for(s=o.length-1;s>=0;--s)r.push(o[s]);return this}function Zo(e,t){for(var n=this,r=[n],o=[],s,i,a,c=-1;n=r.pop();)if(o.push(n),s=n.children)for(i=0,a=s.length;i<a;++i)r.push(s[i]);for(;n=o.pop();)e.call(t,n,++c,this);return this}function es(e,t){let n=-1;for(let r of this)if(e.call(t,r,++n,this))return r}function ts(e){return this.eachAfter(function(t){for(var n=+e(t.data)||0,r=t.children,o=r&&r.length;--o>=0;)n+=r[o].value;t.value=n})}function ns(e){return this.eachBefore(function(t){t.children&&t.children.sort(e)})}function rs(e){for(var t=this,n=tl(t,e),r=[t];t!==n;)t=t.parent,r.push(t);for(var o=r.length;e!==n;)r.splice(o,0,e),e=e.parent;return r}function tl(e,t){if(e===t)return e;var n=e.ancestors(),r=t.ancestors(),o=null;for(e=n.pop(),t=r.pop();e===t;)o=e,e=n.pop(),t=r.pop();return o}function os(){for(var e=this,t=[e];e=e.parent;)t.push(e);return t}function ss(){return Array.from(this)}function is(){var e=[];return this.eachBefore(function(t){t.children||e.push(t)}),e}function as(){var e=this,t=[];return e.each(function(n){n!==e&&t.push({source:n.parent,target:n})}),t}function*ls(){var e=this,t,n=[e],r,o,s;do for(t=n.reverse(),n=[];e=t.pop();)if(yield e,r=e.children)for(o=0,s=r.length;o<s;++o)n.push(r[o]);while(n.length)}function ue(e,t){e instanceof Map?(e=[void 0,e],t===void 0&&(t=ol)):t===void 0&&(t=rl);for(var n=new Le(e),r,o=[n],s,i,a,c;r=o.pop();)if((i=t(r.data))&&(c=(i=Array.from(i)).length))for(r.children=i,a=c-1;a>=0;--a)o.push(s=i[a]=new Le(i[a])),s.parent=r,s.depth=r.depth+1;return n.eachBefore(il)}function nl(){return ue(this).eachBefore(sl)}function rl(e){return e.children}function ol(e){return Array.isArray(e)?e[1]:null}function sl(e){e.data.value!==void 0&&(e.value=e.data.value),e.data=e.data.data}function il(e){var t=0;do e.height=t;while((e=e.parent)&&e.height<++t)}function Le(e){this.data=e,this.depth=this.height=0,this.parent=null}Le.prototype=ue.prototype={constructor:Le,count:Yo,each:Qo,eachAfter:Zo,eachBefore:Jo,find:es,sum:ts,sort:ns,path:rs,ancestors:os,descendants:ss,leaves:is,links:as,copy:nl,[Symbol.iterator]:ls};function cs(e){if(typeof e!="function")throw new Error;return e}function de(){return 0}function pe(e){return function(){return e}}function us(e){e.x0=Math.round(e.x0),e.y0=Math.round(e.y0),e.x1=Math.round(e.x1),e.y1=Math.round(e.y1)}function ds(e,t,n,r,o){for(var s=e.children,i,a=-1,c=s.length,p=e.value&&(r-t)/e.value;++a<c;)i=s[a],i.y0=n,i.y1=o,i.x0=t,i.x1=t+=i.value*p}function ps(e,t,n,r,o){for(var s=e.children,i,a=-1,c=s.length,p=e.value&&(o-n)/e.value;++a<c;)i=s[a],i.x0=t,i.x1=r,i.y0=n,i.y1=n+=i.value*p}var al=(1+Math.sqrt(5))/2;function ll(e,t,n,r,o,s){for(var i=[],a=t.children,c,p,u=0,d=0,l=a.length,f,m,y=t.value,v,w,g,x,b,$,q;u<l;){f=o-n,m=s-r;do v=a[d++].value;while(!v&&d<l);for(w=g=v,$=Math.max(m/f,f/m)/(y*e),q=v*v*$,b=Math.max(g/q,q/w);d<l;++d){if(v+=p=a[d].value,p<w&&(w=p),p>g&&(g=p),q=v*v*$,x=Math.max(g/q,q/w),x>b){v-=p;break}b=x}i.push(c={value:v,dice:f<m,children:a.slice(u,d)}),c.dice?ds(c,n,r,o,y?r+=m*v/y:s):ps(c,n,r,y?n+=f*v/y:o,s),y-=v,u=d}return i}var fs=function e(t){function n(r,o,s,i,a){ll(t,r,o,s,i,a)}return n.ratio=function(r){return e((r=+r)>1?r:1)},n}(al);function ln(){var e=fs,t=!1,n=1,r=1,o=[0],s=de,i=de,a=de,c=de,p=de;function u(l){return l.x0=l.y0=0,l.x1=n,l.y1=r,l.eachBefore(d),o=[0],t&&l.eachBefore(us),l}function d(l){var f=o[l.depth],m=l.x0+f,y=l.y0+f,v=l.x1-f,w=l.y1-f;v<m&&(m=v=(m+v)/2),w<y&&(y=w=(y+w)/2),l.x0=m,l.y0=y,l.x1=v,l.y1=w,l.children&&(f=o[l.depth+1]=s(l)/2,m+=p(l)-f,y+=i(l)-f,v-=a(l)-f,w-=c(l)-f,v<m&&(m=v=(m+v)/2),w<y&&(y=w=(y+w)/2),e(l,m,y,v,w))}return u.round=function(l){return arguments.length?(t=!!l,u):t},u.size=function(l){return arguments.length?(n=+l[0],r=+l[1],u):[n,r]},u.tile=function(l){return arguments.length?(e=cs(l),u):e},u.padding=function(l){return arguments.length?u.paddingInner(l).paddingOuter(l):u.paddingInner()},u.paddingInner=function(l){return arguments.length?(s=typeof l=="function"?l:pe(+l),u):s},u.paddingOuter=function(l){return arguments.length?u.paddingTop(l).paddingRight(l).paddingBottom(l).paddingLeft(l):u.paddingTop()},u.paddingTop=function(l){return arguments.length?(i=typeof l=="function"?l:pe(+l),u):i},u.paddingRight=function(l){return arguments.length?(a=typeof l=="function"?l:pe(+l),u):a},u.paddingBottom=function(l){return arguments.length?(c=typeof l=="function"?l:pe(+l),u):c},u.paddingLeft=function(l){return arguments.length?(p=typeof l=="function"?l:pe(+l),u):p},u}function ms(e,t){switch(arguments.length){case 0:break;case 1:this.range(e);break;default:this.range(t).domain(e);break}return this}var cn=Symbol("implicit");function Ce(){var e=new se,t=[],n=[],r=cn;function o(s){let i=e.get(s);if(i===void 0){if(r!==cn)return r;e.set(s,i=t.push(s)-1)}return n[i%n.length]}return o.domain=function(s){if(!arguments.length)return t.slice();t=[],e=new se;for(let i of s)e.has(i)||e.set(i,t.push(i)-1);return o},o.range=function(s){return arguments.length?(n=Array.from(s),o):n.slice()},o.unknown=function(s){return arguments.length?(r=s,o):r},o.copy=function(){return Ce(t,n).unknown(r)},ms.apply(o,arguments),o}function j(e,t,n){this.k=e,this.x=t,this.y=n}j.prototype={constructor:j,scale:function(e){return e===1?this:new j(this.k*e,this.x,this.y)},translate:function(e,t){return e===0&t===0?this:new j(this.k,this.x+this.k*e,this.y+this.k*t)},apply:function(e){return[e[0]*this.k+this.x,e[1]*this.k+this.y]},applyX:function(e){return e*this.k+this.x},applyY:function(e){return e*this.k+this.y},invert:function(e){return[(e[0]-this.x)/this.k,(e[1]-this.y)/this.k]},invertX:function(e){return(e-this.x)/this.k},invertY:function(e){return(e-this.y)/this.k},rescaleX:function(e){return e.copy().domain(e.range().map(this.invertX,this).map(e.invert,e))},rescaleY:function(e){return e.copy().domain(e.range().map(this.invertY,this).map(e.invert,e))},toString:function(){return"translate("+this.x+","+this.y+") scale("+this.k+")"}};var un=new j(1,0,0);dn.prototype=j.prototype;function dn(e){for(;!e.__zoom;)if(!(e=e.parentNode))return un;return e.__zoom}var Et=class{constructor(t){this.currentPath="/";this.pathHistory=[];this.isLoading=!1;let n=document.getElementById(t);if(!n)throw new Error(`Container ${t} not found`);this.container=n,this.width=800,this.height=500,this.buildUI()}buildUI(){this.container.innerHTML=`
            <div class="disk-viz-wrapper">
                <div class="disk-viz-controls">
                    <div class="disk-viz-path-group">
                        <label for="disk-viz-path">Path:</label>
                        <input type="text" id="disk-viz-path" value="/" placeholder="/" />
                        <button id="disk-viz-scan" class="primary">Scan</button>
                        <button id="disk-viz-back" class="secondary" disabled>\u2190 Back</button>
                        <button id="disk-viz-home" class="secondary">\u{1F3E0} Home</button>
                    </div>
                    <div class="disk-viz-options">
                        <label>
                            Depth: 
                            <select id="disk-viz-depth">
                                <option value="2">2 levels</option>
                                <option value="3" selected>3 levels</option>
                                <option value="4">4 levels</option>
                                <option value="5">5 levels</option>
                            </select>
                        </label>
                        <label>
                            Min size: 
                            <select id="disk-viz-min-size">
                                <option value="0">Show all</option>
                                <option value="1" selected>1 MB+</option>
                                <option value="10">10 MB+</option>
                                <option value="100">100 MB+</option>
                                <option value="1000">1 GB+</option>
                            </select>
                        </label>
                    </div>
                </div>
                
                <div class="disk-viz-quick-paths">
                    <span>Quick:</span>
                    <button class="quick-path-btn" data-path="/">/ (root)</button>
                    <button class="quick-path-btn" data-path="/Users">Users</button>
                    <button class="quick-path-btn" data-path="/Applications">Applications</button>
                    <button class="quick-path-btn" data-path="/Library">Library</button>
                </div>
                
                <div class="disk-viz-breadcrumbs" id="disk-viz-breadcrumbs"></div>
                
                <div class="disk-viz-chart" id="disk-viz-chart">
                    <div class="disk-viz-placeholder">
                        <div class="placeholder-icon">\u{1F4CA}</div>
                        <h3>Disk Usage Visualization</h3>
                        <p>Click "Scan" to analyze disk usage and see an interactive treemap.</p>
                        <p class="hint">Click on folders in the treemap to drill down.</p>
                    </div>
                </div>
                
                <div class="disk-viz-legend" id="disk-viz-legend"></div>
                
                <div class="disk-viz-details" id="disk-viz-details" style="display: none;">
                    <h4>Selected:</h4>
                    <div id="disk-viz-selected-info"></div>
                </div>
            </div>
            
            <style>
                .disk-viz-wrapper {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .disk-viz-controls {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 1rem;
                    align-items: center;
                    margin-bottom: 1rem;
                    justify-content: space-between;
                }
                
                .disk-viz-path-group {
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                    flex-wrap: wrap;
                }
                
                .disk-viz-path-group input {
                    width: 250px;
                    padding: 0.5rem 0.75rem;
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    background: var(--bg-tertiary);
                    color: var(--text-primary);
                }
                
                .disk-viz-options {
                    display: flex;
                    gap: 1rem;
                    align-items: center;
                }
                
                .disk-viz-options select {
                    padding: 0.4rem 0.6rem;
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    background: var(--bg-tertiary);
                    color: var(--text-primary);
                }
                
                .disk-viz-quick-paths {
                    display: flex;
                    gap: 0.5rem;
                    align-items: center;
                    margin-bottom: 1rem;
                    flex-wrap: wrap;
                }
                
                .disk-viz-quick-paths span {
                    color: var(--text-secondary);
                    font-size: 0.875rem;
                }
                
                .disk-viz-quick-paths .quick-path-btn {
                    padding: 0.35rem 0.75rem;
                    font-size: 0.8rem;
                    border-radius: 4px;
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-color);
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .disk-viz-quick-paths .quick-path-btn:hover {
                    background: var(--accent-color);
                    color: white;
                    border-color: var(--accent-color);
                }
                
                .disk-viz-breadcrumbs {
                    display: flex;
                    gap: 0.25rem;
                    align-items: center;
                    margin-bottom: 0.75rem;
                    font-size: 0.875rem;
                    flex-wrap: wrap;
                }
                
                .disk-viz-breadcrumbs .breadcrumb {
                    cursor: pointer;
                    color: var(--accent-color);
                    transition: color 0.2s;
                }
                
                .disk-viz-breadcrumbs .breadcrumb:hover {
                    text-decoration: underline;
                }
                
                .disk-viz-breadcrumbs .separator {
                    color: var(--text-secondary);
                }
                
                .disk-viz-chart {
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    min-height: 500px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                    position: relative;
                }
                
                .disk-viz-placeholder {
                    text-align: center;
                    color: var(--text-secondary);
                    padding: 2rem;
                }
                
                .disk-viz-placeholder .placeholder-icon {
                    font-size: 4rem;
                    margin-bottom: 1rem;
                    opacity: 0.5;
                }
                
                .disk-viz-placeholder h3 {
                    margin: 0 0 0.5rem 0;
                    color: var(--text-primary);
                }
                
                .disk-viz-placeholder .hint {
                    font-size: 0.85rem;
                    margin-top: 1rem;
                    opacity: 0.7;
                }
                
                .disk-viz-loading {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 1rem;
                }
                
                .disk-viz-loading .spinner {
                    width: 48px;
                    height: 48px;
                    border: 4px solid var(--border-color);
                    border-top-color: var(--accent-color);
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                }
                
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                
                .disk-viz-legend {
                    display: flex;
                    gap: 1rem;
                    margin-top: 1rem;
                    flex-wrap: wrap;
                    justify-content: center;
                }
                
                .disk-viz-legend-item {
                    display: flex;
                    align-items: center;
                    gap: 0.35rem;
                    font-size: 0.8rem;
                    color: var(--text-secondary);
                }
                
                .disk-viz-legend-color {
                    width: 12px;
                    height: 12px;
                    border-radius: 2px;
                }
                
                .disk-viz-details {
                    margin-top: 1rem;
                    padding: 1rem;
                    background: var(--bg-tertiary);
                    border-radius: 8px;
                }
                
                .disk-viz-details h4 {
                    margin: 0 0 0.5rem 0;
                    font-size: 0.9rem;
                    color: var(--text-secondary);
                }
                
                #disk-viz-selected-info {
                    font-family: monospace;
                    font-size: 0.875rem;
                }
                
                /* Treemap styles */
                .treemap-cell {
                    cursor: pointer;
                    transition: opacity 0.2s;
                }
                
                .treemap-cell:hover {
                    opacity: 0.85;
                }
                
                .treemap-label {
                    pointer-events: none;
                    font-size: 11px;
                    fill: white;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
                }
                
                .treemap-size {
                    pointer-events: none;
                    font-size: 9px;
                    fill: rgba(255,255,255,0.8);
                }
            </style>
        `,this.container.querySelector("#disk-viz-scan")?.addEventListener("click",()=>this.scan()),this.container.querySelector("#disk-viz-back")?.addEventListener("click",()=>this.goBack()),this.container.querySelector("#disk-viz-home")?.addEventListener("click",()=>this.goHome());let t=this.container.querySelector("#disk-viz-path");t?.addEventListener("keypress",n=>{n.key==="Enter"&&this.scan()}),this.container.querySelectorAll(".disk-viz-quick-paths .quick-path-btn").forEach(n=>{n.addEventListener("click",()=>{let r=n.dataset.path||"/";t.value=r,this.currentPath=r,this.scan()})})}async scan(){if(this.isLoading)return;let t=this.container.querySelector("#disk-viz-path"),n=this.container.querySelector("#disk-viz-depth"),r=this.container.querySelector("#disk-viz-min-size"),o=t.value||"/",s=parseInt(n.value)||3,i=parseInt(r.value)||1;this.currentPath=o,this.isLoading=!0,this.showLoading();try{let a=await fetch(`/api/disk/usage?path=${encodeURIComponent(o)}&depth=${s}&min_size_mb=${i}`);if(!a.ok){let p=await a.json().catch(()=>({detail:"Request failed"}));this.showError(p.detail||`HTTP ${a.status}`);return}let c=await a.json();c.error&&!c.name?this.showError(c.error):c.name?(this.renderTreemap(c),this.updateBreadcrumbs(),c.warnings&&c.warnings.length>0?h(`Scan complete with ${c.warnings.length} permission warning(s)`,"warning"):h(`Scan complete: ${c.totalSizeFormatted||"done"}`,"success")):this.showError("Invalid response from server")}catch(a){this.showError(`Failed to scan: ${a}`)}finally{this.isLoading=!1}}showLoading(){let t=this.container.querySelector("#disk-viz-chart");t.innerHTML=`
            <div class="disk-viz-loading">
                <div class="spinner"></div>
                <div>Scanning disk structure...</div>
                <div style="font-size: 0.8rem; color: var(--text-secondary);">This may take a moment for large directories</div>
            </div>
        `}showError(t){let n=this.container.querySelector("#disk-viz-chart");n.innerHTML=`
            <div class="disk-viz-placeholder">
                <div class="placeholder-icon">\u26A0\uFE0F</div>
                <h3>Scan Error</h3>
                <p>${t}</p>
            </div>
        `,h(t,"error")}renderTreemap(t){let n=this.container.querySelector("#disk-viz-chart");n.innerHTML="";let r=n.getBoundingClientRect();this.width=r.width||800,this.height=Math.max(500,r.height);let o=Xt(n).append("svg").attr("width",this.width).attr("height",this.height).attr("viewBox",`0 0 ${this.width} ${this.height}`).style("font-family","-apple-system, BlinkMacSystemFont, sans-serif"),s=ue(t).sum(l=>l.children?0:l.value).sort((l,f)=>(f.value||0)-(l.value||0)),a=ln().size([this.width,this.height]).paddingOuter(3).paddingInner(2).paddingTop(20).round(!0)(s),c=Ce().domain(["Applications","Users","Library","System","private","opt","usr","var","other"]).range(["#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7","#DDA0DD","#98D8C8","#F7DC6F","#B8B8B8"]),p=l=>{let f=l;for(;f&&f.depth>1;)f=f.parent;let m=f?.data.name||"other";return c(m)},u=a.descendants(),d=o.selectAll("g").data(u.filter(l=>l.depth>0)).join("g").attr("transform",l=>`translate(${l.x0},${l.y0})`);d.append("rect").attr("class","treemap-cell").attr("width",l=>Math.max(0,l.x1-l.x0)).attr("height",l=>Math.max(0,l.y1-l.y0)).attr("fill",l=>p(l)).attr("stroke","var(--bg-secondary)").attr("stroke-width",1).on("click",(l,f)=>this.handleCellClick(f)).on("mouseover",(l,f)=>this.showDetails(f)).on("mouseout",()=>this.hideDetails()).append("title").text(l=>`${l.data.path}
${l.data.sizeFormatted||"N/A"}
${(l.data.percentage||0).toFixed(1)}%`),d.filter(l=>l.x1-l.x0>60&&l.y1-l.y0>30).append("text").attr("class","treemap-label").attr("x",4).attr("y",14).text(l=>this.truncateLabel(l.data.name,l.x1-l.x0-8)),d.filter(l=>l.x1-l.x0>50&&l.y1-l.y0>45).append("text").attr("class","treemap-size").attr("x",4).attr("y",26).text(l=>l.data.sizeFormatted||""),this.renderLegend(c)}truncateLabel(t,n){let o=Math.floor(n/7);return t.length<=o?t:t.slice(0,o-2)+"\u2026"}handleCellClick(t){if(t.children&&t.data.path){this.pathHistory.push(this.currentPath),this.currentPath=t.data.path;let n=this.container.querySelector("#disk-viz-path");n.value=t.data.path;let r=this.container.querySelector("#disk-viz-back");r.disabled=!1,this.scan()}}showDetails(t){let n=this.container.querySelector("#disk-viz-details"),r=this.container.querySelector("#disk-viz-selected-info");n.style.display="block",r.innerHTML=`
            <strong>${t.data.name}</strong><br>
            Path: ${t.data.path}<br>
            Size: ${t.data.sizeFormatted||"N/A"}<br>
            Percent: ${(t.data.percentage||0).toFixed(2)}% of parent
        `}hideDetails(){let t=this.container.querySelector("#disk-viz-details");t.style.display="none"}renderLegend(t){let n=this.container.querySelector("#disk-viz-legend"),r=t.domain();n.innerHTML=r.map(o=>`
            <div class="disk-viz-legend-item">
                <div class="disk-viz-legend-color" style="background: ${t(o)}"></div>
                <span>${o}</span>
            </div>
        `).join("")}updateBreadcrumbs(){let t=this.container.querySelector("#disk-viz-breadcrumbs"),n=this.currentPath.split("/").filter(s=>s),r='<span class="breadcrumb" data-path="/">/</span>',o="";n.forEach((s,i)=>{o+="/"+s,r+='<span class="separator">/</span>',r+=`<span class="breadcrumb" data-path="${o}">${s}</span>`}),t.innerHTML=r,t.querySelectorAll(".breadcrumb").forEach(s=>{s.addEventListener("click",()=>{let i=s.dataset.path||"/",a=this.container.querySelector("#disk-viz-path");a.value=i,this.currentPath=i,this.scan()})})}goBack(){if(this.pathHistory.length>0){let t=this.pathHistory.pop();this.currentPath=t;let n=this.container.querySelector("#disk-viz-path");if(n.value=t,this.pathHistory.length===0){let r=this.container.querySelector("#disk-viz-back");r.disabled=!0}this.scan()}}goHome(){this.pathHistory=[],this.currentPath="/";let t=this.container.querySelector("#disk-viz-path");t.value="/";let n=this.container.querySelector("#disk-viz-back");n.disabled=!0,this.scan()}};var kt=class{constructor(t){this.currentScanId=null;this.scanResult=null;this.selectedFiles=new Set;let n=document.getElementById(t);if(!n)throw new Error(`Container ${t} not found`);this.container=n,this.buildUI(),this.bindEvents()}buildUI(){this.container.innerHTML=`
            <div class="duplicate-finder">
                <div class="scan-controls">
                    <div class="control-row">
                        <label for="dup-path">Path:</label>
                        <input type="text" id="dup-path" value="~" placeholder="Directory to scan" />
                        <button id="dup-home-btn" class="quick-path-btn">\u{1F3E0} Home</button>
                        <button id="dup-downloads-btn" class="quick-path-btn">\u{1F4E5} Downloads</button>
                        <button id="dup-documents-btn" class="quick-path-btn">\u{1F4C4} Documents</button>
                    </div>
                    <div class="control-row">
                        <label for="dup-min-size">Min size:</label>
                        <select id="dup-min-size">
                            <option value="0.001">1 KB+</option>
                            <option value="0.1">100 KB+</option>
                            <option value="1" selected>1 MB+</option>
                            <option value="10">10 MB+</option>
                            <option value="100">100 MB+</option>
                        </select>
                        <label for="dup-hidden">
                            <input type="checkbox" id="dup-hidden" /> Include hidden files
                        </label>
                        <button id="dup-scan-btn" class="primary">\u{1F50D} Scan for Duplicates</button>
                    </div>
                </div>
                
                <div id="dup-progress" class="scan-progress" style="display: none;">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">Preparing scan...</div>
                </div>
                
                <div id="dup-results" class="scan-results" style="display: none;">
                    <div class="results-summary">
                        <div class="summary-stat">
                            <span class="stat-value" id="dup-files-scanned">0</span>
                            <span class="stat-label">Files Scanned</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-value" id="dup-groups-found">0</span>
                            <span class="stat-label">Duplicate Groups</span>
                        </div>
                        <div class="summary-stat highlight">
                            <span class="stat-value" id="dup-wasted-space">0 B</span>
                            <span class="stat-label">Potential Savings</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-value" id="dup-scan-time">0s</span>
                            <span class="stat-label">Scan Time</span>
                        </div>
                    </div>
                    
                    <div class="results-actions">
                        <button id="dup-export-csv" class="action-btn">\u{1F4CA} Export CSV</button>
                        <button id="dup-export-text" class="action-btn">\u{1F4DD} Export Text</button>
                        <button id="dup-delete-selected" class="action-btn danger" disabled>\u{1F5D1}\uFE0F Delete Selected (0)</button>
                    </div>
                    
                    <div id="dup-groups-container" class="groups-container">
                        <!-- Duplicate groups will be rendered here -->
                    </div>
                </div>
                
                <div id="dup-empty" class="empty-state" style="display: none;">
                    <div class="empty-icon">\u{1F389}</div>
                    <div class="empty-title">No Duplicates Found</div>
                    <div class="empty-text">Your files are unique! No duplicate files were detected.</div>
                </div>
            </div>
        `,this.pathInput=this.container.querySelector("#dup-path"),this.minSizeSelect=this.container.querySelector("#dup-min-size"),this.includeHiddenCheckbox=this.container.querySelector("#dup-hidden"),this.scanButton=this.container.querySelector("#dup-scan-btn"),this.progressContainer=this.container.querySelector("#dup-progress"),this.resultsContainer=this.container.querySelector("#dup-results")}bindEvents(){this.container.querySelector("#dup-home-btn")?.addEventListener("click",()=>{this.pathInput.value="~"}),this.container.querySelector("#dup-downloads-btn")?.addEventListener("click",()=>{this.pathInput.value="~/Downloads"}),this.container.querySelector("#dup-documents-btn")?.addEventListener("click",()=>{this.pathInput.value="~/Documents"}),this.scanButton.addEventListener("click",()=>this.startScan()),this.container.querySelector("#dup-export-csv")?.addEventListener("click",()=>this.exportResults("csv")),this.container.querySelector("#dup-export-text")?.addEventListener("click",()=>this.exportResults("text")),this.container.querySelector("#dup-delete-selected")?.addEventListener("click",()=>this.deleteSelected())}expandPath(t){return t==="~"||t.startsWith("~/"),t}async startScan(){let t=this.expandPath(this.pathInput.value.trim()||"~"),n=parseFloat(this.minSizeSelect.value),r=this.includeHiddenCheckbox.checked;this.selectedFiles.clear(),this.scanResult=null,this.showProgress();try{let o=await fetch(`/api/duplicates/scan?paths=${encodeURIComponent(t)}&min_size_mb=${n}&include_hidden=${r}`,{method:"POST"});if(!o.ok){let i=await o.json();throw new Error(i.detail||"Failed to start scan")}let{scan_id:s}=await o.json();this.currentScanId=s,await this.pollScanStatus(s)}catch(o){h(`Scan error: ${o}`,"error"),this.hideProgress()}}async pollScanStatus(t){let o=0,s=async()=>{try{let i=await fetch(`/api/duplicates/status/${t}`);if(!i.ok)throw new Error("Failed to get scan status");let a=await i.json();if(this.updateProgress(a),a.status==="complete"){await this.loadResults(t);return}if(a.status==="error")throw new Error(a.error||"Scan failed");if(o++,o<600)setTimeout(s,500);else throw new Error("Scan timeout - taking too long")}catch(i){h(`${i}`,"error"),this.hideProgress()}};await s()}updateProgress(t){let n=this.progressContainer.querySelector(".progress-fill"),r=this.progressContainer.querySelector(".progress-text"),s={scanning:"Scanning files...",size_grouping:"Grouping by size...",partial_hashing:"Computing partial hashes...",full_hashing:"Verifying duplicates..."}[t.progress.stage]||t.progress.stage;if(t.progress.total>0){let i=Math.round(t.progress.current/t.progress.total*100);n.style.width=`${i}%`,r.textContent=`${s} (${i}%)`}else r.textContent=s}async loadResults(t){try{let n=await fetch(`/api/duplicates/results/${t}`);if(!n.ok)throw new Error("Failed to load results");let r=await n.json();this.scanResult=r,this.renderResults(r)}catch(n){h(`Failed to load results: ${n}`,"error"),this.hideProgress()}}renderResults(t){if(this.hideProgress(),t.duplicate_groups.length===0){this.container.querySelector("#dup-empty").style.display="block",this.resultsContainer.style.display="none";return}this.container.querySelector("#dup-empty").style.display="none",this.resultsContainer.style.display="block";let{scan_summary:n}=t;this.container.querySelector("#dup-files-scanned").textContent=n.total_files_scanned.toLocaleString(),this.container.querySelector("#dup-groups-found").textContent=n.duplicate_groups_count.toString(),this.container.querySelector("#dup-wasted-space").textContent=n.total_wasted_formatted,this.container.querySelector("#dup-scan-time").textContent=`${n.scan_duration_seconds.toFixed(1)}s`;let r=this.container.querySelector("#dup-groups-container");r.innerHTML="",t.duplicate_groups.forEach((o,s)=>{let i=this.createGroupElement(o,s);r.appendChild(i)})}createGroupElement(t,n){let r=document.createElement("div");r.className="duplicate-group",r.innerHTML=`
            <div class="group-header" data-index="${n}">
                <span class="group-toggle">\u25B6</span>
                <span class="group-title">Group ${n+1}: ${t.file_count} files</span>
                <span class="group-size">${t.size_formatted} each</span>
                <span class="group-savings">Save ${t.potential_savings_formatted}</span>
            </div>
            <div class="group-files" style="display: none;">
                ${t.files.map((a,c)=>`
                    <div class="file-row">
                        <label>
                            <input type="checkbox" 
                                   class="file-checkbox" 
                                   data-path="${this.escapeHtml(a.path)}"
                                   data-group="${n}"
                                   ${c===0?'disabled title="Keep at least one copy"':""}>
                            <span class="file-path">${this.escapeHtml(a.path)}</span>
                        </label>
                        <span class="file-mtime">${a.mtime?new Date(a.mtime).toLocaleDateString():""}</span>
                    </div>
                `).join("")}
                <div class="group-actions">
                    <button class="group-btn keep-newest" data-group="${n}">Keep Newest</button>
                    <button class="group-btn keep-oldest" data-group="${n}">Keep Oldest</button>
                    <button class="group-btn select-all" data-group="${n}">Select All (except first)</button>
                </div>
            </div>
        `;let o=r.querySelector(".group-header"),s=r.querySelector(".group-files"),i=r.querySelector(".group-toggle");return o.addEventListener("click",()=>{let a=s.style.display!=="none";s.style.display=a?"none":"block",i.textContent=a?"\u25B6":"\u25BC"}),r.querySelectorAll(".file-checkbox").forEach(a=>{a.addEventListener("change",c=>{let p=c.target,u=p.dataset.path;p.checked?this.selectedFiles.add(u):this.selectedFiles.delete(u),this.updateDeleteButton()})}),r.querySelector(".keep-newest")?.addEventListener("click",()=>this.keepNewest(t,n,r)),r.querySelector(".keep-oldest")?.addEventListener("click",()=>this.keepOldest(t,n,r)),r.querySelector(".select-all")?.addEventListener("click",()=>this.selectAllExceptFirst(t,n,r)),r}keepNewest(t,n,r){let o=t.files.map((i,a)=>({file:i,index:a})).filter(i=>i.file.mtime).sort((i,a)=>new Date(a.file.mtime).getTime()-new Date(i.file.mtime).getTime()),s=o.length>0?o[0].index:0;r.querySelectorAll(".file-checkbox").forEach((i,a)=>{let c=i;if(!c.disabled){c.checked=a!==s;let p=c.dataset.path;c.checked?this.selectedFiles.add(p):this.selectedFiles.delete(p)}}),this.updateDeleteButton()}keepOldest(t,n,r){let o=t.files.map((i,a)=>({file:i,index:a})).filter(i=>i.file.mtime).sort((i,a)=>new Date(i.file.mtime).getTime()-new Date(a.file.mtime).getTime()),s=o.length>0?o[0].index:0;r.querySelectorAll(".file-checkbox").forEach((i,a)=>{let c=i;if(!c.disabled){c.checked=a!==s;let p=c.dataset.path;c.checked?this.selectedFiles.add(p):this.selectedFiles.delete(p)}}),this.updateDeleteButton()}selectAllExceptFirst(t,n,r){r.querySelectorAll(".file-checkbox").forEach(o=>{let s=o;s.disabled||(s.checked=!0,this.selectedFiles.add(s.dataset.path))}),this.updateDeleteButton()}updateDeleteButton(){let t=this.container.querySelector("#dup-delete-selected");t.disabled=this.selectedFiles.size===0,t.textContent=`\u{1F5D1}\uFE0F Delete Selected (${this.selectedFiles.size})`}async deleteSelected(){if(this.selectedFiles.size===0||!this.currentScanId)return;let t=this.selectedFiles.size;if(!confirm(`Move ${t} file(s) to Trash? This can be undone from Trash.`))return;let n=this.container.querySelector("#dup-delete-selected");n.disabled=!0,n.textContent="Deleting...";try{let r=await fetch(`/api/duplicates/delete?scan_id=${this.currentScanId}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({paths:Array.from(this.selectedFiles)})});if(!r.ok){let s=await r.json();throw new Error(s.detail||"Delete failed")}let o=await r.json();o.deleted_count>0&&h(`Moved ${o.deleted_count} file(s) to Trash`,"success"),o.error_count>0&&h(`Failed to delete ${o.error_count} file(s)`,"error"),await this.startScan()}catch(r){h(`Delete error: ${r}`,"error"),this.updateDeleteButton()}}async exportResults(t){if(this.currentScanId)try{let n=await fetch(`/api/duplicates/results/${this.currentScanId}?format=${t}`);if(!n.ok)throw new Error("Export failed");let r=await n.text(),o=new Blob([r],{type:t==="csv"?"text/csv":"text/plain"}),s=URL.createObjectURL(o),i=document.createElement("a");i.href=s,i.download=`duplicates-${this.currentScanId}.${t==="csv"?"csv":"txt"}`,i.click(),URL.revokeObjectURL(s),h(`Exported as ${t.toUpperCase()}`,"success")}catch(n){h(`Export error: ${n}`,"error")}}showProgress(){this.progressContainer.style.display="block",this.resultsContainer.style.display="none",this.container.querySelector("#dup-empty").style.display="none",this.scanButton.disabled=!0,this.scanButton.textContent="Scanning...";let t=this.progressContainer.querySelector(".progress-fill");t.style.width="0%"}hideProgress(){this.progressContainer.style.display="none",this.scanButton.disabled=!1,this.scanButton.textContent="\u{1F50D} Scan for Duplicates"}escapeHtml(t){let n=document.createElement("div");return n.textContent=t,n.innerHTML}};console.log("\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557");console.log("\u2551   UPKEEP - SCRIPT LOADING            \u2551");console.log("\u255A\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255D");window.switchTab=$t;window.showTab=$t;window.toggleTheme=fn;window.reloadScripts=yn;window.setTheme=vn;window.toggleAutoRefresh=wn;window.setRefreshInterval=bn;window.togglePreviewMode=kn;window.toggleConfirmations=_n;window.showKeyboardShortcuts=Tn;window.loadSystemInfo=Pe;window.loadHealthScore=Oe;window.runQuickHealthCheck=$n;window.loadTopProcesses=Ne;window.loadOperations=Hn;window.runDoctor=Ve;window.fixDoctorIssue=Xn;window.runSelectedOperations=Rn;window.cancelOperations=Un;window.skipCurrentOperation=Fn;window.applyTemplate=Nn;window.selectAllOperations=zn;window.deselectAllOperations=Dn;window.upkeepFilterByCategory=qn;window.upkeepToggleCategory=Ue;window.upkeepExpandAll=Pn;window.upkeepCollapseAll=On;window.copyOutputToClipboard=qt;window.showQuickStartWizard=Wn;window.closeWizard=Ge;window.selectWizardOption=jn;window.closeShortcuts=Pt;window.exportLatestLog=Yn;window.analyzeStorage=Nt;window.setPath=Zn;window.getUsername=er;window.onScheduleTabShow=lr;window.openScheduleModal=Ft;window.closeScheduleModal=je;window.loadSchedules=O;window.saveSchedule=nr;window.deleteSchedule=rr;window.toggleScheduleEnabled=or;window.runScheduleNow=sr;window.applyScheduleTemplate=ar;window.showToast=h;document.addEventListener("DOMContentLoaded",()=>{console.log("\u2713 DOM Content Loaded"),Kn(),pn(),console.log("\u2713 Theme initialized"),Sn(),console.log("\u2713 Settings initialized"),Pe(),Oe(),Ne(),console.log("\u2713 Initial dashboard data loading");try{new Xe("app-uninstaller-container"),console.log("\u2713 App Uninstaller initialized")}catch(e){console.warn("App Uninstaller init failed (container missing?):",e)}try{new Et("disk-viz-container"),console.log("\u2713 Disk Visualizer initialized")}catch(e){console.warn("Disk Visualizer init failed (container missing?):",e)}try{new kt("duplicates-container"),console.log("\u2713 Duplicate Finder initialized")}catch(e){console.warn("Duplicate Finder init failed (container missing?):",e)}console.log("\u2713 Auto-refresh configured via settings"),console.log("\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557"),console.log("\u2551   UPKEEP - READY                     \u2551"),console.log("\u255A\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255D")});})();
//# sourceMappingURL=app.js.map
