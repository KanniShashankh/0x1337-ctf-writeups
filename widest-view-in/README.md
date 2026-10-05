---
title: "widest view in..."
ctf: "ContextCon Deccan CTF"
date: 2026-10-02
category: osint
difficulty: medium
points: 200
flag_format: "0x1337{xxx.xxx.xxx}"
author: "shashankh.kanni"
---

# widest view in...

## Summary

The challenge gives one Google Street View screenshot (`i would live here.png`) and the hint *"Skinniest of countries got the widest of views. ///Can you find the fork in the road?"*. The `///` prefix and the `xxx.xxx.xxx` flag format point to a what3words address. You geolocate the screenshot to a junction on Chile's Ruta 5, then take the what3words square at the fork in the road.

**Files:** [`files/widest_view_in.zip`](files/widest_view_in.zip) (challenge screenshot), [`files/matched-pano.jpg`](files/matched-pano.jpg) (matching May 2024 Street View panorama)

## Solution

### Step 1: Geolocate the screenshot

- **Country:** the "skinniest of countries" is Chile. The desert coastline, with the Pacific on the left and coastal mountains on the right, fits the Atacama coast.
- **Road:** the lane markings are a white edge line, a dashed white lane line, and a yellow line on the right. In Chile, yellow marks the median edge, so this is a divided highway. That rules out the two-lane Ruta 1 and points to the upgraded coastal Ruta 5 between Caldera and Chañaral.
- **Capture date:** the altocumulus ("mackerel") sky only appears in the May 2024 Street View capture of that stretch. Sweeping the May 2024 panoramas along Ruta 5 finds the curbed island, pole, reflector posts, two dark coastal rocks and the mountain with a sand ramp.
- **Match:** panorama `a6ZCw0jdYOMxaqYD6D8H5A`, **-26.694522, -70.729625**, May 2024. It sits where Ruta Las Lisas branches off Ruta 5 (Panamericana Norte), just south of Puerto Flamenco, Chañaral, Atacama. The mountain ahead is Cerro del Obispo.

Script used to sweep the historical panoramas and render candidate views (no API key needed):

```python
import json, subprocess

def search(lat, lon, r=40):
    """Return (pano_id, [year, month], lat, lon) for every capture near a point."""
    body = json.dumps([["apiv3",None,None,None,"US",None,None,None,None,None,[[False]]],
                       [[None,None,lat,lon],r],
                       [None,["en","US"],None,None,None,None,None,None,[2],None,
                        [[[2,True,2],[3,True,2],[10,True,2]]]],[[1,2,3,4,8,6]]])
    d = json.loads(subprocess.run(
        ["curl","-s","-A","Mozilla/5.0","-H","Content-Type: application/json+protobuf",
         "-X","POST","https://maps.googleapis.com/$rpc/google.internal.maps.mapsjs.v1."
         "MapsJsInternalService/SingleImageSearch","--data",body],
        capture_output=True, text=True).stdout)
    nb, hist = d[1][5][0][3][0], d[1][5][0][8] or []
    out = [(nb[0][0][1], d[1][6][7], nb[0][2][0][2], nb[0][2][0][3])]
    out += [(nb[i][0][1], ym, nb[i][2][0][2], nb[i][2][0][3]) for i, ym, *_ in hist]
    return out

def thumb(pano, yaw, fn, pitch=0, fov=110):
    subprocess.run(["curl","-s","-A","Mozilla/5.0","-o",fn,
        f"https://streetviewpixels-pa.googleapis.com/v1/thumbnail?panoid={pano}"
        f"&cb_client=maps_sv.tactile.gps&w=1024&h=576&yaw={yaw}&pitch={pitch}&thumbfov={fov}"])

# May-2024 capture at the Ruta 5 / Ruta Las Lisas junction
for pano, ym, la, lo in search(-26.69452, -70.72962, 6):
    if ym == [2024, 5]:
        print(pano, la, lo)
        thumb(pano, 12, f"{pano}.jpg", pitch=-15, fov=95)  # matches the challenge framing
```

Output:

```
uPT45iB5urj69yGkkCEpNg -26.694476088107663 -70.729741533527
a6ZCw0jdYOMxaqYD6D8H5A -26.694521641009448 -70.72962465096592   <- exact match
v4-QK7Gu3OhDA07AUezWAQ -26.694545291015846 -70.72948653349198
```

### Step 2: Find the fork on what3words

The camera's own square (`deceits.redeems.outdoorsy`) is wrong. So are the nearby OSM junction nodes. The flag is the fork itself.

1. Open what3words at the junction.
2. Switch from satellite view to the normal map view. There, Ruta Las Lisas visibly forks off the Ruta 5 line.
3. Select the square at that fork: **`///yoyo.magically.blessings`**. Its centre is -26.694521, -70.729499, in the same row as the camera and 4 squares (about 12 m) east.

```bash
curl -s -H "Referer: https://what3words.com/" \
  "https://mapapi.what3words.com/api/convert-to-3wa?coordinates=-26.694521,-70.729499&language=en&format=json"
# {"country":"CL", ..., "nearestPlace":"Diego de Almagro, Atacama", "words":"yoyo.magically.blessings", ...}
```

Lesson: the satellite imagery and the vector map are drawn differently. The challenge's "fork" is the road split as drawn on the map, not a feature in the photo or an OSM node.

## Flag

```
0x1337{yoyo.magically.blessings}
```
