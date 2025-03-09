#include "encoder_interface.h"




int Interface::map_to_socket_can() {
	int ret; 
    std::ostringstream map_command;
    map_command << "sudo slcand -o -c " << baud_rate_string << " " << serial_port << " " << can_interface;

    std::string map_command_string = map_command.str();
    BOOST_LOG_TRIVIAL(info) << "[+] Executing system command: " << map_command_string;

    ret = std::system(map_command_string.c_str());
    if(ret == 0){
    	 std::ostringstream ip_command; 

    	 ip_command << "sudo ip link set "<<can_interface<<" up"; 
    	 std::string ip_command_string = ip_command.str(); 
    	 BOOST_LOG_TRIVIAL(info) << "[+] Executing system command: " << ip_command_string;
    	 ret = std::system(ip_command_string.c_str()); 
    }

    return ret;
}


volatile int Interface::exception_flag = 1; 

// Interface::Interface(char * baud_rate_string, char * can_interface, char * serial_port){
	
// }; 

int Interface::initialize_channel(){
	BOOST_LOG_TRIVIAL(info) << "[+] initializing channel: ";

	if(map_to_socket_can() != 0){
		BOOST_LOG_TRIVIAL(error)<<"[x] could not perform mapping"; 
		exit(0);
	}
	BOOST_LOG_TRIVIAL(info) << "[+] initializing socket" ; 
	can_socket = socket(PF_CAN, SOCK_RAW, CAN_RAW); 
	if(can_socket <0){
		BOOST_LOG_TRIVIAL(error)<<"[x] could not open socket"; 
		return -1;  
	}

	strcpy(ifr.ifr_name, can_interface); 
	BOOST_LOG_TRIVIAL(info) << "[+] fetching interface" ; 
	if(ioctl(can_socket, SIOGIFINDEX, &ifr)<0){
		BOOST_LOG_TRIVIAL(error)<<"[x] could not find can interface"; 
		close(can_socket); 
		return -1; 
	}
	BOOST_LOG_TRIVIAL(info) << "[+] binding socket" ; 
	addr.can_family = AF_CAN; 
	addr.can_ifindex = ifr.ifr_ifindex; 
	if(bind(can_socket,(struct sockaddr *)&addr, sizeof(addr))<0){
		BOOST_LOG_TRIVIAL(error)<<"[x] could not bind socket to can interface"; 
		close(can_socket); 
		return -1; 
	}
	BOOST_LOG_TRIVIAL(info) << "[+] finished initializing channel" ; 
	return 0; 
	
}


void Interface::begin_read_loop(){
	BOOST_LOG_TRIVIAL(info) << "[+] beginning read loop: ";
	while(exception_flag){
		int nbytes = read(can_socket, &message, sizeof(struct can_frame)); 
				if(message.len == 8){
							handle_angle(); 
							handle_temp(); 
							handle_all(); 
							// handle_delta();
				}
				else{
					BOOST_LOG_TRIVIAL(error)<<"[x] invalid data length "<<message.len; 
				}
		}	
}; 

void Interface::handle_all(){
	verbose_signal(message); 
}; 

void Interface::handle_angle(){
	auto message_data = message.data; 
	if(message_data[0] == 0x55 && message_data[1] == 0x55){
		uint16_t angle_register = message_data[3]<<8|message_data[2]; 
		double angle = angle_register * 360/32768; 
		uint16_t angular_velocity_register = message_data[5]<<8|message_data[4]; 
		double angular_velocity = angular_velocity_register * ((360/32768)/0.1); 
		uint16_t number_of_rotations = message_data[8]<<8|message_data[7]; 
		angle_signal(message.can_id,angle,angular_velocity,number_of_rotations); 
	}
}; 

void Interface::handle_temp(){
	auto message_data = message.data; 
	if(message_data[0] == 0x55 && message_data[1] == 0x56){
		uint16_t temperature_register = message_data[3]<<8|message_data[2]; 
		double temperature = temperature_register/100; 
		temp_signal(message.can_id,temperature); 
	}
}; 

// void Interface::handle_delta(uint8_t* message_data){

// }; 


int Interface::teardown(){ 
	close(can_socket); 
}; 


void Interface::signal_handler(int signal){
	BOOST_LOG_TRIVIAL(info)<<"[o] keyboard interrupt identified \n"; 
	exception_flag = 0; //ends read loop; 
	//this->teardown(); 
	exit(0); //exits program
}; 

