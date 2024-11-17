mx.Netdata = (function( ret ) {
  ret.applyTheme = function(url)
  {
      js = "loadDashboard(); let settings = localStorage.getItem('userSettings'); if( settings ){ settings = JSON.parse(settings); settings['theme'] = '" +  (mx.Page.isDarkTheme() ? 'dark' : 'light') +"'; console.log(settings['theme']); localStorage.setItem('userSettings', JSON.stringify(settings)); }";
      return { 'type': 'js', 'content': js };
  }
  return ret;
})( mx.Netdata || {} );

mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('netdata', ['admin'], '//netdata.{host}/', { 'order': 110, 'title': '{i18n_Server State}', 'info': '{i18n_Netdata}', 'icon': 'netdata_logo.svg', 'callbacks': { 'ping': mx.Netdata.applyTheme } });

