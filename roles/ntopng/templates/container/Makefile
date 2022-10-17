ntop: netflow2ng ndpi
	cd ntopng && ./autogen.sh && ./configure && make

ndpi:
	cd nDPI && ./autogen.sh && ./configure && make

netflow2ng:
	cd netflow2ng && make -B

all: ntop
	echo "Done"

