# -*- coding: utf-8 -*-
"""
Живая диспетчерская в герое главной: три машины едут по настоящим улицам Атырау
поверх снимка Sentinel-2.

Координаты везде — пиксели десктопного кадра public/img/atyrau-city.* (1600×1000,
12,5 м/px). Маршруты сняты вручную по увеличенным фрагментам кадра.

Два режима, переключаются по ширине экрана (979 px):
  компьютер — весь город сразу: кадр и SVG прижаты вправо (object-position 100% /
              xMaxYMid slice), справа журнал событий, у машин подписи со скоростью;
  телефон   — «камера»: отдельный кадр в родном разрешении 10 м/px (atyrau-city-m.*),
              SVG-слой и снимок двигаются вместе (viewBox + transform), камера ведёт
              одну машину, на событии наезжает ближе, между машинами отъезжает
              на общий план. Внизу карточка машины со скоростью, наверху часы.

Сценарий (каждая машина показывает свой статус из дизайн-системы):
  Газель 07 — выезжает с установочного центра на Курмангазы, 70Б, едет на восток
              по широтной улице, после моста пропадает связь: маркер замирает на
              последней точке, разрыв потом рисуется пунктиром;
  КамАЗ 12  — кольцо через оба моста над Уралом, стоянка на восточном берегу;
  Hilux 03  — стоит на базе в промзоне, выезжает — срабатывает геозона.

Тексты событий формируются скриптом и в HTML не попадают: поисковики их не видят.
Без JS остаются снимок и статичные треки (на телефоне — только снимок).
Максимум три машины в кадре — по guidelines.md, «Движение».

prefers-reduced-motion НЕ останавливает машины: Android в режиме энергосбережения
сам включает этот флаг, и анимация замирала у обычных посетителей (11.10.2026).
Вместо остановки — спокойный режим: машины едут, камера на телефоне не наезжает
и не проезжает, а переставляется склейками; пульсаций нет. Для всех есть кнопка
«Пауза» (WCAG 2.2.2), выбор запоминается.
"""
import json

ROUTES = {
    # с установочного центра на север по улице x≈982, дальше на восток по y≈347
    "avenue": [[976, 390], [982, 380], [985, 347], [1074, 349], [1087, 351],
               [1170, 366], [1197, 355], [1330, 349], [1424, 350]],
    # кольцо: нижний мост → улица x≈1233 на север → верхний мост → улица x≈1085 на юг
    "ring": [[1085, 468], [1175, 467], [1233, 467], [1233, 353], [1197, 355],
             [1170, 366], [1087, 351]],
    # из промзоны на юго-запад вдоль железной дороги
    "base": [[1545, 319], [1488, 368], [1420, 426], [1360, 477], [1310, 520]],
}

ZONE = [[1400, 310], [1530, 262], [1570, 372], [1445, 425]]
ZONE_NAME = "База"

# установочный центр: координаты из карточки 2ГИС, пересчитанные в пиксели кадра
CENTER = {"pt": [976, 386], "label": "УСТАНОВКА · КУРМАНГАЗЫ, 70Б"}

# мобильный кадр: какую часть десктопных координат он покрывает [x, y, w, h]
MRECT = [760, 60, 920, 700]

CARS = [
    {"id": "Газель 07", "kind": "van", "route": "avenue", "closed": False,
     "v": 40, "kmh": 54, "hold": 2.6, "startTxt": "подключена, выезд с установки",
     "gap": [[1240, 353], [1335, 349]]},
    {"id": "КамАЗ 12", "kind": "truck", "route": "ring", "closed": True,
     "v": 34, "kmh": 46, "d0": 100, "stop": [1233, 410], "stopT": 3.6},
    {"id": "Hilux 03", "kind": "pickup", "route": "base", "closed": False,
     "v": 30, "kmh": 41, "hold": 9, "zone": True},
]


def _pts(p):
    return " ".join(f"{x},{y}" for x, y in p)


def media(alt):
    static = "".join(
        f'<polyline class="ds-track-history" points="{_pts(p + ([p[0]] if k == "ring" else []))}"/>'
        for k, p in ROUTES.items())
    return f"""<div class="ds-hero__media"><div class="hero-frame">
<picture>
<source media="(max-width: 979px)" type="image/avif" srcset="/img/atyrau-city-m.avif">
<source media="(max-width: 979px)" type="image/webp" srcset="/img/atyrau-city-m.webp">
<source type="image/avif" srcset="/img/atyrau-city.avif">
<img src="/img/atyrau-city.webp" width="1600" height="1000" alt="{alt}" loading="eager" fetchpriority="high" decoding="async"></picture>
<div class="ds-hero__scrim"></div>
<svg class="hero-live" id="hl" viewBox="0 0 1600 1000" preserveAspectRatio="xMaxYMid slice" aria-hidden="true" focusable="false">
<polygon class="ds-geofence" id="hz" points="{_pts(ZONE)}"/>
<g class="static">{static}</g>
<g id="ht"></g><g id="hc"></g>
</svg></div>
<div class="mchip" aria-hidden="true"><i></i><span class="mch-t">Диспетчерская ·</span><span>Атырау</span><span id="mclk">--:--</span></div>
<button type="button" class="hpause hp-m" aria-pressed="false">Пауза</button>
<div class="mcard" id="mcard" aria-hidden="true"></div>
</div>"""


HUD = ('<div class="hud"><div class="hud-h"><span aria-hidden="true">Диспетчерская</span>'
       '<span class="hud-r"><span id="hclk" aria-hidden="true">--:--:--</span>'
       '<button type="button" class="hpause" aria-pressed="false">Пауза</button></span></div>'
       '<ol id="hlog" aria-hidden="true"></ol></div>')


_JS = r"""
(function(){
var svg=document.getElementById("hl");if(!svg||!svg.getBoundingClientRect)return;
var CFG=__CFG__,NS="http://www.w3.org/2000/svg",D=document,W=window;
/* calm — спокойный режим при prefers-reduced-motion: всё едет, камера без наездов */
var calm=!!(W.matchMedia&&W.matchMedia("(prefers-reduced-motion: reduce)").matches);
var mq=W.matchMedia?W.matchMedia("(max-width: 979px)"):null;
var ACC=26,HIST=520,LIVE=110,k=1,gs=1,cam=false;
function E(n,a,p){var e=D.createElementNS(NS,n);if(a)for(var q in a)e.setAttribute(q,a[q]);if(p)p.appendChild(e);return e;}
function f1(v){return v.toFixed(1);}
function cl(v,a,b){return Math.max(a,Math.min(b,v));}

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
function norm(r,d){return r.closed?((d%r.len)+r.len)%r.len:cl(d,0,r.len);}
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
var ST={move:"в движении",idle:"стоит",lost:"нет связи",alert:"выезд за геозону"};

var ht=D.getElementById("ht"),hc=D.getElementById("hc"),hz=D.getElementById("hz"),
    log=D.getElementById("hlog"),clk=D.getElementById("hclk"),mclk=D.getElementById("mclk"),mcard=D.getElementById("mcard"),
    media=svg.closest?svg.closest(".ds-hero__media"):null,img=media?media.querySelector("img"):null;
var st=svg.querySelector(".static");if(st)st.parentNode.removeChild(st);

/* установочный центр */
var cp=E("g",{"class":"cpin"},ht);
E("circle",{"class":"pr pp",r:"9"},cp);E("circle",{"class":"pr",r:"9"},cp);E("rect",{"class":"pd",x:"-4",y:"-4",width:"8",height:"8"},cp);
var cl1=E("g",{"class":"cl"},cp);var clr=E("rect",{x:"14",y:"-11",height:"22",width:"10"},cl1);
var clt=E("text",{x:"22",y:"4"},cl1);clt.textContent=CFG.center.label;

var cars=CFG.cars.map(function(c,ix){
 var r=prep(CFG.routes[c.route],c.closed),o={c:c,ix:ix,r:r,d:c.d0||0,spd:0,ang:at(r,c.d0||0)[2],op:1,end:0,
  hold:c.hold||0,state:c.hold?"idle":"move",lost:false,alert:false,ev:""};
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
 o.lr=E("rect",{x:"0",y:"-12",height:"20",width:"120"},o.lb);
 o.lt=E("text",{x:"8",y:"2"},o.lb);
 return o;
});
var Z=CFG.zone;

/* прицел камеры на телефоне: четыре уголка вокруг ведомой машины */
var ret=E("g",{"class":"ret"},hc),rc=[];
for(var q=0;q<4;q++)rc.push(E("path",{},ret));
var lock=70;

/* --- часы и журнал событий: время Атырау, UTC+5 --- */
function now(sec){var s=new Date(Date.now()+5*36e5).toISOString().substr(11,8);return sec?s:s.substr(0,5);}
function ev(o,txt,s,focus){
 var li=D.createElement("li");
 li.innerHTML='<time>'+now()+'</time><i class="s s-'+s+'"></i><span><b>'+o.c.id+'</b> '+txt+'</span>';
 if(log){log.insertBefore(li,log.firstChild);while(log.children.length>2)log.removeChild(log.lastChild);}
 o.ev=now()+" · "+txt;
 if(cam&&focus){if(focus===3)focusOn(o.ix,true);else want(o.ix,focus===2);}
}

/* подпись геозоны — над её левой вершиной */
var zl=E("g",{"class":"zl"},hc);E("rect",{x:"0",y:"-30",height:"22",width:"10"},zl);
var zt=E("text",{x:"8",y:"-14"},zl);zt.textContent="ГЕОЗОНА · "+CFG.zoneName.toUpperCase();
var SW=1280,SHh=700,OX=0,OY=0,zbox=null,cbox=null,zw=90;
function scr(x,y){return[OX+x*k,OY+y*k];}
function tw(t){var w=0;try{w=t.getComputedTextLength();}catch(e){}return w;}

/* --- камера (телефон) --- */
/* первый кадр — установочный центр: оттуда выезжает Газель с новым трекером */
var R=CFG.mrect,SC=[1230,400],C={x:CFG.center.pt[0]+40,y:CFG.center.pt[1]-20,w:250},dir={mode:"follow",t:6.5,f:0,punch:0,since:0,q:[]};
function overW(){return Math.min(600,R[2],R[3]*SW/SHh)-8;}
function focusOn(i,punch){dir.f=i;dir.mode="follow";dir.t=punch?6.2:5.6;dir.punch=punch?2.6:0;dir.since=0;lock=72;}
/* событие во время показа другой машины ждёт своей очереди: камера не дёргается */
function want(i,punch){
 if(dir.mode==="follow"&&dir.f===i){if(punch){dir.punch=2.6;lock=72;}dir.t=Math.max(dir.t,4.5);return;}
 if(dir.mode==="follow"&&dir.since<3.4){dir.q=dir.q.filter(function(x){return x[0]!==i;});dir.q.push([i,punch,0]);if(dir.q.length>2)dir.q.shift();return;}
 focusOn(i,punch);}
function camTarget(){
 if(dir.mode==="over")return[SC[0],SC[1],overW()];
 var o=cars[dir.f];if(o.op<0.35){focusOn((dir.f+1)%cars.length,false);o=cars[dir.f];}
 /* масштаб держим около 1,2 экранного px на пиксель снимка, иначе на планшете кадр мылится */
 var p=at(o.r,o.lost?o.gap[0]:o.d),ld=Math.min(34,o.spd*0.85),base=Math.max(290,SW/1.3),w=calm?base:dir.punch>0?Math.max(210,SW/1.75):base;
 /* машина держится в видимой части кадра — над карточкой внизу */
 return[p[0]+Math.cos(o.ang)*ld,p[1]+Math.sin(o.ang)*ld+CARD/2*w/SW,w];
}
function camStep(dt,snap){
 dir.t-=dt;dir.since+=dt;if(dir.punch>0)dir.punch-=dt;
 dir.q=dir.q.filter(function(x){x[2]+=dt;return x[2]<7;});
 if(dir.q.length&&(dir.since>=3.4||dir.t<=0)){var n=dir.q.shift();focusOn(n[0],n[1]);}
 else if(dir.t<=0){if(dir.mode==="follow"){dir.mode="over";dir.t=3;}else focusOn((dir.f+1)%cars.length,false);}
 var T=camTarget();
 if(calm){ /* склейки: камера стоит, пока машина в кадре, потом переставляется сразу */
  var tw=Math.min(T[2],overW()),hh=tw*SHh/SW,key=dir.mode+dir.f,o=cars[dir.f],cx=T[0],cy=T[1];
  if(dir.mode!=="over"){cx+=Math.cos(o.ang)*tw*0.26;cy+=Math.sin(o.ang)*hh*0.14;}
  if(snap||dir.cut!==key||Math.abs(T[0]-C.x)>tw*0.42||Math.abs(T[1]-C.y)>hh*0.36){C.x=cx;C.y=cy;C.w=tw;dir.cut=key;}
  applyCam();return;
 }
 var a=snap?1:1-Math.exp(-dt*2.4),az=snap?1:1-Math.exp(-dt*1.7);
 C.x+=(T[0]-C.x)*a;C.y+=(T[1]-C.y)*a;C.w+=(Math.min(T[2],overW())-C.w)*az;
 applyCam();
}
function applyCam(){
 var w=Math.min(C.w,overW()),h=w*SHh/SW,vx=cl(C.x-w/2,R[0],R[0]+R[2]-w),vy=cl(C.y-h/2,R[1],R[1]+R[3]-h);
 k=SW/w;OX=-vx*k;OY=-vy*k;
 svg.setAttribute("viewBox",f1(vx)+" "+f1(vy)+" "+f1(w)+" "+f1(h));
 if(img)img.style.transform="translate("+f1((R[0]-vx)*k)+"px,"+f1((R[1]-vy)*k)+"px) scale("+k.toFixed(4)+")";
 overlays();
}

function overlays(){
 var a=Z[0];zl.setAttribute("transform","translate("+a[0]+" "+a[1]+") scale("+(1/k).toFixed(4)+")");
 var z=scr(a[0],a[1]);zbox=[z[0],z[1]-30,zw,22];
 var c=CFG.center.pt;cp.setAttribute("transform","translate("+c[0]+" "+c[1]+") scale("+(gs/k).toFixed(4)+")");
 var s=scr(c[0],c[1]),lw=(cw+16)*gs,fl=s[0]+14*gs+lw>SW-8;
 if(fl!==cflip){cflip=fl;cl1.setAttribute("transform",fl?"translate("+(-(cw+16+28))+" 0)":"translate(0 0)");}
 cbox=[fl?s[0]-14*gs-lw:s[0]+14*gs,s[1]-11*gs,lw,22*gs];
}

var cw=200,cflip=null,CARD=0;
function setMode(){
 cam=!!(mq&&mq.matches)&&!!media;
 if(media)media.classList.toggle("cam",cam);
 var b=(cam?media:svg).getBoundingClientRect();SW=b.width||1;SHh=b.height||1;
 zw=Math.round((tw(zt)||90)+16);zl.firstChild.setAttribute("width",String(zw));
 cw=Math.round(tw(clt)||190);clr.setAttribute("width",String(cw+16));
 if(cam){
  CARD=mcard?(mcard.getBoundingClientRect().height||104)+14:0;
  gs=0.9;svg.setAttribute("preserveAspectRatio","none");
  if(img){img.style.width=R[2]+"px";img.style.height=R[3]+"px";}
  applyCam();
 }else{
  if(img)img.removeAttribute("style");
  svg.setAttribute("viewBox","0 0 1600 1000");svg.setAttribute("preserveAspectRatio","xMaxYMid slice");
  k=Math.max(SW/1600,SHh/1000)||1;gs=k<0.5?0.75:1;OX=SW-1600*k;OY=(SHh-1000*k)/2;overlays();
 }
}

/* подписи (компьютер): первая позиция, что не вылезает за кадр и не наезжает на соседние */
function hit(a,b){return a[0]<b[0]+b[2]+6&&b[0]<a[0]+a[2]+6&&a[1]<b[1]+b[3]+4&&b[1]<a[1]+a[3]+4;}
function layout(){
 if(cam)return;
 var taken=[zbox,cbox].filter(Boolean),i,j,cb=[];
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
 if(o.hold>0){o.hold-=dt;o.spd=0;if(o.hold<=0){o.state=o.alert?"alert":"move";
  if(c.startTxt&&o.d<1)ev(o,c.startTxt,"move",2);else ev(o,"начал движение","move",0);}return;}
 var tg=c.v,a0,a1,da;
 if(o.stopD!=null){var rem=o.stopD-o.d;if(rem>=0){tg=Math.min(tg,Math.sqrt(2*ACC*rem)+1.2);
  if(rem<0.6){o.d=o.stopD;o.spd=0;o.hold=c.stopT;o.state="idle";ev(o,"стоянка","idle",2);
   o.stopD=r.closed?o.stopD+r.len:null;return;}}}
 a0=at(r,o.d)[2];a1=at(r,o.d+24)[2];da=Math.abs(Math.atan2(Math.sin(a1-a0),Math.cos(a1-a0)));
 tg=Math.min(tg,c.v*(1-0.62*Math.min(1,da/1.3)));
 var m=ACC*dt,dv=tg-o.spd;o.spd+=Math.max(-m*1.8,Math.min(m,dv));if(o.spd<0)o.spd=0;
 o.d+=o.spd*dt;
 if(o.gap){
  if(!o.lost&&o.d>=o.gap[0]&&o.d<o.gap[1]){o.lost=true;o.state="lost";ev(o,"нет связи","lost",2);}
  if(o.lost&&o.d>=o.gap[1]){o.lost=false;o.state="move";ev(o,"связь восстановлена","move",1);}
 }
 if(c.zone&&!o.alert){var p=at(r,o.d);if(!inside(Z,p[0],p[1])){o.alert=true;o.state="alert";
  ev(o,"выезд за геозону «"+CFG.zoneName+"»","alert",3);hz.classList.add("hit");setTimeout(function(){hz.classList.remove("hit");},2600);}}
 if(!r.closed&&o.d>=r.len){o.d=r.len;o.end=1;}
}

function kmh(o){return o.state==="idle"||o.state==="lost"||o.spd<1?0:Math.max(5,Math.round(o.c.kmh*o.spd/o.c.v+Math.sin(Date.now()/900+o.c.v)*1.6));}
function lbl(o){
 var t=o.state==="alert"?"ВЫЕЗД ЗА ГЕОЗОНУ":o.state==="lost"?"НЕТ СВЯЗИ":kmh(o)?kmh(o)+" КМ/Ч":"СТОИТ";
 t=o.c.id.toUpperCase()+" · "+t;
 if(t!==o.txt){o.txt=t;o.lt.textContent=t;o.lw=Math.round((tw(o.lt)||t.length*7.4)+16);o.lr.setAttribute("width",String(o.lw));}
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
 o.pt=p;o.cp=scr(p[0],p[1]);
 if(!cam)lbl(o);
}

/* прицел и карточка машины (телефон) */
var lastCard=0;
function hud(dt){
 if(!cam){ret.style.opacity=0;return;}
 var o=cars[dir.f],show=dir.mode==="follow"&&o.op>0.3;
 lock=calm?34:lock+(34-lock)*(1-Math.exp(-dt*7));
 ret.style.opacity=show?1:0;ret.setAttribute("class","ret"+(o.state==="alert"?" al":o.state==="lost"?" ls":""));
 if(o.pt){var s=lock/2,a=Math.min(9,s*0.45),dd=[[-1,-1],[1,-1],[1,1],[-1,1]];
  for(var i=0;i<4;i++){var x=dd[i][0]*s,y=dd[i][1]*s;
   rc[i].setAttribute("d","M"+f1(x)+","+f1(y-dd[i][1]*a)+"V"+f1(y)+"H"+f1(x-dd[i][0]*a));}
  ret.setAttribute("transform","translate("+f1(o.pt[0])+" "+f1(o.pt[1])+") scale("+(1/k).toFixed(4)+")");}
 lastCard-=dt;if(lastCard>0||!mcard)return;lastCard=0.2;
 var v=kmh(o),stt=o.state;
 mcard.className="mcard st-"+stt;
 mcard.innerHTML='<div class="mc-top"><b>'+o.c.id+'</b><span><i class="s s-'+stt+'"></i>'+ST[stt]+'</span></div>'+
  '<div class="mc-mid"><span class="mc-v">'+(stt==="lost"?"—":v)+'</span><span class="mc-u">км/ч</span>'+
  '<span class="mc-e">'+(o.ev||"на линии")+'</span></div>';
}

function tickClock(){var t=now(1);if(clk)clk.textContent=t;if(mclk)mclk.textContent=t;}

var seed=new Date(Date.now()+5*36e5-6e4).toISOString().substr(11,5);
if(log)log.innerHTML='<li><time>'+seed+'</time><i class="s s-move"></i><span><b>КамАЗ 12</b> начал движение</span></li>'+
 '<li><time>'+seed+'</time><i class="s s-idle"></i><span><b>Hilux 03</b> стоянка на базе «'+CFG.zoneName+'»</span></li>';
cars[0].ev=now()+" · установка трекера";cars[1].ev=seed+" · начал движение";cars[2].ev=seed+" · стоянка на базе";

setMode();
var rt;W.addEventListener("resize",function(){clearTimeout(rt);rt=setTimeout(function(){setMode();frameOnce(0);},120);});
function frameOnce(dt){for(var i=0;i<cars.length;i++){cars[i].dt=dt;draw(cars[i]);}if(cam)camStep(dt,dt===0);layout();hud(dt||0.016);}


var run=true,raf=0,last=0;
function frame(ts){
 if(!run){raf=0;return;}
 /* в энергосбережении кадров бывает 30 и меньше: шаг по реальному времени, с потолком */
 var dt=last?Math.min(0.1,(ts-last)/1000):0.016;last=ts;
 for(var i=0;i<cars.length;i++){cars[i].dt=dt;step(cars[i],dt);draw(cars[i]);}
 if(cam)camStep(dt);layout();hud(dt);
 raf=requestAnimationFrame(frame);
}
/* пауза: кнопка в журнале (компьютер) и на карте (телефон), выбор запоминается */
var paused=false;try{paused=localStorage.getItem("hero-pause")==="1";}catch(e){}
var btns=[].slice.call(D.querySelectorAll(".hpause"));
function setBtn(){btns.forEach(function(b){b.setAttribute("aria-pressed",paused?"true":"false");
 b.setAttribute("aria-label",paused?"Запустить движение на карте":"Остановить движение на карте");
 b.innerHTML=(paused?'<i class="ic-pl"></i>Пуск':'<i class="ic-pa"></i>Пауза');});}
btns.forEach(function(b){b.addEventListener("click",function(){paused=!paused;
 try{localStorage.setItem("hero-pause",paused?"1":"0");}catch(e){}setBtn();go(vis);});});
setBtn();
function go(on){run=on&&!D.hidden&&!paused;if(run&&!raf){last=0;raf=requestAnimationFrame(frame);}}
var hero=svg.closest?svg.closest(".ds-hero"):null,vis=true;
if(hero&&"IntersectionObserver" in W){new IntersectionObserver(function(e){vis=e[0].isIntersecting;go(vis);}).observe(hero);}
D.addEventListener("visibilitychange",function(){go(vis);});
frameOnce(0);tickClock();setInterval(tickClock,1000);go(true);
})();
"""


def script():
    cfg = {"routes": ROUTES, "zone": ZONE, "zoneName": ZONE_NAME, "cars": CARS,
           "center": CENTER, "mrect": MRECT}
    js = _JS.replace("__CFG__", json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    # убираем отступы и пустые строки: скрипт встраивается в страницу
    js = "\n".join(l.strip() for l in js.strip().splitlines() if l.strip() and not l.strip().startswith("/*"))
    return f"<script>{js}</script>"
