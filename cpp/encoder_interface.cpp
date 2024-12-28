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
				if(message.dlc == 8){
					switch(type){
						case 'a':
							handle_angle(message.data); 
							break; 
						case 't':
							handle_temp(message.data); 
							break; 
						case 'e':
							handle_all(message.data); 
							break; 
						case 'd':
							handle_delta(message.data);
							break; 
						default:
							std::cout<<"[x] unknown read operation "<<type<<" exiting..."<<"\n"; 
							exception_flag = 0;
					}
				}
		}
	}
}; 

void Interface::handle_all(uint8_t* message_data){
	std::cout<<"message id: "<<message.id<<"\n"<<"message data count: "<<message.dlc<<"\n"
	<<"message time stamp(s): "<<message.timestamp.tv_sec<<"\n"<<"message data: "; 
	for (size_t i{}; i < message.dlc; i++){
		printf("The value in hexadecimal is: 0x%02X", message.data[i]);
	};
	std::cout<<std::endl; 
}; 

void Interface::handle_angle(uint8_t* message_data){
	if(message_data[0] == 0x55 && message_data[1] == 0x55){
		uint16_t angle_register = message_data[3]<<8|message_data[2]; 
		double angle = angle_register * 360/32768; 
		uint16_t angular_velocity_register = message_data[5]<<8|message_data[4]; 
		double angular_velocity = angular_velocity_register * ((360/32768)/0.1); 
		uint16_t number_of_rotations = message_data[8]<<8|message_data[7]; 
		printf("angle register(0x%02X) = %0.4f ° \n angualr velocity register(0x%02X) = %0.4f °/s \n number of roatations = %d",angle_register,angle, angular_velocity_register, angular_velocity, number_of_rotations); 
	}
}; 

void Interface::handle_temp(uint8_t* message_data){
	if(message_data[0] == 0x55 && message_data[1] == 0x56){
		uint16_t temperature_register = message_data[3]<<8|message_data[2]; 
		double temperature = temperature_register/100; 
		printf("temperature register(0x%02X) = %0.4f °C",temperature_register, temperature); 
	}
}; 

// void Interface::handle_delta(uint8_t* message_data){

// }; 


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

