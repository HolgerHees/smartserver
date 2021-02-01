<html>
<head>
<meta name="viewport" content="width=device-width,height=device-height,initial-scale=1.0,minimum-scale=1.0,maximum-scale=1.0,user-scalable=0">
<link rel="stylesheet" href="/static/shared/habpanel/css/theme.css">
<link rel="stylesheet" href="/static/shared/habpanel/css/panelui.css">
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
        while( current.parent && current.parent != window.top )
        {
            if( current.location.pathname.includes("habpanel") )
            {   
                theme = 'black';
                break;
            }
            current = current.parent;
        }
        if( parent.location.pathname.indexOf("basicui")!==-1 )
        {   
            basicui = true;
        }
    }
    catch(e){}

    document.querySelector("html").classList.add(theme);
    
    if( !basicui )
    {
        document.body.style.maxWidth = "1024px";
        document.body.style.margin = "10px auto";
    }
    else
    {
        document.body.classList.add("basicui");
    }
</script>
<div id="openButton">Woche</div>
<div class="mvWidget">
<?php
include "widgetWeatherDetailOverview.php"
?>
</div>
<script>
    var openButton = document.getElementById("openButton");
    openButton.addEventListener("click",function(){
    var weekList = document.querySelector(".mvWidget .weatherDetailForecast .week");
    if( weekList.classList.contains("open") )
    {
      weekList.classList.remove("open");
      openButton.classList.remove("open");
    }
    else
    {
      weekList.classList.add("open");
      openButton.classList.add("open");
    }
  });
  
  var elements = document.querySelectorAll('div[mv-url]');
  for( var i = 0; i < elements.length; i++)
  { 
    var element = elements[i];
    element.addEventListener("click",function()
    {
      var src = this.getAttribute("mv-url");
      var parameter = src.split("?")[1];
      document.location.href=document.location.pathname+"?"+parameter;
    });
  }
</script>
</body>
</html>
