#!/usr/bin/perl
#
# Holt die Daten vom D0-Zaehler Pafal 20ec3gr
# es wird die obere optische Schnittstelle ausgelesen
# dort liefert der Zaehler alle 2sec. einen Datensatz
# wird von CRON jede Minute aufgerufen
# http://wiki.volkszaehler.org/software/sml
# 03.2012 by NetFritz
# 07.2013 by Ollir
# 09.2013 by TK for Pafal 20ec3gr


# ========================================
#
use Device::SerialPort;
my $port = Device::SerialPort->new("/dev/ttyUSB0") || die $!;
$port->databits(8);
$port->baudrate(4800);
$port->parity("even");
$port->stopbits(2);
$port->handshake("none");
$port->write_settings;

$port->purge_all();
$port->read_char_time(0);     # don't wait for each character
$port->read_const_time(1000); # 1 second per unfulfilled "read" call

#request for pafal
$output="/?!\r\n";
#$count=$port->write($output);
$count=$port->write("\x04");
sleep(1);

# von der schnittstelle lesen
for($i=0;$i<=10;$i++) {

         my ($count,$saw)=$port->read(255);   # will read max 255 chars
         
         print $count . "\n";
         print $saw . "\n";
         
}
