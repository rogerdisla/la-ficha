#!/usr/bin/env python3
"""La Ficha TestFlight Build 4: change ONLY the winner haptic to continuous 5 seconds.

Prerequisites (in ~/la-ficha-ios):
  npm install --save-exact @capawesome/capacitor-haptics@0.2.0
  npm uninstall @capacitor/haptics

Runs against the installed Build 3 iOS development copy (www/index.html).
Creates a dated backup. Does not touch root index.html, GitHub Pages, or camera UI.
"""
from pathlib import Path
from datetime import datetime
import shutil, sys

root = Path.home() / "la-ficha-ios"
html_file = root / "www" / "index.html"
pkg_file = root / "package.json"
if not html_file.is_file() or not pkg_file.is_file():
    sys.exit("ERROR: expected ~/la-ficha-ios/www/index.html and package.json")

import json
pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
if "@capawesome/capacitor-haptics" not in deps:
    sys.exit("ERROR: first install @capawesome/capacitor-haptics@0.2.0")
if "@capacitor/haptics" in deps:
    sys.exit("ERROR: uninstall @capacitor/haptics to avoid native plugin name collision")

html = html_file.read_text(encoding="utf-8")
marker = "lf-ios-build4-5sec-winner-haptic"
if marker in html:
    sys.exit("Build 4 winner haptic patch is already present; no changes made.")
old = """function lfWinnerHaptic(){
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
}"""
new = """// lf-ios-build4-5sec-winner-haptic: single continuous Core Haptics event.
function lfWinnerHaptic(){
  const cap=window.Capacitor;
  const h=cap&&cap.Plugins&&cap.Plugins.Haptics;
  if(h && typeof cap.isNativePlatform==='function' && cap.isNativePlatform()){
    try {
      if(typeof h.playPattern==='function'){
        // One continuous event, not five seconds of repeated taps.
        Promise.resolve(h.playPattern({
          events:[{time:0, intensity:1, sharpness:0.45, duration:5000}]
        })).catch(e=>{
          console.warn('5-second Core Haptics playback failed',e);
          if(typeof h.notification==='function'){
            Promise.resolve(h.notification({type:'SUCCESS'})).catch(()=>{});
          }
        });
        return;
      }
      console.warn('Continuous haptics plugin unavailable; using prior tap');
      if(typeof h.notification==='function'){
        Promise.resolve(h.notification({type:'SUCCESS'})).catch(()=>{});
        return;
      }
    }catch(e){console.warn('Native winner haptics failed',e);}
  }
  try{if(navigator.vibrate)navigator.vibrate(5000);}catch(_e){}
}"""
if html.count(old) != 1:
    sys.exit("ERROR: expected the EXACT Build 3 winner haptic function once. No file changes.")
if html.count("function showWinner(") != 1 or "lf-ios-build3-camera-visual" not in html:
    sys.exit("ERROR: Build 3 winner/camera baseline not detected. No changes.")

backup_dir = Path.home() / "la-ficha-ios-backups"
backup_dir.mkdir(parents=True, exist_ok=True)
backup = backup_dir / ("index-pre-build4-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".html")
shutil.copy2(html_file, backup)
html_file.write_text(html.replace(old,new,1), encoding="utf-8")
print("SUCCESS: five-second continuous winner haptic applied to Build 4 iOS copy.")
print("HTML:", html_file)
print("Backup:",backup)
print("Camera overlay and all winner visuals preserved.")
print("No GitHub Pages/main changes. Next: npx cap sync ios")
