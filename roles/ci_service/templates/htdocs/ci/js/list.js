mx.CIList = (function( ret ) {
    var listElement = null;
    var stateColorSelector = null;
    var stateTextSelector = null;
    var runtimeSelector = null;
        
    var elementStates = {};
    var elementRunningDuration = {};

    var duration = 0;
    
    var currentInterval = 0;

    function refreshDuration(runtimeElement)
    {
        for( key in elementRunningDuration )
        {
            var formattedDuration = mx.Logfile.formatDuration(++elementRunningDuration[key]);
            document.getElementById(key).querySelector(runtimeSelector).innerHTML = formattedDuration;
        }
    }
    
    function registerNode(node)
    {
        var hash = node.getAttribute("id");
        var state = node.getAttribute("data-state");
        var duration = node.getAttribute("data-duration");
    
        elementStates[hash] = state;
        if( state == "running" ) elementRunningDuration[hash] = duration;
    }
    
    function getRefreshInterval(hasRunningJobs)
    {
        return hasRunningJobs ? 5 : 10;
    }
    
    function handleListUpdates(data)
    {
        var content = document.createElement("div");
        content.innerHTML = data;
        
        var newJobs = content.querySelector("#newJobs").childNodes;
        var runningJobs = content.querySelector("#runningJobs").childNodes;
        var removedJobHashes = content.querySelector("#removedJobs").innerHTML;
        if( removedJobHashes ) removedJobHashes = removedJobHashes.split(",");
        
        if( runningJobs.length > 0 )
        {
            for( i = 0; i < runningJobs.length; i++ )
            {
                var job = runningJobs[i];
                
                var hash = job.getAttribute("id");
                
                var _state = job.querySelector(".state").innerHTML;
                var _stateElementFormatted = job.querySelector(".stateFormatted > *");

                var _duration = job.querySelector(".duration").innerHTML;
                var _durationFormatted = job.querySelector(".durationFormatted").innerHTML;
                
                var row = document.getElementById(hash);

                if( _state == 'running' )
                {
                    elementRunningDuration[hash] = _duration;
                    row.querySelector(runtimeSelector).innerHTML = _durationFormatted;
                }
                else
                {
                    var stateTextElement = row.querySelector(stateTextSelector);
                    stateTextElement.innerHTML = _stateElementFormatted.innerHTML;
                    stateTextElement.className = _stateElementFormatted.className;

                    var stateColorElement = row.querySelector(stateColorSelector);
                    stateColorElement.classList.remove('running');
                    stateColorElement.classList.add(_state);

                    elementStates[hash] = _state;
                    delete elementRunningDuration[hash];
                }
            }
        }
        
        if( newJobs.length > 0 )
        {
            var firstElement = listElement.firstChild;
            var parentElement = firstElement.parentNode;

            for( i = newJobs.length - 1; i >= 0 ; i-- )
            {
                var newNode = newJobs[i].cloneNode(true);
                
                registerNode(newNode);
                            
                parentElement.insertBefore(newNode, firstElement);
                firstElement = newNode;
                
                var job = newJobs[i];
            }
        }
        
        if( removedJobHashes.length > 0 )
        {
            for( i = 0; i < removedJobHashes.length ; i++ )
            {
                var hash = removedJobHashes[i];
                var row = document.getElementById(hash);
                if( row )
                {
                    row.parentNode.removeChild(row);
                    delete elementRunningDuration[hash];
                    delete elementStates[hash];
                }
            }
        }
    }
    
    function updateList(force)
    {
        var hasRunningJobs = Object.keys(elementRunningDuration).length > 0
        refreshInterval = getRefreshInterval(hasRunningJobs);
        
        if( force || !hasRunningJobs ) currentInterval = 0;
             
        if( currentInterval == 0 )
        {
            var url = mx.Host.getBase() + 'index_update.php';
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", url );
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 ) 
                {
                    handleListUpdates(this.response);
                                            
                    hasRunningJobs = Object.keys(elementRunningDuration).length > 0
                    refreshInterval = getRefreshInterval(hasRunningJobs);

                    updateTimer = window.setTimeout(updateList, hasRunningJobs ? 1000 : refreshInterval * 1000);
                }
                else 
                {
                    try 
                    {
                        window.top.mx.State.handleRequestError(this.status,url,updateList);
                    }
                    catch
                    {
                        updateTimer = window.setTimeout(updateList, 10000);
                    }
                }
            };
            
            var data = {};
            data['visibleJobs'] = Object.keys(elementStates);
            data['runningJobs'] = Object.keys(elementRunningDuration);
            
            xhr.send(JSON.stringify(data));
        }
        else if( updateTimer )
        {
            refreshDuration();
            updateTimer = window.setTimeout(updateList,1000);
        }

        currentInterval += 1;
        if( currentInterval == refreshInterval ) currentInterval = 0;
    }
    
    ret.startUpdateProcess = function(position)
    {
        updateList(true);
    }
    
    ret.init = function(_rows, _listElement, _stateColorSelector, _stateTextSelector, _runtimeSelector)
    {
        if( _rows.length > 0 )
        {
            for( i = 0; i < _rows.length; i++ )
            {
                registerNode(_rows[i]);
            }
        }
        
        listElement = _listElement;
        stateColorSelector = _stateColorSelector;
        stateTextSelector = _stateTextSelector;
        runtimeSelector = _runtimeSelector;
    }

    return ret;
})( mx.CIList || {} );
