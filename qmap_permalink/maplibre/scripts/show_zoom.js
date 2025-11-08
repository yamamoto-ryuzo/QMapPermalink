(function(){
  // Create a zoom display element and keep it updated from the MapLibre map instance.
  function setup() {
    var map = window.map || window.qmap_map;
    if (!map) {
      // Map not available yet — retry shortly
      setTimeout(setup, 150);
      return;
    }

    // Avoid creating duplicate element
    if (document.getElementById('qmap-zoom-display')) return;

    var el = document.createElement('div');
    el.id = 'qmap-zoom-display';
    el.style.position = 'absolute';
    el.style.top = '50px';
    el.style.right = '10px';
    el.style.zIndex = 1001;
    el.style.padding = '6px 8px';
    el.style.background = '#fff';
    el.style.border = '1px solid #666';
    el.style.borderRadius = '4px';
    el.style.fontFamily = 'sans-serif';
    el.style.fontSize = '13px';
    el.style.pointerEvents = 'none';
    el.textContent = 'Zoom: --';

    document.body.appendChild(el);

    function update() {
      try {
        var z = map.getZoom();
        if (typeof z === 'number') el.textContent = 'Zoom: ' + z.toFixed(2);
      } catch (e) {
        // ignore
      }
    }

    // Initial update and event bindings
    update();
    try {
      if (map.on) {
        map.on('move', update);
        map.on('zoom', update);
      } else {
        // fallback: poll occasionally
        setInterval(update, 500);
      }
    } catch (e) {
      // ignore
    }
  }

  // Kick off setup
  try { setup(); } catch (e) { setTimeout(setup, 200); }
})();
