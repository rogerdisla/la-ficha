from pathlib import Path
import re

path = Path("index.html")
html = path.read_text()

old_gate = "if(lfCaptureNeedsTap||captureInProgress||autoCaptureTimer||!framingReady)return;"
new_gate = "if(captureInProgress||autoCaptureTimer||!framingReady)return;"
if old_gate not in html:
    raise SystemExit("Auto-capture gate not found")
html = html.replace(old_gate, new_gate, 1)

pattern_uncertain = re.compile(
    r"""    lfCaptureNeedsTap=true;
    if\(consensus\)lfRenderDiagnostics\(consensus\);
    console\.info\('\[La Ficha consensus retry\]',consensus\);
    captureInProgress=false;
    if\(captureBtn\)captureBtn\.disabled=false;
    if\(status\)status\.textContent=framingText\('unstable'\);
    startFramingAssistant\(\);
    if\(status\)status\.textContent='Uncertain count — tap Capture to retry';
    return;"""
)

replacement_uncertain = """    lfCaptureNeedsTap=false;
    console.info('[La Ficha consensus retry]',consensus);
    captureInProgress=false;
    if(captureBtn)captureBtn.disabled=false;
    if(status)status.textContent=framingText('unstable');

    /* Automatically re-arm after an uncertain burst instead of requiring a tap. */
    await new Promise(r=>setTimeout(r,260));
    if(liveCameraModal&&liveCameraModal.classList.contains('show')){
      startFramingAssistant();
    }
    return;"""

html, n = pattern_uncertain.subn(replacement_uncertain, html, count=1)
if n != 1:
    raise SystemExit("Uncertain consensus retry block not found")

pattern_catch = re.compile(
    r"""  \}catch\(err\)\{
    lfCaptureNeedsTap=true;
    console\.error\('Consensus capture failed',err\);
    captureInProgress=false;
    if\(captureBtn\)captureBtn\.disabled=false;
    if\(liveCameraModal&&liveCameraModal\.classList\.contains\('show'\)\)\{
      if\(status\)status\.textContent=framingText\('unstable'\);
      startFramingAssistant\(\);
      if\(status\)status\.textContent='Fresh frame not confirmed — tap Capture';
    \}else\{
      showGuidedCameraRequirement\(\);
    \}
  \}"""
)

replacement_catch = """  }catch(err){
    lfCaptureNeedsTap=false;
    console.error('Consensus capture failed',err);
    captureInProgress=false;
    if(captureBtn)captureBtn.disabled=false;
    if(liveCameraModal&&liveCameraModal.classList.contains('show')){
      if(status)status.textContent=framingText('unstable');
      await new Promise(r=>setTimeout(r,260));
      startFramingAssistant();
    }else{
      showGuidedCameraRequirement();
    }
  }"""

html, n = pattern_catch.subn(replacement_catch, html, count=1)
if n != 1:
    raise SystemExit("Capture error retry block not found")

for forbidden in [
    "Uncertain count — tap Capture to retry",
    "Fresh frame not confirmed — tap Capture",
    old_gate,
]:
    if forbidden in html:
        raise SystemExit("Old manual retry behavior remains: " + forbidden)

path.write_text(html)
