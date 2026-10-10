# -*- coding: utf-8 -*-
"""
Живая диспетчерская в герое главной: три машины едут по настоящим улицам Атырау
поверх снимка Sentinel-2 (public/img/atyrau-city.*, 1600×1000, 12,5 м/px).

Координаты — пиксели снимка. SVG имеет тот же viewBox и тот же якорь кадрирования
(xMaxYMid slice = object-position 100% 50%), поэтому маршрут остаётся на улице
при любой ширине экрана. Маршруты сняты вручную по увеличенным фрагментам кадра.

Сценарий (каждая машина показывает свой статус из дизайн-системы):
  КамАЗ 12  — кольцо через оба моста над Уралом, стоянка на восточном берегу;
  Газель 07 — широтная улица с запада на восток, после моста пропадает связь:
              маркер замирает на последней точке, разрыв потом рисуется пунктиром;
  Hilux 03  — стоит на базе в промзоне, выезжает — срабатывает геозона.

Тексты событий формируются скриптом и в HTML не попадают: поисковики их не видят,
на странице без JS остаются снимок и статичные треки.
Максимум три машины в кадре и reduced-motion — по guidelines.md, «Движение».
"""
import json

ROUTES = {
    # кольцо: нижний мост → улица x≈1233 на север → верхний мост → улица x≈1085 на юг
    "ring": [[1085, 468], [1175, 467], [1233, 467], [1233, 353], [1197, 355],
             [1170, 366], [1087, 351]],
    # широтная улица y≈345–350, через верхний мост
    "avenue": [[860, 345], [1074, 349], [1087, 351], [1170, 366], [1197, 355],
               [1330, 349], [1424, 350]],
    # из промзоны на юго-запад вдоль железной дороги
    "base": [[1545, 319], [1488, 368], [1420, 426], [1360, 477], [1310, 520]],
}

ZONE = [[1400, 310], [1530, 262], [1570, 372], [1445, 425]]
ZONE_NAME = "База"

CARS = [
    {"id": "КамАЗ 12", "kind": "truck", "route": "ring", "closed": True,
     "v": 34, "kmh": 46, "d0": 0, "stop": [1233, 410], "stopT": 3.6},
    {"id": "Газель 07", "kind": "van", "route": "avenue", "closed": False,
     "v": 40, "kmh": 54, "d0": 0, "gap": [[1240, 353], [1335, 349]]},
    {"id": "Hilux 03", "kind": "pickup", "route": "base", "closed": False,
     "v": 30, "kmh": 41, "d0": 0, "hold": 3.2, "zone": True},
]


def _pts(p):
    return " ".join(f"{x},{y}" for x, y in p)


def media(alt):
    static = "".join(
        f'<polyline class="ds-track-history" points="{_pts(p + ([p[0]] if k == "ring" else []))}"/>'
        for k, p in ROUTES.items())
    return f"""<div class="ds-hero__media"><div class="hero-frame">
<picture><source type="image/avif" srcset="/img/atyrau-city.avif">
<img src="/img/atyrau-city.webp" width="1600" height="1000" alt="{alt}" loading="eager" fetchpriority="high" decoding="async"></picture>
<div class="ds-hero__scrim"></div>
<svg class="hero-live" id="hl" viewBox="0 0 1600 1000" preserveAspectRatio="xMaxYMid slice" aria-hidden="true" focusable="false">
<polygon class="ds-geofence" id="hz" points="{_pts(ZONE)}"/>
<g class="static">{static}</g>
<g id="ht"></g><g id="hc"></g>
</svg></div>
<div class="tick" id="htk" aria-hidden="true"></div>
</div>"""


HUD = ('<div class="hud" aria-hidden="true"><div class="hud-h"><span>Диспетчерская · Атырау</span>'
       '<span id="hclk">--:--:--</span></div><ol id="hlog"></ol></div>')


_JS = r"""
(function(){
var svg=document.getElementById("hl");if(!svg||!svg.getBoundingClientRect)return;
var CFG=__CFG__,NS="http://www.w3.org/2000/svg",D=document,W=window;
var reduce=W.matchMedia&&W.matchMedia("(prefers-reduced-motion: reduce)").matches;
var ACC=26,HIST=520,LIVE=110,k=1,gs=1;
function E(n,a,p){var e=D.createElementNS(NS,n);if(a)for(var q in a)e.setAttribute(q,a[q]);if(p)p.appendChild(e);return e;}
function f1(v){return v.toFixed(1);}

/* --- геометрия: скругляем углы, считаем длины --- */
function rounded(pts,closed){
 var o=[],n=pts.length,i,j;
 for(i=0;i<n;i++){
  var B=pts[i],A=closed?pts[(i-1+n)%n]:pts[i-1],C=closed?pts[(i+1)%n]:pts[i+1];
  if(!A||!C){o.push(B);continue;}
  var ux=A[0]-B[0],uy=A[1]-B[1],lu=Math.hypot(ux,uy),vx=C[0]-B[0],vy=C[1]-B[1],lv=Math.hypot(vx,vy),
      r=Math.min(14,lu/2,lv/2),P=[B[0]+ux/lu*r,B[1]+uy/lu*r],Q=[B[0]+vx/lv*r,B[1]+vy/lv*r];
  for(j=0;j<=6;j++){var t=j/6,m=1-t;o.push([m*m*P[0]+2*m*t*B[0]+t*t*Q[0],m*m*P[1]+2*m*t*B[1]+t*t*Q[1]]);}
 }
 if(closed)o.push(o[0]);
 return o;
}
function prep(pts,closed){var p=rounded(pts,closed),L=[0],i;for(i=1;i<p.length;i++)L.push(L[i-1]+Math.hypot(p[i][0]-p[i-1][0],p[i][1]-p[i-1][1]));return{p:p,L:L,len:L[L.length-1],closed:closed};}
function norm(r,d){return r.closed?((d%r.len)+r.len)%r.len:Math.max(0,Math.min(r.len,d));}
function at(r,d){
 d=norm(r,d);var lo=0,hi=r.L.length-1;while(hi-lo>1){var m=(lo+hi)>>1;if(r.L[m]<=d)lo=m;else hi=m;}
 var a=r.p[lo],b=r.p[hi],l=(r.L[hi]-r.L[lo])||1,t=(d-r.L[lo])/l;
 return[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,Math.atan2(b[1]-a[1],b[0]-a[0])];
}
function sub(r,d0,d1){
 if(!r.closed){d0=Math.max(0,d0);d1=Math.min(r.len,d1);}
 if(d1-d0<0.5)return"";
 var s=at(r,d0),o="M"+f1(s[0])+","+f1(s[1]),kk,i,v,k0=r.closed?Math.floor(d0/r.len):0,k1=r.closed?Math.floor(d1/r.len):0;
 for(kk=k0;kk<=k1;kk++)for(i=1;i<r.L.length-1;i++){v=r.L[i]+kk*r.len;if(v>d0&&v<d1)o+="L"+f1(r.p[i][0])+","+f1(r.p[i][1]);}
 var e=at(r,d1);return o+"L"+f1(e[0])+","+f1(e[1]);
}
function near(r,x,y){var b=1e9,bd=0,d,q,h;for(d=0;d<=r.len;d+=1){q=at(r,d);h=Math.hypot(q[0]-x,q[1]-y);if(h<b){b=h;bd=d;}}return bd;}
function inside(P,x,y){var c=false,i,j;for(i=0,j=P.length-1;i<P.length;j=i++){var a=P[i],b=P[j];if((a[1]>y)!=(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])c=!c;}return c;}

/* --- силуэты сверху, нос по оси +x, размеры в экранных px --- */
var SH={
 truck:'<rect class="b" x="-15" y="-5.5" width="18" height="11" rx="1.2"/><rect class="b" x="4.5" y="-5" width="9.5" height="10" rx="2.2"/><rect class="w" x="10.5" y="-4" width="2.2" height="8" rx=".8"/>',
 van:'<rect class="b" x="-11" y="-5" width="22" height="10" rx="3"/><rect class="w" x="4" y="-4.1" width="3" height="8.2" rx="1"/><rect class="w r" x="-9" y="-3.4" width="11" height="6.8" rx="1"/>',
 pickup:'<rect class="b" x="-11" y="-5" width="10.5" height="10" rx="1.4"/><rect class="w r" x="-9.6" y="-3.6" width="7.6" height="7.2" rx=".8"/><rect class="b" x="0" y="-5" width="11" height="10" rx="2.6"/><rect class="w" x="5" y="-4.1" width="2.6" height="8.2" rx="1"/>'
};

var ht=D.getElementById("ht"),hc=D.getElementById("hc"),hz=D.getElementById("hz"),
    log=D.getElementById("hlog"),clk=D.getElementById("hclk"),tk=D.getElementById("htk");
var st=svg.querySelector(".static");if(st)st.parentNode.removeChild(st);

var cars=CFG.cars.map(function(c){
 var r=prep(CFG.routes[c.route],c.closed),o={c:c,r:r,d:c.d0||0,spd:0,ang:at(r,c.d0||0)[2],op:1,end:0,
  hold:c.hold||0,state:c.hold?"idle":"move",lost:false,alert:false,next:0};
 if(c.stop){o.stopD=near(r,c.stop[0],c.stop[1]);}
 if(c.gap){o.gap=[near(r,c.gap[0][0],c.gap[0][1]),near(r,c.gap[1][0],c.gap[1][1])];}
 o.g=E("g",{"class":"trk"},ht);
 o.ph=E("path",{"class":"ds-track-history"},o.g);
 o.pg=E("path",{"class":"ds-track-gap"},o.g);
 o.pl=E("path",{"class":"ds-track-live"},o.g);
 o.el=E("g",{"class":"car"},hc);
 E("circle",{"class":"ping",r:"10"},o.el);
 o.body=E("g",{},o.el);o.body.innerHTML=SH[c.kind];
 o.lb=E("g",{"class":"lbl",transform:"translate(16 -30)"},o.el);
 o.ld=E("line",{"class":"ld",x1:"-16",y1:"30",x2:"0",y2:"8"},o.lb);o.lw=120;o.pos=-1;
 o.lr=E("rect",{x:"0",y:"-12",height:"20"},o.lb);
 o.lt=E("text",{x:"8",y:"2"},o.lb);
 o.lr.setAttribute("width","120");
 return o;
});
var Z=CFG.zone;

/* --- часы и журнал событий: время Атырау, UTC+5 --- */
function now(sec){var s=new Date(Date.now()+5*36e5).toISOString().substr(11,8);return sec?s:s.substr(0,5);}
function ev(o,txt,s){
 var li=D.createElement("li");
 li.innerHTML='<time>'+now()+'</time><i class="s s-'+s+'"></i><span><b>'+o.c.id+'</b> '+txt+'</span>';
 if(log){log.insertBefore(li,log.firstChild);while(log.children.length>4)log.removeChild(log.lastChild);}
 if(tk){tk.innerHTML='<i class="s s-'+s+'"></i><span><b>'+o.c.id+'</b> '+txt+'</span>';}
}

/* подпись геозоны — над её левой вершиной */
var zl=E("g",{"class":"zl"},hc);E("rect",{x:"0",y:"-30",height:"22",width:"10"},zl);
var zt=E("text",{x:"8",y:"-14"},zl);zt.textContent="ГЕОЗОНА · "+CFG.zoneName.toUpperCase();
var SW=1280,SHh=700,OX=0,OY=0,zbox=null;
function scr(x,y){return[OX+x*k,OY+y*k];}
function measure(){var b=svg.getBoundingClientRect();SW=b.width;SHh=b.height;k=Math.max(SW/1600,SHh/1000)||1;gs=k<0.5?0.75:1;
 OX=SW-1600*k;OY=(SHh-1000*k)/2;
 var a=CFG.zone[0];zl.setAttribute("transform","translate("+a[0]+" "+a[1]+") scale("+(1/k).toFixed(4)+")");
 var w=0;try{w=zt.getComputedTextLength();}catch(e){}w=Math.round((w||90)+16);zl.firstChild.setAttribute("width",String(w));
 var z=scr(a[0],a[1]);zbox=[z[0],z[1]-30,w,22];}
/* подписи: первая позиция, что не вылезает за кадр и не наезжает на соседние */
function hit(a,b){return a[0]<b[0]+b[2]+6&&b[0]<a[0]+a[2]+6&&a[1]<b[1]+b[3]+4&&b[1]<a[1]+a[3]+4;}
function layout(){
 var taken=zbox?[zbox]:[],i,j,cb=[];
 for(i=0;i<cars.length;i++)if(cars[i].cp&&cars[i].op>0.05)cb.push([cars[i].cp[0]-15,cars[i].cp[1]-15,30,30,i]);
 for(i=0;i<cars.length;i++){var o=cars[i],c=o.cp;if(!c)continue;var w=o.lw,
  opts=[[16,-30],[-16-w,-30],[16,32],[-16-w,32]],pick=0;
  for(j=0;j<opts.length;j++){var bx=[c[0]+opts[j][0],c[1]+opts[j][1]-12,w,20];
   if(bx[0]<6||bx[0]+w>SW-6||bx[1]<6)continue;
   var ok=true,t;for(t=0;t<taken.length;t++)if(hit(bx,taken[t])){ok=false;break;}
   if(ok)for(t=0;t<cb.length;t++)if(cb[t][4]!==i&&hit(bx,cb[t])){ok=false;break;}
   if(ok){pick=j;break;}}
  var op=opts[pick];taken.push([c[0]+op[0],c[1]+op[1]-12,w,20]);
  if(o.pos!==pick||o.pw!==w){o.pos=pick;o.pw=w;
   o.lb.setAttribute("transform","translate("+op[0]+" "+op[1]+")");
   var lx=op[0]>0?0:w,ly=op[1]<0?8:-12;
   o.ld.setAttribute("x1",String(-op[0]));o.ld.setAttribute("y1",String(-op[1]));
   o.ld.setAttribute("x2",String(lx));o.ld.setAttribute("y2",String(ly));}
 }
}

function reset(o){o.d=o.c.d0||0;o.spd=0;o.hold=o.c.hold||0;o.state=o.hold?"idle":"move";o.lost=false;o.alert=false;
 if(o.stopD!=null&&!o.r.closed)o.stopD=near(o.r,o.c.stop[0],o.c.stop[1]);o.ang=at(o.r,o.d)[2];}

function step(o,dt){
 var r=o.r,c=o.c;
 if(o.end){ /* открытый маршрут кончился: гаснем и начинаем сначала */
  o.op-=dt/0.9;if(o.op<=0){o.op=0;o.end=0;reset(o);o.fadeIn=1;}return;}
 if(o.fadeIn){o.op=Math.min(1,o.op+dt/0.6);if(o.op>=1)o.fadeIn=0;}
 if(o.hold>0){o.hold-=dt;o.spd=0;if(o.hold<=0){o.state=o.alert?"alert":"move";ev(o,"начал движение","move");}return;}
 var tg=c.v,a0,a1,da;
 if(o.stopD!=null){var rem=o.stopD-o.d;if(rem>=0){tg=Math.min(tg,Math.sqrt(2*ACC*rem)+1.2);
  if(rem<0.6){o.d=o.stopD;o.spd=0;o.hold=c.stopT;o.state="idle";ev(o,"стоянка","idle");
   o.stopD=r.closed?o.stopD+r.len:null;return;}}}
 a0=at(r,o.d)[2];a1=at(r,o.d+24)[2];da=Math.abs(Math.atan2(Math.sin(a1-a0),Math.cos(a1-a0)));
 tg=Math.min(tg,c.v*(1-0.62*Math.min(1,da/1.3)));
 var m=ACC*dt,dv=tg-o.spd;o.spd+=Math.max(-m*1.8,Math.min(m,dv));if(o.spd<0)o.spd=0;
 o.d+=o.spd*dt;
 if(o.gap){
  if(!o.lost&&o.d>=o.gap[0]&&o.d<o.gap[1]){o.lost=true;o.state="lost";ev(o,"нет связи","lost");}
  if(o.lost&&o.d>=o.gap[1]){o.lost=false;o.state="move";ev(o,"связь восстановлена","move");}
 }
 if(c.zone&&!o.alert){var q=at(r,o.d);if(!inside(Z,q[0],q[1])){o.alert=true;o.state="alert";
  ev(o,"выезд за геозону «"+CFG.zoneName+"»","alert");hz.classList.add("hit");setTimeout(function(){hz.classList.remove("hit");},2600);}}
 if(!r.closed&&o.d>=r.len){o.d=r.len;o.end=1;}
}

function lbl(o){
 var c=o.c,t;
 if(o.state==="alert")t="ВЫЕЗД ЗА ГЕОЗОНУ";
 else if(o.state==="lost")t="НЕТ СВЯЗИ";
 else if(o.state==="idle"||o.spd<1)t="СТОИТ";
 else t=Math.max(5,Math.round(c.kmh*o.spd/c.v+Math.sin(Date.now()/900+c.v)*1.6))+" КМ/Ч";
 t=c.id.toUpperCase()+" · "+t;
 if(t!==o.txt){o.txt=t;o.lt.textContent=t;var w=0;try{w=o.lt.getComputedTextLength();}catch(e){}
  o.lw=Math.round((w||t.length*7.4)+16);o.lr.setAttribute("width",String(o.lw));}
}

function draw(o){
 var r=o.r,d=o.d,h=r.closed?d-HIST:Math.max(0,d-HIST),pd=d;
 var H="",G="",Lv="";
 if(o.gap&&d>=o.gap[0]){
  var g0=o.gap[0],g1=o.gap[1];
  if(o.lost){pd=g0;H=sub(r,h,g0-LIVE);Lv=sub(r,Math.max(h,g0-LIVE),g0);}
  else{H=sub(r,h,Math.min(g0,d-LIVE))+sub(r,g1,d-LIVE);G=sub(r,Math.max(h,g0),g1);Lv=sub(r,Math.max(g1,d-LIVE),d);}
 }else{H=sub(r,h,d-LIVE);Lv=sub(r,Math.max(h,d-LIVE),d);}
 o.ph.setAttribute("d",H||"M0,0");o.pg.setAttribute("d",G||"M0,0");o.pl.setAttribute("d",Lv||"M0,0");
 o.g.style.opacity=o.op;o.el.style.opacity=o.op;
 var p=at(r,pd),dd=p[2]-o.ang;dd=Math.atan2(Math.sin(dd),Math.cos(dd));
 if(!o.lost&&o.spd>0.5)o.ang+=dd*Math.min(1,o.dt*9);
 o.el.setAttribute("transform","translate("+f1(p[0])+" "+f1(p[1])+") scale("+(gs/k).toFixed(4)+")");
 o.body.setAttribute("transform","rotate("+(o.ang*180/Math.PI).toFixed(1)+")");
 var cls="car st-"+o.state;if(o.el.getAttribute("class")!==cls)o.el.setAttribute("class",cls);
 o.cp=scr(p[0],p[1]);
 lbl(o);
}

function tickClock(){if(clk)clk.textContent=now(1);}

measure();W.addEventListener("resize",measure);
var seed=new Date(Date.now()+5*36e5-6e4).toISOString().substr(11,5);
if(log)log.innerHTML='<li><time>'+seed+'</time><i class="s s-move"></i><span><b>КамАЗ 12</b> начал движение</span></li>'+
 '<li><time>'+seed+'</time><i class="s s-idle"></i><span><b>Hilux 03</b> стоянка на базе «'+CFG.zoneName+'»</span></li>';

if(reduce){ /* без движения: прокручиваем сценарий вперёд и рисуем один кадр */
 var i,t;for(t=0;t<11;t+=1/30)for(i=0;i<cars.length;i++){cars[i].dt=1/30;step(cars[i],1/30);}
 cars.forEach(draw);layout();tickClock();setInterval(tickClock,1000);return;
}

var run=true,raf=0,last=0;
function frame(ts){
 if(!run){raf=0;return;}
 var dt=last?Math.min(0.05,(ts-last)/1000):0.016;last=ts;
 for(var i=0;i<cars.length;i++){cars[i].dt=dt;step(cars[i],dt);draw(cars[i]);}
 layout();
 raf=requestAnimationFrame(frame);
}
function go(on){run=on&&!D.hidden;if(run&&!raf){last=0;raf=requestAnimationFrame(frame);}}
var hero=svg.closest?svg.closest(".ds-hero"):null,vis=true;
if(hero&&"IntersectionObserver" in W){new IntersectionObserver(function(e){vis=e[0].isIntersecting;go(vis);}).observe(hero);}
D.addEventListener("visibilitychange",function(){go(vis);});
for(var i0=0;i0<cars.length;i0++){cars[i0].dt=0;draw(cars[i0]);}layout();
tickClock();setInterval(tickClock,1000);go(true);
})();
"""


def script():
    cfg = {"routes": ROUTES, "zone": ZONE, "zoneName": ZONE_NAME, "cars": CARS}
    js = _JS.replace("__CFG__", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    # убираем отступы и пустые строки: скрипт встраивается в страницу
    js = "\n".join(l.strip() for l in js.strip().splitlines() if l.strip() and not l.strip().startswith("/*"))
    return f"<script>{js}</script>"
