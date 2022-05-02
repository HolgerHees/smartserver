mx.Netdata = (function( ret ) {
  ret.applyTheme = function(url)
  {
      url += url.includes("?") ? '&' : '?';
      url += "theme=" + ( mx.Page.isDarkTheme() ? "slate": "white" );
      return url;
  }
  return ret;
})( mx.Netdata || {} ); 

mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('netdata',{ "url": '//netdata.{host}/', "callback": mx.Netdata.applyTheme }, 'admin', 110, '{i18n_Server State}', '{i18n_Netdata}', false, "netdata_logo.svg");

mx.Alarms = (function( ret ) {
    var buttonSelector;
    var counterSelector;
    var alarmIsWorking = true;

    function handleAlarms(data) 
    {
        var warnCount = 0;
        var errorCount = 0;

        for(x in data.alarms) 
        {
            if(!data.alarms.hasOwnProperty(x)) continue;

            var alarm = data.alarms[x];
            if(alarm.status === 'WARNING')
            {
                warnCount++;
            }
            if(alarm.status === 'CRITICAL')
            {
                errorCount++;
            }
        }

        mx.$$(counterSelector).forEach(function(element){ element.innerText = warnCount + errorCount });

        var badgeButtons = mx.$$(buttonSelector);
        if( warnCount > 0 )
        {
            badgeButtons.forEach(function(element){ element.classList.add("warn") });
        }
        else
        {
            badgeButtons.forEach(function(element){ element.classList.remove("warn") });
        }
        if( errorCount > 0 )
        {
            badgeButtons.forEach(function(element){ element.classList.add("error") });
        }
        else
        {
            badgeButtons.forEach(function(element){ element.classList.remove("error") });
        }
    }            

    function loadAlerts()
    {
        var id = Math.round( Date.now() / 1000 );

        var url = "//" + mx.Host.getAuthPrefix() + "netdata." + mx.Host.getDomain() + "/api/v1/alarms?active&_=" + id;
        
        var xhr = new XMLHttpRequest();
        xhr.open("GET", url );
        xhr.withCredentials = true;
        xhr.onreadystatechange = function() {
            //console.log(this.responseURL);
    
            if (this.readyState != 4) return;

            if( this.status == 200 )
            {
                if( !alarmIsWorking )
                {
                    mx.$$(buttonSelector).forEach(function(element){ element.classList.remove("disabled") });
                    alarmIsWorking = true;
                }
                handleAlarms( JSON.parse(this.response) );

                // must be 10000, because the apache KeepAlive timeout is 15 seconds. 
                // Otherwise, the https connection is established again and again and will take ~700ms instead of 40ms 
                window.setTimeout(loadAlerts,10000);
            }
            else if( alarmIsWorking )
            {
                mx.$$(buttonSelector).forEach(function(element){ element.classList.add("disabled") });
                alarmIsWorking = false;

                mx.Page.handleRequestError(this.status,url,loadAlerts);
            }
        };
        xhr.send();
    }

    ret.init = function(_buttonSelector,_counterSelector)
    {
        buttonSelector = _buttonSelector;
        counterSelector = _counterSelector;
        
        mx.$$(buttonSelector).forEach(function(element){ 
            element.addEventListener("click",function()
            {
                mx.Actions.openEntry(mx.Menu.getMainGroup('admin').getSubGroup('system').getEntry('netdata'));
            });
        });
        loadAlerts();
    }

    return ret;
})( mx.Alarms || {} );
