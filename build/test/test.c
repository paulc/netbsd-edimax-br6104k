
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

int devfd = -1;

void	pinread(int);
void	pinwrite(int, int);

int main(int argc, char **argv) {

    int i,fd;
    char *message = "===== Starting =====\n";
    char *hello = "Hello..\n";

    setsid();
    setlogin("root");

    fd = open("/dev/console",O_RDWR);
    write(fd,(void *)message,21);

    devfd = open("/dev/gpio0",O_RDWR);

    dup2(fd,0);
    dup2(fd,1);
    dup2(fd,2);

    for (i=0;i<10;i++) {
        write(fd,(void *)hello,8);
        usleep(500000);
    }

    close(fd);

    for (i=0;i<10;i++) {
        printf("printf...\n");
        pinwrite(0,2);
        usleep(500000);
    }
    return(0);
}
