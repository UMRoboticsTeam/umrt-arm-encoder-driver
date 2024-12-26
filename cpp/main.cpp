#include <iostream> 
#include "encoder_interface.h"




int main(int argc, char**argv){
	Interface myInterface{Interface()}; 
	myInterface.initialize_channel(); 
	std::cout <<CSerialCAN::GetVersion<< std::endl; 		
};
