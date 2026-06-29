# QGIS Notes

QGIS is not required to use the published web map. If you install QGIS later,
you can drag `data/jobs.geojson` into QGIS directly.

Suggested QGIS filters:

- `"Can GW Access" = 'TRUE'`
- `"Before 2025 EOFY" = 'TRUE'`
- `"image_count" > 0`
- `"priority" = 'High'`

Suggested HTML popup/map tip:

```html
<h3>Job [% "job_id" %]</h3>
<img src="[% "image_1_url" %]" width="320">
<p>[% "recent_comment" %]</p>
<a href="[% "url" %]">Asset Vision</a>
<a href="[% "google_maps_url" %]">Google Maps</a>
<a href="[% "image_gallery_url" %]">All photos</a>
```
