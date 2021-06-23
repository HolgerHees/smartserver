var mxTheme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];

var css = `
  header, header > * { 
    max-height: 56px !important; 
    min-height: 56px !important; 
  }`;

if( mxTheme == 'light' )
{
    css += `
      body[data-theme="default"] {
          --body-bg: white !important;
          --header-bg: #1976D2 !important;
      }
   `;
}
else if( mxTheme == 'dark' )
{
    css += `
      body[data-theme="default"] {
          --body-bg: #202124 !important;
          --header-bg: rgba(25,118,210,0.3) !important;
      }
    `;
}
var element = document.createElement('style');
element.type = 'text/css'; 
element.innerHTML = css;

document.getElementsByTagName("head")[0].appendChild(element); 

const hideWebviewImages = function()
{
    var imgs = document.querySelectorAll('img[data-icon=webview]');
    imgs.forEach(function(img, index) {
        img.parentNode.parentNode.style.display="none";
    });
}

const callback = function(mutationsList, observer) {
    hideWebviewImages();
}
const config = { attributes: false, childList: true, subtree: true };
const observer = new MutationObserver(callback);
observer.observe(document, config);
