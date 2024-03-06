var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('tools');

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
        opacity: 0;
        position: absolute;
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

            var obfuscated_img = mx._$("img.obfuscated", element);
            var deobfuscated_img = mx._$("img.deobfuscated", element);

            function handler(event)
            {
                if( obfuscated_img.style.opacity == "" )
                {
                    deobfuscated_img.style.opacity = "1";
                    obfuscated_img.style.opacity = "0";
                }
                else
                {
                    deobfuscated_img.style.opacity = "";
                    obfuscated_img.style.opacity = "";
                }
            }
            element.addEventListener("click",handler);
        });
    }
    return ret;
})({});

{% for name in wifi_networks %}{% if wifi_networks[name]["type"] == "public" %}
subGroup.addHtml('guest_wifi', ['admin'], '<div class="service guestwifi" style="text-align: center;text-shadow: var(--submenu-shadow-service-info);"><img class="obfuscated" src="/guest_wifi/?name={{name}}&obfuscated=1"><img class="deobfuscated" src="/guest_wifi/?name=sirius&obfuscated=0"><div class="wifiname">{{name}}</div></div>', { 'order': 380, 'callbacks': { "init": [ mx.GuestWifi.init ] }, 'title': '{i18n_Guest Wifi}', 'info': '{i18n_QRCode}', 'icon': 'guest_wifi.svg' });
{% endif %}{% endfor %}
