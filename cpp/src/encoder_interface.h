#ifndef ENCODER_INTERFACE
#define ENCODER_INTERFACE
#include <boost/signals2/signal.hpp>
#include <cstring>
#include <iostream> 
#include <signal.h>
#include <ctime>
#include <boost/signals2/signal.hpp>
#include <boost/log/trivial.hpp>
#include <thread>
#include <cstdlib>
#include <fstream>
#include <fcntl.h> 
#include <unistd.h> 
#include <string.h> 
#include <sys/socket.h>
#include <sys/ioctl.h> 
#include <net/if.h> 
#include <linux/can.h>
#include <linux/can/raw.h>
#include <sstream>






class Interface{
private: 
	char * can_interface = "can0";     
	char * baud_rate_string = "-s5";
	char* serial_port = "/dev/ttyACM15";
	struct can_frame message; 
	struct ifreq ifr; 
	struct sockaddr_can addr; 
	int can_socket; 
	
	static volatile int exception_flag;
	void handle_angle(); 
	void handle_temp(); 
	void handle_all(); 
	// void handle_delta(); 
	int map_to_socket_can(); 
public: 
	Interface() = default;
	int initialize_channel(); 
	void begin_read_loop(); 
	void static signal_handler(int signal); 
	int teardown(); 
	boost::signals2::signal<void(uint32_t can_id, double angle, double angular_velocity, uint16_t number_of_rotations)> angle_signal; 
	boost::signals2::signal<void(uint32_t can_id, double temp)> temp_signal; 
	boost::signals2::signal<void(struct can_frame)> verbose_signal; 
}; 



#endif