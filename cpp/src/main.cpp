#include <iostream> 
#include "encoder_interface.h"
#include <boost/signals2/slot.hpp>

void temperature_handler(uint32_t can_id, double temp){
    
    BOOST_LOG_TRIVIAL(info) << "can_id: " <<can_id<<" temp: "<<temp<<"\n"; 
}; 
void angle_handler(uint32_t can_id,double angle, double angular_vel, uint16_t n_rotations ){
     BOOST_LOG_TRIVIAL(info) << "can_id: "<<can_id<<" velocity: "<<angular_vel<<" num rotations: "<<n_rotations<<"\n"; 
};


int main(int argc, char**argv){
	Interface myInterface{Interface()}; 
	myInterface.angle_signal.connect([&](uint32_t can_id, double angle, double angular_vel, uint16_t n_rotations){angle_handler(can_id,angle,angular_vel,n_rotations);}); 
    myInterface.temp_signal.connect([&](uint32_t can_id, double temp){temperature_handler(can_id,temp);}); 
	if(myInterface.initialize_channel() == 0){
		 myInterface.begin_read_loop(); 
	}
	
	return 0;  		
};
