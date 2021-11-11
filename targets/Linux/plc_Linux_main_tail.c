/**
 * Tail of code to BBB C targets
 **/

#ifndef MSG_BUFFER_SIZE
#define MSG_BUFFER_SIZE (1<<10) /*1Ko*/
#endif
#ifndef BTN_BUFFER_SIZE
#define BTN_BUFFER_SIZE (32)
#endif

static char Msg1Buff[MSG_BUFFER_SIZE+1];
static char Msg2Buff[MSG_BUFFER_SIZE+1];
static char Msg3Buff[MSG_BUFFER_SIZE+1];

static char Btn1Buff[BTN_BUFFER_SIZE+1];
static char Btn2Buff[BTN_BUFFER_SIZE+1];
static char Btn3Buff[BTN_BUFFER_SIZE+1];

static int32_t Btn1Code = 0;
static int32_t Btn2Code = 0;
static int32_t Btn3Code = 0;

static uint8_t Processed = 0;
static int32_t BtnPressedCode = 0;

void setPlcMessages(char* msg1, uint32_t msg1_size, char* msg2, uint32_t msg2_size, char* msg3, uint32_t msg3_size)
{
    pthread_mutex_lock(&msg_mutex);

    uint32_t size = (size >= MSG_BUFFER_SIZE) ? MSG_BUFFER_SIZE : msg1_size;
    memcpy(Msg1Buff, msg1, size);
    Msg1Buff[size] = 0;

    size = (size >= MSG_BUFFER_SIZE) ? MSG_BUFFER_SIZE : msg2_size;
    memcpy(Msg2Buff, msg2, size);
    Msg2Buff[size] = 0;

    size = (size >= MSG_BUFFER_SIZE) ? MSG_BUFFER_SIZE : msg3_size;
    memcpy(Msg3Buff, msg3, size);
    Msg3Buff[size] = 0;

    pthread_mutex_unlock(&msg_mutex);
}

uint32_t getPlcMessages(char* msg1, uint32_t msg1_max_size, char* msg2, uint32_t msg2_max_size, char* msg3, uint32_t msg3_max_size)
{
    pthread_mutex_lock(&msg_mutex);

    uint32_t size = strlen(Msg1Buff);
    size = (msg1_max_size < size) ? msg1_max_size-1 : size;
    if (msg1 != NULL)
    {
       memcpy(msg1, Msg1Buff, size);
       msg1[size] = 0;
    }

    size = strlen(Msg2Buff);
    size = (msg2_max_size < size) ? msg2_max_size-1 : size;
    if (msg2 != NULL)
    {
       memcpy(msg2, Msg2Buff, size);
       msg2[size] = 0;
    }

    size = strlen(Msg3Buff);
    size = (msg3_max_size < size) ? msg3_max_size-1 : size;
    if (msg3 != NULL)
    {
       memcpy(msg3, Msg3Buff, size);
       msg3[size] = 0;
    }

    pthread_mutex_unlock(&msg_mutex);
    return 0;
}

void setPlcButtons(char* btn_text1, uint32_t btn_text1_size, int32_t btn_code1, char* btn_text2, uint32_t btn_text2_size, int32_t btn_code2, char* btn_text3, uint32_t btn_text3_size, int32_t btn_code3)
{
    pthread_mutex_lock(&msg_mutex);

    uint32_t size = (size >= BTN_BUFFER_SIZE) ? BTN_BUFFER_SIZE : btn_text1_size;
    memcpy(Btn1Buff, btn_text1, size);
    Btn1Buff[size] = 0;
    Btn1Code = btn_code1;

    size = (size >= BTN_BUFFER_SIZE) ? BTN_BUFFER_SIZE : btn_text2_size;
    memcpy(Btn2Buff, btn_text2, size);
    Btn2Buff[size] = 0;
    Btn2Code = btn_code2;

    size = (size >= BTN_BUFFER_SIZE) ? BTN_BUFFER_SIZE : btn_text3_size;
    memcpy(Btn3Buff, btn_text3, size);
    Btn3Buff[size] = 0;
    Btn3Code = btn_code3;

    pthread_mutex_unlock(&msg_mutex);
}

uint32_t getPlcButtons(char* btn_text1, uint32_t btn_text1_max_size, int32_t* btn_code1, char* btn_text2, uint32_t btn_text2_max_size, int32_t* btn_code2, char* btn_text3, uint32_t btn_text3_max_size, int32_t* btn_code3)
{
    pthread_mutex_lock(&msg_mutex);

    uint32_t size = strlen(Btn1Buff);
    size = (btn_text1_max_size < size) ? btn_text1_max_size-1 : size;
    if (btn_text1 != NULL)
    {
       memcpy(btn_text1, Btn1Buff, size);
       btn_text1[size] = 0;
    }
    if (btn_code1 != NULL)
        *btn_code1 = Btn1Code;

    size = strlen(Btn2Buff);
    size = (btn_text2_max_size < size) ? btn_text2_max_size-1 : size;
    if (btn_text2 != NULL)
    {
       memcpy(btn_text2, Btn2Buff, size);
       btn_text2[size] = 0;
    }
    if (btn_code2 != NULL)
        *btn_code2 = Btn2Code;

    size = strlen(Btn3Buff);
    size = (btn_text3_max_size < size) ? btn_text3_max_size-1 : size;
    if (btn_text3 != NULL)
    {
       memcpy(btn_text3, Btn3Buff, size);
       btn_text3[size] = 0;
    }
    if (btn_code3 != NULL)
        *btn_code3 = Btn3Code;

    pthread_mutex_unlock(&msg_mutex);
    return 0;
}

void setPlcButtonProcessed(uint8_t processed)
{
    pthread_mutex_lock(&msg_mutex);
    Processed = processed;
    pthread_mutex_unlock(&msg_mutex);
}

uint32_t getPlcButtonProcessed(uint8_t* processed)
{
    pthread_mutex_lock(&msg_mutex);
    if (processed != NULL)
        *processed = Processed;
    pthread_mutex_unlock(&msg_mutex);
    return 0;
}

void setPlcButtonPressed(int32_t code)
{
    pthread_mutex_lock(&msg_mutex);
    BtnPressedCode = code;
    pthread_mutex_unlock(&msg_mutex);
}

int32_t getPlcButtonPressed()
{
    pthread_mutex_lock(&msg_mutex);
    int32_t code = BtnPressedCode;
    pthread_mutex_unlock(&msg_mutex);
    return code;
}
