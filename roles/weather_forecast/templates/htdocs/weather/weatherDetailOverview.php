<html>
<head>
<title>Wetterbericht</title>
<meta name="viewport" content="width=device-width,height=device-height,initial-scale=1.0,minimum-scale=1.0,maximum-scale=1.0,user-scalable=0">
<link rel="stylesheet" href="./css/main.css">
<link rel="stylesheet" href="./css/panelui.css">
<style>
.mxWidget * {
    box-sizing: border-box;
    background-color: red;
}
</style>
</head>
<body>
<script>
    var theme = "";
    if( document.cookie.indexOf("theme=") != -1 )
    {
        var cookies = document.cookie.split(";");
        for(var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].split("=");
            if( cookie[0].trim() == "theme" )
            {
                theme = cookie[1].trim();
                break;
            }
        }
    }
    else
    {
        var isPhone = ( navigator.userAgent.indexOf("Android") != -1 && navigator.userAgent.indexOf("Mobile") != -1 );
        theme = isPhone ? 'black' : 'light';
    }
    
    var basicui = false;
    try{
        var current = window;
        while( current )
        {
            if( current.location.pathname.includes("habpanel") )
            {   
                theme = 'black';
                break;
            }
            current = current != current.parent ? current.parent : null;
        }
        if( parent.location.pathname.indexOf("basicui")!==-1 )
        {   
            basicui = true;
        }
    }
    catch(e){}

    document.querySelector("html").classList.add(theme);
    document.querySelector("html").classList.add(theme == "light" ? "lightTheme" : "darkTheme" );

    if( basicui )
    {
        document.body.classList.add("basicui");
    }
</script>
<div id="openButton">Woche</div>
<div id="rainButton">Radar</div>
<div class="mvWidget">
<?php
include "widgetWeatherDetailOverview.php"
?>
</div>
<div id="rainFrame"><iframe src=""></iframe></div>
<script>
  var openButton = document.getElementById("openButton");
  openButton.addEventListener("click",function(){
    var weekList = document.querySelector(".mvWidget .weatherDetailForecast .week");
    if( weekList.classList.contains("open") )
    {
      openButton.innerHTML = "Woche";
      openButton.classList.remove("open");
      weekList.classList.remove("open");
      window.setTimeout(function(){
        if( !openButton.classList.contains("open") )
        {
          openButton.style.zIndex = "";
          openButton.classList.remove("animated");
        }
      },300);
    }
    else
    {
      openButton.classList.add("animated");
      window.setTimeout(function(){
        openButton.innerHTML = "Schliessen";
        openButton.style.zIndex = "101";
        openButton.classList.add("open");
        weekList.classList.add("open");
      },0);
    }
  });
  
  // LOCATION => 52.3476672,13.6215805 lat / long
  // target => 1516323.13/6863234.61
  
  var rainButton = document.querySelector("#rainButton");
  var rainFrame = document.querySelector("#rainFrame iframe");
  rainFrame.src="about:blank";
  rainButton.addEventListener("click",function(){
    //var url = "https://meteocool.com/#widgetMap=10/<?php echo str_replace(",","/",LOCATION); ?>/1";
    //var url = "https://meteocool.com/?latLonZ=52.347667%2C13.621581%2C10.00&logo=";
    //var url = "https://www.windy.com/de/-Wetterradar-radar?radar,52.316,13.392,10";
    //var url = "https://meteocool.com/#map=10/1516347.41/6863233.92/0";
    var url = "https://embed.windy.com/embed2.html?lat=52.344&lon=13.618&detailLat=52.316&detailLon=13.392&zoom=10&level=surface&overlay=radar&product=radar&menu=&message=true&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1"
    //window.open(url);
    if( rainFrame.parentNode.classList.contains("open") )
    {
      rainButton.classList.remove("open");
      rainButton.innerHTML = "Radar";
      rainFrame.parentNode.classList.remove("open");
      rainFrame.src="";
      window.setTimeout(function(){
        if( !openButton.classList.contains("open") )
        {
          rainButton.style.zIndex = "";
          rainButton.classList.remove("animated");
        }
      },300);
    }
    else
    {
      rainButton.classList.add("animated");
      window.setTimeout(function(){
        rainButton.innerHTML = "Schliessen";
        rainButton.style.zIndex = "101";
        rainButton.classList.add("open");
        rainFrame.parentNode.classList.add("open");
        rainFrame.src=url;
      },0);
    }
  });
  
  function clickHandler()
  {
    var src = this.getAttribute("mv-url");
    var parameter = src.split("?")[1];
    
    xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function (e) { 
      if (xhr.readyState == 4 && xhr.status == 200) {
        openButton.classList.remove("open");
        openButton.innerHTML = "Woche";
        
        element = document.querySelector(".mvWidget");
        element.innerHTML = xhr.responseText;
        
        var elements = element.querySelectorAll('div[mv-url]');
        for( var i = 0; i < elements.length; i++)
        { 
          var element = elements[i];
          element.addEventListener("click",clickHandler);
        }
      }
    }
    
    xhr.open("GET", "<?php echo dirname($_SERVER['REQUEST_URI']); ?>/widgetWeatherDetailOverview.php?"+parameter, true);
    xhr.setRequestHeader('Content-type', 'text/html');
    xhr.send();


    //document.location.href=document.location.pathname+"?"+parameter;
  }
  
  var elements = document.querySelectorAll('div[mv-url]');
  for( var i = 0; i < elements.length; i++)
  { 
    var element = elements[i];
    element.addEventListener("click",clickHandler);
  }
</script>
</body>
</html>
