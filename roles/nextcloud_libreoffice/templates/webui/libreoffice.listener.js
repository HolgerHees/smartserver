var mxTheme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];

var css = `
    nav:not(.hasnotebookbar).main-nav {
        height: 53px !important;
    }
    .lo-menu > li a {
        color: #3c4043
    }
    .lo-menu > li .disabled {
        opacity: 0.4;
    }
`;
var element = document.createElement('style');
element.type = 'text/css'; 
element.innerHTML = css;

document.getElementsByTagName("head")[0].appendChild(element); 
