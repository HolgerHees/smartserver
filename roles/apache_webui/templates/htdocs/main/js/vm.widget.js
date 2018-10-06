$.vmWidget = function( name, base ) {

	//var namespace = name.split( "." )[ 0 ];
	//name = name.split( "." )[ 1 ];

	//$[ namespace ] = $[ namespace ] || {};
	//var existingConstructor = $[ namespace ][ name ];

	$.fn[name] = function( data, additionals ){

		var instanceName = "_" + name;
		var instance = this[ instanceName ];

		if( !instance ) instance = this.data( instanceName );

		if( typeof data == 'object' )
		{
			if( !instance )
			{
				instance = {};

				$.extend(true, instance, base);
				$.extend(true, instance.options, data);

				instance.create(this);

				this.data( instanceName, instance );

				this[ instanceName ] = instance;
			}
		}
		else if( instance )
		{
			if( data == "remove" )
			{
				instance.destroy(data, additionals);
				this.removeData( instanceName );
				delete this[ instanceName ];
			}
			else
			{
				instance.call(data, additionals);
			}
		}

		return this;
	}
};