import json,sys
W=sys.argv[1]
caps=json.load(open(W+'/caps.json'))['cards']
def wt(i,j=0): return caps[i]['w'][j]['s']
SC=[
 dict(s=12.0,e=18.9,title="المغالطة تمنعك من:",rows=[["تعمل المحتوى",wt(2,-1)],["تشارك معلوماتك وخبراتك",wt(3)],["تسوّق لنفسك بالمحتوى",wt(4)]]),
 dict(s=28.71,e=39.69,type="eq",text="الصمت ≠ العلم",at=29.3),
 dict(s=39.71,e=56.95,title="الشطّار الناشطين",rows=[["مهندسين شطار في مجالاتهم",wt(12)],["بيألفوا كتب",wt(13,-1)],["نشطين على السوشيل ميديا",wt(14)],["غرضهم نفع المجتمع",wt(16)]]),
 dict(s=56.97,e=63.75,title="فوائد حقيقية",rows=[["براند قوي على السوشيل ميديا",wt(18)],["فرص حقيقية في مجالاتهم",wt(19)]]),
 dict(s=70.8,e=77.0,title="الجاي إن شاء الله",rows=[["استراتيجيات قوية في صناعة المحتوى",wt(23)],["على لينكد إن",wt(24)]]),
]
Y0=170
for c in SC:
    n=len(c.get('rows',[])); H=260 if c.get('type')=='eq' else 150+n*112+36
    c['H']=H; c['gb']=Y0+H+20
js="""<script>
/* ===== كروت الشرح — مولّدة من gen_cards.py ===== */
(function(){
const CARDS=%s;
const _rd=rDown; rDown=function(gb,lines){const r=_rd(gb,lines); const h=r.h, w=Math.min(Math.round(h*0.66),1000); return {x:Math.round((W-w)/2),y:r.y,w:w,h:h,r:44};};
const SC_=[];let _t=0;
CARDS.forEach(c=>{ SC_.push({s:_t,e:c.s,m:R_FULL}); SC_.push({s:c.s,e:c.e,m:R_DOWN,gb:c.gb}); _t=c.e; });
SC_.push({s:_t,e:999,m:R_FULL});
SCENES=SC_;
const ONC=()=>ONACC||'#FFFFFF';
function fit(txt,f0,wmax){ let f=f0; X.font='800 '+f+'px '+FONT; X.direction='rtl'; while(X.measureText(txt).width>wmax&&f>26){ f-=2; X.font='800 '+f+'px '+FONT; } return f; }
function cardScenes(t){
  const cardCol=(THEME_RAW&&THEME_RAW.card)||'#FFFFFF';
  for(const c of CARDS){ if(t<c.s+TR-0.1||t>c.e) continue;
    const k=ease(pr(t,c.s+TR-0.1,c.s+TR+0.3)), out=1-pr(t,c.e-0.25,c.e);
    X.save(); X.globalAlpha=k*out; X.translate(0,(1-k)*-40);
    sh(36,14,0.16); X.fillStyle=cardCol; rr(60,%d,960,c.H,44); X.fill(); nsh();
    if(c.type==='eq'){
      const kk=ease(pr(t,c.at,c.at+0.4)); X.save(); X.globalAlpha*=kk; X.translate(540,%d+c.H/2); X.scale(0.9+0.1*kk,0.9+0.1*kk);
      const f=fit(c.text,92,860); X.font='900 '+f+'px '+FONT; X.fillStyle=INK; X.textAlign='center'; X.textBaseline='middle'; X.direction='rtl'; X.fillText(c.text,0,0); X.restore();
    } else {
      X.font='900 54px '+FONT; X.direction='rtl'; X.textAlign='right'; X.textBaseline='middle'; X.fillStyle=INK; X.fillText(c.title,1020-48,%d+62);
      const tw=X.measureText(c.title).width; X.fillStyle=ACC; rr(1020-48-tw,%d+104,tw,6,3); X.fill();
      c.rows.forEach((r,i)=>{ const y=%d+150+i*112, kr=ease(pr(t,r[1],r[1]+0.35)); if(kr<=0) return;
        X.save(); X.globalAlpha*=kr; X.translate((1-kr)*50,0);
        X.fillStyle=rgba(ACC,0.09); rr(96,y,888,92,46); X.fill();
        X.fillStyle=ACC; X.beginPath(); X.arc(984-46,y+46,34,0,Math.PI*2); X.fill();
        X.font='900 36px '+FONT; X.fillStyle=ONC(); X.textAlign='center'; X.textBaseline='middle'; X.direction='ltr'; X.fillText(String(i+1),984-46,y+49);
        const f=fit(r[0],42,740); X.font='800 '+f+'px '+FONT; X.fillStyle=INK; X.textAlign='right'; X.direction='rtl'; X.textBaseline='middle'; X.fillText(r[0],984-46-34-22,y+48);
        X.restore(); });
    }
    X.restore(); }
}
SCENE_LIST.push(['cardScenes',cardScenes]);
})();
</script>
""" % (json.dumps(SC,ensure_ascii=False),Y0,Y0,Y0,Y0,Y0)
h=open(W+'/compose.html',encoding='utf-8').read()
a=h.find('/* ===== كروت الشرح'); 
if a>=0:
    a=h.rfind('<script>',0,a); b=h.find('</script>',a)+len('</script>\n'); h=h[:a]+h[b:]
h=h.replace('</body></html>',js+'</body></html>')
open(W+'/compose.html','w',encoding='utf-8').write(h)
sfx={"outro":0,"whoosh_up":[round(c['s']+0.3,2) for c in SC],"tap":[round(r[1],2) for c in SC for r in c.get('rows',[])]+[round(c['at'],2) for c in SC if c.get('type')=='eq']}
json.dump(sfx,open(W+'/sfx.json','w'))
print(len(SC),'scenes',sfx)
