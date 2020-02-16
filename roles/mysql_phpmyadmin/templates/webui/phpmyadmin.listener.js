var mxTheme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];

var css = '';

if( mxTheme == 'light' )
{
    css += `
    :root {
      --mx-link-color: #111;
      --mx-text-color: #333;
      --mx-background-color: white;
      --mx-header-background-color: #1976D2;
      --mx-header-text-color: white;

      --mx-headline-color: #111;

      --mx-active-background-color: rgba(51,122,183,.12);
      --mx-hover-background-color: rgba(51,122,183,.12);
      
      --mx-group-border-color: #1976D2;
      --mx-button-border-color: #111;
      
      --mx-table-row-odd-color: #f3f7fb;
      --mx-table-hover-color: #e6eff6;
      --mx-table-active-color: rgba(51,122,183,.12);
    }
   `;
}
else if( mxTheme == 'dark' )
{
    css += `
    :root {
      --mx-link-color: white;
      --mx-text-color: #aaa;
      --mx-background-color: #202124;
      --mx-header-background-color: rgba(25,118,210,0.3);
      --mx-header-text-color: white;
      
      --mx-headline-color: white;

      --mx-active-background-color: rgba(51,122,183,.12);
      --mx-hover-background-color: rgba(51,122,183,.12);
      
      --mx-group-border-color: rgba(25,118,210,0.3);
      --mx-button-border-color: rgba(25,118,210,0.8);

      --mx-table-row-odd-color: #222c36;
      --mx-table-hover-color: #3e5163;
      --mx-table-active-color: rgba(25,118,210,.12);
    }
   `;
}

css += `
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
    ul#topmenu, ul#topmenu2, ul.tabs {
      font-weight: normal !important;
    }
    ul#topmenu > li.active {
      border-bottom: none !important;
    }
    .group, fieldset, .group h2, .btn, ul#topmenu2 a { 
      background: none !important;
      background-image: none !important;
    }

    
    
    * {
      color: var(--mx-text-color) !important;
    }
    a:link, a:visited, a:active, a:link *, a:visited *, a:active * {
        color: var(--mx-link-color) !important;
    }
    input, select, textarea, #pma_console .toolbar, #pma_console .content, .CodeMirror-scroll, .CodeMirror-linenumbers, .CodeMirror-lint-markers {
      background: var(--mx-background-color) !important;
    }
    .result_query div.sqlOuter, div.tools, .tblFooters {
      background: var(--mx-active-background-color) !important;
      border-left: 1px solid var(--mx-group-border-color) !important;
      border-right: 1px solid var(--mx-group-border-color) !important;
    }
    .result_query div.sqlOuter {
      border-left: 1px solid var(--mx-group-border-color) !important;
      border-right: 1px solid var(--mx-group-border-color) !important;
    }
    .success {
      color: var(--mx-header-text-color) !important;
      background: var(--mx-header-background-color) !important;
      border: 1px solid var(--mx-group-border-color) !important;
    }
    div.tools, .tblFooters {
      border: 1px solid var(--mx-group-border-color) !important;
    }
    #topmenu .tabactive {
        background: var(--mx-background-color) !important;
    }
    #pma_navigation, .menucontainer, body { 
      background: var(--mx-background-color) !important;
    }
    #serverinfo, #goto_pagetop, #lock_page_icon, #page_settings_icon, #pma_navigation_collapser {
      background-color: var(--mx-header-background-color) !important;
      color: var(--mx-header-text-color) !important;
      border: none !important;
    }
    #serverinfo * {
      color: var(--mx-header-text-color) !important;
    }
    .notice, #pma_navigation_tree li.activePointer, #pma_navigation_tree li.selected {
      background: var(--mx-active-background-color) !important;
    }
    th, table {
        border: none !important;
    }
    thead th { 
      border-bottom: 1px solid var(--mx-group-border-color) !important;
    }
    tfoot th, #tbl_summary_row th { 
      border-top: 1px solid var(--mx-group-border-color) !important;
    }
    table tbody:first-of-type tr:nth-child(2n+1), table tbody:first-of-type tr:nth-child(2n+1) th, #table_index tbody:nth-of-type(2n+1) tr, #table_index tbody:nth-of-type(2n+1) th {
      background: var(--mx-background-color) !important;
    }
    table tbody:first-of-type tr:nth-child(2n), table tbody:first-of-type tr:nth-child(2n) th, #table_index tbody:nth-of-type(2n) tr, #table_index tbody:nth-of-type(2n) th {
      background: var(--mx-table-row-odd-color) !important;
    }
    table tbody:first-of-type tr:not(.nopointer):hover, table tbody:first-of-type tr:not(.nopointer):hover th, .hover:not(.nopointer) {
      background: var(--mx-table-hover-color) !important;
    }
    td.marked:not(.nomarker), table tr.marked:not(.nomarker) td, table tbody:first-of-type tr.marked:not(.nomarker) th, table tr.marked:not(.nomarker) {
      background: var(--mx-table-active-color) !important;
    }
    h2 { 
      color: var(--mx-headline-color) !important;
    }
    .group, fieldset, legend, .group h2, .btn, ul#topmenu2 a { 
      background-color: var(--mx-background-color) !important;
    }
    fieldset, .group {
      border: var(--mx-group-border-color) solid 1px !important;
    }
    legend {
      border: none !important;
    }
    select, input, ul#topmenu2 a {
      border: var(--mx-button-border-color) solid 1px !important;
    }
    ul#topmenu > li { 
      border-right: 1px solid var(--mx-group-border-color) !important;
      border-bottom: 1px solid var(--mx-group-border-color) !important;
    }
    ul.resizable-menu li:hover { 
      background: var(--mx-hover-background-color) !important;
    }
`;
var element = document.createElement('style');
element.type = 'text/css'; 
element.innerHTML = css;

document.getElementsByTagName("head")[0].appendChild(element); 
