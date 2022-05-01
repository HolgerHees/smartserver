mx.Grafana = (function( ret ) {
  ret.applyTheme = function(url)
  {
      url += url.includes("?") ? '&' : '?';
      url += "theme=" + ( mx.Page.isDarkTheme() ? "dark": "light" );
      return url;
  }
  return ret;
})( mx.Grafana || {} ); 

mx.Menu.getMainGroup('admin').getSubGroup('tools').addUrl('grafana_ui', { "url": '//grafana.{host}/', "callback": mx.Grafana.applyTheme },'admin', 210, '{i18n_Grafana}', '{i18n_Dashboards}', false, 'grafana_logo.svg');
