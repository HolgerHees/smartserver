$.vmWidget("panel", {
	options: {
		classes: {
			panel: "vm-panel",
			panelOpen: "vm-panel-open",
			panelClosed: "vm-panel-closed",
			page: "vm-page",
			pageMoved: "vm-page-moved",
			dismiss: "vm-panel-dismiss",
			dismissOpen: "vm-panel-dismiss-open",
			dismissDark: "vm-panel-dismiss-dark",
			animate: "vm-animate",
			positionPrefix: "vm-panel-position-"
		},
		animate: true,
		defaults: true,
		dismissible: true,
		dismissDark: true,
		dismissTop: -1,
		swipeClose: true,
		positionFixed: true,
		position: "left",
		display: "overlay",
		pageSelector: "[data-role='header'], [data-role='main'], [data-role='footer']"
	},

	_panel: null,
	_page: null,
	_wrapper: null,
	_dismiss: null,
	_document: null,

	_isOpen: false,
	_isOverlay: false,

	// used for manual panel swipe
	_touchStartPosition: -1,
	_touchStartTime: -1,
	_touchDistance: -1,
	_transitionReference: -1,
	_transitionValue: -1,
	_isManualMoved: false,

	create: function(panel) {

		var self = this;

		self._panel = panel;//$('div[data-role="panel"]');

		self._isOverlay = ( self.options.display == "overlay" );

		if (!self._isOverlay) {
			var $page = $('div[data-role="page"]');

			if ($page.children().length > 1) {
				self._wrapper = $page.children(self.options.pageSelector).wrapAll("<div></div>").parent();
			}
			else {
				self._wrapper = $page.children().first();
			}
			self._page = $page;
		}
		else {
			self._wrapper = $("body");
			self._page = self._wrapper;

			$(window).on("touchstart.panel", function( event ) { self._touchStart( event ); } );
		}

		self._document = $(window.document);

		self._createModal();

		self._addPanelClasses();

		self._bindPageEvents();

		self._bindSwipeEvents();
	},
	destroy: function() {
		this._cleanPanelClasses();
	},
	call: function(cmd, data) {
		switch (cmd) {
			case "open":
				this._open();
				break;
			case "close":
				this._close();
				break;
			case "toggle":
				this._toggle();
				break;
			default:
				break;
		}
	},
	_createModal: function() {
		var self = this;

		if (self._dismiss || !this.options.dismissible)
			return;

		var className = self.options.classes.dismiss;

		if (this.options.dismissDark) {
			className = className + ' ' + self.options.classes.dismissDark;
		}

		self._dismiss = $("<div></div>", {
			css: this.options.dismissTop >= 0 ? {top: this.options.dismissTop} : {},
			addClass: className,
			on: {
				click: function() {
					self._close();
				}
			}
		}).appendTo(self._wrapper);
	},
	_cleanPanelClasses: function() {
		if (this._panel) {
			this._panel.removeClass(function(index, css) {
				return (css.match(/(^|\s)vm-\S+/g) || []).join(' ');
			});
		}

		if (this._wrapper) {
			this._wrapper.removeClass(function(index, css) {
				return (css.match(/(^|\s)vm-\S+/g) || []).join(' ');
			});
		}

		if (this._dismiss) {
			this._dismiss.removeClass(function(index, css) {
				return (css.match(/(^|\s)vm-\S+/g) || []).join(' ');
			});
		}
	},
	_addPanelClasses: function() {
		this._panel.addClass(
				this.options.classes.panel
				+ " " + this.options.classes.positionPrefix + ( this.options.position == "left" ? "left" : "right" )
				+ " " + this.options.classes.panelClosed
		);
		if (!this._isOverlay) {
			this._wrapper.addClass(
					this.options.classes.page
					+ " " + this.options.classes.positionPrefix + ( this.options.position == "left" ? "left" : "right" )
			);
		}
		var self = this;
		window.setTimeout( function() {
			if (self.options.animate) {
				self._panel.addClass(self.options.classes.animate);

				if (self._dismiss) {
					self._dismiss.addClass(self.options.classes.animate);
				}

				if (!self._isOverlay) {
					self._wrapper.addClass(self.options.classes.animate);
				}
			}
		}, 0 );
	},
	_bindPageEvents: function() {
		var self = this;

		this._document
		// Close the panel if another panel on the page opens
				.on("panelbeforeopen", function(e) {
					if (self._open && e.target !== self._panel) {
						self._close();
					}
				})
				// On escape, close? might need to have a target check too...
				.on("keyup.panel", function(e) {
					if (e.keyCode === 27 && self._open) {
						self._close();
					}
				});
	},
	_bindSwipeEvents: function() {
		var self = this;

		// on swipe, close the panel
		if (self.options.swipeClose) {
			self._page.on(self.options.position === "left" ? "swipeleft.panel" : "swiperight.panel", function(/* e */) {
				self._close();
			});
		}
	},
	_trigger: function(type, event, data) {
		var prop, orig,
				callback = this.options[type];

		data = data || {};
		event = $.Event(event);
		event.type = ( type === this.widgetEventPrefix ?
				type :
		this.widgetEventPrefix + type ).toLowerCase();
		// the original event may come from any element
		// so we need to reset the target on the new event
		event.target = this._panel;

		// copy original event properties over to the new event
		orig = event.originalEvent;
		if (orig) {
			for (prop in orig) {
				if (!( prop in event )) {
					event[prop] = orig[prop];
				}
			}
		}

		this._panel.trigger(event, data);
		return !( $.isFunction(callback) &&
		callback.apply(this._panel, [event].concat(data)) === false ||
		event.isDefaultPrevented() );
	},
	_toggle: function() {
		this[this._isOpen ? "_close" : "_open"]();
	},
	_open: function(immediate) {
		if (!this._isOpen) {
			var self = this,
					o = self.options;

			var _complete = function() {
				self._panel.off('transitionend');
				self._trigger("open");
			};

			var _openPanel = function() {

				self._trigger("beforeopen");

				if (!immediate && o.animate) {
					self._panel.on("transitionend", _complete);
				}
				else {
					setTimeout(_complete, 0);
				}
				//self._off( self.document , "panelclose" );

				self._panel.removeClass(o.classes.panelClosed).addClass(o.classes.panelOpen);

				if (self._dismiss)
				{
					self._dismiss.addClass(o.classes.dismissOpen);
				}

				if (!self._isOverlay)
				{
					self._wrapper.addClass(o.classes.pageMoved);
				}
			};

			_openPanel();

			self._isOpen = true;
		}
	},
	_close: function(immediate) {
		if (this._isOpen) {
			var self = this,
					o = this.options;

			var _complete = function() {
				self._panel.off('transitionend');
				self._panel.addClass(o.classes.panelClosed);
				self._trigger("close");
			};

			var _closePanel = function() {

				self._trigger("beforeclose");

				if (!immediate && o.animate) {
					self._panel.on("transitionend", _complete);
				}
				else {
					setTimeout(_complete, 0);
				}

				self._panel.removeClass(o.classes.panelOpen);

				if (self._dismiss)
				{
					self._dismiss.removeClass(o.classes.dismissOpen);
				}

				if (!self._isOverlay)
				{
					self._wrapper.removeClass(o.classes.pageMoved);
				}
			};

			_closePanel();

			self._isOpen = false;
		}
	},
	_touchStart: function(event)
	{
		//console.log( this.options.position );
		//console.log(  this._panel[0] );

		var _panel = $('.vm-panel');

		// check if any panel is open
		for( var i = 0; i < _panel.length; i++ )
		{
			// found an active panel
			if( $(_panel[i]).hasClass("vm-panel-open") )
			{
				// if the active panel is different to the current one. Skip touchStart.
				// touch/swipe actions are ony allowed to the current active panel
				if( this._panel[0] !== _panel[i] )
				{
					return;
				}
			}
		}

		var elementOffset = this._panel[0].getBoundingClientRect().left;
		if( this.options.position === "left" ) elementOffset = elementOffset + this._panel[0].offsetWidth;

		var currentOffset = event.originalEvent.touches[0].clientX;

		var diff = currentOffset - elementOffset;

		if( Math.abs(diff) < 45)
		{
			//event.stopPropagation();

			this._touchStartPosition = currentOffset;
			this._touchStartTime = Date.now();
			this._touchDistance = -1;
			this._transitionReference = this._isOpen ? 0 : 100;
			this._transitionValue = -1;

			this._panel.addClass("manualControl");

			var self = this;
			$(window).on( "touchmove.panel", function( event ){ self._touchMove( event ); } );
			$(window).on( "touchend.panel", function( event ){ self._touchEnd( event ); } );
			$(window).on( "touchcancel.panel", function( event ){ self._touchEnd( event ); } );
		}
	},
	_touchEnd: function(event)
	{
		//console.log("touchend");

		//event.stopPropagation();

		if(this._isManualMoved)
		{
			//console.log(touchLastDiff);

			var timeDiff = Date.now() - this._touchStartTime;

			var acceleration = Math.abs(this._touchDistance / timeDiff);

			var correction = 0;
			if(acceleration >= 0.5) correction = 30;
			else if(acceleration >= 0.4) correction = 20;
			else if(acceleration >= 0.3) correction = 10;

			//console.log( correction + " " + acceleration );

			if(this._isOpen)
			{
				var refererence = 50 - correction;

				if(this._transitionValue > refererence)
				{
					this._close();
				}
			}
			else
			{
				var refererence = 50 + correction;

				if(this._transitionValue < refererence)
				{
					this._open();
				}
			}

			this._dismiss.css("opacity","");
			this._dismiss.removeClass("manualControl");

			this._panel.css("transform","");
			this._isManualMoved = false;
		}

		this._touchStartPosition = -1;
		this._touchStartTime = -1;
		this._touchDistance = -1;
		this._transitionReference = -1;
		this._transitionValue = -1;

		this._panel.removeClass("manualControl");

		$(window).off( "touchmove.panel" );
		$(window).off( "touchend.panel" );
		$(window).off( "touchcancel.panel" );
	},
	_touchMove: function(event)
	{
		event.stopPropagation();
		//event.preventDefault();
		event.stopImmediatePropagation();

		var diff = event.originalEvent.touches[0].clientX - this._touchStartPosition;

		var diffPercentage = ( diff * 100 / this._panel[0].clientWidth );

		if( this.options.position === "right" ) diffPercentage = diffPercentage * -1;

		var _transitionValue = Math.round( ( this._transitionReference - diffPercentage ) * 10.0 ) / 10.0;

		//console.log( _transitionValue + " " + this._transitionReference + " " + diffPercentage  );

		if(_transitionValue < 0) _transitionValue = 0;

		else if(_transitionValue > 100) _transitionValue = 100;

		if(this._transitionValue == _transitionValue)
		{
			//console.log('skip');
			return;
		}

		if(!this._isManualMoved)
		{
			this._dismiss.addClass("manualControl");
		}

		this._touchDistance = diffPercentage;
		this._transitionValue = _transitionValue;
		this._isManualMoved = true;

		this._panel.css("transform","translate3d(" + ( this.options.position === "left" ? this._transitionValue * -1 : this._transitionValue ) + "%, 0, 0)");

		var value = ( 100.0 - this._transitionValue ) / 100.0;

		//console.log( value );

		this._dismiss.css("opacity", value );
	}
});
