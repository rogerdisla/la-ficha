#!/usr/bin/env python3
"""La Ficha: prepare TestFlight Build 3 from the local iOS web copy.
Never changes repository root index.html or GitHub Pages production.
"""
from pathlib import Path
import shutil
import sys
from datetime import datetime

root = Path.home() / "la-ficha-ios"
file = root / "www" / "index.html"
if not file.is_file():
    sys.exit("ERROR: missing ~/la-ficha-ios/www/index.html")
html = file.read_text(encoding="utf-8")
marker = "lf-ios-build3-camera-and-haptics"
if marker in html:
    sys.exit("Build 3 patch already installed; nothing changed.")

old = "function showWinner(name,scoreVal){$('winnerName').textContent=name;$('winnerScore').textContent=scoreVal+' '+tr().pointsWord;$('winKicker').textContent=tr().winner;$('winner').classList.add('show');startFireworks();try{if(navigator.vibrate)navigator.vibrate([180,80,180,90,350,80,180])}catch(e){}}"
new = """// lf-ios-build3-camera-and-haptics: native iOS haptic with web fallback.
function lfWinnerHaptic(){
  const cap=window.Capacitor;
  const h=cap&&cap.Plugins&&cap.Plugins.Haptics;
  if(h && typeof cap.isNativePlatform==='function' && cap.isNativePlatform()){
    try {
      Promise.resolve(h.notification({type:'SUCCESS'})).catch(e=>console.warn('Haptic notification failed',e));
      setTimeout(()=>{try{Promise.resolve(h.impact({style:'HEAVY'})).catch(()=>{});}catch(_e){}},250);
      return;
    } catch(e) { console.warn('Native haptic failed',e); }
  }
  try { if(navigator.vibrate) navigator.vibrate([180,80,180,90,350,80,180]); } catch(_e){}
}
function showWinner(name,scoreVal){$('winnerName').textContent=name;$('winnerScore').textContent=scoreVal+' '+tr().pointsWord;$('winKicker').textContent=tr().winner;$('winner').classList.add('show');startFireworks();lfWinnerHaptic();}"""
visual = """
<!-- lf-ios-build3-camera-and-haptics: camera appearance only -->
<style id="lf-ios-build3-camera-visual">
/* Preserve all JS framing/distance/focus checks; hide their visual HUD. */
.liveCameraModal .framingHud { display: none !important; }
/* Keep FRAME ALL DOMINOES centered and fully inside the preview. */
.liveCameraModal .liveCameraGuide::before {
  top: 0 !important;
  transform: translate(-50%, -50%) !important;
  box-sizing: border-box !important;
  min-width: 200px !important;
  padding: 6px 14px !important;
  font-size: 10px !important;
  line-height: 1.25 !important;
  z-index: 6 !important;
}
</style>
"""
if html.count(old) != 1 or html.count("</head>") != 1:
    sys.exit("ERROR: expected original winner code/head not found, no changes made.")
if 'class="framingHud"' not in html or 'id="frameGuide"' not in html:
    sys.exit("ERROR: expected camera markup not found, no changes made.")
backup_dir = Path.home() / "la-ficha-ios-backups"
backup_dir.mkdir(parents=True, exist_ok=True)
backup = backup_dir / ("index-pre-build3-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".html")
shutil.copy2(file, backup)
updated = html.replace("</head>", visual + "</head>", 1).replace(old, new, 1)
file.write_text(updated, encoding="utf-8")
print("SUCCESS: Build 3 camera visual and winner haptics patch applied.")
print("Changed:", file)
print("Backup:", backup)
print("No GitHub Pages / main changes. Run: npx cap sync ios")
