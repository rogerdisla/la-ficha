#!/usr/bin/env python3
"""Build 8 — fix only La Ficha native Google TEST banner's vertical offset.

The @capacitor-community/admob@8.2.1 iOS plugin anchors BOTTOM_CENTER
to the UIKit safeAreaLayoutGuide.bottom, not the physical screen bottom.
Build 7 calculated its native margin from WKWebView window.innerHeight and
did not subtract that iOS bottom safe-area inset. On a notched iPhone this
puts the ad about 34 points too high, overlapping Add to Team buttons.

Applies to local ~/la-ficha-ios/www/index.html, backs up before writing.
No production ads; camera/scoring/winner vibration/consent otherwise unchanged.
"""
from pathlib import Path
from datetime import datetime
import shutil
import sys

file = Path.home() / "la-ficha-ios" / "www" / "index.html"
if not file.is_file():
    sys.exit("ERROR: iOS HTML not found; no changes.")
src = file.read_text(encoding="utf-8")
marker = "lf-ios-build8-admob-safe-area-adjust"
if marker in src:
    sys.exit("INFO: Build 8 alignment correction already applied.")
expected = [
    'lf-ios-build7-auto-test-banner-v1',
    'lf-ios-build4-5sec-winner-haptic',
    'id="lfPrivacyOptionsBtn"',
]
for item in expected:
    if item not in src:
        sys.exit("ERROR: unexpected baseline; missing " + item + "; no changes.")

old = """      // Center a 50-point banner vertically in the 47-60-point reserved slot.
      const desiredBottom=r.top+(r.height/2)+25;
      const margin=Math.round(h-desiredBottom);
      if(margin<0 || margin>Math.min(280,h*0.5))return null;
      return margin;"""
new = """      // lf-ios-build8-admob-safe-area-adjust:
      // Native plugin 8.2.1 anchors the banner to UIKit safeAreaLayoutGuide.bottom,
      // whereas our screen-space target uses WKWebView's window.innerHeight.
      // Subtract the iPhone's bottom safe-area inset or the banner sits too high.
      const desiredBottom=r.top+(r.height/2)+25;
      const probe=document.createElement('div');
      probe.style.cssText='position:fixed;left:0;bottom:0;visibility:hidden;pointer-events:none;padding-bottom:env(safe-area-inset-bottom, 0px)';
      document.body.appendChild(probe);
      const cssSafeInset=parseFloat(window.getComputedStyle(probe).paddingBottom)||0;
      probe.remove();
      // Fallback for modern Home-indicator iPhones when WKWebView reports
      // zero for CSS env(safe-area-inset-bottom). Does not apply to SE or iPad.
      const shortEdge=Math.min(screen.width,screen.height);
      const longEdge=Math.max(screen.width,screen.height);
      const homeIndicatorPhone=shortEdge<=480 && longEdge/shortEdge>1.95;
      const safeInset=cssSafeInset>0?cssSafeInset:(homeIndicatorPhone?34:0);
      const margin=Math.round(h-desiredBottom-safeInset);
      if(margin<0 || margin>Math.min(280,h*0.5))return null;
      return margin;"""

if src.count(old) != 1:
    sys.exit("ERROR: expected exact Build 7 measuredMargin code once. No changes.")
updated = src.replace(old,new,1)
if updated.count(marker)!=1:
    sys.exit("ERROR: patch verification failed. No changes.")
backup_dir=Path.home()/"la-ficha-ios-backups"
backup_dir.mkdir(parents=True,exist_ok=True)
backup=backup_dir/("index-pre-build8-"+datetime.now().strftime("%Y%m%d-%H%M%S")+".html")
shutil.copy2(file,backup)
file.write_text(updated,encoding="utf-8")
print("SUCCESS: Build 8 native AdMob banner safe-area alignment corrected.")
print("Banner is expected to move DOWN ~34 points on Home-indicator iPhones.")
print("Google TEST ad ID retained; auto-loading and consent preserved.")
print("Gameplay, app styling, translation and five-second haptics not changed.")
print("Backup:",backup)
print("Next: npx cap sync ios; archive and TestFlight test as 1.0 (8).")
