def fileGetContents(filename):
	return open(filename).read()

def isForbiddenTag(node):
	return node.tag == '{http://www.w3.org/2000/svg}defs' or node.tag == '{http://www.w3.org/2000/svg}metadata' or node.tag == '{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}namedview'

def cleanStyles( child ):
	_styles = []
	_classes = []
	styles = child.attrib['style'].split(";")

	for style in styles:
		data = style.split(":")
		if data[0] == 'fill':
			#child.attrib['fill'] = data[1]
			pass

		elif data[0] == 'stroke':
			#child.attrib['stroke'] = data[1]
			pass

        # Keep opacity. Used for info svg icon.
		elif ( data[0] == 'stroke-opacity' or data[0] == 'fill-opacity' ) and ( data[1] == '1' or data[1] == '0' ) :
			_styles.append(data[0]+":"+data[1])
			pass

		else:
			#_styles.append(style)
			pass

	if len(_styles) > 0:
		child.attrib['style'] = ";".join(_styles)
	else:
		del child.attrib['style']
		#pass

def cleanGrayscaled(xml, createCleanGrayscaled):
    for node in xml.findall('.//*[@style]'):
        if createCleanGrayscaled:
            del node.attrib['style']
        else:
            cleanStyles(node)

    for node in xml.findall('.//*[@fill]'):
        del node.attrib['fill']

    for node in xml.findall('.//*[@stroke]'):
        del node.attrib['stroke']

    if createCleanGrayscaled:
        for node in xml.findall('.//*[@stroke-width]'):
            del node.attrib['stroke-width']

