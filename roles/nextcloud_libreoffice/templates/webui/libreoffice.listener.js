var mxTheme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];

var css = '';

if( mxTheme == 'light' )
{
    css += `
    nav:not(.hasnotebookbar).main-nav {
        background-color: #1976D2 !important;
    }
    nav:not(.hasnotebookbar) #main-menu > li > a {
        color: white !important;
        border: none !important;
    }
    nav:not(.hasnotebookbar) #main-menu > li > a.highlighted,
    nav:not(.hasnotebookbar) #main-menu > li > a:active,
    nav:not(.hasnotebookbar) #main-menu > li > a:hover,
    #closebuttonwrapper:hover,
    nav:not(.hasnotebookbar) > #icon-nextcloud-sidebar.icon-nextcloud-sidebar:hover {
        background-color: #0966C2 !important;
    }
    nav:not(.hasnotebookbar) #menu-last-mod > a span, nav:not(.hasnotebookbar) #menu-last-mod > a span:hover, #document-name-input {
        color: #3c4043 !important;
    }
   `;
}
else if( mxTheme == 'dark' )
{
    css += `
    nav:not(.hasnotebookbar).main-nav {
        background-color: #1976d24D !important;
    }
    nav:not(.hasnotebookbar) #main-menu > li > a {
        color: #202124 !important;
        border: none !important;
    }
    nav:not(.hasnotebookbar) #main-menu > li > a.highlighted,
    nav:not(.hasnotebookbar) #main-menu > li > a:active,
    nav:not(.hasnotebookbar) #main-menu > li > a:hover,
    #closebuttonwrapper:hover,
    nav:not(.hasnotebookbar) > #icon-nextcloud-sidebar.icon-nextcloud-sidebar:hover {
        background-color: #0966C24D !important;
    }
    nav:not(.hasnotebookbar) #menu-last-mod > a span, nav:not(.hasnotebookbar) #menu-last-mod > a span:hover, #document-name-input {
        color: #fff !important;
    }
   `;
}

css += `
    nav:not(.hasnotebookbar).main-nav {
        height: 53px !important;
    }
`;
var element = document.createElement('style');
element.type = 'text/css'; 
element.innerHTML = css;

document.getElementsByTagName("head")[0].appendChild(element); 
