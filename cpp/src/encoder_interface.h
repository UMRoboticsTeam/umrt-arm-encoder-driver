#ifndef ENCODER_INTERFACE
#define ENCODER_INTERFACE
#include <boost/signals2/signal.hpp>
#include <cstring>
#include <iostream> 
#include "../include/SerialCAN/Includes/SerialCAN.h"
#include "../include/SLCAN/Includes/slcan.h"
#include <iostream>
#include <signal.h>
#include <ctime>
#include <boost/signals2/signal.hpp>
#include <boost/log/trivial.hpp>
#include <thread>





class Interface{
private: 
	slcan_port_t can_port; 
	size_t queue_size = 50; 
	uint8_t bitrate_index;
	sio_attr_t attributes;  
	int ret_val= 0;  
	const char* serial_port = "/dev/ttyACM0"; 
	slcan_message_t message; 

	// CANAPI_OpMode_t opmode = {}; 
	// CANAPI_Bitrate_t bitrate = {};  
	//CANAPI_Message_t message; 


	
	static volatile int exception_flag;
	void handle_angle(uint8_t* message_data); 
	void handle_temp(uint8_t* message_data); 
	void handle_all(uint8_t* message_data); 
	void handle_delta(uint8_t* message_data); 
public: 
	Interface(uint8_t bitrate_index = CAN_250K);
	CANAPI_Return_t initialize_channel(); 
	void begin_read_loop(uint16_t timeout = 0); 
	void static signal_handler(int signal); 
	std::thread test_channel(); 
	int teardown(); 
	boost::signals2::signal<void(uint32_t can_id, double angle, double angular_velocity, uint16_t number_of_rotations)> angle_signal; 
	boost::signals2::signal<void(uint32_t can_id, double temp)> temp_signal; 
	boost::signals2::signal<void(slcan_message_t)> verbose_signal; 
}; 



#endif