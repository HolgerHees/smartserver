var mxTheme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];

var css = `
  * {
    box-shadow: none !important;
    text-shadow: none !important;
  }
  thead th, tfoot th, #tbl_summary_row th { 
    background: transparent !important; 
  }
  ul#topmenu > li { 
    border-left: none !important;
  }
`;

if( mxTheme == 'light' )
{
    css += `
    #pma_navigation, .menucontainer { 
      background: #fff !important;
    }
    #serverinfo, #goto_pagetop, #lock_page_icon, #page_settings_icon {
      background-color: #1976D2 !important;
    }
    .notice, #pma_navigation_tree li.activePointer, #pma_navigation_tree li.selected, table tbody:first-of-type tr:not(.nopointer):hover, table tbody:first-of-type tr:not(.nopointer):hover th, .hover:not(.nopointer) {
      background: rgba(51,122,183,.12) !important;
    }
    thead th { 
      border-bottom: 1px solid #1976D2;
    }
    tfoot th { 
      border-top: 1px solid #1976D2;
    }
    table tbody:first-of-type tr:nth-child(2n), table tbody:first-of-type tr:nth-child(2n) th, #table_index tbody:nth-of-type(2n) tr, #table_index tbody:nth-of-type(2n) th {
      background: rgba(51,122,183,.06) !important;
    }
    .group h2 { 
      color: #111 !important;
    }
    .group, fieldset, .group h2, .btn { 
      background: none !important;
      background-image: none !important;
      background-color: #fff !important;
    }
    ul#topmenu > li { 
      border-right: 1px solid #ccc !important;
    }
    ul.resizable-menu li:hover { 
      background: rgba(51,122,183,.12) !important;
    }
  `;
}
else if( mxTheme == 'dark' )
{
    css += `
    * {
      color: #aaa !important;
    }
    a:link, a:visited, a:active, a:link *, a:visited *, a:active * {
        color: #fff !important;
    }
    input, select, #pma_console .toolbar, #pma_console .content, #pma_console .CodeMirror-scroll {
      background: #202124 !important;
    }
    #topmenu .tabactive {
        background: rgba(51,122,183,.3) !important;
    }
    #pma_navigation, .menucontainer, body { 
      background: #202124 !important;
    }
    #serverinfo, #goto_pagetop, #lock_page_icon, #page_settings_icon {
      background-color: rgba(25,118,210,0.3) !important;
    }
    .notice, #pma_navigation_tree li.activePointer, #pma_navigation_tree li.selected, table tbody:first-of-type tr:not(.nopointer):hover, table tbody:first-of-type tr:not(.nopointer):hover th, .hover:not(.nopointer) {
      background: rgba(51,122,183,.12) !important;
    }
    table tbody:first-of-type tr:nth-child(2n+1), table tbody:first-of-type tr:nth-child(2n+1) th, #table_index tbody:nth-of-type(2n+1) tr, #table_index tbody:nth-of-type(2n+1) th {
      background: #202124 !important;
    }
    thead th { 
      border-bottom: 1px solid rgba(25,118,210,0.3);
    }
    tfoot th, #tbl_summary_row th { 
      border-top: 1px solid rgba(25,118,210,0.3);
    }
    table tbody:first-of-type tr:nth-child(2n), table tbody:first-of-type tr:nth-child(2n) th, #table_index tbody:nth-of-type(2n) tr, #table_index tbody:nth-of-type(2n) th {
      background: rgba(51,122,183,.06) !important;
    }
    .group h2 { 
      color: #111 !important;
    }
    .group, fieldset, .group h2, .btn { 
      background: none !important;
      background-image: none !important;
      background-color: #202124 !important;
    }
    ul#topmenu > li { 
      border-right: 1px solid #ccc !important;
    }
    ul.resizable-menu li:hover { 
      background: rgba(51,122,183,.12) !important;
    }
  `;
}
var element = document.createElement('style');
element.type = 'text/css'; 
element.innerHTML = css;

document.getElementsByTagName("head")[0].appendChild(element); 
