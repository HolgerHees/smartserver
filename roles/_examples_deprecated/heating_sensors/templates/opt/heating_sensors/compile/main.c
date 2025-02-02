#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>

#if defined(OS_LINUX) || defined(OS_MACOSX)
  #include <sys/ioctl.h>
  #include <termios.h>
#elif defined(OS_WINDOWS)
  #include <conio.h>
#endif

#include "hid.h"
//*----------------------------------------------------------------------------
static char getkey(void);
//*----------------------------------------------------------------------------
int main()
{
	int i, r, num, temp;
	char c, buf[64], *pwr;

    int foundSensor1 = 0;
    int foundSensor2 = 0;
    
    int count = 0;

	r = rawhid_open(1, 0x16C0, 0x0480, 0xFFAB, 0x0200);
	if (r <= 0) {
		fprintf(stdout, "No Temp-Sensor found\n");
		return -1;
	}
    //fprintf(stdout, "Found Temp-Sensor\n");
    
	while ( !foundSensor1 || !foundSensor2 ) {
      
        count++;
        if( count == 50 )
        {
            fprintf(stdout, "Not all Temp-Sensors found\n");
            return -1;
        }
        
		//....................................
		// check if any Raw HID packet has arrived
		//....................................
		num = rawhid_recv(0, buf, 64, 220);
		if (num < 0) {
			fprintf(stdout, "\nError Reading\n");
			rawhid_close(0);
			return 0;
		}
		
		if (num == 64) {
            temp = *(short *)&buf[4];
            if(buf[2]) { pwr = "Extern"; }
            else { pwr = "Parasite"; }
            
            if( buf[1] == 1 )
            {
                if( foundSensor1 ) continue;
                foundSensor1 = 1;
            }
            if( buf[1] == 2 )
            {
                if( foundSensor2 ) continue;
                foundSensor2 = 1;
            }
		  
            fprintf(stdout, "Sensor #%d of %d: %+.1f°C Power: %-10s ID: ", buf[1], buf[0], temp / 10.0, pwr);
		  
            for (i = 0x08; i < 0x10; i++) {
				fprintf(stdout, "%02X ", (unsigned char)buf[i]);
			}
			fprintf(stdout, "\n");
		}
		//....................................
		// check if any input on stdin
		//....................................
		c = getkey();
		if(c == 0x1B) { return 0; }   // ESC
		if(c >= 32) {
			fprintf(stdout, "\ngot key '%c', sending...\n", c);
			buf[0] = c;
			for (i=1; i<64; i++) {
				buf[i] = 0;
			}
			rawhid_send(0, buf, 64, 100);
		}
	}
}
//*----------------------------------------------------------------------------
#if defined(OS_LINUX) || defined(OS_MACOSX)
// Linux (POSIX) implementation of _kbhit().
// Morgan McGuire, morgan@cs.brown.edu
static int _kbhit() {
	static const int STDIN = 0;
	static int initialized = 0;
	int bytesWaiting;

	if (!initialized) {
		// Use termios to turn off line buffering
		struct termios term;
		tcgetattr(STDIN, &term);
		term.c_lflag &= ~ICANON;
		tcsetattr(STDIN, TCSANOW, &term);
		setbuf(stdin, NULL);
		initialized = 1;
	}
	ioctl(STDIN, FIONREAD, &bytesWaiting);
	return bytesWaiting;
}
static char _getch(void) {
	char c;
	if (fread(&c, 1, 1, stdin) < 1) return 0;
	return c;
}
#endif
//*----------------------------------------------------------------------------
static char getkey(void)
{
	if (_kbhit()) {
		char c = _getch();
		if (c != 0) return c;
	}
	return 0;
}
//*----------------------------------------------------------------------------
