#!/usr/bin/env python3
"""La Ficha Build 6, stage 1: Google UMP + bilingual Quick Menu privacy option.

Applies only to ~/la-ficha-ios/www/index.html.
Does NOT modify GitHub Pages, original root index.html, winner haptics,
scoreboard, domino detection, target modal, or advertise/load any banner yet.

Requires @capacitor-community/admob@8.2.1 already installed and synced.
Run from your Mac: python3 /tmp/lf_build6_ump.py
Then: npx cap sync ios
"""
from pathlib import Path
from datetime import datetime
import json
import re
import shutil
import sys

root = Path.home() / "la-ficha-ios"
file = root / "www" / "index.html"
pkg = root / "package.json"
tag = "lf-build6-ump-privacy-v1"
if not file.is_file() or not pkg.is_file():
    sys.exit("ERROR: expected local iOS project at ~/la-ficha-ios. Nothing changed.")
deps = json.loads(pkg.read_text(encoding="utf-8")).get("dependencies", {})
if "@capacitor-community/admob" not in deps:
    sys.exit("ERROR: AdMob plugin not found in package.json. Nothing changed.")

html = file.read_text(encoding="utf-8")
if tag in html:
    sys.exit("INFO: Build 6 UMP patch already applied. No changes needed.")
if "lf-ios-build4-5sec-winner-haptic" not in html:
    sys.exit("ERROR: approved five-second haptic baseline not found. Nothing changed.")
if "lf-ios-build3-camera-visual" not in html:
    sys.exit("ERROR: approved camera baseline not found. Nothing changed.")
if "id=\"lfPrivacyOptionsBtn\"" in html or "id='lfPrivacyOptionsBtn'" in html:
    sys.exit("ERROR: privacy button already exists. Nothing changed.")

# The Quick Menu is distinct from the Winning Score gear/target modal.
start_matches = list(re.finditer(r'<div\b[^>]*\bid=["\']quickMenu["\'][^>]*>', html, re.I))
if len(start_matches) != 1:
    sys.exit("ERROR: expected exactly one quickMenu element. Nothing changed.")
start = start_matches[0].end()
end_match = re.search(r'</div\s*>', html[start:], re.I)
if not end_match:
    sys.exit("ERROR: quickMenu closing tag not found. Nothing changed.")
end = start + end_match.start()
menu_body = html[start:end]
if '<div' in menu_body.lower() or 'id="newBtn"' not in menu_body:
    sys.exit("ERROR: unexpected Quick Menu structure. Nothing changed.")
if not re.search(r'</head\s*>', html, re.I) or not re.search(r'</body\s*>', html, re.I):
    sys.exit("ERROR: HTML head/body close tags missing. Nothing changed.")

menu_button = '<button id="lfPrivacyOptionsBtn" type="button" hidden aria-label="Privacy Options">Privacy Options</button>'
html2 = html[:end] + menu_button + html[end:]
style = """
<style id="lf-build6-ump-privacy-style">
/* The opt-in privacy item is only shown when Google's UMP requires it. */
#lfPrivacyOptionsBtn[hidden] { display:none!important; }
</style>
"""
html2 = re.sub(r'</head\s*>', style + '\n</head>', html2, count=1, flags=re.I)

script = r"""
<script id="lf-build6-ump-privacy-v1">
/* Native iOS only: UMP consent before any future ad requests.
   Does not initialize Mobile Ads SDK or display banners in this stage. */
(function () {
  'use strict';
  function boot() {
    const cap = window.Capacitor;
    if (!cap || typeof cap.isNativePlatform !== 'function' || !cap.isNativePlatform()) return;
    const admob = cap.Plugins && cap.Plugins.AdMob;
    const btn = document.getElementById('lfPrivacyOptionsBtn');
    if (!admob || !btn) {
      console.warn('La Ficha Build 6: native AdMob / privacy button unavailable');
      return;
    }
    const langEs = document.getElementById('langEs');
    function updateLanguage() {
      const spanish = !!(langEs && langEs.classList.contains('active'));
      const label = spanish ? 'Opciones de privacidad' : 'Privacy Options';
      btn.textContent = label;
      btn.setAttribute('aria-label', label);
    }
    updateLanguage();
    if (langEs && window.MutationObserver) {
      new MutationObserver(updateLanguage).observe(langEs, {
        attributes: true, attributeFilter: ['class']
      });
    }
    function updateVisibility(info) {
      const status = String(info && info.privacyOptionsRequirementStatus || '').toUpperCase();
      btn.hidden = status !== 'REQUIRED';
      window.lfBuild6CanRequestAds = !!(info && info.canRequestAds);
    }
    btn.addEventListener('click', async function () {
      if (btn.hidden) return;
      try {
        await admob.showPrivacyOptionsForm();
        // Consent can change, so always refresh status before future ad requests.
        const updated = await admob.requestConsentInfo();
        updateVisibility(updated);
      } catch (error) {
        console.warn('La Ficha: privacy options form unavailable', error);
      }
    });
    (async function () {
      try {
        let info = await admob.requestConsentInfo();
        updateVisibility(info);
        if (info.isConsentFormAvailable && info.status === 'REQUIRED') {
          info = await admob.showConsentForm();
          updateVisibility(info);
        }
        console.info('La Ficha Build 6: UMP ready; canRequestAds=', !!info.canRequestAds);
      } catch (error) {
        window.lfBuild6CanRequestAds = false;
        console.warn('La Ficha Build 6: UMP consent unavailable; ads disabled', error);
      }
    })();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
</script>
"""
html2 = re.sub(r'</body\s*>', script + '\n</body>', html2, count=1, flags=re.I)
if html2.count(tag) != 1 or html2.count('id="lfPrivacyOptionsBtn"') != 1:
    sys.exit("ERROR: patch verification failed before write. Nothing changed.")
backup_dir = Path.home() / "la-ficha-ios-backups"
backup_dir.mkdir(parents=True, exist_ok=True)
backup = backup_dir / ("index-pre-build6-ump-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".html")
shutil.copy2(file, backup)
file.write_text(html2, encoding="utf-8")
print("SUCCESS: Build 6 UMP consent and bilingual Quick Menu privacy option applied.")
print("HTML:", file)
print("Backup:", backup)
print("Winner haptics, camera and scoring unchanged.")
print("Ads are NOT being displayed yet. Next: npx cap sync ios")
