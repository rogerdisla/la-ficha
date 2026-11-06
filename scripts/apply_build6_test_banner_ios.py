#!/usr/bin/env python3
"""La Ficha Build 6 stage 2: temporary native Google demo-banner test button.

Adds ONE native-only Quick Menu test control to the Build 6 UMP HTML.
Deliberately does NOT show ads automatically or alter La Ficha's layout.
A Google demo ad appears only when the tester taps the control; it disappears
after 30 seconds. It may briefly overlay lower screen content during testing.
Not a production ad placement. Do not ship this temporary control to App Store.
"""
from pathlib import Path
from datetime import datetime
import shutil, sys

root=Path.home()/"la-ficha-ios"
file=root/"www"/"index.html"
if not file.is_file():
    sys.exit("ERROR: iOS HTML not found; no files changed.")
src=file.read_text(encoding="utf-8")
stage1="lf-build6-ump-privacy-v1"
tag="lf-build6-native-test-banner-v1"
anchor='<button id="lfPrivacyOptionsBtn" type="button" hidden aria-label="Privacy Options">Privacy Options</button>'
if tag in src:
    sys.exit("INFO: test banner patch already installed; no changes.")
if stage1 not in src or src.count(anchor)!=1:
    sys.exit("ERROR: Build 6 UMP baseline missing/unexpected; no changes.")
if 'lf-ios-build4-5sec-winner-haptic' not in src:
    sys.exit("ERROR: stable winner haptics missing; no changes.")
if src.lower().count('</body>')!=1:
    sys.exit("ERROR: expected one closing body tag; no changes.")

button='<button id="lfBuild6TestBannerBtn" type="button" hidden aria-label="Show test ad">Show Test Ad</button>'
updated=src.replace(anchor, anchor+button, 1)
style="""
<style id="lf-build6-test-banner-style">
#lfBuild6TestBannerBtn[hidden] { display:none!important; }
</style>
"""
updated=updated.replace('</head>',style+'\n</head>',1)

script=r"""
<script id="lf-build6-native-test-banner-v1">
/* Temporary native iPhone QA control. Uses Google's official iOS demo ad.
   The normal score screen remains ad-free unless the tester opts in here. */
(function(){
  'use strict';
  function ready(){
    const cap=window.Capacitor;
    if(!cap || typeof cap.isNativePlatform!=='function' || !cap.isNativePlatform()) return;
    const ad=cap.Plugins && cap.Plugins.AdMob;
    const btn=document.getElementById('lfBuild6TestBannerBtn');
    if(!ad || !btn)return;
    btn.hidden=false;
    let busy=false,shown=false,initialized=false,autoHide=null;
    const langEs=document.getElementById('langEs');
    function label(){
      const es=!!(langEs&&langEs.classList.contains('active'));
      const s=shown?(es?'Ocultar anuncio de prueba':'Hide Test Ad'):
        (es?'Mostrar anuncio de prueba':'Show Test Ad');
      btn.textContent=s;btn.setAttribute('aria-label',s);
    }
    label();
    if(langEs&&window.MutationObserver){
      new MutationObserver(label).observe(langEs,{attributes:true,attributeFilter:['class']});
    }
    async function hide(){
      if(autoHide!==null){clearTimeout(autoHide);autoHide=null;}
      if(!shown)return;
      try{await ad.hideBanner();}
      catch(e){console.warn('La Ficha test ad hide issue',e);}
      shown=false;label();
    }
    btn.addEventListener('click',async function(){
      if(busy)return;
      busy=true;btn.disabled=true;
      try{
        if(shown){await hide();return;}
        let info=await ad.requestConsentInfo();
        if(info.isConsentFormAvailable && info.status==='REQUIRED'){
          info=await ad.showConsentForm();
        }
        window.lfBuild6CanRequestAds=!!info.canRequestAds;
        if(!info.canRequestAds){
          alert(langEs&&langEs.classList.contains('active')?
            'Google aún no permite solicitar anuncios con la configuración actual de privacidad.':
            'Google has not permitted ad requests under the current privacy settings.');
          return;
        }
        if(!initialized){await ad.initialize();initialized=true;}
        // Test only. Positioned at native screen bottom; can overlay content.
        await ad.showBanner({
          adId:'ca-app-pub-3940256099942544/2934735716',
          isTesting:true,
          adSize:'ADAPTIVE_BANNER',
          position:'BOTTOM_CENTER',
          margin:0
        });
        shown=true;label();
        autoHide=setTimeout(function(){void hide();},30000);
      }catch(e){
        console.error('La Ficha native demo banner failed',e);
        alert('Google test banner failed; see Xcode logs. No production ads requested.');
      }finally{busy=false;btn.disabled=false;}
    });
    document.addEventListener('visibilitychange',function(){
      if(document.hidden && shown){void hide();}
    });
  }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',ready,{once:true});
  }else{ready();}
})();
</script>
"""
updated=updated.replace('</body>',script+'\n</body>',1)
if updated.count('id="lfBuild6TestBannerBtn"')!=1 or updated.count(tag)!=1:
    sys.exit("ERROR: patch verification failed; no changes.")

bk=root.parent/"la-ficha-ios-backups"
bk.mkdir(parents=True,exist_ok=True)
dest=bk/("index-pre-build6-test-ad-"+datetime.now().strftime("%Y%m%d-%H%M%S")+".html")
shutil.copy2(file,dest)
file.write_text(updated,encoding="utf-8")
print("SUCCESS: optional Google demo banner test added to Build 6 Quick Menu.")
print("Saved HTML:",file)
print("Backup:",dest)
print("No ads load automatically. Tap Show Test Ad only on native iPhone.")
print("Test banner automatically hides after 30 seconds; not production placement.")
print("Next: npx cap sync ios")
