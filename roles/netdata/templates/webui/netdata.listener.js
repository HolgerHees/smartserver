var mxTheme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];

if( mxTheme == 'light' ) localStorage.setItem('netdataTheme', "white");
else if( mxTheme == 'dark' ) localStorage.setItem('netdataTheme', "slate");

//console.log(localStorage.getItem("netdataTheme"));
