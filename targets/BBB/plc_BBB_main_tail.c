/**
 * Tail of code to BBB C targets
 **/

#ifndef MSG_BUFFER_SIZE
#define MSG_BUFFER_SIZE (1<<10) /*1Ko*/
#endif
#ifndef MSG_BUFFER_ATTRS
#define MSG_BUFFER_ATTRS
#endif

static char MsgBuff[MSG_BUFFER_SIZE+1] MSG_BUFFER_ATTRS;
static int32_t SignalEndCode = 0;

int SignalEnd(char* buf, uint32_t size, int32_t code){
    pthread_mutex_lock(&msg_mutex);
    size = (size >= MSG_BUFFER_SIZE) ? MSG_BUFFER_SIZE : size;
    memcpy(MsgBuff, buf, size);
    MsgBuff[size] = 0;
    SignalEndCode = code;
    pthread_mutex_unlock(&msg_mutex);
}

uint32_t getPlcMessage(char* buf, uint32_t max_size, int32_t* code){
    pthread_mutex_lock(&msg_mutex);
    uint32_t size = strlen(MsgBuff);
    size = (max_size < size) ? max_size-1 : size;
    if (buf != NULL){
       memcpy(buf, MsgBuff, size);
       buf[size] = 0;
    }
    if (code != NULL)
       *code = SignalEndCode;
    // Clear the message buffer till next message
    MsgBuff[0] = 0;
    pthread_mutex_unlock(&msg_mutex);
    return size;
}
