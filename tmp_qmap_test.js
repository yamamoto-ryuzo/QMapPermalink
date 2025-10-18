
    const serverPort = 8089;
    
    const inputX = -21550.369052;
    const inputY = -10063.519083;
    let inputCRS = 'EPSG:3857';
    try{ var __urlParams = (typeof URLSearchParams !== 'undefined') ? new URLSearchParams(window.location.search) : null; if(__urlParams){ var __p = (__urlParams.get('crs') || __urlParams.get('epsg') || null); if(__p){ __p = String(__p).trim(); try{ if(/^[0-9]+$/.test(__p)){ inputCRS = 'EPSG:' + __p; } else { inputCRS = __p; } }catch(e){} } } }catch(e){}
    // expose server-side proj4 defs to the client as an object
    const serverProjDefs = {};
    var displayCRS_global = null; try{ if(typeof __urlParams !== 'undefined' && __urlParams){ var dp = __urlParams.get('display_crs') || __urlParams.get('displayCRS') || __urlParams.get('display_epsg') || __urlParams.get('epsg'); if(dp){ dp = String(dp).trim(); displayCRS_global = (/^[0-9]+$/.test(dp) ? ('EPSG:' + dp) : dp); } } }catch(e){}
    // fallback: if no explicit displayCRS provided, use inputCRS (URL 'crs' param) when it's not web mercator
    try{ if(!displayCRS_global && typeof inputCRS !== 'undefined' && inputCRS && inputCRS !== 'EPSG:3857'){ displayCRS_global = inputCRS; } }catch(e){}
    // debug: expose serverProjDefs and displayCRS to console for troubleshooting
    try{ if(typeof console !== 'undefined' && console.log){ console.log('[QMapPermalink] serverProjDefs=', serverProjDefs); console.log('[QMapPermalink] displayCRS_global=', displayCRS_global); } }catch(e){}
    // if server provided a proj4 for displayCRS, register it (load proj4.js if needed)
    try{ if(displayCRS_global && serverProjDefs && serverProjDefs[displayCRS_global]){
      (function(){
        function _reg(){
          try{
            if(typeof proj4 === 'undefined'){
              var s=document.createElement('script');
              s.src='https://cdnjs.cloudflare.com/ajax/libs/proj4js/2.8.0/proj4.js';
              s.onload=_reg;
              document.head.appendChild(s);
              return;
            }
          }catch(e){}
          try{ if(typeof console !== 'undefined' && console.log){ console.log('[QMapPermalink] registering displayCRS_global=' + displayCRS_global); console.log('[QMapPermalink] def=', serverProjDefs[displayCRS_global]); } }catch(e){}
          try{ proj4.defs(displayCRS_global, serverProjDefs[displayCRS_global]); }catch(e){}
          try{ if(typeof ol !== 'undefined' && ol.proj){ try{ if(ol.proj.proj4 && typeof ol.proj.proj4.register === 'function'){ ol.proj.proj4.register(proj4); } else if(typeof ol.proj.setProj4 === 'function'){ ol.proj.setProj4(proj4); } }catch(e){} } }catch(e){}
        }
        _reg();
      })();
    } }catch(e){}
    const mapScale = 502.6;
    const rotationRad = (0 || 0) * Math.PI / 180;
    const bookmarks = [];
    const themes = [];
    const serverGoogleMapsUrl = null;
    const serverGoogleEarthUrl = null;
    // prefer the configured server port (useful for testing). Use explicit IPv4 (127.0.0.1) to avoid IPv6 (::1) resolution issues.
        // Determine wms base URL: prefer page origin when usable, but when opened via file://
        // or when origin is not available, fall back to the configured serverPort on 127.0.0.1.
        const wmsBase = (function(){
            try{
                if(typeof window !== 'undefined' && window.location){
                    try{
                        var proto = window.location.protocol || '';
                        if(proto === 'file:'){
                            if(typeof serverPort !== 'undefined' && serverPort) return 'http://127.0.0.1:' + serverPort;
                        } else if(window.location.origin){
                            return window.location.origin;
                        }
                    }catch(e){}
                }
            }catch(e){}
            try{ if(typeof serverPort !== 'undefined' && serverPort) return 'http://127.0.0.1:' + serverPort; }catch(e){}
            return 'http://127.0.0.1:8089';
        })();
    const wmsSource = new ol.source.ImageWMS({ url: wmsBase + '/wms', params: { 'x': inputX, 'y': inputY, 'scale': mapScale, 'crs': inputCRS, 'ANGLE': rotationRad * 180 / Math.PI }, serverType: 'qgis', crossOrigin: 'anonymous' });
    const mapLayer = new ol.layer.Image({ source: wmsSource });
    const map = new ol.Map({ target: 'map', layers: [ mapLayer ], view: new ol.View({ center: [inputX, inputY], projection: 'EPSG:3857', zoom: 20, rotation: rotationRad }) });
    map.addControl(new ol.control.Rotate({ tipLabel: '北向きに回転', resetNorthLabel: '北向きにリセット' }));
    // 地図の回転に合わせてWMSパラメータも更新
    map.getView().on('change:rotation', function() {
        const rotation = map.getView().getRotation();
        const angleDeg = rotation * 180 / Math.PI;
        if(window.wmsSource && typeof window.wmsSource.updateParams === 'function'){
            window.wmsSource.updateParams({ 'ANGLE': angleDeg });
            window.wmsSource.refresh();
        }
    });
    window.map = map; window.wmsSource = wmsSource;
        // Add ScaleLine and realtime coords display (XY in map projection + Lat/Lon)
        try{ map.addControl(new ol.control.ScaleLine({ units: 'metric' })); }catch(e){}
        (function(){
            try{
                var coordsEl = null;
                try{ coordsEl = document.getElementById('qmp-coords'); }catch(e){ coordsEl = null; }
                map.on('pointermove', function(evt){
                    try{
                        if(evt.dragging) return;
                        var c = evt.coordinate;
                        if(!c) return;
                        var ix = (c[0]||0).toFixed(3);
                        var iy = (c[1]||0).toFixed(3);
                        var ll = ol.proj.toLonLat(c, 'EPSG:3857');
                        var lat = (ll && ll[1]) ? ll[1].toFixed(6) : '';
                        var lon = (ll && ll[0]) ? ll[0].toFixed(6) : '';
                        var scaleText = '';
                        try{
                            var view = map.getView();
                            var res = (view && typeof view.getResolution === 'function') ? view.getResolution() : null;
                            if(res !== null){
                                var mpu = (view && view.getProjection && view.getProjection().getMetersPerUnit) ? view.getProjection().getMetersPerUnit() : 1;
                                var dpi = 96;
                                var scaleDen = Math.round(res * mpu * dpi / 0.0254);
                                scaleText = '1:' + (scaleDen.toString());
                            } else if(typeof mapScale !== 'undefined' && mapScale){
                                scaleText = '1:' + mapScale;
                            }
                        }catch(e){}
                        if(coordsEl){
                            var crsLabel = (function(){ try{ var v = map.getView(); if(v && v.getProjection && typeof v.getProjection().getCode === 'function') return v.getProjection().getCode(); if(v && v.getProjection && v.getProjection().getCode) return v.getProjection().getCode(); }catch(e){} return 'EPSG:3857'; })();
                            var displayPart = '';
                            try{
                                if(typeof displayCRS_global !== 'undefined' && displayCRS_global && typeof ol !== 'undefined' && ol.proj){
                                    try{
                                        var viewp = map.getView();
                                        var viewProj = (viewp && viewp.getProjection && typeof viewp.getProjection().getCode === 'function') ? viewp.getProjection().getCode() : 'EPSG:3857';
                                        var t = null;
                                        try{ t = ol.proj.transform(c, viewProj, displayCRS_global); }catch(e){ try{ t = ol.proj.transform(c, 'EPSG:3857', displayCRS_global); }catch(e){ t = null; } }
                                        if(t && t.length>=2){ var dx = (t[0]||0).toFixed(3); var dy = (t[1]||0).toFixed(3); displayPart = ' / XY(' + displayCRS_global + '): ' + dx + ' ' + dy; }
                                    }catch(e){}
                                }
                            }catch(e){}
                            coordsEl.textContent = 'XY (' + crsLabel + '): ' + ix + ' ' + iy + displayPart + ' / LatLon(EPSG:4326): ' + lat + ' ' + lon + ' / Scale: ' + scaleText;
                        }
                    }catch(e){}
                });
            }catch(e){}
        })();
            (function(){
  try{
    var themeSel = document.getElementById('qmp-themes');
    try{ var urlParams = (typeof URLSearchParams !== 'undefined') ? new URLSearchParams(window.location.search) : null; }catch(e){ urlParams = null; }
    if(themeSel && Array.isArray(themes) && themes.length){
      themes.forEach(function(t){ try{ var opt = document.createElement('option'); opt.value = t; opt.text = t; themeSel.appendChild(opt);}catch(e){} });
      try{ var initialTheme = urlParams ? urlParams.get('theme') : null; if(initialTheme && Array.isArray(themes) && themes.indexOf(initialTheme) !== -1){ themeSel.value = initialTheme; if(window.wmsSource && typeof window.wmsSource.updateParams === 'function'){ window.wmsSource.updateParams({ 'theme': initialTheme }); } } }catch(e){}
      themeSel.addEventListener('change', function(){
        try{
          var sel = this.value;
          if(window.wmsSource && typeof window.wmsSource.updateParams === 'function'){
            if(sel && sel !== '__prompt'){
              window.wmsSource.updateParams({ 'theme': sel });
            } else {
              window.wmsSource.updateParams({});
            }
            window.wmsSource.refresh();
          }
          try{
            if(urlParams){
              if(sel && sel !== '__prompt') urlParams.set('theme', sel);
              else urlParams.delete('theme');
              var search = urlParams.toString();
              var newUrl = window.location.origin + window.location.pathname + (search ? ('?' + search) : '') + window.location.hash;
              if(window.history && typeof window.history.replaceState === 'function'){
                window.history.replaceState(null, '', newUrl);
              }
            }
          }catch(e){}
        }catch(e){}
      });
    }
    var sel = document.getElementById('qmp-bookmarks');
    if(sel && Array.isArray(bookmarks) && bookmarks.length){
      bookmarks.forEach(function(b,i){ try{ var opt = document.createElement('option'); opt.value = i; opt.text = b.name || ('Bookmark ' + (i+1)); sel.appendChild(opt);}catch(e){} });
      sel.addEventListener('change', function(){ try{ if(this.value === '__home' || this.value === '__prompt'){ map.getView().animate({ center: [inputX, inputY], duration: 600 }); } else { var idx = parseInt(this.value); var b = bookmarks[idx]; if(b){ var bx = parseFloat(b.x || b.orig_x || b.lon || b.lng || 0); var by = parseFloat(b.y || b.orig_y || b.lat || 0); if(isFinite(bx) && isFinite(by)){ map.getView().animate({ center: [bx, by], duration: 600 }); try{ if(window.wmsSource && typeof window.wmsSource.updateParams === 'function'){ var up = { 'x': bx, 'y': by, 'crs': 'EPSG:3857' }; try{ if(typeof mapScale !== 'undefined' && mapScale !== null) up.scale = mapScale; }catch(e){} try{ var currentTheme = (document.getElementById('qmp-themes') ? document.getElementById('qmp-themes').value : null); if(currentTheme && currentTheme !== '__prompt'){ up.theme = currentTheme; } }catch(e){} window.wmsSource.updateParams(up); window.wmsSource.refresh(); } }catch(e){} } } } }catch(e){} try{ this.value = '__prompt'; }catch(e){} });
    }
  }catch(e){}
})();
(function(){
  try{
    var btnMap = document.getElementById('qmp-open-googlemaps');
    if(btnMap){
      btnMap.addEventListener('click', function(){
        try{
          var view = map.getView(); var c = view.getCenter(); var x=c[0], y=c[1];
          var lon = (x / 20037508.34) * 180.0; var lat = (y / 20037508.34) * 180.0;
          lat = 180.0 / Math.PI * (2.0 * Math.atan(Math.exp(lat * Math.PI / 180.0)) - Math.PI / 2.0);
          var zoom = view.getZoom ? Math.round(view.getZoom()) : 12;
          // prefer server-computed URL if available
          if(typeof serverGoogleMapsUrl !== 'undefined' && serverGoogleMapsUrl){ var w = window.open(serverGoogleMapsUrl, '_blank'); if(!w){ alert('ポップアップブロック'); } return; }
          var url = 'https://www.google.com/maps/@' + encodeURIComponent(lat) + ',' + encodeURIComponent(lon) + ',' + encodeURIComponent(zoom) + 'z';
          var w = window.open(url, '_blank'); if(!w){ alert('ポップアップブロック'); }
        }catch(e){ console.error(e); }
      });
    }
  }catch(e){}
})();
(function(){
  try{
    var btnEarth = document.getElementById('qmp-open-googleearth');
    if(btnEarth){
      btnEarth.addEventListener('click', function(){
        try{
          var view = map.getView(); var c = view.getCenter(); var x=c[0], y=c[1];
          var lon = (x / 20037508.34) * 180.0; var lat = (y / 20037508.34) * 180.0;
          lat = 180.0 / Math.PI * (2.0 * Math.atan(Math.exp(lat * Math.PI / 180.0)) - Math.PI / 2.0);
          // prefer server-computed URL if available
          if(typeof serverGoogleEarthUrl !== 'undefined' && serverGoogleEarthUrl){ var w = window.open(serverGoogleEarthUrl, '_blank'); if(!w){ alert('ポップアップブロック'); } return; }
          // Use Google Earth Web search link (best-effort)
          var url = 'https://earth.google.com/web/search/' + encodeURIComponent(lat) + ',' + encodeURIComponent(lon);
          var w = window.open(url, '_blank'); if(!w){ alert('ポップアップブロック'); }
        }catch(e){ console.error(e); }
      });
    }
  }catch(e){}
})();

    try{ /* show CORS warning if page loaded via file: */ if(typeof window !== "undefined" && window.location && window.location.protocol === 'file:'){ try{ var el=document.getElementById("qmp-cors-warning"); if(el) el.style.display='block'; }catch(e){} } }catch(e){}
  