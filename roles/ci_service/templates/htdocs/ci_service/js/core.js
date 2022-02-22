mx.CICore = (function( ret ) {

    ret.openDetails = function(event,datetime,config,os,branch,hash)
    {
        document.location = './details/?datetime=' + datetime + '&config=' + config + '&os=' + os + '&branch=' + branch + '&hash=' + hash;
    }
    ret.openOverview = function(event)
    {
        document.location = '../';
    }
    ret.openGitCommit = function(event,url)
    {
        event.stopPropagation();
        window.open(url);
    }
    return ret;
})( mx.CICore || {} );
