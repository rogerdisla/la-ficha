from pathlib import Path
import base64, re

path = Path("index.html")
html = path.read_text()

if "function lfTileFaceGate(" in html:
    print("Tile-boundary detector already present; no detector insertion needed.")
else:
    old_geom = "return {matched,score,avgSurface,count:pattern.length};"
    new_geom = """const cc=lfTransformPoint([0,0],a,b,p,q);
  return {
    matched,score,avgSurface,count:pattern.length,
    cx:cc.x,cy:cc.y,A,B,scale:Math.hypot(A,B)
  };"""

    if html.count(old_geom) != 1:
        raise SystemExit(f"Expected one lfTryPattern return anchor, found {html.count(old_geom)}")

    helper_b64 = "LyogdjguNCDigJQgVHJ1ZSB0aWxlLWZhY2UgdmFsaWRhdGlvbi4KICAgQSBkYXJrIGNpcmNsZSBpcyBub3QgZW5vdWdoLiBQaXBzIG11c3QgZmlyc3QgZm9ybSBhIGxlZ2FsIGRvbWluby1mYWNlCiAgIGh5cG90aGVzaXMsIGFuZCB0aGF0IGh5cG90aGVzaXMgbXVzdCBzaXQgb24gYSBib3VuZGVkIHRpbGUtbGlrZSBzdXJmYWNlLiAqLwoKZnVuY3Rpb24gbGZGYWNlUmluZ0NvbG9yKGMsZGF0YSx3LGgpewogIGNvbnN0IHI9TWF0aC5tYXgoMixjLnIpLHJpPXIqMS40NSxybz1yKjMuMTsKICBjb25zdCBzdGVwPU1hdGgubWF4KDEsTWF0aC5mbG9vcihyLzMpKTsKICBsZXQgc3I9MCxzZz0wLHNiPTAsbj0wOwoKICBmb3IobGV0IHk9TWF0aC5tYXgoMCxNYXRoLmZsb29yKGMueS1ybykpO3k8PU1hdGgubWluKGgtMSxNYXRoLmNlaWwoYy55K3JvKSk7eSs9c3RlcCl7CiAgICBmb3IobGV0IHg9TWF0aC5tYXgoMCxNYXRoLmZsb29yKGMueC1ybykpO3g8PU1hdGgubWluKHctMSxNYXRoLmNlaWwoYy54K3JvKSk7eCs9c3RlcCl7CiAgICAgIGNvbnN0IGQ9TWF0aC5oeXBvdCh4LWMueCx5LWMueSk7CiAgICAgIGlmKGQ8cml8fGQ+cm8pY29udGludWU7CgogICAgICBjb25zdCBpPSh5KncreCkqNCxSPWRhdGFbaV0sRz1kYXRhW2krMV0sQj1kYXRhW2krMl07CiAgICAgIGNvbnN0IG14PU1hdGgubWF4KFIsRyxCKSxtbj1NYXRoLm1pbihSLEcsQik7CiAgICAgIGNvbnN0IGx1bT0oUitHK0IpLzM7CiAgICAgIGNvbnN0IHNhdD0obXgtbW4pL01hdGgubWF4KDEsbXgpOwoKICAgICAgaWYobHVtPDg0fHxzYXQ+LjYyKWNvbnRpbnVlOwogICAgICBzcis9UjtzZys9RztzYis9QjtuKys7CiAgICB9CiAgfQoKICBpZighbilyZXR1cm4gbnVsbDsKICBjb25zdCBSPXNyL24sRz1zZy9uLEI9c2IvbixzdW09UitHK0J8fDE7CiAgcmV0dXJuIHtyOlIsZzpHLGI6QixsdW06KFIrRytCKS8zLG5yOlIvc3VtLG5nOkcvc3VtLG5iOkIvc3VtfTsKfQoKZnVuY3Rpb24gbGZGYWNlQm91bmRhcnlFdmlkZW5jZShmYWNlLGNhbmRzLGRhdGEsdyxoKXsKICBjb25zdCBjb2xvcnM9W107CiAgZm9yKGNvbnN0IGl4IG9mIGZhY2UubWF0Y2hlZCl7CiAgICBjb25zdCBjPWxmRmFjZVJpbmdDb2xvcihjYW5kc1tpeF0sZGF0YSx3LGgpOwogICAgaWYoYyljb2xvcnMucHVzaChjKTsKICB9CiAgaWYoIWNvbG9ycy5sZW5ndGgpcmV0dXJuIG51bGw7CgogIGxldCBSPTAsRz0wLEI9MDsKICBmb3IoY29uc3QgYyBvZiBjb2xvcnMpe1IrPWMucjtHKz1jLmc7Qis9Yy5ifQogIFIvPWNvbG9ycy5sZW5ndGg7Ry89Y29sb3JzLmxlbmd0aDtCLz1jb2xvcnMubGVuZ3RoOwoKICBjb25zdCBzdW09UitHK0J8fDE7CiAgY29uc3QgcmVmPXtyOlIsZzpHLGI6QixsdW06KFIrRytCKS8zLG5yOlIvc3VtLG5nOkcvc3VtLG5iOkIvc3VtfTsKCiAgY29uc3QgcG9pbnQ9KHUsdik9Pih7CiAgICB4OmZhY2UuY3grZmFjZS5BKnUtZmFjZS5CKnYsCiAgICB5OmZhY2UuY3krZmFjZS5CKnUrZmFjZS5BKnYKICB9KTsKCiAgZnVuY3Rpb24gc2FtcGxlKHUsdil7CiAgICBjb25zdCBwPXBvaW50KHUsdikseD1NYXRoLnJvdW5kKHAueCkseT1NYXRoLnJvdW5kKHAueSk7CiAgICBpZih4PDB8fHg+PXd8fHk8MHx8eT49aClyZXR1cm4ge21hdGNoOmZhbHNlLGx1bTowfTsKCiAgICBjb25zdCBpPSh5KncreCkqNCxyPWRhdGFbaV0sZz1kYXRhW2krMV0sYj1kYXRhW2krMl07CiAgICBjb25zdCBteD1NYXRoLm1heChyLGcsYiksbW49TWF0aC5taW4ocixnLGIpOwogICAgY29uc3QgbHVtPShyK2crYikvMzsKICAgIGNvbnN0IHNhdD0obXgtbW4pL01hdGgubWF4KDEsbXgpOwogICAgY29uc3Qgcz1yK2crYnx8MTsKICAgIGNvbnN0IGNocm9tYT1NYXRoLmh5cG90KHIvcy1yZWYubnIsZy9zLXJlZi5uZyxiL3MtcmVmLm5iKTsKCiAgICByZXR1cm4gewogICAgICBtYXRjaDpsdW0+ODAgJiYgc2F0PC42NSAmJiBjaHJvbWE8LjEzICYmIE1hdGguYWJzKGx1bS1yZWYubHVtKTwxMDAsCiAgICAgIGx1bQogICAgfTsKICB9CgogIGxldCBpbnNpZGVIaXRzPTAsaW5zaWRlTj0wOwogIGZvcihjb25zdCB1IG9mIFstMS4zNSwtLjc1LDAsLjc1LDEuMzVdKXsKICAgIGZvcihjb25zdCB2IG9mIFstMS4zNSwtLjc1LDAsLjc1LDEuMzVdKXsKICAgICAgY29uc3Qgcz1zYW1wbGUodSx2KTsKICAgICAgaWYocy5tYXRjaClpbnNpZGVIaXRzKys7CiAgICAgIGluc2lkZU4rKzsKICAgIH0KICB9CgogIGxldCBvdXRzaWRlSGl0cz0wLG91dHNpZGU9MCxkaWZmU3VtPTAsZGlmZk49MCxnb29kRWRnZXM9MDsKICBmb3IobGV0IHNpZGU9MDtzaWRlPDQ7c2lkZSsrKXsKICAgIGxldCBzaWRlT3V0c2lkZT0wLHNpZGVOPTAseXNpZGVEaWZmPTA7CiAgICBmb3IoY29uc3QgdCBvZiBbLTEuMTUsLS41NSwwLC41NSwxLjE1XSl7CiAgICAgIGxldCB1aSx2aSx1byx2bzsKICAgICAgaWYoc2lkZT09PTApe3VpPTEuNTt2aT10O3VvPTEuOTU7dm89dH0KICAgICAgZWxzZSBpZihzaWRlPT09MSl7dWk9LTEuNTt2aT10O3VvPS0xLjk1O3ZvPXR9CiAgICAgIGVsc2UgaWYoc2lkZT09PTIpe3VpPXQ7dmk9MS41O3VvPXQ7dm89MS45NX0KICAgICAgZWxzZXt1aT10O3ZpPS0xLjU7dW89dDt2bz0tMS45NX0KICAgICAgY29uc3QgYT1zYW1wbGUodWksdmkpLGI9c2FtcGxlKHVvLHZvKTsKICAgICAgaWYoYi5tYXRjaClzaWRlT3V0c2lkZSsrOwogICAgICBzaWRlTisrOwogICAgICB5c2lkZURpZmYrPU1hdGguYWJzKGEubHVtLWIubHVtKTsKICAgIH0KICAgIGNvbnN0IG91dHNpZGVGcmFjdGlvbj1zaWRlT3V0c2lkZS9NYXRoLm1heCgxLHNpZGVOKTsKICAgIGNvbnN0IGVkZ2VEaWZmPXlzaWRlRGlmZi9NYXRoLm1heCgxLHNpZGVOKTsKICAgIG91dHNpZGVIaXRzKz1zaWRlT3V0c2lkZTsKICAgIG91dHNpZGU9c2lkZU47CiAgICBkaWZmU3VtKz15c2lkZURpZmY7CiAgICBkaWZmTis9c2lkZU47CiAgICBpZihvdXRzaWRlRnJhY3Rpb248PS40NSAmJiBlZGdlRGlmZj49MTIpZ29vZEVkZ2VzKys7CiAgfQoKICBjb25zdCBpbnNpZGU9aW5zaWRlSGl0cy9NYXRoLm1heCgxLGluc2lkZU4pOwogIGNvbnN0IG91dHNpZGU9b3V0c2lkZUhpdHMvTWF0aC5tYXgoMSxvdXRzaWRlTik7CiAgY29uc3QgZWRnZURpZmY9ZGlmZlN1bS9NYXRoLm1heCgxLGRpZmZOKTsKICBjb25zdCBib3VuZGFyeT1pbnNpZGUtb3V0c2lkZSsuMTUqTWF0aC5taW4oMSxlZGdlRGlmZi80NSkrLjA2Kihnb29kRWRnZXMvNCk7CiAgcmV0dXJuIHtpbnNpZGUsb3V0c2lkZSxlZGdlRGlmZixnb29kRWRnZXMsYm91bmRhcnl9Owp9Cg==";
    helper = base64.b64decode(helper_b64).decode()

    # NOTE: helper_b64 above is only a sentinel. Refuse if it did not decode the full helper.
    if "function lfTileFaceGate(" not in helper:
        raise SystemExit("Embedded tile-boundary helper is incomplete; refusing to alter index.html")

    html = html.replace(old_geom, new_geom, 1)

    marker = "function analyzeCanvas(canvas){"
    if html.count(marker) != 1:
        raise SystemExit(f"Expected one analyzeCanvas marker, found {html.count(marker)}")
    html = html.replace(marker, helper + marker, 1)

    prefix = "  const validated=lfDominoValidationLayer(chosen,gray,w,h,polarity);"
    p = html.find(prefix)
    if p < 0:
        raise SystemExit("Detector final-stage prefix not found")

    a = html.find("  const avgContrast=", p)
    if a < 0 or a - p > 2500:
        raise SystemExit("Detector final-stage boundary not found safely")

    segment = html[p:a]
    if "const final=polarity==='dark'?" not in segment:
        raise SystemExit("Unexpected detector final-stage structure; refusing to replace it")

    new_final = """  const validated=lfDominoValidationLayer(chosen,gray,w,h,polarity);

  const preFinal=polarity==='dark'
    ? lfFilterGroups(
        chosen.map(c=>({...c,validation:lfColorSurface(c,data,w,h)}))
              .filter(c=>c.validation>=.50),
        data,w,h
      )
    : validated.candidates;

  const tileGate=polarity==='dark'
    ? lfTileFaceGate(preFinal,data,gray,w,h)
    : {
        candidates:preFinal,rejected:0,anchored:0,
        faces:0,boundaryFaces:0,surfaceLocked:false
      };

  const final=tileGate.candidates;

"""
    html = html[:p] + new_final + html[a:]

# Production safeguards from the user's approved camera/UI state.
for forbidden in [
    "Enlarge dots",
    "Save diagnostic report",
    "Save captured photo",
    "Scan diagnostics",
    "Uncertain count — tap Capture to retry",
    "Fresh frame not confirmed — tap Capture",
    "if(lfCaptureNeedsTap||captureInProgress||autoCaptureTimer||!framingReady)return;"
]:
    if forbidden in html:
        raise SystemExit("Production safeguard failed; found: " + forbidden)

if "function lfTileFaceGate(" not in html:
    raise SystemExit("Tile-boundary detector missing after patch")

path.write_text(html)
print("Tile-boundary detector patch prepared successfully.")
