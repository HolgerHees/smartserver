#!/usr/bin/python3

import json
import time
import sys
import os
from os import listdir, system
from os.path import isfile, join, basename, normpath
import xml.etree.ElementTree as ET

from smartserver.svg import fileGetContents, isForbiddenTag, cleanStyles, cleanGrayscaled

base_src_path = "./"
base_svg_target_path = "../etc/weather_service/icons/svg/"
base_png_target_path = "../etc/weather_service/icons/png/"
base_html_target_path = "../etc/weather_service/icons/"

base_html_web_path = "/dataDisk/etc/weather_service/icons/"

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
    "raindrop1": { "cloudy": [ 22, 16 ], "cloudy-day-0": [ 34, 14 ], "cloudy-day-1": [ 27, 16 ], "cloudy-day-2": [ 22, 16 ], "cloudy-night-0": [ 14, 16 ], "cloudy-night-1": [ 15, 16 ], "cloudy-night-2": [ 23, 16 ] },
    "raindrop2": { "cloudy": [ 20, 20 ], "cloudy-day-0": [ 31, 19 ], "cloudy-day-1": [ 25, 21 ], "cloudy-day-2": [ 19, 22 ], "cloudy-night-0": [ 11, 20 ], "cloudy-night-1": [ 12, 21 ], "cloudy-night-2": [ 19, 22 ] },
    "raindrop3": { "cloudy": [ 17, 31 ], "cloudy-day-0": [ 30, 25 ], "cloudy-day-1": [ 22, 30 ], "cloudy-day-2": [ 17, 30 ], "cloudy-night-0": [ 10, 25 ], "cloudy-night-1": [ 10, 30 ], "cloudy-night-2": [ 17, 30 ] },
    "raindrop4": { "cloudy": [ 16, 30 ], "cloudy-day-0": [ 30, 24 ], "cloudy-day-1": [ 22, 29 ], "cloudy-day-2": [ 16, 29 ], "cloudy-night-0": [ 10, 24 ], "cloudy-night-1": [ 9, 29 ], "cloudy-night-2": [ 16, 29 ] },
    "snowflake1": { "cloudy": [ 22, 17 ], "cloudy-day-0": [ 34, 14 ], "cloudy-day-1": [ 27, 17 ], "cloudy-day-2": [ 22, 17 ], "cloudy-night-0": [ 14, 14 ], "cloudy-night-1": [ 16, 17 ], "cloudy-night-2": [ 23, 17 ] },
    "snowflake2": { "cloudy": [ 19, 24 ], "cloudy-day-0": [ 31, 20 ], "cloudy-day-1": [ 24, 24 ], "cloudy-day-2": [ 19, 24 ], "cloudy-night-0": [ 12, 20 ], "cloudy-night-1": [ 12, 24 ], "cloudy-night-2": [ 19, 24 ] },
    "snowflake3": { "cloudy": [ 15, 31 ], "cloudy-day-0": [ 30, 26 ], "cloudy-day-1": [ 21, 31 ], "cloudy-day-2": [ 16, 31 ], "cloudy-night-0": [ 10, 26 ], "cloudy-night-1": [ 9, 31 ], "cloudy-night-2": [ 16, 31 ] },
    "snowflake4": { "cloudy": [ 16, 30 ], "cloudy-day-0": [ 29, 25 ], "cloudy-day-1": [ 21, 29 ], "cloudy-day-2": [ 15, 29 ], "cloudy-night-0": [ 9, 24 ], "cloudy-night-1": [ 8, 29 ], "cloudy-night-2": [ 16, 29 ] },
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
        'snowflake1','snowflake2','snowflake3','snowflake4','wind','temperature','rain','compass_circle','compass_needle','sun'
    ],
    'clean_grayscaled': [
        'raindrop1','raindrop2','raindrop3','raindrop4','thunder',
        'day','cloudy-day-0','cloudy-day-1','cloudy-day-2','night','cloudy-night-0','cloudy-night-1','cloudy-night-2','cloudy'
    ]
}

additionals = ["compass_circle","compass_needle","rain","temperature","wind","sun"]

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

            #defs = ET.Element('defs')
            #top_group.append(defs)
            mask = ET.Element('mask', attrib = { 'id': "mask_{}".format(name) })
            rect = ET.Element('rect', attrib = { "x": "0", "y": "0", "width": "64", "height": "64", "fill": "white" })
            mask.append(rect)

            #rect = ET.Element('rect', attrib = { "x": "0", "y": "0", "width": "100%", "height": "100%", "fill": "black" })
            #rain_group.append(rect)

            clipping = rain_clipping[rain][main]
            rect = ET.Element('rect', attrib = { "x": str(clipping[0] ), "y": "50", "width": str(clipping[1]), "height": "5", "fill": "var(--svg-weather-mask-fill)" })
            #applyTransform(mask_rect, settings)
            mask.append(rect)

            top.append(mask)

            main_group.attrib["mask"] = "url(#mask_{})".format(name)


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

        all_files.append("{}#{}".format(filename,name))

	#xml = ET.fromstring(content)

system('mkdir {}'.format(base_svg_target_path))
system('rm {}*.svg'.format(base_svg_target_path))
system('mkdir {}'.format(base_png_target_path))
system('rm {}*.png'.format(base_png_target_path))

all_files = []
for main_icon, main_settings in main_icons.items():
    processFile(top, main_icon, main_settings, None, None, None, None, all_files)

    for rain_icon, rain_settings in rain_icons.items():
        processFile(top, main_icon, main_settings, rain_icon, rain_settings, None, None, all_files)

        for effect_icon, effect_settings in effect_icons.items():
            processFile(top, main_icon, main_settings, rain_icon, rain_settings, effect_icon, effect_settings, all_files)

    for effect_icon, effect_settings in effect_icons.items():
        processFile(top, main_icon, main_settings, None, None, effect_icon, effect_settings, all_files)

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

        all_files.append("{}#{}".format(filename,name))

system('mogrify -background "#00000000" -path {} -format png {}*colored.svg'.format(base_png_target_path, base_svg_target_path))

html = """
<html class='lightTheme'><head>
<link rel="stylesheet" href="/weather/css/main.css">
<link rel="stylesheet" href="/weather/css/page.css">
<style>
svg {
    border: 1px solid red;
}
</style>
</head><body><div class='mvWidget'><div class='weatherForecast'><div class='cloud'>"""
for filename in all_files:
    if "grayscaled" not in filename:
        continue
    html = '{}<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" style="height:64px;width:65px;padding:10px;">'.format(html)
    html = '{}<use ShadowRootMode="open" href="/weather/icons/svg/{}">'.format(html,filename)
    html = '{}</svg>'.format(html)

html = "{}</div></div></div></body></html>".format(html)

save(html,base_html_target_path,"index.html")

if os.path.exists(base_html_web_path):
    system('rm -R {}/*'.format(base_html_web_path))
    system('cp -r {}/* {}'.format(base_html_target_path, base_html_web_path))
