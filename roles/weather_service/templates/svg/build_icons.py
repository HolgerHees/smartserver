#!/usr/bin/python3

import json
import time
import sys
import os
from os import listdir, system
from os.path import isfile, join, basename, normpath
import xml.etree.ElementTree as ET
from copy import deepcopy

from smartserver.svg import fileGetContents, isForbiddenTag, cleanStyles, cleanGrayscaled

base_src_path = "./"
base_svg_target_path = "../opt/weather_service/icons/svg/"
base_png_target_path = "../opt/weather_service/icons/png/"
base_service_target_path = "../opt/weather_service/icons/"
base_htdocs_target_path = "../htdocs/weather_service/icons/"

base_service_live_target_path = "/smartserver/opt/weather_service/icons/"
base_htdocs_live_target_path = "/smartserver/htdocs/weather_service/icons/"

main_icons = {
    "day": [],
    "night": [ 0.85, 7, 7 ],
    "cloudy": [],
    "cloudy-day-0": [],
    "cloudy-day-1": [],
    "cloudy-day-2": [],
    "cloudy-night-0": [],
    "cloudy-night-1": [],
    "cloudy-night-2": []
}

rain_icons = {
    "raindrop1": { "cloudy": [ 0.5, 30, 70 ], "cloudy-day-0": [ 0.4, 70, 100 ], "cloudy-day-1": [ 0.5, 40, 70 ], "cloudy-day-2": [ 0.5, 30, 70 ], "cloudy-night-0": [ 0.4, 20, 100 ], "cloudy-night-1": [ 0.5, 15, 70 ], "cloudy-night-2": [ 0.5, 30, 70 ] },
    "raindrop2": { "cloudy": [ 0.5, 30, 70 ], "cloudy-day-0": [ 0.4, 70, 100 ], "cloudy-day-1": [ 0.5, 40, 70 ], "cloudy-day-2": [ 0.5, 30, 70 ], "cloudy-night-0": [ 0.4, 20, 100 ], "cloudy-night-1": [ 0.5, 15, 70 ], "cloudy-night-2": [ 0.5, 30, 70 ] },
    "raindrop3": { "cloudy": [ 0.5, 30, 77 ], "cloudy-day-0": [ 0.4, 70, 107 ], "cloudy-day-1": [ 0.5, 40, 77 ], "cloudy-day-2": [ 0.5, 30, 77 ], "cloudy-night-0": [ 0.4, 20, 107 ], "cloudy-night-1": [ 0.5, 15, 77 ], "cloudy-night-2": [ 0.5, 30, 77 ] },
    "raindrop4": { "cloudy": [ 0.5, 30, 72 ], "cloudy-day-0": [ 0.4, 70, 102 ], "cloudy-day-1": [ 0.5, 40, 72 ], "cloudy-day-2": [ 0.5, 30, 72 ], "cloudy-night-0": [ 0.4, 20, 102 ], "cloudy-night-1": [ 0.5, 15, 72 ], "cloudy-night-2": [ 0.5, 30, 72 ] },
    "snowflake1": { "cloudy": [ 0.5, 30, 73 ], "cloudy-day-0": [ 0.4, 70, 100 ], "cloudy-day-1": [ 0.5, 40, 73 ], "cloudy-day-2": [ 0.5, 30, 73 ], "cloudy-night-0": [ 0.4, 20, 100 ], "cloudy-night-1": [ 0.5, 15, 73 ], "cloudy-night-2": [ 0.5, 30, 73 ] },
    "snowflake2": { "cloudy": [ 0.5, 30, 73 ], "cloudy-day-0": [ 0.4, 70, 100 ], "cloudy-day-1": [ 0.5, 40, 73 ], "cloudy-day-2": [ 0.5, 30, 73 ], "cloudy-night-0": [ 0.4, 25, 100 ], "cloudy-night-1": [ 0.5, 15, 73 ], "cloudy-night-2": [ 0.5, 30, 73 ] },
    "snowflake3": { "cloudy": [ 0.5, 30, 73 ], "cloudy-day-0": [ 0.4, 75, 100 ], "cloudy-day-1": [ 0.5, 40, 73 ], "cloudy-day-2": [ 0.5, 30, 73 ], "cloudy-night-0": [ 0.4, 25, 100 ], "cloudy-night-1": [ 0.5, 17, 73 ], "cloudy-night-2": [ 0.5, 30, 73 ] },
    "snowflake4": { "cloudy": [ 0.5, 30, 65 ], "cloudy-day-0": [ 0.4, 72, 90 ], "cloudy-day-1": [ 0.5, 40, 65 ], "cloudy-day-2": [ 0.5, 30, 65 ], "cloudy-night-0": [ 0.4, 22, 90 ], "cloudy-night-1": [ 0.5, 15, 70 ], "cloudy-night-2": [ 0.5, 30, 65 ] },
}
rain_clipping = {
    "raindrop1": { "cloudy": [ 24, 51, 16 ], "cloudy-day-0": [ 34, 51, 14 ], "cloudy-day-1": [ 27, 51, 16 ], "cloudy-day-2": [ 22, 51, 16 ], "cloudy-night-0": [ 14, 51, 16 ], "cloudy-night-1": [ 15, 51, 16 ], "cloudy-night-2": [ 23, 51, 16 ] },
    "raindrop2": { "cloudy": [ 21, 51, 20 ], "cloudy-day-0": [ 31, 51, 19 ], "cloudy-day-1": [ 25, 51, 21 ], "cloudy-day-2": [ 19, 51, 22 ], "cloudy-night-0": [ 11, 51, 20 ], "cloudy-night-1": [ 12, 51, 21 ], "cloudy-night-2": [ 19, 51, 22 ] },
    "raindrop3": { "cloudy": [ 18, 51, 31 ], "cloudy-day-0": [ 30, 51, 25 ], "cloudy-day-1": [ 22, 51, 30 ], "cloudy-day-2": [ 17, 51, 30 ], "cloudy-night-0": [ 10, 51, 25 ], "cloudy-night-1": [ 10, 51, 30 ], "cloudy-night-2": [ 17, 51, 30 ] },
    "raindrop4": { "cloudy": [ 17, 51, 30 ], "cloudy-day-0": [ 30, 51, 24 ], "cloudy-day-1": [ 22, 51, 29 ], "cloudy-day-2": [ 16, 51, 29 ], "cloudy-night-0": [ 10, 51, 24 ], "cloudy-night-1": [ 9, 51, 29 ], "cloudy-night-2": [ 16, 51, 29 ] },
    "snowflake1": { "cloudy": [ 22, 51, 17 ], "cloudy-day-0": [ 34, 51, 14 ], "cloudy-day-1": [ 27, 51, 17 ], "cloudy-day-2": [ 22, 51, 17 ], "cloudy-night-0": [ 14, 51, 14 ], "cloudy-night-1": [ 16, 51, 17 ], "cloudy-night-2": [ 23, 51, 17 ] },
    "snowflake2": { "cloudy": [ 19, 51, 24 ], "cloudy-day-0": [ 31, 51, 20 ], "cloudy-day-1": [ 24, 51, 24 ], "cloudy-day-2": [ 19, 51, 24 ], "cloudy-night-0": [ 12, 51, 20 ], "cloudy-night-1": [ 12, 51, 24 ], "cloudy-night-2": [ 19, 51, 24 ] },
    "snowflake3": { "cloudy": [ 15, 51, 31 ], "cloudy-day-0": [ 30, 51, 26 ], "cloudy-day-1": [ 21, 51, 31 ], "cloudy-day-2": [ 16, 51, 31 ], "cloudy-night-0": [ 10, 51, 26 ], "cloudy-night-1": [ 9, 51, 31 ], "cloudy-night-2": [ 16, 51, 31 ] },
    "snowflake4": { "cloudy": [ 16, 51, 30 ], "cloudy-day-0": [ 29, 51, 25 ], "cloudy-day-1": [ 21, 51, 29 ], "cloudy-day-2": [ 15, 51, 33 ], "cloudy-night-0": [ 9, 51, 24 ], "cloudy-night-1": [ 8, 51, 29 ], "cloudy-night-2": [ 16, 51, 33 ] },
}

effect_icons = {
    "thunder": {
        "single": { "cloudy": [ 0.4, 40, 58 ], "cloudy-day-0": [ 0.3, 105, 100 ], "cloudy-day-1": [ 0.4, 54, 58 ], "cloudy-day-2": [ 0.4, 44, 58 ], "cloudy-night-0": [ 0.3, 40, 100 ], "cloudy-night-1": [ 0.4, 30, 58], "cloudy-night-2": [ 0.4, 50, 58 ] },
        "dual": { "cloudy": [ 0.4, 40, 58 ], "cloudy-day-0": [ 0.3, 105, 100 ], "cloudy-day-1": [ 0.4, 54, 58 ], "cloudy-day-2": [ 0.4, 44, 58 ], "cloudy-night-0": [ 0.3, 40, 100 ], "cloudy-night-1": [ 0.4, 30, 58], "cloudy-night-2": [ 0.4, 50, 58 ] },
        #"dual": { "cloudy": [ 0.4, 40, 52 ], "cloudy-day-0": [ 0.3, 105, 95 ], "cloudy-day-1": [ 0.4, 54, 52 ], "cloudy-day-2": [ 0.4, 44, 52 ], "cloudy-night-0": [ 0.3, 40, 95 ], "cloudy-night-1": [ 0.4, 30, 52], "cloudy-night-2": [ 0.4, 50, 52 ] }
     }
}

style_config = {
    'grayscaled': [
        'snowflake1','snowflake2','snowflake3','snowflake4','wind','temperature','rain','raindrop','compass_circle','compass_needle','sun'
    ],
    'clean_grayscaled': [
        'raindrop1','raindrop2','raindrop3','raindrop4','thunder',
        'day','cloudy-day-0','cloudy-day-1','cloudy-day-2','night','cloudy-night-0','cloudy-night-1','cloudy-night-2','cloudy'
    ]
}

additionals = ["compass_circle","compass_needle","rain","raindrop","temperature","wind","sun"]

ET.register_namespace("","http://www.w3.org/2000/svg")
top = ET.Element('svg', attrib = { 'version':'1.1', 'xmlns:xlink':'http://www.w3.org/1999/xlink', 'x':"0px", 'y':"0px", 'viewBox':"0 0 64 64", 'enable-background':"new 0 0 64 64", 'xml:space':"preserve"})
#comment = ET.Comment('Generated by Marvin')
#top.append(comment)

def appendChild(group, content, color_type, name):
    xml = ET.fromstring(content)

    createGrayscaled = name in style_config['grayscaled']
    createCleanGrayscaled = name in style_config['clean_grayscaled']

    if color_type == "grayscaled" and ( createGrayscaled or createCleanGrayscaled ):
        cleanGrayscaled(xml, createCleanGrayscaled)

    for node in xml.findall('.//*[@id]'):
        if node.attrib["id"] == "sun":
            var_prefix = "--svg-weather-sun"
        elif node.attrib["id"] == "moon":
            var_prefix = "--svg-weather-moon"
        elif node.attrib["id"] == "clouds":
            var_prefix = "--svg-weather-clouds"
        elif node.attrib["id"] == "stars":
            var_prefix = "--svg-weather-stars"
        else:
            var_prefix = None

        if var_prefix is not None:
            node.attrib["fill"] = "var({}-fill)".format(var_prefix)
            node.attrib["stroke"] = "var({}-stroke)".format(var_prefix)
            node.attrib["stroke-width"] = "var({}-stroke-width)".format(var_prefix)

    for child in xml:
        if isForbiddenTag(child):
            continue
        group.append(child)
    return xml

def applyTransform(group, settings):
    transform = []
    if settings[0] != 1.0:
        transform.append("scale({})".format(settings[0]))
    if settings[1] != 0 or settings[2] != 0:
        transform.append("translate({},{})".format(settings[1],settings[2]))

    if len(transform)>0:
        group.attrib['transform'] = ",".join(transform)

def save(data,base_path,filename):
    f = open("{}{}".format(base_path, filename), 'w')
    f.write(data)
    f.close()


def processFile(top, main, main_settings, rain, rain_settings, effect, effect_settings, all_files):
    for color_type in ["colored","grayscaled"]:
        top = ET.Element('svg', attrib = { 'version':'1.1', 'xmlns:xlink':'http://www.w3.org/1999/xlink', 'x':"0px", 'y':"0px", 'viewBox':"0 0 64 64", 'enable-background':"new 0 0 64 64", 'xml:space':"preserve"})

        name = "{}_{}_{}".format( main, rain if rain is not None else "none", effect if effect is not None else "none")
        var_prefix = "--svg-weather-cloud"
        top_group = ET.Element('g', attrib = { 'id': name, 'fill': "var({}-fill)".format(var_prefix), 'stroke': "var({}-stroke)".format(var_prefix), 'stroke-width': "var({}-stroke-width)".format(var_prefix) })

        main_group = ET.Element('g')
        if len(main_settings) > 0:
            applyTransform(main_group, main_settings)
        main_content = fileGetContents( "{}{}.svg".format(base_src_path, main))
        appendChild(main_group, main_content, color_type, main)
        top_group.append(main_group)

        top.append(top_group)

        if rain is not None:
            rain_content = fileGetContents( "{}{}.svg".format(base_src_path, rain))
            var_prefix = "--svg-weather-{}".format(rain[:-1])
            rain_group = ET.Element('g', attrib = { 'fill': "var({}-fill)".format(var_prefix), 'stroke': "var({}-stroke)".format(var_prefix), 'stroke-width': "var({}-stroke-width)".format(var_prefix) } )
            settings = rain_settings[main] if main in rain_settings else None
            if settings is None:
                return
            applyTransform(rain_group, settings)
            rain_xml = appendChild(rain_group, rain_content, color_type, rain)
            top_group.append(rain_group)

            mask = ET.Element('mask', attrib = { 'id': "mask_{}".format(name) })
            rect = ET.Element('rect', attrib = { "x": "0", "y": "0", "width": "64", "height": "64", "fill": "white" })
            mask.append(rect)

            clipping = rain_clipping[rain][main]
            rect = ET.Element('rect', attrib = { "x": str(clipping[0] ), "y": str(clipping[1]), "width": str(clipping[2]), "height": "4", "fill": "black" })
            mask.append(rect)
            top.append(mask)

            parent_map = {c: p for p in main_group.iter() for c in p}

            tmp = main_group.findall(".//*[@id='clouds']")
            if len(tmp) > 0:
                _tmp = deepcopy(tmp[0])
                _tmp.attrib["id"] = "clouds_mask"
                for key in list(_tmp.attrib.keys()):
                    if key[:6] == "stroke":
                        del _tmp.attrib[key]
                #print(parent_map[tmp[0]])
                parent_map[tmp[0]].insert(0, _tmp)

                tmp[0].attrib["fill"] = "transparent"
                tmp[0].attrib["mask"] = "url(#mask_{})".format(name)
            #else:
            #    main_group.attrib["mask"] = "url(#mask_{})".format(name)

            #rect = ET.Element('rect', attrib = { "x": str(clipping[0] ), "y": str(clipping[1] - 5), "width": str(clipping[2]), "height": "7", "fill": "var(--svg-weather-clouds-fill)" })
            #top_group.append(rect)


        if effect is not None:
            effect_content = fileGetContents( "{}{}.svg".format(base_src_path, effect))
            var_prefix = "--svg-weather-{}".format(effect)
            effect_group = ET.Element('g', attrib = { 'fill': "var({}-fill)".format(var_prefix), 'stroke': "var({}-stroke)".format(var_prefix), 'stroke-width': "var({}-stroke-width)".format(var_prefix) } )
            pos = "single" if rain is None else "dual"
            settings = effect_settings[pos][main] if main in effect_settings[pos] else None
            if settings is None:
                return
            applyTransform(effect_group, settings)
            appendChild(effect_group, effect_content, color_type, effect)
            top_group.append(effect_group)

        filename = "{}_{}.svg".format(name,color_type)
        data = ET.tostring(top,encoding='utf8', method='xml').decode("utf-8")
        save(data,base_svg_target_path,filename)

        all_files.append([filename,name,data])

	#xml = ET.fromstring(content)

system('mkdir {}'.format(base_svg_target_path))
system('rm {}*.svg'.format(base_svg_target_path))
system('mkdir {}'.format(base_png_target_path))
system('rm {}*.png'.format(base_png_target_path))

all_files = []
for main_icon, main_settings in main_icons.items():
    processFile(top, main_icon, main_settings, None, None, None, None, all_files)

    for effect_icon, effect_settings in effect_icons.items():
        processFile(top, main_icon, main_settings, None, None, effect_icon, effect_settings, all_files)

    for rain_icon, rain_settings in rain_icons.items():
        processFile(top, main_icon, main_settings, rain_icon, rain_settings, None, None, all_files)

        for effect_icon, effect_settings in effect_icons.items():
            processFile(top, main_icon, main_settings, rain_icon, rain_settings, effect_icon, effect_settings, all_files)

for name in additionals:
    for color_type in ["colored","grayscaled"]:

        top = ET.Element('svg', attrib = { 'version':'1.1', 'xmlns:xlink':'http://www.w3.org/1999/xlink', 'x':"0px", 'y':"0px", 'viewBox':"0 0 64 64", 'enable-background':"new 0 0 64 64", 'xml:space':"preserve"})
        top_group = ET.Element('g', attrib = { 'id': name })

        main_content = fileGetContents( "{}{}.svg".format(base_src_path, name))
        appendChild(top_group, main_content, color_type, name)
        top.append(top_group)

        filename = "{}_{}.svg".format(name, color_type)
        data = ET.tostring(top,encoding='utf8', method='xml').decode("utf-8")
        save(data,base_svg_target_path,filename)

        all_files.append([filename,name,data])

system('mogrify -background "#00000000" -path {} -format png {}*colored.svg'.format(base_png_target_path, base_svg_target_path))

html = """
<html><head>
<style>
body {
    background-color: black;
}
svg {
    --svg-weather-clouds-stroke: blue;
    --svg-weather-clouds-stroke-width: 1px;
    --svg-weather-clouds-fill: red;
    --svg-weather-sun-stroke: rgba(255, 165, 0, 0.5);
    --svg-weather-sun-stroke-width: 1px;
    --svg-weather-sun-fill: yellow;
    --svg-weather-moon-stroke: white;
    --svg-weather-moon-stroke-width: 1px;
    --svg-weather-moon-fill: white;
    --svg-weather-stars-stroke: gray;
    --svg-weather-stars-stroke-width: 0.5px;
    --svg-weather-stars-fill: white;
    --svg-weather-thunder-stroke: rgba(255, 165, 0, 1.0);
    --svg-weather-thunder-stroke-width: 1px;
    --svg-weather-thunder-fill: rgba(255, 165, 0, 0.2);
    --svg-weather-raindrop-stroke: #0055ff;
    --svg-weather-raindrop-stroke-width: 4px;
    --svg-weather-raindrop-fill: #0055ff;
    --svg-weather-snowflake-stroke: #0055ff;
    --svg-weather-snowflake-stroke-width: 1px;
    --svg-weather-snowflake-fill: #0055ff;
}
svg {
    border: 1px solid red;
    width: 64px;
    height: 64px;
}
</style>
</head><body><div class='mvWidget'><div class='weatherForecast'><div class='cloud'>"""
for filename, name, svg in all_files:
    if "grayscaled" not in filename:
        continue

    #print(filename)

    html = '{}{}'.format(html,svg)

    #html = '{}<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" style="height:64px;width:65px;padding:10px;">'.format(html)
    #html = '{}<use ShadowRootMode="open" href="./svg/{}">'.format(html,filename)
    #html = '{}</svg>'.format(html)

html = "{}</div></div></div></body></html>".format(html)

save(html,base_service_target_path,"index.html")

system('rm -R {}/*'.format(base_htdocs_target_path))
system('mkdir {}/svg'.format(base_htdocs_target_path))
for name in additionals:
    system('cp {}/{}* {}svg/'.format(base_svg_target_path, name, base_htdocs_target_path))

if os.path.exists(base_service_live_target_path):
    system('rm -R {}/*'.format(base_service_live_target_path))
    system('cp -r {}/* {}'.format(base_service_target_path, base_service_live_target_path))

if os.path.exists(base_htdocs_live_target_path):
    system('rm -R {}/*'.format(base_htdocs_live_target_path))
    system('mkdir {}/svg'.format(base_htdocs_live_target_path))
    for name in additionals:
        system('cp {}/{}* {}svg/'.format(base_svg_target_path, name, base_htdocs_live_target_path))
