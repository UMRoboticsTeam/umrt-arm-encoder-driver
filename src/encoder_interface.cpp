#include "encoder_interface.h"

EncoderInterface::~EncoderInterface(){
    if(can_socket >= 0){
        close(can_socket); 
        can_socket = -1 ; 
    }
};

int EncoderInterface::initialize_channel(const char* can_interface) {
    BOOST_LOG_TRIVIAL(info) << "[+] initializing channel: ";

    BOOST_LOG_TRIVIAL(info) << "[+] initializing socket";
    can_socket = socket(PF_CAN, SOCK_RAW, CAN_RAW);
    if (can_socket < 0) {
        BOOST_LOG_TRIVIAL(error) << "[x] could not open socket";
        return -1;
    }

    strcpy(ifr.ifr_name, can_interface);
    BOOST_LOG_TRIVIAL(info) << "[+] fetching interface";
    if (ioctl(can_socket, SIOGIFINDEX, &ifr) < 0) {
        BOOST_LOG_TRIVIAL(error) << "[x] could not find can interface: "<<can_interface;
        close(can_socket);
        return -1;
    }
    BOOST_LOG_TRIVIAL(info) << "[+] binding socket";
    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;
    if (bind(can_socket, (sockaddr*)&addr, sizeof(addr)) < 0) {
        BOOST_LOG_TRIVIAL(error) << "[x] could not bind socket to can interface";
        close(can_socket);
        return -1;
    }
    BOOST_LOG_TRIVIAL(info) << "[+] finished initializing channel";
    return 0;
}


void EncoderInterface::begin_read_loop() {
    BOOST_LOG_TRIVIAL(info) << "[+] beginning read loop: ";
    while (true) {
        can_frame message;
        ssize_t nbytes = read(can_socket, &message, sizeof(can_frame));
        if (nbytes>0 && message.len == 8) {
            handle_angle(message.data, message.can_id);
            handle_temp(message.data,message.can_id);
            handle_all(message);
            handle_delta(message.data, previous_data);
            previous_data = message.data; 
        } else {
            BOOST_LOG_TRIVIAL(error) << "[x] invalid data length " << message.len;
        }
    }
};

void EncoderInterface::handle_all(can_frame message) {
    verbose_signal(message);
};

void EncoderInterface::handle_angle(uint8_t* message_data, uint32_t can_id) {
    if (message_data[0] == 0x55 && message_data[1] == 0x55) {
        uint16_t angle_register_value = uint16_t(message_data[3]) << 8 | message_data[2];
        double angle = angle_register_value * 360 / 32768;
        uint16_t angular_velocity_register_value = uint16_t(message_data[5])<<8 | message_data[4];
        double angular_velocity = angular_velocity_register_value * ((360 / 32768) / 0.1);
        uint16_t number_of_rotations = uint16_t(message_data[7]) << 8 | message_data[6];
        angle_signal(can_id, angle, angular_velocity, number_of_rotations);
    }
};

void EncoderInterface::handle_temp(uint8_t* message_data, uint32_t can_id) {
    if (message_data[0] == 0x55 && message_data[1] == 0x56) {
        uint16_t temperature_register_value = uint16_t(message_data[3]) << 8 | message_data[2];
        int temperature = temperature_register_value / 100;
        temp_signal(can_id, temperature);
    }
};

void EncoderInterface::handle_delta(uint8_t* message_data, uint8_t* previous_data){
    if (message_data[1] == previous_data[1]){  //if both messages are of same type i.e both temperature messages or both angle messages then find difference
        if(message_data[1] == 0x56){
            BOOST_LOG_TRIVIAL(debug)<<"previous message data : "; 
          for(int i=0;  i < 8; i++){
            BOOST_LOG_TRIVIAL(debug)<<previous_data[i]<<" "; 
          }
            BOOST_LOG_TRIVIAL(debug)<<"current message data : "; 
          for(int i=0;  i < 8; i++){
            BOOST_LOG_TRIVIAL(debug)<<message_data[i]<<" "; 
          }
          

        }
    }
};


