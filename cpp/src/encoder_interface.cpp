#include "encoder_interface.h"


volatile int Interface::exception_flag = 1; 

Interface::Interface(uint8_t bitrate_index){
	this->bitrate_index = bitrate_index; 
	can_port = slcan_create(queue_size);
	signal(SIGINT,signal_handler); //set up signal handler on class initialization
	slcan_setup_bitrate(can_port,bitrate_index); 
}; 

int Interface::initialize_channel(){
	
	if(ret_val = slcan_connect(can_port,serial_port, &attributes) != 0){
		switch (ret_val)
		{
		case ENODEV :
			BOOST_LOG_TRIVIAL(error)<< "[x] interface could not be initialzed "<<exception_flag<<" "<< serial_port <<" **no such device** \n"; 
			break;
		case EINVAL:
			BOOST_LOG_TRIVIAL(error)<< "[x] interface could not be initialzed "<<exception_flag<<" "<< serial_port <<" **invalid argument** \n"; 
		break; 

		case EALREADY:
			BOOST_LOG_TRIVIAL(error)<< "[x] interface could not be initialzed "<<exception_flag<<" "<< serial_port <<" **already connected** \n"; 
		break; 
		
		default:
			BOOST_LOG_TRIVIAL(error)<< "[x] interface could not be initialzed "<<exception_flag<<" "<< serial_port <<" something else \n"; 
			break;
		}
		
		
	}
	else{
		BOOST_LOG_TRIVIAL(info)<<" [o] initialized channel at "<<serial_port<<". \n";
		BOOST_LOG_TRIVIAL(info)<<" [o] starting interface... \n"; 
		if(ret_val =slcan_open_channel(can_port) != 0){
			BOOST_LOG_TRIVIAL(error)<<"[x] interface could not be started, tearing down... \n"; 
			teardown(); 
		}
		else{
			BOOST_LOG_TRIVIAL(info)<<"[o] interface started \n Press Ctrl+c to abort..\n"; 
			begin_read_loop(); 
		}
	}
	return ret_val; 
}


std::thread Interface::test_channel(){
	std::thread loop_thread([](){int counter = 0; while(true){BOOST_LOG_TRIVIAL(info)<<"test loop ["<<counter<<"] \n"; sleep(5); counter++;}}); 
	return loop_thread; 
}

void Interface::begin_read_loop(uint16_t timeout){
	while(exception_flag){
		if(ret_val = slcan_read_message(can_port,&message,timeout) == CSerialCAN::NoError){
				if(message.can_dlc == 8){
							handle_angle(message.data); 
							handle_temp(message.data); 
							handle_all(message.data); 
							handle_delta(message.data);
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
		angle_signal(message.can_id,angle,angular_velocity,number_of_rotations); 
	}
}; 

void Interface::handle_temp(uint8_t* message_data){
	if(message_data[0] == 0x55 && message_data[1] == 0x56){
		uint16_t temperature_register = message_data[3]<<8|message_data[2]; 
		double temperature = temperature_register/100; 
		temp_signal(message.can_id,temperature); 
	}
}; 

void Interface::handle_delta(uint8_t* message_data){

}; 


int Interface::teardown(){ 
	slcan_close_channel(can_port); 
	slcan_disconnect(can_port); 
	slcan_destroy(can_port); 
	// if((ret_val = mySerialCAN.TeardownChannel())!= CSerialCAN::NoError){
	// 	BOOST_LOG_TRIVIAL(error)<<"[x] interface could not be shutdown \n";
	// }
	// else{
	// 	BOOST_LOG_TRIVIAL(info)<<"[o] interface shutdown successfuly \n"; 
	// }
	// return ret_val; 
}; 


void Interface::signal_handler(int signal){
	BOOST_LOG_TRIVIAL(info)<<"[o] keyboard interrupt identified \n"; 
	exception_flag = 0; //ends read loop; 
	// teardown(); // closes channels, connections and kills can interface
	exit(0); //exits program
}; 

