<!DOCTYPE html>
<html>
<head>
<meta name="viewport"></meta>
<title>df_info_locations - Google Fusion Tables</title>
<style type="text/css">
html, body, #googft-mapCanvas {
  height: 300px;
  margin: 0;
  padding: 0;
  width: 500px;
}
#googft-legend{background-color:#fff;border:1px solid #000;font-family:Arial, sans-serif;font-size:12px;margin:5px;padding:10px 10px 8px;}#googft-legend p{font-weight:bold;margin-top:0;}#googft-legend div{margin-bottom:5px;}.googft-legend-swatch{border:1px solid;float:left;height:12px;margin-right:8px;width:20px;}.googft-legend-range{margin-left:0;}.googft-dot-icon{margin-right:8px;}.googft-paddle-icon{height:24px;left:-8px;margin-right:-8px;position:relative;vertical-align:middle;width:24px;}.googft-legend-source{margin-bottom:0;margin-top:8px;}.googft-legend-source a{color:#666;font-size:11px;}
</style>

<script type="text/javascript" src="//maps.google.com/maps/api/js?sensor=false"></script>

<script type="text/javascript">
  function initialize() {
    google.maps.visualRefresh = true;
    var isMobile = (navigator.userAgent.toLowerCase().indexOf('android') > -1) ||
      (navigator.userAgent.match(/(iPod|iPhone|iPad|BlackBerry|Windows Phone|iemobile)/));
    if (isMobile) {
      var viewport = document.querySelector("meta[name=viewport]");
      viewport.setAttribute('content', 'initial-scale=1.0, user-scalable=no');
    }
    var mapDiv = document.getElementById('googft-mapCanvas');
    mapDiv.style.width = isMobile ? '100%' : '500px';
    mapDiv.style.height = isMobile ? '100%' : '300px';
    var map = new google.maps.Map(mapDiv, {
      center: new google.maps.LatLng(48.337990558362236, -2.8062404914776296),
      zoom: 8,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    });
    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(document.getElementById('googft-legend-open'));
    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(document.getElementById('googft-legend'));

    layer = new google.maps.FusionTablesLayer({
      map: map,
      heatmap: { enabled: false },
      query: {
        select: "col21",
        from: "1XfoTvO3_tb1JHR8HVzrIEaDhzYOq1HVfGrINH4Al",
        where: "col6 \x3d \x27\x27 and col5 \x3d \x27Bretagne\x27 and col12 in (\x27IND\x27, \x27OIL\x27, \x27SUP\x27)"
      },
      options: {
        styleId: 2,
        templateId: 2
      }
    });

    if (isMobile) {
      var legend = document.getElementById('googft-legend');
      var legendOpenButton = document.getElementById('googft-legend-open');
      var legendCloseButton = document.getElementById('googft-legend-close');
      legend.style.display = 'none';
      legendOpenButton.style.display = 'block';
      legendCloseButton.style.display = 'block';
      legendOpenButton.onclick = function() {
        legend.style.display = 'block';
        legendOpenButton.style.display = 'none';
      }
      legendCloseButton.onclick = function() {
        legend.style.display = 'none';
        legendOpenButton.style.display = 'block';
      }
    }
  }

  google.maps.event.addDomListener(window, 'load', initialize);
</script>
</head>

<body>
  <div id="googft-mapCanvas"></div>
  <input id="googft-legend-open" style="display:none" type="button" value="Legend"></input>
  <div id="googft-legend">
    <p id="googft-legend-title">Nb comp 3 km</p>
    <div>
      <img class="googft-dot-icon" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJCAYAAADgkQYQAAAAi0lEQVR42mNgQIAoIF4NxGegdCCSHAMzEC+NijL7v3p1+v8zZ6rAdGCg4X+g+EyYorS0NNv////PxMCxsRYghbEgRQcOHCjGqmjv3kKQor0gRQ8fPmzHquj27WaQottEmxQLshubopAQI5CiEJjj54N8t3FjFth369ZlwHw3jQENgMJpIzSc1iGHEwB8p5qDBbsHtAAAAABJRU5ErkJggg=="/>
      <span class="googft-legend-range">0 to 5</span>
    </div>
    <div>
      <img class="googft-dot-icon" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJCAYAAADgkQYQAAAAiElEQVR42mNgQIAoIF4NxGegdCCSHAMzEC81izL7n746/X/VmSowbRho+B8oPhOmKM02zfb/TCzQItYCpDAWpOhA8YFirIoK9xaCFO0FKXrY/rAdq6Lm280gRbeJNikWZDc2RUYhRiBFITDHzwf5LmtjFth3GesyYL6bxoAGQOG0ERpO65DDCQDX7ovT++K9KQAAAABJRU5ErkJggg=="/>
      <span class="googft-legend-range">5 to 10</span>
    </div>
    <div>
      <img class="googft-dot-icon" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJCAYAAADgkQYQAAAAi0lEQVR42mNgQIAoIF4NxGegdCCSHAMzEC+NMov6vzp99f8zVWfAdKBh4H+g+EyYorQ027T//2f+x8CxFrEghbEgRQcOFB/Aqmhv4V6Qor0gRQ8ftj/Equh2822QottEmxQLshubohCjEJCiEJjj54N8tzFrI9h36zLWwXw3jQENgMJpIzSc1iGHEwBt95qDejjnKAAAAABJRU5ErkJggg=="/>
      <span class="googft-legend-range">10 to 20</span>
    </div>
    <div>
      <img class="googft-dot-icon" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJCAYAAADgkQYQAAAAiklEQVR42mNgQIAoIF4NxGegdCCSHAMzEC81M4v6n56++n9V1RkwbWgY+B8oPhOmKM3WNu3/zJn/MbCFRSxIYSxI0YHi4gNYFRUW7gUp2gtS9LC9/SFWRc3Nt0GKbhNtUizIbmyKjIxCQIpCYI6fD/JdVtZGsO8yMtbBfDeNAQ2AwmkjNJzWIYcTAMk+i9OhipcQAAAAAElFTkSuQmCC"/>
      <span class="googft-legend-range">20 to 50</span>
    </div>
    <div class="googft-legend-source">
      <a href="data?docid=1XfoTvO3_tb1JHR8HVzrIEaDhzYOq1HVfGrINH4Al" target="_blank">prix-carburants.gouv.fr</a>
    </div>
    <input id="googft-legend-close" style="display:none" type="button" value="Hide"></input>
  </div>
</body>
</html>
