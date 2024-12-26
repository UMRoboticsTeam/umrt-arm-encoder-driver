#include "encoder_interface.h"
#include <iostream>
#include <signal.h>
#include <ctime>


volatile int Interface::exception_flag = 1; 

Interface::Interface(uint32_t baudrate_param, uint32_t opmode_param, const char* serial_port_param){
	this->bitrate.index = baudrate_param; 
	this->opmode.byte = opmode_param;
	strncpy(serial_port,serial_port_param, sizeof(serial_port)); 
	signal(SIGINT,signal_handler); //set up signal handler on class initialization

}; 

CANAPI_Return_t Interface::initialize_channel(){

	if((ret_val = mySerialCAN.InitializeChannel(serial_port,opmode)) != CSerialCAN::NoError){
		std::cerr << "[x] interface could not be initialzed \n"; 
	}
	else{
		std::cout<<" [o] initialized channel at "<<serial_port<<". \n";
		std::cout<<" [o] starting interface... \n"; 
		if((ret_val = mySerialCAN.StartController(bitrate))!= CSerialCAN::NoError){
			std::cerr <<"[x] interface could not be started, tearing down... \n"; 
			teardown_channel(); 
		}
		else{
			std::cout<<"[o] interface started \n Press Ctrl+c to abort..\n"; 
			begin_read_loop(); 
		}
	}
	return ret_val; 
}

void Interface::begin_read_loop(const char type, int timeout){
	int start_time = std::time(nullptr); 
	while(timeout?exception_flag&start_time-std::time(nullptr)<=timeout:exception_flag){
		if(ret_val = mySerialCAN.ReadMessage(message,timeout?timeout:CANREAD_INFINITE) == CSerialCAN::NoError){
				
		}
	}
}; 



CANAPI_Return_t Interface::teardown_channel(){ 
	if((ret_val = mySerialCAN.TeardownChannel())!= CSerialCAN::NoError){
		std::cerr <<"[x] interface could not be shutdown \n";
	}
	else{
		std::cout<<"[o] interface shutdown successfuly \n"; 
	}
	return ret_val; 
}; 


void Interface::signal_handler(int signal){
	mySerialCAN.SignalChannel(); //kills all channels
	exception_flag = 0; //ends read loop; 
}; 

