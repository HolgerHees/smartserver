mx.Netdata = (function( ret ) {
  ret.applyTheme = function(url)
  {
      url += url.includes("?") ? '&' : '?';
      url += "theme=" + ( mx.Page.isDarkTheme() ? "slate": "white" );
      return url;
  }
  return ret;
})( mx.Netdata || {} ); 

mx.Menu.getMainGroup('admin').getSubGroup('system').addUrl('netdata',{ "url": '//netdata.{host}/', "callback": mx.Netdata.applyTheme }, 'admin', 110, '{i18n_Server State}', '{i18n_Netdata}', "netdata_logo.svg", false);

