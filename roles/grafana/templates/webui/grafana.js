mx.Grafana = (function( ret ) {
  ret.applyTheme = function(url)
  {
      url += url.includes("?") ? '&' : '?';
      url += "theme=" + ( mx.Page.isDarkTheme() ? "dark": "light" );
      return url;
  }
  return ret;
})( mx.Grafana || {} );

mx.Menu.getMainGroup('admin').getSubGroup('tools').addUrl('grafana_ui', ['admin'], '//grafana.{host}/', { 'order': 210, 'title': '{i18n_Grafana}', 'info': '{i18n_Dashboards}', 'icon': 'grafana_logo.svg', 'callbacks': { 'url': mx.Grafana.applyTheme } });
