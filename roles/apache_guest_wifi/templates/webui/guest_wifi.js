var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('tools');
//subGroup.addUrl('guest_wifi', '/guest_wifi/', 'admin', 380, '{i18n_Guest Wifi}', '{i18n_QRCode}', false, "guest_wifi.svg");

mx.GuestWifi = (function( ret ) {
    var css = `
    div.guestwifi {
        position: relative;
    }
    div.guestwifi > img.deobfuscated {
        transition: opacity 0.3s;
        left: 0;
        right: 0;
        margin-left: auto;
        margin-right: auto;
        z-index: 1;
    }
    div.guestwifi > img.obfuscated {
        filter: blur(10px);
        transition: opacity 0.3s;
    }
    div.guestwifi > div.obfuscated {
        position: absolute;
        top: 0px;
        left: 0px;
        right: 0px;
        bottom: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    div.guestwifi > div.obfuscated {
        color: black;
        font-size: 20px;
        text-shadow: 2px 2px 5px white;
    }
    `;

    let style = document.createElement('style');
    document.getElementsByTagName('head')[0].appendChild(style);
    style.type = 'text/css';
    style.appendChild(document.createTextNode(css));

    ret.init = function()
    {
        mx.$$(".guestwifi").forEach(function(element)
        {
            if( mx.Page.isDemoMode() ) mx.$(".wifiname").innerHTML = "demo";

            var obfuscationInfoDiv = document.createElement("div");
            obfuscationInfoDiv.innerHTML = "<div>" + mx.I18N.get("Click to show QR Code", "guest_wifi") + "</div>";
            obfuscationInfoDiv.classList.add("obfuscated");
            element.appendChild(obfuscationInfoDiv);

            function deobfuscate(event)
            {
                var img = mx._$("img", element);
                var _img = document.createElement("img");
                _img.onload = function()
                {
                    mx.Core.waitForTransitionEnd(_img, function()
                    {
                        _img.style.position = "";
                        img.parentNode.removeChild(img);
                        element.removeChild(obfuscationInfoDiv);
                    }, "guest_wifi");
                    _img.style.opacity = "";
                };
                _img.classList.add("deobfuscated");
                _img.style.opacity = "0";
                _img.style.position = "absolute";
                _img.src = img.getAttribute("src").replace("obfuscated=1", mx.Page.isDemoMode() ? "obfuscated=-1" : "obfuscated=0");

                img.style.opacity = "0";

                img.parentNode.insertBefore(_img, img);

                element.removeEventListener("click",deobfuscate);
            }
            element.addEventListener("click",deobfuscate);
        });
    }
    return ret;
})({});

{% for name in vault_wifi_networks %}{% if vault_wifi_networks[name]["type"] == "public" %}
subGroup.addHtml('guest_wifi', '<div class="service guestwifi" style="text-align: center;text-shadow: var(--submenu-shadow-service-info);"><img class="obfuscated" src="/guest_wifi/?name={{name}}&obfuscated=1"><div class="wifiname">{{name}}</div></div>', {"init": [ mx.GuestWifi.init ] }, 'admin', 380, '{i18n_Guest Wifi}', '{i18n_QRCode}', "guest_wifi.svg");
{% endif %}{% endfor %}
