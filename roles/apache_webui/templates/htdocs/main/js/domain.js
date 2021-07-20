if( window.parent != window && window.parent == window.top ){ 
    window.top.postMessage({ type: 'load', url: document.location.href },'https://' + document.domain); 
    var _pushState = history.pushState; 
    history.pushState = function() { 
        _pushState.apply(this, arguments); 
        window.top.postMessage({ type: 'pushState', url: document.location.href },'https://' + document.domain); 
    }; 
    var _replaceState = history.replaceState; 
    history.replaceState = function() { 
        _replaceState.apply(this, arguments); 
        window.top.postMessage({ type: 'replaceState', url: document.location.href },'https://' + document.domain); 
    }; 
} 
