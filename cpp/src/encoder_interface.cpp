#include "encoder_interface.h"


volatile int Interface::exception_flag = 1; 

Interface::Interface(uint32_t baudrate_param, uint32_t opmode_param, const char* serial_port_param){
	this->bitrate.index = baudrate_param; 
	this->opmode.byte = opmode_param;
	strncpy(serial_port,serial_port_param, sizeof(serial_port)); 
	signal(SIGINT,signal_handler); //set up signal handler on class initialization

}; 

CANAPI_Return_t Interface::initialize_channel(){

	if((ret_val = mySerialCAN.InitializeChannel(serial_port,opmode)) != CSerialCAN::NoError){
		BOOST_LOG_TRIVIAL(error)<< "[x] interface could not be initialzed \n"; 
	}
	else{
		BOOST_LOG_TRIVIAL(info)<<" [o] initialized channel at "<<serial_port<<". \n";
		BOOST_LOG_TRIVIAL(info)<<" [o] starting interface... \n"; 
		if((ret_val = mySerialCAN.StartController(bitrate))!= CSerialCAN::NoError){
			BOOST_LOG_TRIVIAL(error)<<"[x] interface could not be started, tearing down... \n"; 
			teardown_channel(); 
		}
		else{
			BOOST_LOG_TRIVIAL(info)<<"[o] interface started \n Press Ctrl+c to abort..\n"; 
			begin_read_loop(); 
		}
	}
	return ret_val; 
}




void Interface::begin_read_loop(const char type, int timeout){
	int start_time = std::time(nullptr); 
	while(timeout?exception_flag&&(start_time-std::time(nullptr)<=timeout):exception_flag){
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
							BOOST_LOG_TRIVIAL(error)<<"[x] unknown read operation "<<type<<" exiting..."<<"\n"; 
							exception_flag = 0;
					}
				}
				else{
					BOOST_LOG_TRIVIAL(error)<<"[x] invalid data length"; 
				}
		}
	}
}; 

void Interface::handle_all(uint8_t* message_data){
	verbose_signal(message); 
}; 

void Interface::handle_angle(uint8_t* message_data){
	if(message_data[0] == 0x55 && message_data[1] == 0x55){
		uint16_t angle_register = message_data[3]<<8|message_data[2]; 
		double angle = angle_register * 360/32768; 
		uint16_t angular_velocity_register = message_data[5]<<8|message_data[4]; 
		double angular_velocity = angular_velocity_register * ((360/32768)/0.1); 
		uint16_t number_of_rotations = message_data[8]<<8|message_data[7]; 
		angle_signal(message.id,angle,angular_velocity,number_of_rotations); 
	}
}; 

void Interface::handle_temp(uint8_t* message_data){
	if(message_data[0] == 0x55 && message_data[1] == 0x56){
		uint16_t temperature_register = message_data[3]<<8|message_data[2]; 
		double temperature = temperature_register/100; 
		temp_signal(message.id,temperature); 
	}
}; 

void Interface::handle_delta(uint8_t* message_data){

}; 


CANAPI_Return_t Interface::teardown_channel(){ 
	if((ret_val = mySerialCAN.TeardownChannel())!= CSerialCAN::NoError){
		BOOST_LOG_TRIVIAL(error)<<"[x] interface could not be shutdown \n";
	}
	else{
		BOOST_LOG_TRIVIAL(info)<<"[o] interface shutdown successfuly \n"; 
	}
	return ret_val; 
}; 


void Interface::signal_handler(int signal){
	mySerialCAN.SignalChannel(); //kills all channels
	exception_flag = 0; //ends read loop; 
}; 

