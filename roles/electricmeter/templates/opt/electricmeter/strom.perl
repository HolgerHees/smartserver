#!/usr/bin/perl

# ========================================
#
use Device::SerialPort;
my $port = Device::SerialPort->new("/dev/ttyOpenHabStrom") || die $!;
$port->databits(7);
$port->baudrate(300);
$port->parity("even");
$port->stopbits(1);
$port->handshake("none");
$port->write_settings;

$port->purge_all();
$port->read_char_time(0);     # don't wait for each character
$port->read_const_time(1000); # 1 second per unfulfilled "read" call

#
# OBIS-Kennzahl und Anzahl der Zeichen von Anfang OBIS bis Messwert,
# Messwertwertlaenge  8-10 Zeichen
# Multiplikator (Einspeisung negativ)

%channel = (
  'dde4f180-2bf3-11e3-8380-XXXXXXXXXXXX' => ['1.8.0',4,9,1], # 1-0:1.8.0  /* kWh aufgenommen */
#  '054e89b0-26cf-11e3-a635-XXXXXXXXXXXX' => ['2.8.0',4,9,-1000],# 1-0:2.8.0  /* kWh rueckgespeis*/
);
$value_count=1;

#request for pafal
$output="/?!\r\n";
$count=$port->write($output);
sleep(2);
$output="\x06\x30\x30\x30\r\n";
$count=$port->write($output);

# von der schnittstelle lesen
for($i=0;$i<=10;$i++) {
        # wenn mehr als 10 chars gelesen werden wird ausgewertet,
        # wenn nicht wird Schleife 10 mal wiederholt
         my ($count,$saw)=$port->read(255);   # will read max 255 chars
         
         if ($count >10) {
                #print  "read $count chars\n";
                #print  "$count <> $saw\n";  # gibt die empfangenen Daten aus

                while (($uuid) = each(%channel)){
                        $key =  $channel{$uuid}[0] ;
                        $pos =  $channel{$uuid}[1] ;
                        $len =  $channel{$uuid}[2] ;
                                #print "uuid=$uuid , key=$key, pos=$pos, len=$len\n" ;

                        # Stringpos raussuchen
                        $pos1=index($saw,$key);
                        if( $pos1 != -1 )
                        {
                            # grob rausschneiden
                            $val1 = substr( $saw , $pos1  , 50);
                            # print $key . " = " . $val1  . "\n";

                            # Messwert selber
                            $val2 = substr( $val1 , length($key) + $pos , $len);

                            # Wert umwandeln
                            $val3 =  $val2*$channel{$uuid}[3]; 
                            #print $uuid . " :: " . $val3 . "\n";

                            # Wert im Hash ablegen
                            $channel{$uuid}[4] = $val3;
                            
                            $value_count--;
                        }
                }
                #print $channel;
                #last; # while verlassen
        } 
        else
        {
                if( $value_count == 0 )
                {
                    last;
                }
		        #print join(", ", @$channel);
                #print "Schnittstellenlesefehler redu = $i ; count = $count <> \n";
        }
}

$timestamp = time() * 1000 ; # msec seit 1.1.1970
while (($uuid) = each(%channel)){
        $val =  $channel{$uuid}[4] ;
        #print $val . " " . $uuid . "\n";
        if ($val != 0) {
               $request = "curl -s -X PUT -H \"Content-Type: text/plain\" -d \"".$val."\" \"http://127.0.0.1:8080/rest/items/Electricity_Meter/state\"";
               #print $val;
               #print $request;
               system $request;
	}
}
