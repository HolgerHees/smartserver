mx.CICore = (function( ret ) {

    ret.openDetails = function(event,datetime,config,os,branch,hash)
    {
        document.location = 'details.php?datetime=' + datetime + '&config=' + config + '&os=' + os + '&branch=' + branch + '&hash=' + hash;
    }
    ret.openOverview = function(event)
    {
        document.location = './';
    }
    ret.openGitCommit = function(event,url)
    {
        event.stopPropagation();
        window.open(url);
    }
    
    ret.formatDuration = function(duration)
    {
        var days = Math.floor(duration / 86400);
        duration -= days * 86400;
        var hours = Math.floor(duration / 3600);
        duration -= hours * 3600;
        var minutes = Math.floor(duration / 60);
        var seconds = duration - minutes * 60;
        
        if( hours < 10 ) hours = '0' + hours;
        if( minutes < 10 ) minutes = '0' + minutes;
        if( seconds < 10 ) seconds = '0' + seconds;

        return hours + ':' + minutes + ':' + seconds;
    }
    
    return ret;
})( mx.CICore || {} );
