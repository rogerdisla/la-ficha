#!/usr/bin/env python3
"""La Ficha Build 7 (native iOS): automatic Google TEST banner near existing ad slot.

Changes only ~/la-ficha-ios/www/index.html. Requires tested Build 6 patches.
Keeps the Google demo unit ID, published UMP consent checks, bilingual Privacy Options,
winning score gear, camera/scoring and five-second haptics unchanged.
Converts the temporary menu-controlled demo ad into an automatic consent-gated ad.
Backs up the HTML and refuses to patch unexpected HTML.
"""
from pathlib import Path
from datetime import datetime
import json
import re
import shutil
import sys

ROOT = Path.home() / 'la-ficha-ios'
FILE = ROOT / 'www' / 'index.html'
PKG = ROOT / 'package.json'
TAG = 'lf-ios-build7-auto-test-banner-v1'
if not FILE.is_file() or not PKG.is_file():
    sys.exit('ERROR: Missing local iOS HTML or package.json. No files changed.')
deps = json.loads(PKG.read_text(encoding='utf-8')).get('dependencies', {})
if deps.get('@capacitor-community/admob') is None:
    sys.exit('ERROR: AdMob dependency missing. No files changed.')
s = FILE.read_text(encoding='utf-8')
if TAG in s:
    sys.exit('INFO: Build 7 already applied. No files changed.')
for marker in ('lf-ios-build3-camera-visual', 'lf-ios-build4-5sec-winner-haptic',
               'lf-build6-ump-privacy-v1', 'lf-build6-native-test-banner-v1',
               'id="lfPrivacyOptionsBtn"', 'id="lfBuild6TestBannerBtn"'):
    if marker not in s:
        sys.exit(f'ERROR: expected Build 6 baseline marker missing: {marker!r}. No files changed.')

# Require a genuine DOM element for the existing ad slot rather than matching CSS only.
if not re.search(r'<[a-z][^>]*\bclass=["\'][^"\']*\blf-ad-slot\b(?=\s|["\'])', s, flags=re.I):
    if not re.search(r'<[a-z][^>]*\bid=["\']lf-ad-slot["\']', s, flags=re.I):
        sys.exit('ERROR: existing lf-ad-slot HTML element not found. No files changed.')

# Remove only the Build 6 experimental button, demo-banner CSS, and test JS.
patterns = [
    (r'<button\s+id="lfBuild6TestBannerBtn"[^>]*>Show Test Ad</button>', 1, 'test menu button'),
    (r'<style\s+id="lf-build6-test-banner-style">.*?</style\s*>', 1, 'test-only CSS'),
    (r'<script\s+id="lf-build6-native-test-banner-v1">.*?</script\s*>', 1, 'test banner JS'),
    (r'<script\s+id="lf-build6-ump-privacy-v1">.*?</script\s*>', 1, 'old UMP JS'),
]
for pat, expected, label in patterns:
    count = len(re.findall(pat, s, flags=re.S | re.I))
    if count != expected:
        sys.exit(f'ERROR: expected one {label}, found {count}. No files changed.')
for pat, _, label in patterns:
    s = re.sub(pat, '', s, count=1, flags=re.S | re.I)

# Keep the existing privacy button, and preserve its CSS that hides it unless required.
new_style = '''
<style id="lf-build7-ad-slot-style">
/* Only hide the old placeholder label AFTER a native test ad has loaded.
   No sizing, position, spacing, scoreboard, or camera styles are modified. */
.lf-ad-slot.lf-build7-ad-loaded .lf-ad-slot__label,
.lf-ad-slot.lf-build7-ad-loaded .lf-ad-slot__badge { opacity:0 !important; }
</style>
'''
if len(re.findall(r'</head\s*>', s, flags=re.I)) != 1:
    sys.exit('ERROR: expected exactly one </head>. No files changed.')
s = re.sub(r'</head\s*>', new_style + '\n</head>', s, count=1, flags=re.I)

new_script = r'''
<script id="lf-ios-build7-auto-test-banner-v1">
/* Build 7: automatic consent-gated Google demo banner near the existing ad slot.
   Native ads overlay the WKWebView, so this uses a bottom margin based on the
   *measured* ad placeholder. We still require an iPhone screenshot for alignment.
   TEST UNIT ONLY. Do not replace it with the production unit until approval. */
(function(){
  'use strict';
  const TEST_IOS_UNIT = 'ca-app-pub-3940256099942544/2934735716';
  function start(){
    const cap=window.Capacitor;
    if(!cap || typeof cap.isNativePlatform!=='function' || !cap.isNativePlatform())return;
    const ad=cap.Plugins && cap.Plugins.AdMob;
    const privacyBtn=document.getElementById('lfPrivacyOptionsBtn');
    if(!ad || !privacyBtn){console.warn('Build 7: AdMob/Privacy Options missing');return;}
    const slot=document.querySelector('.lf-ad-slot')||document.getElementById('lf-ad-slot');
    const esBtn=document.getElementById('langEs');
    let consentInfo=null, sdkReady=false, bannerShown=false, requestedMargin=null;
    let busy=false, rerun=false, renderTimer=null, loaded=false;

    function isEs(){return !!(esBtn && esBtn.classList.contains('active'));}
    function translateLabels(){
      const title=isEs()?'Opciones de privacidad':'Privacy Options';
      privacyBtn.textContent=title;privacyBtn.setAttribute('aria-label',title);
      if(!slot)return;
      // Change only the text nodes, preserving the separate AD badge and styling.
      const walker=document.createTreeWalker(slot,NodeFilter.SHOW_TEXT);
      let node;
      while((node=walker.nextNode())){
        const t=node.nodeValue||'';
        const match=t.match(/^(\s*)(Advertisement|Publicidad)(\s*)$/i);
        if(match)node.nodeValue=match[1]+(isEs()?'Publicidad':'Advertisement')+match[3];
      }
    }
    translateLabels();
    if(esBtn&&window.MutationObserver){
      new MutationObserver(translateLabels).observe(esBtn,{attributes:true,attributeFilter:['class']});
    }

    function applyConsent(info){
      consentInfo=info||null;
      const privacyStatus=String(info&&info.privacyOptionsRequirementStatus||'').toUpperCase();
      privacyBtn.hidden=(privacyStatus!=='REQUIRED');
      window.lfBuild7CanRequestAds=!!(info&&info.canRequestAds);
    }

    // The native standard BANNER is 320 by 50 iOS points. The reserved slot
    // is ~50 high; only position the banner when the slot can fit it.
    function measuredMargin(){
      if(!slot)return null;
      const r=slot.getBoundingClientRect();
      const h=window.innerHeight;
      if(r.width<320 || r.height<44 || r.top<0 || r.bottom>h-1)return null;
      // Center a 50-point banner vertically in the 47-60-point reserved slot.
      const desiredBottom=r.top+(r.height/2)+25;
      const margin=Math.round(h-desiredBottom);
      if(margin<0 || margin>Math.min(280,h*0.5))return null;
      return margin;
    }

    function blockingDialog(){
      // Native views can float over HTML modals; suppress banners while open.
      const elems=document.querySelectorAll(
        '.modal, .liveCameraModal, .winnerOverlay, .winnerScreen, [role="dialog"], [aria-modal="true"]'
      );
      for(const el of elems){
        const st=window.getComputedStyle(el);
        if(st.display!=='none' && st.visibility!=='hidden' && st.opacity!=='0'){
          const r=el.getBoundingClientRect();
          if(r.width>130 && r.height>120)return true;
        }
      }
      return false;
    }

    async function removeBanner(){
      if(bannerShown){
        try{await ad.removeBanner();}
        catch(e){console.warn('Build 7: banner removal',e);}
        bannerShown=false;
      }
      loaded=false;requestedMargin=null;
      if(slot)slot.classList.remove('lf-build7-ad-loaded');
    }

    function schedule(){
      if(renderTimer!==null)return;
      renderTimer=setTimeout(function(){renderTimer=null;void updateBanner();},175);
    }
    async function updateBanner(){
      if(busy){rerun=true;return;}
      busy=true;
      try{
        const margin=measuredMargin();
        const can=!!(consentInfo&&consentInfo.canRequestAds);
        if(!can || margin===null || document.hidden || blockingDialog()){
          await removeBanner();return;
        }
        if(bannerShown && Math.abs(margin-requestedMargin)<3)return;
        if(bannerShown)await removeBanner();
        if(!sdkReady){await ad.initialize();sdkReady=true;}
        await ad.showBanner({
          adId:TEST_IOS_UNIT,
          isTesting:true,
          adSize:'BANNER',
          position:'BOTTOM_CENTER',
          margin:margin
        });
        bannerShown=true;
        requestedMargin=margin;
        console.info('La Ficha Build 7: test banner requested; margin=',margin);
      }catch(err){
        await removeBanner();
        console.warn('La Ficha Build 7: Google demo banner not shown',err);
      }finally{
        busy=false;
        if(rerun){rerun=false;schedule();}
      }
    }

    if(typeof ad.addListener==='function'){
      Promise.resolve(ad.addListener('bannerAdLoaded',function(){
        loaded=true;if(slot)slot.classList.add('lf-build7-ad-loaded');
      })).catch(function(){});
      Promise.resolve(ad.addListener('bannerAdFailedToLoad',function(error){
        loaded=false;if(slot)slot.classList.remove('lf-build7-ad-loaded');
        console.warn('La Ficha Build 7: Google test ad failed to load',error);
      })).catch(function(){});
    }

    privacyBtn.addEventListener('click',async function(){
      if(privacyBtn.hidden)return;
      try{
        await removeBanner();
        await ad.showPrivacyOptionsForm();
        applyConsent(await ad.requestConsentInfo());
      }catch(e){
        console.warn('La Ficha Build 7: privacy form unavailable',e);
      }finally{schedule();}
    });

    window.addEventListener('resize',schedule,{passive:true});
    window.addEventListener('scroll',schedule,{passive:true});
    document.addEventListener('visibilitychange',schedule);
    if(window.visualViewport){
      window.visualViewport.addEventListener('resize',schedule,{passive:true});
    }
    if(window.MutationObserver){
      // Debounced for the camera and animation state; no expensive DOM rewrites.
      new MutationObserver(schedule).observe(document.body,{
        subtree:true,attributes:true,attributeFilter:['class','style','aria-hidden']
      });
    }

    (async function(){
      try{
        let info=await ad.requestConsentInfo();
        applyConsent(info);
        if(info.isConsentFormAvailable && String(info.status).toUpperCase()==='REQUIRED'){
          info=await ad.showConsentForm();
          applyConsent(info);
        }
        if(!info.canRequestAds){
          console.info('La Ficha Build 7: ads not permitted by current UMP consent');
          return;
        }
        schedule();
      }catch(e){
        applyConsent(null);
        await removeBanner();
        console.warn('La Ficha Build 7: UMP consent unavailable; no ad requested',e);
      }
    })();
  }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',start,{once:true});
  }else{start();}
})();
</script>
'''
if len(re.findall(r'</body\s*>', s, flags=re.I)) != 1:
    sys.exit('ERROR: expected exactly one </body>. No files changed.')
s = re.sub(r'</body\s*>', lambda _: new_script + '\n</body>', s, count=1, flags=re.I)

# Final integrity checks before changing anything.
if (s.count('id="lfPrivacyOptionsBtn"') != 1
        or s.count(TAG) != 1
        or 'id="lfBuild6TestBannerBtn"' in s
        or 'lf-build6-native-test-banner-v1' in s
        or '<script id="lf-build6-ump-privacy-v1">' in s):
    sys.exit('ERROR: post-patch integrity check failed. Nothing changed.')
backup_dir = Path.home() / 'la-ficha-ios-backups'
backup_dir.mkdir(parents=True, exist_ok=True)
backup = backup_dir / ('index-pre-build7-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.html')
shutil.copy2(FILE, backup)
FILE.write_text(s, encoding='utf-8')
print('SUCCESS: Build 7 automatic, consent-gated Google TEST banner configured.')
print('Privacy Options preserved; temporary Show/Hide Test Ad removed.')
print('Spanish placeholder changes to Publicidad; app layout unchanged.')
print('HTML:', FILE)
print('Backup:', backup)
print('Next: npx cap sync ios; archive as 1.0 (7) for physical iPhone testing.')
print('NOTE: Native banner placement must be visually checked on iPhone.')
