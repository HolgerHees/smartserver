mx.Grafana = (function( ret ) {
  ret.applyTheme = function(url)
  {
      url += url.includes("?") ? '&' : '?';
      url += "theme=" + ( mx.Page.isDarkTheme() ? "dark": "light" );
      return url;
  }
  return ret;
})( mx.Grafana || {} ); 

let menu = mx.Menu.getMainGroup('admin');
menu.getSubGroup('system').addUrl('grafana_logs', { "url": '//grafana.{host}/d/logs/logs?autofitpanels', "callback": mx.Grafana.applyTheme },'admin', 100, '{i18n_Server Logs}', '{i18n_Grafana}', false, 'grafana_logs.svg');
menu.getSubGroup('tools').addUrl('grafana_ui', { "url": '//grafana.{host}/', "callback": mx.Grafana.applyTheme },'admin', 210, '{i18n_Grafana}', '{i18n_Dashboards}', false, 'grafana_logo.svg');
